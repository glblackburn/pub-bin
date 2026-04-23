"""Unit tests for ``learn_collect`` text helpers (Plan 11 coverage gaps, no Quartz)."""

from __future__ import annotations

import io
from contextlib import redirect_stdout
from types import SimpleNamespace

import macos_mouse_click as mmc


def test_learn_collect_plain_text_line_format() -> None:
    assert mmc.learn_collect_plain_text_line(1, 111.0, 222.0) == "1 111.0000 222.0000"
    assert mmc.learn_collect_plain_text_line(3, 1.5, 2.125) == "3 1.5000 2.1250"


def test_emit_learn_collect_dry_run_stdout_samples_infinite() -> None:
    cfg = SimpleNamespace(learn_point_cap=None)
    buf = io.StringIO()
    with redirect_stdout(buf):
        mmc.emit_learn_collect_dry_run_stdout_samples(cfg)  # type: ignore[arg-type]
    lines = buf.getvalue().strip().splitlines()
    assert len(lines) == 3  # ``_LEARN_COLLECT_DRY_FAKE`` length for infinite dry-run
    assert lines[0].startswith("1 ")


def test_emit_learn_collect_dry_run_stdout_samples_capped() -> None:
    cfg = SimpleNamespace(learn_point_cap=2)
    buf = io.StringIO()
    with redirect_stdout(buf):
        mmc.emit_learn_collect_dry_run_stdout_samples(cfg)  # type: ignore[arg-type]
    lines = buf.getvalue().strip().splitlines()
    assert len(lines) == 2
    assert lines[0].startswith("1 ")
    assert lines[1].startswith("2 ")


def test_emit_learn_collect_dry_run_cap_over_fake_len_uses_min() -> None:
    """Cap larger than fake list still bounded by emit loop (min(cap, 50))."""
    cfg = SimpleNamespace(learn_point_cap=50)
    buf = io.StringIO()
    with redirect_stdout(buf):
        mmc.emit_learn_collect_dry_run_stdout_samples(cfg)  # type: ignore[arg-type]
    lines = buf.getvalue().strip().splitlines()
    assert len(lines) == 50
    assert all(len(line.split()) == 3 for line in lines)
