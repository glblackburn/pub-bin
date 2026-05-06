---
id: hand-off-rich-pre-run-tui-layout-2026-04-21
type: hand-off
related_plans:
  - plan-002-macos-mouse-click-terminal-ux.md
  - plan-006-macos-mouse-click-rich-tui-terminal-resize.md
  - plan-009-macos-mouse-click-tui-arrow-navigation-narrative.md
related_defects:
  - ../defects/def-009-rich-pre-run-tui-table-layout-corruption.md
---

### Hand-off: Rich pre-run TUI layout (session summary)

**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).

**Audience:** Next agent working on **`osx/macos_mouse_click.py`** Rich pre-run editor layout, blank rows, resize, or PTY tests.

**Status:** **Closed (archive)** — This file is a **frozen session snapshot** (Apr 21, 2026). At write time, layout was **still reported broken** on some real terminals while automated tests passed. **Normative follow-up** lives in **plan-006**, **plan-009**, and **DEF-009** / **DEF-010**; **do not extend this hand-off** as if it were an open checklist.

---

#### Reporter-verified baseline (git)

**Layout works as expected** at commit **`32d5820bf068047eb6271894a697b63d05073283`**. In that state (manual Terminal.app / real TTY, per reporter):

- There are **no empty lines** in the pre-run editor UI.
- The layout **dynamically corrects** when **scaling the terminal window** (resize feels correct).

**The commit immediately after `32d5820` breaks the layout** from the reporter’s perspective (extra blank-looking rows and resize no longer behaving as above). That child commit is **`a0c621f9464249cf16b839e5f307df20feba7b7e`** (`fix(osx): Rich TTY editor stdin fixes and DEF-009 layout regression`). Note: `32d5820` itself only touches `osx/macos_mouse_click_loop.sh` in git metadata; checking it out moves the tree **before** the stdin/raw editor changes in `a0c621f`, so the “good” behavior is the **combined** `osx/macos_mouse_click.py` + environment at that revision.

**Implication for the next agent:** diff **`32d5820..a0c621f`** (especially `run_rich_pre_run_editor`, `read_raw_key`, TTY discipline) against current `main` while preserving arrow-key behavior, until resize and spacer symptoms match the baseline again.

---

#### What the user wanted

- Remove **extra empty / “spacer” lines** inside the bordered table (Rich `row_height` padding when any cell wraps).
- Keep **arrow / stdin fixes** from after `32d5820` (`/dev/tty`, persistent raw mode in the editor loop, `_read_raw_key_impl`, `_flush_stdout_safe` before stderr debug).
- Restore **resize behavior** like **`32d5820`**: dynamic layout correction when scaling the window (see reporter baseline above). **DEF-005** / **plan-006** document deferred reflow work, but the reporter did **not** see the same failure mode at the good commit—so the regression may be **interaction** (TTY + Rich + env) rather than only “missing SIGWINCH handler.”

---

#### Commits and code evolution (high level)

1. **`32d5820bf068047eb6271894a697b63d05073283`** (reporter “good layout” baseline): default Rich `Table` / `Panel`, `read_raw_key()` on `sys.stdin` (no dedicated TTY fd). **`a0c621f9464249cf16b839e5f307df20feba7b7e`** (next commit) did **not** change `_build_editor_table` markup in the diff, but changed **stdin path and raw TTY discipline** for the editor loop; layout and resize **regressed** from the reporter’s perspective starting there.
2. **`3bd517d`** introduced **`box.ROUNDED`** on the inner table and **`_flush_stdout_safe()`** after `clear` / `print` to reduce DEF-009 stdout/stderr interleave on narrow PTYs.
3. Later iteration **dropped `ROUNDED`** again (user preference for “legacy” look) but that brought back **fused panel title + inner heavy rules** on small PTYs unless geometry/env matched.
4. **Fix commit `ea264d6`** (`fix(osx): Rich pre-run editor — no spacer rows, legacy table, PTY env sync`):
   - **`_build_editor_table`:** default inner table (no `ROUNDED`); **`no_wrap=True`** and **`overflow="ellipsis"`** on **Setting, Value, and Source** to avoid multi-line cells and spacer rows.
   - **`pty_harness.spawn_clicker_pexpect`:** when **`dimensions=(rows, cols)`** is passed, set **`LINES`** and **`COLUMNS`** in the child env to match. Rich consults **`os.environ`** before **`get_terminal_size`**, so tests were previously lying (PTY wide but `COLUMNS=120`).
   - **Tests:** `def010_vertical_spacer_reason()`; **`layout_corruption_reason(..., ignore_fused_panel_heavy_line=True)`** for the live DEF-009 PTY test so **legitimate** narrow `HEAVY_HEAD` header lines are not confused with DEF-009 fusion; narrow synthetic test asserts **no** DEF-010 spacer rows with long cell text.

---

#### Files to read first

| Area | Path |
|------|------|
| Editor table + loop | `osx/macos_mouse_click.py` (`_build_editor_table`, `_run_rich_pre_run_editor_loop`, `_flush_stdout_safe`, `_kbd_tty_fd_get`, `_read_raw_key_impl`) |
| Transcript heuristics | `osx/tests/def009_layout_heuristics.py` |
| PTY spawn | `osx/tests/pty_harness.py` |
| Layout / DEF-010 tests | `osx/tests/test_def009_rich_table_layout_pty.py` |

---

#### Historical context (superseded by plans 006 / 009 + defects)

The bullets below were **session notes for the next agent** at hand-off time. They are **not** an open backlog for this file. Track work in **plan-006**, **plan-009**, and **`docs/osx/defects/`** instead.

1. **Manual layout still wrong** (per reporter): reproduce with the same Terminal profile, font, line spacing, and **`MACOS_MOUSE_CLICK_DEBUG_TUI`** on/off; compare transcript to **`layout_corruption_reason`** / **`def010_vertical_spacer_reason`** output.
2. **`┃┃` / `││` heuristics** can disagree with **valid** narrow `HEAVY_HEAD` + nested `Panel` output; **`def010_vertical_spacer_reason`** was added to assert spacer absence **without** the full DEF-009 bundle on narrow renders.
3. **Resize:** reporter saw **correct dynamic reflow at `32d5820`**; later revisions do not. There is still **no explicit SIGWINCH handler** in the script today; **`plan-006`** remains the umbrella for reflow work, but the next agent should **reproduce at `32d5820` vs `a0c621f`** to learn what changed (TTY raw mode, `/dev/tty`, **`COLUMNS`/`LINES`**, Rich `Console` sizing) before assuming only a missing signal handler.
4. **Docs gap:** module docstrings may mention DEF-010; there is **no** `docs/osx/defects/def-010-*.md` in tree at hand-off time; add or trim references when filing narrative.
5. **Tradeoff space:** If fusion on very short terminals returns as a **real** bug, **`ROUNDED`** (or another inner box) may need to return behind a **width/height threshold**, with tests updated accordingly.

---

#### Verification

- From repo root: **`make -C osx test`** (includes **`test_def009_*`**, **`test_def010_*`**, table nav PTY tests on darwin).

---

#### Index

Listed in **[`docs/osx/plans/README.md`](README.md)** under **Hand-off** session notes.

---

#### Closure (repository)

This hand-off is **complete as an archive**. No further edits are required to “finish” it. Open TUI product work continues only under the **numbered plans** and **defect** docs linked above.
