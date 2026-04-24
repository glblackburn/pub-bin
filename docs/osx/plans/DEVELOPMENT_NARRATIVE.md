# Development Narrative: macOS Mouse Click Utility

This document is a **chronological, human-oriented story** of how **`osx/macos_mouse_click.py`**, its companion **`osx/macos_mouse_click_loop.sh`** operator loop, and the clicker documentation evolved in **`pub-bin`**. It is **not normative**: behavior, acceptance criteria, and defect records remain in **[plan-001-macos-clicker.md](plan-001-macos-clicker.md)** through **[plan-010-macos-mouse-click-learn-points-collect.md](plan-010-macos-mouse-click-learn-points-collect.md)**, **[../defects/](../defects/README.md)**, and **[README.md](README.md)** (plan index).

Sources: `git log` on **`osx/macos_mouse_click.py`** and **`osx/macos_mouse_click_loop.sh`**, plus **`docs/osx/`**, **`osx/tests/`**, and the plan/defect files named below.

## Table of Contents

- [Project overview](#project-overview)
- [Development phases summary](#development-phases-summary)
- [The genesis: why a tiny click utility](#the-genesis-why-a-tiny-click-utility)
- [Phase 1: Utility plan and first shipped script](#phase-1-utility-plan-and-first-shipped-script)
- [Phase 2: Rich pre-run terminal UX and plan 02](#phase-2-rich-pre-run-terminal-ux-and-plan-02)
- [Phase 3: Roadmap expansion (plans 03–08) and operator index](#phase-3-roadmap-expansion-plans-0308-and-operator-index)
- [Phase 4: Pytest, dry-run hook, Makefile, and macOS CI](#phase-4-pytest-dry-run-hook-makefile-and-macos-ci)
- [Phase 5: DEF-006 — CSI / SS3 arrow tails and PTY timing](#phase-5-def-006--csi--ss3-arrow-tails-and-pty-timing)
- [Phase 6: Table navigation agent plans and TUI debug logging](#phase-6-table-navigation-agent-plans-and-tui-debug-logging)
- [Phase 7: DEF-007 / DEF-008 — CLI hygiene and log semantics](#phase-7-def-007--def-008--cli-hygiene-and-log-semantics)
- [Phase 8: Documentation migration to `docs/osx/` and defect extraction](#phase-8-documentation-migration-to-docsosx-and-defect-extraction)
- [Phase 9: Plan 09 — TUI Up / Down phased remediation narrative](#phase-9-plan-09--tui-up--down-phased-remediation-narrative)
- [Phase 10: DEF-009 — Rich pre-run table layout and PTY regression tests](#phase-10-def-009--rich-pre-run-table-layout-and-pty-regression-tests)
- [Phase 11: Plan 10 — `--learn-points` batch anchor collection](#phase-11-plan-10---learn-points-batch-anchor-collection)
- [Phase 12: Coverage tooling and Plan 11 documentation](#phase-12-coverage-tooling-and-plan-11-documentation)
- [Phase 13: Hub polish — agent plan index, Plan 13, unified plan index](#phase-13-hub-polish--agent-plan-index-plan-13-unified-plan-index)
- [Phase 14: Operator loop wrapper (macos_mouse_click_loop.sh)](#phase-14-operator-loop-wrapper-macos_mouse_click_loopsh)
- [Key technical decisions](#key-technical-decisions)
- [Challenges and solutions](#challenges-and-solutions)
- [Project evolution timeline (selected commits)](#project-evolution-timeline-selected-commits)
- [Lessons learned](#lessons-learned)
- [Current state](#current-state)
- [Future considerations](#future-considerations)
- [Conclusion](#conclusion)

## Project overview

**`osx/macos_mouse_click.py`** is a narrow **macOS** utility that posts **synthetic left-button mouse events** via **Quartz** (**PyObjC**), with an optional **Rich**-based **pre-run TTY** for coordinates, counts, and safety prompts. It supports **learn** modes (anchor from a real user click), **non-interactive** automation (**`-Y` / `--yes`** — distinct from **`-y`** coordinate), **dry-run** hooks for **pytest** and CI, **NDJSON** debug logging for TUI sessions, and **batch learn-point collection** (**`--learn-points`**, plan **010**).

**`osx/macos_mouse_click_loop.sh`** is a separate **Bash** harness: an infinite **`while`** loop that invokes the Python clicker with **`-Y`** at **operator-chosen fixed coordinates** (a long-running “buy buildings then spam the cookie” sequence in practice). It is **not** covered by **`pytest`**; it exists to **dogfood** the tool under **`MACOS_MOUSE_CLICK_DEBUG_TUI`** and to keep repetitive sessions out of shell one-liners.

The engineering story is unusually **documentation-heavy for the line count**: numbered **product plans**, **defect detail files**, **agent session plans**, and a **55-test** `pytest` suite under **`osx/tests/`** (collected with repo **`osx/pytest.ini`**).

## Development phases summary

| # | Topic | Start (UTC date) | Stop (UTC date) | Notes |
|---|-------|------------------|-----------------|-------|
| 1 | Utility plan + first script | 2026-04-18 | 2026-04-18 | Plan **01** + **`macos_mouse_click.py`** land together. |
| 2 | Rich pre-run UX + plan **02** closure | 2026-04-18 | 2026-04-18 | **MT-01–MT-09** manual matrix; **DEF-001–003** fixed in code + docs. |
| 3 | Roadmap plans **03–08** + plans README | 2026-04-18 | 2026-04-18 | Deferred work captured as numbered follow-ons (later moved under **`docs/osx/`**). |
| 4 | Pytest + dry-run + Makefile + CI | 2026-04-18 | 2026-04-18 | **`9e96fc8`**: `MACOS_MOUSE_CLICK_DRY_RUN_JSON`, **`osx/Makefile`**, **`osx/tests/`**, macOS CI path. |
| 5 | **DEF-006** arrow CSI / SS3 + PTY runner | 2026-04-18 | 2026-04-18 | Subprocess **PTY** tests; monotonic deadline for escape tails. |
| 6 | Table nav agent plans + TUI NDJSON sink | 2026-04-19 | 2026-04-19 | **`plan-agent-*`** for Up/Down navigation; append debug log file. |
| 7 | **DEF-007** / **DEF-008** | 2026-04-19 | 2026-04-19 | Duplicate **`-n`** rejection; **`after_key`** log alignment. |
| 8 | Move clicker docs to **`docs/osx/`** + **`def-###`** | 2026-04-19 | 2026-04-19 | **`fc8af03`**: split long defect prose out of plan **02**. |
| 9 | Plan **09** phased Up/Down remediation | 2026-04-20 | 2026-04-20 | Narrative + **`ts_wall` / `ts_mono_ns`** in debug streams. |
| 10 | **DEF-009** Rich layout + PTY layout tests | 2026-04-21 | 2026-04-21 | Cooked paint, legacy table, fused panel/table detection. |
| 11 | Plan **10** **`--learn-points`** | 2026-04-22 | 2026-04-22 | **`7e7c6ee`**: batch captures; dry-run stdout contract. |
| 12 | **`pytest-cov`** + Plan **11** gap doc | 2026-04-22 | 2026-04-22 | **`485e420`**: coverage targets + **`macos-mouse-click-coverage-gap.md`**. |
| 13 | Index merge + stub removal + Plan **13** doc | 2026-04-23 | 2026-04-23 | **`29c9246`**: single canonical plan **`README`** under **`docs/osx/plans/`**. |
| 14 | **`macos_mouse_click_loop.sh`** operator loop | 2026-04-20 | 2026-04-22 | Bash wrapper: cookie burst + building buys; **TUI debug** env; coordinates **local to one setup**. |

**Scale signal:** `git log --oneline -- osx/macos_mouse_click.py` shows on the order of **17** commits touching the Python script from first add through **`--learn-points`**. `git log --oneline -- osx/macos_mouse_click_loop.sh` adds **6** commits (**`765f15a`** … **`a40d1b6`**) over **~3 calendar days** in April 2026 — dense burst, not calendar months.

## The genesis: why a tiny click utility

The project started from a **deliberately small surface**: one **macOS** host, one **Python** file, **Quartz** for synthetic clicks, and a clear split between **“what the clicker does”** (coordinates, counts, signals, Accessibility) and **“how the operator configures it in a TTY”** (Rich table, checklists, defect IDs).

Core requirements (from early **[plan-001-macos-clicker.md](plan-001-macos-clicker.md)** intent):

1. **Synthetic left clicks** at learned, fixed, or cursor positions.
2. **Explicit confirmation** paths for interactive use; **`-Y`** for automation (and **never** overload **`-y`** as “yes” because **`-y`** is the **Y coordinate**).
3. **Signals**: **Ctrl+C** / **SIGINT** and **SIGTERM** behave predictably during loops.
4. **Learn mode** that records a **real** user mousedown location (Accessibility-gated) for repeat clicks.
5. **Documented** pip dependencies (**`pyobjc-framework-Quartz`**, optional **`rich`**) and **System Settings → Accessibility** for the invoking terminal.

## Phase 1: Utility plan and first shipped script

**Timeline:** 2026-04-18  
**Focus:** **[plan-001-macos-clicker.md](plan-001-macos-clicker.md)** + **`osx/macos_mouse_click.py`**

### What landed

- **Plan 01** captured language choice (**Python 3** + **PyObjC** vs future Swift/Rust), CLI shape, and safety semantics.
- **`910f272`** introduced **`osx/macos_mouse_click.py`** alongside plan **01** extension — the repo’s **executable spec** and **implementation** began together.

### Design choice called out in plan 01

**Python first** trades a **pip** dependency for iteration speed; the plan explicitly allows **reimplementations** later if the **CLI contract** stays aligned.

## Phase 2: Rich pre-run terminal UX and plan 02

**Timeline:** 2026-04-18  
**Focus:** **[plan-002-macos-mouse-click-terminal-ux.md](plan-002-macos-mouse-click-terminal-ux.md)**

### Operator model

Plan **02** defined the **Rich** pre-run table, **MT-01–MT-09** manual verification rows, and the **Defect summary** table that later pointed at extracted **`def-###`** files.

### Early defect loop on the same day

- **`2319207`** — **DEF-001** / **DEF-002** (console input / arrow misread) fixes in **`macos_mouse_click.py`**, with plan **02** updated to record fix SHAs.
- **`a96d6fe`** — **DEF-003** (wheel / unknown ESC-led input canceling the TUI) — behavior fix + plan **02** documentation.

By end of day **2026-04-18**, plan **02** reached **Closed (v1)** in the sense documented there: the **v1** Rich pre-run program was signed off with manual matrix evidence and triaged deferrals (**DEF-004**, **DEF-005**) routed to later plans.

## Phase 3: Roadmap expansion (plans 03–08) and operator index

**Timeline:** 2026-04-18  
**Focus:** roadmap specs + discoverability

### Plans authored

- **[plan-003-macos-mouse-click-tui-automation.md](plan-003-macos-mouse-click-tui-automation.md)** — pytest / PTY / CI for TUI paths.
- **[plan-004-macos-mouse-click-run-progress-ui.md](plan-004-macos-mouse-click-run-progress-ui.md)** through **[plan-008-macos-mouse-click-stop-during-run.md](plan-008-macos-mouse-click-stop-during-run.md)** — post-start UI, target preview, resize (**DEF-005** deferred), field edit (**DEF-004** deferred), stop-during-**`-Y`** / long runs.

### Index

**`fa31edc`** added a **plans README** under **`docs/plans/`** (historical location) with shortcuts **01–08** — later superseded by the **`docs/osx/plans/README.md`** merge (Phase **13**).

## Phase 4: Pytest, dry-run hook, Makefile, and macOS CI

**Timeline:** 2026-04-18  
**Anchor commit:** **`9e96fc8`** — *macos_mouse_click: dry-run hook, pytest suite, osx Makefile, and macOS CI*

### Why it mattered

Interactive Quartz code is hard to run in CI. The **dry-run** path prints a deterministic **`MACOS_MOUSE_CLICK_DRY_RUN_JSON`** envelope on **stderr** and exits without importing Quartz when configured — enabling **`osx/tests/`** to assert CLI contracts on **macOS** (and selected behaviors under **`pytest`**).

### Artifacts

- **`osx/Makefile`** targets (**`test`**, **`test-quick`**, later **`test-coverage`**).
- Initial **`pytest`** layout evolving into **55** collected tests (see Phase **12** for coverage).

## Phase 5: DEF-006 — CSI / SS3 arrow tails and PTY timing

**Timeline:** 2026-04-18  
**Focus:** multi-byte escape sequences read from raw TTY input

### Problem

Arrow keys can arrive as **CSI** / **SS3** sequences split across reads; naive parsers treated trailing bytes as separate keys (**DEF-006**).

### Response

- **`95dd1a3`**, **`7cfec51`**, **`f76d46b`** — retry reads against a **monotonic deadline**, subprocess **PTY** test harness, and documentation sync in plan **02** / agent plans.

This phase cemented **“PTY tests are part of the product story”** for the Rich table editor.

## Phase 6: Table navigation agent plans and TUI debug logging

**Timeline:** 2026-04-19  
**Focus:** reproducibility and observability

### Agent plans

Kebab-cased **`plan-agent-*`** files (under **`docs/plans/agent/`** at the time, later under **[agent/](agent/README.md)**) captured **phased** work for Rich table **Up/Down** navigation tests and logging (**Phase 2** file sink, meta-tests).

### Logging

- **`01b5d06`** — append **TUI debug** log across processes.
- **`83634f7`** — emit **NDJSON** lines for run/anchor events to stderr and structured log.

These logs became the **ground truth** for correlating **PTY transcripts** with in-process Rich behavior.

## Phase 7: DEF-007 / DEF-008 — CLI hygiene and log semantics

**Timeline:** 2026-04-19  
**Anchor commit:** **`faeb3d8`** — *reject duplicate CLI flags (DEF-007) and align TUI after_key log (DEF-008)*

### Outcomes

- **DEF-007** — reject duplicate **`-n`** / last-wins confusion at argparse level.
- **DEF-008** — align **`after_key`** logging with residual multi-press / CSI semantics so transcripts match operator reality.

Defect rows in plan **02** and **`../defects/`** detail files were closed in tandem (**`1c260b1`** docs commit).

## Phase 8: Documentation migration to `docs/osx/` and defect extraction

**Timeline:** 2026-04-19  
**Anchor commit:** **`fc8af03`** — *move clicker plans to docs/osx and split DEF details*

### What changed

- Numbered plans, handoffs, and clicker **`plan-agent-*`** files moved under **`docs/osx/plans/`** (and **`docs/osx/plans/agent/`**).
- Long-form **DEF-001–009** narratives extracted to **`docs/osx/defects/def-###-….md`**, with plan **02** keeping the **summary table** + workflow.

### Meta plan

**`OSX-DOCS-REORGANIZATION-PLAN.md`** (under **`docs/osx/`**) records the migration checklist and naming rules (**`plan-###`**, **`plan-agent-*`**, **`plan-handoff-*`**).

## Phase 9: Plan 09 — TUI Up / Down phased remediation narrative

**Timeline:** 2026-04-20  
**Focus:** **[plan-009-macos-mouse-click-tui-arrow-navigation-narrative.md](plan-009-macos-mouse-click-tui-arrow-navigation-narrative.md)**

### Content evolution

Plan **09** was expanded into **phased** remediation: acceptance language, **Phase 1 / 2** checklists, and requirements for **automated** evidence tied to debug timestamps.

### Code support

**`a8c3e93`** added **`ts_wall`** and **`ts_mono_ns`** fields to **TUI debug** NDJSON and stderr lines — making PTY + log correlation **testable** (plan **09** explicitly calls for that discipline).

## Phase 10: DEF-009 — Rich pre-run table layout and PTY regression tests

**Timeline:** 2026-04-21  
**Focus:** layout corruption when panel + table regions interact

### Engineering notes

Commits such as **`a0c621f`**, **`3bd517d`**, **`ea264d6`**, **`9bbe5ab`** iterated **stdin** handling, **legacy table** rendering, **cooked** terminal geometry, and **PTY** environment sync.

### Tests

**`91eb8fd`** added **PTY** coverage detecting the **fused panel/table** failure mode described in **[../defects/def-009-rich-pre-run-tui-table-layout-corruption.md](../defects/def-009-rich-pre-run-tui-table-layout-corruption.md)**.

## Phase 11: Plan 10 — `--learn-points` batch anchor collection

**Timeline:** 2026-04-22  
**Anchor commit:** **`7e7c6ee`** — *add learn_collect mode (`--learn-points`)*

### Behavior

Operators record **many** anchor samples in one session: **Rich** path shows a log region under the settings table; **`-Y`** prints **`index x y`** lines; **dry-run** prints deterministic fake samples for CI.

### Documentation

**`fd4496d`** added **[agent/plan-agent-12-learn-points-collect.plan.md](agent/plan-agent-12-learn-points-collect.plan.md)** and index/hub hygiene. Plan **010** is marked **Shipped** in **[README.md](README.md)**.

## Phase 12: Coverage tooling and Plan 11 documentation

**Timeline:** 2026-04-22  
**Anchor commit:** **`485e420`** — *add pytest-cov, Makefile coverage targets, and CI artifacts*

### Outcomes

- **`make -C osx test-coverage`** (and related targets) align with repo patterns used elsewhere in **`pub-bin`**.
- **[../macos-mouse-click-coverage-gap.md](../macos-mouse-click-coverage-gap.md)** captures baseline / gap narrative (**Plan 11**).

## Phase 13: Hub polish — agent plan index, Plan 13, unified plan index

**Timeline:** 2026-04-23  
**Focus:** discoverability and dead-link avoidance

Representative commits:

- **`32e8c84`** — status + dates on **[agent/README.md](agent/README.md)** index.
- **`cfec29f`** — **[agent/plan-agent-13-post-start-click-tests.plan.md](agent/plan-agent-13-post-start-click-tests.plan.md)** (Plan **13**: post-start synthetic click tests — agent plan).
- **`29c9246`** — merged the long **`docs/plans/README.md`** plan index into **`docs/osx/plans/README.md`**; removed legacy **stub** redirects under **`docs/plans/`**; **`docs/plans/README.md`** is now a **short pointer** only.

## Phase 14: Operator loop wrapper (macos_mouse_click_loop.sh)

**Timeline:** 2026-04-20 – 2026-04-22  
**Focus:** long-running **operator automation** next to **`macos_mouse_click.py`** (not a second product binary)

### Why the file exists

The Python tool is deliberately **general** (coordinates, counts, modes). **`macos_mouse_click_loop.sh`** captures a **personal, repetitive session**: the same **`${script_dir}/macos_mouse_click.py`** binary, **`bash`** `set -euET -o pipefail`, and a **`while (true)`** loop so the operator can leave a **Cookie Clicker**–shaped workload running while still exercising **Rich** paths under **`MACOS_MOUSE_CLICK_DEBUG_TUI`** / **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`**.

### Chronology (from `git log -- osx/macos_mouse_click_loop.sh`)

1. **`765f15a`** (**2026-04-20**) — *add osx/macos_mouse_click_loop.sh as a wrapper loop script*  
   - Minimal loop: stamp **`date`**, run **`macos_mouse_click.py`** at fixed **`-x/-y`** with **`-n 3000 -Y`**, stamp again, **`sleep 25`**.  
   - **`MACOS_MOUSE_CLICK_DEBUG_TUI=yes`** and **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG=debug.json`** passed per invocation (later iterations move these to **`export`** at the top of the loop body for readability).

2. **`32d5820`** (**2026-04-20**) — *add buy clicks*  
   - Inserted additional **`-Y`** blocks (fixed coordinates) ahead of the long cookie burst — the script becomes a **sequenced macro** (buy rows + cookie spam).

3. **`22f08fd`** (**2026-04-21**) — *add other buy clicks*  
   - Further expanded the buy ladder so the loop mirrors more of the in-game purchase strip.

4. **`43a727d`** (**2026-04-22**) — *docs(osx): sync plans 003/004/006/008…* (includes **`osx:`** hunk)  
   - **Commented out** several mid-loop **purchase** invocations so the checked-in macro stayed closer to what the **plan-003**/**004**/**006**/**008** doc sync described as the **current** operator + test story (the cookie burst remained the heavy tail).

5. **`a40d1b6`** (**2026-04-22**) — *chore(osx): extend macos_mouse_click_loop automation sequence*  
   - Re-enabled / extended the ladder (**time machine**, **portal**, **temple**–**cursor** buys) and reshaped the shell so the sequence is easier to read line-by-line.

### Current shape (maintenance note)

The loop still encodes **machine-specific Quartz coordinates** and **sleep** spacing (**`sleep 30`** after the cookie burst in the tree at narrative time). That is intentional for a **repo-local operator harness**: it documents *how the author ran the tool*, not a portable contract. Anyone reusing it should treat coordinates like **secrets** — wrong for CI, fine for a **bounded personal target**.

## Key technical decisions

1. **Quartz via PyObjC** — fastest path to **CGEvent**-level control in Python; Accessibility remains an OS policy gate.
2. **Rich optional** — script must degrade when **`rich`** is missing; **dry-run** avoids Quartz in CI paths.
3. **Separate `-Y` vs `-y`** — **`argparse`** shape prevents the classic **“yes vs Y pixel”** footgun.
4. **Defect split** — keep **plan-002** as the **operator hub** for the TTY while moving long narratives to **`def-###`** files.
5. **Documentation colocation** — **`docs/osx/`** sits beside **`osx/`** in mental navigation: hub → plans → defects → script.
6. **Bash loop beside Python** — keep long-running **`-Y`** sequences in **`macos_mouse_click_loop.sh`** so **`macos_mouse_click.py`** stays a **library-grade CLI** without baking one game’s coordinate ladder into Python.

## Challenges and solutions

| Challenge | Response |
|-----------|----------|
| **CSI / SS3** split reads on arrows | Monotonic read deadlines + PTY subprocess tests (**DEF-006**). |
| **CI without Quartz** | **`MACOS_MOUSE_CLICK_DRY_RUN=1`** / **`--dry-run-after-start`** JSON + stdout contracts. |
| **Layout corruption** in Rich pre-run | Iterative terminal geometry + PTY transcript tests (**DEF-009**). |
| **Doc drift** vs implementation | Numbered plans + **Closed (v1)** / **Shipped** semantics on **[README.md](README.md)**; handoffs for cross-cutting sessions (**[plan-handoff-2026-04-18-linkedin-macos-clicker-draft.md](plan-handoff-2026-04-18-linkedin-macos-clicker-draft.md)**). |
| **Legacy URLs** after `docs/plans/` stub removal | Prefer **`docs/osx/`** tree links; thin **`docs/plans/README.md`** pointer for repo visitors. |
| **Hardcoded buy grid** in **`macos_mouse_click_loop.sh`** | Accept as **operator-local**; edit **`-x/-y`** per monitor layout; keep **`-Y`** + **debug** env patterns for Rich investigation. |

## Project evolution timeline (selected commits)

Chronological **high-signal** anchors (read with **`git show <hash>`**):

- **`7ec5824`** — add **plan 01** (utility plan).
- **`910f272`** — add **`osx/macos_mouse_click.py`** + extend plan **01**.
- **`93a1f15`** — add **plan 02** (Rich TTY).
- **`9e96fc8`** — **pytest** + **dry-run** + **`osx/Makefile`** + CI wiring.
- **`95dd1a3`** / **`7cfec51`** — **DEF-006** CSI tail + monotonic deadline.
- **`fc8af03`** — move plans/defects to **`docs/osx/`**.
- **`faeb3d8`** — **DEF-007** / **DEF-008** fixes.
- **`a8c3e93`** — **TUI debug** timestamps (**plan 09** alignment).
- **`3bd517d`** / **`9bbe5ab`** — **DEF-009** layout fixes.
- **`7e7c6ee`** — **`--learn-points`** shipped.
- **`485e420`** — coverage Makefile / **`pytest-cov`** integration.
- **`29c9246`** — unified **`docs/osx/plans/README.md`** index; stub removal.
- **`765f15a`** / **`32d5820`** / **`22f08fd`** — introduce and grow **`macos_mouse_click_loop.sh`** buy + cookie sequence.
- **`43a727d`** — trim commented buy lines in the loop while syncing roadmap plans to **shipped** test reality.
- **`a40d1b6`** — extend / un-comment loop steps (**time machine**, **portal**, **temple**–**cursor**).

## Lessons learned

1. **Small tools still earn big docs** when the risk surface is **Accessibility**, **raw TTY**, and **operator error**.
2. **Dry-run contracts** pay off immediately: the same flags operators use can drive **CI** without Quartz.
3. **PTY tests** are expensive to write but **cheaper** than repeated manual **MT-** passes for regressions.
4. **Split “summary vs narrative”** for defects — operators want a **table** in plan **02**; engineers want **`def-###`** detail without scrolling a novel inline.
5. **Colocate docs with code** (**`docs/osx/`**) reduced cross-directory confusion once migration completed.
6. **Keep “toy orchestration” in shell** — the **`while true`** buy ladder belongs in **`macos_mouse_click_loop.sh`**, which makes the boundary between **product** (Python) and **personal automation** (Bash + coordinates) obvious to future readers.

## Current state

**As of the last update to this narrative (April 2026):**

- **Implementation:** **[osx/macos_mouse_click.py](../../../osx/macos_mouse_click.py)** — module docstring points to **[../README.md](../README.md)** for navigation.
- **Operator loop:** **[osx/macos_mouse_click_loop.sh](../../../osx/macos_mouse_click_loop.sh)** — Bash **`while`** harness invoking the Python clicker with **`-Y`**; **hardcoded coordinates**; smoke-tested by the maintainer, not **`pytest`**.
- **Plans:** **plan-001** **Shipped**; **plan-002** **Closed (v1)**; **plan-010** **Shipped**; **plan-003**–**009** **Roadmap** rows on **[README.md](README.md)**; **Plan 13** tracked as **[agent/plan-agent-13-post-start-click-tests.plan.md](agent/plan-agent-13-post-start-click-tests.plan.md)** (post-start click tests).
- **Defects:** **DEF-001**–**DEF-009** detail files under **`../defects/`**; summary table in **plan-002**.
- **Tests:** **55** tests collected under **`osx/tests/`** (see **`make -C osx test-quick`**).
- **Marketing handoff:** LinkedIn draft session captured in **[plan-handoff-2026-04-18-linkedin-macos-clicker-draft.md](plan-handoff-2026-04-18-linkedin-macos-clicker-draft.md)** (revision **5** aligned to **`docs/osx/`** links).

## Future considerations

Drawn from roadmap plans and **[plan-001-macos-clicker.md](plan-001-macos-clicker.md)** “Future” language:

1. **TUI automation / CI** — deepen **plan-003** items (markers, PTY matrix, timing discipline).
2. **Post-start progress UI** — **plan-004** scope once pre-run path is stable.
3. **Target preview** — **plan-005** “show before run” overlays.
4. **Resize / reflow** — **plan-006** (**DEF-005** context) for **SIGWINCH** behavior.
5. **Field-edit UX** — **plan-007** (**DEF-004** deferred narrative).
6. **Stop during long `-Y` runs** — **plan-008** operator safety.
7. **Arrow navigation completion** — **plan-009** remaining phases / evidence bars.
8. **Coverage closure** — **Plan 11** gap doc vs **`pytest-cov`** reports.
9. **Optional rewrite** — Swift / Rust / thin wrapper while preserving **CLI semantics** (plan **01**).

## Conclusion

The macOS clicker effort stayed intentionally **small in binary ambition** but **large in process**: a **single Python script**, a **small Bash loop** for long-running **`-Y`** sessions, plus **plans**, **defects**, **agent notes**, **PTY-based tests**, and a **`docs/osx/`** hub that matches where operators look for **`osx/`** code.

The arc mirrors the React2Shell narrative pattern: **genesis → phased delivery → test and doc hardening → migration/consolidation → explicit future work**. For this repo, the **canonical spec** remains the **`plan-###`** files — this document only tells **how the pieces landed in time**.

---

**Project status:** Active (roadmap plans open; script shipped features include **`--learn-points`**).  
**Last updated:** 2026-04-23 (narrative matches `git` history through **`29c9246`** / **`485e420`** / **`7e7c6ee`** / **`a40d1b6`** loop era).  
**Test collection:** 55 tests under **`osx/tests/`** (per `pytest --collect-only`).  
**Maintainer:** Project owner / contributors per **`pub-bin`** history.
