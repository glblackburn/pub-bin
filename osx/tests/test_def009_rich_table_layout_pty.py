"""DEF-009 / DEF-010: regression tests for Rich pre-run table / panel layout (PTY transcript).

See ``docs/osx/defects/def-009-rich-pre-run-tui-table-layout-corruption.md``.
"""

from __future__ import annotations

import io
import time
from pathlib import Path
from typing import Any

import pytest

from def009_layout_heuristics import (
    def010_vertical_spacer_reason,
    layout_corruption_reason,
    strip_csi,
)

pytest.importorskip("rich", reason="Rich pre-run editor tests need rich")


def test_def009_clean_synthetic_rich_panel_has_no_corruption() -> None:
    """Sanity: production-shaped Panel+Table (legacy ``32d5820`` layout) must not trip heuristics."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    buf = io.StringIO()
    # Tall virtual console: short PTYs can fuse inner ``HEAVY_HEAD`` rules with the panel.
    c = Console(
        file=buf,
        width=120,
        height=80,
        force_terminal=True,
        color_system="truecolor",
    )
    t = Table(show_header=True, header_style="bold cyan", expand=True)
    _nw = {"no_wrap": True, "overflow": "ellipsis"}
    t.add_column("Setting", style="white", **_nw)
    t.add_column("Value", style="green", **_nw)
    t.add_column("Source", style="dim", **_nw)
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


def test_def010_narrow_panel_table_has_no_spacer_only_interior_rows() -> None:
    """DEF-010: long Value/Source must not wrap to extra pipe-only rows (Rich row_height)."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    buf = io.StringIO()
    c = Console(
        file=buf,
        width=56,
        height=40,
        force_terminal=True,
        color_system="truecolor",
    )
    t = Table(show_header=True, header_style="bold cyan", expand=True)
    _nw = {"no_wrap": True, "overflow": "ellipsis"}
    t.add_column("Setting", style="white", **_nw)
    t.add_column("Value", style="green", **_nw)
    t.add_column("Source", style="dim", **_nw)
    t.add_row(
        Text("Mode", style="bold black on bright_cyan"),
        Text("learn" + "x" * 120, style="bold black on bright_cyan"),
        Text("cli" + "y" * 120, style="bold black on bright_cyan"),
    )
    c.print(
        Panel(
            t,
            title="[bold cyan]macOS mouse click[/] — review / edit",
            border_style="cyan",
        )
    )
    out = buf.getvalue()
    assert def010_vertical_spacer_reason(out) is None, out[:2000]


def test_def010_heuristic_still_flags_synthetic_spacer_transcript() -> None:
    """If spacer-only interior lines reappear in captures, ``layout_corruption_reason`` flags them."""
    spacer = "│ │" + " " * 60 + "│" + " " * 50 + "│" + " " * 8
    transcript = (
        "╭─ macOS mouse click — review / edit ─╮\n"
        "│ ╭───────────────────────────────╮ │\n"
        f"{spacer}\n"
        "│ │ \x1b[1mMode\x1b[0m │ learn │ cli │\n"
    )
    assert def010_vertical_spacer_reason(transcript) is not None
    r = layout_corruption_reason(transcript)
    assert r is not None and "DEF-010" in r and "spacer" in r.lower()


def test_def010_short_pipe_only_line_not_flagged() -> None:
    """Avoid false positives on very short ``│`` fragments."""
    assert layout_corruption_reason("│ │ │\n") is None


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
    """Live PTY: stderr interleave / doubled pipes / spacers (not HEAVY_HEAD fuse line)."""
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
        reason = layout_corruption_reason(
            transcript,
            ignore_fused_panel_heavy_line=True,
            ignore_merged_debug_tui_rows=True,
        )
        assert reason is None, reason
    finally:
        try:
            child.send("q")
            child.expect(pexpect.EOF, timeout=15)
        except Exception:
            child.close(force=True)


@pytest.mark.darwin
@pytest.mark.table_nav
def test_def009_editor_layout_after_pty_resize_pexpect(
    pexpect_module: Any,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    """PTY ``setwinsize`` then redraw (Down): layout heuristics stay clean (plan-agent-rich-pre-run)."""
    pytest.importorskip("pexpect", reason="pty tests need pexpect")

    from pty_harness import base_child_env, spawn_clicker_pexpect
    from test_rich_table_nav_down_pty import (
        _drain_until_setting_from,
        _transcript_after_editor_banner,
    )

    pexpect = pexpect_module
    log_path = Path(tmp_path) / "def009-resize.ndjson"
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
        t0 = _drain_until_setting_from(child, base, "Mode", timeout=15.0)
        r0 = layout_corruption_reason(
            t0,
            ignore_fused_panel_heavy_line=True,
            ignore_merged_debug_tui_rows=True,
        )
        assert r0 is None, r0
        assert def010_vertical_spacer_reason(t0) is None, t0[:2000]

        child.setwinsize(28, 72)
        time.sleep(0.35)
        try:
            child.read_nonblocking(size=500_000, timeout=2)
        except Exception:
            pass
        child.send("\x1b[B")
        t1 = _drain_until_setting_from(child, t0, "Count", timeout=20.0)
        r1 = layout_corruption_reason(
            t1,
            ignore_fused_panel_heavy_line=True,
            ignore_merged_debug_tui_rows=True,
        )
        assert r1 is None, r1
        assert def010_vertical_spacer_reason(t1) is None, t1[:2000]
    finally:
        try:
            child.send("q")
            child.expect(pexpect.EOF, timeout=15)
        except Exception:
            child.close(force=True)
