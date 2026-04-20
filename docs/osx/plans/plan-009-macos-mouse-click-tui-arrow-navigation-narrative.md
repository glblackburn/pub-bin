---
todos:
  - id: add-plan-09-narrative
    content: "Add plan-009 consolidated narrative for Rich TUI Up/Down arrow issues (DEF-002/003/006/008)"
    status: completed
  - id: add-plan-09-evidence-bundle
    content: "Document evidence bundle and agent validation for one-press Up/Down (plan-09)"
    status: completed
  - id: phase-1-tui-debug-timestamps
    content: "Phase 1: add wall-clock (and optional monotonic) timestamps to TUI debug JSON + stderr MACOS_MOUSE_CLICK_TUI_STATE lines"
    status: pending
isProject: false
---

# Plan 09: Rich TUI arrow navigation — consolidated problem narrative

This document **primarily summarizes** how **Up** / **Down** misbehavior in the Rich pre-run table was **described** across **DEF-002**, **DEF-003**, **DEF-006**, and **DEF-008**, and points to the canonical specs and defect detail files. **Phase 1** below records a **planned** logging enhancement (timestamps) to make operator and agent validation easier; implementation is tracked in frontmatter **`phase-1-tui-debug-timestamps`**.

**Normative UX and checklist:** **[`plan-002-macos-mouse-click-terminal-ux.md`](plan-002-macos-mouse-click-terminal-ux.md)**  
**Per-defect detail:** **[`../defects/README.md`](../defects/README.md)**  
**Engineering notes:** **[`agent/plan-agent-def-006-tui-arrow-keys.plan.md`](agent/plan-agent-def-006-tui-arrow-keys.plan.md)**, **[`agent/plan-agent-arrow-key-double-press-analysis.plan.md`](agent/plan-agent-arrow-key-double-press-analysis.plan.md)**, **[`agent/plan-agent-new-test-up-down-navigation.plan.md`](agent/plan-agent-new-test-up-down-navigation.plan.md)**

---

## Summary by defect

### DEF-002 — Arrow misread as cancel (**[`def-002`](../defects/def-002-arrow-misread-as-esc.md)**)

After editing a row (e.g. **Mode**), **Up** / **Down** could be mis-parsed as a **lone Escape**, which older handling treated like **cancel** — so the session could **spuriously cancel** when the user only intended to **move the highlight**. Related symptoms included **Count** surprises when re-confirming **learn** after edits.

### DEF-003 — Wheel / unknown ESC-led input canceled the TUI (**[`def-003`](../defects/def-003-wheel-esc-cancel.md)**)

Mouse **wheel** and other **Escape-led** byte bursts are normal. Treating generic **ESC** traffic as **“quit the editor”** caused **false** **`Cancelled.`** exits. Intended policy: cancel only via **Q**, **Ctrl+C**, or **Ctrl+D**; **Esc** ignored on the table screen.

### DEF-006 — Multiple presses per row (CSI timing) (**[`def-006`](../defects/def-006-tui-arrow-multi-press.md)**)

**CSI / SS3** arrow sequences can arrive with **large gaps** between bytes. A reader that **timed out per byte** and **broke on the first empty read** could return **`other`** mid-sequence, so **one physical Down** did not reliably advance **one row**; leftover bytes could confuse the **next** read — the highlight felt **“stuck”** until the user pressed again.

### DEF-008 — Residual double-press and log semantics (**[`def-008`](../defects/def-008-residual-arrow-double-press.md)**)

Even after **DEF-006**, some reports mixed **(a)** real stdin / CSI edge cases with **(b)** **debug log confusion**: **`after_key`** could be emitted **before** **`selected`** was updated for **Up** / **Down**, so **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`** could show **`last_key: down`** while **`selected_index` / row labels** still described the **pre-move** row — operators misread that as “the key did nothing” or “two presses.”

---

## Cohesive narrative (undesired Up / Down behavior)

**What users wanted:** in the Rich pre-run table, **Up** and **Down** should **only move the highlighted row**, in a **predictable** way, without **exiting** the editor, and with **diagnostics that match** what they see on screen.

**What was observed instead** (at different times, sometimes overlapping):

1. **“I pressed an arrow and the session cancelled.”**  
   **Escape-like** fragments (after edits, from the wheel, or from CSI prefixes) were sometimes interpreted as **cancel** — **DEF-002**, **DEF-003**.

2. **“I pressed Down once but the highlight did not move (or I needed several tries).”**  
   **Multi-byte arrow** sequences were **split in time**; the reader **exited mid-CSI** and returned **`other`**, sometimes leaving **orphan tail** bytes for the next read — **DEF-006**.

3. **“It still feels like two presses / the logs do not match the UI.”**  
   Mix of **remaining timing / PTY / Rich redraw** hypotheses and **`after_key`** records that did **not yet** reflect the **post-arrow** row — **DEF-008**.

So the undesired behavior is not simply “arrows never work,” but **unstable arrow-driven navigation under real terminals**: **false cancels**, **missed or repeated row moves**, and **misleading debug state** relative to the visible highlight — until the fixes and logging adjustments documented in the defect files and **plan 02**.

---

## Why subjective reports are hard to validate

Phrases like “double press” or “stuck” mix **several failure classes** without time order:

- **Cancel / Esc policy** (**DEF-002**, **DEF-003**) — session ends or mis-handles input that is not “move highlight.”
- **CSI timing** (**DEF-006**) — `read_raw_key` returns **`other`** or splits a sequence; one physical key does not yield one **`down`** / **`up`**.
- **Telemetry vs paint** (**DEF-008**) — logs did not always match the row the operator saw after one arrow (logging order vs `selected`); PTY/Rich timing can still diverge from logs.

Without **structured, time-ordered** evidence tied to **each physical keypress**, an AI coding agent cannot prove which class occurred or whether the **visible** Rich highlight moved.

---

## Target use case (acceptance)

- **Down (once):** the **next** row in the settings table is **highlighted** (focus moves down by one row).
- **Up (once):** the **previous** row is **highlighted** (focus moves up by one row).

“Highlighted” means the same notion as the operator: the **selected** row in the Rich table (bold / focus styling on the **Setting** column in practice).

---

## Evidence bundle from a running `osx/macos_mouse_click.py` (attach to a bug report or agent session)

Collect **all** of the below from the **same run** (one archive: files + short README snippet is ideal).

### 1. Exact invocation

- Full command line (`argv`) and **`TERM`**.
- **`python3 -V`**, **`pip show rich`** (or equivalent), and **git commit** (or note “dirty tree” + diffstat) for `osx/macos_mouse_click.py`.

### 2. TUI debug log (primary machine-readable signal)

Set before launch:

- **`MACOS_MOUSE_CLICK_DEBUG_TUI=1`**
- **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG=/path/to/tui.ndjson`** (must be writable; one session per file keeps parsing simple)

The process appends **one JSON object per line** to that file (NDJSON, **no** prefix). Stderr repeats the same JSON with prefix **`MACOS_MOUSE_CLICK_TUI_STATE `** (see [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py) `_debug_tui_emit` / `_debug_tui_write_line` and operator notes in [`osx/README.md`](../../../osx/README.md)).

### 3. Stderr capture

Even if you also use **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`**, capture **stderr** to a file: Rich output and **`MACOS_MOUSE_CLICK_TUI_STATE`** lines interleave. Grep for the prefix to isolate state events.

### 4. Operator action transcript

Short prose with **order and timing**, e.g.: “Editor visible → pressed **physical Down once** → waited 2s → pressed **physical Up once**.” Wall-clock timestamps help correlate with log line order.

### 5. Optional UI ground truth (harder, best for humans)

- **Screenshot or short screen recording** showing the table before/after each key.
- **Terminal transcript** (raw escape stream): fragile; the repo’s PTY tests parse **bold Setting** labels from transcripts ([`osx/tests/test_rich_table_nav_down_pty.py`](../../../osx/tests/test_rich_table_nav_down_pty.py)) and are often **`xfail`** when capture does not match what a human sees.

### 6. Optional environment context

Paste with the bundle: **Terminal.app vs iTerm**, **local vs SSH**, **tmux/screen**, **Bluetooth keyboard**, CPU load spikes—any factor that changes stdin chunking or scheduling.

---

## How an AI agent validates the use case from the bundle

### Log-based contract (structured)

For **each** claimed physical **Down**:

1. Find an **`after_key`** record with **`"last_key":"down"`** (and similarly **`"up"`** for Up).
2. On **that same line**, check **`selected_index`**, **`row_key`**, and **`setting_label`**: after **DEF-008**, they should describe the **row after** navigation (the highlight the editor logic considers selected).
3. Compare the **prior** **`draw`** line’s **`setting_label`** / **`row_key`** to this **`after_key`**: for **Down**, the label should move **down one row** in the **`editor_row_keys`** order for that config (see [`plan-002` § Pre-run editor](plan-002-macos-mouse-click-terminal-ux.md#pre-run-editor-controls-normative)).

For **Up**, the same checks with **`last_key":"up"`** and movement to the **previous** row.

### Disambiguation when the use case fails

| Observation | Likely class |
|-------------|----------------|
| **`Cancelled.`** on stderr; session exits | Cancel / Esc / wheel (**DEF-002/003** class) — check whether **`after_key`** shows **`q`** / **`ctrl_c`** vs **`other`**. |
| **`after_key`** with **`last_key":"other"`** (or no **`down`/`up`** when user pressed arrow) | **`read_raw_key`** / CSI timing (**DEF-006** class). |
| **`last_key`** is **`down`** but **`setting_label`** did not advance vs prior **`draw`** | Compare with UI capture; if UI moved but log did not, logging bug; if neither moved, reader or Rich path. |

### Limits of logs alone

Logs prove **internal state** the script emits; they do not **by themselves** prove what appeared on glass. For “pixel truth,” add **screenshot/video** or a **transcript** and state that the attachment matches the same run as the NDJSON file.

### Operator pain: stderr looks “unchanged” when state repeats

When a defect causes **`draw`** lines to repeat the **same** `selected_index` / `row_key` / `setting_label` / `value_text` (e.g. highlight did not move after a keypress), **stderr** can look like the terminal is only **redrawing**—successive `MACOS_MOUSE_CLICK_TUI_STATE {"selected_index":0,...,"event":"draw"}` lines are visually identical. That is **literally true** for the JSON body even though the user **did** press a key and expects a **new** row. Without a **per-line time identity**, operators cannot tell “new log emission” from “scrollback” or correlate key timing to log order.

---

## Phase 1 (planned): timestamps on every TUI debug emission

**Goal:** make each **`MACOS_MOUSE_CLICK_TUI_STATE`** emission **obviously distinct** and **time-correlatable** in both the **NDJSON log file** and **stderr**, without changing Rich table rendering.

**Tasks (implementation — not done in this narrative doc alone):**

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
3. **Docs** — update [`osx/README.md`](../../../osx/README.md) (jq examples, field dictionary) and **[`plan-agent-new-test-up-down-navigation.plan.md`](agent/plan-agent-new-test-up-down-navigation.plan.md)** / **[`plan-002`](plan-002-macos-mouse-click-terminal-ux.md)** cross-links if the public contract changes.
4. **Tests** — extend [`osx/tests/test_debug_tui_logging_meta.py`](../../../osx/tests/test_debug_tui_logging_meta.py) (and any fixture strings that assert exact JSON) for required keys/types; keep **log file** lines **jq-friendly** (one JSON object per line; new fields additive).

**Non-goals for Phase 1:** raw stdin hex dumps (deferred to optional deeper instrumentation below); changing **Rich** layout or adding interactive TUI “debug HUD.”

**Tracking:** frontmatter todo **`phase-1-tui-debug-timestamps`** above; mark **`completed`** when shipped and note **Fix commit** in **plan 02** / defect rows if tied to a reopened DEF.

---

## Optional next instrumentation (if bundles stay inconclusive)

Today, **per-key raw stdin** (hex dump of each `read` boundary) is **not** a first-class product log. If **`after_key`** and **`draw`** are insufficient, the next engineering step is a **temporary** trace (e.g. gated env, or a one-off branch) around **`read_raw_key`** — not required for every report.

---

## Repo pointers (tests and docs)

- **Operator jq recipes and env semantics:** [`osx/README.md`](../../../osx/README.md) (TUI debug section).
- **JSON contract / stderr vs file:** [`osx/tests/test_debug_tui_logging_meta.py`](../../../osx/tests/test_debug_tui_logging_meta.py).
- **PTY + highlight parsing (best-effort UI check):** [`osx/tests/test_rich_table_nav_down_pty.py`](../../../osx/tests/test_rich_table_nav_down_pty.py).
- **Agent design for table nav + logging phases:** [`agent/plan-agent-new-test-up-down-navigation.plan.md`](agent/plan-agent-new-test-up-down-navigation.plan.md).
