# macOS clicker defects (`docs/osx/defects/`)


**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).

Detail files for **DEF-001**–**DEF-012**. The **Defect summary** table (status, fix SHAs, manual verification) remains canonical in **[`../plans/plan-002-macos-mouse-click-terminal-ux.md`](../plans/plan-002-macos-mouse-click-terminal-ux.md)**; update the table and the matching **`def-###`** file together when closing a defect.

**Completed** = date the defect was **resolved in process** (fix landed, deferred, or automated verification recorded). **—** means still open for **manual verification** or no single completion date (align with plan-002 **Manual verification** column).

| Id | Title | Opened | Completed | Status | Document |
|----|-------|--------|-----------|--------|----------|
| DEF-001 | `Console.input(highlight=…)` on older Rich | 2026-04-18 | 2026-04-18 | **Fixed** | [def-001-console-input-highlight.md](def-001-console-input-highlight.md) |
| DEF-002 | Arrow / Esc misread → spurious cancel | 2026-04-18 | 2026-04-18 | **Fixed** | [def-002-arrow-misread-as-esc.md](def-002-arrow-misread-as-esc.md) |
| DEF-003 | Wheel / unknown ESC-led input canceled TUI | 2026-04-18 | 2026-04-18 | **Fixed** | [def-003-wheel-esc-cancel.md](def-003-wheel-esc-cancel.md) |
| DEF-004 | TUI field-edit echo / special chars | 2026-04-18 | 2026-04-18 | **Closed (deferred)** | [def-004-tui-edit-echo-special-chars.md](def-004-tui-edit-echo-special-chars.md) |
| DEF-005 | Rich TUI does not reflow on resize | 2026-04-18 | 2026-04-18 | **Closed (deferred)** | [def-005-rich-tui-terminal-resize.md](def-005-rich-tui-terminal-resize.md) |
| DEF-006 | Multiple Up/Down presses per row (CSI) | 2026-04-18 | — | **Fixed** (manual **Pending**) | [def-006-tui-arrow-multi-press.md](def-006-tui-arrow-multi-press.md) |
| DEF-007 | Duplicate **`-n`** / last wins | 2026-04-19 | 2026-04-19 | **Fixed** (script) | [def-007-duplicate-n-flag-last-wins.md](def-007-duplicate-n-flag-last-wins.md) |
| DEF-008 | Residual double-press / log semantics | 2026-04-19 | — | **Fixed** (script) | [def-008-residual-arrow-double-press.md](def-008-residual-arrow-double-press.md) |
| DEF-009 | Rich pre-run TUI table layout corruption | 2026-04-21 | 2026-04-21 | **Fixed** (script) | [def-009-rich-pre-run-tui-table-layout-corruption.md](def-009-rich-pre-run-tui-table-layout-corruption.md) |
| DEF-010 | `--abort-on-mouse-move` used wrong reference (burst-start cursor vs click target) | 2026-04-26 | 2026-04-26 | **Fixed** (script) | [def-010-mouse-move-abort-wrong-reference.md](def-010-mouse-move-abort-wrong-reference.md) |
| DEF-011 | Mouse-move abort annulus: default arm radius > threshold → false stop on buy ladder | 2026-04-26 | 2026-04-26 | **Fixed** (script) | [def-011-mouse-move-abort-arm-threshold-annulus.md](def-011-mouse-move-abort-arm-threshold-annulus.md) |
| DEF-012 | `-P` forces preview; `source_image: "builtin"` → OpenCV imread failure (coords-only profiles) | 2026-04-28 | 2026-04-28 | **Fixed** (script + docs) | [def-012-loop-profile-forces-preview-on-builtin.md](def-012-loop-profile-forces-preview-on-builtin.md) |

**Plans index:** **[`../plans/README.md`](../plans/README.md)**.
