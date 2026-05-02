<!-- 7b30f896-9430-4faf-ae44-92b593896e92 -->
---
todos:
  - id: "write-research-md"
    content: "Create docs/osx/plans/agent/plan-agent-research-looper-cycle-ladder-timing.md with structured summary"
    status: pending
  - id: "index-agent-readme"
    content: "Add README row in docs/osx/plans/agent/README.md for the new research doc"
    status: pending
isProject: false
---
# Research doc: looper buy-ladder vs cycle timing

## Goal

Persist the timing analysis (buy ladder vs full cycle, `cycle_sleep_seconds`, debug env, DEF-011) in-repo so it is not only in chat history.

## Location and naming

- **New file:** [`docs/osx/plans/agent/plan-agent-research-looper-cycle-ladder-timing.md`](docs/osx/plans/agent/plan-agent-research-looper-cycle-ladder-timing.md)
- **Rationale:** Sits beside existing looper research [`plan-agent-looper-cookie-clicker-ui-research.plan.md`](docs/osx/plans/agent/plan-agent-looper-cookie-clicker-ui-research.plan.md); uses **`plan-agent-`** prefix per [`.cursorrules`](.cursorrules) / [`docs/osx/plans/agent/README.md`](docs/osx/plans/agent/README.md).

## Document contents (structure)

1. **Title + date** (2026-04-26) + one-line scope: perceived slowness of **`macos_mouse_click_loop.sh`** buy ladder vs whole run.
2. **Where delays come from** (cite paths only, no large code dumps):
   - **Inter-cycle only:** [`osx/macos_mouse_click_loop.sh`](osx/macos_mouse_click_loop.sh) — `sleep "${CYCLE_SLEEP_SECONDS}"` after `run_once`; `CYCLE_SLEEP_SECONDS` from profile [`osx/config/cookie_clicker_profile.defaults.json`](osx/config/cookie_clicker_profile.defaults.json) `preview_defaults.cycle_sleep_seconds` (e.g. 35 vs 30 adds **+5 s per cycle**, not between ladder rows).
   - **Within ladder rows:** [`click_target`](osx/macos_mouse_click_loop.sh) uses **`-d 0`** — no intentional inter-click delay inside each subprocess.
   - **Per row:** each ladder step is a **new** `macos_mouse_click.py` process (dominant cost vs extra `get_mouse_location` reads).
   - **DEF-011:** [`run_synthetic_loop`](osx/macos_mouse_click.py) adds **`ever_within_thr`** + `get_mouse_location` per iteration — negligible vs process spawn.
   - **Echo line:** `echo "sleep: ${CYCLE_SLEEP_SECONDS}"` once per cycle — negligible.
   - **Debug:** if `MACOS_MOUSE_CLICK_DEBUG_TUI` / `_LOG` are set in `run_once`, note possible extra I/O per subprocess (operator should A/B without debug to compare).
3. **Quick verification** bullet list: measure time between “buy X” lines vs time after cookie before next `sleep:` echo; adjust `cycle_sleep_seconds` in profile if inter-cycle pause is the issue.
4. **Cross-links:** [rate-control / DEF-011](docs/osx/plans/agent/plan-agent-cookie-clicker-rate-control.plan.md), [ui research](docs/osx/plans/agent/plan-agent-looper-cookie-clicker-ui-research.plan.md).

## Index

- Add one row to the table in [`docs/osx/plans/agent/README.md`](docs/osx/plans/agent/README.md): file name, short summary, **Active** (or **Draft**), **Created** / **Updated** dates (use 2026-04-26 for both unless you prefer `git log` after commit).

## Out of scope

- No code or config changes unless you request a follow-up (e.g. revert `cycle_sleep_seconds` or gate debug exports).
