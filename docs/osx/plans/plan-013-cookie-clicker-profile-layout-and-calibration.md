# Plan 013 — Cookie Clicker profile layout: coordinate review and calibration design

**Status:** Design / roadmap (no implementation commitment in this document).

**Scope:** Compare existing profile JSONs under [`osx/config/`](../../../osx/config/), explain why adjustment is painful today, and propose **easier ways** to adapt coordinates when the **browser window** moves or resizes. **No code changes** are specified here—only product/design direction for future work.

**Related:** [`cookie_clicker_profile.schema.json`](../../../osx/config/cookie_clicker_profile.schema.json), [`cookie_clicker_detect_coords.py`](../../../osx/cookie_clicker_detect_coords.py), [`macos_mouse_click_loop.sh`](../../../osx/macos_mouse_click_loop.sh), [plan-001](plan-001-macos-clicker.md), [plan-010](plan-010-macos-mouse-click-learn-points-collect.md), DEF-012.

---

## 1. Review: differences between config JSON files

### 1.1 Files compared

| File | Role |
|------|------|
| [`cookie_clicker_profile.defaults.json`](../../../osx/config/cookie_clicker_profile.defaults.json) | Built-in loop defaults when `-P` is omitted or normalized away; **`source_image: "builtin"`** (coords-only). |
| [`cookie_clicker_profile.laptop_only.json`](../../../osx/config/cookie_clicker_profile.laptop_only.json) | Operator **single-screen** layout; same schema; coords tuned for one machine. |
| [`cookie_clicker_profile.sample.json`](../../../osx/config/cookie_clicker_profile.sample.json) | Example with a **real screenshot path** for preview; numeric layout matches defaults (desktop reference). |

Detected profiles under [`osx/config/cookie_clicker_profiles/`](../../../osx/config/cookie_clicker_profiles/) follow the same shape (global Quartz **x,y**); they are not line-by-line compared here but behave like **sample** (image + absolute coords).

### 1.2 Structural similarity

All profiles share the same top-level keys required by the schema: **`profile_name`**, **`source_image`**, **`detected_at`**, **`cookie`**, **`store`**, **`ladder_rows`**, **`preview_defaults`**, **`warnings`**.

- **`cookie`**: one anchor point (big cookie).
- **`store`**: buy-column **x**, vertical **panel_top** / **panel_bottom**, **`row_spacing`**.
- **`ladder_rows`**: twelve named rows, each absolute **`x`**, **`y`**, **`confidence`**.

The loop script ([`macos_mouse_click_loop.sh`](../../../osx/macos_mouse_click_loop.sh)) exports **`TIME_MACHINE_X`**, … **`CURSOR_X`**, **`COOKIE_X`**, etc., from **`ladder_rows`** and **`cookie`**; it does not interpret **`store.row_spacing`** for click placement today (spacing is informational / preview).

### 1.3 Numeric comparison (defaults vs laptop vs sample)

| Concept | defaults | laptop_only | sample |
|---------|-----------|-------------|--------|
| **profile_name** | `loop-builtin-defaults` | `laptop-single-screen-guess` | `sample-desktop` |
| **source_image** | `builtin` | `builtin` | path to PNG |
| **cookie (x, y)** | (1600.8, −410.9) | (133.3, 514.3) | (1600.8, −410.9) |
| **store.x** | 2344.4 | 699.4 | 2344.4 |
| **store panel_top / bottom** | −720 / 120 | ~269.1 / ~1109.1 | −720 / 120 |
| **row_spacing** | 63.5 | 63.5 | 63.5 |
| **ladder x** | 2344.4 every row | 699.4 every row | 2344.4 every row |
| **ladder y pattern** | Decreasing by ~63 px per step (game order) | Same **relative** steps as defaults, anchored to measured **time_machine** | Same as defaults (rounded y on first row) |
| **preview_defaults.cycle_sleep_seconds** | 35 | 25 | 30 |

**Takeaways:**

1. **defaults** and **sample** align numerically (sample is “defaults + screenshot + confidence metadata”). Coordinates are **global display space** (multi-monitor–friendly in the sense that they encode whatever Quartz returned at detection time).
2. **laptop_only** is a **large translation** of the same logical layout: cookie and buy column moved to a different region of global space; **y** ordering and row-to-row deltas match the **defaults** ladder template once anchored to a corrected **time_machine**.
3. Every actionable click target is still stored as **absolute (x, y)**. There is **no explicit browser window rectangle**, **no normalization** to window size, and **no scale** factor in the JSON.

---

## 2. Problem statement

When the **browser window** moves on the screen or is **resized**:

- Absolute coordinates drift; the operator must edit **many** numbers (or re-run full detection).
- **Pure translation** (cookie delta) works only if scale and layout inside the window are unchanged—**resize** breaks that.
- **Pure “defaults offsets from time_machine”** (as in laptop tuning) preserves **vertical spacing** from a reference template but assumes **row_spacing / geometry** in the game still matches that template at the current zoom and column width.
- Operators think in **“cookie here, store column there, window this big”**, not in twelve independent global pairs.

Goal: a **calibration model** that is easier to reason about and requires **fewer manual edits** when only position and/or scale of the game window change.

---

## 3. Design principles (target experience)

1. **Few anchors, many derived points** — Operator places **2–4** references (e.g. cookie center, top of buy list, bottom of list, or window corners); ladder rows are **computed**, not hand-edited, when possible.
2. **Explicit window frame (optional but powerful)** — Store a **`browser_rect`** `{ left, top, width, height }` (or top-left + size) in **global Quartz space** so normalization **(u, v) ∈ [0,1]²** is well-defined for “inside the window.”
3. **Separate translation from scale** — **Translation** handles window move; **uniform or anisotropic scale** handles resize / zoom changes relative to a **reference profile**.
4. **Backward compatibility** — Existing profiles remain valid; new fields are **optional** with a clear **resolution order** (e.g. if `layout` absent, behave exactly as today).
5. **Preview stays trustworthy** — Any derived global coords must feed **`cookie_clicker_preview_plan.py`** the same way as today (manifest hashing, DEF-012 coords-only rules unchanged unless spec extends).

---

## 4. Proposed directions (choose or combine in phases)

### 4.1 Phase A — “Layout transform” overlay (minimal schema extension)

Add an optional object, e.g. **`layout_transform`**, alongside existing data:

```json
"layout_transform": {
  "mode": "affine",
  "reference_profile": "cookie_clicker_profile.defaults.json",
  "anchor_row": "time_machine",
  "scale_x": 1.0,
  "scale_y": 1.0,
  "delta_x": 0,
  "delta_y": 0
}
```

**Semantics (design intent):** Start from **reference_profile** ladder + cookie, apply **scale** about anchor (or about cookie), then **translate** by `(delta_x, delta_y)` so **`anchor_row`** matches the operator-measured global position. **Implementation later** would merge transforms into the absolute coordinates the loop already consumes—or the shell/Python loader would expand once at load time.

**Operator workflow:** Edit four numbers (or two if scale fixed) instead of twelve rows.

**Resize:** Adjust **`scale_x` / `scale_y`** when the buy column width or row spacing changes with zoom.

### 4.2 Phase B — Window-relative normalized coordinates

Add **`browser_rect`** (global) plus store **`cookie`** and **`store`** (and optionally each ladder row) as **normalized** coordinates:

- `cookie.u`, `cookie.v` in [0, 1] relative to `browser_rect`, **or**
- `cookie.x_offset`, `cookie.y_offset` in **pixels from top-left of browser_rect**.

**Expansion:** `global_x = browser_rect.left + u * browser_rect.width` (and similarly for y, respecting Quartz y direction conventions used elsewhere in the repo).

**Operator workflow:** Move window → update **`browser_rect`** once (e.g. from Accessibility API, or from a “click top-left corner / click bottom-right corner” calibration in a future tool). Cookie and ladder **u,v** stay stable if the **game layout inside the window** is stable.

**Resize:** Change **`browser_rect.width/height`**; normalized points move with the window frame automatically; if **inner** game UI does not scale linearly with window chrome, combine with **Phase A** scale factors.

### 4.3 Phase C — Calibration wizard (UX)

Short scripted flow (future):

1. Operator positions browser; runs **calibrate** mode.
2. Clicks **cookie**; clicks **time_machine** row (or top and bottom of visible buy list).
3. Tool infers **translation + vertical scale** (and optional horizontal offset) vs embedded template, then **writes** either expanded absolute JSON or **`layout_transform`** + anchors.

This reuses mental model from **`--learn`** in [`macos_mouse_click.py`](../../../osx/macos_mouse_click.py) but targets **profile authoring**, not runtime clicking.

### 4.4 Phase D — Detector upgrades (`cookie_clicker_detect_coords.py`)

When **`source_image`** is a screenshot, detector already outputs global coords. Design extensions:

- Detect **browser chrome box** (title bar + client area) vs full screen.
- Emit **`browser_rect`** + normalized subsidiary coords in the JSON for reproducibility across sessions.

Reduces dependence on a single global cookie point as the only “layout hint.”

---

## 5. Recommendation (ordering)

| Priority | Track | Rationale |
|----------|--------|-----------|
| **1** | **Phase A** (`layout_transform` or equivalent) | Smallest schema delta; immediate win for “moved window, same zoom” with **few numeric knobs**; easy to document next to current laptop workflow. |
| **2** | **Phase C** (wizard) | Reduces user error and avoids hand-editing JSON; composes with A or B. |
| **3** | **Phase B** (`browser_rect` + normalized) | Best for **resize-heavy** workflows; needs strict conventions for y-axis and chrome vs content. |
| **4** | **Phase D** (detector) | Best data at capture time; more CV/schema work. |

---

## 6. Non-goals (for this plan document)

- No changes to **`macos_mouse_click_loop.sh`**, **`cookie_clicker_detect_coords.py`**, or schema **in this plan**.
- No deprecation of absolute-coordinate profiles.

---

## 7. Open questions

1. **Quartz y-axis** — Confirm single convention (top-left vs bottom-left) across detector, preview, and profiles in any new math (document in [TERMINOLOGY](../TERMINOLOGY.md) when implemented).
2. **Scroll position** — Buy ladder assumes a **fixed scroll** in the store column; normalized layout does not fix scroll drift—call out in operator docs or add a “scroll to top” assumption.
3. **Multi-monitor** — `browser_rect` in global space remains valid; normalized coords should be **relative to that rect**, not to a single display.

---

## 8. References

- [`cookie_clicker_profile.defaults.json`](../../../osx/config/cookie_clicker_profile.defaults.json) · [`cookie_clicker_profile.laptop_only.json`](../../../osx/config/cookie_clicker_profile.laptop_only.json) · [`cookie_clicker_profile.sample.json`](../../../osx/config/cookie_clicker_profile.sample.json)
- [DEF-012](../defects/def-012-loop-profile-forces-preview-on-builtin.md) (builtin / coords-only preview behavior)
