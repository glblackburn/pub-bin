"""Dry-run hook: JSON line and exit before Quartz (plan 03 phase 0).

**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import macos_mouse_click as mmc
from macos_mouse_click import ResolvedConfig


class _FakeTTY(io.StringIO):
    def isatty(self) -> bool:  # noqa: D401
        return True


def test_resolved_config_for_dry_run_json() -> None:
    cfg = ResolvedConfig(mode="learn", count=0, delay=1.25)
    d = mmc.resolved_config_for_dry_run_json(cfg)
    assert d == {
        "mode": "learn",
        "count": 0,
        "delay": 1.25,
        "x": None,
        "y": None,
        "abort_on_mouse_move": False,
        "mouse_move_threshold_px": 20.0,
        "mouse_arm_radius_px": None,
    }

    cfg2 = ResolvedConfig(mode="fixed", count=2, delay=0.0, x=10.0, y=20.5)
    d2 = mmc.resolved_config_for_dry_run_json(cfg2)
    assert d2["x"] == 10.0 and d2["y"] == 20.5
    assert d2["abort_on_mouse_move"] is False
    assert d2["mouse_move_threshold_px"] == 20.0
    assert d2["mouse_arm_radius_px"] is None

    cfg3 = ResolvedConfig(
        mode="learn_collect", count=0, delay=1.0, learn_point_cap=None
    )
    d3 = mmc.resolved_config_for_dry_run_json(cfg3)
    assert d3["mode"] == "learn_collect"
    assert d3["learn_point_cap"] is None
    assert d3["abort_on_mouse_move"] is False

    cfg4 = ResolvedConfig(
        mode="learn_collect", count=0, delay=1.0, learn_point_cap=2
    )
    d4 = mmc.resolved_config_for_dry_run_json(cfg4)
    assert d4["learn_point_cap"] == 2
    assert d4["mouse_move_threshold_px"] == 20.0
    assert d4["mouse_arm_radius_px"] is None


def test_dry_run_requested_flag_and_env() -> None:
    p = mmc.build_arg_parser()
    ns = p.parse_args(["--learn", "-Y", "--dry-run-after-start"])
    assert mmc.dry_run_after_start_requested(ns) is True
    ns2 = p.parse_args(["--learn", "-Y"])
    assert mmc.dry_run_after_start_requested(ns2) is False

    class NS:
        dry_run_after_start = False

    old = os.environ.get("MACOS_MOUSE_CLICK_DRY_RUN")
    try:
        os.environ["MACOS_MOUSE_CLICK_DRY_RUN"] = "1"
        assert mmc.dry_run_after_start_requested(NS()) is True
        os.environ["MACOS_MOUSE_CLICK_DRY_RUN"] = "yes"
        assert mmc.dry_run_after_start_requested(NS()) is True
        os.environ["MACOS_MOUSE_CLICK_DRY_RUN"] = "0"
        assert mmc.dry_run_after_start_requested(NS()) is False
    finally:
        if old is None:
            os.environ.pop("MACOS_MOUSE_CLICK_DRY_RUN", None)
        else:
            os.environ["MACOS_MOUSE_CLICK_DRY_RUN"] = old


def _run_script(
    repo_root: Path,
    script_path: Path,
    argv: list[str],
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(script_path), *argv],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_subprocess_learn_y_dry_run_exits_before_quartz(
    repo_root: Path, script_path: Path
) -> None:
    r = _run_script(
        repo_root,
        script_path,
        ["--learn", "-Y", "-n", "3", "-d", "0", "--dry-run-after-start"],
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "Running:" in r.stderr
    m = re.search(
        r"MACOS_MOUSE_CLICK_DRY_RUN_JSON (\{.*\})\s*$",
        r.stderr,
        re.MULTILINE,
    )
    assert m, r.stderr
    payload = json.loads(m.group(1))
    assert payload["mode"] == "learn"
    assert payload["count"] == 3
    assert payload["delay"] == 0.0
    assert payload["x"] is None and payload["y"] is None
    assert "Quartz" not in r.stderr or "MACOS_MOUSE_CLICK_DRY_RUN_JSON" in r.stderr


def test_subprocess_learn_collect_dry_run_infinite_stdout(
    repo_root: Path, script_path: Path
) -> None:
    r = _run_script(
        repo_root,
        script_path,
        ["--learn-points", "-Y", "--dry-run-after-start"],
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "Running:" in r.stderr
    m = re.search(
        r"MACOS_MOUSE_CLICK_DRY_RUN_JSON (\{.*\})\s*$",
        r.stderr,
        re.MULTILINE,
    )
    assert m, r.stderr
    payload = json.loads(m.group(1))
    assert payload["mode"] == "learn_collect"
    assert payload["learn_point_cap"] is None
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    assert lines == [
        "1 111.0000 222.0000",
        "2 333.2500 444.5000",
        "3 10.0000 20.0000",
    ]


def test_subprocess_learn_collect_dry_run_capped_stdout(
    repo_root: Path, script_path: Path
) -> None:
    r = _run_script(
        repo_root,
        script_path,
        ["--learn-points", "2", "-Y", "--dry-run-after-start"],
    )
    assert r.returncode == 0, r.stderr + r.stdout
    m = re.search(
        r"MACOS_MOUSE_CLICK_DRY_RUN_JSON (\{.*\})\s*$",
        r.stderr,
        re.MULTILINE,
    )
    assert m, r.stderr
    payload = json.loads(m.group(1))
    assert payload["learn_point_cap"] == 2
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    assert lines == ["1 111.0000 222.0000", "2 333.2500 444.5000"]


def test_subprocess_dry_run_env_var(repo_root: Path, script_path: Path) -> None:
    r = _run_script(
        repo_root,
        script_path,
        ["--at-cursor", "-Y", "-n", "1", "-d", "0.5"],
        extra_env={"MACOS_MOUSE_CLICK_DRY_RUN": "true"},
    )
    assert r.returncode == 0
    assert "MACOS_MOUSE_CLICK_DRY_RUN_JSON" in r.stderr
    m = re.search(
        r"MACOS_MOUSE_CLICK_DRY_RUN_JSON (\{.*\})\s*",
        r.stderr,
        re.DOTALL,
    )
    assert m, r.stderr
    payload = json.loads(m.group(1))
    assert payload["mode"] == "at_cursor"


@pytest.mark.mt02
def test_mt02_rich_branch_dry_run_skips_quartz(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Plan 03 / MT-02 (integration): Rich ``can_tui`` path + dry-run exits before Quartz.

    Full PTY navigation against ``read_raw_key`` is deferred (pexpect + raw TTY
    is flaky on some hosts); this asserts ``main()`` wiring after the editor
    returns Start.
    """
    monkeypatch.setattr(sys, "stdin", _FakeTTY())
    monkeypatch.setattr(sys, "stdout", _FakeTTY())

    def _fake_editor(cfg: ResolvedConfig, _rich: object) -> bool:
        return True

    def _boom_quartz() -> object:
        raise AssertionError("import_quartz must not be called on dry-run path")

    monkeypatch.setattr(mmc, "run_rich_pre_run_editor", _fake_editor)
    monkeypatch.setattr(mmc, "try_import_rich", lambda: MagicMock(name="rich"))
    monkeypatch.setattr(mmc, "import_quartz", _boom_quartz)

    rc = mmc.main(["--learn", "--dry-run-after-start"])
    assert rc == 0
