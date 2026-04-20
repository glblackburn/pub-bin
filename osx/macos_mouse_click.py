#!/usr/bin/env python3
"""
macos_mouse_click.py — synthetic left clicks on macOS via Quartz (PyObjC).

The shebang (#!/usr/bin/env python3) allows running without typing python3,
e.g. ./osx/macos_mouse_click.py --help after: chmod +x osx/macos_mouse_click.py

Requires: Python 3.9+, pyobjc-framework-Quartz; optional rich (TTY UI)
  python3 -m pip install pyobjc-framework-Quartz rich

Permissions: System Settings → Privacy & Security → Accessibility for the
terminal (or app) running this script. Screen Recording is not required.

Stop automated clicking: Ctrl+C (SIGINT) or kill -INT/-TERM <pid>.

Tests / CI: use --dry-run-after-start or env MACOS_MOUSE_CLICK_DRY_RUN=1 to print
MACOS_MOUSE_CLICK_DRY_RUN_JSON on stderr and exit after Running without Quartz.

Coordinates are Quartz global display points (logical points); multi-monitor
layouts can shift expected positions.

Anchor click in --learn: the user's first left mousedown is passed through to
the OS (not swallowed) while we record its location.

Non-interactive automation: use -Y/--yes (not -y, which is the Y coordinate).
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import termios
import tty
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

Quartz: Any = None
_rich_module: Any = None
_rich_import_attempted: bool = False

# Gated Rich editor diagnostics (``MACOS_MOUSE_CLICK_DEBUG_TUI``); see plan
# ``docs/osx/plans/agent/plan-agent-new-test-up-down-navigation.plan.md`` Phase 2.
_DEBUG_TUI_STATE_PREFIX = "MACOS_MOUSE_CLICK_TUI_STATE "
_debug_tui_log_file: Optional[Any] = None
_debug_tui_log_failed: bool = False


def import_quartz() -> Any:
    global Quartz
    if Quartz is not None:
        return Quartz
    try:
        import Quartz as Qz  # type: ignore[import-not-found]

        Quartz = Qz
        return Quartz
    except ImportError:
        print(
            "Error: Quartz (PyObjC) is not installed.\n"
            "  python3 -m pip install pyobjc-framework-Quartz",
            file=sys.stderr,
        )
        sys.exit(2)


shutdown_state: List[bool] = [False]


def _signal_handler(signum: int, frame: Any) -> None:
    shutdown_state[0] = True


def install_signal_handlers() -> None:
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)


def shutdown_requested() -> bool:
    return shutdown_state[0]


def reset_shutdown() -> None:
    shutdown_state[0] = False


def sleep_interruptible(seconds: float) -> None:
    if seconds <= 0:
        return
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if shutdown_requested():
            return
        time.sleep(min(0.2, end - time.monotonic()))


def get_mouse_location(qz: Any) -> tuple:
    ev = qz.CGEventCreate(None)
    loc = qz.CGEventGetLocation(ev)
    return float(loc.x), float(loc.y)


def post_synthetic_click(qz: Any, x: float, y: float) -> None:
    point = qz.CGPoint(x=x, y=y)
    for ev_type in (qz.kCGEventLeftMouseDown, qz.kCGEventLeftMouseUp):
        ev = qz.CGEventCreateMouseEvent(
            None, ev_type, point, qz.kCGMouseButtonLeft
        )
        qz.CGEventPost(qz.kCGHIDEventTap, ev)


def wait_for_anchor_click(qz: Any) -> Union[tuple, bool, None]:
    """Return (x, y) on success, False if tap could not be created, None if interrupted."""
    anchor: List[tuple] = []
    tap_ref: List[Any] = [None]

    def callback(proxy: Any, etype: int, event: Any, refcon: Any) -> Any:
        if shutdown_requested():
            if tap_ref[0] is not None:
                qz.CGEventTapEnable(tap_ref[0], False)
            return event
        if etype == qz.kCGEventLeftMouseDown:
            loc = qz.CGEventGetLocation(event)
            anchor.append((float(loc.x), float(loc.y)))
            if tap_ref[0] is not None:
                qz.CGEventTapEnable(tap_ref[0], False)
        return event

    mask = qz.CGEventMaskBit(qz.kCGEventLeftMouseDown)
    tap = qz.CGEventTapCreate(
        qz.kCGHIDEventTap,
        qz.kCGHeadInsertEventTap,
        qz.kCGEventTapOptionDefault,
        mask,
        callback,
        None,
    )
    if tap is None:
        print(
            "Error: could not create event tap. Enable Accessibility for this "
            "terminal in System Settings → Privacy & Security → Accessibility.",
            file=sys.stderr,
        )
        return False

    tap_ref[0] = tap
    run_loop_source = qz.CFMachPortCreateRunLoopSource(None, tap, 0)
    qz.CFRunLoopAddSource(
        qz.CFRunLoopGetCurrent(),
        run_loop_source,
        qz.kCFRunLoopCommonModes,
    )
    qz.CGEventTapEnable(tap, True)

    print(
        "Waiting for your first left click to record the anchor point…",
        file=sys.stderr,
    )
    try:
        while not anchor and not shutdown_requested():
            qz.CFRunLoopRunInMode(qz.kCFRunLoopDefaultMode, 0.25, True)
    finally:
        qz.CGEventTapEnable(tap, False)
        qz.CFRunLoopRemoveSource(
            qz.CFRunLoopGetCurrent(),
            run_loop_source,
            qz.kCFRunLoopCommonModes,
        )

    if not anchor:
        return None
    return anchor[0]


def default_count_for_mode(mode: str) -> int:
    return 0 if mode == "learn" else 1


def count_label(n: int) -> str:
    return "infinite (until Ctrl+C or SIGTERM)" if n == 0 else str(n)


def _running_message(cfg: ResolvedConfig) -> str:
    """Human-readable tail of the ``Running:`` line (no ``Running:`` prefix)."""
    return f"mode={cfg.mode} count={count_label(cfg.count)} delay={cfg.delay}s"


@dataclass
class ResolvedConfig:
    mode: str = ""
    x: Optional[float] = None
    y: Optional[float] = None
    count: int = 0
    delay: float = 5.0
    sources: Dict[str, str] = field(default_factory=dict)
    assume_yes: bool = False
    used_interactive: bool = False

    def set_field(self, name: str, value: Any, source: str) -> None:
        setattr(self, name, value)
        self.sources[name] = source


def resolved_config_for_dry_run_json(cfg: ResolvedConfig) -> Dict[str, Any]:
    """Serializable resolved config for MACOS_MOUSE_CLICK_DRY_RUN_JSON (tests / CI)."""
    return {
        "mode": cfg.mode,
        "count": cfg.count,
        "delay": cfg.delay,
        "x": None if cfg.x is None else float(cfg.x),
        "y": None if cfg.y is None else float(cfg.y),
    }


def dry_run_after_start_requested(ns: argparse.Namespace) -> bool:
    """True if we should exit after the Running line without importing Quartz."""
    if getattr(ns, "dry_run_after_start", False):
        return True
    v = os.environ.get("MACOS_MOUSE_CLICK_DRY_RUN", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def emit_dry_run_json_line(cfg: ResolvedConfig) -> None:
    payload = resolved_config_for_dry_run_json(cfg)
    print(
        "MACOS_MOUSE_CLICK_DRY_RUN_JSON "
        + json.dumps(payload, sort_keys=True, separators=(",", ":")),
        file=sys.stderr,
    )


def try_import_rich() -> Any:
    global _rich_module, _rich_import_attempted
    if _rich_import_attempted:
        return _rich_module
    _rich_import_attempted = True
    try:
        import rich  # type: ignore[import-not-found]

        _rich_module = rich
        return rich
    except ImportError:
        _rich_module = None
        return None


def tty_can_use_rich_editor(cfg: ResolvedConfig) -> bool:
    return (
        not cfg.assume_yes
        and sys.stdin.isatty()
        and sys.stdout.isatty()
    )


def _restore_terminal(fd: int, attrs: List) -> None:
    termios.tcsetattr(fd, termios.TCSADRAIN, attrs)


def _drain_stdin_burst(max_bytes: int = 256, idle_timeout: float = 0.05) -> None:
    """Discard pending stdin bytes (tail of an unknown ESC / mouse / wheel sequence)."""
    import select

    n = 0
    while n < max_bytes:
        r, _, _ = select.select([sys.stdin], [], [], idle_timeout)
        if not r:
            break
        chunk = sys.stdin.read(max_bytes - n)
        if not chunk:
            break
        n += len(chunk)


def read_raw_key() -> str:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "":
            return ""
        if ch == "\x04":
            return "ctrl_d"
        if ch == "\x1b":
            import select

            def wait_char(timeout: float) -> str:
                r, _, _ = select.select([sys.stdin], [], [], timeout)
                if not r:
                    return ""
                return sys.stdin.read(1) or ""

            # Arrow keys are ESC [ A / ESC [ B (CSI) or ESC O A / ESC O B (SS3).
            # A short select after ESC mis-reads the prefix as lone Escape → false
            # "cancel". Use generous waits and full CSI tails (e.g. ESC [ 1 ; 3 B).
            ch2 = wait_char(0.4)
            if ch2 == "":
                # Lone ESC: do not cancel (DEF-003); wheel / meta can look similar.
                return "other"
            if ch2 == "[":
                buf: List[str] = []
                # DEF-006: CSI tail bytes can arrive slowly. Use one deadline for the whole
                # tail after "["; retry select until the deadline (do not stop on first empty).
                deadline = time.monotonic() + 1.0
                while len(buf) < 32:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    c = wait_char(min(0.5, remaining))
                    if c == "":
                        continue
                    buf.append(c)
                    if c in "ABCDEFGHZab~":
                        break
                tail = "".join(buf)
                if tail.endswith("A"):
                    return "up"
                if tail.endswith("B"):
                    return "down"
                return "other"
            if ch2 == "O":
                deadline = time.monotonic() + 1.0
                ch3 = ""
                while not ch3 and time.monotonic() < deadline:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    got = wait_char(min(0.5, remaining))
                    if got:
                        ch3 = got
                if ch3 == "A":
                    return "up"
                if ch3 == "B":
                    return "down"
                return "other"
            # Unknown ESC prefix (e.g. mouse / wheel `ESC [ < …`, `ESC ]`, `ESC >`).
            _drain_stdin_burst()
            return "other"
        if ch == "\x03":
            return "ctrl_c"
        if ch in ("\r", "\n"):
            return "enter"
        oc = ch.lower()
        if oc == "s":
            return "s"
        if oc == "q":
            return "q"
        if oc == "r":
            return "r"
        return "other"
    finally:
        _restore_terminal(fd, old)


def editor_row_keys(cfg: ResolvedConfig) -> List[str]:
    keys: List[str] = ["mode"]
    if cfg.mode == "fixed":
        keys.extend(["x", "y"])
    keys.extend(["count", "delay"])
    return keys


def _debug_tui_env_enabled() -> bool:
    v = os.environ.get("MACOS_MOUSE_CLICK_DEBUG_TUI", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _debug_tui_log_path() -> Optional[str]:
    p = os.environ.get("MACOS_MOUSE_CLICK_DEBUG_TUI_LOG", "").strip()
    return p if p else None


def _reset_debug_tui_log_sink() -> None:
    """Close optional log file; reset flags (new editor session or tests)."""
    global _debug_tui_log_file, _debug_tui_log_failed
    try:
        if _debug_tui_log_file is not None:
            _debug_tui_log_file.close()
    except OSError:
        pass
    _debug_tui_log_file = None
    _debug_tui_log_failed = False


def _debug_tui_append_file(file_line: str) -> None:
    """Append one line to the optional log file (``file_line`` is JSON + newline only)."""
    global _debug_tui_log_file, _debug_tui_log_failed
    if _debug_tui_log_failed:
        return
    path = _debug_tui_log_path()
    if not path:
        return
    try:
        if _debug_tui_log_file is None:
            # Append: preserve prior runs and other writers; never truncate on open.
            _debug_tui_log_file = open(path, "a", encoding="utf-8", buffering=1)
        _debug_tui_log_file.write(file_line)
        _debug_tui_log_file.flush()
    except OSError:
        _debug_tui_log_failed = True


def _debug_tui_write_line(payload: Dict[str, Any]) -> None:
    if not _debug_tui_env_enabled():
        return
    # Log file: one JSON object per line (``jq``-friendly). Stderr: same JSON with grep prefix.
    raw = json.dumps(payload, separators=(",", ":")) + "\n"
    sys.stderr.write(_DEBUG_TUI_STATE_PREFIX + raw)
    sys.stderr.flush()
    _debug_tui_append_file(raw)


def _debug_tui_emit(
    cfg: ResolvedConfig,
    row_keys: List[str],
    selected: int,
    *,
    event: str,
    last_key: Optional[str] = None,
) -> None:
    """Emit one TUI state record (stderr + optional log file).

    Stderr uses ``MACOS_MOUSE_CLICK_TUI_STATE `` + JSON; the optional log file
    stores **JSON only** (one compact object per line) so tools like ``jq`` work
    per line and with ``jq -n '[inputs]'``.

    ``event`` is ``draw`` / ``after_key`` in the Rich editor. See
    ``_debug_tui_emit_run`` / ``_debug_tui_emit_anchor`` for ``run`` / ``anchor``.
    """
    if not _debug_tui_env_enabled():
        return
    if not row_keys:
        return
    selected = max(0, min(selected, len(row_keys) - 1))
    rk = row_keys[selected]
    label, val = _row_display(cfg, rk)
    src = _field_source(cfg, rk)
    body: Dict[str, Any] = {
        "selected_index": selected,
        "row_key": rk,
        "setting_label": label,
        "value_text": str(val),
        "source": str(src),
        "event": event,
    }
    if last_key is not None:
        body["last_key"] = last_key
    _debug_tui_write_line(body)


def _debug_tui_emit_run(cfg: ResolvedConfig) -> None:
    """Emit resolved run parameters (mirrors the ``Running:`` line) to log + stderr."""
    if not _debug_tui_env_enabled():
        return
    ax: Optional[float] = None
    ay: Optional[float] = None
    if cfg.mode == "fixed" and cfg.x is not None and cfg.y is not None:
        ax, ay = float(cfg.x), float(cfg.y)
    body: Dict[str, Any] = {
        "event": "run",
        "running_text": _running_message(cfg),
        "mode": cfg.mode,
        "count": cfg.count,
        "delay": float(cfg.delay),
        "anchor_x": ax,
        "anchor_y": ay,
    }
    _debug_tui_write_line(body)


def _debug_tui_emit_anchor(
    cfg: ResolvedConfig, x: float, y: float, message: str
) -> None:
    """Emit anchor coordinates (learn: after user click; at-cursor: before loop)."""
    if not _debug_tui_env_enabled():
        return
    body: Dict[str, Any] = {
        "event": "anchor",
        "mode": cfg.mode,
        "anchor_x": float(x),
        "anchor_y": float(y),
        "message": message,
    }
    if cfg.mode == "learn":
        body["warmup_delay"] = float(cfg.delay)
    _debug_tui_write_line(body)


def _row_display(cfg: ResolvedConfig, key: str) -> Tuple[str, str]:
    if key == "mode":
        v = cfg.mode if cfg.mode else "(not set)"
        return "Mode", v
    if key == "x":
        return "Anchor X", "-" if cfg.x is None else str(cfg.x)
    if key == "y":
        return "Anchor Y", "-" if cfg.y is None else str(cfg.y)
    if key == "count":
        if not cfg.mode:
            return "Count", "(set mode first)"
        return "Count", count_label(cfg.count)
    if key == "delay":
        if not cfg.mode:
            return "Delay (s)", "(set mode first)"
        return "Delay (s)", str(cfg.delay)
    return key, ""


def _source_style(src: str) -> str:
    if src == "cli":
        return "green"
    if src == "default":
        return "dim"
    if src == "prompt":
        return "yellow"
    if src == "tui":
        return "cyan"
    return "dim"


def _field_source(cfg: ResolvedConfig, key: str) -> str:
    if key == "mode":
        return cfg.sources.get("mode", "default") if cfg.mode else "—"
    if key == "x":
        return cfg.sources.get("x", "default") if cfg.x is not None else "—"
    if key == "y":
        return cfg.sources.get("y", "default") if cfg.y is not None else "—"
    return cfg.sources.get(key, "default")


def _apply_row_reset(cfg: ResolvedConfig, key: str) -> None:
    if key == "mode":
        cfg.set_field("mode", "learn", "default")
        cfg.x = None
        cfg.y = None
        for k in ("x", "y"):
            cfg.sources.pop(k, None)
        return
    if key == "x":
        cfg.set_field("x", 0.0, "default")
        return
    if key == "y":
        cfg.set_field("y", 0.0, "default")
        return
    if key == "count":
        cfg.set_field("count", default_count_for_mode(cfg.mode or "learn"), "default")
        return
    if key == "delay":
        cfg.set_field("delay", 5.0, "default")


def _prompt_cooked(console: Any, prompt: str) -> str:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    _restore_terminal(fd, old)
    # Older Rich: Console.input() has no highlight= kwarg; omit for compatibility.
    return console.input(prompt).strip()


def _edit_row(console: Any, cfg: ResolvedConfig, key: str) -> None:
    from rich.panel import Panel
    from rich.text import Text

    if key == "mode":
        old_mode = cfg.mode
        console.print(
            Panel(
                "[cyan]Enter mode[/]: [bold]learn[/] | [bold]fixed[/] | [bold]at-cursor[/]",
                title="Edit mode",
                border_style="cyan",
            )
        )
        raw = _prompt_cooked(
            console,
            "Mode [learn/fixed/at-cursor, default learn]: ",
        ).lower()
        if raw in ("", "learn", "l", "1"):
            cfg.set_field("mode", "learn", "tui")
            cfg.x = None
            cfg.y = None
            cfg.sources.pop("x", None)
            cfg.sources.pop("y", None)
        elif raw in ("fixed", "f", "2"):
            cfg.set_field("mode", "fixed", "tui")
            if cfg.x is None:
                cfg.set_field("x", 0.0, "tui")
            if cfg.y is None:
                cfg.set_field("y", 0.0, "tui")
        elif raw in ("at-cursor", "at_cursor", "a", "c", "3"):
            cfg.set_field("mode", "at_cursor", "tui")
            cfg.x = None
            cfg.y = None
            cfg.sources.pop("x", None)
            cfg.sources.pop("y", None)
        else:
            console.print(Text(f"Unrecognized mode: {raw!r}", style="red"))
        # Re-apply mode-specific count default only when mode actually changes,
        # so re-confirming learn does not wipe a CLI -n count.
        if cfg.mode != old_mode:
            cfg.sources.pop("count", None)
            apply_defaults(cfg)
        return
    if key == "x":
        raw = _prompt_cooked(console, f"Anchor X [{cfg.x}]: ")
        if raw == "":
            return
        try:
            cfg.set_field("x", float(raw), "tui")
        except ValueError:
            console.print(Text(f"Invalid number: {raw!r}", style="red"))
        return
    if key == "y":
        raw = _prompt_cooked(console, f"Anchor Y [{cfg.y}]: ")
        if raw == "":
            return
        try:
            cfg.set_field("y", float(raw), "tui")
        except ValueError:
            console.print(Text(f"Invalid number: {raw!r}", style="red"))
        return
    if key == "count":
        raw = _prompt_cooked(
            console,
            f"Count (0=infinite) [{cfg.count}]: ",
        )
        if raw == "":
            return
        try:
            v = int(raw, 10)
            if v < 0:
                raise ValueError
            cfg.set_field("count", v, "tui")
        except ValueError:
            console.print(Text(f"Invalid count: {raw!r}", style="red"))
        return
    if key == "delay":
        raw = _prompt_cooked(console, f"Delay seconds [{cfg.delay}]: ")
        if raw == "":
            return
        try:
            v = float(raw)
            if v < 0:
                raise ValueError
            cfg.set_field("delay", v, "tui")
        except ValueError:
            console.print(Text(f"Invalid delay: {raw!r}", style="red"))


def _build_editor_table(cfg: ResolvedConfig, row_keys: List[str], selected: int) -> Any:
    from rich.table import Table
    from rich.text import Text

    table = Table(show_header=True, header_style="bold cyan", expand=True)
    table.add_column("Setting", style="white", no_wrap=True)
    table.add_column("Value", style="green")
    table.add_column("Source", style="dim")
    for i, key in enumerate(row_keys):
        label, val = _row_display(cfg, key)
        src = _field_source(cfg, key)
        sel = i == selected
        hl = "bold black on bright_cyan" if sel else ""
        src_st = hl if sel else _source_style(str(src))
        table.add_row(
            Text(label, style=hl or "white"),
            Text(str(val), style=hl or "green"),
            Text(str(src), style=src_st),
        )
    return table


def run_rich_pre_run_editor(cfg: ResolvedConfig, _rich: Any) -> bool:
    """TTY review/edit. Returns True to run clicks, False if user cancelled."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text

    _reset_debug_tui_log_sink()
    console = Console()
    row_keys = editor_row_keys(cfg)
    selected = 0

    while True:
        if not row_keys:
            row_keys = editor_row_keys(cfg)
        selected = max(0, min(selected, len(row_keys) - 1))
        table = _build_editor_table(cfg, row_keys, selected)
        console.clear()
        console.print(
            Panel(
                table,
                title="[bold cyan]macOS mouse click[/] — review / edit",
                subtitle=(
                    "[dim]Up/Down  Enter=edit  S=start  "
                    "Q=cancel  Ctrl+D=cancel  R=reset row  Ctrl+C=cancel[/]"
                ),
                border_style="cyan",
            )
        )
        _debug_tui_emit(cfg, row_keys, selected, event="draw")
        key = read_raw_key()
        _debug_tui_emit(cfg, row_keys, selected, event="after_key", last_key=key)
        if key in ("q", "ctrl_c", "ctrl_d"):
            return False
        if key == "s":
            if not cfg.mode:
                console.print(Text("Set mode before starting (Enter on Mode).", style="red"))
                time.sleep(1.2)
                continue
            if cfg.mode == "fixed" and (cfg.x is None or cfg.y is None):
                console.print(Text("Fixed mode needs Anchor X and Y.", style="red"))
                time.sleep(1.2)
                continue
            apply_defaults(cfg)
            if cfg.count < 0 or cfg.delay < 0:
                console.print(Text("Count and delay must be >= 0.", style="red"))
                time.sleep(1.2)
                continue
            return True
        if key == "r":
            rk = row_keys[selected]
            _apply_row_reset(cfg, rk)
            row_keys = editor_row_keys(cfg)
            continue
        if key == "up":
            selected = max(0, selected - 1)
            continue
        if key == "down":
            selected = min(len(row_keys) - 1, selected + 1)
            continue
        if key == "enter":
            rk = row_keys[selected]
            console.clear()
            _edit_row(console, cfg, rk)
            row_keys = editor_row_keys(cfg)
            _prompt_cooked(console, "\nPress Enter to return to the editor…")
            continue
        continue


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Synthetic left mouse clicks on macOS (Quartz / PyObjC).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples (from repo root; the script is executable: chmod +x osx/macos_mouse_click.py):
  ./osx/macos_mouse_click.py --learn
  ./osx/macos_mouse_click.py --learn -Y
  ./osx/macos_mouse_click.py --interactive
  ./osx/macos_mouse_click.py -x 400 -y 300 -n 3 -Y

Install dependencies:
  python3 -m pip install pyobjc-framework-Quartz rich

Stop repeats: Ctrl+C   (Accessibility required for Terminal)
Use -Y or --yes for non-interactive runs (-y is reserved for Y coordinate).
""".strip(),
    )
    p.add_argument(
        "--learn",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Learn anchor from first real left click",
    )
    p.add_argument(
        "--at-cursor",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Use mouse position once at start (no event tap)",
    )
    p.add_argument(
        "-x", "--x", type=float, default=argparse.SUPPRESS, help="Fixed anchor X"
    )
    p.add_argument(
        "-y", "--y", type=float, default=argparse.SUPPRESS, help="Fixed anchor Y"
    )
    p.add_argument(
        "-n",
        "--count",
        type=int,
        default=argparse.SUPPRESS,
        help="Synthetic clicks (0=infinite). Default: 0 learn, 1 fixed/at-cursor",
    )
    p.add_argument(
        "-d",
        "--delay",
        type=float,
        default=argparse.SUPPRESS,
        help="Seconds between synthetics and learn warmup (default: 5)",
    )
    p.add_argument(
        "--interactive",
        action="store_true",
        default=False,
        help=(
            "Prompt for missing options (TTY stdin). If stdout is also a TTY "
            "and rich is installed, a table editor is used instead of plain prompts."
        ),
    )
    p.add_argument(
        "-Y",
        "--yes",
        action="store_true",
        dest="assume_yes",
        default=False,
        help="Skip prompts and confirmation; mode must be fully on CLI",
    )
    p.add_argument(
        "--dry-run-after-start",
        action="store_true",
        default=False,
        help=(
            "After printing Running, emit one MACOS_MOUSE_CLICK_DRY_RUN_JSON line "
            "on stderr and exit 0 without importing Quartz or posting clicks. "
            "Same when env MACOS_MOUSE_CLICK_DRY_RUN is 1/true/yes/on."
        ),
    )
    return p


def validate_ns(ns: argparse.Namespace) -> Optional[str]:
    vd = vars(ns)
    learn = vd.get("learn", False)
    atc = vd.get("at_cursor", False)
    has_x = "x" in vd
    has_y = "y" in vd
    if has_x ^ has_y:
        return "Both -x and -y are required together for fixed mode"
    n_modes = sum([bool(learn), bool(atc), bool(has_x and has_y)])
    if n_modes > 1:
        return "Use only one of --learn, --at-cursor, or -x with -y"
    return None


def mode_fully_on_cli(ns: argparse.Namespace) -> bool:
    vd = vars(ns)
    return bool(
        vd.get("learn") or vd.get("at_cursor") or ("x" in vd and "y" in vd)
    )


def namespace_to_cfg(ns: argparse.Namespace) -> ResolvedConfig:
    vd = vars(ns)
    cfg = ResolvedConfig(
        assume_yes=bool(vd.get("assume_yes", False)),
        used_interactive=bool(vd.get("interactive", False)),
    )
    if vd.get("learn"):
        cfg.set_field("mode", "learn", "cli")
    elif vd.get("at_cursor"):
        cfg.set_field("mode", "at_cursor", "cli")
    elif "x" in vd and "y" in vd:
        cfg.set_field("mode", "fixed", "cli")
        cfg.set_field("x", float(vd["x"]), "cli")
        cfg.set_field("y", float(vd["y"]), "cli")
    if "count" in vd:
        cfg.set_field("count", int(vd["count"]), "cli")
    if "delay" in vd:
        cfg.set_field("delay", float(vd["delay"]), "cli")
    return cfg


def prompt_str(label: str, default: str) -> str:
    raw = input(f"{label} [{default}]: ").strip()
    return default if raw == "" else raw


def prompt_mode_interactive() -> str:
    print(
        "Select mode:\n"
        "  1) learn — first real left click sets anchor\n"
        "  2) fixed — use X and Y coordinates\n"
        "  3) at-cursor — anchor is mouse position when clicking starts",
        file=sys.stderr,
    )
    choice = prompt_str("Choice", "1").lower()
    if choice in ("1", "learn", "l", ""):
        return "learn"
    if choice in ("2", "fixed", "f"):
        return "fixed"
    if choice in ("3", "at-cursor", "at_cursor", "a", "c"):
        return "at_cursor"
    print(f"Unrecognized choice: {choice!r}", file=sys.stderr)
    sys.exit(2)


def prompt_float_value(label: str, default: float) -> float:
    s = prompt_str(label, str(default))
    try:
        return float(s)
    except ValueError:
        print(f"Invalid number: {s!r}", file=sys.stderr)
        sys.exit(2)


def prompt_int_count(label: str, default: int) -> int:
    s = prompt_str(label, str(default))
    try:
        v = int(s, 10)
        if v < 0:
            raise ValueError
        return v
    except ValueError:
        print(f"Invalid count: {s!r} (need non-negative integer)", file=sys.stderr)
        sys.exit(2)


def run_interactive_prompts(cfg: ResolvedConfig) -> None:
    if not cfg.used_interactive:
        return
    if not sys.stdin.isatty():
        print("Error: --interactive requires a TTY stdin.", file=sys.stderr)
        sys.exit(2)

    if cfg.mode == "":
        cfg.set_field("mode", prompt_mode_interactive(), "prompt")

    if cfg.mode == "fixed":
        if cfg.x is None:
            cfg.set_field("x", prompt_float_value("Anchor X", 0.0), "prompt")
        if cfg.y is None:
            cfg.set_field("y", prompt_float_value("Anchor Y", 0.0), "prompt")

    if "count" not in cfg.sources:
        d = default_count_for_mode(cfg.mode)
        cfg.set_field(
            "count",
            prompt_int_count(
                "Synthetic click count (0 = infinite until interrupt)", d
            ),
            "prompt",
        )

    if "delay" not in cfg.sources:
        cfg.set_field(
            "delay",
            prompt_float_value("Delay between synthetic clicks (seconds)", 5.0),
            "prompt",
        )


def apply_defaults(cfg: ResolvedConfig) -> None:
    if not cfg.mode:
        return
    if "count" not in cfg.sources:
        cfg.set_field("count", default_count_for_mode(cfg.mode), "default")
    if "delay" not in cfg.sources:
        cfg.set_field("delay", 5.0, "default")


def print_confirmation_sheet(cfg: ResolvedConfig) -> None:
    print("\nResolved configuration:", file=sys.stderr)
    print(
        f"  mode          = {cfg.mode}  ({cfg.sources.get('mode', 'default')})",
        file=sys.stderr,
    )
    if cfg.mode == "fixed":
        print(
            f"  x, y          = {cfg.x}, {cfg.y}  "
            f"({cfg.sources.get('x', '?')}, {cfg.sources.get('y', '?')})",
            file=sys.stderr,
        )
    print(
        f"  count         = {count_label(cfg.count)}  "
        f"({cfg.sources.get('count', 'default')})",
        file=sys.stderr,
    )
    print(
        f"  delay (s)     = {cfg.delay}  ({cfg.sources.get('delay', 'default')})",
        file=sys.stderr,
    )
    print(file=sys.stderr)


def confirm_or_abort() -> bool:
    if not sys.stdin.isatty():
        print(
            "Error: confirmation requires a TTY stdin. Use -Y/--yes for "
            "non-interactive runs.",
            file=sys.stderr,
        )
        sys.exit(2)
    ans = input("Proceed? [y/N]: ").strip().lower()
    return ans in ("y", "yes")


def run_synthetic_loop(qz: Any, x: float, y: float, count: int, delay: float) -> int:
    infinite = count == 0
    n_done = 0
    while True:
        if shutdown_requested():
            print("Stopped.", file=sys.stderr)
            return 130
        post_synthetic_click(qz, x, y)
        n_done += 1
        if not infinite and n_done >= count:
            break
        if infinite or n_done < count:
            if shutdown_requested():
                print("Stopped.", file=sys.stderr)
                return 130
            sleep_interruptible(delay)
            if shutdown_requested():
                print("Stopped.", file=sys.stderr)
                return 130
    return 0


def run_learn_flow(qz: Any, cfg: ResolvedConfig) -> int:
    pt = wait_for_anchor_click(qz)
    if pt is False:
        return 2
    if pt is None:
        if shutdown_requested():
            print("Stopped.", file=sys.stderr)
            return 130
        print("Error: no anchor click received.", file=sys.stderr)
        return 2
    x, y = pt
    anchor_msg = (
        f"Anchor recorded at ({x:.1f}, {y:.1f}). Warmup: sleeping {cfg.delay}s…"
    )
    _debug_tui_emit_anchor(cfg, x, y, anchor_msg)
    print(anchor_msg, file=sys.stderr)
    sleep_interruptible(cfg.delay)
    if shutdown_requested():
        print("Stopped.", file=sys.stderr)
        return 130
    return run_synthetic_loop(qz, x, y, cfg.count, cfg.delay)


def run_fixed_or_cursor_flow(qz: Any, cfg: ResolvedConfig) -> int:
    if cfg.mode == "at_cursor":
        x, y = get_mouse_location(qz)
        cur_msg = f"Cursor position recorded at ({x:.1f}, {y:.1f})."
        _debug_tui_emit_anchor(cfg, x, y, cur_msg)
    else:
        x, y = float(cfg.x), float(cfg.y)
    return run_synthetic_loop(qz, x, y, cfg.count, cfg.delay)


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_arg_parser()
    ns = parser.parse_args(argv)

    err = validate_ns(ns)
    if err:
        print(f"Error: {err}", file=sys.stderr)
        return 2

    if ns.assume_yes and ns.interactive:
        print("Error: --interactive cannot be combined with -Y/--yes.", file=sys.stderr)
        return 2

    if ns.assume_yes and not mode_fully_on_cli(ns):
        print(
            "Error: -Y/--yes requires --learn, --at-cursor, or both -x and -y "
            "on the command line.",
            file=sys.stderr,
        )
        return 2

    cfg = namespace_to_cfg(ns)
    rich_mod = try_import_rich()
    can_tui = tty_can_use_rich_editor(cfg) and rich_mod is not None

    if tty_can_use_rich_editor(cfg) and rich_mod is None:
        print(
            "Tip: install rich for a colored TTY editor: "
            "python3 -m pip install rich",
            file=sys.stderr,
        )

    if cfg.used_interactive and not can_tui:
        run_interactive_prompts(cfg)

    if cfg.mode == "" and not can_tui:
        print(
            "Error: specify --learn, --at-cursor, or both -x and -y, "
            "or use --interactive, or install rich and rerun without -Y.",
            file=sys.stderr,
        )
        return 2

    if cfg.mode == "fixed" and (cfg.x is None or cfg.y is None) and not can_tui:
        print("Error: fixed mode requires both x and y.", file=sys.stderr)
        return 2

    if can_tui:
        if not run_rich_pre_run_editor(cfg, rich_mod):
            print("Cancelled.", file=sys.stderr)
            return 0
        apply_defaults(cfg)
    elif cfg.mode != "":
        apply_defaults(cfg)

    if cfg.mode == "":
        print("Error: mode was not set.", file=sys.stderr)
        return 2

    if cfg.mode == "fixed" and (cfg.x is None or cfg.y is None):
        print("Error: fixed mode requires both x and y.", file=sys.stderr)
        return 2

    if cfg.count < 0:
        print("Error: count must be >= 0", file=sys.stderr)
        return 2
    if cfg.delay < 0:
        print("Error: delay must be >= 0", file=sys.stderr)
        return 2

    if not cfg.assume_yes and not can_tui:
        print_confirmation_sheet(cfg)
        if not confirm_or_abort():
            print("Cancelled.", file=sys.stderr)
            return 0

    if can_tui:
        from rich.console import Console

        Console(stderr=True).print(
            f"[green]Running:[/] mode={cfg.mode} count={count_label(cfg.count)} "
            f"delay={cfg.delay}s"
        )
    else:
        print(
            f"Running: mode={cfg.mode} count={count_label(cfg.count)} delay={cfg.delay}s",
            file=sys.stderr,
        )

    if not can_tui:
        _reset_debug_tui_log_sink()
    _debug_tui_emit_run(cfg)

    if dry_run_after_start_requested(ns):
        emit_dry_run_json_line(cfg)
        return 0

    qz = import_quartz()
    install_signal_handlers()
    reset_shutdown()

    try:
        if cfg.mode == "learn":
            return run_learn_flow(qz, cfg)
        return run_fixed_or_cursor_flow(qz, cfg)
    except KeyboardInterrupt:
        print("Stopped.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
