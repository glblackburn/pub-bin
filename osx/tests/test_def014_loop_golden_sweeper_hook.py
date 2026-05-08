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
    # Plan-021 wraps the sweeper call in a ``if [ "${TOUR_MODE}" != true ]`` guard
    # (tour mode skips the screen-capture sweeper), so the literal
    # ``done\n    "${golden_sweeper}"`` anchor no longer matches. Check the
    # semantic instead: the sweeper sits after the cookie-phase ``done`` and
    # NOT inside the inner ``while [ "${i}" -le "${k}" ]; do`` body.
    func_body = txt.split("function run_phased_cookie_bursts", 1)[1]
    inner_body, _, after_inner = func_body.partition("    done\n")
    assert '"${golden_sweeper}"' not in inner_body, (
        "sweeper must not run inside the cookie-phase loop body"
    )
    assert '"${golden_sweeper}" --capture display' in after_inner.split(
        "\nfunction ", 1
    )[0]
