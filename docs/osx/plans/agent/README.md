# Agent plans — macOS clicker (`docs/osx/plans/agent/`)


**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).

Cursor / Create-Plan artifacts for **`osx/macos_mouse_click.py`** (PTY tests, DEF-006 / DEF-008 investigations, debug logging, refactors). Filenames use the **`plan-agent-`** prefix.

**Created** / **Updated** are commit dates (`%cs`, ISO) from `git log --follow`: first time the file appeared in history, and the latest commit touching that path. **Status** is derived from each plan’s YAML `todos` (`completed` / `pending` / `cancelled`); plans without todo frontmatter are **Active**. **Done** = every todo is `completed` or `cancelled`. **In progress** = at least one `completed` and one `pending`. **Draft** = all todos `pending`.

| File | Summary | Status | Created | Updated |
|------|---------|--------|---------|---------|
| [plan-agent-osx-docs-hub-hygiene.plan.md](plan-agent-osx-docs-hub-hygiene.plan.md) | **`docs/osx`** inventory alignment (DEF-009), loop script repo baseline, hub path pytest, script doc pointer. | Active | 2026-04-22 | 2026-04-22 |
| [plan-agent-macos-mouse-click-loop-template-skip-buy.plan.md](plan-agent-macos-mouse-click-loop-template-skip-buy.plan.md) | **`macos_mouse_click_loop.sh`**: template-aligned CLI, **`run_buy_ladder`**, **`-S`** cookie-only cycles; **`osx/README.md`** examples. | Done | 2026-04-25 | 2026-04-25 |
| [plan-agent-looper-cookie-clicker-ui-research.plan.md](plan-agent-looper-cookie-clicker-ui-research.plan.md) | Research: current looper behavior, Cookie Clicker screenshot deltas, and prioritized feature backlog. | Done | 2026-04-25 | 2026-04-25 |
| [plan-agent-research-looper-cycle-ladder-timing.md](plan-agent-research-looper-cycle-ladder-timing.md) | Research: buy-ladder row timing vs **`CYCLE_SLEEP_SECONDS`**, DEF-011 overhead, debug I/O. | Active | 2026-04-26 | 2026-04-26 |
| [../../defects/def-012-loop-profile-forces-preview-on-builtin.md](../../defects/def-012-loop-profile-forces-preview-on-builtin.md) | **DEF-012:** **`macos_mouse_click_loop.sh`** — do not force OpenCV preview when **`source_image`** is **`builtin`** / coords-only; gate **`-N`**/**`-R`**. *Merged defect + YAML **`todos`**.* | Active | 2026-04-28 | 2026-04-28 |
| [plan-agent-cookie-clicker-rate-control.plan.md](plan-agent-cookie-clicker-rate-control.plan.md) | **Phase 1** in-band abort (implemented); **Phase 2** inter-click delay / pacing / tuning. | In progress | 2026-04-26 | 2026-04-26 |
| [plan-agent-new-test-up-down-navigation.plan.md](plan-agent-new-test-up-down-navigation.plan.md) | Rich table **Down** PTY test + phased logging design. | Done | 2026-04-19 | 2026-04-23 |
| [plan-agent-def-006-tui-arrow-keys.plan.md](plan-agent-def-006-tui-arrow-keys.plan.md) | DEF-006 CSI / **`read_raw_key`** timing (implemented). | Done | 2026-04-18 | 2026-04-19 |
| [plan-agent-arrow-key-double-press-analysis.plan.md](plan-agent-arrow-key-double-press-analysis.plan.md) | DEF-008 residual double-press analysis. | Draft | 2026-04-19 | 2026-04-19 |
| [plan-agent-osx-dry-refactor.plan.md](plan-agent-osx-dry-refactor.plan.md) | **`osx/tests/`** helper DRY refactor notes. | Draft | 2026-04-18 | 2026-04-19 |
| [plan-agent-automation-deep-dive.plan.md](plan-agent-automation-deep-dive.plan.md) | Plan 03 automation deep dive (historical; much of it landed). | Done | 2026-04-18 | 2026-04-19 |
| [plan-agent-plan-09-phase-3-resume.plan.md](plan-agent-plan-09-phase-3-resume.plan.md) | Plan-09 resume: agent-proxy operator checklist, CI, Phase 3+ draft. | Draft | 2026-04-21 | 2026-04-21 |
| [plan-agent-10-consolidate-dry-run-flag.plan.md](plan-agent-10-consolidate-dry-run-flag.plan.md) | Plan 10: single **`--dry-run`**: observability + no UI automation; phased rename, full-path no-op layer, progress UI hook. | Draft | 2026-04-22 | 2026-04-22 |
| [plan-agent-11-code-coverage-and-testing.plan.md](plan-agent-11-code-coverage-and-testing.plan.md) | Plan 11: **pytest-cov**, Makefile/CI reporting, baseline then targeted tests for `macos_mouse_click.py`. | Done | 2026-04-22 | 2026-04-23 |
| [plan-agent-12-learn-points-collect.plan.md](plan-agent-12-learn-points-collect.plan.md) | Plan 12 / **plan-010:** **`learn_collect`** — Rich log under settings (infinite samples, rotating line colors); exit with zero captures; **`-Y`** plain text; dry-run fake lines for tests; no autoclicker. | Done | 2026-04-22 | 2026-04-23 |
| [plan-agent-13-post-start-click-tests.plan.md](plan-agent-13-post-start-click-tests.plan.md) | Plan 13: **post-start** click tests — Tier 1 mocks (`post_synthetic_click` / `sleep_interruptible` / `wait_for_anchor_click`); optional `main()`; **Tier 2** real macOS `CGEventTap` observer + subprocess SUT (env-gated). | Draft | 2026-04-23 | 2026-04-23 |
| [plan-agent-rich-pre-run-tui-layout-regression.md](plan-agent-rich-pre-run-tui-layout-regression.md) | Rich pre-run editor layout/resize regression (`32d5820` vs `a0c621f`), PTY tests, fix phases. | Done | 2026-04-21 | 2026-04-21 |

**Product plans:** **[`../README.md`](../README.md)** · **Defects:** **[`../../defects/README.md`](../../defects/README.md)** · **Other agent plans (non-clicker):** [`docs/plans/agent/README.md`](../../../plans/agent/README.md)
