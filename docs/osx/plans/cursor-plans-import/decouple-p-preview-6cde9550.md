<!-- 6cde9550-b52d-4c5d-b4f9-316a1b6be015 -->
---
todos:
  - id: "gate-preview"
    content: "macos_mouse_click_loop.sh: derive coords_only from profile source_image; gate render/verify/confirm; -R + coords_only error; -N + coords_only clear exit"
    status: pending
  - id: "docs"
    content: "osx/README.md: document -P vs preview, builtin sentinel, -R/-N interaction"
    status: pending
  - id: "tests"
    content: "Add regression test (pytest or shell) for -P defaults/builtin path without OpenCV preview failure"
    status: pending
isProject: false
---
# Decouple `-P` from mandatory preview (builtin / coords-only profiles)

## Defect summary

- **[osx/macos_mouse_click_loop.sh](osx/macos_mouse_click_loop.sh)** always calls `render_preview_artifacts` whenever `profile_json` is set ([`render_preview_artifacts` → `cookie_clicker_preview_plan.py`](osx/macos_mouse_click_loop.sh) around the main sequence after `load_profile_coordinates`).
- **[osx/config/cookie_clicker_profile.defaults.json](osx/config/cookie_clicker_profile.defaults.json)** (and any copy) uses `"source_image": "builtin"` as a sentinel: coordinates only, no screenshot.
- **[osx/cookie_clicker_preview_plan.py](osx/cookie_clicker_preview_plan.py)** always `cv2.imread`s `source_image` after `os.path.abspath`, so `"builtin"` becomes `cwd/builtin` and fails.

**Expected behavior:** `-P` selects the JSON used for coordinates (`load_profile_coordinates`). Preview is optional unless the operator explicitly asks for it (`-N`), requires manifest verification (`-R`), or the profile supplies a real `source_image` path suitable for drawing.

## Proposed behavior

1. **Detect “coords-only / no preview background”** after loading JSON (same Python one-liner block used for coords is a natural place, or a tiny helper): treat `source_image` as missing or non-file when it is absent, empty, or exactly **`builtin`** (case-sensitive to match existing JSON contract).

2. **When `profile_json` is set and preview is skipped** (coords-only):
   - Do **not** run `render_preview_artifacts`.
   - Do **not** run `verify_preview_manifest` (already no-op unless `-R`; if `-R` with coords-only, **fail fast** with a clear `usage`/stderr message: cannot require manifest without a drawable `source_image`).
   - Do **not** run `confirm_preview_before_clicks` (no artifacts to review).

3. **When `source_image` is a real path** (existing detector output / sample profiles): keep current behavior — generate preview, optional `-R`/`-A` as today.

4. **`-N` (preview only) with coords-only profile:** exit **non-zero** with a clear message (“preview requires a real `source_image` in the profile or use `-D` …”), rather than calling OpenCV on `builtin`.

5. **Docs:** [osx/README.md](osx/README.md) (or the section that documents `-P`/`-N`/`-R`): state that `source_image: "builtin"` means coords-only; preview is skipped unless a real image path is present; `-R` + builtin is invalid.

6. **Tests:** If there is shell-level or pytest coverage for the loop, add one case: `-P` defaults JSON (or minimal fixture with `builtin`) without `-N`/`-R` does not invoke preview script (e.g. grep log / mock / exit 0 dry path). If no harness exists, a small **pytest** that shells out with `bash -c` and asserts no “unable to load source image” is enough.

## Files to touch

| File | Change |
|------|--------|
| [osx/macos_mouse_click_loop.sh](osx/macos_mouse_click_loop.sh) | Introduce a flag or `PREVIEW_SKIPPED` from embedded Python reading `source_image`; gate `render_preview_artifacts`, `verify_preview_manifest` (with `-R` error), `confirm_preview_before_clicks`. |
| [osx/README.md](osx/README.md) | Document `builtin` + `-P` semantics. |
| Optional: [docs/osx/defects/](docs/osx/defects/) | Short defect note linking loop + preview coupling (if the repo keeps DEF-* style for this product). |
| [osx/tests/](osx/tests/) or new test | Regression for `-P` + builtin without preview. |

## Non-goals

- Changing `cookie_clicker_preview_plan.py` to synthesize a fake canvas for `builtin` unless you explicitly want visual previews without a screenshot (out of scope unless requested).
