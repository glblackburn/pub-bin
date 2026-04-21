"""Rich pre-run settings table: Down navigation (plan: normative cases 1–2).

Golden argv (learn + interactive, ``editor_row_keys`` = mode/count/delay only):

``--learn --interactive -n 2 -d 3.5``

Requires **pexpect**, **rich**, and **darwin** (PTY + real TUI). Marked ``table_nav``;
excluded from ``make -C osx test-quick`` (``table_nav``) to keep the default suite fast.

See ``docs/osx/plans/agent/plan-agent-new-test-up-down-navigation.plan.md``.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Iterator

import pytest

from pty_harness import REPO_ROOT, base_child_env, spawn_clicker_pexpect

def _iter_tui_payloads_from_log(path: Path) -> Iterator[dict[str, Any]]:
    """Log file lines are raw JSON (one object per line) for ``jq`` compatibility."""
    if not path.exists():
        yield from ()
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        yield json.loads(s)


def _wait_debug_log(path: Path, *, timeout: float = 8.0) -> None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if path.exists() and path.stat().st_size > 0:
            return
        time.sleep(0.05)
    raise AssertionError(f"expected non-empty debug log at {path}")


def _latest_draw_payload(path: Path) -> dict[str, Any]:
    draws = [p for p in _iter_tui_payloads_from_log(path) if p.get("event") == "draw"]
    assert draws, f"no draw events in {path}"
    return draws[-1]


def _last_nav_tui_payload(path: Path) -> dict[str, Any] | None:
    """Last ``draw`` / ``after_key`` line in the log (selection state for both events)."""
    last: dict[str, Any] | None = None
    for p in _iter_tui_payloads_from_log(path):
        if p.get("event") in ("draw", "after_key"):
            last = p
    return last


def _wait_latest_nav_setting(path: Path, want: str, *, timeout: float = 15.0) -> dict[str, Any]:
    """Poll NDJSON until the last nav payload's ``setting_label`` matches ``want``.

    After an arrow key, ``after_key`` is emitted before the next loop iteration's
    ``draw``, so the final ``draw`` line can still describe the prior row while
    the PTY already shows the new highlight — waiting on ``draw`` alone flakes.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            tail = _last_nav_tui_payload(path)
            if tail is not None and tail.get("setting_label") == want:
                return tail
        time.sleep(0.05)
    tail = _last_nav_tui_payload(path) if path.exists() else None
    raise AssertionError(
        f"timeout waiting for nav setting_label={want!r}; last_nav={tail!r}"
    )

# Rich highlights the selected Setting cell with bold when TERM supports ANSI.
# Rich may emit ``\\x1b[1m`` alone or combined SGR (e.g. ``\\x1b[1;30;106m`` for bold+fg+bg).
_SETTING_BOLD_RE = re.compile(
    r"\x1b\[1m\s*(Mode|Count|Delay \(s\))\s*\x1b\[0m"
)
# Do not use ``\b`` after ``Delay (s)``: the next char is often ``\x1b`` (``)`` and
# ``\`` are both non-word, so there is no word boundary between them.
_SETTING_BOLD_COMBINED_RE = re.compile(
    r"\x1b\[1(?:;\d+)*m(?:\x1b\[[0-9;]+m)*\s*(Mode|Count|Delay \(s\))"
)


def _highlighted_setting_label(transcript: str) -> str | None:
    """Return the Setting-column label for the row whose Setting cell is bold."""
    for line in reversed(transcript.splitlines()):
        if "│" not in line:
            continue
        m = _SETTING_BOLD_RE.search(line)
        if m:
            return m.group(1)
        m2 = _SETTING_BOLD_COMBINED_RE.search(line)
        if m2:
            return m2.group(1)
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


def _drain_until_setting_from(
    child: Any, initial: str, expected: str, *, timeout: float = 15.0
) -> str:
    """Append PTY reads to ``initial`` until the bold Setting column matches ``expected``."""
    parts: list[str] = [initial]
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        acc = "".join(parts)
        if _highlighted_setting_label(acc) == expected:
            return acc
        try:
            chunk = child.read_nonblocking(size=500_000, timeout=0.5)
        except Exception:
            chunk = ""
        parts.append(chunk or "")
        time.sleep(0.05)
    return "".join(parts)


def _drain_until_setting(child: Any, expected: str, *, timeout: float = 12.0) -> str:
    """Read PTY output until parser sees ``expected`` as the bold Setting column."""
    return _drain_until_setting_from(child, "", expected, timeout=timeout)


def _mode_row_preconditions(transcript: str, *, debug_log: Path | None = None) -> None:
    """Plan case 1 (i)–(ii): first highlight Mode; Mode value matches learn CLI."""
    hi = _highlighted_setting_label(transcript)
    assert hi == "Mode", f"expected initial highlight Mode, got {hi!r}"
    found = False
    for line in transcript.splitlines():
        if "│" not in line or "Mode" not in line or "learn" not in line:
            continue
        if _SETTING_BOLD_RE.search(line) or _SETTING_BOLD_COMBINED_RE.search(line):
            if "\x1b[1mlearn" in line or re.search(r"\x1b\[1(?:;\d+)*m[^\n]*learn", line):
                found = True
                break
    assert found, "expected Mode row value learn with bold styling when selected"
    assert "2" in transcript and "3.5" in transcript, "expected Count/Delay cells in table"
    if debug_log is not None:
        _wait_debug_log(debug_log)
        d = _latest_draw_payload(debug_log)
        assert d["setting_label"] == "Mode" and str(d["value_text"]) == "learn"
        assert d["row_key"] == "mode" and d["selected_index"] == 0


@pytest.mark.darwin
@pytest.mark.table_nav
def test_rich_table_down_moves_to_row_below(
    pexpect_module: Any,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    """Normative case 1: one Down; new highlight Setting equals prior row-below."""
    pexpect = pexpect_module
    log_path = tmp_path / "nav.log"
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
        assert _highlighted_setting_label(t0) == "Mode", (
            "table did not show bold Mode within timeout; subtitle can match before rows render"
        )
        _mode_row_preconditions(t0, debug_log=log_path)
        a = _highlighted_setting_label(t0)
        b = _row_below_setting(a)
        assert b is not None and a != b
        child.send("\x1b[B")
        d_count = _wait_latest_nav_setting(log_path, "Count", timeout=15.0)
        t1 = _drain_until_setting_from(child, t0, "Count", timeout=15.0)
        c = _highlighted_setting_label(t1)
        assert d_count["setting_label"] == "Count"
        tail = list(_iter_tui_payloads_from_log(log_path))
        downs = [p for p in tail if p.get("event") == "after_key" and p.get("last_key") == "down"]
        assert downs, "expected after_key down in debug log"
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
def test_rich_table_two_downs_mode_count_delay_labels(
    pexpect_module: Any,
    repo_root: Path,
    tmp_path: Path,
) -> None:
    """Normative case 2: two Downs; Setting column Mode -> Count -> Delay (s)."""
    pexpect = pexpect_module
    log_path = tmp_path / "nav2.log"
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
        assert _highlighted_setting_label(t0) == "Mode", (
            "table did not show bold Mode within timeout; subtitle can match before rows render"
        )
        _mode_row_preconditions(t0, debug_log=log_path)
        assert _highlighted_setting_label(t0) == "Mode"
        child.send("\x1b[B")
        d1 = _wait_latest_nav_setting(log_path, "Count", timeout=15.0)
        t1 = _drain_until_setting_from(child, t0, "Count", timeout=15.0)
        assert _highlighted_setting_label(t1) == "Count"
        assert d1["setting_label"] == "Count"
        child.send("\x1b[B")
        d2 = _wait_latest_nav_setting(log_path, "Delay (s)", timeout=15.0)
        t2 = _drain_until_setting_from(child, t1, "Delay (s)", timeout=15.0)
        assert _highlighted_setting_label(t2) == "Delay (s)"
        assert d2["setting_label"] == "Delay (s)"
    finally:
        try:
            child.send("q")
            child.expect(pexpect.EOF, timeout=15)
        except Exception:
            child.close(force=True)
