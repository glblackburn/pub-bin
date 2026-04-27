# Research: Looper buy-ladder vs cycle timing

**Date:** 2026-04-26

**Scope:** Why **[`macos_mouse_click_loop.sh`](../../../../osx/macos_mouse_click_loop.sh)** can *feel* slower—especially distinguishing **time between buy-ladder rows** (time machine → portal → alchemy lab, …) from **time between full automation cycles** (ladder + cookie burst + pause).

This note is research only; it does not change product behavior.

## Where delays come from

### Inter-cycle pause (dominant for “whole run” slowness)

- After each **`run_once`** (buy ladder if enabled, then cookie clicks), the main loop calls **`sleep "${CYCLE_SLEEP_SECONDS}"`** in **[`macos_mouse_click_loop.sh`](../../../../osx/macos_mouse_click_loop.sh)**.
- **`CYCLE_SLEEP_SECONDS`** is loaded from the profile’s **`preview_defaults.cycle_sleep_seconds`** (see **[`osx/config/cookie_clicker_profile.defaults.json`](../../../../osx/config/cookie_clicker_profile.defaults.json)** and the embedded Python in the loop script that prints `CYCLE_SLEEP_SECONDS=…`).
- Increasing that value (e.g. **30 → 35**) adds **+5 seconds per cycle** between cycles. It does **not** insert delay **between** individual ladder rows inside **`run_buy_ladder`**.

### Within each ladder row (clicks on one building)

- **`click_target`** invokes **`macos_mouse_click.py`** with **`-d 0`**: no intentional delay between synthetic clicks **inside** that subprocess.
- **`sleep_interruptible(delay)`** in **`run_synthetic_loop`** therefore adds no pause when delay is zero.

### Per ladder row (process overhead)

- Each **`click_target`** line is a **new** **`macos_mouse_click.py`** process. Interpreter startup dominates wall time compared to extra **`get_mouse_location`** reads.

### DEF-011 mouse-move guard

- **[`run_synthetic_loop`](../../../../osx/macos_mouse_click.py)** evaluates **`get_mouse_location`** once per loop iteration when **`--abort-on-mouse-move`** is on, and uses **`n_done`** plus **`ever_within_thr`** before treating distance as “left target.”
- That work is **small** next to **subprocess spawn** per ladder row.

### Echo before inter-cycle sleep

- **`echo "sleep: ${CYCLE_SLEEP_SECONDS}"`** runs **once per cycle** before **`sleep`**. Overhead is negligible.

### Debug / logging (operator variable)

- If **`run_once`** exports **`MACOS_MOUSE_CLICK_DEBUG_TUI`** / **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`**, each **`macos_mouse_click.py`** subprocess may do extra stderr / file I/O. For an A/B timing check, run with those **unset** or commented out and compare.

## Quick verification

- **Between ladder rows:** Watch timestamps on **`buy time machine`**, **`buy portal`**, … lines. Gaps there are mostly **per-invocation Python + Quartz**, not **`cycle_sleep_seconds`**.
- **Between cycles:** Watch for the **`sleep: …`** line (if present) and the following pause—that duration should match **`CYCLE_SLEEP_SECONDS`**.
- **Tune inter-cycle wait:** Edit **`cycle_sleep_seconds`** in the profile JSON (or use **`-P`** with a copy) if only the **post-cookie** pause should change.

## Cross-links

- **[`plan-agent-cookie-clicker-rate-control.plan.md`](plan-agent-cookie-clicker-rate-control.plan.md)** — Phase 1 in-band abort, **DEF-011** (mouse-move annulus / hysteresis).
- **[`plan-agent-looper-cookie-clicker-ui-research.plan.md`](plan-agent-looper-cookie-clicker-ui-research.plan.md)** — Broader looper + Cookie Clicker UI research.
