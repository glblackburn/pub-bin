"""Phase 1: --abort-on-mouse-move during synthetic loop (mocked Quartz)."""

from __future__ import annotations

from unittest.mock import MagicMock

import macos_mouse_click as mmc
from macos_mouse_click import ResolvedConfig


def test_mouse_move_abort_triggers_after_threshold(monkeypatch) -> None:
    """Second iteration sees cursor jump; loop exits 130 without posting second click."""
    positions = [(10.0, 10.0), (10.0, 10.0), (100.0, 10.0)]

    def fake_location(_qz: object) -> tuple:
        return positions.pop(0)

    monkeypatch.setattr(mmc, "get_mouse_location", fake_location)
    posted: list[tuple[float, float]] = []

    def fake_post(_qz: object, x: float, y: float) -> None:
        posted.append((x, y))

    monkeypatch.setattr(mmc, "post_synthetic_click", fake_post)
    mmc.reset_shutdown()
    cfg = ResolvedConfig(
        mode="fixed",
        x=1.0,
        y=2.0,
        count=5,
        delay=0.0,
        abort_on_mouse_move=True,
        mouse_move_threshold_px=15.0,
    )
    qz = MagicMock()
    rc = mmc.run_synthetic_loop(qz, 1.0, 2.0, 5, 0.0, cfg)
    assert rc == 130
    assert len(posted) == 1


def test_mouse_move_abort_disabled_allows_all_clicks(monkeypatch) -> None:
    monkeypatch.setattr(mmc, "get_mouse_location", lambda _qz: (0.0, 0.0))
    posted: list[int] = []

    def fake_post(_qz: object, _x: float, _y: float) -> None:
        posted.append(1)

    monkeypatch.setattr(mmc, "post_synthetic_click", fake_post)
    mmc.reset_shutdown()
    cfg = ResolvedConfig(
        mode="fixed",
        count=3,
        delay=0.0,
        abort_on_mouse_move=False,
    )
    qz = MagicMock()
    rc = mmc.run_synthetic_loop(qz, 0.0, 0.0, 3, 0.0, cfg)
    assert rc == 0
    assert len(posted) == 3


def test_main_rejects_abort_with_non_positive_threshold() -> None:
    import sys
    from io import StringIO

    err = StringIO()
    old_err = sys.stderr
    try:
        sys.stderr = err
        rc = mmc.main(
            [
                "-x",
                "1",
                "-y",
                "2",
                "-n",
                "2",
                "-d",
                "0",
                "-Y",
                "--abort-on-mouse-move",
                "--mouse-move-threshold-px",
                "0",
                "--dry-run-after-start",
            ]
        )
    finally:
        sys.stderr = old_err
    assert rc == 2
    assert "threshold" in err.getvalue().lower()
