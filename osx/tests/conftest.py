"""Pytest configuration for macOS mouse click automation (plan 03)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

OSX_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = OSX_DIR.parent
SCRIPT_PATH = OSX_DIR / "macos_mouse_click.py"

if str(OSX_DIR) not in sys.path:
    sys.path.insert(0, str(OSX_DIR))


@pytest.fixture(autouse=True)
def _reset_rich_import_cache_between_tests() -> None:
    import macos_mouse_click as mmc

    mmc._rich_import_attempted = False
    mmc._rich_module = None
    yield
    mmc._rich_import_attempted = False
    mmc._rich_module = None


def pytest_configure(config: pytest.Config) -> None:
    for line in (
        "darwin: requires macOS",
        "mt02: plan 03 MT-02 automation",
        "mt09: plan 03 MT-09 automation",
        "table_nav: Rich table Down + DEF-009 layout PTY tests (darwin; collected in test-quick)",
    ):
        config.addinivalue_line("markers", line)


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def script_path() -> Path:
    return SCRIPT_PATH


@pytest.fixture
def pexpect_module():
    try:
        import pexpect
    except ImportError:
        pytest.skip("pexpect is required for PTY tests (pip install -r osx/requirements-test.txt)")
    return pexpect


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Function]) -> None:
    skip_non_darwin = pytest.mark.skip(reason="macOS-only (plan 03)")
    for item in items:
        if "darwin" in [m.name for m in item.iter_markers()]:
            if sys.platform != "darwin":
                item.add_marker(skip_non_darwin)
