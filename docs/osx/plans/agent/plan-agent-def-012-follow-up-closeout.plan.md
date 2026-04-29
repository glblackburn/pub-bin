<!-- Cursor agent plan (canonical copy in-repo; do not use ~/.cursor/plans/). -->
---
isProject: false
todos:
  - id: close-def012-docs
    content: "def-012.md Fixed + Resolution; plan-002 + defects README; YAML todos completed"
    status: completed
  - id: manual-verify-def012
    content: "Manual verification blurb in def-012 + plan-002 (automated + optional operator §6)"
    status: completed
  - id: agent-readme-row
    content: "This file + docs/osx/plans/agent/README.md row"
    status: completed
  - id: optional-preview-ux
    content: "cookie_clicker_preview_plan.py — coords-only source_image SystemExit before imread"
    status: completed
  - id: optional-dry-paths
    content: "macos_mouse_click_loop.sh — remove 2>/dev/null on samefile normalize so stderr visible"
    status: completed
---

# DEF-012 follow-up: defect close-out and optional hardening

**Defect:** [`../../defects/def-012-loop-profile-forces-preview-on-builtin.md`](../../defects/def-012-loop-profile-forces-preview-on-builtin.md)

## What shipped in `deb0389` (reference)

[`osx/macos_mouse_click_loop.sh`](../../../../osx/macos_mouse_click_loop.sh): **`COORDS_ONLY_PROFILE`** from profile JSON; gate preview / confirm / **`-N`** / **`-R`**; **`os.path.samefile`** clears **`profile_json`** when **`-P`** points at the built-in default file; tests in [`osx/tests/test_def012_loop_preview_coords_only.py`](../../../../osx/tests/test_def012_loop_preview_coords_only.py); [`osx/README.md`](../../../../osx/README.md).

## This follow-up pass (documentation + optional hardening)

1. **Defect / plan hub** — Close **DEF-012** in [`def-012`…](../../defects/def-012-loop-profile-forces-preview-on-builtin.md), [`plan-002`](../plan-002-macos-mouse-click-terminal-ux.md), [`defects/README`](../../defects/README.md).
2. **Manual verification** — Record automated **`test_def012`** + optional operator §6 in the defect file and plan-002 blurb.
3. **Preview helper** — [`osx/cookie_clicker_preview_plan.py`](../../../../osx/cookie_clicker_preview_plan.py): fail fast on coords-only **`source_image`** (aligned with loop semantics).
4. **`samefile` stderr** — Stop discarding stderr on the **`samefile`** normalization probe so rare **`OSError`** paths surface.

## Deferred (not in this pass)

- Shared Python module for coords-only vs drawable (single source of truth).
- **`source_image`** paths relative to profile JSON directory.
- Rate-control Phase 2 loop wiring — [`plan-agent-cookie-clicker-rate-control.plan.md`](plan-agent-cookie-clicker-rate-control.plan.md).
