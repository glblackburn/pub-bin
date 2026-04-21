# macOS clicker defects (`docs/osx/defects/`)

Detail files for **DEF-001**–**DEF-009**. The **Defect summary** table (status, fix SHAs, manual verification) remains canonical in **[`../plans/plan-002-macos-mouse-click-terminal-ux.md`](../plans/plan-002-macos-mouse-click-terminal-ux.md)**; update the table and the matching **`def-###`** file together when closing a defect.

| Id | Title | Opened | Status | Document |
|----|-------|--------|--------|----------|
| DEF-001 | `Console.input(highlight=…)` on older Rich | 2026-04-18 | **Fixed** | [def-001-console-input-highlight.md](def-001-console-input-highlight.md) |
| DEF-002 | Arrow / Esc misread → spurious cancel | 2026-04-18 | **Fixed** | [def-002-arrow-misread-as-esc.md](def-002-arrow-misread-as-esc.md) |
| DEF-003 | Wheel / unknown ESC-led input canceled TUI | 2026-04-18 | **Fixed** | [def-003-wheel-esc-cancel.md](def-003-wheel-esc-cancel.md) |
| DEF-004 | TUI field-edit echo / special chars | 2026-04-18 | **Closed (deferred)** | [def-004-tui-edit-echo-special-chars.md](def-004-tui-edit-echo-special-chars.md) |
| DEF-005 | Rich TUI does not reflow on resize | 2026-04-18 | **Closed (deferred)** | [def-005-rich-tui-terminal-resize.md](def-005-rich-tui-terminal-resize.md) |
| DEF-006 | Multiple Up/Down presses per row (CSI) | 2026-04-18 | **Fixed** (manual **Pending**) | [def-006-tui-arrow-multi-press.md](def-006-tui-arrow-multi-press.md) |
| DEF-007 | Duplicate **`-n`** / last wins | 2026-04-19 | **Fixed** (script) | [def-007-duplicate-n-flag-last-wins.md](def-007-duplicate-n-flag-last-wins.md) |
| DEF-008 | Residual double-press / log semantics | 2026-04-19 | **Fixed** (script) | [def-008-residual-arrow-double-press.md](def-008-residual-arrow-double-press.md) |
| DEF-009 | Rich pre-run TUI table layout corruption | 2026-04-21 | **Reported** | [def-009-rich-pre-run-tui-table-layout-corruption.md](def-009-rich-pre-run-tui-table-layout-corruption.md) |

**Plans index:** **[`../plans/README.md`](../plans/README.md)**.
