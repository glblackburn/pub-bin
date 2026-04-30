"""Smoke: docs/osx hub and operator paths still exist after doc tree moves."""

from __future__ import annotations

from pathlib import Path

OSX_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = OSX_DIR.parent

_EXPECTED_FILES = (
    "docs/osx/README.md",
    "docs/osx/plans/README.md",
    "docs/osx/plans/DEVELOPMENT_NARRATIVE.md",
    "docs/osx/TERMINOLOGY.md",
    "docs/osx/plans/plan-010-macos-mouse-click-learn-points-collect.md",
    "docs/osx/defects/README.md",
    "docs/osx/OSX-DOCS-REORGANIZATION-PLAN.md",
    "docs/osx/macos-mouse-click-coverage-gap.md",
    "osx/README.md",
    "osx/macos_mouse_click.py",
    "osx/macos_mouse_click_loop.sh",
)


def test_docs_osx_hub_paths_exist() -> None:
    for rel in _EXPECTED_FILES:
        path = REPO_ROOT / rel
        assert path.is_file(), f"missing hub path: {rel}"


def test_docs_osx_plans_agent_tree_removed() -> None:
    """Mouse-clicker session plans were merged into plan-### under docs/osx/plans/."""
    agent_dir = REPO_ROOT / "docs" / "osx" / "plans" / "agent"
    assert not agent_dir.exists(), f"expected removed directory: {agent_dir}"
