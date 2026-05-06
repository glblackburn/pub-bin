"""Tests for tools/eval_magic_cookie_labels.py (plan-018)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL = REPO_ROOT / "tools" / "eval_magic_cookie_labels.py"


def test_eval_script_smoke_pos_and_neg(tmp_path: Path) -> None:
    pytest.importorskip("cv2")
    import cv2  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415

    neg = tmp_path / "neg.png"
    pos = tmp_path / "pos.png"
    cv2.imwrite(str(neg), np.zeros((200, 200, 3), dtype=np.uint8))
    img = np.zeros((320, 480, 3), dtype=np.uint8)
    cv2.circle(img, (120, 100), 22, (0, 220, 255), -1)
    cv2.imwrite(str(pos), img)

    labels = tmp_path / "magic-cookie-labels.jsonl"
    rows = [
        {
            "schema_version": 1,
            "image_path": str(neg.resolve()),
            "image_sha256": "0",
            "image_wh": [200, 200],
            "magic_cookie": False,
            "bbox_px": None,
            "labeled_at": "2026-05-04T00:00:00Z",
            "tool_version": "test",
        },
        {
            "schema_version": 1,
            "image_path": str(pos.resolve()),
            "image_sha256": "1",
            "image_wh": [480, 320],
            "magic_cookie": True,
            "bbox_px": [90, 70, 70, 70],
            "labeled_at": "2026-05-04T00:00:00Z",
            "tool_version": "test",
        },
    ]
    labels.write_text("\n".join(json.dumps(r, separators=(",", ":")) for r in rows) + "\n", encoding="utf-8")

    r = subprocess.run(
        [sys.executable, str(EVAL), "--labels", str(labels), "--iou-threshold", "0.25", "--top-k", "6"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    summary = json.loads(r.stdout.strip())
    assert summary["n_positives"] == 1
    assert summary["n_negatives"] == 1
    assert summary["false_negatives"] == 0
    assert summary["false_positives"] == 0
    assert summary["recall_at_k"] == 1.0
