"""Plan 03: MT-09 legacy --interactive without Rich (PTY + PYTHONPATH fake rich)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from dry_run_parse import parse_dry_run_json
from pty_harness import REPO_ROOT, SCRIPT_PATH, spawn_clicker_pexpect


@pytest.fixture
def fake_rich_dir(tmp_path: Path) -> Path:
    (tmp_path / "rich.py").write_text(
        'raise ImportError("mt09 test fake rich")\n',
        encoding="utf-8",
    )
    return tmp_path


def _prepend_pythonpath(fake_dir: Path) -> str:
    d = str(fake_dir)
    old = os.environ.get("PYTHONPATH")
    return d + os.pathsep + old if old else d


@pytest.mark.darwin
@pytest.mark.mt09
def test_mt09_c_no_interactive_stderr_hint(fake_rich_dir: Path) -> None:
    """MT-09-C: fake rich, no --interactive, non-TTY stdin -> exit 2 and hint."""
    env = {
        **os.environ,
        "PYTHONPATH": _prepend_pythonpath(fake_rich_dir),
        "PYTHONUNBUFFERED": "1",
    }
    r = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=str(REPO_ROOT),
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 2
    err = r.stderr or ""
    assert "use --interactive" in err or "or use --interactive" in err


@pytest.mark.darwin
@pytest.mark.mt09
def test_mt09_a_proceed_n_no_quartz(
    fake_rich_dir: Path, pexpect_module, repo_root: Path
) -> None:
    """MT-09-A: legacy prompts, Proceed n -> Cancelled., no learn wait, exit 0."""
    pexpect = pexpect_module
    child = spawn_clicker_pexpect(
        pexpect,
        ["--interactive"],
        cwd=repo_root,
        env={"PYTHONPATH": _prepend_pythonpath(fake_rich_dir)},
        timeout=120,
    )
    child.expect(["Select mode:", "Tip:"], timeout=60)
    child.sendline("1")
    child.expect("Synthetic click count", timeout=30)
    child.sendline("")
    child.expect("Delay between synthetic", timeout=30)
    child.sendline("1.0")
    child.expect("Resolved configuration", timeout=30)
    child.expect("Proceed?", timeout=30)
    child.sendline("n")
    child.expect("Cancelled.", timeout=30)
    child.expect(pexpect.EOF, timeout=30)
    child.close()
    assert child.exitstatus == 0
    buf = str(child.before or "")
    assert "review / edit" not in buf
    assert "Waiting for your first left click" not in buf


@pytest.mark.darwin
@pytest.mark.mt09
def test_mt09_b_proceed_y_dry_run_json(
    fake_rich_dir: Path, pexpect_module, repo_root: Path
) -> None:
    """MT-09-B: Proceed y + dry-run -> JSON line, no anchor wait."""
    pexpect = pexpect_module
    child = spawn_clicker_pexpect(
        pexpect,
        ["--interactive", "--dry-run-after-start"],
        cwd=repo_root,
        env={"PYTHONPATH": _prepend_pythonpath(fake_rich_dir)},
        timeout=120,
    )
    child.expect(["Select mode:", "Tip:"], timeout=60)
    child.sendline("1")
    child.expect("Synthetic click count", timeout=30)
    child.sendline("")
    child.expect("Delay between synthetic", timeout=30)
    child.sendline("1.0")
    child.expect("Resolved configuration", timeout=30)
    child.expect("Proceed?", timeout=30)
    child.sendline("y")
    child.expect("Running:", timeout=30)
    child.expect("MACOS_MOUSE_CLICK_DRY_RUN_JSON", timeout=30)
    child.expect(pexpect.EOF, timeout=30)
    child.close()
    assert child.exitstatus == 0
    tail = str(child.before or "")
    assert "Waiting for your first left click" not in tail
    payload = parse_dry_run_json(tail)
    assert payload["mode"] == "learn"
