#!/usr/bin/env python3
"""Offline eval: human labels (plan-016 JSONL) vs ``detect_magic_cookie_hits`` (plan-017 / plan-018).

Loads each labeled frame, runs the detector, reports IoU / recall@K on positives and
false positives on negatives. Optional debug PNGs: detector overlay (green) plus
ground-truth box in magenta.

Example::

    ./osx/.venv/bin/python3 tools/eval_magic_cookie_labels.py \\
      --labels docs/osx/screenshots/golden-sweeper-captures/magic-cookie-labels.jsonl

With profile big-cookie exclusion (when capture size matches profile ``detector`` metadata)::

    ./osx/.venv/bin/python3 tools/eval_magic_cookie_labels.py --labels PATH.jsonl \\
      --profile osx/config/cookie_clicker_profile.defaults.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]


def _parse_crop(s: str) -> Tuple[int, int, int, int]:
    parts = [p.strip() for p in s.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("crop must be x,y,w,h")
    return (int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))


def _resolve_image_path(image_path: str, labels_file: Path) -> Path:
    p = Path(image_path).expanduser()
    if p.is_file():
        return p
    cand = labels_file.parent / p.name
    if cand.is_file():
        return cand
    cand2 = REPO_ROOT / "docs" / "osx" / "screenshots" / "golden-sweeper-captures" / p.name
    if cand2.is_file():
        return cand2
    return p


def _apply_crop(bgr: Any, crop: Optional[Tuple[int, int, int, int]]) -> Any:
    import cv2  # noqa: PLC0415

    if crop is None:
        return bgr
    x, y, w, h = crop
    h0, w0 = bgr.shape[:2]
    x = max(0, min(x, w0 - 1))
    y = max(0, min(y, h0 - 1))
    x2 = max(x + 1, min(x + w, w0))
    y2 = max(y + 1, min(y + h, h0))
    return bgr[y:y2, x:x2].copy()


def _shift_bbox(bbox: Tuple[int, int, int, int], crop: Optional[Tuple[int, int, int, int]]) -> Tuple[int, int, int, int]:
    if crop is None:
        return bbox
    cx, cy, _, _ = crop
    x, y, w, h = bbox
    return (x - cx, y - cy, w, h)


def _annotate_gt_magenta(bgr: Any, bbox: Tuple[int, int, int, int]) -> None:
    import cv2  # noqa: PLC0415

    x, y, w, h = bbox
    cv2.rectangle(bgr, (x, y), (x + w, y + h), (255, 0, 255), 2)


def _add_detector_args(p: argparse.ArgumentParser) -> None:
    g = p.add_argument_group("detector overrides (same semantics as golden sweeper)")
    g.add_argument("--det-min-area", type=int, default=None, metavar="N")
    g.add_argument("--det-max-area", type=int, default=None, metavar="N")
    g.add_argument("--det-max-hits", type=int, default=None, metavar="N")
    g.add_argument("--det-max-aspect", type=float, default=None, metavar="R")
    g.add_argument("--det-min-extent", type=float, default=None, metavar="R")
    g.add_argument("--det-min-solidity", type=float, default=None, metavar="R")
    g.add_argument("--det-min-circularity", type=float, default=None, metavar="R")
    g.add_argument("--det-min-side-px", type=int, default=None, metavar="N")
    g.add_argument(
        "--min-confidence",
        type=float,
        default=None,
        metavar="C",
        help="Passed through to detect_magic_cookie_hits (filter weak hits).",
    )


def _detect_kwargs(ns: argparse.Namespace, *, exclude_xy: Optional[Tuple[float, float]], exclude_radius: float) -> Dict[str, Any]:
    kw: Dict[str, Any] = {"exclude_xy": exclude_xy, "exclude_radius": float(exclude_radius)}
    if ns.det_min_area is not None:
        kw["min_area"] = int(ns.det_min_area)
    if ns.det_max_area is not None:
        kw["max_area"] = int(ns.det_max_area)
    if ns.det_max_hits is not None:
        kw["max_hits"] = int(ns.det_max_hits)
    if ns.det_max_aspect is not None:
        kw["max_aspect"] = float(ns.det_max_aspect)
    if ns.det_min_extent is not None:
        kw["min_extent"] = float(ns.det_min_extent)
    if ns.det_min_solidity is not None:
        kw["min_solidity"] = float(ns.det_min_solidity)
    if ns.det_min_circularity is not None:
        kw["min_circularity"] = float(ns.det_min_circularity)
    if ns.det_min_side_px is not None:
        kw["min_side_px"] = int(ns.det_min_side_px)
    if ns.min_confidence is not None:
        kw["min_confidence"] = float(ns.min_confidence)
    return kw


def main() -> int:
    sys.path.insert(0, str(REPO_ROOT / "osx"))
    import cv2  # noqa: PLC0415

    from cookie_clicker_golden_sweeper import (  # noqa: PLC0415
        _annotate_hits_on_bgr,
        _load_profile_cookie_image_px,
        detect_magic_cookie_hits,
    )
    from magic_cookie_labels import LabelStore, bbox_iou  # noqa: PLC0415

    default_labels = (
        REPO_ROOT / "docs" / "osx" / "screenshots" / "golden-sweeper-captures" / "magic-cookie-labels.jsonl"
    )
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument(
        "--labels",
        type=Path,
        default=default_labels,
        help=f"JSONL label file (default: {default_labels})",
    )
    p.add_argument("--profile", type=Path, default=None, help="Profile JSON for big-cookie exclusion (optional).")
    p.add_argument("--exclude-radius", type=float, default=140.0)
    p.add_argument(
        "--no-exclude",
        action="store_true",
        help="Do not pass big-cookie exclusion to the detector.",
    )
    p.add_argument("--iou-threshold", type=float, default=0.4, help="IoU threshold for recall@K (default 0.4).")
    p.add_argument("--top-k", type=int, default=6, metavar="K", help="Top detector hits to check vs GT (default 6).")
    p.add_argument(
        "--fp-min-confidence",
        type=float,
        default=None,
        metavar="C",
        help="On negatives, count as FP only if some hit has confidence >= C (default: any hit is FP).",
    )
    p.add_argument(
        "--crop",
        type=_parse_crop,
        default=None,
        metavar="x,y,w,h",
        help="Crop each frame to this rect before detect (image pixels). Implies no profile exclusion.",
    )
    p.add_argument("--write-debug-dir", type=Path, default=None, help="Write overlay PNGs (detector + GT magenta).")
    _add_detector_args(p)
    ns = p.parse_args()
    labels_path = ns.labels.expanduser()
    if not labels_path.is_file():
        print(f"Error: labels file not found: {labels_path}", file=sys.stderr)
        return 1

    store = LabelStore(labels_path)
    store.load()
    records = store.all_records()

    n_pos = n_neg = n_skip = 0
    fn = 0
    fp = 0
    pos_ious: List[float] = []
    missing_images: List[str] = []
    worst_fn: List[Tuple[float, str]] = []
    worst_fp: List[Tuple[float, str]] = []
    warned_crop_profile = False

    if ns.write_debug_dir is not None:
        ns.write_debug_dir.mkdir(parents=True, exist_ok=True)

    for rec in records:
        if rec.magic_cookie is None:
            n_skip += 1
            continue
        img_path = _resolve_image_path(rec.image_path, labels_path)
        if not img_path.is_file():
            missing_images.append(str(img_path))
            continue

        bgr = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
        if bgr is None:
            missing_images.append(str(img_path))
            continue

        crop: Optional[Tuple[int, int, int, int]] = ns.crop
        bgr_eval = _apply_crop(bgr, crop)
        ih, iw = bgr_eval.shape[:2]

        exclude: Optional[Tuple[float, float]] = None
        if (
            not warned_crop_profile
            and crop is not None
            and ns.profile is not None
            and not ns.no_exclude
        ):
            print(
                "# warning: --crop disables big-cookie exclusion (profile mapping is for full-frame captures).",
                file=sys.stderr,
            )
            warned_crop_profile = True
        if crop is None and not ns.no_exclude and ns.profile is not None:
            exclude = _load_profile_cookie_image_px(
                str(ns.profile.expanduser()),
                iw,
                ih,
                map_from_global=True,
            )

        det_kw = _detect_kwargs(ns, exclude_xy=exclude, exclude_radius=float(ns.exclude_radius))
        hits = detect_magic_cookie_hits(bgr_eval, **det_kw)

        stem = img_path.stem
        if rec.magic_cookie is True:
            n_pos += 1
            assert rec.bbox_px is not None
            gt = _shift_bbox(
                (rec.bbox_px[0], rec.bbox_px[1], rec.bbox_px[2], rec.bbox_px[3]),
                crop,
            )
            best = 0.0
            for h in hits[: max(1, ns.top_k)]:
                best = max(best, bbox_iou(h.bbox, gt))
            pos_ious.append(best)
            ok = best >= float(ns.iou_threshold)
            if not ok:
                fn += 1
                worst_fn.append((best, str(img_path)))
            if ns.write_debug_dir is not None:
                vis = _annotate_hits_on_bgr(bgr_eval, hits)
                _annotate_gt_magenta(vis, gt)
                out = ns.write_debug_dir / f"{stem}-eval.png"
                cv2.imwrite(str(out), vis)
        else:
            n_neg += 1
            triggered = False
            if hits:
                if ns.fp_min_confidence is None:
                    triggered = True
                else:
                    triggered = any(h.confidence >= float(ns.fp_min_confidence) for h in hits)
            if triggered:
                fp += 1
                worst_conf = max((h.confidence for h in hits), default=0.0)
                worst_fp.append((worst_conf, str(img_path)))
            if ns.write_debug_dir is not None and hits:
                vis = _annotate_hits_on_bgr(bgr_eval, hits)
                out = ns.write_debug_dir / f"{stem}-eval.png"
                cv2.imwrite(str(out), vis)

    def _median(xs: List[float]) -> float:
        if not xs:
            return 0.0
        s = sorted(xs)
        m = len(s) // 2
        return float(s[m]) if len(s) % 2 else 0.5 * (s[m - 1] + s[m])

    recall_at_k = (n_pos - fn) / n_pos if n_pos else 0.0
    fp_rate = fp / n_neg if n_neg else 0.0

    print(
        json.dumps(
            {
                "labels": str(labels_path),
                "n_positives": n_pos,
                "n_negatives": n_neg,
                "n_skipped_null": n_skip,
                "false_negatives": fn,
                "false_positives": fp,
                "recall_at_k": round(recall_at_k, 4),
                "fp_rate_on_negatives": round(fp_rate, 4),
                "iou_threshold": float(ns.iou_threshold),
                "top_k": int(ns.top_k),
                "mean_best_iou_on_positives": round(sum(pos_ious) / len(pos_ious), 4) if pos_ious else None,
                "median_best_iou_on_positives": round(_median(pos_ious), 4) if pos_ious else None,
                "missing_or_unreadable_images": len(missing_images),
            },
            indent=2,
        )
    )
    if missing_images:
        print("\n# missing or unreadable (first 20):", file=sys.stderr)
        for m in missing_images[:20]:
            print(f"#   {m}", file=sys.stderr)

    worst_fn.sort(key=lambda t: t[0])
    worst_fp.sort(key=lambda t: -t[0])
    if worst_fn:
        print("\n# lowest IoU positives (up to 10):", file=sys.stderr)
        for iou, path in worst_fn[:10]:
            print(f"#   iou={iou:.4f}  {path}", file=sys.stderr)
    if worst_fp:
        print("\n# false-positive stems (up to 10, by max hit confidence):", file=sys.stderr)
        for conf, path in worst_fp[:10]:
            print(f"#   max_conf={conf:.4f}  {path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
