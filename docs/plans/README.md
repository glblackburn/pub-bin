# Plans index

Design and roadmap documents for the **macOS mouse click** tooling (primarily [`osx/macos_mouse_click.py`](../../osx/macos_mouse_click.py)). Files are ordered by plan number.

| Plan | Document | Status | Summary |
|------|----------|--------|---------|
| **01** | [01-macos-clicker.md](01-macos-clicker.md) | **Shipped** | Core clicker: modes (learn / fixed / at-cursor), Quartz, CLI, signals, **`--yes`** / **`--interactive`**, confirmation — **source of truth** for behavior. |
| **02** | [02-macos-mouse-click-terminal-ux.md](02-macos-mouse-click-terminal-ux.md) | **Closed (v1)** | Rich **pre-run** TTY table, keybindings, operator **MT-01–MT-09**, defects **DEF-001–005**; links to plans **03–08**. |
| **03** | [03-macos-mouse-click-tui-automation.md](03-macos-mouse-click-tui-automation.md) | **Roadmap** | **pytest** / PTY / CI for pre-Quartz TUI and pipe paths (**MT-02**, **MT-09**, etc.) — document done; **implementation todos pending** in plan frontmatter. |
| **04** | [04-macos-mouse-click-run-progress-ui.md](04-macos-mouse-click-run-progress-ui.md) | **Roadmap** | Post-**Start** Rich summary + **in-run progress** — not implemented. |
| **05** | [05-macos-mouse-click-target-preview.md](05-macos-mouse-click-target-preview.md) | **Roadmap** | **Preview-only** + **show-before-run** for fixed **`-x`/`-y`** — not implemented. |
| **06** | [06-macos-mouse-click-rich-tui-terminal-resize.md](06-macos-mouse-click-rich-tui-terminal-resize.md) | **Roadmap** | **SIGWINCH** / reflow (**DEF-005** deferred here) — not implemented. |
| **07** | [07-macos-mouse-click-tui-field-edit-input.md](07-macos-mouse-click-tui-field-edit-input.md) | **Roadmap** | Field-edit **`Console.input`** hygiene (**DEF-004** deferred here) — not implemented. |
| **08** | [08-macos-mouse-click-stop-during-run.md](08-macos-mouse-click-stop-during-run.md) | **Roadmap** | Stop during run without foreground terminal (**`-Y`**, long runs) — not implemented. |

### Status meanings

| Status | Meaning |
|--------|---------|
| **Shipped** | Described behavior is **in the repo** for the main script; this plan stays the **normative reference** (small doc drift vs YAML todos may exist). |
| **Closed (v1)** | That plan’s **v1** scope is **finished and signed off** in the document (implementation + manual QA as defined there). |
| **Roadmap** | **Future work**: spec / phases exist; **no** matching product change yet (or only partial — see that plan’s frontmatter **`todos:`**). |

When adding a new plan, use the next free number (`09-…`), link it from **plan 02** *Implementation touchpoints* if it affects terminal UX, add a row here, and pick a **Status** from the table above (or extend the legend).

## Cursor / agent session plans

Machine-generated or working-session plans (Create Plan, handoffs) live under **[`agent/`](agent/README.md)** with **kebab-case, no spaces** filenames. Do **not** treat `~/.cursor/plans/` as the canonical location for pub-bin work — copy or author plans in **`docs/plans/agent/`** instead.

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

