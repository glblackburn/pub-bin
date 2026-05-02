<!-- 493b81a3-5f4d-4869-9445-21ddf8772098 -->
---
todos:
  - id: "analyze-wrap"
    content: "Confirm multi-line cell / row_height alignment in rich/table.py; verify only Setting has no_wrap in _build_editor_table"
    status: pending
  - id: "tighten-table-panel"
    content: "Update _build_editor_table + Panel: no_wrap/overflow on all columns; padding=0 (and collapse_padding) on Table; padding=0 on Panel"
    status: pending
  - id: "tests-heuristic"
    content: "Extend def009 heuristics + PTY/synthetic tests for spacer-only bordered rows"
    status: pending
  - id: "defect-docs"
    content: "Reopen DEF-009 or add DEF-010 + plan-002/README + new screenshot after fix verified"
    status: pending
isProject: false
---
# Plan: Fix extra blank lines in Rich pre-run TUI

## What you are seeing

Your transcript and screenshot show **full-width rows that contain only border characters and spaces** between the real header, separator, and data rows. That pattern is **not** the earlier DEF-009 “fused `╭` + `━` on one line” corruption; the frame is now structurally sane but **vertically bloated**.

## Most likely cause (Rich `Table` behavior)

In Rich’s `Table` renderer (`rich/table.py`), each row computes:

- `lines = console.render_lines(...)` per cell
- `row_height = max(len(cell) for cell in cells)`
- cells are then aligned to **`row_height`** via `_Segment.align_top` / `align_middle` / `align_bottom`

So **if any single cell in that row wraps to 2+ lines**, **every other cell in the same row is padded vertically** to match. Visually that reads as an **empty “spacer” line** between the text lines of the row (still inside the table border), and it can repeat **between every row** if multiple rows have the same issue.

Today only the **Setting** column sets `no_wrap=True` in `_build_editor_table`:

```716:733:osx/macos_mouse_click.py
    table = Table(
        show_header=True,
        header_style="bold cyan",
        expand=True,
        box=box.ROUNDED,
    )
    table.add_column("Setting", style="white", no_wrap=True)
    table.add_column("Value", style="green")
    table.add_column("Source", style="dim")
```

If **Value** or **Source** (or header cells) wrap under your effective terminal width / font metrics, you get the spacer effect even when the strings look short.

Secondary contributors worth ruling out:

- **Default padding**: Rich `Table` defaults to `padding=(0, 1)` and `Panel` defaults to `padding=(0, 1)` (see `rich/table.py` and `rich/panel.py`). That is **horizontal** padding in Rich’s unpack, but tightening **`padding=0`** on both is still a low-cost experiment for a denser layout.
- **Terminal profile**: macOS Terminal “line spacing” &gt; 1 visually doubles every line for **all** output (not just this app). Worth one manual check in Profile → Font, because you said “it was not this way a while back.”

## Recommended code changes (in order)

1. **`_build_editor_table` (`osx/macos_mouse_click.py`)**
   - Set **`no_wrap=True`** (and a sensible **`overflow`**, e.g. `"ellipsis"` or `"ignore"`) on **all three** columns, not only `Setting`.
   - Optionally set **`padding=0`** and **`collapse_padding=True`** on the `Table` for a tighter grid (matches older “dense” TUIs).
   - Confirm **`leading=0`** and **`show_lines=False`** remain defaults (do not accidentally enable `show_lines` / `leading`).

2. **`Panel(...)` in `_run_rich_pre_run_editor_loop`**
   - Pass **`padding=0`** (or `(0,0)`) on the outer `Panel` wrapping the table so the inner frame is not inset with an extra blank band under the title when Rich wraps the inner renderable.

3. **Optional: constrain render height for this print only**
   - If investigation shows `ConsoleOptions.height` is ever non-`None` for your environment, use Rich’s supported pattern to avoid vertical “fill” padding in `render_lines` (only applies when `options.height` is set). First confirm with a tiny debug print of `console.options` / `child_options` in a scratch branch, or reproduce with `python -c` + same `Console()` setup.

4. **Tests (`osx/tests/def009_layout_heuristics.py` + PTY test)**
   - Add a heuristic or assertion for **“spacer row”**: a table line that matches `│` borders but has **no** alphanumeric content between left/right borders (after CSI strip). This catches the regression you still see, distinct from the fused `╭`+`━` check.
   - Keep the existing fused-line detector; both can coexist.

5. **Defect bookkeeping**
   - **DEF-009 is currently documented as Fixed** in `docs/osx/defects/def-009-…md`, `docs/osx/defects/README.md`, and `plan-002` — but your report means either **reopen DEF-009** or file **DEF-010** (“vertical spacer rows in Rich editor”) once a fix lands, with updated screenshots under `osx/tests/screenshots/`.

## Verification steps

- Render the same `Panel`+`Table` to a **`StringIO` + `Console(..., force_terminal=True)`** at the same width as your terminal and assert **no spacer-only rows** between header and data.
- Run **`make -C osx test`** (includes `test_def009_*` and table nav PTY tests on darwin).
- Manual: same command you used with `MACOS_MOUSE_CLICK_DEBUG_TUI=yes` in Terminal.app at your usual font size.
