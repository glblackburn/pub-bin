#!/usr/bin/env python3
"""
macos_mouse_click.py — synthetic left clicks on macOS via Quartz (PyObjC).

The shebang (#!/usr/bin/env python3) allows running without typing python3,
e.g. ./osx/macos_mouse_click.py --help after: chmod +x osx/macos_mouse_click.py

Requires: Python 3.9+, pyobjc-framework-Quartz
  python3 -m pip install pyobjc-framework-Quartz

Permissions: System Settings → Privacy & Security → Accessibility for the
terminal (or app) running this script. Screen Recording is not required.

Stop automated clicking: Ctrl+C (SIGINT) or kill -INT/-TERM <pid>.

Coordinates are Quartz global display points (logical points); multi-monitor
layouts can shift expected positions.

Anchor click in --learn: the user's first left mousedown is passed through to
the OS (not swallowed) while we record its location.

Non-interactive automation: use -Y/--yes (not -y, which is the Y coordinate).
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

Quartz: Any = None


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

Install dependency:
  python3 -m pip install pyobjc-framework-Quartz

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
        help="Prompt for missing options (stdin must be a TTY)",
    )
    p.add_argument(
        "-Y",
        "--yes",
        action="store_true",
        dest="assume_yes",
        default=False,
        help="Skip prompts and confirmation; mode must be fully on CLI",
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
    print(
        f"Anchor recorded at ({x:.1f}, {y:.1f}). Warmup: sleeping {cfg.delay}s…",
        file=sys.stderr,
    )
    sleep_interruptible(cfg.delay)
    if shutdown_requested():
        print("Stopped.", file=sys.stderr)
        return 130
    return run_synthetic_loop(qz, x, y, cfg.count, cfg.delay)


def run_fixed_or_cursor_flow(qz: Any, cfg: ResolvedConfig) -> int:
    if cfg.mode == "at_cursor":
        x, y = get_mouse_location(qz)
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

    if cfg.used_interactive:
        run_interactive_prompts(cfg)

    if cfg.mode == "":
        print(
            "Error: specify --learn, --at-cursor, or both -x and -y, "
            "or use --interactive.",
            file=sys.stderr,
        )
        return 2

    if cfg.mode == "fixed" and (cfg.x is None or cfg.y is None):
        print("Error: fixed mode requires both x and y.", file=sys.stderr)
        return 2

    apply_defaults(cfg)

    if cfg.count < 0:
        print("Error: count must be >= 0", file=sys.stderr)
        return 2
    if cfg.delay < 0:
        print("Error: delay must be >= 0", file=sys.stderr)
        return 2

    if not cfg.assume_yes:
        print_confirmation_sheet(cfg)
        if not confirm_or_abort():
            print("Cancelled.", file=sys.stderr)
            return 0

    if cfg.assume_yes:
        print(
            f"Running: mode={cfg.mode} count={count_label(cfg.count)} delay={cfg.delay}s",
            file=sys.stderr,
        )

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
