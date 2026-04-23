# Agent plan: `docs/osx` hub hygiene (orientation follow-up)

**Scope:** Close the gap between the review plan for `docs/osx` + `osx/` and repo state—without a new product feature.

## Goals

1. **Doc inventory alignment** — Update [`OSX-DOCS-REORGANIZATION-PLAN.md`](../../OSX-DOCS-REORGANIZATION-PLAN.md) so canonical inventory and success criteria mention **DEF-001–DEF-009** and **`def-009`** where the live tree already includes them (remove drift vs [`defects/README.md`](../../defects/README.md)).
2. **Loop script policy** — Keep [`macos_mouse_click_loop.sh`](../../../../osx/macos_mouse_click_loop.sh) at the **shared-repo example** (last committed baseline): no local-only sleep/coord/debug toggles in the working tree. Operators customize in a branch or copy.
3. **Regression guard** — Add a small pytest that asserts core hub files under `docs/osx/` and `osx/` still exist (catches broken moves/renames).
4. **Discoverability** — Point [`macos_mouse_click.py`](../../../../osx/macos_mouse_click.py) module docs at the hub [`docs/osx/README.md`](../../README.md).

## Non-goals

- Changing Rich TUI behavior, dry-run flags, or PTY tests beyond the new doc-path smoke test.
- Rewriting product plans (plan-001–009) body text.

## Verification

- `make -C osx test` (or `test-quick` if CI-equivalent subset is enough; full test preferred after doc-only + small test add).

## Owner

This file; product umbrella remains **plan-002** (terminal UX / defects process) for defect table edits—**none** required here (no defect closed).
