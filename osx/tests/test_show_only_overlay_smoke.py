"""Plan-021: AppKit overlay tests.

Mix of platform-agnostic unit tests for the small, mockable helpers and
darwin-only smoke tests that drive the live AppKit ``NSWindow`` path.

The regression for DEF-015 (overlay using ``mainScreen`` height instead of
the primary display) is ``test_overlay_height_uses_primary_screen_not_main``
— it would FAIL on the buggy code that read ``NSScreen.mainScreen().frame()``
on a multi-monitor setup where the focused display is not the primary.
"""

from __future__ import annotations

import sys

import pytest

import macos_mouse_click as mmc


class _FakeFrameSize:
    def __init__(self, height: float) -> None:
        self.height = height


class _FakeFrame:
    def __init__(self, height: float) -> None:
        self.size = _FakeFrameSize(height)


class _FakeScreen:
    def __init__(self, height: float) -> None:
        self._height = height

    def frame(self) -> _FakeFrame:
        return _FakeFrame(self._height)


def _make_fake_appkit(primary_h: float, *other_heights: float, main_index: int = -1):
    """Return a fake AppKit module with controllable primary vs main screens.

    ``screens()`` returns ``[primary, *others]`` (primary is index 0 by AppKit
    convention). ``mainScreen()`` returns ``screens()[main_index]`` so tests
    can simulate the focused display being a non-primary screen (the exact
    multi-monitor situation DEF-015 was about).
    """
    screens = [_FakeScreen(primary_h), *(_FakeScreen(h) for h in other_heights)]

    class _NSScreen:
        @staticmethod
        def screens():
            return list(screens)

        @staticmethod
        def mainScreen():
            return screens[main_index]

    class _AppKit:
        NSScreen = _NSScreen

    return _AppKit


def test_overlay_primary_screen_height_returns_screens_zero() -> None:
    fake = _make_fake_appkit(1117.0, 2160.0, 1080.0)
    assert mmc._overlay_primary_screen_height(fake) == 1117.0


def test_overlay_primary_screen_height_returns_none_when_no_screens() -> None:
    class _NSScreen:
        @staticmethod
        def screens():
            return []

    class _AppKit:
        NSScreen = _NSScreen

    assert mmc._overlay_primary_screen_height(_AppKit) is None


def test_overlay_height_uses_primary_screen_not_main() -> None:
    """DEF-015 regression: reading ``mainScreen().frame()`` on a setup where
    the focused display is not the primary silently shifts the overlay by
    ``(primary_h - focused_h)`` pixels. The helper MUST consult ``screens()[0]``
    (the primary by AppKit convention), regardless of which screen the OS
    currently considers ``mainScreen``.
    """
    primary_h = 1117.0  # e.g. 16-inch MBP built-in @ default scaling
    secondary_h = 2160.0  # external 4K above the laptop, focused (terminal)
    fake = _make_fake_appkit(primary_h, secondary_h, main_index=1)
    # Sanity: in this fake, mainScreen and screens()[0] disagree, so a buggy
    # implementation that read mainScreen would return the wrong height.
    assert fake.NSScreen.mainScreen().frame().size.height == secondary_h
    assert fake.NSScreen.screens()[0].frame().size.height == primary_h
    # The helper must pick the primary, not the focused screen.
    assert mmc._overlay_primary_screen_height(fake) == primary_h
    assert mmc._overlay_primary_screen_height(fake) != secondary_h


def test_overlay_height_helper_handles_missing_screens_attribute() -> None:
    class _AppKit:
        NSScreen = object()

    assert mmc._overlay_primary_screen_height(_AppKit) is None


# ---------------------------------------------------------------------------
# Darwin-only live AppKit smokes (build + tear down a real NSWindow).
# ---------------------------------------------------------------------------


@pytest.mark.darwin
def test_show_target_overlay_dwell_smoke() -> None:
    if sys.platform != "darwin":
        pytest.skip("AppKit overlay is darwin-only")
    pytest.importorskip("AppKit")
    # 0.05s is short enough to keep the suite fast and long enough for the
    # AppKit run loop to render at least one tick.
    mmc.show_target_overlay(
        x=10.0, y=10.0, count=5, dwell_seconds=0.05, step=False,
    )


@pytest.mark.darwin
def test_show_target_overlay_zero_dwell_returns_immediately() -> None:
    if sys.platform != "darwin":
        pytest.skip("AppKit overlay is darwin-only")
    pytest.importorskip("AppKit")
    mmc.show_target_overlay(
        x=20.0, y=30.0, count=0, dwell_seconds=0.0, step=False,
    )


@pytest.mark.darwin
def test_show_target_overlay_negative_dwell_clamped() -> None:
    if sys.platform != "darwin":
        pytest.skip("AppKit overlay is darwin-only")
    pytest.importorskip("AppKit")
    mmc.show_target_overlay(
        x=15.0, y=25.0, count=1, dwell_seconds=-1.0, step=False,
    )
