---
id: DEF-012
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
isProject: false
todos:
  - id: shell-detect
    content: "macos_mouse_click_loop.sh — detect coords-only (source_image missing, empty, or builtin); export flag or env for downstream gates"
    status: pending
  - id: shell-gate
    content: "Gate render_preview_artifacts, verify_preview_manifest (-R + coords-only error), confirm_preview_before_clicks; -N + coords-only clear exit"
    status: pending
  - id: docs-readme
    content: "osx/README.md — document -P, builtin, -N/-R/-A/-D interaction"
    status: pending
  - id: tests
    content: "osx/tests — regression for -P defaults/builtin without OpenCV preview failure"
    status: pending
  - id: close-def
    content: "After merge — update def-012 status, plan-002 Defect summary row, defects README, manual verification"
    status: pending
---

### DEF-012: `-P` profile path forces preview; `source_image: "builtin"` breaks OpenCV load

**Terminology:** **Profile JSON** — Cookie Clicker coordinate file consumed by [`macos_mouse_click_loop.sh`](../../../osx/macos_mouse_click_loop.sh) (`-P`) and [`cookie_clicker_preview_plan.py`](../../../osx/cookie_clicker_preview_plan.py). **`builtin`** — sentinel string in `source_image` meaning “baked-in / defaults coordinates; no detector screenshot path” (see [`cookie_clicker_profile.defaults.json`](../../../osx/config/cookie_clicker_profile.defaults.json)). Shared **CSI** / **PTY** vocabulary (where relevant to other defects) is defined in **[`README.md`](README.md)** and **[DEF-011](def-011-mouse-move-abort-arm-threshold-annulus.md)**.

- **Status:** **Open** — implementation tracked via **`todos`** in YAML frontmatter above.
- **Severity:** Medium — operator cannot use `-P` with coords-only profiles (including the repo defaults file) without supplying a fake image path or hitting a hard error before clicks.
- **Opened:** 2026-04-28
- **Affects:** [`osx/macos_mouse_click_loop.sh`](../../../osx/macos_mouse_click_loop.sh); [`osx/cookie_clicker_preview_plan.py`](../../../osx/cookie_clicker_preview_plan.py); profiles with `"source_image": "builtin"` (e.g. [`osx/config/cookie_clicker_profile.defaults.json`](../../../osx/config/cookie_clicker_profile.defaults.json)).

---

### Observed

From repo root, with a profile that sets coordinates but uses **`builtin`** for `source_image`:

```text
$ ./osx/macos_mouse_click_loop.sh -P osx/config/cookie_clicker_profile.defaults.json
[ WARN:0@0.022] global loadsave.cpp:278 findDecoder imread_('/Users/.../pub-bin/builtin'): can't open/read file: check file path/integrity
Error: unable to load source image: /Users/.../pub-bin/builtin
```

OpenCV receives **`os.path.abspath("builtin")`** (cwd + `/builtin`), not an image file.

---

### Expected behavior

- **`-P`** should mean: load **cookie** and **ladder_rows** (and preview defaults) from this JSON for automation — the same semantic role as the implicit default profile when `-P` is omitted.
- **Preview** (annotated PNG + manifest) should run only when the operator wants visual verification against a **real** screenshot, or when **`source_image`** in the profile is a path to an existing image (typical output of [`cookie_clicker_detect_coords.py`](../../../osx/cookie_clicker_detect_coords.py) / `-D`).
- **`source_image: "builtin"`** (or absent / empty, if we document that) should **not** imply “open a file named `builtin`” for `cv2.imread`.

---

### Design intent: `profile_json` as override for `default_profile_json`, not a preview switch

In **`load_profile_coordinates`**, the file that supplies coordinates is chosen the same way whether the operator uses the built-in default path or an explicit path:

```180:184:osx/macos_mouse_click_loop.sh
function load_profile_coordinates {
    coord_profile=${profile_json}
    if [ -z "${coord_profile}" ]; then
        coord_profile="${default_profile_json}"
    fi
```

**Desired effect:** setting **`-P`** should be equivalent to “use this JSON path wherever **`coord_profile`** would otherwise be **`default_profile_json`**” — i.e. **`-P` is only an override for which profile file feeds the coordinate `eval`**. It should **not** imply additional behavior (OpenCV preview, manifest generation, confirmation prompts) solely because the variable **`profile_json`** is non-empty. Today, other functions key off **`profile_json`** directly, so **`-P`** acts like a **side channel** (preview always on) instead of a **pure override** of **`default_profile_json`**. The fix should align the rest of the script with the same mental model as **`coord_profile`**: preview and manifest steps depend on **whether the profile can support preview** (drawable **`source_image`**) and on explicit flags (**`-N`**, **`-R`**, **`-A`**), not merely on “operator passed **`-P`**.”

---

### Root cause

1. **`macos_mouse_click_loop.sh`** calls **`render_preview_artifacts`** whenever **`profile_json`** is non-empty, **unconditionally**, before clicks (see **`render_preview_artifacts`** in [`macos_mouse_click_loop.sh`](../../../osx/macos_mouse_click_loop.sh) → [`cookie_clicker_preview_plan.py`](../../../osx/cookie_clicker_preview_plan.py)).
2. Omitting **`-P`** leaves **`profile_json`** empty → **`render_preview_artifacts`** returns immediately → no OpenCV path. Passing **`-P`** to the **same** defaults JSON therefore changes behavior beyond “which file supplies coordinates.”
3. **`cookie_clicker_preview_plan.py`** resolves `source_image` from the profile and always **`cv2.imread`** it; it does not treat **`builtin`** as a sentinel.

---

### Why this is a defect (not user error)

Help text presents **`-P`** as the coordinate profile path; operators reasonably use **`-P`** to swap JSON without intending the preview pipeline. Coupling “profile path set” to “always generate preview artifacts” contradicts coords-only / **`builtin`** profiles shipped in-repo.

---

### Fix plan and implementation

**Goal:** **`-P` / `profile_json`** should match **`load_profile_coordinates`**: only override which file becomes **`coord_profile`** (same role as **`default_profile_json`** when **`-P`** is omitted). Do not invoke **`cookie_clicker_preview_plan.py`** before clicks when **`source_image`** is **`builtin`** or missing/empty (per agreed rule). Preserve preview + manifest when the profile has a drawable **`source_image`** and for **`-N`** / **`-R`** where valid.

**1. Coords-only detection** — After the profile path is known (and after **`-D`** if applicable), classify **coords-only** when `source_image` is missing, empty, or exactly **`builtin`** (case-sensitive, matching existing JSON). **Drawable preview** when `source_image` is a non-empty string other than **`builtin`** and the path is a regular file. Extend the **`python3 - "${coord_profile}"`** block in **`load_profile_coordinates`** to emit shell assignments (e.g. **`COORDS_ONLY_PROFILE=true`** or **`PROFILE_PREVIEW_MODE=skip|draw`**) for **`eval`**.

**2. Gate loop stages (`macos_mouse_click_loop.sh`)**

| Stage | Coords-only (`builtin` / no path) | Drawable `source_image` |
|-------|-------------------------------------|-------------------------|
| `load_profile_coordinates` | Unchanged | Unchanged |
| `render_preview_artifacts` | **Skip** | Run (today) |
| `verify_preview_manifest` | **Skip**; if **`-R`**, **fail fast** before clicks (no manifest to verify — see bullets below) | Honor **`-R`** |
| `confirm_preview_before_clicks` | **Skip** (no artifacts) | Today’s behavior unless **`-A`** |

**`-R` + coords-only:** **Fail fast** with a clear message (cannot require a matching manifest if preview was never generated / no backing image). Do not silently skip **`-R`**.

**`-N` (preview only) + coords-only:** **Exit non-zero** with a message: preview requires a real `source_image` or run detection (**`-D`**) first — do not call OpenCV on **`builtin`**.

**3. Optional: friendlier error in `cookie_clicker_preview_plan.py`**

If the script is invoked directly with **`builtin`**, optionally detect and **`SystemExit`** with text that explains the sentinel (secondary; main fix is the loop).

**4. Documentation**

- **[`osx/README.md`](../../../osx/README.md):** **`-P`** vs preview; **`builtin`**; interaction of **`-N`**, **`-R`**, **`-A`**, **`-D`**.
- On close: update **[`docs/osx/plans/plan-002-macos-mouse-click-terminal-ux.md`](../plans/plan-002-macos-mouse-click-terminal-ux.md)** Defect summary row and **[`docs/osx/defects/README.md`](README.md)** status.

**5. Tests**

Regression: **`-P`** with defaults JSON (or minimal fixture with **`builtin`**) without **`-N`**/**`-R`** must not run preview / must not emit **`unable to load source image`** (pytest subprocess or shell test under **`osx/tests/`**, consistent with existing loop coverage if any).

**6. Regression check (manual, after fix)**

- `./osx/macos_mouse_click_loop.sh -P osx/config/cookie_clicker_profile.defaults.json -A -c 1` (or **Ctrl+C** after first cycle): reaches **`Running:`** / clicks without OpenCV error on **`builtin`**.
- Profile with a real **`source_image`** path: preview artifacts still generated when drawable; **`-R`** still validates when applicable.

**Non-goals:** Synthetic blank canvas in **`cookie_clicker_preview_plan.py`** for **`builtin`** unless separately requested.

**Git / Completed:** — (populate when fixed per repo defect workflow).
