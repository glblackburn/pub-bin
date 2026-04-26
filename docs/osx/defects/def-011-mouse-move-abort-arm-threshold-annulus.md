---
id: DEF-011
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
  - ../plans/agent/plan-agent-cookie-clicker-rate-control.plan.md
---

### DEF-011: Mouse-move abort false positive — arm radius larger than leave threshold (open)

**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on transcripts (sometimes with stderr merged into the capture).

- **Status:** **Open**
- **Severity:** High — buy ladder stops mid-run without intentional operator mouse motion; breaks Cookie Clicker **`macos_mouse_click_loop.sh`** defaults.
- **Opened:** 2026-04-26
- **Affects:** [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py) (`run_synthetic_loop`, `--abort-on-mouse-move`, default **`--mouse-arm-radius-px`** via `_effective_mouse_arm_radius_px`); [`osx/macos_mouse_click_loop.sh`](../../../osx/macos_mouse_click_loop.sh) (`click_target` passes **`--mouse-move-threshold-px 20`**); **[DEF-010](def-010-mouse-move-abort-wrong-reference.md)** (reference vs click target — fixed; this defect is a **follow-on geometry bug** in the same loop).

**Relationship to DEF-010**

DEF-010 fixed comparing the cursor to **burst-start** instead of **`(x, y)`**. DEF-011 is separate: with DEF-010’s design, **default arm radius** can be **larger** than **leave threshold**, so one cursor sample can **arm** and **abort** before any synthetic click.

**Observed**

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

Per-row **`anchor_y`** changes are **expected** (different ladder rows). The defect is the **stop** on the third row without the operator choosing to move the mouse away from gameplay.

**Reproduction (expected)**

1. From repo root: **`./osx/macos_mouse_click_loop.sh`** with default profile (no **`-P`**, or any profile whose store **row spacing** is on the order of **60 px**).
2. Let the buy ladder run through at least **time_machine** → **portal** → **alchemy_lab** with **`macos_mouse_click_loop.sh`** defaults (**`--abort-on-mouse-move`**, **`--mouse-move-threshold-px 20`**).
3. Observe **`Stopped (cursor moved away from click target beyond --mouse-move-threshold-px).`** on an early row (often third) even when the operator did not intentionally move the cursor away from the game.

**Root cause**

In **`run_synthetic_loop`**, each loop iteration **before** `post_synthetic_click`:

1. If **`d² ≤ arm_sq`**, set **`armed`** (cursor within **arm radius** of **`(x, y)`**).
2. If **`armed`** and **`d² > thr_sq`**, abort (**exit 130**).

Default **`arm_r`** from **`_effective_mouse_arm_radius_px`**: **`max(60, 2 × threshold)`** → **60 px** when threshold is **20**. **Abort** fires when **d > 20 px**.

So **20 < d ≤ 60** defines an **annulus**: the same sample **arms** and **immediately aborts** — including **before the first click** of a new subprocess.

Each ladder row is a **new** **`macos_mouse_click.py`** invocation; **`armed`** resets to **false**. After **portal** clicks, the cursor sits near **portal** **`(x, y)`**; **alchemy_lab** target is **`~63.5 px`** away in **`y`** in [`osx/config/cookie_clicker_profile.defaults.json`](../../../osx/config/cookie_clicker_profile.defaults.json) (**Δy ≈ 55**). That lies in **(20, 60]**, so the annulus triggers.

```mermaid
flowchart LR
  target[ClickTarget]
  inner["d_le_thr"]
  band["thr_lt_d_le_arm"]
  outer["d_gt_arm"]
  target --> inner
  inner --> band
  band --> outer
```

**Expected behavior**

- Buy ladder rows complete **without** spurious mouse-move stop when the operator has not deliberately moved the cursor away from the click target (or document clearly that ladder + current defaults are unsupported until fixed).

**Fix directions** (design only; no obligation until implementation pass)

- Enforce **`arm_r ≤ threshold`** whenever both apply, or **arm only when `d ≤ threshold`** (tighter arming).
- **Defer “leave” abort** until after at least one synthetic click in the burst, or until the cursor has been within **`threshold`** of target since arming (hysteresis).
- **Loop script:** pass **`--mouse-arm-radius-px`** **≤** threshold as a temporary workaround (may reintroduce DEF-010-class “never arm” cases if set too small — trade off per operator layout).
- Add **automated regression** covering **sequential fixed targets** ~**55 px** apart with **`abort-on-mouse-move`** defaults.

**Implementation backlog** (single canonical doc — no separate `plan-agent-def-011` file)

- Apply one of the **Fix directions** above in code/tests; close this defect and mirror **plan-002** / **`docs/osx/defects/README.md`** when done.

**Git:** —
