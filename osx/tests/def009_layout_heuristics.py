"""DEF-009: heuristics to detect Rich pre-run table / panel layout corruption in PTY transcripts.

See ``docs/osx/defects/def-009-rich-pre-run-tui-table-layout-corruption.md``.
"""

from __future__ import annotations

import re
from typing import Final

# CSI / SGR sequences (subset sufficient for Rich truecolor output).
_CSI_RE: Final = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


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


def layout_corruption_reason(transcript: str) -> str | None:
    """Return a human-readable reason if DEF-009-style corruption is detected, else ``None``."""
    for raw in transcript.splitlines():
        if "│" not in raw and "┃" not in raw:
            continue
        if not _is_probable_editor_table_line(raw):
            continue
        # Telemetry merged into a row that still shows table borders (stdout/stderr interleave).
        if "MACOS_MOUSE_CLICK_TUI_STATE" in raw:
            return (
                "DEF-009: MACOS_MOUSE_CLICK_TUI_STATE appears inside a table row "
                f"(stderr/stdout interleaving): {raw[:240]!r}"
            )
        vis = strip_csi(raw)
        # Adjacent duplicate column rules (screenshot: double verticals).
        if "││" in vis:
            return f"DEF-009: doubled light vertical rule (││) after CSI strip: {raw[:240]!r}"
        if "┃┃" in vis:
            return f"DEF-009: doubled heavy vertical rule (┃┃) after CSI strip: {raw[:240]!r}"
        # ASCII double-pipe column corruption (some terminals / legacy paths).
        if "||" in vis:
            return f"DEF-009: doubled ASCII pipe (||) after CSI strip: {raw[:240]!r}"
    return None
