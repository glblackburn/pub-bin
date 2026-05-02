# Plan 012 — Code review archive (`macos_mouse_click_loop.sh`)

**Status:** Session note (read-only review; not a normative product spec).

**Summary:** Archived review of [`osx/macos_mouse_click_loop.sh`](../../../osx/macos_mouse_click_loop.sh) companion to [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py).

## Purpose

Bash operator harness: a `while true` cycle of an optional **buy ladder** (fixed building order) then a long **cookie** burst. Each step invokes `macos_mouse_click.py` with **`-Y`**, **`-d 0`**, and **`--abort-on-mouse-move --mouse-move-threshold-px 20`** (see [`osx/README.md`](../README.md), DEF-010/011). Optional **`-P`** profile JSON, **`-D`** screenshot detection, preview/manifest flow (**`-N` / `-R` / `-A`**), and DEF-012-style **coords-only** vs drawable `source_image` handling.

## Strengths

- **`set -euET -o pipefail`** and structured **`usage` / `getopts`** validation (`-c` positive integer, `-B` enum, `-D` requires `-P`, detector path checks).
- **`click_target`** centralizes Python invocation and abort flags.
- **`load_profile_coordinates`** embeds Python that validates profile shape (cookie + ladder rows), sets **`COORDS_ONLY_PROFILE`**, and exports coordinates.
- **DEF-012 normalization** (lines 381–388 in the script): if **`-P`** resolves to the same file as the built-in default profile, clear **`profile_json`** so behavior matches omitting **`-P`** and preview is not forced incorrectly.
- **Preview gates**: **`-N`** with coords-only fails with a clear message; **`-R`** with coords-only explains the limitation; **`verify_preview_manifest`** checks profile and options hashes.
- **Tests/docs**: [`osx/tests/test_def012_loop_preview_coords_only.py`](../../../osx/tests/test_def012_loop_preview_coords_only.py); [`docs/osx/defects/def-012-loop-profile-forces-preview-on-builtin.md`](../defects/def-012-loop-profile-forces-preview-on-builtin.md).

## Risks / polish (informational)

1. **TUI debug always on** in **`run_once`**: `export MACOS_MOUSE_CLICK_DEBUG_TUI=yes` and `MACOS_MOUSE_CLICK_DEBUG_TUI_LOG=debug.json` are active while the nearby comment still says “uncomment … for debug”. Every cycle writes TUI debug to a fixed **`debug.json`** in the working directory unless the script is edited.
2. **Buy ladder vs embedded `order` list**: The Python `order` tuple in **`load_profile_coordinates`** and the shell **`run_buy_ladder`** sequence must be kept in sync manually; a drift would be a silent logic bug. As reviewed, they match (time_machine through cursor).
3. **Comments** above **`run_buy_ladder`**: Useful operator context but small typos (“f the screen”, “top f”).
4. **No pytest for the full live loop** (by design per [`DEVELOPMENT_NARRATIVE.md`](DEVELOPMENT_NARRATIVE.md)); safety is partial automation tests plus manual runs.

## Code quality

Matches repo Bash conventions (section headers, functions, heredoc Python for structured validation). Paths are anchored with **`script_dir`** next to the Python helpers.

## Follow-up

None unless the maintainer wants (e.g.) debug exports gated by env, comment fixes, more tests, or README alignment.
