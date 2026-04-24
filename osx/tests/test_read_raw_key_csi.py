"""DEF-006: CSI arrow keys must survive slow inter-byte delivery on the TTY.

**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

OSX_DIR = Path(__file__).resolve().parent.parent
_RUNNER = Path(__file__).resolve().parent / "csi_pty_child_runner.py"


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
def test_read_raw_key_csi_down_slow_inter_byte_gap() -> None:
    """CSI Down: ``ESC [`` then a gap >250ms before ``B``.

    Pre-DEF-006 used ``wait_char(0.25)`` after ``[``; a 350ms gap forces a timeout
    unless the reader uses a cumulative deadline (DEF-006).

    The probe runs in a **subprocess** (see ``csi_pty_child_runner.py``) so we do
    not call ``pty.fork()`` inside pytest's multi-threaded interpreter (that can
    hang or reorder I/O vs the old in-process test).
    """
    assert _run_runner("csi") == "down"


@pytest.mark.darwin
def test_read_raw_key_ss3_down_slow_final_byte() -> None:
    """SS3 Down: ``ESC O`` then a gap >250ms before ``B``."""
    assert _run_runner("ss3") == "down"
