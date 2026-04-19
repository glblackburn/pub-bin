"""Rich pre-run settings table: Down navigation (plan: normative cases 1–2).

Golden argv (learn + interactive, ``editor_row_keys`` = mode/count/delay only):

``--learn --interactive -n 2 -d 3.5``

Requires **pexpect**, **rich**, and **darwin** (PTY + real TUI). Marked ``table_nav``;
excluded from ``make -C osx test-quick`` until Phase 3 stabilizes navigation/parsing.

See ``docs/plans/agent/new-test-up-down-navigation.plan.md``.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

import pytest

from pty_harness import REPO_ROOT, base_child_env, spawn_clicker_pexpect

# Rich highlights the selected Setting cell with bold (``\\x1b[1m``) when TERM
# supports ANSI (use ``xterm-256color`` in env below).
_SETTING_BOLD_RE = re.compile(r"\x1b\[1m\s*(Mode|Count|Delay \(s\))\s*\x1b\[0m")


def _highlighted_setting_label(transcript: str) -> str | None:
    """Return the Setting-column label for the row whose Setting cell is bold."""
    for line in reversed(transcript.splitlines()):
        if "│" not in line:
            continue
        m = _SETTING_BOLD_RE.search(line)
        if m:
            return m.group(1)
    return None


def _row_below_setting(highlight: str | None) -> str | None:
    order = ("Mode", "Count", "Delay (s)")
    if highlight is None:
        return None
    try:
        i = order.index(highlight)
    except ValueError:
        return None
    if i + 1 < len(order):
        return order[i + 1]
    return None


def _transcript_after_editor_banner(child: Any) -> str:
    """Append post-match drain so the Rich table body is in the buffer."""
    parts: list[str] = []
    b = getattr(child, "before", None) or ""
    parts.append(b)
    m = getattr(child, "match", None)
    if m is not None and hasattr(m, "group"):
        try:
            parts.append(m.group(0))
        except (IndexError, AttributeError):
            parts.append(str(m))
    elif m is not None:
        parts.append(str(m))
    base = "".join(parts)
    time.sleep(0.35)
    try:
        extra = child.read_nonblocking(size=500_000, timeout=3)
    except Exception:
        extra = ""
    return base + (extra or "")


def _drain_until_setting(child: Any, expected: str, *, timeout: float = 12.0) -> str:
    """Read PTY output until parser sees ``expected`` as the bold Setting column."""
    parts: list[str] = []
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            chunk = child.read_nonblocking(size=500_000, timeout=0.5)
        except Exception:
            chunk = ""
        parts.append(chunk or "")
        acc = "".join(parts)
        if _highlighted_setting_label(acc) == expected:
            return acc
        time.sleep(0.05)
    return "".join(parts)


def _mode_row_preconditions(transcript: str) -> None:
    """Plan case 1 (i)–(ii): first highlight Mode; Mode value matches learn CLI."""
    hi = _highlighted_setting_label(transcript)
    assert hi == "Mode", f"expected initial highlight Mode, got {hi!r}"
    found = False
    for line in transcript.splitlines():
        if _SETTING_BOLD_RE.search(line) and "Mode" in line and "\x1b[1mlearn" in line:
            found = True
            break
    assert found, "expected Mode row value learn with bold styling when selected"
    assert "2" in transcript and "3.5" in transcript, "expected Count/Delay cells in table"


@pytest.mark.darwin
@pytest.mark.table_nav
@pytest.mark.xfail(
    strict=False,
    reason=(
        "Phase 1 capture: CSI Down via pexpect leaves highlight on Mode (read_raw_key "
        "or PTY timing vs Rich redraw); second test may drain only footer. Phase 3."
    ),
)
def test_rich_table_down_moves_to_row_below(
    pexpect_module: Any,
    repo_root: Path,
) -> None:
    """Normative case 1: one Down; new highlight Setting equals prior row-below."""
    pexpect = pexpect_module
    env = base_child_env(
        {
            "TERM": "xterm-256color",
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
        t0 = _transcript_after_editor_banner(child)
        _mode_row_preconditions(t0)
        a = _highlighted_setting_label(t0)
        b = _row_below_setting(a)
        assert b is not None and a != b
        child.send("\x1b[B")
        t1 = _drain_until_setting(child, "Count")
        c = _highlighted_setting_label(t1)
        assert c == b, f"expected highlight after Down == row-below {b!r}, got {c!r}"
        if a and c:
            assert c != a, "selection should leave the original row"
    finally:
        try:
            child.send("q")
            child.expect(pexpect.EOF, timeout=15)
        except Exception:
            child.close(force=True)


@pytest.mark.darwin
@pytest.mark.table_nav
@pytest.mark.xfail(
    strict=False,
    reason=(
        "Phase 1 capture: bold Setting parse / PTY transcript after Down not yet "
        "stable with Rich console.clear; see _scratch_phase1_rich_table_pty.md."
    ),
)
def test_rich_table_two_downs_mode_count_delay_labels(
    pexpect_module: Any,
    repo_root: Path,
) -> None:
    """Normative case 2: two Downs; Setting column Mode -> Count -> Delay (s)."""
    pexpect = pexpect_module
    env = base_child_env({"TERM": "xterm-256color"})
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
        t0 = _transcript_after_editor_banner(child)
        _mode_row_preconditions(t0)
        assert _highlighted_setting_label(t0) == "Mode"
        child.send("\x1b[B")
        t1 = _drain_until_setting(child, "Count")
        assert _highlighted_setting_label(t1) == "Count"
        child.send("\x1b[B")
        t2 = _drain_until_setting(child, "Delay (s)")
        assert _highlighted_setting_label(t2) == "Delay (s)"
    finally:
        try:
            child.send("q")
            child.expect(pexpect.EOF, timeout=15)
        except Exception:
            child.close(force=True)
