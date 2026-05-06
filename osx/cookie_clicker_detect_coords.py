#!/usr/bin/env python3
"""Detect Cookie Clicker click coordinates from a screenshot.

Outputs a profile JSON used by the looper and preview scripts.
This tool never posts clicks.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple


def _reexec_with_project_venv() -> None:
    """Use osx/.venv Python automatically for direct script execution."""
    if os.environ.get("OSX_VENV_REEXEC") == "1":
        return
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(script_dir, ".venv")
    venv_python = os.path.join(script_dir, ".venv", "bin", "python3")
    if not os.path.exists(venv_python):
        return
    if os.path.realpath(sys.prefix) == os.path.realpath(venv_dir):
        return
    env = dict(os.environ)
    env["OSX_VENV_REEXEC"] = "1"
    os.execve(venv_python, [venv_python, os.path.abspath(__file__), *sys.argv[1:]], env)


if __name__ == "__main__":
    _reexec_with_project_venv()

try:
    import cv2  # type: ignore[import-not-found]
except ImportError as exc:  # pragma: no cover - import guard
    raise SystemExit(
        "Error: opencv-python is required.\n"
        "Setup recommended: make -C osx setup\n"
        "Or install directly: python3 -m pip install opencv-python"
    ) from exc


VISIBLE_STORE_ORDER = [
    "cursor",
    "grandma",
    "farm",
    "mine",
    "factory",
    "bank",
    "temple",
    "wizard_tower",
    "shipment",
    "alchemy_lab",
    "portal",
    "time_machine",
]

LADDER_EXECUTION_ORDER = list(reversed(VISIBLE_STORE_ORDER))


@dataclass
class DetectionResult:
    profile: Dict
    warnings: List[str]
    min_confidence: float


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Detect cookie/store coordinates from a Cookie Clicker screenshot."
    )
    p.add_argument("--input", required=True, help="Path to screenshot image (png/jpg).")
    p.add_argument(
        "--profile",
        default="auto",
        help="Profile name to persist (default: auto timestamp).",
    )
    p.add_argument(
        "--output",
        default="",
        help="Output JSON path; default: osx/config/cookie_clicker_profiles/<profile>.json",
    )
    p.add_argument(
        "--min-confidence",
        type=float,
        default=0.55,
        help="Minimum confidence threshold for fail-closed behavior (default: 0.55).",
    )
    return p.parse_args()


def _timestamp_name() -> str:
    return datetime.now().strftime("detected-%Y%m%d-%H%M%S")


def _smooth(values: List[float], radius: int = 4) -> List[float]:
    if radius <= 0:
        return list(values)
    out: List[float] = []
    n = len(values)
    for i in range(n):
        lo = max(0, i - radius)
        hi = min(n, i + radius + 1)
        out.append(sum(values[lo:hi]) / max(1, (hi - lo)))
    return out


def detect_cookie_center(gray) -> Tuple[float, float, float]:
    h, w = gray.shape
    roi = gray[:, : int(w * 0.6)]
    blurred = cv2.GaussianBlur(roi, (9, 9), 2.2)
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=max(40, int(h * 0.12)),
        param1=100,
        param2=35,
        minRadius=max(35, int(min(h, w) * 0.06)),
        maxRadius=max(100, int(min(h, w) * 0.26)),
    )
    if circles is not None and len(circles[0]) > 0:
        c = max(circles[0], key=lambda item: item[2])
        return float(c[0]), float(c[1]), 0.9

    # Fallback location for the large cookie region.
    return float(w * 0.20), float(h * 0.40), 0.35


def detect_store_panel(gray) -> Tuple[int, int, int, int, float]:
    h, w = gray.shape
    edges = cv2.Canny(gray, 75, 160)
    col_energy = edges.sum(axis=0).astype(float).tolist()
    col_s = _smooth(col_energy, radius=8)
    right_start = int(w * 0.52)
    right_slice = col_s[right_start:]
    if not right_slice:
        return int(w * 0.70), w - 1, int(h * 0.10), int(h * 0.95), 0.3

    peak_off = max(range(len(right_slice)), key=lambda i: right_slice[i])
    peak_x = right_start + peak_off
    panel_w = int(w * 0.29)
    panel_left = max(int(w * 0.55), peak_x - int(panel_w * 0.35))
    panel_right = min(w - 2, panel_left + panel_w)
    panel_top = int(h * 0.11)
    panel_bottom = int(h * 0.95)

    baseline = sum(col_s) / max(1.0, float(len(col_s)))
    peak_val = right_slice[peak_off]
    confidence = min(0.95, max(0.3, peak_val / max(1.0, baseline * 6.0)))
    return panel_left, panel_right, panel_top, panel_bottom, float(confidence)


def detect_row_spacing(gray, panel_left: int, panel_right: int, panel_top: int, panel_bottom: int):
    panel = gray[panel_top:panel_bottom, panel_left:panel_right]
    edges = cv2.Canny(panel, 75, 160)
    row_energy = edges.sum(axis=1).astype(float).tolist()
    row_s = _smooth(row_energy, radius=3)
    if not row_s:
        return int(panel_top + 40), 64.0, 0.2

    threshold = max(row_s) * 0.55
    peaks: List[int] = []
    for i in range(1, len(row_s) - 1):
        if row_s[i] > threshold and row_s[i] >= row_s[i - 1] and row_s[i] >= row_s[i + 1]:
            peaks.append(i)

    if len(peaks) < 3:
        return int(panel_top + 40), 64.0, 0.35

    filtered = []
    for i in range(1, len(peaks)):
        d = peaks[i] - peaks[i - 1]
        if 28 <= d <= 120:
            filtered.append(d)
    if not filtered:
        spacing = 64.0
        conf = 0.4
    else:
        filtered.sort()
        spacing = float(filtered[len(filtered) // 2])
        conf = min(0.95, 0.45 + min(0.45, len(filtered) / 20.0))

    first_row_rel = peaks[0]
    first_row_abs = int(panel_top + first_row_rel + spacing * 0.5)
    return first_row_abs, spacing, conf


def build_profile(args: argparse.Namespace) -> DetectionResult:
    img = cv2.imread(args.input, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"Error: unable to read image: {args.input}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    warnings: List[str] = []

    cookie_x, cookie_y, cookie_conf = detect_cookie_center(gray)
    if cookie_conf < args.min_confidence:
        warnings.append(
            f"Cookie confidence {cookie_conf:.2f} below threshold {args.min_confidence:.2f}."
        )

    panel_left, panel_right, panel_top, panel_bottom, store_conf = detect_store_panel(gray)
    if store_conf < args.min_confidence:
        warnings.append(
            f"Store panel confidence {store_conf:.2f} below threshold {args.min_confidence:.2f}."
        )

    first_row_y, row_spacing, spacing_conf = detect_row_spacing(
        gray, panel_left, panel_right, panel_top, panel_bottom
    )
    if spacing_conf < args.min_confidence:
        warnings.append(
            f"Row-spacing confidence {spacing_conf:.2f} below threshold {args.min_confidence:.2f}."
        )

    store_x = float(panel_left + int((panel_right - panel_left) * 0.30))
    visible_rows: Dict[str, float] = {}
    for idx, name in enumerate(VISIBLE_STORE_ORDER):
        visible_rows[name] = float(first_row_y + idx * row_spacing)

    ladder_rows = []
    row_conf = min(store_conf, spacing_conf)
    for name in LADDER_EXECUTION_ORDER:
        ladder_rows.append(
            {
                "name": name,
                "x": round(store_x, 3),
                "y": round(visible_rows[name], 3),
                "confidence": round(float(row_conf), 3),
            }
        )

    profile_name = args.profile if args.profile != "auto" else _timestamp_name()
    profile = {
        "profile_name": profile_name,
        "source_image": os.path.abspath(args.input),
        "detected_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "detector": {
            "method": "opencv_heuristic_v1",
            "min_confidence": args.min_confidence,
            "image_width": w,
            "image_height": h,
        },
        "cookie": {
            "x": round(cookie_x, 3),
            "y": round(cookie_y, 3),
            "confidence": round(cookie_conf, 3),
        },
        "store": {
            "x": round(store_x, 3),
            "panel_top": round(float(panel_top), 3),
            "panel_bottom": round(float(panel_bottom), 3),
            "row_spacing": round(float(row_spacing), 3),
            "confidence": round(min(store_conf, spacing_conf), 3),
            "panel_left": round(float(panel_left), 3),
            "panel_right": round(float(panel_right), 3),
            "first_row_y": round(float(first_row_y), 3),
        },
        "ladder_rows": ladder_rows,
        "preview_defaults": {
            "cookie_click_count": 3000,
            "ladder_click_count": 5,
            "cycle_sleep_seconds": 30,
        },
        "warnings": warnings,
    }
    return DetectionResult(profile=profile, warnings=warnings, min_confidence=args.min_confidence)


def default_output_path(profile_name: str) -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(
        script_dir, "config", "cookie_clicker_profiles", f"{profile_name}.json"
    )


def main() -> int:
    args = parse_args()
    result = build_profile(args)
    out_path = args.output or default_output_path(result.profile["profile_name"])
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result.profile, f, indent=2, sort_keys=False)
        f.write("\n")

    status = "ok"
    if result.warnings:
        status = "warning"
    print(
        json.dumps(
            {
                "status": status,
                "output": os.path.abspath(out_path),
                "warnings": result.warnings,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
