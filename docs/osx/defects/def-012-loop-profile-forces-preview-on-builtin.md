---
id: DEF-012
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
  - ../plans/agent/plan-agent-def-012-follow-up-closeout.plan.md
isProject: false
todos:
  - id: shell-detect
    content: "macos_mouse_click_loop.sh — detect coords-only (source_image missing, empty, or builtin); export flag or env for downstream gates"
    status: completed
  - id: shell-gate
    content: "Gate render_preview_artifacts, verify_preview_manifest (-R + coords-only error), confirm_preview_before_clicks; -N + coords-only clear exit"
    status: completed
  - id: docs-readme
    content: "osx/README.md — document -P, builtin, -N/-R/-A/-D interaction"
    status: completed
  - id: tests
    content: "osx/tests — regression for -P defaults/builtin without OpenCV preview failure"
    status: completed
  - id: close-def
    content: "After merge — update def-012 status, plan-002 Defect summary row, defects README, manual verification"
    status: completed
---

### DEF-012: `-P` profile path forces preview; `source_image: "builtin"` breaks OpenCV load

**Terminology:** **Profile JSON** — Cookie Clicker coordinate file consumed by [`macos_mouse_click_loop.sh`](../../../osx/macos_mouse_click_loop.sh) (`-P`) and [`cookie_clicker_preview_plan.py`](../../../osx/cookie_clicker_preview_plan.py). **`builtin`** — sentinel string in `source_image` meaning “baked-in / defaults coordinates; no detector screenshot path” (see [`cookie_clicker_profile.defaults.json`](../../../osx/config/cookie_clicker_profile.defaults.json)). Shared **CSI** / **PTY** vocabulary (where relevant to other defects) is defined in **[`README.md`](README.md)** and **[DEF-011](def-011-mouse-move-abort-arm-threshold-annulus.md)**.

- **Status:** **Fixed** (script + tests + docs close-out).
- **Severity:** Medium (was) — operator could not use **`-P`** with coords-only profiles without OpenCV **`imread`** failing before clicks.
- **Opened:** 2026-04-28
- **Completed:** 2026-04-28
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

1. **`macos_mouse_click_loop.sh`** called **`render_preview_artifacts`** whenever **`profile_json`** was non-empty, **unconditionally**, before clicks (see **`render_preview_artifacts`** in [`macos_mouse_click_loop.sh`](../../../osx/macos_mouse_click_loop.sh) → [`cookie_clicker_preview_plan.py`](../../../osx/cookie_clicker_preview_plan.py)).
2. Omitting **`-P`** left **`profile_json`** empty → **`render_preview_artifacts`** returned immediately → no OpenCV path. Passing **`-P`** to the **same** defaults JSON therefore changed behavior beyond “which file supplies coordinates.”
3. **`cookie_clicker_preview_plan.py`** resolved `source_image` from the profile and always **`cv2.imread`** it; it did not treat **`builtin`** as a sentinel.

---

### Why this is a defect (not user error)

Help text presents **`-P`** as the coordinate profile path; operators reasonably use **`-P`** to swap JSON without intending the preview pipeline. Coupling “profile path set” to “always generate preview artifacts” contradicted coords-only / **`builtin`** profiles shipped in-repo.

---

### Resolution

1. **`load_profile_coordinates`** embedded Python emits **`COORDS_ONLY_PROFILE=true|false`** from **`source_image`** (missing / empty / **`builtin`** / non-file after **`abspath`** + **`isfile`**).
2. **`render_preview_artifacts`** and **`confirm_preview_before_clicks`** return early when coords-only (or when **`profile_json`** is empty as before).
3. **`-N`** with explicit coords-only **`-P`**: exit **2** with a clear message (no OpenCV). **`-R`** with coords-only: **`usage`** + exit **1**.
4. **`os.path.samefile(profile_json, default_profile_json)`** clears **`profile_json`** so an explicit path to the built-in default matches **omitting `-P`** (including **`-N`** preview-only exit **0** parity).
5. **`cookie_clicker_preview_plan.py`**: **`SystemExit`** with an explanatory message when **`source_image`** is coords-only (direct invocation).
6. **`samefile` normalization:** stderr from Python is no longer discarded (**`2>/dev/null`** removed) so **`samefile`** failures are visible.
7. **Docs:** [`osx/README.md`](../../../osx/README.md); follow-up plan **[`plan-agent-def-012-follow-up-closeout.plan.md`](../plans/agent/plan-agent-def-012-follow-up-closeout.plan.md)**.

**Tests:** [`osx/tests/test_def012_loop_preview_coords_only.py`](../../../osx/tests/test_def012_loop_preview_coords_only.py).

**Git:** `deb0389107dce98b0f7927e080523ecf069914c9` — loop + README + [`test_def012_loop_preview_coords_only.py`](../../../osx/tests/test_def012_loop_preview_coords_only.py). Follow-up on **`main`** (defect/plan close-out, **`cookie_clicker_preview_plan.py`** coords-only **`SystemExit`**, **`samefile`** stderr, **`test_preview_plan_builtin_source_image_exits_before_imread`**) — see **`git log --follow`** for this file under **`docs/osx/defects/`**.

---

### Fix plan and implementation (historical checklist — all landed)

**Goal:** **`-P` / `profile_json`** should match **`load_profile_coordinates`**: only override which file becomes **`coord_profile`** (same role as **`default_profile_json`** when **`-P`** is omitted). Do not invoke **`cookie_clicker_preview_plan.py`** before clicks when **`source_image`** is **`builtin`** or missing/empty (per agreed rule). Preserve preview + manifest when the profile has a drawable **`source_image`** and for **`-N`** / **`-R`** where valid.

**1–6.** As originally specified in the open defect; see **Resolution** above.

**Non-goals:** Synthetic blank canvas in **`cookie_clicker_preview_plan.py`** for **`builtin`** unless separately requested.

---

### Manual verification

- **2026-04-28** — **Automated:** `osx/tests/test_def012_loop_preview_coords_only.py` passes; `make -C osx test` recommended after follow-up commit.
- **Operator (§6 bullets, optional):** `./osx/macos_mouse_click_loop.sh -P osx/config/cookie_clicker_profile.defaults.json -A -c 1` (or **Ctrl+C** after first cycle): no OpenCV **`imread`** error on **`builtin`**; profile with drawable **`source_image`** still generates preview and honors **`-R`** when applicable.
