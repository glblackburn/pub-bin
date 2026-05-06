"""Tests for magic_cookie_labels (plan-016)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from magic_cookie_labels import (  # noqa: E402
    LabelRecord,
    LabelStore,
    bbox_iou,
    display_rect_to_image_bbox,
    image_bbox_to_display_rect,
    utc_now_iso,
)


def test_display_rect_to_image_bbox_square_fit() -> None:
    # Widget 100x100, image 50x50 (scale 2, no letterbox offset).
    x, y, w, h = display_rect_to_image_bbox(100, 100, 50, 50, 10.0, 10.0, 40.0, 40.0)
    assert (x, y) == (5, 5)
    assert w == 16 and h == 16


def test_image_bbox_roundtrip_full_fit() -> None:
    # Image 50x50 scaled 2x into widget 100x100 (no letterbox).
    x1, y1, x2, y2 = image_bbox_to_display_rect(100, 100, 50, 50, 10, 10, 20, 20)
    back = display_rect_to_image_bbox(100, 100, 50, 50, x1, y1, x2, y2)
    assert back == (10, 10, 20, 20)


def test_label_store_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "magic-cookie-labels.jsonl"
    st = LabelStore(p)
    r1 = LabelRecord(
        image_path=str(tmp_path / "a.png"),
        image_sha256="aa",
        image_wh=(10, 20),
        magic_cookie=False,
        bbox_px=None,
        labeled_at=utc_now_iso(),
    )
    st.upsert(r1)
    st.save()
    st2 = LabelStore(p)
    st2.load()
    got = st2.get(tmp_path / "a.png")
    assert got is not None
    assert got.magic_cookie is False
    assert got.bbox_px is None


def test_label_store_upsert_replaces(tmp_path: Path) -> None:
    p = tmp_path / "labels.jsonl"
    st = LabelStore(p)
    path = tmp_path / "b.png"
    path.write_bytes(b"x")
    st.upsert(
        LabelRecord(
            image_path=str(path.resolve()),
            image_sha256="1",
            image_wh=(4, 4),
            magic_cookie=None,
            bbox_px=None,
            labeled_at="t1",
        )
    )
    st.save()
    st.upsert(
        LabelRecord(
            image_path=str(path.resolve()),
            image_sha256="2",
            image_wh=(4, 4),
            magic_cookie=True,
            bbox_px=(0, 0, 2, 2),
            labeled_at="t2",
        )
    )
    st.save()
    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 1
    o = json.loads(lines[0])
    assert o["magic_cookie"] is True
    assert o["bbox_px"] == [0, 0, 2, 2]


def test_bbox_iou_identical() -> None:
    b = (10, 20, 30, 40)
    assert bbox_iou(b, b) == pytest.approx(1.0)


def test_bbox_iou_disjoint() -> None:
    assert bbox_iou((0, 0, 10, 10), (20, 0, 10, 10)) == 0.0


def test_bbox_iou_partial_overlap() -> None:
    a = (0, 0, 10, 10)
    b = (5, 5, 10, 10)
    inter = 5 * 5
    union = 100 + 100 - inter
    assert bbox_iou(a, b) == pytest.approx(inter / union)
