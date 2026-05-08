"""Plan-021: macos_mouse_click_loop.sh -T routes --show-only / pacing flags to the clicker.

The loop hard-codes ``mouse_click=${script_dir}/macos_mouse_click.py``, so the
shimmed clicker has to live next to a copy of the loop script. Each test stages
the loop + helpers + a stub ``macos_mouse_click.py`` (and other scripts the
loop touches) into ``tmp_path`` and invokes the staged loop.
"""

from __future__ import annotations

import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LOOP_SH_SRC = REPO_ROOT / "osx" / "macos_mouse_click_loop.sh"
DEFAULTS_PROFILE_SRC = REPO_ROOT / "osx" / "config" / "cookie_clicker_profile.defaults.json"


_STUB_CLICKER = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import json
    import os
    import sys

    # Record argv per invocation so the loop test can assert on every call.
    log_path = os.environ.get("PLAN021_STUB_LOG")
    if log_path:
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"argv": sys.argv[1:]}) + "\\n")
    sys.exit(0)
    """
)


_STUB_GOLDEN_SWEEPER = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import json
    import os
    import sys

    log_path = os.environ.get("PLAN021_STUB_LOG")
    if log_path:
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"sweeper_argv": sys.argv[1:]}) + "\\n")
    sys.exit(0)
    """
)


def _stage_loop(tmp_path: Path) -> Path:
    """Copy the loop into ``tmp_path`` next to stub clicker / sweeper / config.

    Returns the path of the staged ``macos_mouse_click_loop.sh``.
    """
    staged = tmp_path / "macos_mouse_click_loop.sh"
    shutil.copyfile(LOOP_SH_SRC, staged)
    staged.chmod(0o755)

    clicker = tmp_path / "macos_mouse_click.py"
    clicker.write_text(_STUB_CLICKER)
    clicker.chmod(0o755)

    sweeper = tmp_path / "cookie_clicker_golden_sweeper.py"
    sweeper.write_text(_STUB_GOLDEN_SWEEPER)
    sweeper.chmod(0o755)

    # The loop also references detect / preview helpers; provide no-op stubs so
    # the loop's existence checks pass without invoking real detection.
    for name in (
        "cookie_clicker_detect_coords.py",
        "cookie_clicker_preview_plan.py",
    ):
        path = tmp_path / name
        path.write_text("#!/usr/bin/env python3\nimport sys; sys.exit(0)\n")
        path.chmod(0o755)

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    shutil.copyfile(
        DEFAULTS_PROFILE_SRC,
        config_dir / "cookie_clicker_profile.defaults.json",
    )
    return staged


def _run_staged_loop(
    staged: Path, argv: list[str], env_extra: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    env = {"PATH": "/usr/bin:/bin"}
    import os as _os

    env = {**_os.environ, **env}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["/usr/bin/env", "bash", str(staged), *argv],
        cwd=str(staged.parent),
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )


def _read_stub_log(log_path: Path) -> list[dict]:
    if not log_path.exists():
        return []
    out: list[dict] = []
    import json as _json

    for line in log_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(_json.loads(line))
    return out


def test_loop_help_documents_tour_flags() -> None:
    r = subprocess.run(
        ["/usr/bin/env", "bash", str(LOOP_SH_SRC), "-h"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert r.returncode == 0, r.stderr
    out = r.stdout + r.stderr
    assert "-T" in out
    assert "-W" in out
    assert "-X" in out
    assert "show-only" in out.lower() or "tour" in out.lower()


def test_loop_w_without_t_rejected() -> None:
    r = subprocess.run(
        ["/usr/bin/env", "bash", str(LOOP_SH_SRC), "-W", "0.5"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert r.returncode == 1, (r.stdout, r.stderr)
    assert "-W requires -T" in (r.stdout + r.stderr)


def test_loop_x_without_t_rejected() -> None:
    r = subprocess.run(
        ["/usr/bin/env", "bash", str(LOOP_SH_SRC), "-X"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert r.returncode == 1, (r.stdout, r.stderr)
    assert "-X requires -T" in (r.stdout + r.stderr)


def test_loop_w_invalid_value_rejected() -> None:
    r = subprocess.run(
        ["/usr/bin/env", "bash", str(LOOP_SH_SRC), "-T", "-W", "abc"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert r.returncode == 1, (r.stdout, r.stderr)
    assert "Invalid -W value" in (r.stdout + r.stderr)


def test_loop_tour_one_cycle_records_show_only_argv(tmp_path: Path) -> None:
    staged = _stage_loop(tmp_path)
    log = tmp_path / "stub.log"
    r = _run_staged_loop(
        staged,
        ["-T", "-c", "1", "-W", "0.5"],
        env_extra={"PLAN021_STUB_LOG": str(log)},
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    entries = _read_stub_log(log)
    clicker_calls = [e for e in entries if "argv" in e]
    sweeper_calls = [e for e in entries if "sweeper_argv" in e]
    assert clicker_calls, "stub clicker was not invoked"
    # Plan-021: golden sweeper is skipped during a tour.
    assert sweeper_calls == [], sweeper_calls
    for entry in clicker_calls:
        argv = entry["argv"]
        assert "--show-only" in argv, argv
        assert "--show-dwell-seconds" in argv, argv
        idx = argv.index("--show-dwell-seconds")
        assert argv[idx + 1] == "0.5", argv
        assert "--show-step" not in argv, argv
        assert "--abort-on-mouse-move" not in argv, argv
        assert "-Y" in argv, argv


def test_loop_tour_step_mode_uses_show_step(tmp_path: Path) -> None:
    staged = _stage_loop(tmp_path)
    log = tmp_path / "stub.log"
    r = _run_staged_loop(
        staged,
        ["-T", "-X", "-c", "1", "-S"],
        env_extra={"PLAN021_STUB_LOG": str(log)},
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    entries = _read_stub_log(log)
    clicker_calls = [e for e in entries if "argv" in e]
    assert clicker_calls, "stub clicker was not invoked"
    # -S => skip ladder => only cookie burst targets
    for entry in clicker_calls:
        argv = entry["argv"]
        assert "--show-only" in argv
        assert "--show-step" in argv
        assert "--show-dwell-seconds" not in argv
        assert "--abort-on-mouse-move" not in argv


def test_loop_no_tour_keeps_abort_on_mouse_move(tmp_path: Path) -> None:
    staged = _stage_loop(tmp_path)
    log = tmp_path / "stub.log"
    r = _run_staged_loop(
        staged,
        ["-c", "1", "-S"],
        env_extra={"PLAN021_STUB_LOG": str(log)},
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    entries = _read_stub_log(log)
    clicker_calls = [e for e in entries if "argv" in e]
    assert clicker_calls, "stub clicker was not invoked"
    for entry in clicker_calls:
        argv = entry["argv"]
        assert "--abort-on-mouse-move" in argv, argv
        assert "--show-only" not in argv, argv
        assert "--show-step" not in argv, argv
