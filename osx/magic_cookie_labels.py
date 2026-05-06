"""JSONL label store and image coordinate mapping for plan-016 (magic cookie label tool)."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = 1
TOOL_VERSION = "magic_cookie_label_tool/1"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def image_bbox_to_display_rect(
    widget_w: int,
    widget_h: int,
    img_w: int,
    img_h: int,
    x: int,
    y: int,
    w: int,
    h: int,
) -> Tuple[float, float, float, float]:
    """Map image ``[x,y,w,h]`` to widget-space axis-aligned rect as ``(x1,y1,x2,y2)`` floats."""
    if img_w < 1 or img_h < 1 or widget_w < 1 or widget_h < 1:
        return (0.0, 0.0, 1.0, 1.0)
    scale = min(widget_w / float(img_w), widget_h / float(img_h))
    dw = img_w * scale
    dh = img_h * scale
    ox = (widget_w - dw) * 0.5
    oy = (widget_h - dh) * 0.5
    x1d = x * scale + ox
    y1d = y * scale + oy
    x2d = (x + max(0, w - 1)) * scale + ox
    y2d = (y + max(0, h - 1)) * scale + oy
    return (x1d, y1d, x2d, y2d)


def display_rect_to_image_bbox(
    widget_w: int,
    widget_h: int,
    img_w: int,
    img_h: int,
    disp_x1: float,
    disp_y1: float,
    disp_x2: float,
    disp_y2: float,
) -> Tuple[int, int, int, int]:
    """Map a rubber-band rectangle in widget pixels to ``[x, y, w, h]`` in image pixels.

    The image is letterboxed (aspect preserved, centered) inside the widget.
    """
    if img_w < 1 or img_h < 1 or widget_w < 1 or widget_h < 1:
        return (0, 0, 1, 1)
    scale = min(widget_w / float(img_w), widget_h / float(img_h))
    dw = img_w * scale
    dh = img_h * scale
    ox = (widget_w - dw) * 0.5
    oy = (widget_h - dh) * 0.5

    def to_img(px: float, py: float) -> Tuple[float, float]:
        return (px - ox) / scale, (py - oy) / scale

    ix1, iy1 = to_img(disp_x1, disp_y1)
    ix2, iy2 = to_img(disp_x2, disp_y2)
    fx_lo = max(0.0, min(float(img_w - 1), min(ix1, ix2)))
    fy_lo = max(0.0, min(float(img_h - 1), min(iy1, iy2)))
    fx_hi = max(0.0, min(float(img_w - 1), max(ix1, ix2)))
    fy_hi = max(0.0, min(float(img_h - 1), max(iy1, iy2)))
    x1 = int(math.floor(fx_lo))
    y1 = int(math.floor(fy_lo))
    x2 = int(math.ceil(fx_hi))
    y2 = int(math.ceil(fy_hi))
    x1 = max(0, min(x1, img_w - 1))
    y1 = max(0, min(y1, img_h - 1))
    x2 = max(0, min(x2, img_w - 1))
    y2 = max(0, min(y2, img_h - 1))
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1
    w = max(1, x2 - x1 + 1)
    h = max(1, y2 - y1 + 1)
    return (x1, y1, w, h)


@dataclass
class LabelRecord:
    image_path: str
    image_sha256: str
    image_wh: Tuple[int, int]
    magic_cookie: Optional[bool]
    bbox_px: Optional[Tuple[int, int, int, int]]
    labeled_at: str
    tool_version: str = TOOL_VERSION

    def to_json_obj(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "image_path": self.image_path,
            "image_sha256": self.image_sha256,
            "image_wh": [int(self.image_wh[0]), int(self.image_wh[1])],
            "magic_cookie": self.magic_cookie,
            "bbox_px": list(self.bbox_px) if self.bbox_px is not None else None,
            "labeled_at": self.labeled_at,
            "tool_version": self.tool_version,
        }

    @classmethod
    def from_json_obj(cls, o: Dict[str, Any]) -> LabelRecord:
        mc = o.get("magic_cookie")
        if mc is not None and not isinstance(mc, bool):
            raise ValueError("magic_cookie must be bool or null")
        bp = o.get("bbox_px")
        bbox: Optional[Tuple[int, int, int, int]]
        if bp is None:
            bbox = None
        else:
            bbox = (int(bp[0]), int(bp[1]), int(bp[2]), int(bp[3]))
        wh = o.get("image_wh")
        return cls(
            image_path=str(o["image_path"]),
            image_sha256=str(o["image_sha256"]),
            image_wh=(int(wh[0]), int(wh[1])),
            magic_cookie=mc,
            bbox_px=bbox,
            labeled_at=str(o["labeled_at"]),
            tool_version=str(o.get("tool_version", TOOL_VERSION)),
        )


class LabelStore:
    """Load / upsert / save JSONL (one object per line), keyed by resolved image path."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._by_key: Dict[str, LabelRecord] = {}

    @staticmethod
    def _key(image_path: Path) -> str:
        return str(image_path.resolve())

    def load(self) -> None:
        self._by_key.clear()
        if not self.path.is_file():
            return
        text = self.path.read_text(encoding="utf-8")
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            rec = LabelRecord.from_json_obj(json.loads(line))
            self._by_key[self._key(Path(rec.image_path))] = rec

    def get(self, image_path: Path) -> Optional[LabelRecord]:
        return self._by_key.get(self._key(image_path))

    def upsert(self, rec: LabelRecord) -> None:
        self._by_key[self._key(Path(rec.image_path))] = rec

    def all_records(self) -> List[LabelRecord]:
        return sorted(self._by_key.values(), key=lambda r: r.image_path)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(rec.to_json_obj(), separators=(",", ":")) for rec in self.all_records()]
        body = "\n".join(lines) + ("\n" if lines else "")
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(body, encoding="utf-8")
        tmp.replace(self.path)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def bbox_iou(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> float:
    """Intersection-over-union for axis-aligned boxes ``(x, y, w, h)`` in image pixels."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax2, ay2 = ax + max(0, aw), ay + max(0, ah)
    bx2, by2 = bx + max(0, bw), by + max(0, bh)
    ix1 = max(ax, bx)
    iy1 = max(ay, by)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0, ix2 - ix1)
    ih = max(0, iy2 - iy1)
    inter = float(iw * ih)
    if inter <= 0.0:
        return 0.0
    area_a = float(max(0, aw) * max(0, ah))
    area_b = float(max(0, bw) * max(0, bh))
    union = area_a + area_b - inter
    if union <= 1e-9:
        return 0.0
    return inter / union
