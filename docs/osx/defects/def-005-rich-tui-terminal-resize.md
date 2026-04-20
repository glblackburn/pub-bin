---
id: DEF-005
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
---

### DEF-005: Rich TUI does not reflow on terminal resize
- **Frontmatter todo:** `defect-def-005-rich-tui-terminal-resize` (**completed** — filed and **deferred**; no script change in this closure).
- **Status:** **Closed (deferred)** — no in-repo fix for the Rich editor resize behavior in the cycle that recorded **MT-08**; tracked as product/implementation work under **[plan 06 — Rich TUI terminal resize](plan-006-macos-mouse-click-rich-tui-terminal-resize.md)**.
- **Manual verification:** **N/A** — closure is **documentation-only** (deferral), not a code fix.
- **Severity:** Medium (UX) — confusing layout when resizing; does not corrupt config or cause spurious cancel by itself.
- **Environment (reporter):** `yoda.local`, **2026-04-18**, **MT-08** (`./osx/macos_mouse_click.py --learn` without **`-Y`**, **`rich`**).

**Observed**

- **Shrink** terminal width/height: **weird wrapping**, readability suffers.
- **Expand** terminal: UI **does not grow**; effective layout **stays** as if dimensions were still the smaller size.

**Resolution (this defect record)**

- **No `Fix commit`.** Work is **out of scope** for immediate script changes; implement reflow / **SIGWINCH** / redraw per **[plan 06](plan-006-macos-mouse-click-rich-tui-terminal-resize.md)**. When plan **06** ships, add a **Fix commit** row here (or supersede with a new DEF if the behavior changes materially).

**Regression check (after plan 06)**

- Re-run **MT-08**: resize narrow → wide → narrow; table/panel should track terminal size or show a clear “too narrow” mode without escape soup.
