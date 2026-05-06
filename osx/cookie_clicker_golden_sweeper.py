#!/usr/bin/env python3
"""Poll for Cookie Clicker 'magic' (golden) cookies; emit coordinates per plan-015 §6.1.

Standalone or subprocess-callable. See docs/osx/plans/plan-015-cookie-clicker-golden-cookie-sweeper.md

Display captures: each ``--capture display`` poll runs macOS ``/usr/sbin/screencapture -x -t png`` to a PNG.
By default PNGs are kept under ``docs/osx/screenshots/golden-sweeper-captures/`` (relative to the repo root;
that directory is listed in the repo ``.gitignore`` — local captures only). Use ``--no-capture-save`` for
ephemeral temp files only.

When there is at least one hit, a **JSONL** sidecar is written next to the **raw** image basename
(``*.json``). For ``--capture display``, **raw** ``screencapture`` bytes stay in ``*.png``; a second file
``*-annotated.png`` holds boxes + confidence markup. For ``--input-image``, the input file is unchanged;
``*-annotated.png`` is written beside it when hits exist.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Optional Quartz mapping for --capture display (main display only).
try:
    import Quartz  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - guarded use
    Quartz = None  # type: ignore[misc, assignment]


def _reexec_with_project_venv() -> None:
    """Use osx/.venv Python automatically for direct script execution."""
    if os.environ.get("OSX_VENV_REEXEC") == "1":
        return
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(script_dir, ".venv", "bin", "python3")
    if not os.path.exists(venv_python):
        return
    if os.path.realpath(sys.prefix) == os.path.realpath(os.path.join(script_dir, ".venv")):
        return
    env = dict(os.environ)
    env["OSX_VENV_REEXEC"] = "1"
    os.execve(venv_python, [venv_python, os.path.abspath(__file__), *sys.argv[1:]], env)


_reexec_with_project_venv()


def default_capture_save_dir(script_dir: Path) -> Path:
    """Directory for retained ``screencapture`` PNGs (under repo ``docs/osx/screenshots/``)."""
    return script_dir.parent / "docs" / "osx" / "screenshots" / "golden-sweeper-captures"


try:
    import cv2  # type: ignore[import-not-found]
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Error: opencv-python is required.\n"
        "Setup recommended: make -C osx setup\n"
        "Or: python3 -m pip install opencv-python"
    ) from exc


@dataclass
class Hit:
    x: float
    y: float
    confidence: float
    bbox: Tuple[int, int, int, int]
    kind: str = "golden"


def _load_profile_cookie_image_px(
    path: Optional[str],
    img_w: int,
    img_h: int,
    *,
    map_from_global: bool,
) -> Optional[Tuple[float, float]]:
    """Return big-cookie center in **image pixel** space for exclusion, or None."""
    if not path:
        return None
    p = Path(path)
    if not p.is_file():
        raise SystemExit(f"Error: profile not found: {path}")
    with p.open(encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
    c = data.get("cookie") or {}
    if "x" not in c or "y" not in c:
        return None
    gx, gy = float(c["x"]), float(c["y"])
    det = data.get("detector") or {}
    if det.get("image_width") == img_w and det.get("image_height") == img_h:
        return gx, gy
    if map_from_global:
        return quartz_global_to_capture_px(gx, gy, img_w, img_h)
    return None


def capture_main_display_png(out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["/usr/sbin/screencapture", "-x", "-t", "png", str(out_path)],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        msg = (r.stderr or r.stdout or "").strip() or f"exit {r.returncode}"
        raise SystemExit(f"Error: screencapture failed: {msg}")


def quartz_global_to_capture_px(gx: float, gy: float, img_w: int, img_h: int) -> Tuple[float, float]:
    """Inverse of capture_px_to_quartz_global for main display (image pixels, top-left origin)."""
    if Quartz is None:
        raise SystemExit("Error: Quartz required for coordinate conversion.")
    disp = Quartz.CGMainDisplayID()
    bounds = Quartz.CGDisplayBounds(disp)
    pw = int(Quartz.CGDisplayPixelsWide(disp))
    ph = int(Quartz.CGDisplayPixelsHigh(disp))
    if pw <= 0 or ph <= 0:
        raise SystemExit("Error: CGDisplayPixelsWide/High returned non-positive size.")
    ox = float(bounds.origin.x)
    oy = float(bounds.origin.y)
    w_pt = float(bounds.size.width)
    h_pt = float(bounds.size.height)
    ix = (gx - ox) * (float(pw) / w_pt)
    iy_top = (oy + h_pt - gy) * (float(ph) / h_pt)
    # If capture bitmap size differs from display pixel size, scale into image indices.
    ix *= float(img_w) / float(pw)
    iy_top *= float(img_h) / float(ph)
    return ix, iy_top


def capture_px_to_quartz_global(ix: float, iy_top: float, img_w: int, img_h: int) -> Tuple[float, float]:
    """Map top-left-origin pixel (ix, iy_top) from main-display capture to Quartz global (points)."""
    if Quartz is None:
        raise SystemExit("Error: Quartz (pyobjc-framework-Quartz) required for --capture display coordinate mapping.")
    disp = Quartz.CGMainDisplayID()
    bounds = Quartz.CGDisplayBounds(disp)
    pw = int(Quartz.CGDisplayPixelsWide(disp))
    ph = int(Quartz.CGDisplayPixelsHigh(disp))
    if pw <= 0 or ph <= 0:
        raise SystemExit("Error: CGDisplayPixelsWide/High returned non-positive size.")
    ox = float(bounds.origin.x)
    oy = float(bounds.origin.y)
    w_pt = float(bounds.size.width)
    h_pt = float(bounds.size.height)
    # Map indices in captured bitmap (iw x ih) to display pixel space, then to points.
    ix_disp = ix * (float(pw) / float(max(1, img_w)))
    iy_disp = iy_top * (float(ph) / float(max(1, img_h)))
    sx = w_pt / float(pw)
    sy = h_pt / float(ph)
    gx = ox + ix_disp * sx
    gy = oy + h_pt - (iy_disp * sy)
    return gx, gy


def detect_magic_cookie_hits(
    bgr,
    *,
    exclude_xy: Optional[Tuple[float, float]] = None,
    exclude_radius: float = 140.0,
    min_area: int = 150,
    max_area: int = 7200,
    max_hits: int = 6,
    max_aspect: float = 2.35,
    min_extent: float = 0.50,
    min_solidity: float = 0.76,
    min_circularity: float = 0.38,
    min_side_px: int = 12,
    min_confidence: Optional[float] = None,
) -> List[Hit]:
    """HSV blob detector tuned for compact golden-ish blobs (heuristic v2).

    Corpus-driven filters (``docs/osx/golden-sweeper-corpus-INDEX.md``): drop tall
    gold UI strips and hollow bars using aspect ratio, extent, solidity, and
    circularity; keep at most ``max_hits`` candidates ranked by blob compactness.
    """
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    # Two golden-ish ranges (OpenCV H 0-180)
    lower1 = (12, 80, 140)
    upper1 = (35, 255, 255)
    lower2 = (0, 90, 140)
    upper2 = (11, 255, 255)
    m1 = cv2.inRange(hsv, lower1, upper1)
    m2 = cv2.inRange(hsv, lower2, upper2)
    mask = cv2.bitwise_or(m1, m2)
    mask = cv2.medianBlur(mask, 5)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    scored: List[Tuple[float, float, float, float, float, Tuple[int, int, int, int]]] = []
    ih, iw = bgr.shape[:2]
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue
        x, y, cw, ch = cv2.boundingRect(cnt)
        if max(cw, ch) > min(iw, ih) * 0.18:
            continue
        if min(cw, ch) < min_side_px:
            continue
        aspect = max(cw, ch) / max(1, min(cw, ch))
        if aspect > max_aspect:
            continue
        rect_a = float(cw * ch)
        extent = area / rect_a if rect_a > 1e-6 else 0.0
        if extent < min_extent:
            continue
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 1e-6 else 0.0
        if solidity < min_solidity:
            continue
        perim = cv2.arcLength(cnt, True)
        circularity = (4.0 * math.pi * area) / (perim * perim) if perim > 1e-6 else 0.0
        if circularity < min_circularity:
            continue
        cx = x + cw * 0.5
        cy = y + ch * 0.5
        if exclude_xy is not None:
            dx = cx - exclude_xy[0]
            dy = cy - exclude_xy[1]
            if math.hypot(dx, dy) < exclude_radius:
                continue
        rank = circularity * extent * solidity * math.sqrt(area)
        base_conf = min(0.95, 0.45 + min(area, 3000.0) / 6000.0)
        scored.append((rank, base_conf, cx, cy, (x, y, cw, ch)))
    scored.sort(key=lambda t: -t[0])
    top = scored[: max(0, max_hits)]
    if not top:
        return []
    best_rank = top[0][0]
    hits: List[Hit] = []
    for rank, base_conf, cx, cy, bbox in top:
        rel = rank / best_rank if best_rank > 1e-9 else 1.0
        conf = min(0.95, base_conf * (0.82 + 0.18 * min(1.0, rel)))
        hits.append(Hit(x=float(cx), y=float(cy), confidence=float(conf), bbox=bbox))
    hits.sort(key=lambda h: -h.confidence)
    if min_confidence is not None:
        hits = [h for h in hits if h.confidence >= float(min_confidence)]
    return hits


def _emit_text(h: Hit) -> str:
    return f"{h.x:.2f} {h.y:.2f} {h.confidence:.3f}"


def _emit_json(h: Hit, *, ts: str, frame_id: int, coord_space: str) -> str:
    obj = {
        "x": round(h.x, 3),
        "y": round(h.y, 3),
        "kind": h.kind,
        "ts": ts,
        "confidence": round(h.confidence, 4),
        "bbox": list(h.bbox),
        "frame_id": frame_id,
        "coord_space": coord_space,
    }
    return json.dumps(obj, separators=(",", ":"))


def _annotated_image_path(raw_path: Path) -> Path:
    """Sibling path ``{stem}-annotated{suffix}`` (e.g. ``foo.png`` → ``foo-annotated.png``)."""
    return raw_path.parent / f"{raw_path.stem}-annotated{raw_path.suffix}"


def _annotate_hits_on_bgr(bgr, hits: Sequence[Hit]):
    """Return a BGR copy with each hit: green bbox, centroid dot, confidence label."""
    vis = bgr.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX
    for h in hits:
        x, y, w, hgt = h.bbox
        x2, y2 = x + w, y + hgt
        cv2.rectangle(vis, (x, y), (x2, y2), (0, 220, 0), 2)
        cv2.circle(vis, (int(round(h.x)), int(round(h.y))), 5, (0, 0, 255), -1)
        label = f"{h.confidence:.2f}"
        scale = 0.55
        thickness = 2
        (tw, th), bl = cv2.getTextSize(label, font, scale, thickness)
        pad = 4
        tx = max(0, min(x, vis.shape[1] - tw - 2 * pad))
        ty_top = max(th + pad + 2, y - pad)
        cv2.rectangle(
            vis,
            (tx, ty_top - th - pad),
            (min(vis.shape[1] - 1, tx + tw + 2 * pad), min(vis.shape[0] - 1, ty_top + pad)),
            (0, 0, 0),
            -1,
        )
        cv2.putText(
            vis,
            label,
            (tx + pad, ty_top - pad // 2),
            font,
            scale,
            (0, 255, 255),
            thickness,
            cv2.LINE_AA,
        )
    return vis


def _write_overlay(bgr, hits: Sequence[Hit], path: Path) -> None:
    vis = _annotate_hits_on_bgr(bgr, hits)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), vis):
        raise SystemExit(f"Error: failed to write overlay: {path}")


def _click(script_dir: Path, gx: float, gy: float, yes: bool) -> None:
    clicker = script_dir / "macos_mouse_click.py"
    if not clicker.is_file():
        raise SystemExit(f"Error: macos_mouse_click.py not found: {clicker}")
    cmd = [
        sys.executable,
        str(clicker),
        "-x",
        str(gx),
        "-y",
        str(gy),
        "-n",
        "1",
        "-d",
        "0",
    ]
    if yes:
        cmd.append("-Y")
    r = subprocess.run(cmd, cwd=str(script_dir.parent))
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Detect magic (golden) cookies; emit coordinates (plan-015). "
        "Use --input-image for tests; --capture display for live Quartz-global coords."
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--input-image", help="Analyze this PNG/JPG (coordinates in image pixel space).")
    src.add_argument(
        "--capture",
        choices=("display",),
        help="Capture main display each poll via screencapture (coordinates mapped to Quartz global).",
    )
    p.add_argument("--profile", help="Profile JSON for big-cookie exclusion when dimensions match detector metadata.")
    p.add_argument("--exclude-radius", type=float, default=140.0, help="Exclusion radius around profile cookie (default 140).")
    p.add_argument(
        "--min-confidence",
        type=float,
        default=None,
        metavar="C",
        help="Drop detector hits with confidence below C (default: keep all).",
    )
    det = p.add_argument_group("detector overrides (default: built-in v2 constants)")
    det.add_argument("--det-min-area", type=int, default=None, metavar="N")
    det.add_argument("--det-max-area", type=int, default=None, metavar="N")
    det.add_argument("--det-max-hits", type=int, default=None, metavar="N")
    det.add_argument("--det-max-aspect", type=float, default=None, metavar="R")
    det.add_argument("--det-min-extent", type=float, default=None, metavar="R")
    det.add_argument("--det-min-solidity", type=float, default=None, metavar="R")
    det.add_argument("--det-min-circularity", type=float, default=None, metavar="R")
    det.add_argument("--det-min-side-px", type=int, default=None, metavar="N")
    p.add_argument("--poll-interval", type=float, default=0.75, help="Seconds between polls (default 0.75).")
    p.add_argument("--run-seconds", type=float, default=0.0, help="Stop after this many seconds (0 = ignore).")
    p.add_argument("--max-polls", type=int, default=0, help="Stop after this many polls (0 = ignore).")
    p.add_argument("--max-wall-seconds", type=float, default=0.0, help="Hard wall-clock limit (0 = ignore).")
    p.add_argument("--output", choices=("text", "json"), default="json", help="stdout coordinate format (plan-015 §6.1).")
    p.add_argument("--overlay-path", default="", help="If set, write annotated PNG each poll with hits.")
    p.add_argument("--coord-log", default="", help="Append JSONL hits to this file (in addition to stdout rules).")
    p.add_argument("--dry-run", action="store_true", help="Detect and emit coords only; do not click.")
    p.add_argument("-Y", "--yes", action="store_true", help="Pass -Y to macos_mouse_click.py when clicking.")
    p.add_argument("--verbose-polls", action="store_true", help="Log human lines to stderr when no hit.")
    p.add_argument(
        "--capture-save-dir",
        default="",
        metavar="DIR",
        help="Save each poll's raw screencapture PNG under DIR; on hits also writes *-annotated.png (default: docs/osx/screenshots/golden-sweeper-captures).",
    )
    p.add_argument(
        "--no-capture-save",
        action="store_true",
        help="Do not keep PNGs on disk; capture to a temp file and delete after each poll.",
    )
    ns = p.parse_args()
    if ns.capture == "display":
        if not (ns.max_polls > 0 or ns.run_seconds > 0 or ns.max_wall_seconds > 0):
            p.error("with --capture display, set one of --max-polls, --run-seconds, or --max-wall-seconds")
        if ns.no_capture_save and ns.capture_save_dir:
            p.error("do not combine --no-capture-save with --capture-save-dir")
    return ns


def build_detect_kwargs(
    args: argparse.Namespace,
    *,
    exclude_xy: Optional[Tuple[float, float]],
    exclude_radius: float,
) -> Dict[str, Any]:
    """Map argparse ``args`` (golden sweeper) to ``detect_magic_cookie_hits`` keyword args."""
    kw: Dict[str, Any] = {"exclude_xy": exclude_xy, "exclude_radius": float(exclude_radius)}
    if args.det_min_area is not None:
        kw["min_area"] = int(args.det_min_area)
    if args.det_max_area is not None:
        kw["max_area"] = int(args.det_max_area)
    if args.det_max_hits is not None:
        kw["max_hits"] = int(args.det_max_hits)
    if args.det_max_aspect is not None:
        kw["max_aspect"] = float(args.det_max_aspect)
    if args.det_min_extent is not None:
        kw["min_extent"] = float(args.det_min_extent)
    if args.det_min_solidity is not None:
        kw["min_solidity"] = float(args.det_min_solidity)
    if args.det_min_circularity is not None:
        kw["min_circularity"] = float(args.det_min_circularity)
    if args.det_min_side_px is not None:
        kw["min_side_px"] = int(args.det_min_side_px)
    if args.min_confidence is not None:
        kw["min_confidence"] = float(args.min_confidence)
    return kw


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    start = time.monotonic()
    polls = 0
    frame_id = 0
    tmp_png: Optional[Path] = None
    use_ephemeral_capture = args.capture == "display" and bool(args.no_capture_save)
    capture_save_dir: Optional[Path] = None
    if args.capture == "display" and not args.no_capture_save:
        raw = (args.capture_save_dir or "").strip()
        capture_save_dir = Path(raw).expanduser() if raw else default_capture_save_dir(script_dir)
        capture_save_dir.mkdir(parents=True, exist_ok=True)
        print(f"# capture-save-dir: {capture_save_dir.resolve()}", file=sys.stderr, flush=True)
    if use_ephemeral_capture:
        tmp_png = Path(tempfile.mkdtemp(prefix="golden-sweeper-")) / "cap.png"

    coord_log_fp = open(args.coord_log, "a", encoding="utf-8") if args.coord_log else None

    try:
        while True:
            wall = time.monotonic() - start
            if args.max_wall_seconds and wall >= args.max_wall_seconds:
                break
            if args.run_seconds and wall >= args.run_seconds:
                break
            if args.max_polls and polls >= args.max_polls:
                break

            cap_path: Optional[Path] = None
            img_path: Optional[Path] = None
            if args.input_image:
                img_path = Path(args.input_image)
                bgr = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
                if bgr is None:
                    raise SystemExit(f"Error: unable to read image: {img_path}")
                coord_space = "image_pixels"
                map_to_global = False
            else:
                if use_ephemeral_capture:
                    assert tmp_png is not None
                    cap_path = tmp_png
                else:
                    assert capture_save_dir is not None
                    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S-%f")
                    cap_path = capture_save_dir / f"golden-sweeper-{stamp}-f{frame_id:05d}.png"
                capture_main_display_png(cap_path)
                bgr = cv2.imread(str(cap_path), cv2.IMREAD_COLOR)
                if bgr is None:
                    raise SystemExit("Error: screencapture wrote unreadable PNG.")
                coord_space = "quartz_global"
                map_to_global = True

            ih, iw = bgr.shape[:2]
            exclude = _load_profile_cookie_image_px(
                args.profile,
                iw,
                ih,
                map_from_global=bool(map_to_global),
            )
            det_kw = build_detect_kwargs(args, exclude_xy=exclude, exclude_radius=float(args.exclude_radius))
            hits_img = detect_magic_cookie_hits(bgr, **det_kw)
            polls += 1
            frame_id += 1

            if hits_img:
                vis = _annotate_hits_on_bgr(bgr, hits_img)
                if cap_path is not None:
                    ann_path = _annotated_image_path(cap_path)
                    if not cv2.imwrite(str(ann_path), vis):
                        raise SystemExit(f"Error: failed to write annotated capture: {ann_path}")
                    print(f"# annotated: {ann_path.resolve()}", file=sys.stderr, flush=True)
                elif img_path is not None:
                    ann_path = _annotated_image_path(img_path)
                    if not cv2.imwrite(str(ann_path), vis):
                        raise SystemExit(f"Error: failed to write annotated image: {ann_path}")
                    print(f"# annotated: {ann_path.resolve()}", file=sys.stderr, flush=True)

            hits_out: List[Hit] = []
            for h in hits_img:
                if map_to_global:
                    gx, gy = capture_px_to_quartz_global(h.x, h.y, iw, ih)
                    hits_out.append(
                        Hit(x=gx, y=gy, confidence=h.confidence, bbox=h.bbox, kind=h.kind)
                    )
                else:
                    hits_out.append(h)

            ts = datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")

            if args.overlay_path and hits_out:
                _write_overlay(bgr, hits_img, Path(args.overlay_path))

            jsonl_lines = [
                _emit_json(h, ts=ts, frame_id=frame_id, coord_space=coord_space) for h in hits_out
            ]
            for h, jline in zip(hits_out, jsonl_lines):
                if args.output == "text":
                    line = _emit_text(h)
                    print(line, flush=True)
                else:
                    line = jline
                    print(line, flush=True)
                if coord_log_fp:
                    coord_log_fp.write(line + "\n")
                    coord_log_fp.flush()

            sidecar_src = img_path if img_path is not None else cap_path
            if jsonl_lines and sidecar_src is not None:
                json_path = sidecar_src.with_suffix(".json")
                json_path.write_text("\n".join(jsonl_lines) + "\n", encoding="utf-8")

            if args.overlay_path:
                # plan-015: overlay mode still emit coords — already to stdout; mirror to stderr human hint
                if hits_out:
                    print(f"# overlay written: {args.overlay_path}", file=sys.stderr, flush=True)

            if hits_out and not args.dry_run and map_to_global:
                for h in hits_out:
                    _click(script_dir, h.x, h.y, args.yes)
            elif hits_out and not args.dry_run and not map_to_global:
                print(
                    "# warning: clicks require quartz_global coords; use --capture display for live clicks",
                    file=sys.stderr,
                    flush=True,
                )

            if not hits_out and args.verbose_polls:
                print(f"# poll {polls} no hit ({coord_space})", file=sys.stderr, flush=True)

            if args.input_image:
                break

            time.sleep(max(0.05, float(args.poll_interval)))
    finally:
        if coord_log_fp:
            coord_log_fp.close()
        if use_ephemeral_capture and tmp_png is not None and tmp_png.parent.is_dir():
            try:
                for c in tmp_png.parent.glob("*"):
                    c.unlink(missing_ok=True)
                tmp_png.parent.rmdir()
            except OSError:
                pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
