"""Plan-021: --show-only + --dry-run-after-start exits 0 with show-only fields in JSON."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


def _run_script(
    repo_root: Path,
    script_path: Path,
    argv: list[str],
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    return subprocess.run(
        [sys.executable, str(script_path), *argv],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _extract_dry_run_payload(stderr: str) -> dict:
    m = re.search(
        r"MACOS_MOUSE_CLICK_DRY_RUN_JSON (\{.*\})\s*$",
        stderr,
        re.MULTILINE,
    )
    assert m, stderr
    return json.loads(m.group(1))


def test_show_only_dry_run_emits_show_only_fields_default_dwell(
    repo_root: Path, script_path: Path
) -> None:
    r = _run_script(
        repo_root,
        script_path,
        [
            "-x", "100", "-y", "200", "-n", "5", "-Y",
            "--show-only", "--dry-run-after-start",
        ],
    )
    assert r.returncode == 0, r.stderr + r.stdout
    payload = _extract_dry_run_payload(r.stderr)
    assert payload["mode"] == "fixed"
    assert payload["x"] == 100.0
    assert payload["y"] == 200.0
    assert payload["count"] == 5
    assert payload["show_only"] is True
    assert payload["show_dwell_seconds"] == 1.5
    assert payload["show_step"] is False
    # Quartz / AppKit must not be touched on the dry-run path.
    assert "Quartz" not in r.stderr or "MACOS_MOUSE_CLICK_DRY_RUN_JSON" in r.stderr
    assert "AppKit" not in r.stderr
    # Running line surfaces the show-only summary.
    assert "show_only=true" in r.stderr
    assert "would_click=5" in r.stderr
    assert "dwell=1.5s" in r.stderr


def test_show_only_dry_run_with_explicit_dwell(
    repo_root: Path, script_path: Path
) -> None:
    r = _run_script(
        repo_root,
        script_path,
        [
            "-x", "10", "-y", "20", "-n", "1", "-Y",
            "--show-only", "--show-dwell-seconds", "0.25",
            "--dry-run-after-start",
        ],
    )
    assert r.returncode == 0, r.stderr + r.stdout
    payload = _extract_dry_run_payload(r.stderr)
    assert payload["show_only"] is True
    assert payload["show_dwell_seconds"] == 0.25
    assert payload["show_step"] is False
    assert "dwell=0.25s" in r.stderr


def test_show_only_dry_run_with_step(
    repo_root: Path, script_path: Path
) -> None:
    r = _run_script(
        repo_root,
        script_path,
        [
            "-x", "10", "-y", "20", "-n", "1", "-Y",
            "--show-only", "--show-step",
            "--dry-run-after-start",
        ],
    )
    assert r.returncode == 0, r.stderr + r.stdout
    payload = _extract_dry_run_payload(r.stderr)
    assert payload["show_only"] is True
    assert payload["show_step"] is True
    assert "step" in r.stderr
    assert "dwell=" not in r.stderr.split("Running:", 1)[-1].splitlines()[0]


def test_show_only_dry_run_at_cursor_mode(
    repo_root: Path, script_path: Path
) -> None:
    r = _run_script(
        repo_root,
        script_path,
        [
            "--at-cursor", "-n", "3", "-Y",
            "--show-only", "--show-dwell-seconds", "0.1",
            "--dry-run-after-start",
        ],
    )
    assert r.returncode == 0, r.stderr + r.stdout
    payload = _extract_dry_run_payload(r.stderr)
    assert payload["mode"] == "at_cursor"
    assert payload["show_only"] is True
    assert payload["show_dwell_seconds"] == 0.1


def test_show_only_invalid_combination_exits_two(
    repo_root: Path, script_path: Path
) -> None:
    r = _run_script(
        repo_root,
        script_path,
        ["--learn", "-Y", "--show-only", "--dry-run-after-start"],
    )
    assert r.returncode == 2, r.stderr + r.stdout
    assert "--show-only" in r.stderr
    assert "--learn" in r.stderr
