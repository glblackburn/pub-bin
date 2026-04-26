---
id: DEF-010
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
  - ../plans/agent/plan-agent-cookie-clicker-rate-control.plan.md
---

### DEF-010: `--abort-on-mouse-move` used burst-start cursor, not click target (fixed)

**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on transcripts (sometimes with stderr merged into the capture).

- **Status:** **Fixed** (script).
- **Severity:** High (was) — spurious abort when the looper was started from a terminal with the cursor over the terminal while synthetic clicks targeted a distant cookie.
- **Opened:** 2026-04-26
- **Completed:** 2026-04-26
- **Affects:** `osx/macos_mouse_click.py` (`run_synthetic_loop`, `--abort-on-mouse-move`); `osx/macos_mouse_click_loop.sh` (pass-through flags); [`osx/README.md`](../../../osx/README.md).

**Observed (before fix)**

1. Run [`osx/macos_mouse_click_loop.sh`](../../../osx/macos_mouse_click_loop.sh) or [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py) with `-Y` from a terminal with the **physical cursor over the terminal**.
2. Synthetic clicks at Quartz `(x, y)` far from that cursor.
3. Process exited quickly with: `Stopped (cursor moved beyond --mouse-move-threshold-px).`

**Root cause (before fix)**

`run_synthetic_loop` stored **`ref = get_mouse_location()` at burst start** and compared subsequent cursor positions to **`ref`**, not to the **click anchor** `(x, y)`. If the OS moved the logical cursor toward the synthetic click, distance from **T0 ref** could exceed the threshold **without deliberate user motion**.

**Resolution**

- **Arming:** Leave-target detection **arms** only after the cursor lies within **`--mouse-arm-radius-px`** of the click target `(x, y)`. Default radius: **`max(60, 2 × --mouse-move-threshold-px)`** when the flag is omitted.
- **Abort (after armed):** Exit **130** if the cursor is **farther than** `--mouse-move-threshold-px` from `(x, y)`.
- **CLI:** `--mouse-arm-radius-px` (optional; must be **≥** threshold).
- **Git:** `a4361c307e046c3fb2d56ac4932b12d3345cdf01`
- **Tests:** [`osx/tests/test_mouse_move_abort.py`](../../../osx/tests/test_mouse_move_abort.py), [`osx/tests/test_dry_run.py`](../../../osx/tests/test_dry_run.py).

**Regression check**

- Cursor stays far from `(x, y)` for the whole burst (terminal-first): burst completes; no spurious mouse abort.
- Cursor near `(x, y)` then moved away beyond threshold: abort **130** with updated stderr text.
