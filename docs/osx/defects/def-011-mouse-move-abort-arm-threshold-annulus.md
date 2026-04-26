---
id: DEF-011
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
  - ../plans/agent/plan-agent-cookie-clicker-rate-control.plan.md
---

### DEF-011: Mouse-move abort false positive — arm radius larger than leave threshold (fixed)

**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on transcripts (sometimes with stderr merged into the capture).

- **Status:** **Fixed** (script).
- **Severity:** High (was) — buy ladder stopped mid-run without intentional operator mouse motion.
- **Opened:** 2026-04-26
- **Completed:** 2026-04-26
- **Affects:** [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py) (`run_synthetic_loop`, `--abort-on-mouse-move`); [`osx/macos_mouse_click_loop.sh`](../../../osx/macos_mouse_click_loop.sh); **[DEF-010](def-010-mouse-move-abort-wrong-reference.md)** (follow-on in the same loop).

**Relationship to DEF-010**

DEF-010 fixed comparing the cursor to **burst-start** instead of **`(x, y)`**. DEF-011 was separate: **default arm radius** could be **larger** than **leave threshold**, so one cursor sample could **arm** and **abort** before any synthetic click.

**Observed (before fix)**

Operator transcript (default profile, no `-P`):

```text
./osx/macos_mouse_click_loop.sh
…
buy time machine
Running: mode=fixed count=5 delay=0.0s
… "anchor_y":14.5888 …
buy portal
Running: mode=fixed count=5 delay=0.0s
… "anchor_y":-48.8354 …
buy alchemy lab
Running: mode=fixed count=5 delay=0.0s
… "anchor_y":-103.6 …
Stopped (cursor moved away from click target beyond --mouse-move-threshold-px).
```

Per-row **`anchor_y`** changes are **expected** (different ladder rows). The defect was the **stop** on the third row without the operator choosing to move the mouse away from gameplay.

**Root cause (before fix)**

In **`run_synthetic_loop`**, each loop iteration **before** `post_synthetic_click`:

1. If **`d² ≤ arm_sq`**, set **`armed`**.
2. If **`armed`** and **`d² > thr_sq`**, abort (**exit 130**).

Default **`arm_r`**: **`max(60, 2 × threshold)`** → **60 px** at threshold **20**. **Abort** when **d > 20 px**. So **20 < d ≤ 60** **armed** and **aborted** on the **same** sample, **before the first click** of a new subprocess. Buy ladder **row_spacing** ~**63.5 px** left the cursor **~55 px** from the next row’s target — inside that annulus.

**Resolution**

- **Leave detection** runs only when **`n_done > 0`** (at least one synthetic click has been posted) in addition to **`armed`** and **`d > threshold`**.
- **Tests:** [`osx/tests/test_mouse_move_abort.py`](../../../osx/tests/test_mouse_move_abort.py) (`test_def011_annulus_no_abort_before_first_click`).
- **Docs:** [`osx/README.md`](../../../osx/README.md) in-band stop bullet **2**; module docstring and **`argparse`** help in [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py).

**Git:** `8e2843c45cc5074c4dc7dc4159f6be01f906f361`

**Regression check**

- Default buy ladder: **time_machine** → **portal** → **alchemy_lab** completes **five** clicks each row without spurious stop when the operator does not move the cursor away from the game.
- Armed then cursor leaves target **after** the first click: still exits **130** (existing **`test_abort_when_armed_then_cursor_leaves_target`**).
