"""Parse MACOS_MOUSE_CLICK_DRY_RUN_JSON line from merged PTY output."""

from __future__ import annotations

import json


def parse_dry_run_json(text: str) -> dict:
    marker = "MACOS_MOUSE_CLICK_DRY_RUN_JSON "
    i = text.rfind(marker)
    if i >= 0:
        rest = text[i + len(marker) :]
        line = rest.splitlines()[0].strip()
        return json.loads(line)
    for raw in reversed(text.splitlines()):
        line = raw.strip()
        if line.startswith("{") and '"mode"' in line:
            return json.loads(line)
    raise AssertionError(
        "missing dry-run marker or JSON line (last 3000 chars):\n" + text[-3000:]
    )
