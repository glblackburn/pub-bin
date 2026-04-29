"""DEF-012: coords-only profiles skip OpenCV; explicit -P default file ≡ no -P."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LOOP_SH = REPO_ROOT / "osx" / "macos_mouse_click_loop.sh"
DEFAULTS_PROFILE = REPO_ROOT / "osx" / "config" / "cookie_clicker_profile.defaults.json"


def _run_loop(argv: list[str]) -> subprocess.CompletedProcess[str]:
    cmd = ["/usr/bin/env", "bash", str(LOOP_SH), *argv]
    return subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_def012_explicit_default_profile_same_outcome_as_no_p_preview_only() -> None:
    """-P path same as built-in default is normalized to no -P (same exit + message)."""
    r_no_p = _run_loop(["-N"])
    r_explicit = _run_loop(
        ["-P", str(DEFAULTS_PROFILE.relative_to(REPO_ROOT)), "-N"]
    )
    assert r_no_p.returncode == 0, (r_no_p.stderr, r_no_p.stdout)
    assert r_explicit.returncode == 0, (r_explicit.stderr, r_explicit.stdout)
    assert "Preview-only mode complete" in (r_no_p.stdout + r_no_p.stderr)
    assert "Preview-only mode complete" in (r_explicit.stdout + r_explicit.stderr)


def test_def012_preview_only_separate_coords_only_path_exits_2_before_opencv(
    tmp_path: Path,
) -> None:
    """Explicit -P to a different path (still builtin) + -N must error before OpenCV."""
    alt = tmp_path / "coords_only_profile.json"
    shutil.copyfile(DEFAULTS_PROFILE, alt)
    r = _run_loop(["-P", str(alt), "-N"])
    assert r.returncode == 2, (r.stderr, r.stdout)
    combined = (r.stdout + r.stderr).lower()
    assert "unable to load source image" not in combined
    assert "preview only" in combined or "drawable" in combined or "source_image" in combined


def test_def012_require_preview_separate_coords_only_path_exits_1(
    tmp_path: Path,
) -> None:
    alt = tmp_path / "coords_only_profile.json"
    shutil.copyfile(DEFAULTS_PROFILE, alt)
    r = _run_loop(["-P", str(alt), "-R"])
    assert r.returncode == 1, (r.stderr, r.stdout)
    combined = (r.stdout + r.stderr).lower()
    assert "unable to load source image" not in combined
    assert "-r" in combined or "manifest" in combined or "drawable" in combined
