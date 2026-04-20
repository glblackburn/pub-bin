<!-- Cursor agent plan (canonical copy in-repo; do not use ~/.cursor/plans/). -->
---
todos:
  - id: "test-paths-subprocess"
    content: "Consolidate OSX_DIR/REPO_ROOT/SCRIPT_PATH and subprocess runner helper under osx/tests/; migrate conftest, pty_harness, test_read_raw_key_csi, test_dry_run"
    status: pending
  - id: "csi-runner-dry"
    content: "Merge _inject_csi_down/_inject_ss3_down in csi_pty_child_runner.py; run CSI pytest module"
    status: pending
  - id: "read-raw-key-helpers"
    content: "Extract shared stdin wait + deadline loop helpers in macos_mouse_click.read_raw_key; keep semantics identical"
    status: pending
  - id: "editor-pause-start"
    content: "Add _pause_error (or similar) and shared can_start_clicking / fixed_anchor validation for editor S-key and main()"
    status: pending
  - id: "row-metadata-registry"
    content: "Optional: replace parallel if key== chains with table/registry for _row_display, _field_source, _apply_row_reset, _edit_row"
    status: pending
  - id: "optional-package-split"
    content: "Defer: split macos_mouse_click.py into submodules only if team wants package layout"
    status: pending
isProject: false
---
# DRY / refactor opportunities (osx)

## Scope

Primary focus: [`osx/macos_mouse_click.py`](../../../../osx/macos_mouse_click.py) (single large module) and [`osx/tests/`](../../../../osx/tests/). Implementation order should go **tests/helpers first**, then **pure helpers**, then **behavior-sensitive** refactors with existing pytest coverage.

## 1. Test layout and subprocess DRY

**Duplication:** Path constants and repo/script resolution appear in three places:

- [`osx/tests/conftest.py`](../../../../osx/tests/conftest.py): `OSX_DIR`, `REPO_ROOT`, `SCRIPT_PATH` + `sys.path` insertion
- [`osx/tests/pty_harness.py`](../../../../osx/tests/pty_harness.py): same trio + `base_child_env`
- [`osx/tests/test_read_raw_key_csi.py`](../../../../osx/tests/test_read_raw_key_csi.py): local `OSX_DIR` only for `PYTHONPATH` / `cwd`

[`osx/tests/test_dry_run.py`](../../../../osx/tests/test_dry_run.py) defines `_run_script(repo_root, script_path, argv, extra_env)` (subprocess + env merge), overlapping conceptually with CSI tests’ `_run_runner` pattern.

**Refactor direction:**

- Single canonical module (e.g. `osx/tests/paths.py` or extend `pty_harness.py`) exporting `osx_dir`, `repo_root`, `script_path`, and optionally `ensure_osx_on_path()`.
- One `run_script_subprocess(...)` helper (fixtures pass paths; default `PYTHONUNBUFFERED`, `cwd`, `timeout`) used by `test_dry_run` and `test_read_raw_key_csi`; keep `pexpect`-specific logic in `pty_harness` only.

**Risk:** Low (tests only).

## 2. PTY CSI runner injection (`csi_pty_child_runner.py`)

**Duplication:** `_inject_csi_down` and `_inject_ss3_down` differ only by the middle byte (`[` vs `O`) and final `B`; structure (sleep, ESC, `_INTER_ESC`, middle, `_GAP`, final) is identical.

**Refactor direction:** One `_inject_arrow(master_fd, middle: bytes, final: bytes)` or parameterized loop; keep module docstring on staggered writes.

**Risk:** Low; re-run [`osx/tests/test_read_raw_key_csi.py`](../../../../osx/tests/test_read_raw_key_csi.py) after.

## 3. `read_raw_key` and stdin I/O

**Duplication:**

- `select` imported at top of `_drain_stdin_burst` and again inside `read_raw_key`’s `ESC` branch.
- Nested `wait_char` is the same primitive as drain: **select on stdin + `read(1)`**.
- CSI tail loop and SS3 final-byte loop both use: `deadline = monotonic + 1.0`, `wait_char(min(0.5, remaining))`, treat empty as retry until deadline, then map `A`/`B` to up/down.

**Refactor direction:**

- Module-level `_stdin_wait_char(timeout: float) -> str` (or private helper next to `_drain_stdin_burst`) to unify select+read; reuse from `_drain_stdin_burst` if the drain loop can call it without changing semantics (same fd, same read size).
- Small `_read_direction_byte_deadline(wait_fn, deadline: float) -> str` returning the first non-empty byte before deadline (SS3) and optionally reuse the “accumulate until terminator” loop for CSI with a passed predicate / terminator set.

**Risk:** Medium (TTY behavior); rely on existing CSI/SS3 subprocess tests and manual MT-01/02 spot-check after.

## 4. Editor row metadata (`mode` / `x` / `y` / `count` / `delay`)

**Duplication:** The same key set is dispatched repeatedly with parallel `if key == "mode":` chains in:

- `_row_display`, `_field_source`, `_apply_row_reset`, `_edit_row` (and indirectly `_build_editor_table` via `row_keys`).

**Refactor direction (pick one style; avoid over-abstracting):**

- **Table-driven:** e.g. `ROW_SPECS: dict[str, RowSpec]` with `label`, `source_fn`, `reset_fn`, `edit_fn` (callables), or
- **Small dataclass + functions** per row type registered once.

**Benefit:** One place to add a row or change “set mode first” behavior for count/delay. **Cost:** Indirection; `_edit_row` stays imperative but shorter.

**Risk:** Medium (TUI behavior); needs careful manual pass on field edits and reset.

## 5. Rich editor UX helpers

**Duplication:** In `run_rich_pre_run_editor`, validation failures repeat the same pattern: `console.print(Text(..., style="red")); time.sleep(1.2); continue` (lines ~567–579).

**Refactor direction:** `_pause_error(console, message: str, pause: float = 1.2) -> None` (or reuse a single helper name consistent with the codebase).

**Risk:** Low.

## 6. `main()` / CLI vs editor validation

**Duplication:** “Fixed mode needs x/y” and “mode must be set” style checks appear in both `run_rich_pre_run_editor` and the non-Rich / `main` flow (grep shows multiple `cfg.mode == "fixed"` and `cfg.x is None` patterns around ~930–960).

**Refactor direction:** Extract `def fixed_anchor_incomplete(cfg) -> bool` and/or `def can_start_clicking(cfg) -> tuple[bool, str | None]` (ok + error message) used by both the table **S** handler and `main`.

**Risk:** Medium (two code paths must stay aligned).

## 7. Optional / defer

- **Splitting** `macos_mouse_click.py` into a package (`osx/macos_mouse_click/` with `tty_keys.py`, `editor.py`, `cli.py`) improves navigation but is a large diff and complicates the “single script” epilog story; treat as a later phase unless you explicitly want a package layout.
- **Rich imports:** `from rich.console import Console` appears in multiple functions; minor; only consolidate if touching those areas anyway.

## Suggested implementation order

```mermaid
flowchart LR
  T[Test paths + subprocess helper]
  P[PTY injector DRY]
  K[read_raw_key stdin helpers]
  U[Editor pause_error + can_start]
  R[RowSpec table for row keys]
  T --> P
  P --> K
  K --> U
  U --> R
```

## Success criteria

- No behavior change intended: **`make -C osx test-quick`** (or full `osx/tests`) green after each phase.
- For `read_raw_key` / row registry changes: add or extend automated coverage where cheap (CSI already covered; consider **CSI “A” / up** symmetry in the same runner style if not already present).
