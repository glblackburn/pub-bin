"""DEF-006 symmetry: CSI / SS3 Up arrow slow final byte on the TTY."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

OSX_DIR = Path(__file__).resolve().parent.parent
_RUNNER = Path(__file__).resolve().parent / "read_raw_key_up_pty_child_runner.py"


def _run_runner(mode: str) -> str:
    env = {**os.environ, "PYTHONPATH": str(OSX_DIR)}
    proc = subprocess.run(
        [sys.executable, str(_RUNNER), mode],
        cwd=str(OSX_DIR.parent),
        env=env,
        capture_output=True,
        timeout=30,
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    return proc.stdout.decode("utf-8", errors="replace").strip()


@pytest.mark.darwin
def test_read_raw_key_csi_up_slow_inter_byte_gap() -> None:
    """CSI Up: ``ESC [`` then a gap >250ms before ``A`` (DEF-006 tail deadline)."""
    assert _run_runner("csi-up") == "up"


@pytest.mark.darwin
def test_read_raw_key_ss3_up_slow_final_byte() -> None:
    """SS3 Up: ``ESC O`` then a gap >250ms before ``A``."""
    assert _run_runner("ss3-up") == "up"
