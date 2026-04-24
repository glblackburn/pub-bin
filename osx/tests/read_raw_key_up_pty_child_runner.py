#!/usr/bin/env python3
"""Run in a fresh interpreter (no pytest): PTY + handshake + read_raw_key (Up).

Terminology (see ``docs/osx/TERMINOLOGY.md``):
- **CSI** = Control Sequence Introducer (terminal bytes often starting ``ESC`` ``[``).
- **SS3-style** = arrow bytes introduced by ``ESC`` ``O`` instead of ``ESC`` ``[``.
- **PTY** = pseudo-terminal; pytest spawns this helper under a PTY with timed writes.

Same staggered-write rationale as ``csi_pty_child_runner.py``, but the final
byte is **``A``** (CSI ``ESC [ … A`` / SS3 ``ESC O A``) so ``read_raw_key()``
should return ``up`` after the slow tail.

Invoked by ``test_read_raw_key_up_slow_gap.py`` to avoid ``pty.fork()`` inside
pytest's process.
"""

from __future__ import annotations

import os
import pty
import sys
import time
from pathlib import Path

_GAP = 0.45
_INTER_ESC = 0.04


def _inject_csi_up(master_fd: int) -> None:
    time.sleep(0.08)
    os.write(master_fd, b"\x1b")
    time.sleep(_INTER_ESC)
    os.write(master_fd, b"[")
    time.sleep(_GAP)
    os.write(master_fd, b"A")


def _inject_ss3_up(master_fd: int) -> None:
    time.sleep(0.08)
    os.write(master_fd, b"\x1b")
    time.sleep(_INTER_ESC)
    os.write(master_fd, b"O")
    time.sleep(_GAP)
    os.write(master_fd, b"A")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("csi-up", "ss3-up"):
        print("usage: read_raw_key_up_pty_child_runner.py csi-up|ss3-up", file=sys.stderr)
        sys.exit(2)
    mode = sys.argv[1]

    sync_r, sync_w = os.pipe()
    result_r, result_w = os.pipe()
    pid, master_fd = pty.fork()
    if pid == 0:
        os.close(sync_r)
        os.close(result_r)
        try:
            here = Path(__file__).resolve().parent.parent
            if str(here) not in sys.path:
                sys.path.insert(0, str(here))
            import macos_mouse_click as mmc

            os.write(sync_w, b"R")
            os.close(sync_w)
            k = mmc.read_raw_key()
            os.write(result_w, (k + "\n").encode())
        finally:
            os.close(result_w)
        os._exit(0)

    os.close(sync_w)
    os.close(result_w)
    if os.read(sync_r, 1) != b"R":
        os.close(sync_r)
        os.waitpid(pid, 0)
        os.close(master_fd)
        print("handshake-fail", flush=True)
        sys.exit(1)
    os.close(sync_r)

    if mode == "csi-up":
        _inject_csi_up(master_fd)
    else:
        _inject_ss3_up(master_fd)

    _, status = os.waitpid(pid, 0)
    os.close(master_fd)
    if not (os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0):
        print("child-exit-fail", flush=True)
        sys.exit(1)
    sys.stdout.buffer.write(os.read(result_r, 256))
    os.close(result_r)


if __name__ == "__main__":
    main()
