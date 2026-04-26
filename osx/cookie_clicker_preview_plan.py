#!/usr/bin/env python3
"""Render a click preview from a Cookie Clicker coordinate profile.

This script never performs real clicks; it only creates preview artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from typing import Dict, List


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


_reexec_with_project_venv()

try:
    import cv2  # type: ignore[import-not-found]
except ImportError as exc:  # pragma: no cover - import guard
    raise SystemExit(
        "Error: opencv-python is required.\n"
        "Setup recommended: make -C osx setup\n"
        "Or install directly: python3 -m pip install opencv-python"
    ) from exc


LADDER_ORDER = [
    "time_machine",
    "portal",
    "alchemy_lab",
    "shipment",
    "wizard_tower",
    "temple",
    "bank",
    "factory",
    "mine",
    "farm",
    "grandma",
    "cursor",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate annotated preview artifacts for planned click coordinates."
    )
    p.add_argument("--profile", required=True, help="Profile JSON file.")
    p.add_argument("--output-dir", default="", help="Directory for generated files.")
    p.add_argument("--image-out", default="", help="Optional explicit PNG output path.")
    p.add_argument("--manifest-out", default="", help="Optional explicit manifest JSON path.")
    p.add_argument("--cookie-clicks", type=int, default=3000)
    p.add_argument("--ladder-clicks", type=int, default=5)
    p.add_argument("--skip-ladder", action="store_true")
    p.add_argument("--source-image", default="", help="Override source image path.")
    return p.parse_args()


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _build_targets(profile: Dict, skip_ladder: bool, ladder_clicks: int, cookie_clicks: int):
    rows = {row["name"]: row for row in profile.get("ladder_rows", [])}
    targets: List[Dict] = []
    if not skip_ladder:
        for idx, name in enumerate(LADDER_ORDER, start=1):
            row = rows.get(name)
            if row is None:
                continue
            targets.append(
                {
                    "id": idx,
                    "phase": "ladder",
                    "name": name,
                    "x": float(row["x"]),
                    "y": float(row["y"]),
                    "click_count": int(ladder_clicks),
                }
            )

    targets.append(
        {
            "id": len(targets) + 1,
            "phase": "cookie_burst",
            "name": "cookie_center",
            "x": float(profile["cookie"]["x"]),
            "y": float(profile["cookie"]["y"]),
            "click_count": int(cookie_clicks),
        }
    )
    return targets


def _label(target: Dict) -> str:
    return f'{target["id"]}:{target["name"]} x{target["click_count"]}'


def _draw_preview(img, targets: List[Dict]):
    for target in targets:
        x = int(round(target["x"]))
        y = int(round(target["y"]))
        color = (50, 220, 255) if target["phase"] == "cookie_burst" else (50, 160, 50)
        cv2.circle(img, (x, y), 12, color, 2)
        cv2.drawMarker(img, (x, y), color, markerType=cv2.MARKER_CROSS, markerSize=18, thickness=2)
        cv2.putText(
            img,
            _label(target),
            (x + 10, max(20, y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            1,
            cv2.LINE_AA,
        )
    return img


def _default_output_dir(profile_path: str) -> str:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(
        repo_root, "docs", "osx", "screenshots", "cookie-clicker", "previews"
    )


def main() -> int:
    args = parse_args()
    with open(args.profile, "r", encoding="utf-8") as f:
        profile = json.load(f)

    source_image = args.source_image or profile.get("source_image", "")
    if not source_image:
        raise SystemExit("Error: profile is missing source_image and --source-image not provided.")
    source_image = os.path.abspath(source_image)

    img = cv2.imread(source_image, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"Error: unable to load source image: {source_image}")

    targets = _build_targets(profile, args.skip_ladder, args.ladder_clicks, args.cookie_clicks)
    annotated = _draw_preview(img.copy(), targets)

    out_dir = args.output_dir or _default_output_dir(args.profile)
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    image_out = args.image_out or os.path.join(out_dir, f"{ts}-click-preview.png")
    manifest_out = args.manifest_out or os.path.join(out_dir, f"{ts}-click-preview.json")

    options_payload = {
        "skip_ladder": bool(args.skip_ladder),
        "cookie_clicks": int(args.cookie_clicks),
        "ladder_clicks": int(args.ladder_clicks),
    }
    options_hash = hashlib.sha256(
        json.dumps(options_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()
    profile_hash = _sha256(args.profile)

    manifest = {
        "profile_path": os.path.abspath(args.profile),
        "profile_hash": profile_hash,
        "source_image": source_image,
        "preview_image": os.path.abspath(image_out),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "options": options_payload,
        "options_hash": options_hash,
        "targets": targets,
        "warnings": profile.get("warnings", []),
    }

    cv2.imwrite(image_out, annotated)
    with open(manifest_out, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=False)
        f.write("\n")

    print(
        json.dumps(
            {
                "preview_image": os.path.abspath(image_out),
                "manifest": os.path.abspath(manifest_out),
                "target_count": len(targets),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
