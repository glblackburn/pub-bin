# Plan 011 — Code review archive (`macos_mouse_click.py`)

**Status:** **Closed (archive)** — Read-only code review snapshot; **not** a normative product spec. **No open follow-up** in this document (optional maintainer polish only).

**Summary:** Archived review of [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py) as of 2026-05-02. Canonical copy lives in this repository; do not rely on `~/.cursor/plans/` alone.

## Role

Single-file CLI (~1737 lines) for **synthetic left clicks** on macOS via **Quartz (PyObjC)**, with modes: **learn** (event tap for first real click), **fixed** `-x/-y`, **at-cursor**, **learn-collect** (`--learn-points`). Optional **Rich** pre-run TTY table, **`MACOS_MOUSE_CLICK_DRY_RUN`** / `--dry-run-after-start` for CI, **abort-on-mouse-move** (DEF-010/011), and extensive **TUI debug** (`MACOS_MOUSE_CLICK_DEBUG_TUI`). Documented cross-links: [`docs/osx/README.md`](../README.md), plans under this directory.

## Architecture (high level)

```mermaid
flowchart LR
  CLI[argparse argv]
  CFG[ResolvedConfig]
  TUI[Rich pre-run editor]
  DRY[dry-run JSON exit]
  QZ[import_quartz]
  FLOWS[learn / learn_collect / fixed_or_cursor]
  LOOP[run_synthetic_loop]
  CLI --> CFG
  CFG --> TUI
  CFG --> DRY
  CFG --> QZ
  QZ --> FLOWS
  FLOWS --> LOOP
```

- **Config**: `ResolvedConfig` + `namespace_to_cfg` / `apply_defaults` / source tracking for TUI styling.
- **I/O**: Lazy `/dev/tty` FD for raw keys; `termios`/`tty` split from `sys.stdin` to work with PTY/Rich; `_tty_setraw_now` uses `TCSANOW` to avoid flushing pexpect bytes (documented).
- **Safety**: `install_signal_handlers` + `sleep_interruptible`; learn tap disables on shutdown.

## Strengths

- **Lazy Quartz** — import only after dry-run path; clear `import_quartz()` error message and exit code 2.
- **Operator ergonomics** — `-Y`/`--yes` vs `-y` coordinate called out in docstring and argparse; duplicate-flag scan (`argv_duplicate_cli_option_error`) for DEF-007.
- **TUI robustness** — CSI/SS3 arrow handling with deadlines and `_drain_stdin_burst` for ambiguous ESC; stdout flush before stderr debug (DEF-009); Rich console size sync after resize (`_sync_rich_console_size`).
- **Mouse-move abort** — state machine in `run_synthetic_loop` matches documented semantics (arm radius, threshold, `n_done` / `ever_within_thr` gating).
- **Testability** — dry-run JSON shape via `resolved_config_for_dry_run_json`; learn-collect dry fake stdout; repo has PTY tests under `osx/tests/`.

## Risks / edge cases (informational)

- **`wait_for_anchor_click`**: If `CGEventTapCreate` succeeds but run loop never delivers (unusual), behavior relies on shutdown or anchor; tap/source removal in `finally` is correct for normal paths.
- **`read_raw_key` vs `_read_raw_key_impl`**: `read_raw_key` uses `tty.setraw` (default may be `TCSAFLUSH` in some Python versions)—loop uses `_tty_setraw_now` intentionally; worth knowing if anything still calls `read_raw_key` on paths that need the non-flush behavior (loop uses `_read_raw_key_impl` after `_tty_setraw_now`).
- **Globals**: `_kbd_tty_fd`, `_rich_editor_tty_cooked_attrs`, shutdown flag—fine for a CLI single process; would matter if imported as a library (not the intended use).
- **`_sync_rich_console_size`**: Broad `except Exception` swallows unexpected errors silently (acceptable for best-effort UI).

## Code quality

- Module docstring and DEF/plan references aid maintenance.
- Typing is pragmatic (`Any` for Quartz/Rich); dataclass for config is clear.
- Structure is long but sectioned by concern.

## Follow-up

None from this review unless the maintainer requests refactors, new flags, bugfixes, or test gaps.

---

## Closure (repository)

This archive is **complete**. Do not treat it as a backlog. New work belongs in the owning **plan-###** or a defect file, not in follow-up edits to plan-011.
