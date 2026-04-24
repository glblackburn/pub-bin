<!-- Cursor agent plan 11 (canonical copy in-repo; do not use ~/.cursor/plans/). -->
---
todos:
  - id: "cov-01-baseline"
    content: "Run coverage locally on macOS; record baseline % and largest uncovered regions (macos_mouse_click.py)."
    status: completed
  - id: "cov-02-tooling"
    content: "Add pytest-cov + osx/.coveragerc; Makefile COV_MODULE + coverage target (html+term+xml+term-missing, --cov-config); .gitignore; osx/README.md."
    status: completed
  - id: "cov-03-ci-artifact"
    content: "Optional: CI step to emit coverage XML/HTML artifact on macos-mouse-click workflow (no third-party token required for v1)."
    status: completed
  - id: "cov-04-gaps-tests"
    content: "Prioritize tests for pure helpers, argparse branches, and non-PTY paths; defer flaky PTY unless high value."
    status: completed
  - id: "cov-05-gap-doc"
    content: "Optional: add dated coverage-gap markdown under docs/osx/ (pattern from network-tools/capture test-coverage-analysis.md) when baseline exists."
    status: completed
isProject: false
---
# Plan 11 — Code coverage reporting and coverage-driven tests


**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).

## Scope

Primary code under test: **[`osx/macos_mouse_click.py`](../../../../osx/macos_mouse_click.py)** (single large module). Tests live under **[`osx/tests/`](../../../../osx/tests/)**. Orchestration today: **[`osx/Makefile`](../../../../osx/Makefile)** (`make -C osx test`, `test-report`, …), **[`osx/pytest.ini`](../../../../osx/pytest.ini)**, CI **[`.github/workflows/macos-mouse-click.yml`](../../../../.github/workflows/macos-mouse-click.yml)** (Python 3.11, `pytest osx/tests`).

This plan adds **measurable coverage**, **repeatable local/CI commands**, and **targeted tests** to raise coverage without destabilizing **darwin-only** and **PTY** suites.

## Prior art (search under `/Users/lblackb/data/lblackb/git`; in-repo examples below)

A quick scan of sibling projects for **how coverage is implemented, reported, and “trended”** did not find Codecov/Coveralls-style PR dashboards in this workspace; **trending** is mostly **dated markdown + artifacts + optional targets**.

| Pattern | Where | Takeaway for `osx/` |
|--------|--------|---------------------|
| **`COV_MODULE` + `test-coverage` Makefile target** | [`LinkedIn-posts/Makefile`](../../../../LinkedIn-posts/Makefile), [`network-tools/capture/Makefile`](../../../../network-tools/capture/Makefile) | Single variable for `--cov=…`; target runs pytest with **html + term + xml** (`--cov-report=html --cov-report=term --cov-report=xml`). Echo where to open `htmlcov/index.html`. |
| **Exclude slow markers on coverage runs** | `LinkedIn-posts` uses `-m "not integration_real"` on `test-coverage` | `osx/Makefile` **`coverage-quick`** runs the full suite (including **`table_nav`** on darwin); use a custom `-m` locally if you need a faster coverage pass. |
| **`clean` removes coverage junk** | Both Makefiles: `htmlcov`, `.coverage`, sometimes `coverage.xml` | Align `make -C osx test-clean` (or `coverage-clean`) with the same list. |
| **Gap analysis / “trend” as a living doc** | [`network-tools/capture/docs/test-coverage-analysis.md`](../../../../network-tools/capture/docs/test-coverage-analysis.md) | Dated snapshot: **current %, target %, gap**, component table, **prioritized missing regions** (e.g. entire `main()` untested). Re-run coverage after milestones and **revise the doc** (or add a new dated section) — this is the main **human trend** mechanism found. |
| **`--cov-config=.coveragerc`** | Mentioned in [`docs/analyze-tcpdump-plan.md`](../../../../docs/analyze-tcpdump-plan.md) (Makefile snippet) | Prefer explicit `--cov-config=osx/.coveragerc` in Makefile so cwd-independent behavior matches capture’s intent. |
| **`pytest-cov` version floor** | Sibling checkout **`better-creds-management`** (`tests/requirements.txt` lists `pytest-cov>=4.1.0`; copies also under `compare-agents/…`) | Pin a minimum (e.g. `pytest-cov>=4.1.0`) alongside pytest 7+ in `osx/requirements-test.txt`. |
| **Optional global cov in `pytest.ini`** | `react2shell-server` (separate checkout): commented `# addopts = --cov=src --cov-report=html` | Prefer **Makefile-driven** cov for `osx/` (like capture) so normal `make test` stays fast; avoid turning on `--cov` for every developer pytest by default. |

**Not found** in sampled `pub-bin` workflows: automated coverage **diff on PRs**, `diff-cover`, or badge generation. Treat those as **Phase 2+ optional** if policy allows third-party tokens.

## Goals

1. **Coverage tooling:** `pytest-cov` (or equivalent) with a checked-in config so `source=` / omit patterns are stable (e.g. omit tests themselves if desired, omit `if TYPE_CHECKING` blocks as appropriate).
2. **Operator UX:** `make -C osx coverage` (or `test-coverage` to match capture naming) producing **terminal** + **HTML** (`htmlcov/`) + **`coverage.xml`** (gitignored except as CI artifact), documented next to existing test targets — **same triple-report pattern** as capture / LinkedIn-posts.
3. **Baseline then deltas:** Establish a **baseline** (commit hash + overall line %). **Trending:** (a) optional **dated gap doc** under `docs/osx/` modeled on capture’s `test-coverage-analysis.md`; (b) **CI artifact** `coverage.xml` / HTML zip for download/compare across runs; (c) later optional `fail_under` once stable.
4. **Coverage-driven tests:** Use the report to find **high-value, low-risk** gaps: pure functions, validation paths, argparse combinations, error branches that do not need a GUI. Avoid chasing **100%** if it requires brittle PTY or Accessibility-dependent paths.

## Non-goals (initially)

- **Codecov / Coveralls** or PR comment bots (optional later; needs token/policy).
- **Merging coverage** from multiple OS jobs (only `macos-latest` today).
- **Rewriting** the script into packages solely for coverage (see separate refactor plans).

## Phased work

### Phase 0 — Baseline

- On **macOS**, from repo root: add `pytest-cov` to **[`osx/requirements-test.txt`](../../../../osx/requirements-test.txt)**, run (from repo root, same as existing Makefile `cd "$(REPO_ROOT)"` pattern):

  `$(venv pytest) osx/tests -c osx/pytest.ini --cov=<module> --cov-report=term-missing`

  Resolve `<module>` the way tests load the script (likely `macos_mouse_click` with `PYTHONPATH=osx` or `--cov=osx.macos_mouse_click` depending on import path — verify once).

- Note **overall line %** and top **uncovered** functions (especially `main`, Rich paths, Quartz-guarded blocks).

### Phase 1 — Tooling in repo

- Add **`pytest-cov`** to `requirements-test.txt` with a lower bound compatible with pytest 7+ (see prior art for version pinning style).
- Add **`osx/.coveragerc`** (or repo root with documented choice): branch coverage optional; `omit` for tests if policy is “production module only”; `relative_files = true` if useful for CI paths; optional `fail_under` **commented** until baseline exists.
- **Makefile:** add `COV_MODULE` (or inline) and a **`coverage` / `test-coverage`** target mirroring capture: `--cov=$(COV_MODULE) --cov-report=html --cov-report=term --cov-report=xml` plus **`--cov-report=term-missing`** if supported alongside `term` (or use `term-missing` instead of plain `term`). Pass **`--cov-config=osx/.coveragerc`** when file exists. Write HTML under **`osx/htmlcov/`** if pytest is run from repo root with cwd considerations — **document** actual paths.
- **`.gitignore`:** `htmlcov/`, `.coverage`, `coverage.xml` under `osx/` (or repo root — match where files land).
- **`osx/README.md`:** “Coverage” section: install, `make` target, open `htmlcov/index.html`, where `coverage.xml` goes for CI.

### Phase 2 — CI (optional but valuable)

- Extend **`.github/workflows/macos-mouse-click.yml`**: prefer **one** pytest invocation that produces **JUnit + coverage XML** (if both are needed) to avoid doubling macOS runner time; **upload-artifact** for `coverage.xml` and optionally a **zip of `htmlcov/`** for human diff between workflow runs (“trend by download”).
- Do **not** fail the job on coverage threshold in v1 unless the team wants a **floor** (e.g. `fail_under` in config) after baseline is stable.

### Phase 3 — Tests to improve coverage (prioritized)

Use the HTML / missing-line report to queue work:

1. **Pure / IO-light helpers** (keyboard parsing, config resolution, dry-run JSON helpers): unit tests with no Quartz.
2. **Argparse / exit codes** for invalid combinations: subprocess or direct `parse_args` where safe.
3. **Branches shared by `-Y` and TTY** already partially covered by dry-run; extend only where missing lines are **deterministic**.
4. **Rich / PTY** only where prior plans (**plan-003**, DEF-009 tests) show stable patterns; do not block coverage goals on flaky full-table drives.

Document in PRs which **lines** or **functions** each new test is meant to cover (brief).

**cov-04 closure (2026-04):** Added [`osx/tests/test_learn_collect_helpers.py`](../../../../osx/tests/test_learn_collect_helpers.py) for **`learn_collect_plain_text_line`** and **`emit_learn_collect_dry_run_stdout_samples`** (pure stdout paths, no Quartz). Further argparse / `main()` gaps remain fair game for follow-up PRs.

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
