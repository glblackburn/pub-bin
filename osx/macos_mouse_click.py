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
With ``--abort-on-mouse-move``, a burst stops if the cursor was first
seen near the click target (``--mouse-arm-radius-px``, default
``max(60, 2× threshold)``), then after at least one synthetic click and
after the read cursor has been within ``--mouse-move-threshold-px`` of
that target at least once, a later read farther than the threshold from
that target stops the burst (DEF-010, DEF-011; see README).

Tests / CI: use --dry-run-after-start or env MACOS_MOUSE_CLICK_DRY_RUN=1 to print
MACOS_MOUSE_CLICK_DRY_RUN_JSON on stderr and exit after Running without Quartz.

Plans, defects, and agent session notes: docs/osx/README.md (repo root).

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
from datetime import datetime
import termios
import tty
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

Quartz: Any = None
_rich_module: Any = None
_rich_import_attempted: bool = False

# Raw key reads use this FD (lazy-open ``/dev/tty``) so bytes are not consumed by
# :class:`io.TextIOWrapper` buffering on ``sys.stdin`` (pexpect PTY + Rich).
_kbd_tty_fd: Optional[int] = None
# Cooked TTY attrs snapshot while Rich pre-run editor holds stdin raw (pexpect CSI).
_rich_editor_tty_cooked_attrs: Optional[List] = None


def _kbd_tty_fd_get() -> int:
    """Return a FD for reading keyboard bytes, bypassing ``sys.stdin`` text buffering."""
    global _kbd_tty_fd
    if _kbd_tty_fd is not None:
        return _kbd_tty_fd
    if sys.stdin.isatty():
        try:
            _kbd_tty_fd = os.open("/dev/tty", os.O_RDONLY | os.O_NOCTTY)
        except OSError:
            _kbd_tty_fd = sys.stdin.fileno()
    else:
        _kbd_tty_fd = sys.stdin.fileno()
    return _kbd_tty_fd

# Gated Rich editor diagnostics (``MACOS_MOUSE_CLICK_DEBUG_TUI``); see plan
# ``docs/osx/plans/plan-009-macos-mouse-click-tui-arrow-navigation-narrative.md`` appendix (Down PTY / logging).
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
            "  Setup recommended: make -C osx setup\n"
            "  Or install directly: python3 -m pip install pyobjc-framework-Quartz",
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


def request_shutdown() -> None:
    """Request cooperative stop (same flag as SIGINT/SIGTERM handlers)."""
    shutdown_state[0] = True


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


def warp_cursor(qz: Any, x: float, y: float) -> None:
    """Plan-021: move the cursor to (x, y) without posting any click events.

    Uses ``CGWarpMouseCursorPosition`` (global display points, top-left origin),
    then re-associates the mouse with the cursor so subsequent physical motion
    is honored. Accessibility permission (already required for clicks) is
    sufficient; no Screen Recording needed.
    """
    point = qz.CGPoint(x=float(x), y=float(y))
    qz.CGWarpMouseCursorPosition(point)
    assoc = getattr(qz, "CGAssociateMouseAndMouseCursorPosition", None)
    if assoc is not None:
        try:
            assoc(True)
        except Exception:  # pragma: no cover - best-effort restore
            pass


def show_target_overlay(
    x: float,
    y: float,
    count: int,
    dwell_seconds: float,
    step: bool,
) -> None:
    """Plan-021: draw a borderless AppKit overlay near (x, y) with click count.

    Lazy-imports ``AppKit`` so dry-run / non-darwin paths never load Cocoa.
    Renders two windows: a small floating panel ("would click N" + "(x, y)")
    and a tiny crosshair sitting at (x, y). Pumps the current run loop in
    short slices for ``dwell_seconds`` seconds, or until Enter is read on
    stdin when ``step`` is true.
    """
    try:
        import AppKit  # type: ignore[import-not-found]
    except ImportError:
        # PyObjC AppKit (Cocoa) not installed; degrade to a stderr line so the
        # tour still produces visible output.
        print(
            f"show-only: would click {int(count)} at ({float(x):.1f}, {float(y):.1f}) "
            f"[AppKit not available; install pyobjc-framework-Cocoa for overlay]",
            file=sys.stderr,
            flush=True,
        )
        if step:
            try:
                sys.stdin.readline()
            except (OSError, ValueError):
                pass
        else:
            time.sleep(max(0.0, float(dwell_seconds)))
        return

    AppKit.NSApplication.sharedApplication()
    screen = AppKit.NSScreen.mainScreen()
    if screen is None:  # pragma: no cover - headless smoke
        return
    screen_h = float(screen.frame().size.height)

    win_w, win_h = 220.0, 70.0
    panel_x = float(x) + 20.0
    # Cocoa coordinates are bottom-left; Quartz cursor coords are top-left.
    panel_y = screen_h - float(y) - win_h - 8.0
    panel_rect = AppKit.NSMakeRect(panel_x, panel_y, win_w, win_h)
    style = AppKit.NSWindowStyleMaskBorderless
    backing = AppKit.NSBackingStoreBuffered
    panel = (
        AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            panel_rect, style, backing, False
        )
    )
    panel.setLevel_(AppKit.NSStatusWindowLevel)
    panel.setBackgroundColor_(
        AppKit.NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.65)
    )
    panel.setOpaque_(False)
    panel.setHasShadow_(True)
    panel.setIgnoresMouseEvents_(True)

    cv = panel.contentView()

    label_text = (
        "would click \u221E" if int(count) == 0 else f"would click {int(count)}"
    )
    label = AppKit.NSTextField.alloc().initWithFrame_(
        AppKit.NSMakeRect(10, 36, win_w - 20, 24)
    )
    label.setStringValue_(label_text)
    label.setBezeled_(False)
    label.setDrawsBackground_(False)
    label.setEditable_(False)
    label.setSelectable_(False)
    label.setTextColor_(AppKit.NSColor.whiteColor())
    label.setFont_(AppKit.NSFont.boldSystemFontOfSize_(16.0))
    cv.addSubview_(label)

    coord_text = f"({int(round(float(x)))}, {int(round(float(y)))})"
    coord = AppKit.NSTextField.alloc().initWithFrame_(
        AppKit.NSMakeRect(10, 8, win_w - 20, 22)
    )
    coord.setStringValue_(coord_text)
    coord.setBezeled_(False)
    coord.setDrawsBackground_(False)
    coord.setEditable_(False)
    coord.setSelectable_(False)
    coord.setTextColor_(AppKit.NSColor.whiteColor())
    coord.setFont_(AppKit.NSFont.systemFontOfSize_(12.0))
    cv.addSubview_(coord)

    ch_w, ch_h = 30.0, 30.0
    ch_x = float(x) - ch_w / 2.0
    ch_y_cocoa = screen_h - float(y) - ch_h / 2.0
    ch_rect = AppKit.NSMakeRect(ch_x, ch_y_cocoa, ch_w, ch_h)
    crosshair = (
        AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            ch_rect, style, backing, False
        )
    )
    crosshair.setLevel_(AppKit.NSStatusWindowLevel)
    crosshair.setBackgroundColor_(AppKit.NSColor.clearColor())
    crosshair.setOpaque_(False)
    crosshair.setHasShadow_(False)
    crosshair.setIgnoresMouseEvents_(True)

    ch_cv = crosshair.contentView()
    h_line = AppKit.NSView.alloc().initWithFrame_(
        AppKit.NSMakeRect(0.0, ch_h / 2.0 - 1.0, ch_w, 2.0)
    )
    h_line.setWantsLayer_(True)
    h_line.layer().setBackgroundColor_(
        AppKit.NSColor.systemRedColor().CGColor()
    )
    ch_cv.addSubview_(h_line)
    v_line = AppKit.NSView.alloc().initWithFrame_(
        AppKit.NSMakeRect(ch_w / 2.0 - 1.0, 0.0, 2.0, ch_h)
    )
    v_line.setWantsLayer_(True)
    v_line.layer().setBackgroundColor_(
        AppKit.NSColor.systemRedColor().CGColor()
    )
    ch_cv.addSubview_(v_line)

    panel.orderFrontRegardless()
    crosshair.orderFrontRegardless()

    try:
        if step:
            import select

            while True:
                if shutdown_requested():
                    break
                rl = AppKit.NSRunLoop.currentRunLoop()
                rl.runUntilDate_(
                    AppKit.NSDate.dateWithTimeIntervalSinceNow_(0.05)
                )
                try:
                    r, _, _ = select.select([sys.stdin], [], [], 0)
                except (OSError, ValueError):
                    break
                if r:
                    try:
                        sys.stdin.readline()
                    except (OSError, ValueError):
                        pass
                    break
        else:
            deadline = time.monotonic() + max(0.0, float(dwell_seconds))
            while time.monotonic() < deadline:
                if shutdown_requested():
                    break
                remaining = deadline - time.monotonic()
                slice_s = min(0.05, remaining)
                rl = AppKit.NSRunLoop.currentRunLoop()
                rl.runUntilDate_(
                    AppKit.NSDate.dateWithTimeIntervalSinceNow_(slice_s)
                )
    finally:
        panel.orderOut_(None)
        crosshair.orderOut_(None)
        try:
            panel.close()
            crosshair.close()
        except Exception:  # pragma: no cover - defensive teardown
            pass


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
    if mode == "learn":
        return 0
    if mode == "learn_collect":
        return 0
    return 1


def count_label(n: int) -> str:
    return "infinite (until Ctrl+C or SIGTERM)" if n == 0 else str(n)


def _running_message(cfg: ResolvedConfig) -> str:
    """Human-readable tail of the ``Running:`` line (no ``Running:`` prefix)."""
    if cfg.mode == "learn_collect":
        cap = cfg.learn_point_cap
        cap_s = "infinite" if cap is None else str(cap)
        return f"mode={cfg.mode} learn_point_cap={cap_s} delay={cfg.delay}s"
    if cfg.show_only:
        # Plan-021: tour the target instead of clicking; surface count as a
        # "would click" preview and the chosen pacing (dwell vs step).
        if cfg.show_step:
            pacing = "step"
        else:
            pacing = f"dwell={cfg.show_dwell_seconds}s"
        return (
            f"mode={cfg.mode} show_only=true would_click={count_label(cfg.count)} "
            f"{pacing}"
        )
    return f"mode={cfg.mode} count={count_label(cfg.count)} delay={cfg.delay}s"


@dataclass
class ResolvedConfig:
    mode: str = ""
    x: Optional[float] = None
    y: Optional[float] = None
    count: int = 0
    delay: float = 5.0
    # learn_collect: None = infinite samples; int >= 1 = stop after N real clicks.
    learn_point_cap: Optional[int] = None
    sources: Dict[str, str] = field(default_factory=dict)
    assume_yes: bool = False
    used_interactive: bool = False
    # Phase 1 in-band abort (see docs/osx/plans/plan-002 § Cookie burst rate control).
    abort_on_mouse_move: bool = False
    mouse_move_threshold_px: float = 20.0
    # None => max(60, 2 * mouse_move_threshold_px) at runtime (DEF-010).
    mouse_arm_radius_px: Optional[float] = None
    # Plan-021: --show-only target tour (warp + AppKit overlay; no synthetic clicks).
    show_only: bool = False
    show_dwell_seconds: float = 1.5
    show_step: bool = False

    def set_field(self, name: str, value: Any, source: str) -> None:
        setattr(self, name, value)
        self.sources[name] = source


def resolved_config_for_dry_run_json(cfg: ResolvedConfig) -> Dict[str, Any]:
    """Serializable resolved config for MACOS_MOUSE_CLICK_DRY_RUN_JSON (tests / CI)."""
    d: Dict[str, Any] = {
        "mode": cfg.mode,
        "count": cfg.count,
        "delay": cfg.delay,
        "x": None if cfg.x is None else float(cfg.x),
        "y": None if cfg.y is None else float(cfg.y),
        "abort_on_mouse_move": bool(cfg.abort_on_mouse_move),
        "mouse_move_threshold_px": float(cfg.mouse_move_threshold_px),
        "mouse_arm_radius_px": (
            None
            if cfg.mouse_arm_radius_px is None
            else float(cfg.mouse_arm_radius_px)
        ),
        "show_only": bool(cfg.show_only),
        "show_dwell_seconds": float(cfg.show_dwell_seconds),
        "show_step": bool(cfg.show_step),
    }
    if cfg.mode == "learn_collect":
        d["learn_point_cap"] = cfg.learn_point_cap
    return d


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


def _tty_setraw_now(fd: int) -> None:
    """Enter raw mode with ``TCSANOW`` (not ``tty.setraw``'s default ``TCSAFLUSH``).

    ``TCSAFLUSH`` discards unread input; on PTY + ``pexpect`` that can remove bytes
    the next editor loop needs before ``_read_raw_key_impl`` runs.
    """
    mode = termios.tcgetattr(fd)
    new = list(mode)
    tty.cfmakeraw(new)
    termios.tcsetattr(fd, termios.TCSANOW, new)


def _flush_stdout_safe() -> None:
    """Push Rich frame bytes to the TTY before stderr (DEF-009: avoid stdout/stderr interleave)."""
    try:
        sys.stdout.flush()
    except (OSError, BrokenPipeError, ValueError):
        pass


def _sync_rich_console_size(console: Any) -> None:
    """Refresh Rich ``Console`` dimensions from the TTY (resize / PTY ``setwinsize``).

    If ``COLUMNS`` / ``LINES`` were set when ``Console()`` was constructed, Rich keeps
    fixed ``_width`` / ``_height`` and never re-queries ``ioctl`` — stale layout after
    resize. Sync from ``os.get_terminal_size(sys.stdout)`` before each full redraw.

    Call this **after** restoring cooked line discipline for the paint (see
    ``_run_rich_pre_run_editor_loop``), matching the ``32d5820`` hand-off baseline.
    """
    try:
        wh = os.get_terminal_size(sys.stdout.fileno())
    except (OSError, AttributeError, ValueError):
        return
    try:
        console.size = (wh.columns, wh.lines)
    except Exception:
        pass


def _drain_stdin_burst(
    max_bytes: int = 256, idle_timeout: float = 0.05, fd: Optional[int] = None
) -> None:
    """Discard pending stdin bytes (tail of an unknown ESC / mouse / wheel sequence)."""
    import select

    use_fd = fd if fd is not None else _kbd_tty_fd_get()
    n = 0
    while n < max_bytes:
        r, _, _ = select.select([use_fd], [], [], idle_timeout)
        if not r:
            break
        chunk = os.read(use_fd, max_bytes - n)
        if not chunk:
            break
        n += len(chunk)


def _read_raw_key_impl(fd: int) -> str:
    """Read one logical key; caller must leave ``fd`` in raw mode."""
    import select

    def read_byte() -> str:
        chunk = os.read(fd, 1)
        if not chunk:
            return ""
        return chunk.decode("latin-1", errors="replace")

    def wait_byte(timeout: float) -> str:
        r, _, _ = select.select([fd], [], [], timeout)
        if not r:
            return ""
        chunk = os.read(fd, 1)
        if not chunk:
            return ""
        return chunk.decode("latin-1", errors="replace")

    ch = read_byte()
    if ch == "":
        return ""
    if ch == "\x04":
        return "ctrl_d"
    if ch == "\x1b":
        # Arrow keys use CSI (Control Sequence Introducer) bytes ESC [ … A/B or
        # SS3-style ESC O … A/B (historical "Single Shift 3" terminal encoding).
        # PTY tests in osx/tests/ drive this path under a pseudo-terminal (pexpect).
        # A short select after ESC mis-reads the prefix as lone Escape → false
        # "cancel". Use generous waits and full CSI tails (e.g. ESC [ 1 ; 3 B).
        ch2 = wait_byte(0.4)
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
                c = wait_byte(min(0.5, remaining))
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
                got = wait_byte(min(0.5, remaining))
                if got:
                    ch3 = got
            if ch3 == "A":
                return "up"
            if ch3 == "B":
                return "down"
            return "other"
        # Unknown ESC prefix (e.g. mouse / wheel `ESC [ < …`, `ESC ]`, `ESC >`).
        _drain_stdin_burst(fd=fd)
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


def read_raw_key() -> str:
    """Read one logical key; sets raw mode around the read (subprocess PTY tests)."""
    fd = _kbd_tty_fd_get()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return _read_raw_key_impl(fd)
    finally:
        _restore_terminal(fd, old)


def editor_row_keys(cfg: ResolvedConfig) -> List[str]:
    keys: List[str] = ["mode"]
    if cfg.mode == "fixed":
        keys.extend(["x", "y"])
    elif cfg.mode == "learn_collect":
        keys.append("learn_point_cap")
        return keys
    keys.extend(["count", "delay"])
    return keys


def _debug_tui_env_enabled() -> bool:
    v = os.environ.get("MACOS_MOUSE_CLICK_DEBUG_TUI", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _debug_tui_log_path() -> Optional[str]:
    p = os.environ.get("MACOS_MOUSE_CLICK_DEBUG_TUI_LOG", "").strip()
    return p if p else None


def _debug_tui_ts_wall() -> str:
    """Wall time for TUI debug lines: ISO-8601 with ms and a numeric UTC offset."""
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


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
    # Log file: one JSON object per line (``jq``-friendly). Stderr: ``ts_wall``, a space,
    # then ``MACOS_MOUSE_CLICK_TUI_STATE `` + same JSON (``ts_wall`` / ``ts_mono_ns`` in body).
    ts_wall = _debug_tui_ts_wall()
    ts_mono_ns = time.monotonic_ns()
    body: Dict[str, Any] = dict(payload)
    body["ts_wall"] = ts_wall
    body["ts_mono_ns"] = ts_mono_ns
    raw = json.dumps(body, separators=(",", ":")) + "\n"
    sys.stderr.write(f"{ts_wall} {_DEBUG_TUI_STATE_PREFIX}{raw}")
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

    Stderr uses ``<ts_wall> MACOS_MOUSE_CLICK_TUI_STATE `` + JSON (``ts_wall`` and
    ``ts_mono_ns`` are in the JSON too); the optional log file stores **JSON only**
    (one compact object per line) so tools like ``jq`` work
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


def _debug_tui_emit_show_target(
    cfg: ResolvedConfig, x: float, y: float
) -> None:
    """Plan-021: one record per show-only invocation (warp + overlay)."""
    if not _debug_tui_env_enabled():
        return
    body: Dict[str, Any] = {
        "event": "show_target",
        "mode": cfg.mode,
        "anchor_x": float(x),
        "anchor_y": float(y),
        "would_click": int(cfg.count),
        "show_dwell_seconds": float(cfg.show_dwell_seconds),
        "show_step": bool(cfg.show_step),
    }
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
    if key == "learn_point_cap":
        cap = cfg.learn_point_cap
        return "Max points", "infinite" if cap is None else str(cap)
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
    if key == "learn_point_cap":
        return cfg.sources.get("learn_point_cap", "default")
    return cfg.sources.get(key, "default")


def _apply_row_reset(cfg: ResolvedConfig, key: str) -> None:
    if key == "mode":
        cfg.set_field("mode", "learn", "default")
        cfg.x = None
        cfg.y = None
        for k in ("x", "y"):
            cfg.sources.pop(k, None)
        cfg.set_field("learn_point_cap", None, "default")
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
        return
    if key == "learn_point_cap":
        cfg.set_field("learn_point_cap", None, "default")
        return


def _prompt_cooked(console: Any, prompt: str) -> str:
    fd = _kbd_tty_fd_get()
    raw_attrs = termios.tcgetattr(fd)
    cooked = _rich_editor_tty_cooked_attrs
    try:
        if cooked is not None:
            termios.tcsetattr(fd, termios.TCSADRAIN, cooked)
        # Older Rich: Console.input() has no highlight= kwarg; omit for compatibility.
        return console.input(prompt).strip()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, raw_attrs)


def _edit_row(console: Any, cfg: ResolvedConfig, key: str) -> None:
    from rich.panel import Panel
    from rich.text import Text

    if key == "mode":
        old_mode = cfg.mode
        console.print(
            Panel(
                "[cyan]Enter mode[/]: [bold]learn[/] | [bold]fixed[/] | [bold]at-cursor[/] "
                "| [bold]learn-collect[/]",
                title="Edit mode",
                border_style="cyan",
            )
        )
        raw = _prompt_cooked(
            console,
            "Mode [learn/fixed/at-cursor/learn-collect, default learn]: ",
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
        elif raw in ("learn-collect", "learn_collect", "collect", "lc", "4"):
            cfg.set_field("mode", "learn_collect", "tui")
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
            cfg.sources.pop("learn_point_cap", None)
            apply_defaults(cfg)
        return
    if key == "learn_point_cap":
        cur = "0" if cfg.learn_point_cap is None else str(cfg.learn_point_cap)
        raw = _prompt_cooked(
            console,
            f"Max sample points (0=infinite) [{cur}]: ",
        )
        if raw == "":
            return
        try:
            v = int(raw, 10)
        except ValueError:
            console.print(Text(f"Invalid integer: {raw!r}", style="red"))
            return
        if v < 0:
            console.print(Text("Value must be >= 0", style="red"))
            return
        if v == 0:
            cfg.set_field("learn_point_cap", None, "tui")
        else:
            cfg.set_field("learn_point_cap", v, "tui")
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
    # Default ``Table``/``Panel`` (same box/padding as ``32d5820``). DEF-010: if any cell
    # wraps, Rich pads every cell in that row to the same height (blank “spacer” lines
    # between borders). ``no_wrap`` + ellipsis on **all** columns prevents that without
    # changing the inner box style (``ROUNDED``) or zero padding experiments.
    from rich.table import Table
    from rich.text import Text

    table = Table(show_header=True, header_style="bold cyan", expand=True)
    _nw = {"no_wrap": True, "overflow": "ellipsis"}
    table.add_column("Setting", style="white", **_nw)
    table.add_column("Value", style="green", **_nw)
    table.add_column("Source", style="dim", **_nw)
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


def _tui_bump_selected_for_arrow_key(selected: int, key: str, n_rows: int) -> int:
    """Return ``selected`` after one Up/Down in the Rich table (DEF-008 logging uses this)."""
    if key == "up":
        return max(0, selected - 1)
    if key == "down":
        return min(n_rows - 1, selected + 1)
    return selected


def run_rich_pre_run_editor(cfg: ResolvedConfig, _rich: Any) -> bool:
    """TTY review/edit. Returns True to run clicks, False if user cancelled."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text

    global _rich_editor_tty_cooked_attrs

    _reset_debug_tui_log_sink()
    console = Console()
    row_keys = editor_row_keys(cfg)
    selected = 0

    fd_in = _kbd_tty_fd_get()
    _rich_editor_tty_cooked_attrs = termios.tcgetattr(fd_in)
    try:
        # Raw mode only around ``_read_raw_key_impl`` (see loop). Persistent raw across
        # ``console.clear`` / ``print`` regressed layout vs. ``32d5820`` (hand-off).
        return _run_rich_pre_run_editor_loop(
            cfg, console, row_keys, selected, fd_in
        )
    finally:
        if _rich_editor_tty_cooked_attrs is not None:
            termios.tcsetattr(fd_in, termios.TCSADRAIN, _rich_editor_tty_cooked_attrs)
            _rich_editor_tty_cooked_attrs = None


def _run_rich_pre_run_editor_loop(
    cfg: ResolvedConfig,
    console: Any,
    row_keys: List[str],
    selected: int,
    fd_in: int,
) -> bool:
    from rich.panel import Panel
    from rich.text import Text

    while True:
        if not row_keys:
            row_keys = editor_row_keys(cfg)
        selected = max(0, min(selected, len(row_keys) - 1))
        cooked = _rich_editor_tty_cooked_attrs
        if cooked is not None:
            termios.tcsetattr(fd_in, termios.TCSANOW, cooked)
        _sync_rich_console_size(console)
        table = _build_editor_table(cfg, row_keys, selected)
        console.clear()
        _flush_stdout_safe()
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
        # DEF-009: ``_debug_tui_emit`` writes ``MACOS_MOUSE_CLICK_TUI_STATE`` on stderr.
        # If stdout is still buffered, stderr can interleave mid-frame and garble Panel/Table
        # box drawing on a single TTY. Flush the Rich frame to the kernel first.
        _flush_stdout_safe()
        _debug_tui_emit(cfg, row_keys, selected, event="draw")
        _tty_setraw_now(fd_in)
        key = _read_raw_key_impl(fd_in)
        if key in ("up", "down"):
            selected = _tui_bump_selected_for_arrow_key(
                selected, key, len(row_keys)
            )
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
            if cfg.delay < 0 or (
                cfg.mode != "learn_collect" and cfg.count < 0
            ):
                console.print(Text("Count and delay must be >= 0.", style="red"))
                time.sleep(1.2)
                continue
            return True
        if key == "r":
            rk = row_keys[selected]
            _apply_row_reset(cfg, rk)
            row_keys = editor_row_keys(cfg)
            continue
        if key == "enter":
            rk = row_keys[selected]
            if cooked is not None:
                termios.tcsetattr(fd_in, termios.TCSANOW, cooked)
            _sync_rich_console_size(console)
            console.clear()
            _edit_row(console, cfg, rk)
            row_keys = editor_row_keys(cfg)
            _prompt_cooked(console, "\nPress Enter to return to the editor…")
            continue
        if key in ("up", "down"):
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
  ./osx/macos_mouse_click.py --learn-points -Y
  ./osx/macos_mouse_click.py --learn-points 5 -Y
  ./osx/macos_mouse_click.py --interactive
  ./osx/macos_mouse_click.py -x 400 -y 300 -n 3 -Y

Install dependencies:
  python3 -m pip install pyobjc-framework-Quartz rich

Stop repeats: Ctrl+C   (Accessibility required for Terminal).
Optional --abort-on-mouse-move: arm near click target, then after at least one
synthetic click and a read within threshold of the target, stop if the cursor
later leaves beyond threshold (see README).
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
        "--learn-points",
        nargs="?",
        type=int,
        const=-1,
        default=argparse.SUPPRESS,
        metavar="N",
        help=(
            "Collect real click coordinates only (no synthetic clicks). "
            "Omit N for infinite samples until Ctrl+C; N>=1 stops after N points. "
            "With -Y, plain text on stdout; otherwise Rich-colored lines on stderr."
        ),
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
        "--abort-on-mouse-move",
        action="store_true",
        default=False,
        help=(
            "During synthetic repeat clicks, exit after armed: cursor must first be "
            "within --mouse-arm-radius-px of the click target, then after at least one "
            "synthetic click the read cursor must have been within "
            "--mouse-move-threshold-px of the target before a later read beyond that "
            "distance aborts (Euclidean; DEF-010, DEF-011)."
        ),
    )
    p.add_argument(
        "--mouse-move-threshold-px",
        type=float,
        default=argparse.SUPPRESS,
        metavar="PX",
        help=(
            "After armed, at least one synthetic click, and at least one read within "
            "this distance (px) of the click target, abort if a later read is farther "
            "(default: 20)."
        ),
    )
    p.add_argument(
        "--mouse-arm-radius-px",
        type=float,
        default=argparse.SUPPRESS,
        metavar="PX",
        help=(
            "With --abort-on-mouse-move: arm leave-target checks when the cursor is "
            "within this radius of the click target. Default: max(60, 2× threshold). "
            "Must be >= --mouse-move-threshold-px."
        ),
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
    p.add_argument(
        "--show-only",
        action="store_true",
        default=False,
        help=(
            "Plan-021 target tour: warp the cursor to the target and draw an "
            "AppKit overlay near it; do NOT post any synthetic mouse events. "
            "-n is rendered as a 'would click N' label only. Requires fixed "
            "(-x and -y) or --at-cursor mode."
        ),
    )
    p.add_argument(
        "--show-dwell-seconds",
        type=float,
        default=argparse.SUPPRESS,
        metavar="SECONDS",
        help=(
            "With --show-only: how long the overlay stays up before the script "
            "exits (default: 1.5). Must be >= 0. Ignored when --show-step is set."
        ),
    )
    p.add_argument(
        "--show-step",
        action="store_true",
        default=False,
        help=(
            "With --show-only: wait for Enter on stdin between targets instead "
            "of dwelling. Requires a TTY stdin."
        ),
    )
    return p


def argv_duplicate_cli_option_error(argv: Sequence[str]) -> Optional[str]:
    """Detect duplicate count/delay/x/y flags in raw argv (DEF-007).

    Scans tokens before a bare ``--``. Bundled forms such as ``-n5`` or
    ``--count=3`` each count as one occurrence. ``-n`` and ``--count`` share
    the same logical option.
    """
    counts = {
        "count": 0,
        "delay": 0,
        "x": 0,
        "y": 0,
        "learn_points": 0,
        "mouse_move_threshold_px": 0,
        "mouse_arm_radius_px": 0,
        "show_dwell_seconds": 0,
    }
    for tok in argv:
        if tok == "--":
            break
        if tok == "--learn-points" or tok.startswith("--learn-points="):
            counts["learn_points"] += 1
        elif tok in ("-n", "--count") or tok.startswith("--count="):
            counts["count"] += 1
        elif tok in ("-d", "--delay") or tok.startswith("--delay="):
            counts["delay"] += 1
        elif tok in ("-x", "--x") or tok.startswith("--x="):
            counts["x"] += 1
        elif tok in ("-y", "--y") or tok.startswith("--y="):
            counts["y"] += 1
        elif len(tok) > 2 and tok.startswith("-n"):
            rest = tok[2:]
            if rest.startswith("="):
                rest = rest[1:]
            try:
                int(rest, 10)
            except ValueError:
                pass
            else:
                counts["count"] += 1
        elif len(tok) > 2 and tok.startswith("-d"):
            rest = tok[2:]
            if rest.startswith("="):
                rest = rest[1:]
            try:
                float(rest)
            except ValueError:
                pass
            else:
                counts["delay"] += 1
        elif len(tok) > 2 and tok.startswith("-x"):
            rest = tok[2:]
            if rest.startswith("="):
                rest = rest[1:]
            try:
                float(rest)
            except ValueError:
                pass
            else:
                counts["x"] += 1
        elif len(tok) > 2 and tok.startswith("-y"):
            rest = tok[2:]
            if rest.startswith("="):
                rest = rest[1:]
            try:
                float(rest)
            except ValueError:
                pass
            else:
                counts["y"] += 1
        elif tok == "--mouse-move-threshold-px" or tok.startswith(
            "--mouse-move-threshold-px="
        ):
            counts["mouse_move_threshold_px"] += 1
        elif tok == "--mouse-arm-radius-px" or tok.startswith("--mouse-arm-radius-px="):
            counts["mouse_arm_radius_px"] += 1
        elif tok == "--show-dwell-seconds" or tok.startswith("--show-dwell-seconds="):
            counts["show_dwell_seconds"] += 1
    if counts["count"] > 1:
        return "-n / --count may only appear once"
    if counts["delay"] > 1:
        return "-d / --delay may only appear once"
    if counts["x"] > 1:
        return "-x / --x may only appear once"
    if counts["y"] > 1:
        return "-y / --y may only appear once"
    if counts["learn_points"] > 1:
        return "--learn-points may only appear once"
    if counts["mouse_move_threshold_px"] > 1:
        return "--mouse-move-threshold-px may only appear once"
    if counts["mouse_arm_radius_px"] > 1:
        return "--mouse-arm-radius-px may only appear once"
    if counts["show_dwell_seconds"] > 1:
        return "--show-dwell-seconds may only appear once"
    return None


def validate_ns(ns: argparse.Namespace) -> Optional[str]:
    vd = vars(ns)
    learn = vd.get("learn", False)
    atc = vd.get("at_cursor", False)
    has_x = "x" in vd
    has_y = "y" in vd
    learn_pts = "learn_points" in vd
    if learn_pts:
        lpv = vd["learn_points"]
        if lpv != -1 and lpv < 1:
            return "Invalid --learn-points N (use N >= 1, or omit N for infinite)"
    if has_x ^ has_y:
        return "Both -x and -y are required together for fixed mode"
    n_modes = sum([bool(learn), bool(atc), bool(has_x and has_y), learn_pts])
    if n_modes > 1:
        return (
            "Use only one of --learn, --learn-points, --at-cursor, or -x with -y"
        )
    show_only = bool(vd.get("show_only", False))
    show_step = bool(vd.get("show_step", False))
    has_show_dwell = "show_dwell_seconds" in vd
    if show_only:
        # Plan-021: show-only is preview-only; learn / learn-collect already do not click.
        if learn or learn_pts:
            return (
                "--show-only cannot be combined with --learn or --learn-points "
                "(use fixed -x/-y or --at-cursor)"
            )
        if not (atc or (has_x and has_y)):
            return (
                "--show-only requires fixed (-x and -y) or --at-cursor mode"
            )
        if has_show_dwell:
            sds = vd["show_dwell_seconds"]
            if sds < 0:
                return "--show-dwell-seconds must be >= 0"
    else:
        if has_show_dwell:
            return "--show-dwell-seconds requires --show-only"
        if show_step:
            return "--show-step requires --show-only"
    return None


def mode_fully_on_cli(ns: argparse.Namespace) -> bool:
    vd = vars(ns)
    return bool(
        vd.get("learn")
        or vd.get("at_cursor")
        or ("x" in vd and "y" in vd)
        or ("learn_points" in vd)
    )


def namespace_to_cfg(ns: argparse.Namespace) -> ResolvedConfig:
    vd = vars(ns)
    cfg = ResolvedConfig(
        assume_yes=bool(vd.get("assume_yes", False)),
        used_interactive=bool(vd.get("interactive", False)),
    )
    if vd.get("learn"):
        cfg.set_field("mode", "learn", "cli")
    elif "learn_points" in vd:
        lpv = int(vd["learn_points"])
        cfg.set_field("mode", "learn_collect", "cli")
        if lpv == -1:
            cfg.set_field("learn_point_cap", None, "cli")
        else:
            cfg.set_field("learn_point_cap", lpv, "cli")
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
    if vd.get("abort_on_mouse_move"):
        cfg.set_field("abort_on_mouse_move", True, "cli")
    if "mouse_move_threshold_px" in vd:
        cfg.set_field(
            "mouse_move_threshold_px", float(vd["mouse_move_threshold_px"]), "cli"
        )
    if "mouse_arm_radius_px" in vd:
        cfg.set_field("mouse_arm_radius_px", float(vd["mouse_arm_radius_px"]), "cli")
    if vd.get("show_only"):
        cfg.set_field("show_only", True, "cli")
    if "show_dwell_seconds" in vd:
        cfg.set_field("show_dwell_seconds", float(vd["show_dwell_seconds"]), "cli")
    if vd.get("show_step"):
        cfg.set_field("show_step", True, "cli")
    return cfg


def prompt_str(label: str, default: str) -> str:
    raw = input(f"{label} [{default}]: ").strip()
    return default if raw == "" else raw


def prompt_mode_interactive() -> str:
    print(
        "Select mode:\n"
        "  1) learn — first real left click sets anchor\n"
        "  2) fixed — use X and Y coordinates\n"
        "  3) at-cursor — anchor is mouse position when clicking starts\n"
        "  4) learn-collect — record click coordinates only (no synthetic clicks)",
        file=sys.stderr,
    )
    choice = prompt_str("Choice", "1").lower()
    if choice in ("1", "learn", "l", ""):
        return "learn"
    if choice in ("2", "fixed", "f"):
        return "fixed"
    if choice in ("3", "at-cursor", "at_cursor", "a", "c"):
        return "at_cursor"
    if choice in ("4", "learn-collect", "learn_collect", "collect", "lc"):
        return "learn_collect"
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

    if cfg.mode == "learn_collect" and "learn_point_cap" not in cfg.sources:
        raw = prompt_str("Max sample points (0=infinite)", "0").strip()
        try:
            v = int(raw, 10)
        except ValueError:
            print(f"Invalid integer: {raw!r}", file=sys.stderr)
            sys.exit(2)
        if v < 0:
            print("Value must be >= 0", file=sys.stderr)
            sys.exit(2)
        if v == 0:
            cfg.set_field("learn_point_cap", None, "prompt")
        else:
            cfg.set_field("learn_point_cap", v, "prompt")

    if cfg.mode != "learn_collect" and "count" not in cfg.sources:
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


def _dist_sq(ax: float, ay: float, bx: float, by: float) -> float:
    dx, dy = ax - bx, ay - by
    return dx * dx + dy * dy


def _effective_mouse_arm_radius_px(cfg: ResolvedConfig, threshold_px: float) -> float:
    """Radius within click target to arm leave-target detection (DEF-010)."""
    if cfg.mouse_arm_radius_px is not None:
        return float(cfg.mouse_arm_radius_px)
    return max(60.0, 2.0 * float(threshold_px))


def apply_defaults(cfg: ResolvedConfig) -> None:
    if not cfg.mode:
        return
    if cfg.mode == "learn_collect":
        if "learn_point_cap" not in cfg.sources:
            cfg.set_field("learn_point_cap", None, "default")
        if "delay" not in cfg.sources:
            cfg.set_field("delay", 5.0, "default")
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
    if cfg.mode == "learn_collect":
        cap = cfg.learn_point_cap
        cap_s = "infinite" if cap is None else str(cap)
        print(
            f"  learn_point_cap = {cap_s}  "
            f"({cfg.sources.get('learn_point_cap', 'default')})",
            file=sys.stderr,
        )
    else:
        print(
            f"  count         = {count_label(cfg.count)}  "
            f"({cfg.sources.get('count', 'default')})",
            file=sys.stderr,
        )
    print(
        f"  delay (s)     = {cfg.delay}  ({cfg.sources.get('delay', 'default')})",
        file=sys.stderr,
    )
    if cfg.mode != "learn_collect":
        print(
            f"  abort_on_mouse_move = {cfg.abort_on_mouse_move}  "
            f"({cfg.sources.get('abort_on_mouse_move', 'default')})",
            file=sys.stderr,
        )
        print(
            f"  mouse_move_threshold_px = {cfg.mouse_move_threshold_px}  "
            f"({cfg.sources.get('mouse_move_threshold_px', 'default')})",
            file=sys.stderr,
        )
        eff_arm = _effective_mouse_arm_radius_px(
            cfg, float(cfg.mouse_move_threshold_px)
        )
        arm_src = cfg.sources.get("mouse_arm_radius_px", "computed")
        print(
            f"  mouse_arm_radius_px (effective) = {eff_arm}  ({arm_src})",
            file=sys.stderr,
        )
        if cfg.show_only:
            print(
                f"  show_only     = {cfg.show_only}  "
                f"({cfg.sources.get('show_only', 'default')})",
                file=sys.stderr,
            )
            print(
                f"  show_dwell_seconds = {cfg.show_dwell_seconds}  "
                f"({cfg.sources.get('show_dwell_seconds', 'default')})",
                file=sys.stderr,
            )
            print(
                f"  show_step     = {cfg.show_step}  "
                f"({cfg.sources.get('show_step', 'default')})",
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


def run_synthetic_loop(qz: Any, x: float, y: float, count: int, delay: float, cfg: ResolvedConfig) -> int:
    infinite = count == 0
    n_done = 0
    abort_mouse = cfg.abort_on_mouse_move
    thr = float(cfg.mouse_move_threshold_px)
    arm_r = _effective_mouse_arm_radius_px(cfg, thr) if abort_mouse else 0.0
    thr_sq = thr * thr
    arm_sq = arm_r * arm_r
    armed = False
    ever_within_thr = False
    while True:
        if shutdown_requested():
            print("Stopped.", file=sys.stderr)
            return 130
        if abort_mouse:
            cx, cy = get_mouse_location(qz)
            d_sq = _dist_sq(cx, cy, float(x), float(y))
            if not armed and d_sq <= arm_sq:
                armed = True
            if armed and d_sq <= thr_sq:
                ever_within_thr = True
            # DEF-011: (1) do not evaluate "leave" until at least one click has been
            # posted (annulus arm_r > thr on same sample before first click).
            # (2) do not treat as "leave" until the read cursor has been within
            # threshold of the target at least once; otherwise the next iteration
            # still sees the prior row / stale position while n_done > 0 (buy ladder).
            if armed and n_done > 0 and ever_within_thr and d_sq > thr_sq:
                request_shutdown()
                print(
                    "Stopped (cursor moved away from click target beyond "
                    "--mouse-move-threshold-px).",
                    file=sys.stderr,
                )
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


_LEARN_COLLECT_DRY_FAKE: List[Tuple[float, float]] = [
    (111.0, 222.0),
    (333.25, 444.5),
    (10.0, 20.0),
]
_LEARN_COLLECT_LINE_STYLES = ("green", "yellow", "magenta", "cyan")


def learn_collect_plain_text_line(index: int, x: float, y: float) -> str:
    return f"{index} {x:.4f} {y:.4f}"


def emit_learn_collect_dry_run_stdout_samples(cfg: ResolvedConfig) -> None:
    """Deterministic stdout lines for ``learn_collect`` dry-run (tests / CI)."""
    cap = cfg.learn_point_cap
    if cap is None:
        n_out = len(_LEARN_COLLECT_DRY_FAKE)
    else:
        n_out = min(cap, 50)
    for i in range(n_out):
        x, y = _LEARN_COLLECT_DRY_FAKE[i % len(_LEARN_COLLECT_DRY_FAKE)]
        print(learn_collect_plain_text_line(i + 1, x, y), flush=True)


def run_learn_collect_flow(qz: Any, cfg: ResolvedConfig) -> int:
    """Record real left clicks; plain stdout with -Y, else Rich-colored stderr."""
    cap = cfg.learn_point_cap
    n = 0
    while True:
        if shutdown_requested():
            print("Stopped.", file=sys.stderr)
            return 130
        if cap is not None and n >= cap:
            return 0
        print(
            "Waiting for next left click (Ctrl+C to stop)…",
            file=sys.stderr,
            flush=True,
        )
        pt = wait_for_anchor_click(qz)
        if pt is False:
            return 2
        if pt is None:
            if shutdown_requested():
                print("Stopped.", file=sys.stderr)
                return 130
            print("Error: no anchor click received.", file=sys.stderr)
            return 2
        n += 1
        x, y = float(pt[0]), float(pt[1])
        line = learn_collect_plain_text_line(n, x, y)
        if cfg.assume_yes:
            print(line, flush=True)
        else:
            from rich.console import Console

            st = _LEARN_COLLECT_LINE_STYLES[(n - 1) % len(_LEARN_COLLECT_LINE_STYLES)]
            Console(stderr=True).print(f"[{st}]{line}[/]")
        if cap is not None and n >= cap:
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
    return run_synthetic_loop(qz, x, y, cfg.count, cfg.delay, cfg)


def run_show_only_loop(qz: Any, x: float, y: float, cfg: ResolvedConfig) -> int:
    """Plan-021: warp to (x, y) and draw the AppKit overlay; never click."""
    _debug_tui_emit_show_target(cfg, x, y)
    warp_cursor(qz, float(x), float(y))
    show_target_overlay(
        float(x),
        float(y),
        int(cfg.count),
        float(cfg.show_dwell_seconds),
        bool(cfg.show_step),
    )
    if shutdown_requested():
        return 130
    return 0


def run_fixed_or_cursor_flow(qz: Any, cfg: ResolvedConfig) -> int:
    if cfg.mode == "at_cursor":
        x, y = get_mouse_location(qz)
        cur_msg = f"Cursor position recorded at ({x:.1f}, {y:.1f})."
        _debug_tui_emit_anchor(cfg, x, y, cur_msg)
    else:
        x, y = float(cfg.x), float(cfg.y)
    if cfg.show_only:
        return run_show_only_loop(qz, x, y, cfg)
    return run_synthetic_loop(qz, x, y, cfg.count, cfg.delay, cfg)


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    dup_err = argv_duplicate_cli_option_error(argv)
    if dup_err:
        print(f"Error: {dup_err}", file=sys.stderr)
        return 2
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
            "Error: -Y/--yes requires --learn, --learn-points, --at-cursor, "
            "or both -x and -y on the command line.",
            file=sys.stderr,
        )
        return 2

    cfg = namespace_to_cfg(ns)
    rich_mod = try_import_rich()
    can_tui = tty_can_use_rich_editor(cfg) and rich_mod is not None

    if tty_can_use_rich_editor(cfg) and rich_mod is None:
        print(
            "Tip: install rich for a colored TTY editor.\n"
            "  Setup recommended: make -C osx setup\n"
            "  Or install directly: python3 -m pip install rich",
            file=sys.stderr,
        )

    if cfg.used_interactive and not can_tui:
        run_interactive_prompts(cfg)

    if cfg.mode == "" and not can_tui:
        print(
            "Error: specify --learn, --learn-points, --at-cursor, or both -x and -y, "
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

    if cfg.mode != "learn_collect" and cfg.count < 0:
        print("Error: count must be >= 0", file=sys.stderr)
        return 2
    if cfg.delay < 0:
        print("Error: delay must be >= 0", file=sys.stderr)
        return 2
    if cfg.abort_on_mouse_move and cfg.mouse_move_threshold_px <= 0:
        print(
            "Error: --mouse-move-threshold-px must be > 0 when --abort-on-mouse-move is set.",
            file=sys.stderr,
        )
        return 2
    if cfg.abort_on_mouse_move:
        arm_r = _effective_mouse_arm_radius_px(cfg, float(cfg.mouse_move_threshold_px))
        if arm_r <= 0:
            print(
                "Error: effective --mouse-arm-radius-px must be > 0.",
                file=sys.stderr,
            )
            return 2
        if arm_r < float(cfg.mouse_move_threshold_px):
            print(
                "Error: --mouse-arm-radius-px must be >= --mouse-move-threshold-px "
                "(arm region must contain the leave threshold).",
                file=sys.stderr,
            )
            return 2

    if not cfg.assume_yes and not can_tui:
        print_confirmation_sheet(cfg)
        if not confirm_or_abort():
            print("Cancelled.", file=sys.stderr)
            return 0

    if can_tui:
        from rich.console import Console

        Console(stderr=True).print(f"[green]Running:[/] {_running_message(cfg)}")
    else:
        print(f"Running: {_running_message(cfg)}", file=sys.stderr)

    if not can_tui:
        _reset_debug_tui_log_sink()
    _debug_tui_emit_run(cfg)

    if dry_run_after_start_requested(ns):
        emit_dry_run_json_line(cfg)
        if cfg.mode == "learn_collect":
            emit_learn_collect_dry_run_stdout_samples(cfg)
        return 0

    qz = import_quartz()
    install_signal_handlers()
    reset_shutdown()

    try:
        if cfg.mode == "learn":
            return run_learn_flow(qz, cfg)
        if cfg.mode == "learn_collect":
            return run_learn_collect_flow(qz, cfg)
        return run_fixed_or_cursor_flow(qz, cfg)
    except KeyboardInterrupt:
        print("Stopped.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
