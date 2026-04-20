# Plans index

**macOS mouse click** product plans and operator specs now live under **`[docs/osx/](../osx/README.md)`** — start at **[`docs/osx/plans/README.md`](../osx/plans/README.md)** for the numbered **plan-001**–**plan-009** table, handoffs, and links to **[defects](../osx/defects/README.md)**.

The rows below are **shortcuts** to the same documents (new canonical paths use the **`plan-###-`** filename prefix):

| Plan | Document |
|------|----------|
| **01** | [plan-001 — macOS clicker](../osx/plans/plan-001-macos-clicker.md) |
| **02** | [plan-002 — terminal UX](../osx/plans/plan-002-macos-mouse-click-terminal-ux.md) |
| **03** | [plan-003 — TUI automation](../osx/plans/plan-003-macos-mouse-click-tui-automation.md) |
| **04** | [plan-004 — run progress UI](../osx/plans/plan-004-macos-mouse-click-run-progress-ui.md) |
| **05** | [plan-005 — target preview](../osx/plans/plan-005-macos-mouse-click-target-preview.md) |
| **06** | [plan-006 — Rich TUI resize](../osx/plans/plan-006-macos-mouse-click-rich-tui-terminal-resize.md) |
| **07** | [plan-007 — field-edit input](../osx/plans/plan-007-macos-mouse-click-tui-field-edit-input.md) |
| **08** | [plan-008 — stop during run](../osx/plans/plan-008-macos-mouse-click-stop-during-run.md) |
| **09** | [plan-009 — TUI Up/Down phased remediation](../osx/plans/plan-009-macos-mouse-click-tui-arrow-navigation-narrative.md) |

**Stub paths** (same relative directory as before the move) still exist as one-line redirects — for example [`01-macos-clicker.md`](01-macos-clicker.md) — so older links and external bookmarks keep resolving.

Design and roadmap documents for the **macOS mouse click** tooling (primarily [`osx/macos_mouse_click.py`](../../osx/macos_mouse_click.py)) are described in detail in **`docs/osx/plans/`**; this file remains a **top-level entry** from `docs/plans/`.

## Cursor / agent session plans

Machine-generated or working-session plans for **non–mouse-clicker** work stay under **[`agent/`](agent/README.md)** with **kebab-case, no spaces** filenames.

**Mouse-clicker** session plans live under **[`docs/osx/plans/agent/`](../osx/plans/agent/README.md)** (see **`.cursorrules`**). Do **not** treat `~/.cursor/plans/` as the canonical location for pub-bin work — copy or author plans into the appropriate **`…/plans/agent/`** tree.

## Plan 01 (**Shipped**) vs plan 02 (**Closed (v1)**)

Both statuses align with **code you can run today**, but they answer **different questions**.

**Plan 01** is the **core product / behavior spec**: learn vs fixed vs at-cursor, Quartz, **`-Y`**, signals, confirmation rules, and so on. **Shipped** means the **described behavior is what `osx/macos_mouse_click.py` implements** — plan **01** remains the **long-lived normative reference** for semantics. It does **not** mean “every YAML todo in plan 01 is completed”; the frontmatter tracker can lag while the spec still matches the script.

**Plan 02** is **only the terminal UX layer**: the Rich **pre-run** table, keybindings, operator checklist **MT-01–MT-09**, and **DEF-xxx** records for that surface. **Closed (v1)** means **that plan’s own v1 delivery is finished and signed off in the document** (editor shipped, manual matrix done, defects triaged or deferred as written). Follow-on UX lives in **plans 03–08**, not as open v1 work inside plan **02**.

| | Plan **01** | Plan **02** |
|---|-------------|-------------|
| **What it covers** | Whole clicker **behavior** | **TTY Rich** experience **before** Quartz |
| **What the status emphasizes** | “Spec matches **shipped** core behavior” | “**This UX plan’s v1** milestone is **done**” |
| **“Done?”** | Core behavior: **yes** for v1. Plan file todos: **may still be messy**. | v1 UX work: **yes**, by the plan’s own closure section. |

So: **both** tie to shipped reality for their **scopes**; **Shipped** labels the **semantic reference**, **Closed (v1)** labels the **closed UX program** for that release line.
