"""Automated regressions for defects still marked **Open** in ``docs/osx/defects/README.md``.

When a new defect row is **Open**, add coverage here (or drop **Open** until automated).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

import macos_mouse_click as mmc

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFECTS_README = REPO_ROOT / "docs" / "osx" / "defects" / "README.md"
SCRIPT_PATH = REPO_ROOT / "osx" / "macos_mouse_click.py"

# Every **Open** DEF in the README must be listed here once automated coverage exists.
_AUTOMATED_OPEN_DEFECT_IDS = frozenset({"007", "008"})


def _open_defect_ids_from_readme() -> set[str]:
    text = DEFECTS_README.read_text(encoding="utf-8")
    found: set[str] = set()
    for line in text.splitlines():
        m = re.match(r"^\|\s*(DEF-\d{3})\b", line.strip())
        if not m:
            continue
        if "**Open**" not in line:
            continue
        num = m.group(1).split("-", 1)[1]
        found.add(num)
    return found


def test_readme_open_defects_have_automated_regressions() -> None:
    """Fail CI if a new **Open** row appears without a matching regression entry."""
    open_ids = _open_defect_ids_from_readme()
    missing = open_ids - _AUTOMATED_OPEN_DEFECT_IDS
    assert not missing, (
        f"README lists Open defect(s) {sorted(missing)} not covered in "
        f"test_open_defects._AUTOMATED_OPEN_DEFECT_IDS — add tests or adjust set."
    )


def test_def007_argv_duplicate_cli_option_error_detects_double_count() -> None:
    err = mmc.argv_duplicate_cli_option_error(
        ["--learn", "-Y", "-n", "1", "-n", "2"]
    )
    assert err and "count" in err.lower()


def test_def007_single_count_allowed() -> None:
    assert mmc.argv_duplicate_cli_option_error(["--learn", "-Y", "-n", "3"]) is None


def test_def007_mixed_count_flags_count_as_duplicate() -> None:
    err = mmc.argv_duplicate_cli_option_error(["--learn", "-Y", "-n", "1", "--count=2"])
    assert err


def test_def007_duplicate_delay() -> None:
    err = mmc.argv_duplicate_cli_option_error(["-x", "1", "-y", "2", "-d", "0", "-d", "1"])
    assert err and "delay" in err.lower()


def test_def008_arrow_bump_selected_for_down() -> None:
    assert mmc._tui_bump_selected_for_arrow_key(0, "down", 5) == 1


def test_def008_arrow_bump_selected_for_up() -> None:
    assert mmc._tui_bump_selected_for_arrow_key(2, "up", 5) == 1


def test_def008_non_arrow_unchanged() -> None:
    assert mmc._tui_bump_selected_for_arrow_key(1, "enter", 5) == 1


def test_def007_subprocess_duplicate_n_exits_2(
    repo_root: Path, script_path: Path
) -> None:
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    cp = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--learn",
            "-Y",
            "-n",
            "10",
            "-d",
            "0",
            "-n",
            "5",
        ],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert cp.returncode == 2
    assert "count" in (cp.stderr or "").lower()
