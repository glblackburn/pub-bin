"""DEF-014: golden sweeper runs once after all cookie phases in macos_mouse_click_loop.sh."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LOOP_SH = REPO_ROOT / "osx" / "macos_mouse_click_loop.sh"


def test_golden_sweeper_invoked_once_after_inner_while_done() -> None:
    txt = LOOP_SH.read_text(encoding="utf-8")
    assert txt.count('"${golden_sweeper}" --capture display') == 1
    bad = 'sleep "${CYCLE_SLEEP_SECONDS}"\n            "${golden_sweeper}"'
    assert bad not in txt, "sweeper must not follow inter-phase sleep inside i<k"
    assert '    done\n    "${golden_sweeper}" --capture display' in txt
