"""DEF-010: --abort-on-mouse-move uses click target + arming (mocked Quartz)."""

from __future__ import annotations

from io import StringIO
import sys
from unittest.mock import MagicMock

import macos_mouse_click as mmc
from macos_mouse_click import ResolvedConfig


def test_abort_when_armed_then_cursor_leaves_target(monkeypatch) -> None:
    """Cursor near target arms; next sample far from target aborts before second click."""
    positions = [(98.0, 100.0), (0.0, 0.0)]

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
        x=100.0,
        y=100.0,
        count=5,
        delay=0.0,
        abort_on_mouse_move=True,
        mouse_move_threshold_px=15.0,
        mouse_arm_radius_px=50.0,
    )
    qz = MagicMock()
    rc = mmc.run_synthetic_loop(qz, 100.0, 100.0, 5, 0.0, cfg)
    assert rc == 130
    assert len(posted) == 1


def test_no_mouse_abort_when_cursor_never_near_target(monkeypatch) -> None:
    """Cursor stays far from click target: never arms, burst completes (terminal case)."""
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
        abort_on_mouse_move=True,
        mouse_move_threshold_px=20.0,
    )
    qz = MagicMock()
    rc = mmc.run_synthetic_loop(qz, 1000.0, 1000.0, 3, 0.0, cfg)
    assert rc == 0
    assert len(posted) == 3


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


def test_main_rejects_arm_radius_below_threshold() -> None:
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
                "30",
                "--mouse-arm-radius-px",
                "10",
                "--dry-run-after-start",
            ]
        )
    finally:
        sys.stderr = old_err
    assert rc == 2
    assert "arm" in err.getvalue().lower() or ">=" in err.getvalue()
