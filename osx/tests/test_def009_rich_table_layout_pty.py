"""DEF-009: regression tests for Rich pre-run table / panel layout corruption (PTY transcript).

See ``docs/osx/defects/def-009-rich-pre-run-tui-table-layout-corruption.md``.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import pytest

from def009_layout_heuristics import layout_corruption_reason, strip_csi

pytest.importorskip("rich", reason="Rich pre-run editor tests need rich")


def test_def009_clean_synthetic_rich_panel_has_no_corruption() -> None:
    """Sanity: default Rich Panel+Table render must not trip heuristics."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    buf = io.StringIO()
    c = Console(file=buf, width=120, force_terminal=True, color_system="truecolor")
    t = Table(show_header=True, header_style="bold cyan", expand=True)
    t.add_column("Setting", style="white", no_wrap=True)
    t.add_column("Value", style="green")
    t.add_column("Source", style="dim")
    t.add_row(
        Text("Mode", style="bold black on bright_cyan"),
        Text("learn", style="bold black on bright_cyan"),
        Text("cli", style="bold black on bright_cyan"),
    )
    c.print(
        Panel(
            t,
            title="[bold cyan]macOS mouse click[/] — review / edit",
            border_style="cyan",
        )
    )
    assert layout_corruption_reason(buf.getvalue()) is None


def test_def009_detects_doubled_light_vertical() -> None:
    bad = (
        "╭─ macOS mouse click — review / edit ─╮\n"
        "│ │ \x1b[1mMode\x1b[0m │ learn │ cli │\n"
        "╰──────────────────────────────────────╯\n"
    )
    # Force impossible adjacent light verticals (not the legitimate ``│ │`` panel+table gap).
    bad_corrupt = bad.replace("│ │ \x1b[1mMode", "││\x1b[1mMode", 1)
    assert layout_corruption_reason(bad) is None
    r = layout_corruption_reason(bad_corrupt)
    assert r is not None and "││" in r


def test_def009_detects_doubled_heavy_vertical() -> None:
    line = "│ ┃┃\x1b[1mSetting\x1b[0m ┃ Value ┃ Source ┃ │"
    assert "┃┃" in strip_csi(line)
    r = layout_corruption_reason(line)
    assert r is not None and "┃┃" in r


def test_def009_detects_debug_marker_inside_table_row() -> None:
    corrupt = (
        "╭─ macOS mouse click — review / edit ─╮\n"
        "│ │ \x1b[1mMode\x1b[0m │ learn │ "
        "2026-04-21T00:00:00 MACOS_MOUSE_CLICK_TUI_STATE {\"event\":\"draw\"}\n"
    )
    r = layout_corruption_reason(corrupt)
    assert r is not None and "MACOS_MOUSE_CLICK_TUI_STATE" in r


def test_def009_detects_fused_panel_top_and_inner_heavy_rules() -> None:
    """PTY capture (automation 40×120): panel ``╭`` row shares a line with inner ``Table`` ``━``."""
    # Stripped shape only — CSI stripped the same way as ``layout_corruption_reason``.
    fused_vis = (
        "╭───────────────────────────────────────── macOS mouse click — review / edit"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩ │"
    )
    r = layout_corruption_reason(fused_vis + "\n")
    assert r is not None and "fused" in r.lower() and "2501" in r


@pytest.mark.darwin
@pytest.mark.table_nav
def test_def009_subprocess_editor_transcript_layout_pexpect(
    pexpect_module: Any,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    """Live PTY: assert we still observe DEF-009 structural corruption (open defect).

    ``make -C osx test`` uses the same 40×120 geometry as other Rich PTY tests; the
    captured transcript fuses the Panel top row with inner ``Table`` heavy rules on
    one line (``╭`` + ``━``). When DEF-009 is fixed in the product, flip this assertion
    to ``assert reason is None`` and update the defect status.
    """
    pytest.importorskip("pexpect", reason="pty tests need pexpect")

    from pty_harness import base_child_env, spawn_clicker_pexpect
    from test_rich_table_nav_down_pty import (
        _drain_until_setting_from,
        _transcript_after_editor_banner,
    )

    pexpect = pexpect_module
    log_path = Path(tmp_path) / "def009.ndjson"
    env = base_child_env(
        {
            "TERM": "xterm-256color",
            "MACOS_MOUSE_CLICK_DEBUG_TUI": "1",
            "MACOS_MOUSE_CLICK_DEBUG_TUI_LOG": str(log_path),
        }
    )
    child = spawn_clicker_pexpect(
        pexpect,
        ["--learn", "--interactive", "-n", "2", "-d", "3.5"],
        cwd=repo_root,
        env=env,
        timeout=120,
        dimensions=(40, 120),
        maxread=2_000_000,
    )
    child.delaybeforesend = 0.2
    try:
        child.expect("review / edit", timeout=60)
        base = _transcript_after_editor_banner(child)
        transcript = _drain_until_setting_from(child, base, "Mode", timeout=15.0)
        reason = layout_corruption_reason(transcript)
        assert reason is not None, (
            "expected DEF-009 fused panel/table signature in PTY transcript; "
            "if this fails after a Rich/layout fix, set status to fixed and assert None"
        )
        assert "fused" in reason.lower() and "2501" in reason, reason
    finally:
        try:
            child.send("q")
            child.expect(pexpect.EOF, timeout=15)
        except Exception:
            child.close(force=True)
