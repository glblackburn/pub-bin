<!-- 7b30f896-9430-4faf-ae44-92b593896e92 -->
---
todos:
  - id: "impl-armed-target"
    content: "Implement armed distance-to-(x,y) abort in run_synthetic_loop; update stderr message"
    status: pending
  - id: "tests-mouse-abort"
    content: "Rewrite test_mouse_move_abort.py for arm + leave scenarios"
    status: pending
  - id: "docs-readme"
    content: "README: arming semantics, new optional flag if added"
    status: pending
isProject: false
---
# Fix `--mouse-move-threshold-px` reference semantics

## What the code does today

In [`osx/macos_mouse_click.py`](osx/macos_mouse_click.py) `run_synthetic_loop`, when `abort_on_mouse_move` is set, **`ref` is set once** to `get_mouse_location(qz)` (cursor at **burst start**), then each iteration checks whether the current cursor is farther than `--mouse-move-threshold-px` from **that** point:

```1416:1428:osx/macos_mouse_click.py
    ref: Optional[Tuple[float, float]] = None
    if abort_mouse:
        ref = get_mouse_location(qz)
    while True:
        ...
        if abort_mouse and ref is not None and _mouse_moved_beyond_threshold(qz, ref, thr):
```

So drift is **“cursor now vs cursor at T0”**, not **“cursor vs click target (-x/-y)”**.

## Why that is wrong (your terminal scenario)

1. **Startup geometry:** You launch the looper from a terminal; the **hardware cursor** stays over the terminal (or IDE). `ref` is recorded there.

2. **Clicks are not where the cursor was:** Synthetic events are posted at **Quartz `(x, y)`** (the cookie). Depending on OS / app behavior, **`CGEventPost` may or may not move the logical cursor** to the click point. If it **does** move the cursor toward the cookie, the very next `get_mouse_location()` can jump **hundreds of pixels** away from `ref` (terminal) even though **no human** moved the mouse—only automation did.

3. **False “panic”:** The check interprets that jump as “user moved beyond threshold” and exits with `Stopped (cursor moved beyond --mouse-move-threshold-px).` That is the opposite of the intended **human-in-the-loop** escape.

4. **Wrong mental model:** Operators expect “**I** nudge the mouse to stop,” not “the cursor must stay within 20px of where it was when the subprocess started” (which couples abort to **shell layout**, not **game**).

## Correct direction (choose one primary semantics)

### Recommended: **armed “drift from click target”**

- **Reference for distance:** always the **synthetic anchor** `(x, y)` from `-x/-y` (same as click point), not cursor at T0.

- **Arming (required):** Do **not** treat `distance(cursor, (x,y)) > threshold` as abort until the operator is plausibly “at the game”:
  - **Option A:** Arm when `distance(cursor, (x,y)) <= R_arm` once (e.g. `R_arm = 2 * threshold` or a separate `--mouse-arm-radius-px`).
  - **Option B:** Arm automatically after **N** synthetic clicks or **T** seconds (weaker; documents assumption that cursor may sync to target).

- **Abort after armed:** If armed and `distance(cursor, (x,y)) > threshold`, stop (user moved pointer away from the cookie area).

**Pros:** Matches “nudge away from cookie to stop”; no false trip when mouse starts on terminal. **Cons:** If the user never moves the cursor near the cookie, abort never arms (document + optional `--mouse-abort-unarmed-timeout` later).

### Alternative: **per-iteration delta (jerk detection)**

- Store `prev = get_mouse_location()` each iteration; abort if `distance(curr, prev) > threshold` **and** optionally ignore the first sample after each `post_synthetic_click` if the OS teleports the cursor.

**Pros:** Independent of absolute layout. **Cons:** Harder to tune; synthetic cursor teleport can look like a huge delta unless masked.

## Implementation touchpoints (when you execute)

- [`osx/macos_mouse_click.py`](osx/macos_mouse_click.py): replace “ref at burst start” with **armed + distance to `(x, y)`**; clarify stderr message (e.g. “Stopped (cursor left click target).”).
- [`osx/tests/test_mouse_move_abort.py`](osx/tests/test_mouse_move_abort.py): update mocks to reflect arming + target distance (remove tests that only encoded “T0 cursor” behavior).
- [`osx/README.md`](osx/README.md): document arming, `--mouse-arm-radius-px` (if added), and interaction with terminal-first launch.
- Optional: [`osx/macos_mouse_click_loop.sh`](osx/macos_mouse_click_loop.sh): pass new flags only if you add CLI knobs; defaults can live in Python.

## Non-goals for this fix

- Global Escape `CGEventTap` (Phase 1 optional item still deferred).
