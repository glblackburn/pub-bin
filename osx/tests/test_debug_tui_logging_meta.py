"""Meta-tests for ``MACOS_MOUSE_CLICK_DEBUG_TUI`` logging (plan Phase 2 checklist).

Covers gate off/on, JSON contract, file vs stderr, append-across-processes, stdout
hygiene (unit), unwritable log path, and one PTY ``after_key`` probe on darwin.

**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import textwrap
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

import pytest

from pty_harness import REPO_ROOT, SCRIPT_PATH, base_child_env, spawn_clicker_pexpect

OSX_DIR = Path(__file__).resolve().parent.parent

TUI_PREFIX = "MACOS_MOUSE_CLICK_TUI_STATE "


def _iter_tui_payloads(text: str) -> Iterator[dict[str, Any]]:
    """Parse stderr lines (optional ``ts_wall`` before prefix) or log-file lines (raw JSON)."""
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if TUI_PREFIX in s:
            idx = s.index(TUI_PREFIX)
            yield json.loads(s[idx + len(TUI_PREFIX) :])
        elif s.startswith("{"):
            yield json.loads(s)


@pytest.fixture(autouse=True)
def _reset_debug_tui_sink() -> Any:
    import macos_mouse_click as mmc

    mmc._reset_debug_tui_log_sink()
    yield
    mmc._reset_debug_tui_log_sink()


def test_json_contract_on_fixture_lines() -> None:
    """Checklist #3: every state line parses; required keys and types per ``event``."""
    tw = "2026-04-20T15:23:41.527-07:00"
    tm = 9123456789012345
    base_ts = f'"ts_wall":"{tw}","ts_mono_ns":{tm},'
    sample = (
        tw
        + " "
        + TUI_PREFIX
        + "{"
        + base_ts
        + '"selected_index":0,"row_key":"mode","setting_label":"Mode",'
        '"value_text":"learn","source":"cli","event":"draw"}\n'
        + tw
        + " "
        + TUI_PREFIX
        + "{"
        + base_ts
        + '"selected_index":1,"row_key":"count","setting_label":"Count",'
        '"value_text":"2","source":"cli","event":"after_key","last_key":"down"}\n'
        + tw
        + " "
        + TUI_PREFIX
        + "{"
        + base_ts
        + '"event":"run","running_text":"mode=learn count=2 delay=0.0s",'
        '"mode":"learn","count":2,"delay":0.0,"anchor_x":null,"anchor_y":null}\n'
        + tw
        + " "
        + TUI_PREFIX
        + "{"
        + base_ts
        + '"event":"anchor","mode":"learn","anchor_x":3691.3,"anchor_y":-63.9,'
        '"message":"Anchor recorded at (3691.3, -63.9). Warmup: sleeping 0.0s…",'
        '"warmup_delay":0.0}\n'
    )
    for obj in _iter_tui_payloads(sample):
        ev = obj["event"]
        assert ev in ("draw", "after_key", "run", "anchor")
        assert isinstance(obj["ts_wall"], str)
        assert isinstance(obj["ts_mono_ns"], int)
        datetime.fromisoformat(obj["ts_wall"])
        assert not obj["ts_wall"].endswith("Z"), "use numeric offset, not Z-only UTC"
        if ev in ("draw", "after_key"):
            assert isinstance(obj["selected_index"], int)
            assert isinstance(obj["row_key"], str)
            assert isinstance(obj["setting_label"], str)
            assert isinstance(obj["value_text"], str)
            if "last_key" in obj:
                assert isinstance(obj["last_key"], str)
        elif ev == "run":
            assert isinstance(obj["running_text"], str)
            assert isinstance(obj["mode"], str)
            assert isinstance(obj["count"], int)
            assert isinstance(obj["delay"], (int, float))
            assert "anchor_x" in obj and "anchor_y" in obj
        else:
            assert ev == "anchor"
            assert isinstance(obj["mode"], str)
            assert isinstance(obj["anchor_x"], (int, float))
            assert isinstance(obj["anchor_y"], (int, float))
            assert isinstance(obj["message"], str)
            if "warmup_delay" in obj:
                assert isinstance(obj["warmup_delay"], (int, float))


def test_internal_consistency_first_draw_row_key(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Checklist #4: first draw row_key matches ``editor_row_keys(cfg)[selected]``."""
    monkeypatch.setenv("MACOS_MOUSE_CLICK_DEBUG_TUI", "1")
    import macos_mouse_click as mmc

    cfg = mmc.ResolvedConfig()
    cfg.set_field("mode", "learn", "cli")
    rk = mmc.editor_row_keys(cfg)
    mmc._debug_tui_emit(cfg, rk, 0, event="draw")
    err = capsys.readouterr().err
    lines = list(_iter_tui_payloads(err))
    assert lines and lines[0]["row_key"] == rk[0] == "mode"


def test_no_stdout_pollution_on_emit(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Checklist #7: prefix must not appear on stdout (unit: emit only)."""
    monkeypatch.setenv("MACOS_MOUSE_CLICK_DEBUG_TUI", "1")
    import macos_mouse_click as mmc

    cfg = mmc.ResolvedConfig()
    cfg.set_field("mode", "learn", "cli")
    rk = mmc.editor_row_keys(cfg)
    mmc._debug_tui_emit(cfg, rk, 0, event="draw")
    out = capsys.readouterr().out
    assert TUI_PREFIX.strip() not in out
    assert "MACOS_MOUSE_CLICK_TUI_STATE" not in out


def test_file_sink_duplicates_stderr_lines(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Checklist #5: file JSON lines match stderr JSON (same objects, same order)."""
    log_path = tmp_path / "tui.log"
    monkeypatch.setenv("MACOS_MOUSE_CLICK_DEBUG_TUI", "1")
    monkeypatch.setenv("MACOS_MOUSE_CLICK_DEBUG_TUI_LOG", str(log_path))
    import macos_mouse_click as mmc

    cfg = mmc.ResolvedConfig()
    cfg.set_field("mode", "learn", "cli")
    rk = mmc.editor_row_keys(cfg)
    mmc._debug_tui_emit(cfg, rk, 0, event="draw")
    mmc._debug_tui_emit(cfg, rk, 0, event="after_key", last_key="down")
    err = capsys.readouterr().err
    stderr_json_lines = []
    for ln in err.splitlines():
        if TUI_PREFIX not in ln:
            continue
        idx = ln.index(TUI_PREFIX)
        stderr_json_lines.append(ln[idx + len(TUI_PREFIX) :])
    file_lines = [ln for ln in log_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert stderr_json_lines == file_lines


def test_ts_wall_parseable_ts_mono_increases_stderr_matches_file(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Phase 1: ``ts_wall`` ISO parseable; ``ts_mono_ns`` strictly increases; stderr wall prefix."""
    log_path = tmp_path / "ts.ndjson"
    monkeypatch.setenv("MACOS_MOUSE_CLICK_DEBUG_TUI", "1")
    monkeypatch.setenv("MACOS_MOUSE_CLICK_DEBUG_TUI_LOG", str(log_path))
    import macos_mouse_click as mmc

    cfg = mmc.ResolvedConfig()
    cfg.set_field("mode", "learn", "cli")
    rk = mmc.editor_row_keys(cfg)
    mmc._debug_tui_emit(cfg, rk, 0, event="draw")
    mmc._debug_tui_emit(cfg, rk, 0, event="after_key", last_key="down")
    err = capsys.readouterr().err
    tui_lines = [ln for ln in err.splitlines() if TUI_PREFIX in ln]
    assert len(tui_lines) == 2
    iso_head = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}")
    for ln in tui_lines:
        assert iso_head.match(ln), ln[:80]
        pre, _, rest = ln.partition(TUI_PREFIX)
        assert pre.strip()
        assert rest.startswith("{")
        obj = json.loads(rest)
        datetime.fromisoformat(obj["ts_wall"])
        assert not obj["ts_wall"].endswith("Z")
        assert pre.strip() == obj["ts_wall"]
    objs_err = list(_iter_tui_payloads(err))
    objs_file = list(_iter_tui_payloads(log_path.read_text(encoding="utf-8")))
    assert objs_err == objs_file
    assert objs_err[0]["ts_mono_ns"] < objs_err[1]["ts_mono_ns"]


def test_no_default_log_file_when_log_env_unset(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Checklist #6: debug on, LOG unset — no file under tmp_path."""
    monkeypatch.setenv("MACOS_MOUSE_CLICK_DEBUG_TUI", "1")
    monkeypatch.delenv("MACOS_MOUSE_CLICK_DEBUG_TUI_LOG", raising=False)
    import macos_mouse_click as mmc

    before = {p.name for p in tmp_path.iterdir()} if tmp_path.exists() else set()
    cfg = mmc.ResolvedConfig()
    cfg.set_field("mode", "learn", "cli")
    rk = mmc.editor_row_keys(cfg)
    mmc._debug_tui_emit(cfg, rk, 0, event="draw")
    capsys.readouterr()
    after = {p.name for p in tmp_path.iterdir()} if tmp_path.exists() else set()
    assert before == after


def test_unwritable_log_path_stderr_still_emits(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """Checklist #10: LOG path unusable — stderr logging still works."""
    monkeypatch.setenv("MACOS_MOUSE_CLICK_DEBUG_TUI", "1")
    monkeypatch.setenv("MACOS_MOUSE_CLICK_DEBUG_TUI_LOG", str(tmp_path))
    import macos_mouse_click as mmc

    cfg = mmc.ResolvedConfig()
    cfg.set_field("mode", "learn", "cli")
    rk = mmc.editor_row_keys(cfg)
    mmc._debug_tui_emit(cfg, rk, 0, event="draw")
    err = capsys.readouterr().err
    assert TUI_PREFIX in err


def test_log_file_always_appends_never_replaces_prior_runs(tmp_path: Path) -> None:
    """Policy: ``MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`` must append; prior runs stay in the file.

    Two fresh Python subprocesses write one JSON line each to the same path.
    After the second run, the file must still contain the first run's line **and**
    the second run's line, in order.
    """
    log_path = tmp_path / "append_policy.log"
    code = textwrap.dedent(
        f"""
        import os, sys
        os.environ["MACOS_MOUSE_CLICK_DEBUG_TUI"] = "1"
        os.environ["MACOS_MOUSE_CLICK_DEBUG_TUI_LOG"] = {str(log_path)!r}
        sys.path.insert(0, {str(OSX_DIR)!r})
        import macos_mouse_click as m
        m._reset_debug_tui_log_sink()
        m._debug_tui_write_line({{"append_policy_mark": int(sys.argv[1])}})
        """
    ).strip()
    r1 = subprocess.run(
        [sys.executable, "-c", code, "1"],
        cwd=str(REPO_ROOT),
        env={**os.environ, "PYTHONPATH": str(OSX_DIR)},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r1.returncode == 0, (r1.stdout, r1.stderr)
    after_first = log_path.read_text(encoding="utf-8")
    assert '"append_policy_mark":1' in after_first

    r2 = subprocess.run(
        [sys.executable, "-c", code, "2"],
        cwd=str(REPO_ROOT),
        env={**os.environ, "PYTHONPATH": str(OSX_DIR)},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r2.returncode == 0, (r2.stdout, r2.stderr)
    combined = log_path.read_text(encoding="utf-8")
    assert '"append_policy_mark":1' in combined, (
        "first subprocess line must still be present (append); got: " + repr(combined)
    )
    assert '"append_policy_mark":2' in combined, "second subprocess line missing: " + repr(combined)
    assert combined.index('"append_policy_mark":1') < combined.index('"append_policy_mark":2'), (
        "append order: first run before second; got: " + repr(combined)
    )


@pytest.mark.darwin
def test_gate_off_editor_no_tui_state_lines(pexpect_module: Any) -> None:
    """Checklist #1: debug unset — no TUI state lines while Rich editor runs."""
    pexpect = pexpect_module
    env = base_child_env({"TERM": "xterm-256color"})
    env.pop("MACOS_MOUSE_CLICK_DEBUG_TUI", None)
    env.pop("MACOS_MOUSE_CLICK_DEBUG_TUI_LOG", None)
    buf = io.StringIO()
    child = spawn_clicker_pexpect(
        pexpect,
        ["--learn", "--interactive", "-n", "1", "-d", "1"],
        cwd=REPO_ROOT,
        env=env,
        timeout=90,
        dimensions=(40, 120),
        maxread=2_000_000,
    )
    child.logfile_read = buf
    try:
        child.expect("review / edit", timeout=60)
        time.sleep(0.4)
        try:
            buf.write(child.read_nonblocking(size=200_000, timeout=2) or "")
        except Exception:
            pass
        child.send("q")
        try:
            child.expect(pexpect.EOF, timeout=20)
        except pexpect.TIMEOUT:
            child.close(force=True)
    finally:
        try:
            child.close(force=True)
        except Exception:
            pass
    merged = buf.getvalue()
    assert "MACOS_MOUSE_CLICK_TUI_STATE " not in merged


@pytest.mark.darwin
def test_gate_on_stderr_contains_tui_state(
    pexpect_module: Any, tmp_path: Path
) -> None:
    """Checklist #2: debug on — at least one TUI state line (read log file; PTY merge is flaky)."""
    pexpect = pexpect_module
    log_path = tmp_path / "gate.log"
    env = base_child_env(
        {
            "TERM": "xterm-256color",
            "MACOS_MOUSE_CLICK_DEBUG_TUI": "1",
            "MACOS_MOUSE_CLICK_DEBUG_TUI_LOG": str(log_path),
        }
    )
    child = spawn_clicker_pexpect(
        pexpect,
        ["--learn", "--interactive", "-n", "1", "-d", "1"],
        cwd=REPO_ROOT,
        env=env,
        timeout=90,
        dimensions=(40, 120),
        maxread=2_000_000,
    )
    try:
        child.expect("review / edit", timeout=60)
        time.sleep(0.5)
        try:
            child.read_nonblocking(size=200_000, timeout=2)
        except Exception:
            pass
        for _ in range(60):
            if log_path.exists() and log_path.stat().st_size > 0:
                break
            time.sleep(0.1)
        assert log_path.exists(), "expected DEBUG_TUI_LOG file after first draw"
        text = log_path.read_text(encoding="utf-8")
        assert any(ln.strip().startswith("{") for ln in text.splitlines() if ln.strip()), text[:500]
        child.send("q")
        try:
            child.expect(pexpect.EOF, timeout=20)
        except pexpect.TIMEOUT:
            child.close(force=True)
    finally:
        if not child.closed:
            child.close(force=True)


@pytest.mark.darwin
def test_after_key_down_then_draw_pexpect(pexpect_module: Any, tmp_path: Path) -> None:
    """Checklist #9: one Down — ``after_key`` with ``last_key`` ``down`` then a ``draw``."""
    pexpect = pexpect_module
    log_path = tmp_path / "keys.log"
    env = base_child_env(
        {
            "TERM": "xterm-256color",
            "MACOS_MOUSE_CLICK_DEBUG_TUI": "1",
            "MACOS_MOUSE_CLICK_DEBUG_TUI_LOG": str(log_path),
        }
    )
    child = spawn_clicker_pexpect(
        pexpect,
        ["--learn", "--interactive", "-n", "1", "-d", "1"],
        cwd=REPO_ROOT,
        env=env,
        timeout=90,
        dimensions=(40, 120),
        maxread=2_000_000,
    )
    child.delaybeforesend = 0.15
    try:
        child.expect("review / edit", timeout=60)
        time.sleep(0.35)
        try:
            child.read_nonblocking(size=200_000, timeout=2)
        except Exception:
            pass
        child.send("\x1b[B")
        deadline = time.monotonic() + 8.0
        ok = False
        while time.monotonic() < deadline:
            try:
                child.read_nonblocking(size=500_000, timeout=0)
            except Exception:
                pass
            text = log_path.read_text(encoding="utf-8")
            payloads = list(_iter_tui_payloads(text))
            draw_idx = [i for i, p in enumerate(payloads) if p.get("event") == "draw"]
            if not draw_idx:
                time.sleep(0.05)
                continue
            down_idx = [
                i
                for i, p in enumerate(payloads)
                if p.get("event") == "after_key" and p.get("last_key") == "down"
            ]
            if not down_idx:
                time.sleep(0.05)
                continue
            first_draw = draw_idx[0]
            down_after_first = [i for i in down_idx if i > first_draw]
            if not down_after_first:
                time.sleep(0.05)
                continue
            d0 = down_after_first[0]
            if any(i > d0 for i in draw_idx):
                ok = True
                break
            time.sleep(0.05)
        assert ok, (
            "expected a draw event in the log after the first Down (after_key down); "
            "cooked-then-raw editor loop should log draw, after_key, draw, …"
        )
        child.send("q")
        try:
            child.expect(pexpect.EOF, timeout=20)
        except pexpect.TIMEOUT:
            child.close(force=True)
    finally:
        try:
            child.close(force=True)
        except Exception:
            pass


def test_subprocess_noninteractive_yes_writes_run_to_log(tmp_path: Path) -> None:
    """``-Y`` skips Rich editor; ``event\":\"run\"`` mirrors the ``Running:`` line."""
    log_path = tmp_path / "cli_run.ndjson"
    env = {
        **os.environ,
        "PYTHONUNBUFFERED": "1",
        "PYTHONPATH": str(OSX_DIR),
        "MACOS_MOUSE_CLICK_DEBUG_TUI": "1",
        "MACOS_MOUSE_CLICK_DEBUG_TUI_LOG": str(log_path),
    }
    r = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--learn",
            "-n",
            "2000",
            "-d",
            "0",
            "-Y",
            "--dry-run-after-start",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    err = r.stderr or ""
    assert "MACOS_MOUSE_CLICK_TUI_STATE " in err
    assert '"event":"run"' in err.replace(" ", "")
    text = log_path.read_text(encoding="utf-8")
    assert '"event":"run"' in text.replace(" ", "")
    payloads = list(_iter_tui_payloads(text))
    runs = [p for p in payloads if p.get("event") == "run"]
    assert runs, payloads
    assert runs[0].get("mode") == "learn"
    assert runs[0].get("count") == 2000
    assert runs[0].get("anchor_x") is None and runs[0].get("anchor_y") is None
    rt = runs[0].get("running_text", "")
    assert "mode=learn" in rt and "2000" in rt and "delay=" in rt


def test_subprocess_fixed_mode_run_payload_includes_anchor(tmp_path: Path) -> None:
    """Fixed mode: ``run`` includes anchor coordinates before Quartz."""
    log_path = tmp_path / "fixed_run.ndjson"
    env = {
        **os.environ,
        "PYTHONUNBUFFERED": "1",
        "PYTHONPATH": str(OSX_DIR),
        "MACOS_MOUSE_CLICK_DEBUG_TUI": "1",
        "MACOS_MOUSE_CLICK_DEBUG_TUI_LOG": str(log_path),
    }
    r = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "-x",
            "10.5",
            "-y",
            "-20",
            "-n",
            "1",
            "-d",
            "0",
            "-Y",
            "--dry-run-after-start",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    payloads = list(_iter_tui_payloads(log_path.read_text(encoding="utf-8")))
    runs = [p for p in payloads if p.get("event") == "run"]
    assert runs and runs[0].get("mode") == "fixed"
    assert runs[0].get("anchor_x") == 10.5
    assert runs[0].get("anchor_y") == -20.0


def test_subprocess_dry_run_no_tui_state_when_debug_unset() -> None:
    """Sanity: non-editor path does not emit TUI lines (regression guard)."""
    env = {**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONPATH": str(OSX_DIR)}
    env.pop("MACOS_MOUSE_CLICK_DEBUG_TUI", None)
    r = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--learn",
            "-Y",
            "--dry-run-after-start",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0
    blob = (r.stderr or "") + (r.stdout or "")
    assert "MACOS_MOUSE_CLICK_TUI_STATE " not in blob
