"""Plan-014: post-ladder cookie burst factor (-k) on macos_mouse_click_loop.sh."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LOOP_SH = REPO_ROOT / "osx" / "macos_mouse_click_loop.sh"
SCREENSHOT = (
    REPO_ROOT
    / "docs"
    / "osx"
    / "screenshots"
    / "cookie-clicker"
    / "Screenshot_2026-04-25_at_8.28.45_PM.png"
)


def test_loop_help_documents_k_flag() -> None:
    r = subprocess.run(
        ["/usr/bin/env", "bash", str(LOOP_SH), "-h"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert r.returncode == 0, r.stderr
    out = r.stdout + r.stderr
    assert "-k" in out
    assert "burst factor" in out.lower() or "Post-ladder" in out
    assert "separate" in out.lower()
    assert "cycle_sleep" in out.lower().replace(" ", "_") or "CYCLE_SLEEP" in out


def test_preview_plan_burst_factor_scales_cookie_target(
    repo_root: Path, tmp_path: Path
) -> None:
    if not SCREENSHOT.is_file():
        pytest.skip("screenshot fixture path missing")
    pytest.importorskip("cv2")
    detect_script = repo_root / "osx" / "cookie_clicker_detect_coords.py"
    preview_script = repo_root / "osx" / "cookie_clicker_preview_plan.py"
    profile_json = tmp_path / "profile.json"
    manifest_json = tmp_path / "preview.json"

    r_detect = subprocess.run(
        [
            sys.executable,
            str(detect_script),
            "--input",
            str(SCREENSHOT),
            "--output",
            str(profile_json),
            "--profile",
            "pytest-plan014",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r_detect.returncode == 0, r_detect.stderr

    r_preview = subprocess.run(
        [
            sys.executable,
            str(preview_script),
            "--profile",
            str(profile_json),
            "--manifest-out",
            str(manifest_json),
            "--cookie-clicks",
            "100",
            "--ladder-clicks",
            "2",
            "--post-ladder-cookie-burst-factor",
            "3",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r_preview.returncode == 0, r_preview.stderr
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    assert manifest["options"]["post_ladder_cookie_burst_factor"] == 3
    cookie_targets = [t for t in manifest["targets"] if t["phase"] == "cookie_burst"]
    assert len(cookie_targets) == 3
    for i, t in enumerate(cookie_targets, start=1):
        assert t["click_count"] == 100
        assert t["name"] == f"cookie_phase_{i}"
