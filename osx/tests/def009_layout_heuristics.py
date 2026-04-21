"""DEF-009 / DEF-010: heuristics for Rich pre-run table / panel layout issues in PTY transcripts.

See ``docs/osx/defects/def-009-rich-pre-run-tui-table-layout-corruption.md``.
"""

from __future__ import annotations

import re
from typing import Final

# CSI / SGR sequences (subset sufficient for Rich truecolor output).
_CSI_RE: Final = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

# Rich Panel top border uses light horizontal U+2500 (─). Inner ``Table`` header rules
# use heavy U+2501 (━). Those belong on **different** physical lines; the same line
# containing both ``╭`` and ``━`` is the dominant PTY/automation signature for DEF-009
# (see ``test_def009`` capture: fused panel title row + inner table rule on one line).
_HEAVY_HORIZ: Final = "\u2501"  # ━


def strip_csi(text: str) -> str:
    """Remove CSI sequences so box glyphs sit contiguously for boundary checks."""
    prev = None
    cur = text
    while prev != cur:
        prev = cur
        cur = _CSI_RE.sub("", cur)
    return cur


def _is_probable_editor_table_line(line: str) -> bool:
    """True if this line looks like the Rich panel + table body (not pure NDJSON / stderr)."""
    if "│" not in line and "┃" not in line:
        return False
    # Pure debug / JSON lines should not mix with table glyphs in a healthy PTY merge.
    if line.strip().startswith("{") and "selected_index" in line:
        return False
    markers = (
        "Setting",
        "Value",
        "Source",
        "Mode",
        "Count",
        "Delay",
        "learn",
        "cli",
        "fixed",
        "at-cursor",
        "┏",
        "┡",
        "┗",
        "┏━",
        "╭",
        "╰",
    )
    return any(m in line for m in markers)


def def010_vertical_spacer_reason(transcript: str) -> str | None:
    """Return DEF-010 reason if any line is a spacer-only interior row, else ``None``.

    Use this when asserting the editor does not emit Rich ``row_height`` padding rows,
    without applying other DEF-009 heuristics that false-positive on narrow ``HEAVY_HEAD``
    tables (e.g. legitimate ``┃┃`` next to the panel border).
    """
    for raw in transcript.splitlines():
        vis = strip_csi(raw)
        if _is_spacer_only_inner_table_row(vis):
            return (
                "DEF-010: vertical spacer row (table interior with only pipes/spaces, "
                "typical of Rich row_height padding when a cell wrapped): "
                f"{raw[:240]!r}"
            )
    return None


def _is_spacer_only_inner_table_row(vis: str) -> bool:
    """True if stripped line is only column pipes + whitespace (DEF-010 row-height padding).

    Rich aligns every cell in a row to ``max`` rendered line count; wrapped cells create
    apparent blank interior rows. Real header/data rows always include some non-pipe
    printable content; rule rows use ``├``, ``─``, corners, etc.
    """
    if len(vis) < 25:
        return False
    pipe_like = vis.count("│") + vis.count("┃")
    if pipe_like < 3:
        return False
    return bool(re.fullmatch(r"[\s│┃]+", vis))


def _fused_panel_top_with_inner_heavy_rules(vis: str) -> bool:
    """Detect Panel outer top (``╭`` + light ``─``) fused onto inner Table heavy rules (``━``)."""
    if "╭" not in vis:
        return False
    if _HEAVY_HORIZ not in vis:
        return False
    # A normal Panel top row ends with ``╮`` using only light ``─`` between corners.
    # ``━`` on that same row means inner table box-drawing bled onto the panel border line.
    return True


def layout_corruption_reason(
    transcript: str,
    *,
    ignore_fused_panel_heavy_line: bool = False,
) -> str | None:
    """Return a human-readable reason if DEF-009/DEF-010 layout issues are detected, else ``None``.

    ``ignore_fused_panel_heavy_line``: when True, skip the ``╭``+``━`` same-line fusion check.
    Default Rich ``HEAVY_HEAD`` nested ``Table`` can trip that heuristic even without
    stdout/stderr interleave; live PTY tests use this with the legacy editor layout while
    ``test_def009_detects_fused_panel_top_and_inner_heavy_rules`` still guards the signal.
    """
    for raw in transcript.splitlines():
        vis = strip_csi(raw)
        if not ignore_fused_panel_heavy_line and _fused_panel_top_with_inner_heavy_rules(vis):
            return (
                "DEF-009: panel top (╭…─) fused on one line with inner table heavy rules "
                f"(━ U+2501); truncated or merged box draw: {raw[:240]!r}"
            )
        if "│" not in raw and "┃" not in raw:
            continue
        # DEF-010: must run before ``_is_probable_editor_table_line`` (spacer rows lack labels).
        if _is_spacer_only_inner_table_row(vis):
            return (
                "DEF-010: vertical spacer row (table interior with only pipes/spaces, "
                "typical of Rich row_height padding when a cell wrapped): "
                f"{raw[:240]!r}"
            )
        if not _is_probable_editor_table_line(raw):
            continue
        # Telemetry merged into a row that still shows table borders (stdout/stderr interleave).
        if "MACOS_MOUSE_CLICK_TUI_STATE" in raw:
            return (
                "DEF-009: MACOS_MOUSE_CLICK_TUI_STATE appears inside a table row "
                f"(stderr/stdout interleaving): {raw[:240]!r}"
            )
        # Adjacent duplicate column rules (screenshot: double verticals).
        if "││" in vis:
            return f"DEF-009: doubled light vertical rule (││) after CSI strip: {raw[:240]!r}"
        if "┃┃" in vis:
            return f"DEF-009: doubled heavy vertical rule (┃┃) after CSI strip: {raw[:240]!r}"
        # ASCII double-pipe column corruption (some terminals / legacy paths).
        if "||" in vis:
            return f"DEF-009: doubled ASCII pipe (||) after CSI strip: {raw[:240]!r}"
    return None
