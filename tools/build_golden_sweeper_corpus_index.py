#!/usr/bin/env python3
"""Build ``docs/osx/golden-sweeper-corpus-INDEX.md`` and ``*-v2-annotated.png`` previews.

Reads raw PNGs under ``docs/osx/screenshots/golden-sweeper-captures/`` (gitignored
except this workflow), runs ``detect_magic_cookie_hits`` from
``osx/cookie_clicker_golden_sweeper.py``, writes one v2 annotated image per raw
next to the source, and emits a Markdown index with relative links.

Usage (from repo root)::

    ./osx/.venv/bin/python3 tools/build_golden_sweeper_corpus_index.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CAP_DIR = REPO_ROOT / "docs" / "osx" / "screenshots" / "golden-sweeper-captures"
OUT_INDEX = REPO_ROOT / "docs" / "osx" / "golden-sweeper-corpus-INDEX.md"


def main() -> int:
    sys.path.insert(0, str(REPO_ROOT / "osx"))
    import cv2  # noqa: PLC0415

    from cookie_clicker_golden_sweeper import (  # noqa: PLC0415
        _annotate_hits_on_bgr,
        detect_magic_cookie_hits,
    )

    if not CAP_DIR.is_dir():
        print(f"skip: missing captures dir {CAP_DIR}", file=sys.stderr)
        return 0

    rows: list[tuple[str, int, int, str, str, str, str]] = []
    raw_paths = sorted(
        p
        for p in CAP_DIR.glob("golden-sweeper-*-f*.png")
        if "-annotated" not in p.name and "-v2-annotated" not in p.name
    )
    for raw in raw_paths:
        stem = raw.stem
        bgr = cv2.imread(str(raw))
        if bgr is None:
            continue
        hits = detect_magic_cookie_hits(bgr, exclude_xy=None)
        v2_path = raw.parent / f"{stem}-v2-annotated.png"
        if hits:
            vis = _annotate_hits_on_bgr(bgr, hits)
            cv2.imwrite(str(v2_path), vis)
        else:
            if v2_path.is_file():
                v2_path.unlink()
            v2_path = raw

        jpath = raw.with_suffix(".json")
        legacy_n = 0
        if jpath.is_file():
            legacy_n = sum(1 for ln in jpath.read_text(encoding="utf-8").splitlines() if ln.strip())
        v2_n = len(hits)
        if legacy_n >= 50:
            assess = "No verified golden; legacy run was UI-heavy false positives."
        elif v2_n <= 2 and legacy_n < 40:
            assess = "Sparse candidates — possible spawn (needs human check)."
        else:
            assess = "No verified golden; v2 lists top compact gold-like blobs only."

        rel_raw = f"screenshots/golden-sweeper-captures/{raw.name}"
        rel_json = f"screenshots/golden-sweeper-captures/{jpath.name}" if jpath.is_file() else ""
        rel_preview = f"screenshots/golden-sweeper-captures/{v2_path.name}"
        rows.append((stem, legacy_n, v2_n, assess, rel_raw, rel_json, rel_preview))

    lines = [
        "# Golden sweeper capture corpus (local)",
        "",
        "Raw PNGs, sidecar JSONL, and legacy ``*-annotated.png`` live under "
        "[`screenshots/golden-sweeper-captures/`](screenshots/golden-sweeper-captures/) "
        "(directory is **gitignored** — present only on machines that ran the sweeper).",
        "",
        "**Labeling:** None of these frames were operator-flagged as “golden visible.” "
        "Legacy sidecars often contained **dozens** of lines from gold-tinted UI (scroll strips, "
        "buff rows). **Detector v2** keeps compact, blob-shaped HSV regions and caps output "
        "(see ``detect_magic_cookie_hits`` in ``osx/cookie_clicker_golden_sweeper.py``). "
        "The **assessment** column is a **heuristic** for triage, not ground truth.",
        "",
        "Regenerate this file and ``*-v2-annotated.png`` after new captures:",
        "",
        "```bash",
        "./osx/.venv/bin/python3 tools/build_golden_sweeper_corpus_index.py",
        "```",
        "",
        "| # | stem | legacy JSON lines | v2 hits | assessment | raw | json |",
        "|---|------|-------------------|---------|------------|-----|------|",
    ]
    for i, (stem, legacy_n, v2_n, assess, rel_raw, rel_json, rel_preview) in enumerate(rows, start=1):
        jcell = f"[json]({rel_json})" if rel_json else "—"
        lines.append(
            f"| {i} | `{stem}` | {legacy_n} | {v2_n} | {assess} | "
            f"[raw]({rel_raw}) | {jcell} |"
        )
    lines.extend(["", "## v2 annotated previews", ""])
    for stem, legacy_n, v2_n, assess, rel_raw, rel_json, rel_preview in rows:
        lines.append(f"### `{stem}`")
        lines.append("")
        lines.append(
            f'<p><img src="{rel_preview}" width="560" alt="{stem} v2 annotated" /></p>'
        )
        lines.append("")

    OUT_INDEX.parent.mkdir(parents=True, exist_ok=True)
    OUT_INDEX.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT_INDEX} ({len(rows)} rows)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
