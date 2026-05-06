---
todos:
  - id: add-plan-08
    content: "Write docs/osx/plans/plan-008-macos-mouse-click-stop-during-run.md"
    status: completed
  - id: phase-08-spec-stop-surface
    content: "Choose stop surface: global hotkey vs stop-file vs companion signal"
    status: pending
  - id: phase-08-implement-flag-hook
    content: "Wire chosen surface to existing shutdown_requested / sleep_interruptible"
    status: pending
  - id: phase-08-docs-cli-help
    content: "Document flags, Accessibility/TCC notes, and -Y learn example"
    status: pending
  - id: phase-08-manual-qa
    content: "Operator QA: long -Y finite run, stop without foreground terminal"
    status: pending
isProject: false
---

# Plan 08: Stop the clicker **during** a run (without foreground terminal)

> **Frozen — superseded by [plan-020-uber-true-up](plan-020-uber-true-up.md) on 2026-05-06.**
>
> This document is **read-only**. Do not add new work, status updates, or fix references here.
> Open work moved to plan-020. New features → new `plan-###`. Problems → defects under
> [`docs/osx/defects/`](../defects/) whose `related_plans:` references this file and `plan-020`.

This document designs a way to **abort an in-progress Quartz run** (learn anchor recorded, synthetic loop running, or warmup sleeps) when the user **cannot reach the terminal** quickly enough for **Ctrl+C** / **SIGINT**. It applies especially to **`-Y`/`--yes`** paths where there is **no** Rich pre-run pause and **stdin may not be a TTY** — for example:

```bash
./osx/macos_mouse_click.py --learn -n 10 -d 0.25 -Y
```

Ten synthetics with **0.25 s** between clicks is only a few seconds, but **large `-n`**, **long `delay`**, or **`count=0` (infinite)** can run for a **very long time** with **unintended UI effects** if the operator cannot stop.

It complements **[`plan-001-macos-clicker.md`](plan-001-macos-clicker.md)** (signals, `shutdown_requested`, `sleep_interruptible`), **[`plan-002-macos-mouse-click-terminal-ux.md`](plan-002-macos-mouse-click-terminal-ux.md)** (pre-run only), and **[`plan-004-macos-mouse-click-run-progress-ui.md`](plan-004-macos-mouse-click-run-progress-ui.md)** (post-start **terminal** feedback — still useless if the terminal is not focused).

**Priority note (2026):** Operator feedback ranks **“get out of infinite / unsupervised runs”** above **pretty progress** ([plan 04](plan-004-macos-mouse-click-run-progress-ui.md)). **`count=0`** with **`-Y`**, **`delay=0`**, or a buried terminal means **SIGINT alone** is insufficient; this plan owns **additional stop surfaces** and any **non-terminal** override (file, hotkey, documented `kill`, optional input/mouse heuristics where safe).

## Table of contents

- [Operator goals (break-out)](#operator-goals-break-out)
- [Problem](#problem)
- [Goals](#goals)
- [Constraints](#constraints)
- [Design options](#design-options)
- [Recommended direction](#recommended-direction)
- [Phases](#phases)
- [Risks](#risks)
- [Manual QA](#manual-qa)

## Operator goals (break-out)

Beyond “focus the terminal and **Ctrl+C**,” the product should consider:

1. **`count=0` (infinite)** and **very large finite `-n`** with **small `delay`**: the user must have a **predictable** way to stop without winning a race against the loop (see also **[plan 04 § Operator constraints](plan-004-macos-mouse-click-run-progress-ui.md#operator-constraints-product)** on **`delay=0`** and **`sleep_interruptible`**).
2. **TTY-attached runs:** optional **Escape** (or similar) as a **cancel** during the synthetic loop **only** if it can be implemented without fighting **`termios`** state used elsewhere and without breaking **`-Y`** / pipe contracts when stdin is not a TTY.
3. **Spatial “panic” gesture (optional, product-dependent):** e.g. **user moves the mouse far from the anchor** to trigger **`shutdown_requested()`** — requires defining **distance threshold**, interaction with **learn** taps and **Accessibility**, and false positives (accidental bump). Treat as **later** option after **stop file** / documented **`kill`** provenance.
4. **Cross-link:** Throttled “still alive” output during long runs lives in **[plan 04](plan-004-macos-mouse-click-run-progress-ui.md)**; this plan owns **making stop reachable**.

## Problem

Today, **in-run stop** is effectively **“switch to the terminal and interrupt”** (`Ctrl+C` → **SIGINT**, or **`kill -INT/-TERM`**). That fails when:

- Another app has focus and must stay there during the run.
- The process was started from a **launcher** / **IDE** / **background** shell where the window is buried.
- **`-Y`** was used for automation and **no TTY** is attached for a secondary “press `s` to stop” read.

## Goals

1. **Reliable emergency stop** while **`run_synthetic_loop`**, **`run_learn_flow`** (post-anchor), or interruptible sleeps are active — without requiring the **terminal** to be focused.
2. **Reuse existing shutdown plumbing** where possible: **`shutdown_requested()`** + **`sleep_interruptible`** already poll between iterations ([`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py)).
3. **Predictable operator contract:** document the exact gesture (hotkey, file, or signal to a companion PID) and any **macOS permissions** (Accessibility, etc.).
4. **Default-off or conservative defaults** so scripting is not surprised by global key grabs unless explicitly enabled.

## Constraints

- **Learn mode** may already install a **CGEventTap** for the first real click; any second tap or hotkey path must **not** deadlock, double-tap, or swallow legitimate user input incorrectly (coordinate with plan **01** semantics).
- **Global hotkeys** may require **Accessibility** (or related TCC) beyond what v1 already needed — document clearly.
- **Single-script** preference from plan **02** suggests avoiding a mandatory separate GUI app unless the product accepts a **thin helper** binary.

## Design options

| ID | Mechanism | Pros | Cons |
|----|------------|------|------|
| **A** | **Global hotkey** (e.g. **Ctrl+Opt+Shift+S**) via **Quartz** / **Carbon `RegisterEventHotKey`** (API choice TBD) setting **`shutdown_state`** or raising **SIGINT** to self | Fast, no second terminal | Permission UX; must not clash with OS shortcuts; implementation complexity |
| **B** | **`--stop-file PATH`** (or fixed cache path): main loop **polls** mtime / existence between sleeps; operator **`touch`**s file to stop | Simple, scriptable, no global key | Slower worst-case latency = poll interval; path hygiene |
| **C** | Document **`kill -INT <pid>`** from **Activity Monitor** / another shell + optional **`--pid-file`** | Zero new code if docs-only | Still requires “another terminal” or GUI |
| **D** | Tiny **companion** process: user runs **`macos_mouse_click_stop`** that signals parent by PID file | Clear separation | Two binaries / install story |
| **E** | **Mouse-move cancel** (optional): if cursor moves **> D px** from synthetic anchor, set **`shutdown_state`** | Hands-free “panic” without terminal | False positives; Quartz polling cost; learn/tap interaction |

## Recommended direction

Ship **B** first (**opt-in stop file** + small poll in **`sleep_interruptible`** and/or **top of `run_synthetic_loop`**) for **lowest risk** and **`-Y`** / **infinite** friendliness — worst-case latency is the **poll interval**, so document tradeoffs for **`delay=0`**. Add **A** as an **optional** `--global-stop-hotkey` (exact flag TBD) in a later phase once event-tap interaction with **learn** is proven safe. **E** (mouse-move) remains **exploratory** until **B** ships and operator evidence says it is still needed.

## Phases

### Phase 1 — Specification

- Finalize **flag names** (`--stop-file`, `--poll-stop-ms`, etc.).
- Define interaction with **`count=0`** (infinite), **`delay=0`**, and **learn warmup** delay (poll points when **`sleep_interruptible`** does not run long).
- Decide whether **learn tap waiting** phase also honors stop file / hotkey (probably **yes** for consistency).
- If **Escape** (or stdin line) cancel is in scope for TTY runs: specify exact **when** stdin is read (never block Quartz on **`read`** without a plan) and how it coexists with **[plan 04](plan-004-macos-mouse-click-run-progress-ui.md)** output.

### Phase 2 — Stop file (recommended first ship)

- Poll **stop file** inside **`sleep_interruptible`** and/or before each synthetic pair.
- On trigger: set **`shutdown_state`** (same as signal path), print **`Stopped.`**, exit **130** (align with existing interrupt semantics where applicable).

### Phase 3 — Global hotkey (optional)

- Register hotkey only when flag set; unregister on exit.
- **Thread-safety** or **main-thread** delivery for flipping **`shutdown_state`** (avoid races with Quartz callbacks).

### Phase 4 — Docs + operator checklist

- Extend plan **02** with a new **MT-xx** or a short **“Stop during run”** row once behavior is stable.
- Update **`--help`** / script header with example **`kill`** and stop-file workflow.

## Risks

- **Latency:** poll interval vs CPU wakeups; hotkey vs file race.
- **Security:** world-writable stop path → local abuse; default path must be safe or require explicit **`PATH`**.
- **Learn + tap:** verify stop does not leave tap enabled after abort.

## Manual QA

- **`./osx/macos_mouse_click.py --learn -n 200 -d 1 -Y`** with stop file: trigger mid-run without focusing original terminal; process exits **130** (or agreed code) and **no** further synthetics after stop.
- **Infinite** `-n 0` with **`-Y`**: stop file still ends run.
- **Without** opt-in flags: **zero** behavior change vs today.

