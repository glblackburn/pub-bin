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
            "--no-ocr",
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
            "--no-ocr",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    status = json.loads(r.stdout.strip())
    assert status["output"] == str(output_json.resolve())
    assert status["status"] in ("ok", "warning")


def test_ladder_row_x_in_right_half_of_detected_store(
    repo_root: Path, tmp_path: Path, screenshot_path: Path
) -> None:
    """Buy-ladder clicks must sit on the store's buy side, not the game–store divider."""
    pytest.importorskip("cv2")
    if not screenshot_path.is_file():
        pytest.skip(f"missing fixture screenshot: {screenshot_path}")
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
            "pytest-x-placement",
            "--no-ocr",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    st = payload["store"]
    pl, pr = float(st["panel_left"]), float(st["panel_right"])
    mid = (pl + pr) / 2.0
    for row in payload["ladder_rows"]:
        assert float(row["x"]) > mid, (
            f"ladder {row['name']!r} x={row['x']} should be right of panel mid={mid:.1f}"
        )


def test_match_building_from_ocr_line_multiword_tokens() -> None:
    pytest.importorskip("cv2")
    from cookie_clicker_detect_coords import _match_building_from_ocr_line

    assert _match_building_from_ocr_line("buy wizard tower") == "wizard_tower"
    assert _match_building_from_ocr_line("time machine") == "time_machine"
    assert _match_building_from_ocr_line("alchemy lab") == "alchemy_lab"


def test_interpolate_row_y_for_order() -> None:
    pytest.importorskip("cv2")
    from cookie_clicker_detect_coords import interpolate_row_y_for_order

    order = ["a", "b", "c"]
    partial = {"a": 10.0, "c": 50.0}
    out = interpolate_row_y_for_order(order, partial)
    assert out["a"] == 10.0
    assert out["c"] == 50.0
    assert abs(out["b"] - 30.0) < 1e-6


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
