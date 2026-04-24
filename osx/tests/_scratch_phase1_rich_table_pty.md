# Phase 1 scratch: Rich table Down PTY (2026-04)

**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).

Runtime notes from `test_rich_table_nav_down_pty.py` on darwin (local venv pytest).

## Observed

- `test_read_raw_key_*` subprocess PTY runners (CSI/SS3 Down and new Up) **pass**:
  `read_raw_key()` returns `down` / `up` after slow final byte.
- Rich table tests: after `child.send("\x1b[B")` and draining up to ~12s waiting for
  bold `Count` in the Setting column, highlight often stayed **`Mode`**, or the
  accumulated transcript was **footer-only** (no table row lines), suggesting
  either the Down key is not consumed as navigation in this harness, or
  `console.clear()` + redraw split reads so our parser never sees the new frame.

## Hypotheses (for Phase 3)

1. Rich `Console.print` / `clear` leaves stdin discipline incompatible with
   `read_raw_key` until an explicit `tty.setraw` refresh (investigate order vs
   `_tmp_tty_probe.py` ICANON checks).
2. pexpect `read_nonblocking` coalescing: need a dedicated PTY child runner
   (like CSI runner) driving `macos_mouse_click.py` from the parent `os.write`
   side instead of pexpect for arrow bytes.
3. Parser should key off a Phase 2 `MACOS_MOUSE_CLICK_TUI_STATE` line instead
   of ANSI bold alone.

## Policy

Keep this file until the user signs off Phase 3 / cleanup per plan Agent workflow.
