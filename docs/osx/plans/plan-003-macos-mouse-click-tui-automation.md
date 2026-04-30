---
todos:
  - id: add-plan-03
    content: "Write docs/osx/plans/plan-003-macos-mouse-click-tui-automation.md (scope, phases, CI)"
    status: completed
  - id: phase-0-test-hooks
    content: "Phase 0: Refactor — separate TUI resolution from Quartz; dry-run / SKIP_QUARTZ hook"
    status: completed
  - id: phase-1-pty-tests
    content: "Phase 1: PTY/pexpect tests for pre-Quartz TUI (keys, wheel CSI, cancel/start)"
    status: completed
  - id: phase-2-subprocess-tests
    content: "Phase 2: Subprocess tests for -Y, piped stdin, legacy --interactive (no PTY where possible)"
    status: completed
  - id: phase-3-ci
    content: "Phase 3: macOS CI job (pytest), optional Python version matrix"
    status: completed
  - id: phase-4-docs-trim-manual
    content: "Phase 4: Update plan 02 manual matrix — what stays human vs automated"
    status: completed
  - id: auto-mt-02-implement
    content: "Implement pytest PTY cases for MT-02 (after phase 0 dry-run hook)"
    status: completed
  - id: auto-mt-09-implement
    content: "Implement pytest PTY for MT-09 legacy --interactive + PYTHONPATH fake rich"
    status: completed
isProject: false
---

# Plan 03: Automated testing for macOS clicker TUI (pre-Quartz)


**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).

This document is the **test automation / CI** roadmap for the Rich **pre-run editor** and related stdin paths in [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py). It complements **[`plan-002-macos-mouse-click-terminal-ux.md`](plan-002-macos-mouse-click-terminal-ux.md)** (UX and manual QA) and **[`plan-001-macos-clicker.md`](plan-001-macos-clicker.md)** (click semantics).

## Goals

1. **Automate what does not need Quartz or Accessibility:** navigation, row edit prompts, **S** / **Q** / **Ctrl+C** / **Ctrl+D**, CSI / wheel noise, piped stdin, `-Y` paths — before any synthetic or learn click runs.
2. **Keep manual where hardware/OS integration matters:** real learn anchor tap, fixed clicks at screen coordinates, Accessibility prompts, subjective “readable” layout in odd terminals (optional spot-check).
3. **Run in CI on macOS** without requiring **Accessibility** for the automated slice (use a **dry-run** or **stub Quartz** path after the TUI returns **Start**).

## Table of contents

- [Goals](#goals)
- [Scope](#scope)
- [Phases](#phases)
- [MT-02 automation plan: partial CLI and Rich TUI](#mt-02-automation-plan-partial-cli-and-rich-tui)
- [MT-09 automation plan: legacy interactive without Rich](#mt-09-automation-plan-legacy-interactive-without-rich)
- [Mapping to plan 02 manual tests (MT-xx)](#mapping-to-plan-02-manual-tests-mt-xx)
- [Out of scope (v1)](#out-of-scope-v1)
- [Additional automation backlog (session notes merge)](#additional-automation-backlog-session-notes-merge)

## Scope

| In scope | Out of scope (v1 automation) |
|----------|-------------------------------|
| `read_raw_key` / CSI parsing (pure unit tests after extraction) | Pixel-perfect screenshot diff |
| PTY-driven Rich table loop until dry-run exit | Full **Textual** rewrite |
| Subprocess stderr/exit for pipe + `-Y` | Proving Quartz click landed on a physical pixel |
| PTY + **`PYTHONPATH`** fake **`rich`** for **MT-09** (legacy **`--interactive`**) | Full learn tap in CI without Accessibility (use **Proceed? `n`** or dry-run hook) |
| Optional `MACOS_MOUSE_CLICK_SKIP_QUARTZ` (name TBD) + machine-readable post-TUI output | **DEF-004** field-edit input hygiene — **[plan 07](plan-007-macos-mouse-click-tui-field-edit-input.md)** (deferred) |

## Phases

### Implementation status (repo, 2026-04-18; updated 2026-04-21)

| Item | State |
|------|--------|
| **Phase 0 dry-run** | **Shipped** — CLI `--dry-run-after-start` and env `MACOS_MOUSE_CLICK_DRY_RUN` (`1` / `true` / `yes` / `on`): after the normal **Running:** line, one `MACOS_MOUSE_CLICK_DRY_RUN_JSON …` line on **stderr**, then **exit 0** without `import_quartz()`. Helpers: `resolved_config_for_dry_run_json`, `dry_run_after_start_requested`, `emit_dry_run_json_line` in [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py). |
| **CI** | **`.github/workflows/macos-mouse-click.yml`** — `macos-latest`, Python 3.11, `pip install -r osx/requirements-test.txt`, `pytest osx/tests`. |
| **Tests** | **`osx/tests/`** — subprocess dry-run checks, **MT-09** PTY suite ([`test_mt09.py`](../../../osx/tests/test_mt09.py)), **MT-02** Rich+dry-run **main()** wiring via monkeypatch ([`test_dry_run.py`](../../../osx/tests/test_dry_run.py) `test_mt02_rich_branch_dry_run_skips_quartz`). **Phase 1 / 2 (frontmatter):** **Rich pre-run** PTY coverage now includes **darwin** **`table_nav`** tests: table Down navigation ([`test_rich_table_nav_down_pty.py`](../../../osx/tests/test_rich_table_nav_down_pty.py)), DEF-009/DEF-010 layout + **resize** ([`test_def009_rich_table_layout_pty.py`](../../../osx/tests/test_def009_rich_table_layout_pty.py)), debug NDJSON meta ([`test_debug_tui_logging_meta.py`](../../../osx/tests/test_debug_tui_logging_meta.py)), CSI/SS3 runners — not every plan-02 row is automated, but the earlier “defer full Rich PTY” note is **partially superseded**. Operator **MT-02** remains useful for **subjective** layout and untested terminals. |
| **Plan 02 matrix** | **MT-09** and **MT-02** rows annotated with automation column — see [Manual tests](plan-002-macos-mouse-click-terminal-ux.md#manual-tests-operator-checklist). |

### Phase 0 — Testability refactor

- Split **“resolve config via CLI + TUI”** from **“import Quartz and run clicks”** so tests can stop after the editor without loading PyObjC.
- Add a **test-only hook** (environment variable and/or `--dry-run-after-editor`) that, after **`run_rich_pre_run_editor`** returns **Start**, prints a stable line (e.g. JSON of `mode`, `count`, `delay`, `x`, `y`) and **exits 0** without calling `import_quartz()`.

### Phase 1 — PTY integration tests (macOS, `rich` installed)

- Use **`pexpect`** or **`pty` + subprocess** to spawn the script with the hook from phase 0.
- Feed bytes for **Up** / **Down** / **Enter** / **S** / **Q** / **Ctrl+D** / synthetic **mouse wheel** CSI.
- Assert on PTY output: no spurious **`Cancelled.`** for wheel noise; cancel keys still exit **0** with message; **S** produces dry-run line.

### Phase 2 — Subprocess tests (minimal TTY)

- **Piped stdin**, **`-Y`**, **non-TTY** error messages: assert stderr substrings and exit codes (many cases **without** a PTY).
- **MT-09** — **`--interactive`** with **`rich` import disabled** (see **[§ MT-09 automation plan](#mt-09-automation-plan-legacy-interactive-without-rich)**): PTY + scripted stdin; prefer **Proceed? `n`** for a no-Quartz smoke, or **Phase 0** dry-run after **`y`** once the hook exists.

### Phase 3 — CI

- **GitHub Actions** `macos-latest` (or equivalent): install **`rich`**, run **`pytest`** on the new test package.
- Optionally matrix **Python 3.10–3.12**.

### Phase 4 — Documentation and manual matrix trim

- In plan 02, annotate each **MT-xx** with **“automated in plan 03”** vs **“human required”** once tests exist.
- Link this plan from plan 02 **Implementation touchpoints**.

## MT-02 automation plan: partial CLI and Rich TUI

**Manual baseline:** plan 02 **[MT-02](plan-002-macos-mouse-click-terminal-ux.md#manual-tests-operator-checklist)** — operator passed with **no CLI params**, partial CLI mixes, and setting **Mode**, **Count**, and **Delay** in the Rich table (no legacy `--interactive` prompts).

### Goal

Automate confidence that when the CLI omits one or more of **mode / count / delay**, the **Rich pre-run editor** appears and the resolved configuration matches TUI edits—**without** running Quartz (until a deliberate follow-on test).

### Preconditions

- **Phase 0** (see [Phases](#phases) — *Testability refactor*): dry-run / `SKIP_QUARTZ` (name TBD) so the child process can exit **0** after **S** with a machine-readable summary line.
- **macOS** test host with **`rich`** installed; PTY available (`pexpect` or stdlib `pty` + `select`).
- Tests **skip** on non-macOS unless the hook is ported (not required for v1).

### PTY scenarios (implement as `pytest` cases)

| Case ID | CLI | Driver outline | Pass criteria |
|---------|-----|------------------|---------------|
| **MT-02-A** | No argv (`./osx/macos_mouse_click.py`) | Wait for Rich panel; **Enter** on **Mode** → confirm **learn** (or type `learn` + Enter); adjust **Count** / **Delay** or accept defaults; press **S** | Panel strings present (e.g. `review / edit`); **no** `Select mode:` / numbered legacy menu; dry-run line shows `mode=learn` and expected `count` / `delay` |
| **MT-02-B** | Partial flags only (e.g. `-n 7` **without** `--learn`, if `validate_ns` allows) | Same as A; ensure TUI still opens and mode is set via editor | CLI **count** preserved when not overridden; mode sourced from **tui** after edit |
| **MT-02-C** | `-d 2` only (or another minimal combo that yields **empty mode** + TTY + `rich`) | Fill **Mode** first, then **S** or dry-run | No `run_interactive_prompts` text on stderr |

Exact argv rows depend on `validate_ns` / `main()` rules—trim or extend the matrix when implementing; **MT-02-A** is the required happy path.

### Driver mechanics

1. Spawn child with **PTY**, `env` including dry-run flag + `PYTHONUNBUFFERED=1`, cwd repo root.
2. **Synchronize** on stable Rich output substrings (prefer title / subtitle over full table layout to reduce flake on terminal width).
3. Send **raw** bytes for table navigation (`read_raw_key`: arrows, **Enter**, **S** / **Q**) and **cooked** lines for `Console.input` prompts after **Enter** on a row.
4. Prefer **Q** after assertions for faster tests; use **S** + dry-run assert for full “would start” path.
5. **Negative:** with `rich` + TTY + no `-Y`, assert stderr does **not** contain legacy `--interactive` prompt blocks from `prompt_mode_interactive` unless `--interactive` was explicitly passed.

### CI and ownership

- Run under **`macos-latest`** in Phase 3; tag tests `@pytest.mark.mt02` or `test_mt02_partial_cli_tui.py`.
- **Done when:** **MT-02-A** (and at least one **MT-02-B**-style partial CLI) green in CI; plan 02 MT-02 row notes **automated** with pointer to this section.

**Todo:** `auto-mt-02-implement` (frontmatter) tracks implementation; this section is the **spec** only.

## MT-09 automation plan: legacy interactive without Rich

**Manual baseline:** plan 02 **[MT-09](plan-002-macos-mouse-click-terminal-ux.md#mt-09-operator-one-liner-hide-rich)** — operator verified **legacy stdin** flow (**Tip:**, **Select mode**, counts, **Resolved configuration**, **`Proceed?`**, **Running:**) using a **one-liner** that shadows **`rich`** via **`PYTHONPATH`** (no uninstall).

### Goal

Automate regression coverage for **`run_interactive_prompts`** + **`print_confirmation_sheet`** + **`confirm_or_abort`** when **`try_import_rich()`** returns **`None`**, without requiring operators to uninstall **Rich**.

### Preconditions

- **macOS** host (script entrypoint is macOS-specific for full runs; pre-Quartz assertions are still useful on the same OS the tool ships for).
- Child process attached to a **PTY** (`pexpect` or **`pty` + subprocess**): **stdin must be a TTY** for **`--interactive`** (`run_interactive_prompts` exits **2** if not).
- **`PYTHONPATH`** prefix containing a throwaway **`rich.py`** that raises **`ImportError`** (same pattern as plan 02 one-liner); set **`PYTHONUNBUFFERED=1`**.
- **Optional (preferred after Phase 0):** dry-run / **`SKIP_QUARTZ`** hook so the driver can answer **`Proceed? y`** and assert machine-readable output **without** Accessibility / learn tap.

### PTY scenarios (implement as `pytest` cases)

| Case ID | stdin script (outline) | Pass criteria |
|---------|------------------------|-----------------|
| **MT-09-A** | Choice **`1`** (learn), accept defaults or small **count** / **delay**, then **`n`** at **`Proceed?`** | Stderr contains **`Select mode:`**, **`Resolved configuration:`**, **`Proceed?`**, then **`Cancelled.`**; **no** **`Running:`** line (confirm aborts before Quartz); exit **0**; **no** Rich panel markers (e.g. no **`review / edit`**); **no** **`Waiting for your first left click`**. |
| **MT-09-B** | Same prompts, **`y`** at **`Proceed?`**, then **Phase 0** dry-run env active | After **`Running:`**, child prints stable **dry-run** line / JSON and **exits 0** without **`import_quartz()`** (requires Phase 0 hook in `main()`). |
| **MT-09-C** (negative) | Same **`PYTHONPATH`** trick but **omit** **`--interactive`** and **omit** mode flags | Child prints **`Error: specify --learn`** … **`or use --interactive`** …; exit **2**. |

**Synchronization:** wait for **`Tip: install rich`** (stderr) or **`Select mode:`** before sending the first choice — avoids flake on slow startup.

### Driver mechanics

1. `tmpdir = tempfile.mkdtemp()`; write `rich.py` with `raise ImportError("mt09 test")`; `env = {**os.environ, "PYTHONPATH": tmpdir, "PYTHONUNBUFFERED": "1"}` (prepend `tmpdir` to any existing **`PYTHONPATH`** with `os.pathsep` if tests need to preserve it).
2. Spawn: `./osx/macos_mouse_click.py --interactive` from **repo root** with PTY + `env`.
3. Feed **cooked** lines (`1\n`, `2\n`, `1.0\n`, …) matching `prompt_str` / `prompt_int_count` prompts.
4. Tear down: assert log does **not** contain Rich table path strings unless the fake **`rich`** import was misconfigured.

### CI and ownership

- Run under **`macos-latest`** with the **MT-09** cases tagged (e.g. `@pytest.mark.mt09`).
- **Done when:** **MT-09-A** (and **MT-09-C**) green in CI without Accessibility; **MT-09-B** enabled once Phase 0 lands.
- **Todo:** `auto-mt-09-implement` (frontmatter).

## Mapping to plan 02 manual tests (MT-xx)

| MT | Automation potential (after phases) |
|----|-------------------------------------|
| MT-01 | **Partial** — PTY covers pre-Quartz TUI; **learn + real clicks + Accessibility** stay manual |
| MT-02 | **High** — PTY + partial CLI — see **[§ MT-02 automation plan](#mt-02-automation-plan-partial-cli-and-rich-tui)** |
| MT-03 | **Medium** — subprocess; still hits Quartz after `-Y` (short run or mock) |
| MT-04 | **Medium** — subprocess `-Y` learn |
| MT-05 | **Medium** — subprocess `-Y` fixed |
| MT-06 | **High** — pipe + assert stderr |
| MT-07 | **High** — pipe + `-Y` |
| MT-08 | **Partial** — set `COLUMNS`/`LINES` in PTY; human for subjective readability |
| MT-09 | **High** — PTY + **`PYTHONPATH`** fake **`rich`** + scripted stdin — see **[§ MT-09 automation plan](#mt-09-automation-plan-legacy-interactive-without-rich)**; operator checklist **completed** **2026-04-18** |

## Out of scope (v1)

- Running the full **learn** event tap in unattended CI without a stub.
- Cross-platform Linux CI for macOS-only Quartz behavior (pre-Quartz tests can still run on macOS only).

## Additional automation backlog (session notes merge)

*Design-only items that lived under **`docs/osx/plans/agent/`** are consolidated here so **`plan-003`** remains the single test/CI roadmap.*

- **Dry-run naming (draft “plan 10” idea):** unify **`--dry-run`** semantics with today’s **`--dry-run-after-start`** / **`MACOS_MOUSE_CLICK_DRY_RUN`** only when a product decision renames flags; until then keep one documented pair of hooks.
- **Test helper DRY:** factor shared PTY/spawn helpers across **`osx/tests/`** after child runners stabilize (avoid premature abstraction).
- **Coverage reporting:** optional **`pytest-cov`**, Makefile/CI surfacing, targets in **`docs/osx/macos-mouse-click-coverage-gap.md`**.
- **Post-start synthetic tests (“plan 13” idea):** Tier 1 — mock **`post_synthetic_click`**, **`sleep_interruptible`**, **`wait_for_anchor_click`**; Tier 2 — optional **CGEventTap** observer + subprocess SUT, **env-gated** so default CI stays lightweight.
- **Docs hub paths:** **`osx/tests/test_docs_osx_hub_paths.py`** guards canonical **`docs/osx/**`** entry points (**DEF-009** class hygiene).

