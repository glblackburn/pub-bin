<!-- 7b30f896-9430-4faf-ae44-92b593896e92 -->
---
todos:
  - id: "write-plan-md"
    content: "Add `docs/osx/plans/agent/plan-agent-macos-mouse-click-loop-template-skip-buy.plan.md` with frontmatter, terminology, retrospective sections, verification, non-goals, optional mermaid."
    status: pending
  - id: "update-agent-readme"
    content: "Append index row + dates in `docs/osx/plans/agent/README.md` for the new plan file."
    status: pending
isProject: false
---
# Retrospective plan doc: `macos_mouse_click_loop.sh`

## Context

The operator loop script **[`osx/macos_mouse_click_loop.sh`](osx/macos_mouse_click_loop.sh)** was refactored and extended without an in-repo agent plan. **[`6514731`](https://github.com/)** (local history) introduced usage/`getopts`, **`-c <count>`**, and README operator-loop examples; **`effa253`** (`feat(osx): loop -S cookie-only, run_buy_ladder, template section markers`) added **`-S`**, **`run_buy_ladder`**, **`SKIP_BUY_LADDER`**, and section layout aligned with repo root **[`shell-template.sh`](shell-template.sh)** (`shift $((OPTIND -1))`, **`# functions`** / **`# main script logic`** split).

## Deliverable

1. **New file:** `docs/osx/plans/agent/plan-agent-macos-mouse-click-loop-template-skip-buy.plan.md`

   Match house style from e.g. [`plan-agent-11-code-coverage-and-testing.plan.md`](docs/osx/plans/agent/plan-agent-11-code-coverage-and-testing.plan.md):

   - Leading HTML comment noting canonical in-repo copy (not `~/.cursor/plans/`).
   - YAML `todos` frontmatter: all items **`status: completed`** (retrospective doc only), **`isProject: false`**.
   - Standard **Terminology** paragraph (CSI/SS3/PTY) for consistency with other `docs/osx/plans/agent/` files.
   - **Scope:** `osx/macos_mouse_click_loop.sh` + pointer to [`osx/README.md`](osx/README.md) operator-loop section only (no Python clicker changes).
   - **Implemented behavior** (bullet list):
     - **`-c <count>`:** finite cycles; omit for infinite loop with **30s** sleep between cycles.
     - **`-S`:** skip **`run_buy_ladder`**; each cycle runs only the **`-n 3000`** cookie burst (real clicks via **`-Y`** on `macos_mouse_click.py`).
     - **`run_once`:** conditional ladder + cookie burst; debug env exports unchanged.
     - **Structure:** CLI params → usage → getopts + post-parse validation (clicker exists, **`-c`** positive integer) → **`# functions`** (`run_buy_ladder`, `run_once`) → **`# main script logic`** (counter + `while true`).
   - **Reference alignment:** one short subsection comparing section order to [`shell-template.sh`](shell-template.sh) lines 77–122 (`getopts`, `shift`, functions, main).
   - **Verification:** `bash -n osx/macos_mouse_click_loop.sh` (no new pytest scope unless explicitly desired later).
   - **Non-goals:** Changing coordinates, sleep interval, or adding automated tests for the bash loop in this doc pass.

2. **Index row:** Update [`docs/osx/plans/agent/README.md`](docs/osx/plans/agent/README.md) table (after the hub hygiene row or logically near “loop script” topics):

   - **File:** link to `plan-agent-macos-mouse-click-loop-template-skip-buy.plan.md`
   - **Summary:** one line — template-aligned looper CLI, **`run_buy_ladder`**, **`-S`** cookie-only cycles, README examples.
   - **Status:** **Done** (all todos completed).
   - **Created / Updated:** use `git log -1 --format=%cs -- docs/osx/plans/agent/plan-agent-macos-mouse-click-loop-template-skip-buy.plan.md` after the file exists (same date for both on first add).

## Optional diagram (in the plan doc)

A small **mermaid** `flowchart` is enough: `parseCLI` → `run_once` → `run_buy_ladder?` (if not **`-S`**) → `cookieBurst` → `sleep30` / `break` on cycle cap.

## Out of scope

- Editing `osx/macos_mouse_click_loop.sh` or `osx/README.md` again unless you discover a factual error while writing the plan.
- Commit protocol: per [README-AI-CODING-STANDARDS.md](README-AI-CODING-STANDARDS.md), show commit message and diff preview and wait for confirmation before committing (if the user asks for a commit).
