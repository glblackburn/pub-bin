---
id: DEF-010
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
  - ../plans/agent/plan-agent-cookie-clicker-rate-control.plan.md
---

### DEF-010: `--abort-on-mouse-move` uses cursor at burst start, not click target
- **Status:** **Open** (no fix commit yet).
- **Severity:** High — in-band abort stops immediately in the common case (looper started from a terminal; mouse over terminal; synthetic clicks at a distant cookie).

**Observed**

1. Run `osx/macos_mouse_click_loop.sh` (or `macos_mouse_click.py` with `-Y`) from a terminal with the **physical cursor over the terminal** (typical).
2. Cookie / ladder clicks use Quartz coordinates far from that cursor (e.g. browser cookie).
3. Process exits quickly with stderr:

   `Stopped (cursor moved beyond --mouse-move-threshold-px).`

**Root cause**

In [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py) `run_synthetic_loop`, when `abort_on_mouse_move` is enabled, **`ref` is initialized to `get_mouse_location(qz)` once at burst start** (cursor over terminal). Each iteration compares the **current** cursor to **`ref`**.

Intended product behavior (see **Phase 1** in [`plan-agent-cookie-clicker-rate-control.plan.md`](../plans/agent/plan-agent-cookie-clicker-rate-control.plan.md)) is “**operator nudges the mouse to escape**” while the game has focus — i.e. drift relative to **game interaction**, not relative to **where the cursor happened to be when the subprocess started**.

Additional failure mode: if **`CGEventPost`** (or the OS) **moves the logical cursor** toward the synthetic click point `(x, y)`, the cursor can jump from **terminal** to **near cookie** between samples. The distance from **T0 ref** then exceeds the threshold even with **no human movement**, producing the same spurious stop.

**Desired behavior**

- Drift / “panic” semantics should be tied to the **synthetic anchor** `(x, y)` and/or **human intent**, not raw “distance from cursor at subprocess start.”
- Typical fix direction (design only until implemented): **arm** when the cursor is near the click target (or after a documented grace period), then **abort** when the cursor moves **away** from the target by more than the threshold; or use **per-iteration delta** with masking for synthetic cursor teleport. See discussion in **Cursor plan:** *Fix mouse-abort reference* (`~/.cursor/plans/`).

**Resolution**

- — (pending implementation + tests + README).

**Regression check (after fix)**

- Start burst from terminal with mouse over terminal; automation at distant `(x, y)` should **not** stop until the operator performs the documented escape gesture.
- Existing [`osx/tests/test_mouse_move_abort.py`](../../../osx/tests/test_mouse_move_abort.py) must be updated to match the new semantics.
