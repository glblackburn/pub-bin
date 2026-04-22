# Agent plans — macOS clicker (`docs/osx/plans/agent/`)

Cursor / Create-Plan artifacts for **`osx/macos_mouse_click.py`** (PTY tests, DEF-006 / DEF-008 investigations, debug logging, refactors). Filenames use the **`plan-agent-`** prefix.

| File | Summary |
|------|---------|
| [plan-agent-new-test-up-down-navigation.plan.md](plan-agent-new-test-up-down-navigation.plan.md) | Rich table **Down** PTY test + phased logging design. |
| [plan-agent-def-006-tui-arrow-keys.plan.md](plan-agent-def-006-tui-arrow-keys.plan.md) | DEF-006 CSI / **`read_raw_key`** timing (implemented). |
| [plan-agent-arrow-key-double-press-analysis.plan.md](plan-agent-arrow-key-double-press-analysis.plan.md) | DEF-008 residual double-press analysis. |
| [plan-agent-osx-dry-refactor.plan.md](plan-agent-osx-dry-refactor.plan.md) | **`osx/tests/`** helper DRY refactor notes. |
| [plan-agent-automation-deep-dive.plan.md](plan-agent-automation-deep-dive.plan.md) | Plan 03 automation deep dive (historical; much of it landed). |
| [plan-agent-plan-09-phase-3-resume.plan.md](plan-agent-plan-09-phase-3-resume.plan.md) | Plan-09 resume: agent-proxy operator checklist, CI, Phase 3+ draft. |
| [plan-agent-10-consolidate-dry-run-flag.plan.md](plan-agent-10-consolidate-dry-run-flag.plan.md) | Plan 10: single **`--dry-run`**: observability + no UI automation; phased rename, full-path no-op layer, progress UI hook. |
| [plan-agent-rich-pre-run-tui-layout-regression.md](plan-agent-rich-pre-run-tui-layout-regression.md) | Rich pre-run editor layout/resize regression (`32d5820` vs `a0c621f`), PTY tests, fix phases. |

**Product plans:** **[`../README.md`](../README.md)** · **Defects:** **[`../../defects/README.md`](../../defects/README.md)** · **Other agent plans (non-clicker):** [`docs/plans/agent/README.md`](../../../plans/agent/README.md)
