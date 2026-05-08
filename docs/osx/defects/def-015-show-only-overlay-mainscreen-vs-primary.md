---
id: DEF-015
related_plans:
  - ../plans/plan-021-macos-mouse-click-show-only-target-tour.md
  - ../plans/plan-020-uber-true-up.md
isProject: false
---

### DEF-015: `show_target_overlay` uses `NSScreen.mainScreen()` for the Quartz→Cocoa Y conversion → overlay drawn in the wrong place on multi-monitor setups

**Terminology:** **Quartz global coordinates** — `CG`-flavored coordinate space with origin at the **primary** display's **top-left**, Y increasing downward. Used by `CGWarpMouseCursorPosition`, `CGEventCreateMouseEvent`, and the click-target Y values in [`osx/config/cookie_clicker_profile.defaults.json`](../../../osx/config/cookie_clicker_profile.defaults.json). **Cocoa global coordinates** — AppKit coordinate space with origin at the **primary** display's **bottom-left**, Y increasing upward. Used by `NSWindow` frames. **Primary display** — the one marked primary in *System Settings → Displays*; first entry of `NSScreen.screens()` by AppKit convention. **Main screen** — `NSScreen.mainScreen()`; the screen with the **current keyboard focus**, NOT necessarily the primary.

- **Status:** **Open** (root cause located; fix proposed; awaiting approval).
- **Severity:** Medium — operator-facing miscalibration. Real clicks land at the correct profile coordinates (cursor warp + `CGEventPost` both use Quartz `(x, y)` directly), but the show-only overlay/crosshair drawn by [plan-021](../plans/plan-021-macos-mouse-click-show-only-target-tour.md) appears in the wrong place when the terminal running the script is on a non-primary display. Operators using the tour to verify coordinates may "fix" the profile to compensate for the visual offset and end up with worse real-click coordinates.
- **Opened:** 2026-05-07
- **Affects:** [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py) — `show_target_overlay` (the panel + crosshair `NSWindow` placement). Indirectly affects any operator workflow that uses **`-T`** (loop tour) or `--show-only` (direct python clicker) to validate / calibrate profile click targets. The `--show-only` cursor warp itself is unaffected; only the visual overlay is mispositioned.

---

### Observed

Operator reports that the **`-T`** tour overlay does not land where real clicks (without `-T`) land, after a fresh tour cycle on a profile whose targets live on a secondary display:

```text
./osx/macos_mouse_click_loop.sh -T -W 1.5 -c 1
```

Symptom: the macOS cursor warps to the correct profile target (visible in the menu bar / cursor position), but the red crosshair window and "would click N at (x, y)" panel are drawn at a Y offset that differs from the actual cursor position. Subsequent real-click runs land at the original profile coordinates, NOT where the operator saw the crosshair.

Empirically the offset is roughly the difference between the primary display height and the focused (terminal) display height, which on common laptop + external setups can be **~150–250 px** — easily mistaken for "three buy buttons" of vertical drift.

---

### Root cause

`show_target_overlay` ([`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py) lines around the AppKit block) performs the Quartz → Cocoa Y conversion using:

```python
screen = AppKit.NSScreen.mainScreen()
if screen is None:
    return
screen_h = float(screen.frame().size.height)
…
panel_y = screen_h - float(y) - win_h - 8.0
ch_y_cocoa = screen_h - float(y) - ch_h / 2.0
```

The Cocoa global coordinate system is anchored at the **primary** display's bottom-left, so the correct conversion is

```text
cocoa_y = primary_screen_height - quartz_y
```

`NSScreen.mainScreen()` returns the screen with the current keyboard focus, NOT the primary display. When the terminal running the python clicker has focus on a non-primary screen — the typical setup for this repo, where the cookie clicker browser sits on the primary monitor and the terminal sits on the laptop's built-in display (or vice versa) — `screen.frame().size.height` is the focused screen's height, not the primary's, and the conversion silently shifts the overlay by

```text
delta = primary_screen_height - focused_screen_height
```

The cursor warp (`CGWarpMouseCursorPosition`, line ~167) and the no-tour synthetic click (`post_synthetic_click`, line ~142) both operate purely in Quartz global coordinates, so they are unaffected: real clicks still land where the profile says.

---

### Expected behavior (product)

For any single profile target `(x, y)`:

1. The cursor warps to Quartz `(x, y)` (already correct).
2. The red crosshair window center renders at the **same** screen pixel as the warped cursor on every monitor configuration.
3. The "would click N at (x, y)" panel sits at a fixed visual offset from the crosshair (currently `+20, -8` Cocoa points, intentionally to the lower-right) — that offset is by design and not part of this defect.
4. A subsequent real-click run (no `-T`) lands on the same screen pixel where the crosshair was drawn.

Operators must be able to use the show-only tour to verify coordinates, confident that "where the overlay sat" equals "where real clicks will land".

---

### Suggested fix (for approval before coding)

Single-file change in [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py), inside `show_target_overlay`, replacing the focused-screen lookup with the primary-screen lookup:

```python
# Cocoa global coordinates are anchored at the primary display's bottom-left;
# Quartz global coordinates are anchored at the primary display's top-left.
# NSScreen.mainScreen() returns the screen with current focus, which is NOT
# necessarily the primary display, so using its height for the Quartz->Cocoa Y
# conversion silently shifts the overlay by (primary_h - focused_h) pixels on
# multi-monitor setups. Read the height from screens()[0] — the primary by
# AppKit convention.
screens = AppKit.NSScreen.screens()
if not screens:
    return
primary_screen = screens[0]
screen_h = float(primary_screen.frame().size.height)
```

No change to `panel_y` / `ch_y_cocoa` arithmetic — the conversion `cocoa_y = screen_h - y` already does the right thing once `screen_h` is the primary screen's height (handles negative Quartz `y` for displays above the primary, exactly as today).

No change to:

- `warp_cursor` (already correct — uses Quartz `(x, y)` directly).
- `post_synthetic_click` (unaffected — also Quartz).
- `cookie_clicker_profile.defaults.json` (no profile coordinate changes implied by the fix; but see operator follow-up below).

Tests:

- `osx/tests/test_show_only_overlay_smoke.py` — existing smoke tests still pass without modification (they tolerate any positive screen height).
- Optional new unit test: monkey-patch `AppKit.NSScreen.screens` to return a stub with a known primary frame and assert that `show_target_overlay` reads its height. Skip if mocking AppKit objects is brittle — the manual operator verification below is the authoritative regression check.

Manual regression (operator):

1. Run `./osx/macos_mouse_click_loop.sh -T -W 1.5 -c 1` from a terminal on a non-primary display.
2. Confirm the macOS cursor and the red crosshair coincide on every target (no vertical drift).
3. Run a real cycle (no `-T`) and confirm clicks land where the crosshair sat in step 2.

### Operator follow-up — possible profile shift compensating for this defect

Before the fix is applied, operators may have used the buggy overlay to "calibrate" their profile, shifting all click Y values to make real clicks line up with the (mispositioned) crosshair. Such a shift makes real clicks **wrong** once this defect is fixed.

If an operator suspects their profile carries such a compensating shift, after applying the fix they should re-tour, observe whether the crosshair now sits where they actually want clicks to land, and revert any compensating Y shift in their profile JSON if necessary.

---

### Resolution

Track the fix on plan-020 (`CL-SHOW-ONLY` in [plan-020 §4.1](../plans/plan-020-uber-true-up.md)). When the fix lands:

1. Update this defect's `Status` to **Fixed (script)** and link the commit SHA below.
2. Tick the `CL-SHOW-ONLY` box on plan-020 (do **not** edit plan-021 itself; this defect is part of plan-021's normative scope and the fix updates plan-020's checklist per [plan-020 §1.3](../plans/plan-020-uber-true-up.md)).
3. Update [`README.md`](README.md) defect index with the new row.

| Field | Value |
|-------|-------|
| Fix commit | _pending_ |
| Closed | _pending_ |
