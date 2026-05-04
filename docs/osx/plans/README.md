# macOS clicker plans (`docs/osx/plans/`)

**Canonical index** for product and UX specs (**`plan-###-`…** filenames), session hand-offs, status legend, and agent routing for **`osx/macos_mouse_click.py`**. **Implementation:** **[`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py)**. **Parent hub:** **[`../README.md`](../README.md)**. **Defects:** **[`../defects/README.md`](../defects/README.md)**.

This file is the **only** full plan index for the clicker (content formerly in **`docs/plans/README.md`** is merged here); **[`../../plans/README.md`](../../plans/README.md)** is a short pointer for **`docs/plans/`** visitors.

## Cursor / non-clicker reference plans

Reference material that is **not** a **`plan-###`** clicker spec but is kept with this doc tree: **[react2shell-server — Make and test framework (reference)](react2shell-server-test-framework-reference.plan.md)** (GitHub: [glblackburn/react2shell-server](https://github.com/glblackburn/react2shell-server)). Use **kebab-case ASCII** filenames for any similar additions.

**Historical Cursor home imports:** session **`*.plan.md`** files that previously lived only under **`~/.cursor/plans/`** are copied into **[`cursor-plans-import/`](cursor-plans-import/README.md)** (read that README for the manifest). **Normative** work still belongs in **`plan-###-….md`**; merge forward when a draft becomes the spec.

**Mouse-clicker:** extend the relevant **`plan-###-….md`** in this directory (for example **[plan-002](plan-002-macos-mouse-click-terminal-ux.md)**, **[plan-003](plan-003-macos-mouse-click-tui-automation.md)**, **[plan-009](plan-009-macos-mouse-click-tui-arrow-navigation-narrative.md)**). Do **not** treat `~/.cursor/plans/` as canonical — copy material into the numbered plan that owns the feature. **When the user asks to save a plan document into the repo,** write it under this directory (new **`plan-###-….md`** or update an existing plan); the repo path is the canonical copy.

## Shortcut: plan numbers **01**–**17**

The lookup table below maps **01**–**10** (legacy product plan labels) plus **11**–**17** (session notes, design plans, and loop roadmap) to files in this directory.

| Plan | Document |
|------|----------|
| **01** | [plan-001 — macOS clicker](plan-001-macos-clicker.md) |
| **02** | [plan-002 — terminal UX](plan-002-macos-mouse-click-terminal-ux.md) |
| **03** | [plan-003 — TUI automation](plan-003-macos-mouse-click-tui-automation.md) |
| **04** | [plan-004 — run progress UI](plan-004-macos-mouse-click-run-progress-ui.md) |
| **05** | [plan-005 — target preview](plan-005-macos-mouse-click-target-preview.md) |
| **06** | [plan-006 — Rich TUI resize](plan-006-macos-mouse-click-rich-tui-terminal-resize.md) |
| **07** | [plan-007 — field-edit input](plan-007-macos-mouse-click-tui-field-edit-input.md) |
| **08** | [plan-008 — stop during run](plan-008-macos-mouse-click-stop-during-run.md) |
| **09** | [plan-009 — TUI Up/Down phased remediation](plan-009-macos-mouse-click-tui-arrow-navigation-narrative.md) |
| **10** | [plan-010 — learn-point collect](plan-010-macos-mouse-click-learn-points-collect.md) |
| **11** | [plan-011 — code review archive (`macos_mouse_click.py`)](plan-011-macos-mouse-click-code-review.md) |
| **12** | [plan-012 — code review archive (`macos_mouse_click_loop.sh`)](plan-012-macos-mouse-click-loop-code-review.md) |
| **13** | [plan-013 — profile layout / calibration design](plan-013-cookie-clicker-profile-layout-and-calibration.md) |
| **14** | [plan-014 — post-ladder cookie burst factor (loop)](plan-014-macos-mouse-click-loop-cookie-before-ladder.md) |
| **15** | [plan-015 — golden / magic cookie sweeper](plan-015-cookie-clicker-golden-cookie-sweeper.md) |
| **16** | [plan-016 — magic cookie screenshot label tool](plan-016-magic-cookie-screenshot-label-tool.md) |
| **17** | [plan-017 — magic cookie detector eval and tuning](plan-017-magic-cookie-detector-eval-and-tuning.md) |

## Plan index (dates and status)

**Hand-off** session notes (`hand-off-*.md`, `plan-handoff-*.md`) summarize work for the next agent; they are not normative product specs.

**Dates:** **Opened** is the **first** commit date (`git log --follow --diff-filter=A`, `%cs`, ISO) for each file under **`docs/osx/plans/`**. **Completed** is **—** for **Roadmap** or **Session note** rows. For **Shipped** / **Closed (v1)**, **Completed** is the **last** commit date on that file (proxy for last doc revision), not a separate product sign-off.

| Plan id | Title | Opened | Completed | Status | Document |
|---------|-------|--------|-----------|--------|----------|
| plan-001 | macOS clicker (core behavior) | 2026-04-18 | 2026-04-19 | **Shipped** | [plan-001-macos-clicker.md](plan-001-macos-clicker.md) |
| plan-002 | Terminal UX (Rich pre-run) | 2026-04-18 | 2026-04-21 | **Closed (v1)** | [plan-002-macos-mouse-click-terminal-ux.md](plan-002-macos-mouse-click-terminal-ux.md) |
| plan-003 | TUI automation / CI | 2026-04-18 | — | **Roadmap** | [plan-003-macos-mouse-click-tui-automation.md](plan-003-macos-mouse-click-tui-automation.md) |
| plan-004 | Run progress UI | 2026-04-18 | — | **Roadmap** | [plan-004-macos-mouse-click-run-progress-ui.md](plan-004-macos-mouse-click-run-progress-ui.md) |
| plan-005 | Target preview | 2026-04-18 | — | **Roadmap** | [plan-005-macos-mouse-click-target-preview.md](plan-005-macos-mouse-click-target-preview.md) |
| plan-006 | Rich TUI terminal resize | 2026-04-18 | — | **Roadmap** | [plan-006-macos-mouse-click-rich-tui-terminal-resize.md](plan-006-macos-mouse-click-rich-tui-terminal-resize.md) |
| plan-007 | TUI field-edit input | 2026-04-18 | — | **Roadmap** | [plan-007-macos-mouse-click-tui-field-edit-input.md](plan-007-macos-mouse-click-tui-field-edit-input.md) |
| plan-008 | Stop during run | 2026-04-18 | — | **Roadmap** | [plan-008-macos-mouse-click-stop-during-run.md](plan-008-macos-mouse-click-stop-during-run.md) |
| plan-009 | TUI Up/Down arrows — phased remediation | 2026-04-20 | — | **Roadmap** | [plan-009-macos-mouse-click-tui-arrow-navigation-narrative.md](plan-009-macos-mouse-click-tui-arrow-navigation-narrative.md) |
| plan-010 | Learn-point collect (`--learn-points`) | 2026-04-23 | 2026-04-23 | **Shipped** | [plan-010-macos-mouse-click-learn-points-collect.md](plan-010-macos-mouse-click-learn-points-collect.md) |
| plan-011 | Code review archive (`macos_mouse_click.py`) | 2026-05-02 | — | Session note | [plan-011-macos-mouse-click-code-review.md](plan-011-macos-mouse-click-code-review.md) |
| plan-012 | Code review archive (`macos_mouse_click_loop.sh`) | 2026-05-02 | — | Session note | [plan-012-macos-mouse-click-loop-code-review.md](plan-012-macos-mouse-click-loop-code-review.md) |
| plan-013 | Cookie Clicker profile layout / calibration design | 2026-05-03 | — | Design / roadmap | [plan-013-cookie-clicker-profile-layout-and-calibration.md](plan-013-cookie-clicker-profile-layout-and-calibration.md) |
| plan-014 | Post-ladder cookie burst factor — phased **`-k`** + preview (**v2**) | 2026-05-04 | 2026-05-02 | **Shipped** | [plan-014-macos-mouse-click-loop-cookie-before-ladder.md](plan-014-macos-mouse-click-loop-cookie-before-ladder.md) |
| plan-015 | Cookie Clicker golden / magic cookie sweeper (capture + CV) | 2026-05-02 | — | Design / roadmap | [plan-015-cookie-clicker-golden-cookie-sweeper.md](plan-015-cookie-clicker-golden-cookie-sweeper.md) |
| plan-016 | Magic cookie screenshot labeler (PySide + JSONL) | 2026-05-03 | 2026-05-03 | **Shipped** | [plan-016-magic-cookie-screenshot-label-tool.md](plan-016-magic-cookie-screenshot-label-tool.md) |
| plan-017 | Magic cookie detector eval and tuning (label-driven) | 2026-05-03 | — | **Roadmap** | [plan-017-magic-cookie-detector-eval-and-tuning.md](plan-017-magic-cookie-detector-eval-and-tuning.md) |
| plan-handoff | LinkedIn draft session (2026-04-18) | 2026-04-18 | — | Session note | [plan-handoff-2026-04-18-linkedin-macos-clicker-draft.md](plan-handoff-2026-04-18-linkedin-macos-clicker-draft.md) |
| hand-off | Rich pre-run TUI layout (session to next agent) | 2026-04-21 | — | Session note | [hand-off-2026-04-21-rich-pre-run-tui-layout.md](hand-off-2026-04-21-rich-pre-run-tui-layout.md) |

**Status (summary):** **Shipped** = normative behavior spec matches the script; **Closed (v1)** = that plan’s v1 milestone signed off in-doc; **Roadmap** = future work.

## Plan 01 (**Shipped**) vs plan 02 (**Closed (v1)**)

Both statuses align with **code you can run today**, but they answer **different questions**.

**Plan 01** is the **core product / behavior spec**: learn vs fixed vs at-cursor, Quartz, **`-Y`**, signals, confirmation rules, and so on. **Shipped** means the **described behavior is what `osx/macos_mouse_click.py` implements** — plan **01** remains the **long-lived normative reference** for semantics. It does **not** mean “every YAML todo in plan 01 is completed”; the frontmatter tracker can lag while the spec still matches the script.

**Plan 02** is **only the terminal UX layer**: the Rich **pre-run** table, keybindings, operator checklist **MT-01–MT-09**, and **DEF-xxx** records for that surface. **Closed (v1)** means **that plan’s own v1 delivery is finished and signed off in the document** (editor shipped, manual matrix done, defects triaged or deferred as written). Follow-on UX lives in **plans 03–10** and later plans, not as open v1 work inside plan **02**.

| | Plan **01** | Plan **02** |
|---|-------------|-------------|
| **What it covers** | Whole clicker **behavior** | **TTY Rich** experience **before** Quartz |
| **What the status emphasizes** | “Spec matches **shipped** core behavior” | “**This UX plan’s v1** milestone is **done**” |
| **“Done?”** | Core behavior: **yes** for v1. Plan file todos: **may still be messy**. | v1 UX work: **yes**, by the plan’s own closure section. |

So: **both** tie to shipped reality for their **scopes**; **Shipped** labels the **semantic reference**, **Closed (v1)** labels the **closed UX program** for that release line.

