---
todos:
  - id: add-plan-04
    content: "Write docs/osx/plans/plan-004-macos-mouse-click-run-progress-ui.md (goals, phases, matrix)"
    status: completed
  - id: phase-04-spec-finalize
    content: "Finalize layout: settings panel + progress widget vs discrete stderr lines"
    status: pending
  - id: phase-04-implement-summary
    content: "Implement post-S Rich settings summary (TTY + rich); plain fallback"
    status: pending
  - id: phase-04-implement-progress
    content: "Implement throttled in-run progress (finite + infinite); Ctrl+C clean stop — never log/update every click for high N or delay=0"
    status: pending
  - id: phase-04-docs-plan02
    content: "Cross-link plan 02/03; update manual QA notes for new stderr patterns"
    status: pending
isProject: false
---

# Plan 04: Run-time Rich output (after **S** / clicker start)

> **Frozen — superseded by [plan-020-uber-true-up](plan-020-uber-true-up.md) on 2026-05-06.**
>
> This document is **read-only**. Do not add new work, status updates, or fix references here.
> Open work moved to plan-020. New features → new `plan-###`. Problems → defects under
> [`docs/osx/defects/`](../defects/) whose `related_plans:` references this file and `plan-020`.

This document specifies **post-start** terminal UX for [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py): once the user confirms **Start** (**S**) in the pre-run editor (plan **02**) or starts via **`-Y`** / legacy paths, the tool should present **clear, attractive output** of the **resolved run settings** and **visible progress** through the synthetic click loop (and learn-phase messaging where applicable).

It builds on **[`plan-002-macos-mouse-click-terminal-ux.md`](plan-002-macos-mouse-click-terminal-ux.md)** (pre-run Rich TUI), **[`plan-001-macos-clicker.md`](plan-001-macos-clicker.md)** (click semantics, signals), and may share styling ideas with **[`plan-003-macos-mouse-click-tui-automation.md`](plan-003-macos-mouse-click-tui-automation.md)** (Rich usage patterns).

**Relationship to plan 08:** Fancy progress is **secondary** if the operator cannot **reliably stop** an infinite or very fast run (see **[plan 08](plan-008-macos-mouse-click-stop-during-run.md)** — stop file, optional hotkey, and other overrides). Plan 04 assumes stop plumbing already allows the loop to exit cleanly once **`shutdown_requested()`** is set.

## Table of contents

- [Operator constraints (product)](#operator-constraints-product)
- [Goals](#goals)
- [Behavior matrix](#behavior-matrix)
- [UX design](#ux-design)
- [Implementation touchpoints](#implementation-touchpoints)
- [Phases](#phases)
- [Risks and constraints](#risks-and-constraints)
- [Manual QA (after implementation)](#manual-qa-after-implementation)

## Operator constraints (product)

Synthetics can be delivered **much faster** than a human can read the screen (**large `-n`**, **`delay=0`**, **`count=0` infinite**). For plan 04 to stay credible:

1. **No per-click logging or Rich refresh by default** for high-rate runs. Use **throttled** updates: e.g. every **N** clicks (where **N** scales with total count or rate), and/or every **T** seconds wall time, with caps so **2000** clicks do not emit **2000** lines.
2. **Infinite mode** needs a **clear “still running”** signal at the same throttled cadence (elapsed time + total clicks since start), not a fake percent bar.
3. **Escape hatch** when the user is “stuck” in a tight loop is **not** primarily a plan 04 UI problem — it belongs in **[plan 08](plan-008-macos-mouse-click-stop-during-run.md)** (stop file, **`kill -INT`**, optional **Escape** when a TTY exists, optional **mouse-movement** cancel if product accepts it). Plan 04 must **not** make stop harder (e.g. heavy `Live` that starves poll points).

Implementation detail: today **`sleep_interruptible`** returns immediately when **`delay <= 0`**, so there is **no** sub-interval polling during a zero sleep; tight loops rely on checks **between** iterations and **signals**. Throttled UI work must keep the same **O(1)** overhead per click budget the operator expects.

## Goals

1. **Settings summary after start:** Immediately after the pre-run path hands off to Quartz (or right after the current **Running:** line for `-Y` / non-TTY), print a **structured summary** (mode, anchor strategy, x/y if fixed, count, delay, sources if useful) using **Rich** (`Panel` / `Table`) when the same conditions as the pre-run editor allow (**TTY** + **`rich`** + sensible stdout).
2. **Progress during the run (throttled):** For **finite** counts, show **progress** only at a **bounded rate** (e.g. `rich.progress` or discrete stderr lines: “click **k** / **N**”, elapsed time, optional ETA). For **infinite** (`count == 0`), show an **indeterminate** or “since start” counter at the same throttled cadence — not every synthetic, not a lying percent bar. Scaling rules (every 100 of 2000, time-based floors, etc.) are a **Phase 1** product decision.
3. **Consistent fallback:** **Non-TTY**, **missing `rich`**, or **`-Y`** paths keep **plain stderr** lines (or a single compact block) so scripting and pipes are not broken; no mandatory cursor motion on pipes.
4. **Clean shutdown:** On **Ctrl+C** / SIGINT / SIGTERM, progress UI should **tear down cleanly** (no orphaned Live cursor); final line explains stop (align with plan 01).

## Behavior matrix

| Condition | Presentation |
|-----------|----------------|
| **TTY** + **stdout TTY** + **`rich`** + user came from **Rich pre-run** (`can_tui` path) | Full **Rich** settings **Panel** + **progress** widget for the run |
| **`-Y`** / **scripting** | Keep **one-line** or **minimal** stderr summary + optional compact progress only if it does not flood logs (product decision in Phase 1) |
| **Not a TTY** or **no `rich`** | **Plain** stderr (current style or slightly improved text block); **no** `Live` |

## UX design

- **Placement:** First paint **after** “start” is committed — e.g. immediately after `import_quartz()` + resolved config is final, **before** learn tap wait or first synthetic click.
- **Content — settings block:** Mirror pre-run table columns where possible (**Mode**, **Count**, **Delay**, **Anchor** description: learn / fixed coords / at-cursor).
- **Content — progress:** Update on a **throttle** (every **N** iterations and/or every **T** ms — see [Operator constraints](#operator-constraints-product)); when **`sleep_interruptible`** runs with positive delay, optional sub-line status during long sleeps is OK; when **`delay` is 0**, do **not** assume per-iteration UI is affordable.
- **Learn mode:** Keep existing “waiting for anchor” / “anchor recorded” messages but optionally **wrap** in `Panel` or prefix with consistent **Rich** styles when Rich path is active.
- **Reference look:** Reuse vocabulary from **`what-is-left.py`** and plan **02** (border styles, cyan/green/dim roles).

## Implementation touchpoints

- **Primary file:** [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py) — `main()` after editor; `run_synthetic_loop`, `run_learn_flow`, `run_fixed_or_cursor_flow`; possibly a small helper module later (e.g. `osx/mclick_run_ui.py`) if `main()` grows too large.
- **Lazy Rich:** Import **Rich** only on the “pretty run” path (same idea as pre-run editor) so `--help` and `-Y` cold paths stay light.
- **Signals:** `shutdown_requested()` already exists; progress renderer must **poll** or **check** between sleeps so SIGINT still works.

## Phases

### Phase 1 — Design lock-in

- Choose **Progress** vs **Live** vs **discrete Panel refresh** (Live is heavier but prettier; discrete lines are simpler for infinite mode).
- Confirm **`-Y`** rule: progress **off** by default vs **compact** one-line progress every *k* clicks.
- Lock **throttle parameters**: min interval between UI updates, **`N`** clicks between logs for large finite **`-n`**, and behavior for **`delay=0`** (stderr-only ticks vs silent until stop).

### Phase 2 — Settings summary

- Implement `print_run_summary_rich(cfg)` (name TBD) called once at run start when conditions match matrix.
- Plain-text `print_run_summary_plain(cfg)` for fallback.

### Phase 3 — Progress loop

- Thread **throttled** progress updates through `run_synthetic_loop` (and learn warmup sleeps if desired); never **O(every click)** logging for high-volume paths unless explicitly opted in for debugging.
- Ensure **infinite** mode has a clear **“running until interrupt”** display at the throttled cadence; align wording with **[plan 08](plan-008-macos-mouse-click-stop-during-run.md)** stop surfaces.
- On shutdown: flush final state + “Stopped.” with consistent styling.

### Phase 4 — Docs and manual QA

- Update plan **02** manual checklist notes if stderr patterns change materially.
- Link this plan from plan **02** **Implementation touchpoints**.

## Risks and constraints

- **`rich.live.Live`** + **signal** + **raw tty** history: pre-run editor uses `termios`; ensure run phase does not leave terminal in raw mode.
- **Performance:** High click rates + `delay=0` must not spend more time rendering than clicking; **throttle** UI updates.
- **Tests:** Plan **03** automation may need a “quiet” env flag to disable Live for CI; document alongside dry-run hook.

## Manual QA (after implementation)

- TTY + Rich: **S** after editor — summary appears, progress advances, **Ctrl+C** exits cleanly.
- **`-Y`:** behavior matches Phase 1 decision (minimal noise).
- **Pipe / non-TTY:** no escape garbage; scriptable exit codes unchanged.

