"""Plan-021: AppKit overlay smoke test (darwin only).

Verifies ``show_target_overlay`` builds and tears down the floating window
without raising. We use a very short dwell (0.05s) so the test is fast and
non-interactive. No assertions about visible state — just that the AppKit
path is reachable and stable.
"""

from __future__ import annotations

import sys

import pytest

import macos_mouse_click as mmc

pytestmark = pytest.mark.darwin


def test_show_target_overlay_dwell_smoke() -> None:
    if sys.platform != "darwin":
        pytest.skip("AppKit overlay is darwin-only")
    pytest.importorskip("AppKit")
    # 0.05s is short enough to keep the suite fast and long enough for the
    # AppKit run loop to render at least one tick.
    mmc.show_target_overlay(
        x=10.0, y=10.0, count=5, dwell_seconds=0.05, step=False,
    )


def test_show_target_overlay_zero_dwell_returns_immediately() -> None:
    if sys.platform != "darwin":
        pytest.skip("AppKit overlay is darwin-only")
    pytest.importorskip("AppKit")
    mmc.show_target_overlay(
        x=20.0, y=30.0, count=0, dwell_seconds=0.0, step=False,
    )


def test_show_target_overlay_negative_dwell_clamped() -> None:
    if sys.platform != "darwin":
        pytest.skip("AppKit overlay is darwin-only")
    pytest.importorskip("AppKit")
    mmc.show_target_overlay(
        x=15.0, y=25.0, count=1, dwell_seconds=-1.0, step=False,
    )
