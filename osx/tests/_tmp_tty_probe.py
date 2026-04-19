"""Scratch probe: Rich Console.print vs tty attrs (ICANON/ECHO).

Not collected by pytest (name is not test_*.py). Keep in the tree until the
owning phase is signed off and the user requests cleanup—see
docs/plans/agent/new-test-up-down-navigation.plan.md (Agent workflow).
"""
import os
import sys
import termios

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

fd = sys.stdin.fileno()
print("isatty", os.isatty(fd), file=sys.stderr)
old = termios.tcgetattr(fd)
try:
    t = Table()
    t.add_column("A")
    t.add_row("x")
    Console().print(Panel(t))
    a = termios.tcgetattr(fd)
    print("ICANON after rich", bool(a[3] & termios.ICANON), file=sys.stderr)
    print("ECHO after rich", bool(a[3] & termios.ECHO), file=sys.stderr)
finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old)
