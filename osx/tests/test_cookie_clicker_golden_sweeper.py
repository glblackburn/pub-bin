"""Tests for cookie_clicker_golden_sweeper.py (plan-015)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SWEEPER = REPO_ROOT / "osx" / "cookie_clicker_golden_sweeper.py"


pytest.importorskip("cv2")

from cookie_clicker_golden_sweeper import (  # noqa: E402
    _annotate_hits_on_bgr,
    detect_magic_cookie_hits,
)


def _yellow_blob_bgr(w: int = 480, h: int = 320, cx: int = 120, cy: int = 100, r: int = 22) -> "object":
    import numpy as np
    import cv2

    img = np.zeros((h, w, 3), dtype=np.uint8)
    cv2.circle(img, (cx, cy), r, (0, 220, 255), -1)
    return img


def test_annotate_draws_boxes() -> None:
    bgr = _yellow_blob_bgr()
    hits = detect_magic_cookie_hits(bgr, exclude_xy=None)
    assert hits
    vis = _annotate_hits_on_bgr(bgr, hits)
    assert vis.shape == bgr.shape
    assert (vis != bgr).any(), "annotation should change some pixels"


def test_detect_finds_yellow_blob() -> None:
    bgr = _yellow_blob_bgr()
    hits = detect_magic_cookie_hits(bgr, exclude_xy=None)
    assert hits, "expected at least one HSV hit on synthetic golden blob"
    best = hits[0]
    assert abs(best.x - 120) < 8 and abs(best.y - 100) < 8


def test_exclude_near_cookie() -> None:
    bgr = _yellow_blob_bgr(cx=200, cy=200)
    hits = detect_magic_cookie_hits(bgr, exclude_xy=(200.0, 200.0), exclude_radius=80.0)
    assert not hits


def test_cli_input_image_json_stdout(tmp_path: Path) -> None:
    import cv2

    png = tmp_path / "s.png"
    cv2.imwrite(str(png), _yellow_blob_bgr())
    r = subprocess.run(
        [
            sys.executable,
            str(SWEEPER),
            "--input-image",
            str(png),
            "--output",
            "json",
            "--max-polls",
            "1",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0, r.stderr
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    assert lines, r.stdout
    row = json.loads(lines[0])
    assert "x" in row and "y" in row and row.get("kind") == "golden"
    assert row.get("coord_space") == "image_pixels"
    assert isinstance(row["x"], (int, float))
    sidecar = png.with_suffix(".json")
    assert sidecar.is_file(), f"missing sidecar {sidecar}"
    file_lines = [ln for ln in sidecar.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert file_lines == lines


@pytest.mark.skipif(sys.platform != "darwin", reason="Quartz display mapping is macOS-only")
def test_roundtrip_main_display_mapping() -> None:
    pytest.importorskip("Quartz", reason="pyobjc Quartz")
    from cookie_clicker_golden_sweeper import capture_px_to_quartz_global, quartz_global_to_capture_px

    iw, ih = 800, 600
    ix, iy = 100.0, 200.0
    gx, gy = capture_px_to_quartz_global(ix, iy, iw, ih)
    ix2, iy2 = quartz_global_to_capture_px(gx, gy, iw, ih)
    assert abs(ix2 - ix) < 1.5 and abs(iy2 - iy) < 1.5
