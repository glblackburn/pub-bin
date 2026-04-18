"""DEF-006: CSI arrow keys must survive slow inter-byte delivery on the TTY."""

from __future__ import annotations

import os
import pty
import sys
import time
from pathlib import Path

import pytest

OSX_DIR = Path(__file__).resolve().parent.parent


@pytest.mark.darwin
def test_read_raw_key_csi_down_slow_inter_byte_gap() -> None:
    """Parent sends ESC [ then waits >250ms before B (one logical Down).

    A per-byte 250ms cap (pre-DEF-006) returned ``other`` and broke row nav.

    Uses ``pty.fork()`` so the child has a real controlling terminal; pairing
    ``openpty`` with ``subprocess`` did not deliver master writes to stdin on
    macOS in CI-style runs.
    """
    pipe_r, pipe_w = os.pipe()
    pid, master_fd = pty.fork()
    if pid == 0:
        os.close(pipe_r)
        # Do not close master_fd here: on some systems it shares the open file
        # with the parent and breaks the parent's ability to write.
        try:
            # pty.fork wires fd 0 to the slave, but sys.stdin can still be pytest's
            # DontReadFromInput; rebind stdio to the real fds before read_raw_key().
            sys.stdin = os.fdopen(0, "r", buffering=1)
            sys.stdout = os.fdopen(1, "w", buffering=1)
            sys.stderr = os.fdopen(2, "w", buffering=1)
            if str(OSX_DIR) not in sys.path:
                sys.path.insert(0, str(OSX_DIR))
            import macos_mouse_click as mmc

            k = mmc.read_raw_key()
            os.write(pipe_w, (k + "\n").encode())
        finally:
            os.close(pipe_w)
        os._exit(0)

    os.close(pipe_w)
    time.sleep(0.08)
    os.write(master_fd, b"\x1b[")
    time.sleep(0.30)
    os.write(master_fd, b"B")
    _, status = os.waitpid(pid, 0)
    os.close(master_fd)
    assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
    raw = os.read(pipe_r, 256)
    os.close(pipe_r)
    assert raw.decode().strip() == "down"


@pytest.mark.darwin
def test_read_raw_key_ss3_down_slow_final_byte() -> None:
    """Application cursor Down: ESC O then delayed B."""
    pipe_r, pipe_w = os.pipe()
    pid, master_fd = pty.fork()
    if pid == 0:
        os.close(pipe_r)
        try:
            sys.stdin = os.fdopen(0, "r", buffering=1)
            sys.stdout = os.fdopen(1, "w", buffering=1)
            sys.stderr = os.fdopen(2, "w", buffering=1)
            if str(OSX_DIR) not in sys.path:
                sys.path.insert(0, str(OSX_DIR))
            import macos_mouse_click as mmc

            k = mmc.read_raw_key()
            os.write(pipe_w, (k + "\n").encode())
        finally:
            os.close(pipe_w)
        os._exit(0)

    os.close(pipe_w)
    time.sleep(0.08)
    os.write(master_fd, b"\x1bO")
    time.sleep(0.30)
    os.write(master_fd, b"B")
    _, status = os.waitpid(pid, 0)
    os.close(master_fd)
    assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
    raw = os.read(pipe_r, 256)
    os.close(pipe_r)
    assert raw.decode().strip() == "down"
