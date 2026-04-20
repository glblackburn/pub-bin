---
todos:
  - id: add-plan-05
    content: "Write docs/osx/plans/plan-005-macos-mouse-click-target-preview.md (goals, options, phases)"
    status: completed
  - id: phase-05-spec-flags
    content: "Lock CLI flags: dry preview-only vs show-then-run; interaction with -Y and TUI"
    status: pending
  - id: phase-05-terminal-context
    content: "Implement display-bounds query + Rich/plain summary (which display, % position)"
    status: pending
  - id: phase-05-on-screen
    content: "Optional on-screen indicator (overlay or cursor move); permissions + UX"
    status: pending
  - id: phase-05-docs-qa
    content: "Update help/plan 01/02; manual QA for multi-monitor and at-cursor/learn"
    status: pending
isProject: false
---

# Plan 05: Click target preview (where on the screen before run)

This document designs how [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py) helps the user **understand spatially** where synthetic clicks will land **before** Quartz runs (or immediately before the first synthetic), so that invocations like **`./osx/macos_mouse_click.py -x 400 -y 300 -n 2 -d 0`** are not opaque pairs of numbers.

It complements **[`plan-001-macos-clicker.md`](plan-001-macos-clicker.md)** (global Quartz coordinates, modes), **[`plan-002-macos-mouse-click-terminal-ux.md`](plan-002-macos-mouse-click-terminal-ux.md)** (pre-run Rich table), **[`plan-003-macos-mouse-click-tui-automation.md`](plan-003-macos-mouse-click-tui-automation.md)** (dry-run exit after editor — machine-readable summary without Quartz), and **[`plan-004-macos-mouse-click-run-progress-ui.md`](plan-004-macos-mouse-click-run-progress-ui.md)** (post-start progress). Plan **05** is specifically **“where is (x,y)?”** and optional **on-glass** feedback.

## Table of contents

- [Problem](#problem)
- [Goals](#goals)
- [Modes of operation](#modes-of-operation)
- [Design options](#design-options)
- [Recommended phasing](#recommended-phasing)
- [CLI sketch (non-normative until implemented)](#cli-sketch-non-normative-until-implemented)
- [Behavior matrix](#behavior-matrix)
- [Implementation touchpoints](#implementation-touchpoints)
- [Risks and constraints](#risks-and-constraints)
- [Manual QA (after implementation)](#manual-qa-after-implementation)

## Problem

Quartz uses **global display coordinates** (origin and multi-monitor layout are easy to misremember). A fixed **`-x`/`-y`** pair gives **no visual anchor** in the terminal; **learn** and **`--at-cursor`** are easier to reason about because the user already pointed at the UI. Fixed mode needs either **better textual context** (which display, relative position) or a **brief on-screen indicator**.

## Goals

1. **Preview-only (“dry” spatial mode):** A path that **does not** install taps, **does not** emit synthetic clicks, and **exits successfully** after showing **where** the resolved anchor is (fixed coordinates, or cursor snapshot for **`--at-cursor`**, or post-learn anchor is out of scope for “dry” unless we add a “replay last anchor” file later).
2. **Show before executing:** On interactive runs (and optionally behind an explicit flag for **`-Y`**), **surface the same information** (and optionally a **short on-screen cue**) **immediately before** the real run begins — without changing the default scripting contract until flags are decided in Phase 1.
3. **Multi-monitor honesty:** When we can query display bounds (**Quartz** / **`NSScreen`** via PyObjC if we add `AppKit`), report **which display** contains the point (or “outside all known frames”) and **normalized** position within that frame, not only raw **x,y**.
4. **TTY vs pipe:** Rich panels on **TTY**; **plain stderr** on pipes / no **`rich`**.

## Modes of operation

| User intent | Desired behavior |
|-------------|------------------|
| **“I only want to see where this lands”** | New **preview-only** flag (name TBD, e.g. **`--preview-target`**) → print spatial summary → **exit 0**; no Quartz click loop. |
| **“I want to run, but not blind”** | Default-on for **interactive** fixed / at-cursor after confirmation, or opt-in **`--show-target-before-run`**; may include a **timed on-screen marker** or **cursor visit** (see [Design options](#design-options)). |
| **Scripting (`-Y`)** | Default **unchanged** (no surprise mouse moves or windows). Optional **`-Y`**-compatible **preview-only** flag is fine; **show-then-run** under **`-Y`** should be **explicit** if offered at all. |

Distinction from plan **03** dry-run: plan **03** focuses on **exiting after the Rich editor** with **JSON-ish** config for **tests**. Plan **05** adds **human-oriented spatial** output (and optional overlay). The two can share a **single internal “resolve config then branch”** hook once implemented.

## Design options

### A — Terminal-only context (baseline)

- Query **display frame(s)** and print: global **(x,y)**, **display index / name**, **position within frame** (e.g. percentages from left/top of that display).
- Optional **ASCII sketch** of monitors with a **`*`** marker (coarse but zero new permissions).
- **Pros:** No overlay code, no focus steal, works in SSH if geometry is still meaningful (often not — document limitation).
- **Cons:** Still abstract for users who think in “the OK button on the dialog,” not percentages.

### B — Move pointer to target without clicking (optional flag)

- **`CGWarpMouseCursorPosition`** (or equivalent) to place the cursor at the anchor, **pause** (e.g. 1–2 s), optionally **restore** previous cursor location if we captured it.
- **Pros:** Immediately visible on glass.
- **Cons:** **Surprising** if default-on; must never be implicit for **`-Y`**; Accessibility-sensitive; may confuse if user moves mouse during pause.

### C — Transient overlay (crosshair / circle)

- Small **borderless always-on-top** window (likely **`AppKit`** + **`NSWindow`**, new dependency **`pyobjc-framework-Cocoa`** or careful bridging), draw a circle/crosshair at the anchor, auto-close after **N** seconds or keypress.
- **Pros:** Clear, does not move user’s cursor.
- **Cons:** More code, **Screen Recording** or other TCC buckets may apply depending on implementation (verify before promising); multi-space / full-screen edge cases.

### D — Reuse OS “locate pointer” or accessibility zoom

- **Fragile** / version-dependent; treat as **non-v1** unless we find a supported public API.

**Recommendation:** Ship **A** first (always useful, low risk), then add **B** or **C** behind explicit flags after product choice.

## Recommended phasing

### Phase 1 — Specification

- Finalize **flag names** and defaults ([CLI sketch](#cli-sketch-non-normative-until-implemented)).
- Decide whether **Rich pre-run** shows a **“Preview location”** row or key (**P**) before **S** (plan **02** amendment) vs CLI-only preview.
- Confirm interaction with **learn** (preview meaningless until anchor exists — either **disabled** or **runs after** first real click in a future “stepwise” UX; v1 can **skip** learn for preview-only).

### Phase 2 — Terminal spatial summary

- Implement display enumeration + point-in-rect classification + Rich/plain printers.
- Wire **preview-only** flag for **fixed** and **`--at-cursor`** (snapshot location once, then print — may require **one** Quartz read of cursor position, not a click).

### Phase 3 — Show before run (interactive)

- After **Proceed?** / **S** equivalent, call the same summary function; optional **B** or **C** behind flags.

### Phase 4 — Documentation and tests

- Help text + plan **01** coordinate section cross-link.
- Unit tests for **point-in-display** logic with mocked frames; manual **multi-monitor** checklist.

## CLI sketch (non-normative until implemented)

Examples only — names may change in Phase 1.

```bash
# Preview only: print where (400,300) is, then exit 0 (no clicks)
./osx/macos_mouse_click.py -x 400 -y 300 --preview-target

# Normal interactive run, but flash summary (and optional overlay) once before loop
./osx/macos_mouse_click.py -x 400 -y 300 -n 2 -d 0 --show-target-before-run
```

**`-Y`:** **`--preview-target`**-style behavior is safe; **`--show-target-before-run`** that moves the mouse or opens a window should require **both** **`-Y`** and a **second** consent flag, or be **disallowed** under **`-Y`**.

## Behavior matrix

| Path | Preview-only flag | Show-before-run |
|------|-------------------|-----------------|
| TTY + Rich + pre-run editor | Can run **P** / separate CLI flag; table may show computed display label | After **S**, before `import_quartz` click loop: panel + optional overlay |
| Legacy `--interactive`** | Same flags | After confirmation sheet |
| **`-Y`** | OK if read-only / terminal-only | Default **off**; explicit opt-in only |
| Pipe / non-TTY | Plain lines; no overlay | Plain lines only |

## Implementation touchpoints

- [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py): after full config resolution, before tap/loop; shared helper e.g. `describe_anchor_geometry(cfg) -> str | Renderable`.
- Possible small module for **display frames** vs cluttering `main()`.
- Plan **03** dry-run hook: emit **spatial block** in addition to JSON when both are enabled (or nest spatial in JSON — Phase 1 decision).

## Risks and constraints

- **SSH / headless:** No physical display — degrade gracefully (“cannot query displays”) and still print raw **x,y**.
- **Coordinate system:** Stay consistent with plan **01** (global Quartz); document **top-left vs bottom-left** per API used for **`NSScreen`** vs **`CGDisplayBounds`**.
- **Learn mode:** Preview of **fixed** point is trivial; preview of **learn** target **before** the user clicks is undefined — do not imply we can show it without the tap.
- **Accessibility / TCC:** Overlay (**C**) may add permission story; document in script header when implemented.

## Manual QA (after implementation)

- Single display: **`-x/-y`** corner, center, off-screen negative.
- Multi-monitor: point on each display; point in gap between displays if applicable.
- **`--at-cursor`:** cursor on each display; preview matches.
- **`-Y`** + **preview-only:** no clicks, exit **0**.
- Interactive: **show-before-run** does not steal focus in an unacceptable way (product bar).

