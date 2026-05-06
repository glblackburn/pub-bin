---
todos:
  - id: add-plan-09-narrative
    content: "Add plan-009 consolidated narrative for Rich TUI Up/Down arrow issues (DEF-002/003/006/008)"
    status: completed
  - id: add-plan-09-evidence-bundle
    content: "Document evidence bundle and agent validation for one-press Up/Down (plan-09)"
    status: completed
  - id: phase-1-tui-debug-timestamps
    content: "Phase 1: add wall-clock and monotonic timestamps to TUI debug JSON + stderr (better logging for Up/Down analysis)"
    status: completed
  - id: phase-2-test-execute-analyze
    content: "Phase 2: run automated tests, AI + user manual runs with evidence bundles, analyze all logs; define Phase 3+ from findings"
    status: completed
isProject: false
---

# Plan 09: Rich TUI Up and Down arrow navigation — phased remediation

> **Frozen — superseded by [plan-020-uber-true-up](plan-020-uber-true-up.md) on 2026-05-06.**
>
> This document is **read-only**. Do not add new work, status updates, or fix references here.
> Open work moved to plan-020. New features → new `plan-###`. Problems → defects under
> [`docs/osx/defects/`](../defects/) whose `related_plans:` references this file and `plan-020`.

**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).

This document is the **working plan** to drive **Up** / **Down** arrow behavior in the Rich pre-run table toward stable, predictable navigation and **trustworthy diagnostics**. The **normative outcome** of the whole plan is **[Plan goal: Target use case (acceptance)](#plan-goal-target-use-case-acceptance)**—one physical keypress moves the highlight exactly **one row** in the expected direction, with logs that operators and agents can trust. Work starts with **better logging (Phase 1)**, then **runs tests and analyzes evidence (Phase 2)** using automated tests, AI-driven manual checks, and **user** manual runs with full log bundles fed back for analysis. **Further phases (Phase 3+)** are **not specified here**; they will be written **after Phase 2** results (remaining bugs, environment-specific issues, or deeper instrumentation).

**Normative UX and checklist:** **[`plan-002-macos-mouse-click-terminal-ux.md`](plan-002-macos-mouse-click-terminal-ux.md)**  
**Per-defect detail:** **[`../defects/README.md`](../defects/README.md)**  
**Deep design (CSI, PTY, logging):** **[Appendix: merged engineering notes](#appendix-merged-engineering-notes-formerly-split-agent-plans)** (replaces former **`plan-agent-*`** files under **`docs/osx/plans/agent/`**).

---

## Plan goal: Target use case (acceptance)

Everything in this plan—logging, tests, analysis, and later fixes—exists to **satisfy** the following **acceptance target** for the Rich pre-run settings table:

- **Down (once):** the **next** row in the settings table is **highlighted** (focus moves down by one row).
- **Up (once):** the **previous** row is **highlighted** (focus moves up by one row).

“Highlighted” means the same notion as the operator: the **selected** row in the Rich table (bold / focus styling on the **Setting** column in practice). Broader pre-run UX rules remain in **[`plan-002`](plan-002-macos-mouse-click-terminal-ux.md)**; this plan focuses on proving and preserving **arrow-driven row motion** under real terminals.

---

## Table of contents

- [Plan goal: Target use case (acceptance)](#plan-goal-target-use-case-acceptance)
- [Purpose and scope](#purpose-and-scope)
- [Phased roadmap overview](#phased-roadmap-overview)
- [Phase 1: Better logging for analysis](#phase-1-better-logging-for-analysis)
- [Phase 2: Execute tests and analyze results](#phase-2-execute-tests-and-analyze-results)
  - [Phase 2: Operator checklist (human)](#phase-2-operator-checklist-human)
  - [Phase 2: AI execution record](#phase-2-ai-execution-record)
  - [Phase 2: Analysis (Phase 3+ inputs)](#phase-2-analysis-phase-3-inputs)
- [Phase 3 and beyond](#phase-3-and-beyond)
- [Background: consolidated narrative](#background-consolidated-narrative) — defect summary, operator narrative, acceptance cross-reference, evidence bundle, agent validation, stderr “unchanged lines” note (subsections under that heading)
- [Optional next instrumentation](#optional-next-instrumentation-if-bundles-stay-inconclusive)
- [Appendix: merged engineering notes (formerly split agent plans)](#appendix-merged-engineering-notes-formerly-split-agent-plans)
- [Repo pointers](#repo-pointers-tests-and-docs)

---

## Purpose and scope

**Plan goal (normative):** deliver the behavior and evidence needed to meet **[Plan goal: Target use case (acceptance)](#plan-goal-target-use-case-acceptance)**—reliable **one press → one row** **Up** / **Down** motion in the Rich pre-run table, with **telemetry aligned** to what the operator sees. Phases 1–2 (and any Phase 3+) are **means** toward that end: better logs first, then measured runs and analysis, then targeted remediation as Phase 2 dictates.

**In scope:** pre-run Rich table **Up** / **Down** navigation, related **cancel / Esc** policy interactions, **CSI timing** in `read_raw_key`, and **debug telemetry** that must align with operator perception (**DEF-002**, **DEF-003**, **DEF-006**, **DEF-008** classes).

**Out of scope for this plan file:** implementing fixes beyond what each phase describes; Phase 3+ content until Phase 2 completes.

The **background** section keeps the original **consolidated narrative**, defect summaries, evidence-bundle recipe, and agent validation notes unchanged in substance so reports and agents can still cite one document. The **[Target use case (acceptance)](#target-use-case-acceptance)** heading there points back to the **Plan goal** section above so the acceptance definition stays **single-sourced** at the top.

---

## Phased roadmap overview

| Phase | Focus | Exit criterion (high level) |
|-------|--------|-----------------------------|
| **1** | Instrumentation — time-ordered, distinct TUI debug lines | Timestamps and tests described in Phase 1 are **shipped**; operators can correlate keys to log lines reliably. |
| **2** | Evidence — automated + manual (AI + user) + analysis | Findings documented; failures classified; **Phase 3+** plan drafted from data, not guesswork. |
| **3+** | *TBD after Phase 2* | Code fixes, extra tests, env-specific notes, or optional stdin tracing — whatever Phase 2 shows is needed to meet **[Plan goal: Target use case (acceptance)](#plan-goal-target-use-case-acceptance)**. |

---

## Phase 1: Better logging for analysis

**Goal:** make each **`MACOS_MOUSE_CLICK_TUI_STATE`** emission **obviously distinct** and **time-correlatable** in both the **NDJSON log file** and **stderr**, without changing Rich table rendering. This addresses the **“stderr looks unchanged when state repeats”** problem called out in [Background § Operator pain](#operator-pain-stderr-looks-unchanged-when-state-repeats).

**Status:** **Shipped** in repo (implementation + tests + operator docs). **Phase 1 commit:** `a8c3e93`.

**Tasks (as implemented):**

1. **JSON body** — extend `_debug_tui_emit` payloads (see [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py) `_debug_tui_write_line` / `_debug_tui_emit`) with at least:
   - **`ts_wall`** — wall-clock for **humans** and calendar correlation: **ISO-8601** string with **fractional seconds** and a **numeric timezone offset** (not `Z` alone unless UTC is explicit and documented).  
     - *Example value:* `"2026-04-20T15:23:41.527-07:00"`  
     - Sortable lexicographically if offsets are consistent; unambiguous across DST when offset is present.
   - **`ts_mono_ns`** — monotonic time for **machines**: **integer** count of **nanoseconds** from an **unspecified origin** (e.g. `time.monotonic_ns()` at process start is irrelevant—only **differences** matter). Strict total order even when two emissions share the same **`ts_wall`** millisecond.  
     - *Example value:* `9123456789012345`  
     - *Example delta:* line B `ts_mono_ns` minus line A `ts_mono_ns` ⇒ nanoseconds between those two emissions (overflow across reboot not a concern for one session).
   - *Illustrative one-line NDJSON record* (other keys unchanged from today; ellipses for brevity):

```json
{"ts_wall":"2026-04-20T15:23:41.527-07:00","ts_mono_ns":9123456789012345,"selected_index":0,"row_key":"mode","setting_label":"Mode","value_text":"learn","source":"cli","event":"draw"}
```

2. **Stderr prefix** — prepend the same **`ts_wall`** string (or a compact `HH:MM:SS.mmm` slice derived from it) **before** the existing `MACOS_MOUSE_CLICK_TUI_STATE ` prefix **or** embed it in the prefix pattern so scrolling operators see a **new** line at a glance even when the JSON body matches the previous row.  
   - *Example stderr line:* `2026-04-20T15:23:41.527-07:00 MACOS_MOUSE_CLICK_TUI_STATE {"ts_wall":"2026-04-20T15:23:41.527-07:00","ts_mono_ns":9123456789012345,...}`  
   - (Exact prefix formatting is an implementation detail; the requirement is **visible wall time** + **unchanged** ability to strip a fixed prefix and parse JSON.)
3. **Docs** — update [`osx/README.md`](../../../osx/README.md) (jq examples, field dictionary) and this plan’s **[appendix](#appendix-merged-engineering-notes-formerly-split-agent-plans)** / **[`plan-002`](plan-002-macos-mouse-click-terminal-ux.md)** cross-links if the public contract changes.
4. **Automated tests (required)** — extend [`osx/tests/test_debug_tui_logging_meta.py`](../../../osx/tests/test_debug_tui_logging_meta.py) (and any other tests that parse TUI debug lines) so **CI proves** the feature works end-to-end, not only by manual eyeballing stderr:
   - **Presence:** every parsed **`draw`** / **`after_key`** / **`run`** / **`anchor`** payload from the log sink and from **stderr** (after stripping the `MACOS_MOUSE_CLICK_TUI_STATE ` prefix) includes **`ts_wall`** and **`ts_mono_ns`** when **`MACOS_MOUSE_CLICK_DEBUG_TUI`** is on.
   - **`ts_wall` format:** assert string matches a documented pattern (e.g. ISO-8601 with offset and fractional seconds as in examples above); reject empty or naive `Z`-only forms unless implementation explicitly standardizes on UTC and tests document that.
   - **`ts_mono_ns` type and ordering:** assert **integer**; for **two emissions in one test** (e.g. `draw` then `after_key`), assert `ts_mono_ns` **strictly increases** on the second line (monotonicity within a process).
   - **Stderr prefix:** assert the human-visible wall time appears on stderr **before** or within the prefix as specified in task 2, so operators get a new visual anchor even when JSON bodies repeat.
   - **Fixtures:** update any hard-coded JSON strings in tests to include the new fields; keep **log file** lines **jq-friendly** (one JSON object per line; new fields **additive** so old `jq` filters keep working when keys are ignored).

**Non-goals for Phase 1:** raw stdin hex dumps (deferred to [optional instrumentation](#optional-next-instrumentation-if-bundles-stay-inconclusive)); changing **Rich** layout or adding interactive TUI “debug HUD.”

**Tracking:** frontmatter todo **`phase-1-tui-debug-timestamps`** — **`completed`**.

---

## Phase 2: Execute tests and analyze results

**Goal:** after Phase 1 logging is in place, **produce comparable evidence** from **CI**, **AI-driven manual runs**, and **real user sessions**, then **analyze** that evidence so Phase 3+ addresses actual failure modes. Success is measured against **[Plan goal: Target use case (acceptance)](#plan-goal-target-use-case-acceptance)** (one physical **Up** / **Down** ⇒ one row move, logs match perception).

**Activities:**

1. **Automated tests** — run the full relevant **`pytest`** surface (TUI debug meta, arrow / `read_raw_key` behavior, PTY navigation tests where applicable). Treat failures and **`xfail`**/`skip` patterns as inputs to the analysis (flaky PTY vs real product bug).
2. **AI agent manual tests** — an agent (or scripted checklist from this document’s **[appendix](#appendix-merged-engineering-notes-formerly-split-agent-plans)** and **[`plan-002`](plan-002-macos-mouse-click-terminal-ux.md)**) runs **terminal scenarios**: single Up, single Down, edit-then-arrow, wheel near editor, etc., capturing **NDJSON**, **stderr**, and short **action transcripts** per [Evidence bundle](#evidence-bundle-from-a-running-osxmacos_mouse_clickpy-attach-to-a-bug-report-or-agent-session).
3. **User manual tests** — the human operator repeats representative scenarios in their **real environment** (Terminal.app / iTerm, SSH, tmux, hardware). They attach the **same bundle** described under [Background: consolidated narrative](#background-consolidated-narrative) (**Evidence bundle**): env vars, **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`** file, **stderr** capture, **operator transcript** (ordered keypresses + wall times), optional **screenshot or recording**, and optional **terminal transcript** — and provide **all log output** back to the **AI agent** (or issue thread) for **analysis**.
4. **Analysis** — classify outcomes against **DEF-002/003/006/008** themes, logging gaps, and UI-vs-telemetry mismatches; note **environment-specific** vs **code** issues; record **repro steps** and **jq**/`grep` anchors on specific lines.

**Exit criterion:** a short **written summary** (in-repo doc update, defect comment, or agent session log) that states what passed, what failed, and **what Phase 3+ should contain**.

**Tracking:** frontmatter todo **`phase-2-test-execute-analyze`** — **`completed`** for the **AI + automated** portions documented below; **human** checklist items remain for operators to close in their environments.

### Phase 2: Operator checklist (human)

Use this after pulling **Phase 1** (`a8c3e93` or later). Check boxes as you complete each row; attach the bundle to an issue or agent session when asking for analysis.

- [ ] **Environment snapshot:** record `TERM`, Terminal.app vs iTerm vs other, local vs SSH, tmux/screen if any, `python3 -V`, `pip show rich`, and `git rev-parse HEAD` (or note dirty tree).
- [ ] **Enable debug:** `export MACOS_MOUSE_CLICK_DEBUG_TUI=1` and `export MACOS_MOUSE_CLICK_DEBUG_TUI_LOG=/path/to/session.ndjson` (writable path; one session per file is easiest to parse).
- [ ] **Capture stderr:** tee or redirect `2>` to a file so **`MACOS_MOUSE_CLICK_TUI_STATE`** lines (with leading wall-clock) are preserved alongside Rich output.
- [ ] **Run learn + interactive** (`./osx/macos_mouse_click.py --learn --interactive …`) until the review/edit table is visible.
- [ ] **Plan goal — Down:** press **physical Down once**; confirm highlight moves **exactly one row** down; wait ≥1s.
- [ ] **Plan goal — Up:** press **physical Up once**; confirm highlight moves **exactly one row** up; wait ≥1s.
- [ ] **Edit then arrow:** change **Mode** (or another row), return to table, press **Down** once; confirm highlight and values behave as expected (no spurious cancel).
- [ ] **Wheel / Esc (DEF-003 class):** scroll wheel over the table (or generate Esc-led traffic if you can); confirm session does **not** exit with false **`Cancelled.`** unless you press **Q** / **Ctrl+C** / **Ctrl+D**.
- [ ] **Operator transcript:** short prose with **wall-clock times** and key order (e.g. “15:42:01 table visible → 15:42:03 Down once → 15:42:05 Up once”).
- [ ] **Optional UI ground truth:** screenshot or short recording before/after each arrow if logs and screen ever disagree.
- [ ] **Handoff:** upload **NDJSON log**, **stderr** file, transcript, and environment snapshot; paste **jq** one-liners you used (see [`osx/README.md`](../../../osx/README.md)) and any suspicious line numbers.

### Phase 2: AI execution record

**Recorded:** 2026-04-18 (agent session).

**Phase 1 implementation commit:** `a8c3e93` — `osx/macos_mouse_click.py` (`_debug_tui_ts_wall`, `ts_mono_ns`, stderr `ts_wall` + `MACOS_MOUSE_CLICK_TUI_STATE`), [`osx/README.md`](../../../osx/README.md), [`osx/tests/test_debug_tui_logging_meta.py`](../../../osx/tests/test_debug_tui_logging_meta.py).

**Automated tests (AI-run):**

| Command | Result |
|---------|--------|
| `cd osx && python3 -m pytest tests/test_debug_tui_logging_meta.py -v` | **13 passed**, **1 xfailed** (`test_after_key_down_then_draw_pexpect` — known PTY/CSI limitation per test docstring). |
| `cd osx && python3 -m pytest tests/ -q` | **34 passed**, **3 xfailed** (existing suite; includes PTY / navigation xfails). |

**AI manual / interactive TUI:** not executed as part of this session (requires human terminal and policy-sensitive automation). Evidence from **Operator checklist** above feeds Phase 3 triage.

### Phase 2: Analysis (Phase 3+ inputs)

- **Automated signal:** TUI debug meta tests and subprocess paths **pass**; timestamp fields are **present**, **ISO-parseable**, **`ts_mono_ns` increases** between successive emits, and **stderr wall prefix matches** JSON `ts_wall` in [`test_ts_wall_parseable_ts_mono_increases_stderr_matches_file`](../../../osx/tests/test_debug_tui_logging_meta.py).
- **Remaining risk:** **PTY**-driven **`xfail`** tests still indicate **arrow delivery / timing** under automation is not fully green; Phase 3+ should treat **human bundles** (checklist) as authoritative for **DEF-006/008** class issues until PTY harness improves.
- **Suggested Phase 3+ themes:** (1) stabilize or replace flaky PTY assertions; (2) optional gated **stdin hex** trace only if NDJSON + timestamps still inconclusive; (3) defect-specific fixes if human bundles implicate **DEF-002/003** cancel policy vs **CSI** reader.

---

## Phase 3 and beyond

**Update:** Phase 2 **AI + automated** record and analysis live above; **human** checklist may still yield new bundles. Phase 3+ **implementation tasks** remain **TBD** until those bundles (or CI regressions) justify concrete PRs. Expect items such as: **targeted code fixes**, **new or tightened tests**, **documentation** for edge terminals, or **temporary stdin instrumentation** — chosen from evidence, not from this placeholder alone.

---

## Background: consolidated narrative

The sections below preserve the **original plan-009 narrative**: defect cross-reference, operator story, validation difficulty, acceptance target, evidence bundle, and agent log contract. They explain **why** Phases 1–2 exist.

### Summary by defect

#### DEF-002 — Arrow misread as cancel (**[`def-002`](../defects/def-002-arrow-misread-as-esc.md)**)

After editing a row (e.g. **Mode**), **Up** / **Down** could be mis-parsed as a **lone Escape**, which older handling treated like **cancel** — so the session could **spuriously cancel** when the user only intended to **move the highlight**. Related symptoms included **Count** surprises when re-confirming **learn** after edits.

#### DEF-003 — Wheel / unknown ESC-led input canceled the TUI (**[`def-003`](../defects/def-003-wheel-esc-cancel.md)**)

Mouse **wheel** and other **Escape-led** byte bursts are normal. Treating generic **ESC** traffic as **“quit the editor”** caused **false** **`Cancelled.`** exits. Intended policy: cancel only via **Q**, **Ctrl+C**, or **Ctrl+D**; **Esc** ignored on the table screen.

#### DEF-006 — Multiple presses per row (CSI timing) (**[`def-006`](../defects/def-006-tui-arrow-multi-press.md)**)

**CSI / SS3** arrow sequences can arrive with **large gaps** between bytes. A reader that **timed out per byte** and **broke on the first empty read** could return **`other`** mid-sequence, so **one physical Down** did not reliably advance **one row**; leftover bytes could confuse the **next** read — the highlight felt **“stuck”** until the user pressed again.

#### DEF-008 — Residual double-press and log semantics (**[`def-008`](../defects/def-008-residual-arrow-double-press.md)**)

Even after **DEF-006**, some reports mixed **(a)** real stdin / CSI edge cases with **(b)** **debug log confusion**: **`after_key`** could be emitted **before** **`selected`** was updated for **Up** / **Down**, so **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`** could show **`last_key: down`** while **`selected_index` / row labels** still described the **pre-move** row — operators misread that as “the key did nothing” or “two presses.”

### Cohesive narrative (undesired Up / Down behavior)

**What users wanted:** in the Rich pre-run table, **Up** and **Down** should **only move the highlighted row**, in a **predictable** way, without **exiting** the editor, and with **diagnostics that match** what they see on screen.

**What was observed instead** (at different times, sometimes overlapping):

1. **“I pressed an arrow and the session cancelled.”**  
   **Escape-like** fragments (after edits, from the wheel, or from CSI prefixes) were sometimes interpreted as **cancel** — **DEF-002**, **DEF-003**.

2. **“I pressed Down once but the highlight did not move (or I needed several tries).”**  
   **Multi-byte arrow** sequences were **split in time**; the reader **exited mid-CSI** and returned **`other`**, sometimes leaving **orphan tail** bytes for the next read — **DEF-006**.

3. **“It still feels like two presses / the logs do not match the UI.”**  
   Mix of **remaining timing / PTY / Rich redraw** hypotheses and **`after_key`** records that did **not yet** reflect the **post-arrow** row — **DEF-008**.

So the undesired behavior is not simply “arrows never work,” but **unstable arrow-driven navigation under real terminals**: **false cancels**, **missed or repeated row moves**, and **misleading debug state** relative to the visible highlight — until the fixes and logging adjustments documented in the defect files and **plan 02**.

### Why subjective reports are hard to validate

Phrases like “double press” or “stuck” mix **several failure classes** without time order:

- **Cancel / Esc policy** (**DEF-002**, **DEF-003**) — session ends or mis-handles input that is not “move highlight.”
- **CSI timing** (**DEF-006**) — `read_raw_key` returns **`other`** or splits a sequence; one physical key does not yield one **`down`** / **`up`**.
- **Telemetry vs paint** (**DEF-008**) — logs did not always match the row the operator saw after one arrow (logging order vs `selected`); PTY/Rich timing can still diverge from logs.

Without **structured, time-ordered** evidence tied to **each physical keypress**, an AI coding agent cannot prove which class occurred or whether the **visible** Rich highlight moved.

### Target use case (acceptance)

Authoritative definition: **[Plan goal: Target use case (acceptance)](#plan-goal-target-use-case-acceptance)** at the top of this document. The narrative and validation sections below assume that goal when they discuss “the use case” or “acceptance.”

### Evidence bundle from a running `osx/macos_mouse_click.py` (attach to a bug report or agent session)

Collect **all** of the below from the **same run** (one archive: files + short README snippet is ideal).

#### 1. Exact invocation

- Full command line (`argv`) and **`TERM`**.
- **`python3 -V`**, **`pip show rich`** (or equivalent), and **git commit** (or note “dirty tree” + diffstat) for `osx/macos_mouse_click.py`.

#### 2. TUI debug log (primary machine-readable signal)

Set before launch:

- **`MACOS_MOUSE_CLICK_DEBUG_TUI=1`**
- **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG=/path/to/tui.ndjson`** (must be writable; one session per file keeps parsing simple)

The process appends **one JSON object per line** to that file (NDJSON, **no** prefix). Stderr repeats the same JSON with prefix **`MACOS_MOUSE_CLICK_TUI_STATE `** (see [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py) `_debug_tui_emit` / `_debug_tui_write_line` and operator notes in [`osx/README.md`](../../../osx/README.md)).

#### 3. Stderr capture

Even if you also use **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`**, capture **stderr** to a file: Rich output and **`MACOS_MOUSE_CLICK_TUI_STATE`** lines interleave. Grep for the prefix to isolate state events.

#### 4. Operator action transcript

Short prose with **order and timing**, e.g.: “Editor visible → pressed **physical Down once** → waited 2s → pressed **physical Up once**.” Wall-clock timestamps help correlate with log line order.

#### 5. Optional UI ground truth (harder, best for humans)

- **Screenshot or short screen recording** showing the table before/after each key.
- **Terminal transcript** (raw escape stream): fragile; the repo’s PTY tests parse **bold Setting** labels from transcripts ([`osx/tests/test_rich_table_nav_down_pty.py`](../../../osx/tests/test_rich_table_nav_down_pty.py)) and are often **`xfail`** when capture does not match what a human sees.

#### 6. Optional environment context

Paste with the bundle: **Terminal.app vs iTerm**, **local vs SSH**, **tmux/screen**, **Bluetooth keyboard**, CPU load spikes—any factor that changes stdin chunking or scheduling.

### How an AI agent validates the use case from the bundle

#### Log-based contract (structured)

For **each** claimed physical **Down**:

1. Find an **`after_key`** record with **`"last_key":"down"`** (and similarly **`"up"`** for Up).
2. On **that same line**, check **`selected_index`**, **`row_key`**, and **`setting_label`**: after **DEF-008**, they should describe the **row after** navigation (the highlight the editor logic considers selected).
3. Compare the **prior** **`draw`** line’s **`setting_label`** / **`row_key`** to this **`after_key`**: for **Down**, the label should move **down one row** in the **`editor_row_keys`** order for that config (see [`plan-002` § Pre-run editor](plan-002-macos-mouse-click-terminal-ux.md#pre-run-editor-controls-normative)).

For **Up**, the same checks with **`last_key":"up"`** and movement to the **previous** row.

#### Disambiguation when the use case fails

| Observation | Likely class |
|-------------|----------------|
| **`Cancelled.`** on stderr; session exits | Cancel / Esc / wheel (**DEF-002/003** class) — check whether **`after_key`** shows **`q`** / **`ctrl_c`** vs **`other`**. |
| **`after_key`** with **`last_key":"other"`** (or no **`down`/`up`** when user pressed arrow) | **`read_raw_key`** / CSI timing (**DEF-006** class). |
| **`last_key`** is **`down`** but **`setting_label`** did not advance vs prior **`draw`** | Compare with UI capture; if UI moved but log did not, logging bug; if neither moved, reader or Rich path. |

#### Limits of logs alone

Logs prove **internal state** the script emits; they do not **by themselves** prove what appeared on glass. For “pixel truth,” add **screenshot/video** or a **transcript** and state that the attachment matches the same run as the NDJSON file.

### Operator pain: stderr looks unchanged when state repeats

When a defect causes **`draw`** lines to repeat the **same** `selected_index` / `row_key` / `setting_label` / `value_text` (e.g. highlight did not move after a keypress), **stderr** can look like the terminal is only **redrawing**—successive `MACOS_MOUSE_CLICK_TUI_STATE {"selected_index":0,...,"event":"draw"}` lines are visually identical. That is **literally true** for the JSON body even though the user **did** press a key and expects a **new** row. Without a **per-line time identity**, operators cannot tell “new log emission” from “scrollback” or correlate key timing to log order. **Phase 1** above addresses this.

---

## Optional next instrumentation (if bundles stay inconclusive)

Today, **per-key raw stdin** (hex dump of each `read` boundary) is **not** a first-class product log. If **`after_key`** and **`draw`** are insufficient, the next engineering step is a **temporary** trace (e.g. gated env, or a one-off branch) around **`read_raw_key`** — not required for every report.

---

## Appendix: merged engineering notes (formerly split agent plans)

Condensed from removed **`docs/osx/plans/agent/plan-agent-*.plan.md`** files. **Normative** defect narratives stay in **`docs/osx/defects/`**; **contracts** live in **`osx/tests/`** and **`osx/macos_mouse_click.py`**.

### DEF-006 — CSI / SS3 timing (implemented)

`read_raw_key` previously used a **short per-byte** timeout and **broke on the first empty read** after **`ESC` `[`**, so slow-delivered arrow tails returned **`other`** and left orphan bytes for the next read (**[DEF-006](../defects/def-006-tui-arrow-multi-press.md)**). **Fix:** one **~1 s** monotonic deadline for the whole CSI/SS3 tail; **`wait_char`** until terminator or deadline. **Regression:** **`osx/tests/test_read_raw_key_csi.py`** driving **`osx/tests/csi_pty_child_runner.py`** in a **subprocess** (staggered writes so the PTY does not coalesce the artificial inter-byte gap).

### DEF-008 — “Double press” vs telemetry (implemented)

Per-iteration order is **`draw` → `read_raw_key` → `after_key` → branch**. **`after_key`** must reflect **post-navigation** **`selected`** for **Up**/**Down** so NDJSON matches the visible highlight (**[DEF-008](../defects/def-008-residual-arrow-double-press.md)**). When triaging legacy logs, distinguish **Case A** (arrow recognized; highlight moves on next **`draw`**) from **Case B** (**`last_key`** is **`other`** — real stdin / CSI loss).

### Rich table Down — PTY harness notes

Use a **child process** on a PTY (subprocess, not **`pty.fork`** inside pytest) to inject **CSI**/**SS3** with controlled gaps; assert **Setting** column motion in the transcript. Primary tests: **`osx/tests/test_rich_table_nav_down_pty.py`**, **`osx/tests/test_debug_tui_logging_meta.py`**, runner **`osx/tests/csi_pty_child_runner.py`**. Share helpers across **`osx/tests/`** only after harnesses stabilize (**[plan-003 § Additional automation backlog](plan-003-macos-mouse-click-tui-automation.md#additional-automation-backlog-session-notes-merge)**).

### Plan-009 Phase 3+ — agent checklist proxy (when useful)

An agent pass can: run **`make -C osx test`** (focus PTY / meta suites), assemble **synthetic evidence bundles** (NDJSON + stderr timelines from tests), record **`macos-mouse-click.yml`** CI for the same SHA, map each operator checklist **theme** to **covered / partial / human-only gap**, then replace generic “TBD” in **[Phase 3 and beyond](#phase-3-and-beyond)** with tasks tied to **test names** or **log patterns**. Humans remain for driver-specific stdin chunking or subjective glass truth when automation is inconclusive.

### Rich pre-run layout / resize (DEF-009 class)

**`setwinsize`** redraw and column heuristics: **`osx/tests/test_def009_rich_table_layout_pty.py`**, session note **`hand-off-2026-04-21-rich-pre-run-tui-layout.md`**, product follow-up **[plan-006 — Rich TUI resize](plan-006-macos-mouse-click-rich-tui-terminal-resize.md)**.

---

## Repo pointers (tests and docs)

- **Operator jq recipes and env semantics:** [`osx/README.md`](../../../osx/README.md) (TUI debug section).
- **JSON contract / stderr vs file:** [`osx/tests/test_debug_tui_logging_meta.py`](../../../osx/tests/test_debug_tui_logging_meta.py).
- **PTY + highlight parsing (best-effort UI check):** [`osx/tests/test_rich_table_nav_down_pty.py`](../../../osx/tests/test_rich_table_nav_down_pty.py).
- **Table nav + logging phases (design):** [Appendix § Rich table Down — PTY harness notes](#rich-table-down--pty-harness-notes).
