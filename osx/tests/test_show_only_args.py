"""Plan-021: --show-only argparse, duplicate guard, validate_ns, namespace_to_cfg."""

from __future__ import annotations

import macos_mouse_click as mmc


def _parse(argv: list[str]):
    return mmc.build_arg_parser().parse_args(argv)


def test_show_only_flags_register_on_namespace() -> None:
    ns = _parse(
        [
            "-x", "10", "-y", "20", "-n", "5", "-Y",
            "--show-only", "--show-dwell-seconds", "0.25",
        ]
    )
    assert ns.show_only is True
    assert ns.show_dwell_seconds == 0.25
    assert ns.show_step is False


def test_show_only_step_flag() -> None:
    ns = _parse(["-x", "1", "-y", "2", "-Y", "--show-only", "--show-step"])
    assert ns.show_only is True
    assert ns.show_step is True


def test_show_only_defaults_when_absent() -> None:
    ns = _parse(["-x", "1", "-y", "2", "-Y"])
    assert ns.show_only is False
    assert ns.show_step is False
    assert "show_dwell_seconds" not in vars(ns)


def test_validate_ns_show_only_requires_target_mode() -> None:
    err = mmc.validate_ns(_parse(["-Y", "--show-only"]))
    assert err is not None
    assert "fixed" in err and "at-cursor" in err


def test_validate_ns_show_only_rejects_learn() -> None:
    err = mmc.validate_ns(_parse(["--learn", "-Y", "--show-only"]))
    assert err is not None
    assert "--learn" in err


def test_validate_ns_show_only_rejects_learn_points() -> None:
    err = mmc.validate_ns(_parse(["--learn-points", "-Y", "--show-only"]))
    assert err is not None
    assert "--learn-points" in err


def test_validate_ns_show_only_accepts_at_cursor() -> None:
    err = mmc.validate_ns(_parse(["--at-cursor", "-Y", "--show-only"]))
    assert err is None


def test_validate_ns_show_only_accepts_fixed() -> None:
    err = mmc.validate_ns(_parse(["-x", "1", "-y", "2", "-Y", "--show-only"]))
    assert err is None


def test_validate_ns_show_step_requires_show_only() -> None:
    err = mmc.validate_ns(_parse(["-x", "1", "-y", "2", "-Y", "--show-step"]))
    assert err is not None
    assert "--show-step" in err and "--show-only" in err


def test_validate_ns_show_dwell_requires_show_only() -> None:
    err = mmc.validate_ns(
        _parse(["-x", "1", "-y", "2", "-Y", "--show-dwell-seconds", "1"])
    )
    assert err is not None
    assert "--show-dwell-seconds" in err and "--show-only" in err


def test_validate_ns_show_dwell_must_be_non_negative() -> None:
    err = mmc.validate_ns(
        _parse(
            [
                "-x", "1", "-y", "2", "-Y",
                "--show-only", "--show-dwell-seconds", "-0.1",
            ]
        )
    )
    assert err is not None
    assert ">= 0" in err


def test_argv_duplicate_guard_show_dwell_seconds() -> None:
    err = mmc.argv_duplicate_cli_option_error(
        [
            "-x", "1", "-y", "2", "-Y", "--show-only",
            "--show-dwell-seconds", "1.0",
            "--show-dwell-seconds", "2.0",
        ]
    )
    assert err is not None
    assert "--show-dwell-seconds" in err


def test_argv_duplicate_guard_show_dwell_seconds_equals_form() -> None:
    err = mmc.argv_duplicate_cli_option_error(
        [
            "-x", "1", "-y", "2", "-Y", "--show-only",
            "--show-dwell-seconds=1.0",
            "--show-dwell-seconds=2.0",
        ]
    )
    assert err is not None
    assert "--show-dwell-seconds" in err


def test_namespace_to_cfg_records_show_only_sources() -> None:
    ns = _parse(
        [
            "-x", "10", "-y", "20", "-n", "5", "-Y",
            "--show-only", "--show-dwell-seconds", "0.25",
        ]
    )
    cfg = mmc.namespace_to_cfg(ns)
    assert cfg.show_only is True
    assert cfg.show_dwell_seconds == 0.25
    assert cfg.show_step is False
    assert cfg.sources.get("show_only") == "cli"
    assert cfg.sources.get("show_dwell_seconds") == "cli"


def test_namespace_to_cfg_records_show_step_source() -> None:
    ns = _parse(["-x", "1", "-y", "2", "-Y", "--show-only", "--show-step"])
    cfg = mmc.namespace_to_cfg(ns)
    assert cfg.show_step is True
    assert cfg.sources.get("show_step") == "cli"


def test_mode_fully_on_cli_with_show_only_fixed() -> None:
    assert (
        mmc.mode_fully_on_cli(_parse(["-x", "1", "-y", "2", "-Y", "--show-only"]))
        is True
    )


def test_running_message_show_only_dwell() -> None:
    cfg = mmc.ResolvedConfig(
        mode="fixed", count=5, x=1.0, y=2.0,
        show_only=True, show_dwell_seconds=0.5, show_step=False,
    )
    msg = mmc._running_message(cfg)
    assert "show_only=true" in msg
    assert "would_click=5" in msg
    assert "dwell=0.5s" in msg


def test_running_message_show_only_step() -> None:
    cfg = mmc.ResolvedConfig(
        mode="at_cursor", count=3,
        show_only=True, show_step=True,
    )
    msg = mmc._running_message(cfg)
    assert "show_only=true" in msg
    assert "would_click=3" in msg
    assert "step" in msg
    assert "dwell=" not in msg
