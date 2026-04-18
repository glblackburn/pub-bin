---
todos:
  - id: add-plan-03
    content: "Write docs/plans/03-macos-mouse-click-tui-automation.md (scope, phases, CI)"
    status: completed
  - id: phase-0-test-hooks
    content: "Phase 0: Refactor — separate TUI resolution from Quartz; dry-run / SKIP_QUARTZ hook"
    status: pending
  - id: phase-1-pty-tests
    content: "Phase 1: PTY/pexpect tests for pre-Quartz TUI (keys, wheel CSI, cancel/start)"
    status: pending
  - id: phase-2-subprocess-tests
    content: "Phase 2: Subprocess tests for -Y, piped stdin, legacy --interactive (no PTY where possible)"
    status: pending
  - id: phase-3-ci
    content: "Phase 3: macOS CI job (pytest), optional Python version matrix"
    status: pending
  - id: phase-4-docs-trim-manual
    content: "Phase 4: Update plan 02 manual matrix — what stays human vs automated"
    status: pending
isProject: false
---

# Plan 03: Automated testing for macOS clicker TUI (pre-Quartz)

This document is the **test automation / CI** roadmap for the Rich **pre-run editor** and related stdin paths in [`osx/macos_mouse_click.py`](../../osx/macos_mouse_click.py). It complements **[`02-macos-mouse-click-terminal-ux.md`](02-macos-mouse-click-terminal-ux.md)** (UX and manual QA) and **[`01-macos-clicker.md`](01-macos-clicker.md)** (click semantics).

## Goals

1. **Automate what does not need Quartz or Accessibility:** navigation, row edit prompts, **S** / **Q** / **Ctrl+C** / **Ctrl+D**, CSI / wheel noise, piped stdin, `-Y` paths — before any synthetic or learn click runs.
2. **Keep manual where hardware/OS integration matters:** real learn anchor tap, fixed clicks at screen coordinates, Accessibility prompts, subjective “readable” layout in odd terminals (optional spot-check).
3. **Run in CI on macOS** without requiring **Accessibility** for the automated slice (use a **dry-run** or **stub Quartz** path after the TUI returns **Start**).

## Table of contents

- [Goals](#goals)
- [Scope](#scope)
- [Phases](#phases)
- [Mapping to plan 02 manual tests (MT-xx)](#mapping-to-plan-02-manual-tests-mt-xx)
- [Out of scope (v1)](#out-of-scope-v1)

## Scope

| In scope | Out of scope (v1 automation) |
|----------|-------------------------------|
| `read_raw_key` / CSI parsing (pure unit tests after extraction) | Pixel-perfect screenshot diff |
| PTY-driven Rich table loop until dry-run exit | Full **Textual** rewrite |
| Subprocess stderr/exit for pipe + `-Y` | Proving Quartz click landed on a physical pixel |
| Optional `MACOS_MOUSE_CLICK_SKIP_QUARTZ` (name TBD) + machine-readable post-TUI output | **DEF-004** input echo fix (track under plan 02 until implemented) |

## Phases

### Phase 0 — Testability refactor

- Split **“resolve config via CLI + TUI”** from **“import Quartz and run clicks”** so tests can stop after the editor without loading PyObjC.
- Add a **test-only hook** (environment variable and/or `--dry-run-after-editor`) that, after **`run_rich_pre_run_editor`** returns **Start**, prints a stable line (e.g. JSON of `mode`, `count`, `delay`, `x`, `y`) and **exits 0** without calling `import_quartz()`.

### Phase 1 — PTY integration tests (macOS, `rich` installed)

- Use **`pexpect`** or **`pty` + subprocess** to spawn the script with the hook from phase 0.
- Feed bytes for **Up** / **Down** / **Enter** / **S** / **Q** / **Ctrl+D** / synthetic **mouse wheel** CSI.
- Assert on PTY output: no spurious **`Cancelled.`** for wheel noise; cancel keys still exit **0** with message; **S** produces dry-run line.

### Phase 2 — Subprocess tests (minimal TTY)

- **Piped stdin**, **`-Y`**, **non-TTY** error messages: assert stderr substrings and exit codes (many cases **without** a PTY).
- **`--interactive`** without **Rich**: assert legacy prompt flow (may need TTY in subprocess).

### Phase 3 — CI

- **GitHub Actions** `macos-latest` (or equivalent): install **`rich`**, run **`pytest`** on the new test package.
- Optionally matrix **Python 3.10–3.12**.

### Phase 4 — Documentation and manual matrix trim

- In plan 02, annotate each **MT-xx** with **“automated in plan 03”** vs **“human required”** once tests exist.
- Link this plan from plan 02 **Implementation touchpoints**.

## Mapping to plan 02 manual tests (MT-xx)

| MT | Automation potential (after phases) |
|----|-------------------------------------|
| MT-01 | **Partial** — PTY covers pre-Quartz TUI; **learn + real clicks + Accessibility** stay manual |
| MT-02 | **High** — PTY + partial CLI |
| MT-03 | **Medium** — subprocess; still hits Quartz after `-Y` (short run or mock) |
| MT-04 | **Medium** — subprocess `-Y` learn |
| MT-05 | **Medium** — subprocess `-Y` fixed |
| MT-06 | **High** — pipe + assert stderr |
| MT-07 | **High** — pipe + `-Y` |
| MT-08 | **Partial** — set `COLUMNS`/`LINES` in PTY; human for subjective readability |
| MT-09 | **Medium** — subprocess TTY without `rich` |

## Out of scope (v1)

- Running the full **learn** event tap in unattended CI without a stub.
- Cross-platform Linux CI for macOS-only Quartz behavior (pre-Quartz tests can still run on macOS only).

