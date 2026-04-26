#!/usr/bin/env python3
"""Tests for cookie_clicker_detect_coords.py profile generation."""

from __future__ import annotations

import json
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


def test_detect_coords_generates_profile_json(repo_root: Path, tmp_path: Path, screenshot_path: Path) -> None:
    pytest.importorskip("cv2")
    script = repo_root / "osx" / "cookie_clicker_detect_coords.py"
    output_json = tmp_path / "detected-profile.json"

    r = subprocess.run(
        [
            sys.executable,
            str(script),
            "--input",
            str(screenshot_path),
            "--output",
            str(output_json),
            "--profile",
            "pytest-profile",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    assert output_json.exists()

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["profile_name"] == "pytest-profile"
    assert "cookie" in payload and "x" in payload["cookie"] and "y" in payload["cookie"]
    assert "store" in payload and "row_spacing" in payload["store"]
    assert isinstance(payload["ladder_rows"], list)
    assert len(payload["ladder_rows"]) >= 8


def test_detect_coords_emits_json_status(repo_root: Path, tmp_path: Path, screenshot_path: Path) -> None:
    pytest.importorskip("cv2")
    script = repo_root / "osx" / "cookie_clicker_detect_coords.py"
    output_json = tmp_path / "detected-profile.json"

    r = subprocess.run(
        [
            sys.executable,
            str(script),
            "--input",
            str(screenshot_path),
            "--output",
            str(output_json),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    status = json.loads(r.stdout.strip())
    assert status["output"] == str(output_json.resolve())
    assert status["status"] in ("ok", "warning")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
