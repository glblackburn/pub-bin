#!/usr/bin/env python3
"""Detect Cookie Clicker click coordinates from a screenshot.

Outputs a profile JSON used by the looper and preview scripts.
This tool never posts clicks.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from statistics import median
from typing import Any, Dict, List, Optional, Tuple


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

try:
    import pytesseract  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional until pip install
    pytesseract = None  # type: ignore[misc, assignment]
else:  # pragma: no cover - exercised when dependency installed
    _TESSERACT_OUTPUT_DICT = pytesseract.Output.DICT


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

# Horizontal click position within the detected store [panel_left, panel_right].
# Cookie Clicker places **Buy** controls on the **right** side of the store column; ~0.30
# landed on icons / the game–store divider (see operator feedback). Bias toward the
# price-button strip (~0.80–0.85 of panel width from the left edge).
STORE_LADDER_CLICK_X_FRAC = 0.82

# English store labels (substring match, longest phrase wins per OCR line).
# Order here is only for tie-breaking; matching uses phrase length, not this list order.
_OCR_BUILDING_PHRASES: List[Tuple[str, str]] = sorted(
    [
        ("time_machine", "time machine"),
        ("alchemy_lab", "alchemy lab"),
        ("wizard_tower", "wizard tower"),
        ("shipment", "shipment"),
        ("factory", "factory"),
        ("grandma", "grandma"),
        ("temple", "temple"),
        ("cursor", "cursor"),
        ("portal", "portal"),
        ("farm", "farm"),
        ("mine", "mine"),
        ("bank", "bank"),
    ],
    key=lambda kv: len(kv[1]),
    reverse=True,
)

_OCR_MIN_ASSIGNED = 3  # partial OCR + interpolation still beats edge-only ladder when store is noisy

# OCR only the left part of the store band (building names); prices/icons on the right add junk digits.
_OCR_NAME_COLUMN_FRAC = 0.58

_OCR_PSM_CONFIGS = (
    "--oem 3 --psm 4",  # single column
    "--oem 3 --psm 6",  # uniform block
    "--oem 3 --psm 11",  # sparse text
)


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
    p.add_argument(
        "--no-ocr",
        action="store_true",
        help="Disable Tesseract OCR for store row Y (use edge-density heuristic only).",
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


def _tesseract_cli_available() -> bool:
    return shutil.which("tesseract") is not None


def _norm_ocr_line(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[\s|_]+", " ", s)
    return s.strip()


def _ocr_tokens(line_norm: str) -> List[str]:
    return [t for t in re.split(r"[^a-z0-9]+", line_norm) if len(t) >= 2]


def _is_price_like_token(txt: str) -> bool:
    s = txt.strip().replace(",", "")
    if s.isdigit() and len(s) >= 2:
        return True
    return bool(re.fullmatch(r"\$?\d+[.,]?\d*\s*[kmb]?", s, flags=re.IGNORECASE))


def _match_building_from_ocr_line(line_norm: str) -> Optional[str]:
    """Resolve building from one OCR line (normalized lowercase)."""
    tokens = _ocr_tokens(line_norm)
    ts = set(tokens)

    # Split OCR often breaks two-word building names across tokens.
    if "time" in ts and "machine" in ts:
        return "time_machine"
    if "wizard" in ts and "tower" in ts:
        return "wizard_tower"
    if "alchemy" in line_norm and "lab" in line_norm:
        return "alchemy_lab"

    best: Optional[str] = None
    best_len = 0
    for name, phrase in _OCR_BUILDING_PHRASES:
        if phrase in line_norm and len(phrase) > best_len:
            best = name
            best_len = len(phrase)
    if best is not None:
        return best

    # Single-token names (exact token); avoid short ambiguous words.
    single_map = {
        "cursor": "cursor",
        "grandma": "grandma",
        "farm": "farm",
        "mine": "mine",
        "factory": "factory",
        "bank": "bank",
        "temple": "temple",
        "shipment": "shipment",
        "portal": "portal",
    }
    for tok in sorted(ts, key=len, reverse=True):
        if len(tok) < 4:
            continue
        if tok in single_map:
            return single_map[tok]
    return None


def _cluster_word_boxes_into_lines(boxes: List[Dict[str, int]]) -> List[List[Dict[str, int]]]:
    if not boxes:
        return []
    boxes = sorted(boxes, key=lambda b: (b["top"], b["left"]))
    med_h = int(max(12, median([b["height"] for b in boxes])))
    thr = max(14, int(med_h * 0.65))
    lines: List[List[Dict[str, int]]] = []
    cur = [boxes[0]]
    line_top = boxes[0]["top"]
    for b in boxes[1:]:
        if abs(b["top"] - line_top) <= thr:
            cur.append(b)
            line_top = min(line_top, b["top"])
        else:
            lines.append(cur)
            cur = [b]
            line_top = b["top"]
    lines.append(cur)
    return lines


def detect_ladder_row_y_from_ocr(
    bgr,
    panel_left: int,
    panel_right: int,
    panel_top: int,
    panel_bottom: int,
) -> Tuple[Optional[Dict[str, Tuple[float, float]]], List[str], float]:
    """Map building internal name -> (center_y_px, word_conf_01). None if OCR not trusted."""
    warns: List[str] = []
    if pytesseract is None:
        warns.append("pytesseract not installed; ladder Y from edge heuristic.")
        return None, warns, 0.0
    if not _tesseract_cli_available():
        warns.append("tesseract executable not on PATH (e.g. brew install tesseract).")
        return None, warns, 0.0

    pad = 4
    x0 = max(0, panel_left - pad)
    y0 = max(0, panel_top - pad)
    panel_w = max(1, panel_right - panel_left)
    # Crop to building-name column (left side of store); reduces digit noise from prices.
    name_x1 = min(bgr.shape[1] - 1, panel_left + max(80, int(panel_w * _OCR_NAME_COLUMN_FRAC)))
    y1 = min(bgr.shape[0], panel_bottom + pad)
    crop = bgr[y0:y1, x0:name_x1].copy()
    if crop.size == 0:
        warns.append("OCR: empty store crop.")
        return None, warns, 0.0

    ch, cw = crop.shape[:2]
    scale = 2.5 if ch < 720 else 2.0 if ch < 900 else 1.5
    if scale > 1.0:
        crop = cv2.resize(crop, (int(cw * scale), int(ch * scale)), interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 5, 40, 40)
    rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

    def _parse_tesseract_data(data: Dict[str, Any], scale_val: float) -> List[Dict[str, int]]:
        out_local: List[Dict[str, int]] = []
        nloc = len(data.get("text", []))
        for i in range(nloc):
            txt = (data["text"][i] or "").strip()
            if not txt or len(txt) < 1:
                continue
            if _is_price_like_token(txt):
                continue
            try:
                conf_v = int(float(data["conf"][i]))
            except (TypeError, ValueError):
                conf_v = -1
            if conf_v < 0:
                continue
            if conf_v < 12:
                continue
            lx = int(int(data["left"][i]) / scale_val) + x0
            ly = int(int(data["top"][i]) / scale_val) + y0
            lw = max(1, int(int(data["width"][i]) / scale_val))
            lh = max(1, int(int(data["height"][i]) / scale_val))
            out_local.append({"text": txt, "left": lx, "top": ly, "width": lw, "height": lh, "conf": conf_v})
        return out_local

    raw_boxes: List[Dict[str, int]] = []
    try:
        for tess_cfg in _OCR_PSM_CONFIGS:
            data = pytesseract.image_to_data(
                rgb,
                output_type=_TESSERACT_OUTPUT_DICT,
                config=tess_cfg,
                lang="eng",
            )
            raw_boxes.extend(_parse_tesseract_data(data, scale))
    except Exception as exc:  # noqa: BLE001
        warns.append(f"OCR failed: {type(exc).__name__}: {exc}")
        return None, warns, 0.0

    # Dedupe: same text near same baseline keeps highest confidence.
    dedup: Dict[Tuple[str, int], Dict[str, int]] = {}
    for b in raw_boxes:
        key = (b["text"].lower().strip(), int(b["top"]) // 10)
        if key not in dedup or b["conf"] > dedup[key]["conf"]:
            dedup[key] = b
    boxes = sorted(dedup.values(), key=lambda b: (b["top"], b["left"]))

    if len(boxes) < 4:
        # Second pass: allow low-confidence words (game UI often < 30).
        raw2: List[Dict[str, int]] = []
        try:
            for tess_cfg in _OCR_PSM_CONFIGS:
                data = pytesseract.image_to_data(
                    rgb,
                    output_type=_TESSERACT_OUTPUT_DICT,
                    config=tess_cfg,
                    lang="eng",
                )
                nloc = len(data.get("text", []))
                for i in range(nloc):
                    txt = (data["text"][i] or "").strip()
                    if not txt or _is_price_like_token(txt):
                        continue
                    try:
                        conf_v = int(float(data["conf"][i]))
                    except (TypeError, ValueError):
                        conf_v = -1
                    if conf_v < 0 or len(txt) < 2:
                        continue
                    lx = int(int(data["left"][i]) / scale) + x0
                    ly = int(int(data["top"][i]) / scale) + y0
                    lw = max(1, int(int(data["width"][i]) / scale))
                    lh = max(1, int(int(data["height"][i]) / scale))
                    raw2.append({"text": txt, "left": lx, "top": ly, "width": lw, "height": lh, "conf": conf_v})
        except Exception:
            pass
        dedup2: Dict[Tuple[str, int], Dict[str, int]] = {}
        for b in list(dedup.values()) + raw2:
            key = (b["text"].lower().strip(), int(b["top"]) // 10)
            if key not in dedup2 or b["conf"] > dedup2[key]["conf"]:
                dedup2[key] = b
        boxes = sorted(dedup2.values(), key=lambda b: (b["top"], b["left"]))

    if len(boxes) < 3:
        warns.append(f"OCR: too few words in store name column ({len(boxes)}).")
        return None, warns, 0.0

    line_groups = _cluster_word_boxes_into_lines(boxes)
    assignments: Dict[str, Tuple[float, float]] = {}
    seen: set[str] = set()
    confs_used: List[float] = []

    def _line_center_y(group: List[Dict[str, int]]) -> float:
        return float(median([b["top"] + b["height"] / 2.0 for b in group]))

    for group in sorted(line_groups, key=_line_center_y):
        parts = [b["text"] for b in sorted(group, key=lambda x: x["left"])]
        line_norm = _norm_ocr_line(" ".join(parts))
        name = _match_building_from_ocr_line(line_norm)
        if name is None or name in seen:
            continue
        cy = _line_center_y(group)
        wc = float(median([float(b["conf"]) for b in group]))
        assignments[name] = (cy, wc / 100.0)
        confs_used.append(wc)
        seen.add(name)

    if len(assignments) < _OCR_MIN_ASSIGNED:
        warns.append(
            f"OCR: matched only {len(assignments)} store rows (need >= {_OCR_MIN_ASSIGNED}); "
            "using edge ladder."
        )
        return None, warns, 0.0

    avg_conf = sum(confs_used) / max(1, len(confs_used)) / 100.0
    return assignments, warns, float(avg_conf)


def interpolate_row_y_for_order(order: List[str], partial: Dict[str, float]) -> Dict[str, float]:
    """Linear fill using known Y anchors and uniform extrapolation beyond ends."""
    gaps: List[float] = []
    last_i: Optional[int] = None
    last_y: Optional[float] = None
    for i, n in enumerate(order):
        if n not in partial:
            continue
        y = float(partial[n])
        if last_i is not None and last_y is not None and i > last_i:
            gaps.append((y - last_y) / float(i - last_i))
        last_i, last_y = i, y
    step = float(median(gaps)) if gaps else 41.0

    out: Dict[str, float] = {}
    for i, name in enumerate(order):
        if name in partial:
            out[name] = float(partial[name])
            continue
        jp: Optional[int] = None
        yp: Optional[float] = None
        for j in range(i - 1, -1, -1):
            if order[j] in partial:
                jp, yp = j, float(partial[order[j]])
                break
        jy: Optional[int] = None
        yy: Optional[float] = None
        for j in range(i + 1, len(order)):
            if order[j] in partial:
                jy, yy = j, float(partial[order[j]])
                break
        if jp is not None and jy is not None and yp is not None and yy is not None:
            out[name] = yp + (yy - yp) * (i - jp) / float(jy - jp)
        elif jp is not None and yp is not None:
            out[name] = yp + step * (i - jp)
        elif jy is not None and yy is not None:
            out[name] = yy - step * (jy - i)
        else:
            out[name] = float(median(list(partial.values())))
    return out


def _first_row_and_spacing_from_visible(visible: Dict[str, float], order: List[str]) -> Tuple[float, float]:
    ys = [visible[n] for n in order if n in visible]
    if len(ys) < 2:
        return visible[order[0]], 41.0
    sp = float(median([ys[i + 1] - ys[i] for i in range(len(ys) - 1)]))
    return float(visible[order[0]]), sp


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

    panel_w = max(1, int(panel_right - panel_left))
    store_x = float(panel_left + int(panel_w * STORE_LADDER_CLICK_X_FRAC))

    ladder_rows_source = "edges"
    detector_method = "opencv_heuristic_v1"
    if args.no_ocr:
        ocr_assign, ocr_warns, ocr_word_conf = None, [], 0.0
    else:
        ocr_assign, ocr_warns, ocr_word_conf = detect_ladder_row_y_from_ocr(
            img, panel_left, panel_right, panel_top, panel_bottom
        )
    warnings.extend(ocr_warns)

    visible_rows: Dict[str, float] = {}
    if (
        not args.no_ocr
        and ocr_assign is not None
        and len(ocr_assign) >= _OCR_MIN_ASSIGNED
    ):
        partial_y = {k: v[0] for k, v in ocr_assign.items()}
        visible_rows = interpolate_row_y_for_order(VISIBLE_STORE_ORDER, partial_y)
        ladder_rows_source = "ocr"
        detector_method = "opencv_ocr_v1"
        first_row_y, row_spacing = _first_row_and_spacing_from_visible(
            visible_rows, VISIBLE_STORE_ORDER
        )
        row_conf = min(store_conf, spacing_conf, ocr_word_conf, 0.95)
        warnings.append(
            f"Store ladder Y from Tesseract OCR ({len(ocr_assign)} row labels matched; "
            "others interpolated along store order)."
        )
    else:
        for idx, name in enumerate(VISIBLE_STORE_ORDER):
            visible_rows[name] = float(first_row_y + idx * row_spacing)
        row_conf = min(store_conf, spacing_conf)

    ladder_rows = []
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
            "method": detector_method,
            "min_confidence": args.min_confidence,
            "image_width": w,
            "image_height": h,
            "ladder_rows_source": ladder_rows_source,
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
