<!-- Cursor agent plan 11 (canonical copy in-repo; do not use ~/.cursor/plans/). -->
---
todos:
  - id: "cov-01-baseline"
    content: "Run coverage locally on macOS; record baseline % and largest uncovered regions (macos_mouse_click.py)."
    status: pending
  - id: "cov-02-tooling"
    content: "Add pytest-cov + config (.coveragerc or pyproject); Makefile target(s) and .gitignore for htmlcov/ .coverage; document in osx/README.md."
    status: pending
  - id: "cov-03-ci-artifact"
    content: "Optional: CI step to emit coverage XML/HTML artifact on macos-mouse-click workflow (no third-party token required for v1)."
    status: pending
  - id: "cov-04-gaps-tests"
    content: "Prioritize tests for pure helpers, argparse branches, and non-PTY paths; defer flaky PTY unless high value."
    status: pending
isProject: false
---
# Plan 11 — Code coverage reporting and coverage-driven tests

## Scope

Primary code under test: **[`osx/macos_mouse_click.py`](../../../../osx/macos_mouse_click.py)** (single large module). Tests live under **[`osx/tests/`](../../../../osx/tests/)**. Orchestration today: **[`osx/Makefile`](../../../../osx/Makefile)** (`make -C osx test`, `test-report`, …), **[`osx/pytest.ini`](../../../../osx/pytest.ini)**, CI **[`.github/workflows/macos-mouse-click.yml`](../../../../.github/workflows/macos-mouse-click.yml)** (Python 3.11, `pytest osx/tests`).

This plan adds **measurable coverage**, **repeatable local/CI commands**, and **targeted tests** to raise coverage without destabilizing **darwin-only** and **PTY** suites.

## Goals

1. **Coverage tooling:** `pytest-cov` (or equivalent) with a checked-in config so `source=` / omit patterns are stable (e.g. omit tests themselves if desired, omit `if TYPE_CHECKING` blocks as appropriate).
2. **Operator UX:** `make -C osx coverage` (or similar) producing **terminal summary** + optional **HTML** under `osx/htmlcov/` (gitignored), documented next to existing test targets.
3. **Baseline then deltas:** Establish a **baseline** report (commit hash + overall line %) before large test additions; later PRs can compare informally or via CI artifact.
4. **Coverage-driven tests:** Use the report to find **high-value, low-risk** gaps: pure functions, validation paths, argparse combinations, error branches that do not need a GUI. Avoid chasing **100%** if it requires brittle PTY or Accessibility-dependent paths.

## Non-goals (initially)

- **Codecov / Coveralls** or PR comment bots (optional later; needs token/policy).
- **Merging coverage** from multiple OS jobs (only `macos-latest` today).
- **Rewriting** the script into packages solely for coverage (see separate refactor plans).

## Phased work

### Phase 0 — Baseline

- On **macOS**, from repo root: install dev extra or add `pytest-cov` to **[`osx/requirements-test.txt`](../../../../osx/requirements-test.txt)** temporarily, run `pytest osx/tests --cov=osx.macos_mouse_click --cov-report=term-missing` (exact module path may be `macos_mouse_click` if imported as script; align with how tests `import macos_mouse_click as mmc`).
- Note **overall line %** and top **uncovered** functions (especially `main`, Rich paths, Quartz-guarded blocks).

### Phase 1 — Tooling in repo

- Add **`pytest-cov`** to `requirements-test.txt` with a lower bound compatible with pytest 7+.
- Add **`.coveragerc`** (under `osx/` or repo root — pick one and document): branch coverage optional; `omit` for tests if policy is “production module only”; `relative_files = true` if useful for CI paths.
- **Makefile:** e.g. `coverage` → `pytest … --cov=… --cov-report=html --cov-report=term-missing` writing HTML to `osx/htmlcov/`; add dirs to **`.gitignore`** (repo root or `osx/.gitignore` if present).
- **`osx/README.md`:** short section “Coverage” with the exact `make` target and how to open HTML locally.

### Phase 2 — CI (optional but valuable)

- Extend **`.github/workflows/macos-mouse-click.yml`**: after `make -C osx test`, either run the same suite with `--cov-report=xml` and **upload-artifact** `coverage.xml` + optional HTML zip, or a dedicated job step that does not double runtime unreasonably (e.g. single pytest invocation with both junit and cov if desired).
- Do **not** fail the job on coverage threshold in v1 unless the team wants a **floor** (e.g. `fail_under` in config) after baseline is stable.

### Phase 3 — Tests to improve coverage (prioritized)

Use the HTML / missing-line report to queue work:

1. **Pure / IO-light helpers** (keyboard parsing, config resolution, dry-run JSON helpers): unit tests with no Quartz.
2. **Argparse / exit codes** for invalid combinations: subprocess or direct `parse_args` where safe.
3. **Branches shared by `-Y` and TTY** already partially covered by dry-run; extend only where missing lines are **deterministic**.
4. **Rich / PTY** only where prior plans (**plan-003**, DEF-009 tests) show stable patterns; do not block coverage goals on flaky full-table drives.

Document in PRs which **lines** or **functions** each new test is meant to cover (brief).

## Risks

- **Import side effects:** `macos_mouse_click.py` may import heavy deps; coverage of `import_quartz()` may require mocking (already used in some tests).
- **Slow tests:** full PTY suite; keep `coverage` target optionally excluding slow markers via `-m` if needed (document tradeoff).
- **False confidence:** high % with weak asserts; prefer **assert behavior** on newly covered branches.

## Documentation cross-links

- **[`plan-003-macos-mouse-click-tui-automation.md`](../plan-003-macos-mouse-click-tui-automation.md)** — existing test matrix and CI.
- **[`plan-agent-osx-dry-refactor.plan.md`](plan-agent-osx-dry-refactor.plan.md)** — test/helper layout if coverage work touches shared fixtures.

## Open decisions (before Phase 1 merge)

1. **Coverage scope:** module-only (`macos_mouse_click`) vs include small helpers under `osx/tests/` support code (usually omit).
2. **CI artifact:** XML only vs HTML zip for human inspection in Actions UI.
3. **Threshold:** whether to enable `fail_under` after one baseline sprint.
