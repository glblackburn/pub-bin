---
todos:
  - id: add-plan-06
    content: "Write docs/osx/plans/plan-006-macos-mouse-click-rich-tui-terminal-resize.md"
    status: completed
  - id: phase-06-spec-sigwinch
    content: "Specify SIGWINCH vs polling; min terminal width messaging"
    status: pending
  - id: phase-06-implement-reflow
    content: "Refactor pre-run editor to re-measure Console width/height and redraw table/panel"
    status: pending
  - id: phase-06-regression-mt08
    content: "Re-run MT-08; update DEF-005 / plan 02 if behavior changes"
    status: pending
isProject: false
---

# Plan 06: Rich pre-run TUI and terminal resize (SIGWINCH / reflow)

This document tracks **responsive layout** for the Rich **pre-run editor** in [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py): when the operator **resizes the terminal** (narrower, wider, shorter, taller), the **Panel** + **Table** should **reflow** instead of leaving a stale layout with **awkward wrapping** or a **fixed visual size** that no longer matches the window.

It is motivated by **DEF-005** in **[`plan-002-macos-mouse-click-terminal-ux.md`](plan-002-macos-mouse-click-terminal-ux.md)** (operator **MT-08**, **2026-04-18**): shrinking caused **weird wrap**; expanding the window **did not** grow the rendered UI. Work is **deferred** from v1; no script fix ships until this plan is executed.

Related: **[`plan-004-macos-mouse-click-run-progress-ui.md`](plan-004-macos-mouse-click-run-progress-ui.md)** (post-start **Live** / progress patterns may reuse ideas), **[`plan-003-macos-mouse-click-tui-automation.md`](plan-003-macos-mouse-click-tui-automation.md)** (PTY tests may need **size** assertions after reflow exists).

## Table of contents

- [Problem](#problem)
- [Goals](#goals)
- [Constraints](#constraints)
- [Design options](#design-options)
- [Phases](#phases)
- [Manual QA](#manual-qa)

## Problem

The editor currently paints the Rich layout **as if terminal dimensions were fixed** at first draw. Resizing the emulator window **does not** trigger a clean **re-layout**:

- **Shrink:** text and table columns **wrap** in ways that hurt readability (**DEF-005**).
- **Expand:** the UI **stays** at an **effective old width** (operator report during **MT-08**).

## Goals

1. On **terminal resize**, **re-query** usable width/height (**Rich** `Console.size` / `Console.width` **or** `shutil.get_terminal_size` where appropriate) and **redraw** the main table + help/footer so the layout matches the **current** window.
2. Preserve **existing key model** (plan **02**): **Up**/**Down**, **Enter**, **S** / **Q** / **Ctrl+C** / **Ctrl+D**, **R**, **Esc** ignored — reflow must **not** swallow input or reset selection unexpectedly.
3. Define a **minimum width** below which we show a **short warning** (or compact single-column mode) rather than a broken table.
4. **No change** to **`-Y`**, pipe, or non-Rich paths.

## Constraints

- **SIGWINCH** is the usual Unix signal on resize; macOS Terminal / iTerm emit it — still handle **polling** fallback if a child is run in an environment where **SIGWINCH** is flaky.
- **`read_raw_key`** / **`termios`** raw mode: any **Live** or alternate screen must **not** leave the tty in a bad state on cancel (**DEF-002**/**DEF-003** lessons).
- Avoid **Textual**-scale rewrite (plan **02** out of scope); stay within **Rich** primitives where possible.

## Design options

| Approach | Notes |
|----------|--------|
| **`rich.live.Live`** around the whole editor panel | Centralized refresh on resize + after edits; must integrate with blocking **stdin** reads (refresh from a **SIGWINCH** handler setting a flag, or timeout-based **select** waking to redraw). |
| **Redraw on each main-loop iteration** | On every key wait timeout, compare **(w,h)** to last; if changed, `console.clear_live` / full re-print. Simpler than **Live** but may **flicker**; throttle. |
| **`Layout` + `update`** | If the script moves to **`rich.layout`**, explicit **width** propagation may improve column sizing. |

**Recommendation:** Phase 1 prototypes **size check + full redraw** inside the existing editor loop; escalate to **`Live`** only if flicker is unacceptable.

## Phases

### Phase 1 — Specification

- Document **minimum columns** for the table (count column width, mode string, etc.).
- Decide **SIGWINCH-only** vs **SIGWINCH + 250 ms poll** for environments without reliable signals.

### Phase 2 — Implementation

- Capture **initial** `(columns, lines)`; install **`signal.signal(signal.SIGWINCH, …)`** (or thread-safe flag) where safe in a single-threaded CLI.
- Between **`read_raw_key`** calls (or inside its **select** timeout path), detect size change → rebuild **`Table`** / **`Panel`** and print with **`console.clear`** or Rich’s recommended clear for the region (avoid full scrollback wipe if possible — product choice).

### Phase 3 — Verification

- Re-run **MT-08** checklist in plan **02**; close **DEF-005** remediation notes if superseded.
- Add a **short** automated test only if plan **03** dry-run + PTY can assert **no crash** on injected **SIGWINCH** (optional).

## Manual QA

- Open **`./osx/macos_mouse_click.py --learn`** (no **`-Y`**, **`rich`** on a TTY).
- **Shrink** width in steps; confirm readable table or explicit “too narrow” message.
- **Expand** width; confirm columns use **extra** space (or stable readable wrap).
- **Cancel** with **Q** after resize storms — exit **0**, terminal sane.

