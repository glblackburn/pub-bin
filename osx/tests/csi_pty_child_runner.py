#!/usr/bin/env python3
"""Run in a fresh interpreter (no pytest): PTY + handshake + read_raw_key.

Invoked by test_read_raw_key_csi.py to avoid fork() inside pytest's process.
"""

from __future__ import annotations

import os
import pty
import sys
import time
from pathlib import Path

# Must exceed legacy 250ms CSI/SS3 tail waits so a pre-DEF-006 reader returns ``other``.
# Keep under ~1s so the DEF-006 deadline still covers one delayed final byte.
_GAP = 0.45


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("csi", "ss3"):
        print("usage: csi_pty_child_runner.py csi|ss3", file=sys.stderr)
        sys.exit(2)
    mode = sys.argv[1]
    prefix = b"\x1b[" if mode == "csi" else b"\x1bO"
    final = b"B"

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

    # Let the child enter read_raw_key() and block on the first read(1) before
    # we push bytes (reduces batching ESC+[ and B in one kernel read).
    time.sleep(0.08)
    os.write(master_fd, prefix)
    time.sleep(_GAP)
    os.write(master_fd, final)

    _, status = os.waitpid(pid, 0)
    os.close(master_fd)
    if not (os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0):
        print("child-exit-fail", flush=True)
        sys.exit(1)
    sys.stdout.buffer.write(os.read(result_r, 256))
    os.close(result_r)


if __name__ == "__main__":
    main()
