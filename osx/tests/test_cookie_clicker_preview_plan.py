#!/usr/bin/env python3
"""Tests for cookie_clicker_preview_plan.py artifact generation."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def screenshot_path(repo_root: Path) -> Path:
    return (
        repo_root
        / "docs"
        / "osx"
        / "screenshots"
        / "cookie-clicker"
        / "Screenshot_2026-04-25_at_8.28.45_PM.png"
    )


def test_preview_plan_outputs_image_and_manifest(repo_root: Path, tmp_path: Path, screenshot_path: Path) -> None:
    pytest.importorskip("cv2")
    detect_script = repo_root / "osx" / "cookie_clicker_detect_coords.py"
    preview_script = repo_root / "osx" / "cookie_clicker_preview_plan.py"

    profile_json = tmp_path / "profile.json"
    preview_png = tmp_path / "preview.png"
    manifest_json = tmp_path / "preview.json"

    r_detect = subprocess.run(
        [
            sys.executable,
            str(detect_script),
            "--input",
            str(screenshot_path),
            "--output",
            str(profile_json),
            "--profile",
            "pytest-preview",
            "--no-ocr",
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
            "--image-out",
            str(preview_png),
            "--manifest-out",
            str(manifest_json),
            "--cookie-clicks",
            "200",
            "--ladder-clicks",
            "3",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r_preview.returncode == 0, r_preview.stderr
    assert preview_png.exists()
    assert manifest_json.exists()

    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    assert manifest["preview_image"] == str(preview_png.resolve())
    assert len(manifest["targets"]) >= 2
    assert any(t["phase"] == "cookie_burst" for t in manifest["targets"])
    assert any(t["phase"] == "ladder" for t in manifest["targets"])


def test_preview_plan_skip_ladder_outputs_cookie_target_only(
    repo_root: Path, tmp_path: Path, screenshot_path: Path
) -> None:
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
            str(screenshot_path),
            "--output",
            str(profile_json),
            "--no-ocr",
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
            "--skip-ladder",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r_preview.returncode == 0, r_preview.stderr

    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    assert len(manifest["targets"]) == 1
    assert manifest["targets"][0]["phase"] == "cookie_burst"


def test_preview_plan_builtin_source_image_exits_before_imread(
    repo_root: Path, tmp_path: Path
) -> None:
    pytest.importorskip("cv2")
    preview_script = repo_root / "osx" / "cookie_clicker_preview_plan.py"
    defaults = repo_root / "osx" / "config" / "cookie_clicker_profile.defaults.json"
    profile_json = tmp_path / "builtin_profile.json"
    shutil.copyfile(defaults, profile_json)
    r_preview = subprocess.run(
        [
            sys.executable,
            str(preview_script),
            "--profile",
            str(profile_json),
            "--image-out",
            str(tmp_path / "out.png"),
            "--manifest-out",
            str(tmp_path / "out.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r_preview.returncode != 0
    err = (r_preview.stdout + r_preview.stderr).lower()
    assert "builtin" in err
    assert "coords-only" in err or "preview" in err


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
