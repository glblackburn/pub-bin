"""Tests for magic_cookie_label_tool (plan-016 / plan-019) — pure helpers only (no Qt)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "osx"))

from magic_cookie_label_tool import (  # noqa: E402
    png_indices_matching_query,
    png_path_matches_search_query,
)


def test_png_path_matches_substring_case_insensitive(tmp_path: Path) -> None:
    p = tmp_path / "golden-sweeper-20260504-223259-f00000.png"
    p.write_bytes(b"x")
    assert png_path_matches_search_query(p, "223259")
    assert png_path_matches_search_query(p, "GOLDEN-SWEEper")
    assert not png_path_matches_search_query(p, "nomatch")


def test_png_path_matches_resolved_file(tmp_path: Path) -> None:
    p = tmp_path / "a.png"
    p.write_bytes(b"x")
    assert png_path_matches_search_query(p, str(p.resolve()))


def test_png_indices_matching_query_order(tmp_path: Path) -> None:
    paths = [
        tmp_path / "b.png",
        tmp_path / "golden-x.png",
        tmp_path / "golden-y.png",
    ]
    for q in paths:
        q.write_bytes(b"1")
    ix = png_indices_matching_query(paths, "golden")
    assert ix == [1, 2]


def test_empty_query_no_match(tmp_path: Path) -> None:
    p = tmp_path / "z.png"
    p.write_bytes(b"1")
    assert not png_path_matches_search_query(p, "")
    assert not png_path_matches_search_query(p, "   ")
    assert png_indices_matching_query([p], "") == []
