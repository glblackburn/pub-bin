# macOS mouse click — coverage gap notes (Plan 11)

**Purpose:** Human-readable baseline and gap tracking (same idea as `network-tools/capture/docs/test-coverage-analysis.md`). Update after meaningful test or product changes.

## How to refresh numbers

1. On **macOS**, from repo root: `make -C osx test-setup` (once), then `make -C osx test-coverage` (or `make -C osx coverage-quick` to skip `table_nav` tests).
2. Open **`osx/htmlcov/index.html`** and note overall **line %** (or read the terminal summary).
3. Fill **Baseline snapshot** below (commit hash, date, command used).

## Baseline snapshot (fill in)

| Field | Value |
|--------|--------|
| **Date** | 2026-04-22 |
| **Git commit** | _update after each refresh — `git rev-parse --short HEAD`_ |
| **Command** | `make -C osx coverage-quick` (excludes `table_nav`) |
| **Line coverage (approx.)** | **~29%** on `osx/macos_mouse_click.py` (example: 851 stmts, 601 miss) |
| **Notes** | Full suite: `make -C osx test-coverage`; `table_nav` PTY tests can be timing-sensitive on loaded hosts. |

## Largest gaps (prioritize)

_Use `term-missing` or HTML “missing” column to list functions or regions worth tests first (pure helpers, argparse, dry-run), then harder paths (Rich, Quartz)._

1. **Quartz / synthetic loop / learn** — large contiguous misses around `import_quartz`, `post_synthetic_click`, `wait_for_anchor_click`, `run_synthetic_loop` (expected without UI automation in unit tests).
2. **`main()` / Rich pre-run** — many lines only exercised by interactive or heavy PTY paths; add subprocess tests where deterministic (see existing dry-run / debug patterns).

## Target (optional)

| Target line % | Rationale |
|---------------|-----------|
| _TBD_ | _e.g. 60% before expanding PTY scope_ |

