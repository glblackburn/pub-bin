"""Spawn macos_mouse_click.py under a PTY for plan 03 integration tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

OSX_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = OSX_DIR.parent
SCRIPT_PATH = OSX_DIR / "macos_mouse_click.py"


def base_child_env(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    """PYTHONUNBUFFERED + stable geometry; caller should merge os.environ."""
    out = {
        **os.environ,
        "PYTHONUNBUFFERED": "1",
        "COLUMNS": "120",
        "LINES": "40",
    }
    if extra:
        out.update(extra)
    return out


def spawn_clicker_pexpect(
    pexpect: Any,
    args: Sequence[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    timeout: int = 120,
):
    """
    Start ``python <script>`` with a PTY (stdin+stdout are TTYs).

    Rich pre-run editor writes the panel to stdout; ``Running:`` uses stderr.
    pexpect merges both into ``child.before`` / match buffers.
    """
    cmd = [sys.executable, str(SCRIPT_PATH), *args]
    merged = base_child_env(dict(env) if env else None)
    return pexpect.spawn(
        cmd[0],
        cmd[1:],
        cwd=str(cwd or REPO_ROOT),
        env=merged,
        timeout=timeout,
        maxread=200000,
        encoding="utf-8",
        codec_errors="replace",
        echo=False,
    )
