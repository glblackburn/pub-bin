"""Parse MACOS_MOUSE_CLICK_DRY_RUN_JSON line from merged PTY output.

**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).
"""

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
