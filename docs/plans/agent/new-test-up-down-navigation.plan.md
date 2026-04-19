<!-- Cursor agent plan (canonical copy in-repo; do not use ~/.cursor/plans/). -->
---
todos:
  - id: "plan-doc"
    content: "Add this plan file under docs/plans/agent/ (no code changes in same commit if split)"
    status: completed
  - id: "runner-up-arrow"
    content: "Add new child runner script (separate from csi_pty_child_runner.py) for staggered CSI-A and SS3-A PTY injection"
    status: pending
  - id: "pytest-up-module"
    content: "Add new test module (separate from test_read_raw_key_csi.py) with darwin-gated tests calling the new runner"
    status: pending
  - id: "table-down-nav-pty"
    content: "Rich settings table: capture highlight + row below, send Down once, assert new highlight equals prior row-below (see Normative test case 1)"
    status: pending
  - id: "table-two-down-labels"
    content: "Second test function: learn/at-cursor table only; Mode -> Count -> Delay (s) after two Downs (see Normative test case 2)"
    status: pending
  - id: "precondition-initial-mode-row"
    content: "Before any stdin: assert highlighted row is Mode and Value matches argv/defaults (see Precondition assertions)"
    status: pending
  - id: "phase-1-tests-only"
    content: "Phase 1: add all new tests/runners; no production code changes; failures allowed (see Implementation phases)"
    status: pending
  - id: "phase-2-debug-tui"
    content: "Phase 2: DEBUG_TUI stderr + optional DEBUG_TUI_LOG file sink; tests assert parsed lines vs expected UI; tmp_path + teardown (see Phase 2 — Logging design)"
    status: pending
  - id: "phase-2-logging-meta-tests"
    content: "Phase 2: add meta-tests from 'Expected test cases (validate logging)' list (gate, JSON, file duplicate, no stdout pollution, etc.)"
    status: pending
  - id: "phase-3-fix-production"
    content: "Phase 3: fix macos_mouse_click.py (etc.) until new tests pass; remove xfail/marker gating if used"
    status: pending
  - id: "verify-ci"
    content: "After Phase 3: make -C osx test-quick green; existing CSI/SS3 down tests unchanged"
    status: pending
isProject: false
---
# Plan: New independent test for Up/Down (TTY) navigation diagnosis

## Goal

Add **new** automated coverage to narrow the “settings table Up/Down / highlight” problem without modifying existing tests or the current CSI **Down** harness. Work may proceed in two tracks: (1) low-level **`read_raw_key`** symmetry for **Up** (`A`), and (2) **end-to-end** Rich table behavior: **normative test case 1** (one Down, `A`/`B`/`C`), and **normative test case 2** (two Downs, explicit **Setting** labels **Mode → Count → Delay (s)** with specific CLI constraints).

All implementation work is split into **three phases** (see **Implementation phases** below): **Phase 1** lands tests only; **Phase 2** adds **debugging visibility** in production code (gated, no intended behavior change); **Phase 3** fixes production code so the Phase 1 tests **pass**.

## Implementation phases

### Phase 1 — Tests only (no production code changes)

- **Scope:** Add new test modules, child runners, fixtures, and documentation per this plan (including low-level Up-arrow PTY tests and Rich table tests as specified).
- **Production code:** **Do not** change [`osx/macos_mouse_click.py`](../../osx/macos_mouse_click.py) or any other **non-test** code—including **no** debug logging yet. Existing third-party constraints (e.g. do not alter `csi_pty_child_runner.py` unless policy changes) remain.
- **Pass/fail:** New tests **may fail** on purpose in this phase; failures document the defect and lock in expected behavior for **Phase 3** (after Phase 2 instrumentation exists).
- **CI / default pytest:** If the project requires a **green** default test run on `main` while Phase 1 is incomplete, either (a) land tests as **`@pytest.mark.xfail`** with a clear reason and issue/plan link, (b) register a **separate marker** (e.g. `table_nav`) and exclude it from the default `make test-quick` collection until **Phase 3**, or (c) accept a red CI until **Phase 3**—**pick one** when implementing and record it in the PR / plan 02 if needed. (Phase 2 adds stderr logs but does not require tests to pass.)

### Phase 2 — Debugging visibility (gated production instrumentation)

- **Scope:** Add **env-gated** diagnostic output in [`osx/macos_mouse_click.py`](../../osx/macos_mouse_click.py) per **Debugging visibility** → **Phase 2 — Logging design**: `MACOS_MOUSE_CLICK_DEBUG_TUI=1`, lines on **stderr**, optional duplicate to path in **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`** when set (default unset = stderr only).
- **Intent:** **Instrumentation only**—no functional change to navigation or `read_raw_key` semantics; if behavior changes accidentally, treat as a bug.
- **Preconditions:** Phase 1 tests are merged (they may still fail).
- **Tests (required in Phase 2):** Update the **new** table-navigation tests from Phase 1 so that, when `MACOS_MOUSE_CLICK_DEBUG_TUI=1` is set on the subprocess, they **parse** each `MACOS_MOUSE_CLICK_TUI_STATE` line from **`subprocess.stderr`** and/or from the file named by **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`** when the test sets that env to a unique path under `tmp_path` (same line format in both sinks) and **assert** that the logged **`setting_label`** and **`value_text`** (and optionally **`row_key`**, **`selected_index`**) **match the same expected values** the test already derives for the **UI layer** (preconditions for **Mode**, expected **Count** / **Delay (s)** after each Down, and any **stdout**-parsed row identity where both views exist). Purpose: prove the **internal highlight state** the script logs is **consistent with** what the test claims the Rich table shows—if stderr and stdout expectations diverge, the test or parser is wrong; if stderr is correct but stdout assertions fail, fix **stdout parsing** in Phase 3; if stderr is wrong, fix **selection logic** in Phase 3. **Do not weaken** Phase 1 stdout assertions when adding stderr checks—add **correlation** assertions (and keep running with debug **on** for these tests once Phase 2 lands, or document turning debug on only for failing diagnostics).

- **Logging meta-tests (required in Phase 2):** Add tests that implement the checklist **Phase 2 — Expected test cases (validate logging is wired correctly)** below (gate off/on, JSON schema, file duplicate vs stderr, no stdout pollution, optional truncate and unwritable-path behavior).

### Phase 3 — Fix production code

- **Scope:** Change [`osx/macos_mouse_click.py`](../../osx/macos_mouse_click.py) (and any other production modules) so the Phase 1 tests **pass** without weakening assertions.
- **Preconditions:** Phases 1–2 complete; remove `xfail` / re-enable markers as appropriate before declaring done.
- **Verification:** `make -C osx test-quick` (or the agreed CI target) is green including the new tests.

## Constraints (non-negotiable)

- **Do not edit** existing test files (e.g. [`osx/tests/test_read_raw_key_csi.py`](../../osx/tests/test_read_raw_key_csi.py)) or [`osx/tests/csi_pty_child_runner.py`](../../osx/tests/csi_pty_child_runner.py)) except if a future defect fix *requires* it—this plan assumes **zero** changes there.
- **New top-level scripts stay separate:** one dedicated **child runner** per workstream, one dedicated **pytest module** per workstream. Reuse **patterns** (handshake pipe, `pty.fork`, `PYTHONPATH`, staggered writes) by copy or thin shared helper **only if** it does not force merging runner entrypoints; prefer **copy** over premature abstraction per DRY plan optional phase.
- **Reuse without entanglement:** [`osx/tests/conftest.py`](../../osx/tests/conftest.py) path fixtures, [`osx/tests/pty_harness.py`](../../osx/tests/pty_harness.py) constants if imported, same `OSX_DIR` / `cwd=repo_root` convention as CSI tests.

## Debugging visibility (correlate script state with what the test “sees”)

Rich draws the table to **stdout**. Debug lines must go to **stderr** (and may **duplicate** to an optional **file** path from env) so PTY tests can **capture** diagnostics without writing debug bytes into the Rich **stdout** stream.

### Option A — Gated diagnostics in `run_rich_pre_run_editor` (recommended)

- **Summary:** Phase 2 adds env-gated, line-oriented **TUI state** logs (see **Phase 2 — Logging design** below). **Phase schedule:** land in **Phase 2** only—not in Phase 1. **Phase 3** applies functional fixes.

### Phase 2 — Logging design (how debug values are emitted)

#### Activation

- **`MACOS_MOUSE_CLICK_DEBUG_TUI`:** When set to a **truthy** value (e.g. `1`, `yes`), the editor emits debug lines. When **unset** or empty, **no** TUI debug lines (current behavior).

#### Line format (stable for parsers)

- Each event is **one line**, **UTF-8**, newline-terminated.
- **Prefix** fixed for grep/substring tests, e.g. `MACOS_MOUSE_CLICK_TUI_STATE ` (note trailing space) immediately followed by a **single JSON object** (no pretty-print; use `json.dumps(..., separators=(",", ":"))` in implementation notes).
- **Payload fields** (minimum agreed contract): `selected_index` (int), `row_key` (string, e.g. `mode`), `setting_label` (string, e.g. `Mode`), `value_text` (string), optional `source` (string), optional `last_key` (string, value last returned by `read_raw_key()` for that loop iteration).
- **When to emit:** (1) **After draw** — immediately after the table is built and printed for the loop iteration, `selected` / `row_keys` finalized. (2) **After input** — immediately after `read_raw_key()` returns, same schema plus `last_key` so tests correlate key → state. (Same line shape for both; use a `phase` or `event` field in JSON if implementers want one discriminant: `draw` vs `after_key`.)

#### Log sinks: stderr and optional file

- **stderr (default sink when debug is on):** Always write the same line to **stderr** when `MACOS_MOUSE_CLICK_DEBUG_TUI` is truthy. This preserves **operator** visibility in a normal terminal run and lets tests use `subprocess.run(..., capture_output=True).stderr` without configuring a file.
- **Optional file sink — env `MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`:** When **set** to a non-empty string, treat it as a **filesystem path** (absolute recommended in tests). Open that path in **append** or **truncate-on-first-open** mode (pick one in implementation and document: **truncate once per process** when the editor starts avoids stale lines from prior runs; **append** is friendlier to long sessions—**prefer truncate-on-open** for test determinism). Write the **identical** line bytes as stderr (same prefix + JSON + `\n`). **`flush()`** (or line-buffered text IO) after **each** line so tests can read the file **between** synthetic key injections without waiting for process exit.
- **Default for `MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`:** **Unset / empty** means **stderr only** — no file is created, no default path under `/tmp` (avoids surprise files, permission issues, and **parallel pytest** collisions). This is the **reasonable default**: opt-in file by explicit path.
- **Caller override (tests):** Pass `MACOS_MOUSE_CLICK_DEBUG_TUI_LOG=str(tmp_path / "tui_state.log")` (or `pytest` `tmp_path_factory` / per-worker unique path for **xdist**) so each test has a **unique** file, can **tail** or read fully, and **`unlink`** in a `finally` / fixture teardown. Same pattern for any subprocess wrapper script.
- **Security / hygiene:** The script must **not** log secrets; path is **caller-controlled** (trusted in tests). Document that arbitrary paths are the operator’s responsibility.

#### Implementation sketch (for Phase 2 code)

- Lazy-open file handle on first log line when `MACOS_MOUSE_CLICK_DEBUG_TUI_LOG` is set; register `atexit` or close in `finally` of editor loop is optional; simplest is **open per line** with append (slow but test-simple) or hold one file handle for editor lifetime.
- Use a tiny helper `_debug_tui_line(obj: dict) -> None` that serializes JSON, writes to stderr, optionally duplicates to the log path, flushes both.

#### How tests consume output

- **stderr path:** Parse `result.stderr.decode("utf-8")`, splitlines, filter `startswith("MACOS_MOUSE_CLICK_TUI_STATE ")`, `json.loads` remainder.
- **File path:** Read path passed in env after subprocess step (or open in parent in parallel—usually read after child yields). Prefer **file** when stderr is noisy (Rich / warnings); prefer **stderr** when no tmp desired.
- **Phase 2 assertions:** Compare parsed `setting_label` / `value_text` (and friends) to **expected** values derived from CLI + `_row_display` rules, in lockstep with stdout-based UI assertions.

### Phase 2 — Expected test cases (validate logging is wired correctly)

These are **meta-tests** for the logging machinery itself (in addition to table-navigation tests that **use** the logs for correlation). They should land in **Phase 2** in a **dedicated test module or functions** so regressions in the sink/format/gate are caught without conflating them with Rich navigation failures.

1. **Gate off:** With `MACOS_MOUSE_CLICK_DEBUG_TUI` **unset** (and `MACOS_MOUSE_CLICK_DEBUG_TUI_LOG` unset), run a subprocess that reaches the Rich editor briefly (or a minimal harness that calls the debug helper if extracted); **stderr** must contain **no** line starting with `MACOS_MOUSE_CLICK_TUI_STATE `.

2. **Gate on — stderr present:** With `MACOS_MOUSE_CLICK_DEBUG_TUI=1` and **no** log path env, stderr must contain **at least one** `MACOS_MOUSE_CLICK_TUI_STATE ` line after the table first renders.

3. **JSON contract:** Every `MACOS_MOUSE_CLICK_TUI_STATE ` line must parse with `json.loads`; each object must include **`selected_index`** (int), **`row_key`** (str), **`setting_label`** (str), **`value_text`** (str). If **`event`** / **`phase`** / **`last_key`** are implemented, assert types and allowed values (`draw` / `after_key`, etc.).

4. **Internal consistency on first draw:** For the **first** `draw` (or first emitted state line after startup), assert **`row_key`** equals `editor_row_keys(cfg)[selected_index]` for that scenario (e.g. `mode` at index `0` for learn + default selection).

5. **File sink — created and duplicate:** With `MACOS_MOUSE_CLICK_DEBUG_TUI_LOG` set to a path under `tmp_path`, the file **exists** after logging, is **UTF-8** text, and each line in the file that starts with the prefix is **byte-identical** to the corresponding emitted stderr line (same order for the same run), **or** the multiset of prefixed lines in stderr equals that in the file (document which equality rule the implementation guarantees).

6. **File default unset:** With debug on but **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG` unset**, **no** file is created at a hidden default path (assert path does not exist or list tmp is clean if using isolated `TMPDIR`).

7. **No stdout pollution:** **`MACOS_MOUSE_CLICK_TUI_STATE`** prefix must **not** appear in **stdout** (only on stderr / log file).

8. **Truncate-on-open (if chosen):** Run two sequential subprocesses that both write to the **same** log path; the second run’s file content must **not** include stale prefixed lines from the first run (unless append semantics are explicitly chosen and this test is skipped).

9. **After-key line follows draw:** In a controlled subprocess that sends **one** known key (e.g. Down), assert there is an **`after_key`** (or equivalent) line whose **`last_key`** is **`down`** (or empty/`other` as designed) and that a subsequent **`draw`** line reflects updated `selected_index` if navigation succeeded.

10. **Unwritable log path (optional):** If `MACOS_MOUSE_CLICK_DEBUG_TUI_LOG` points to an invalid or unwritable path, the editor must **not** crash; stderr-only or a documented fallback applies—assert process still runs and stderr logging still works.

### Option B — Test-only wrapper (no `macos_mouse_click.py` edits in Phase 1)

- A tiny **test helper** subprocesses the real script but **records** full PTY transcript; tests assert on stderr if the script already emits useful lines (e.g. existing `Running:` / errors), or compare **snapshots** of stdout slices between Down events. Heavier and still brittle for highlight detection unless **Phase 2** Option A exists.

### Option C — Parse what the human sees (no script change)

- Keep asserting on **stdout** Rich output only; document **regex / snapshot** fragility. Use **smallest terminal geometry** (see `pty_harness` `COLUMNS`/`LINES`) to stabilize wraps.

### Validation workflow

1. Run the failing test with `MACOS_MOUSE_CLICK_DEBUG_TUI=1`; collect **`capture_output=True` stderr** and/or read the file path passed in **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`** after each interaction step (`capfd` does not cross subprocess).
2. **Codify in tests (Phase 2):** After each table draw or each key event boundary, assert parsed JSON (from **stderr** and/or **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`**) **`setting_label` / `value_text`** equal the **expected** strings computed from CLI + `_row_display` rules (same as normative preconditions and case 2 label sequence). Optionally assert the latest line agrees with the **stdout-parsed** highlighted row label when both are available.
3. If parsed TUI state lines match expectations but stdout assertions fail, prioritize **stdout / Rich parser** fixes in Phase 3. If parsed lines are wrong, prioritize **`run_rich_pre_run_editor` / `selected`** in Phase 3.

---

## Normative test case 1: single Down and row-below match (confirmed)

This section records the **intended** behavior and assertions for a test that mirrors a real user: run [`osx/macos_mouse_click.py`](../../osx/macos_mouse_click.py), use the **Rich settings table**, and press **Down** once.

### Steps

1. Start `osx/macos_mouse_click.py` in the configuration that shows the **Rich pre-run editor** (TTY + Rich; same path a user would use to reach the settings table—exact argv/env is an implementation detail).

2. **Before any key**, capture from the rendered UI (what the test can observe on the PTY, e.g. stdout after the table is drawn):

   - **`A`** — identifying content of the **currently highlighted** row (e.g. the **Setting** label such as `Mode`, or another stable token that uniquely identifies that row in the table).

   - **`B`** — identifying content of the **row directly below** the highlighted row (the **next** row in the list).

### Precondition assertions (before any stdin input)

Run these **after** the table is visible and **before** sending arrow keys or any other input to `osx/macos_mouse_click.py`. If a precondition fails, **do not send Down**—fail fast so failures distinguish “wrong initial UI state” from “wrong navigation after key”.

- **(i) Expected first row / highlight:** The Rich pre-run editor initializes **`selected = 0`**, which corresponds to the **`Mode`** row (first key in [`editor_row_keys`](../../osx/macos_mouse_click.py)). Assert the **highlighted** row’s **Setting** resolves to **`Mode`** (same label shown in the **Setting** column for that row).

- **(ii) Expected Mode value:** Assert the **Value** column (and optionally **Source**) for that highlighted **Mode** row matches the **resolved configuration** for the **`argv` / CLI flags and defaults** used to launch the script in that test (e.g. `--learn`, `-n`, `-d`, fixed coordinates, etc.). The test should derive the expected strings from the same rules as runtime (mirroring `_row_display` / `ResolvedConfig` for that invocation) so the precondition stays aligned with product behavior as CLI defaults evolve.

- **(iii) CLI golden vector:** Document the exact `argv` used for the “golden” case so CI and local runs agree; if multiple scenarios are needed later, use parameterized tests each with its own expected **Mode** row **Value** (and sources if asserted).

3. **Send exactly one Down arrow** (the same bytes the terminal would send for Down in that environment).

4. **After the key**, capture from the UI:

   - **`C`** — identifying content of the **new** highlighted row.

### Assertions (required)

- **Preconditions satisfied:** The **Precondition assertions** subsection must pass **before** step 3 (any stdin beyond what was already consumed waiting for the table). If not documented elsewhere, treat failure here as a **fixture or launch** defect, not a navigation defect.

- **`C` equals `B`**: after one Down press, the highlighted row must be the row that was **immediately below** the highlight before the keypress. That is the correct “moved down one row” behavior.

### Assertions (optional)

- When **`A` and `B` are not the same string** (normal case), assert **`C` does not equal `A`**, so the selection actually moved off the original row.

### Clarification (wording)

A literal reading of “first captured value must equal second captured value” where **first** = initial highlight **`A`** and **second** = post-Down highlight **`C`** would imply **no row change** and contradict a successful Down. The **intended** check is **`C` == `B`** (new highlight equals the prior row-below), **not** **`A` == `C`**.

### Implementation notes (for a later phase)

- Parsing **highlight vs non-highlight** from Rich terminal output is **fragile** (ANSI, width, theme). The test harness must define a **stable parse rule** (e.g. regex on “bold black on bright_cyan” / panel content, or a narrow golden-string snapshot for one terminal width) and document brittleness.
- This test is **orthogonal** to the low-level `read_raw_key` **CSI-A / SS3-A** subprocess tests: passing one and failing the other isolates **decode** vs **editor/render** layers.

---

## Normative test case 2: two Down presses — explicit Setting labels (second test function)

Implement as a **separate** pytest test function/method from test case 1 so failures stay attributable (single-step vs multi-step navigation).

### Specific constraints (must hold before implementation)

1. **Table shape:** The process must reach the Rich editor with **`editor_row_keys`** exactly **`["mode", "count", "delay"]`** — i.e. **learn** or **at-cursor** (or any configuration where **Anchor X / Anchor Y** rows are **not** listed). **Do not** use this case’s label expectations when **`cfg.mode == "fixed"`**, because then rows are **Mode**, **Anchor X**, **Anchor Y**, **Count**, **Delay (s)** and the second/third highlighted **Setting** labels after Down are **not** “Count” then “Delay (s)” from the first Down.

2. **Initial highlight:** Same as case 1 — first row is **Mode** (`selected = 0`).

3. **CLI golden vector:** Fix an explicit `argv` in the test (documented in code comment) that satisfies (1), including any **`-n` / `-d`** (or other) flags needed so precondition **(ii)** for the **Mode** row **Value**/sources remains predictable.

### Steps

1. Start `osx/macos_mouse_click.py` per the golden `argv`; wait for the Rich table; run **Precondition assertions** from test case 1 **(i)–(iii)** so the highlighted **Setting** is **Mode** and values match CLI/defaults.

2. **Send first Down arrow.** Capture the highlighted **Setting** column text. **Assert** it equals **`Count`** (the label from [`_row_display`](../../osx/macos_mouse_click.py) for key **`count`**, not the placeholder “(set mode first)” — that only applies when `cfg.mode` is unset; the constrained launch must have a real mode set).

3. **Send second Down arrow.** Capture the highlighted **Setting** column text. **Assert** it equals **`Delay (s)`** (the label for key **`delay`** from `_row_display`).

### Assertions (required) — summary

| Step | Highlighted Setting (label) |
|------|-----------------------------|
| Startup (after preconditions) | **Mode** |
| After 1× Down | **Count** |
| After 2× Down | **Delay (s)** |

### Assertions (optional)

- After the second Down, optionally assert the **Value** cells for **Count** and **Delay (s)** match the configured CLI/defaults (same idea as precondition (ii)) to catch wrong-row binding vs wrong highlight only.

### Failure interpretation

- If case 1 passes and case 2 fails on **first** Down: likely **Count** row / parsing / highlight style, not “row below” logic in the abstract.
- If case 2 fails only on **second** Down: likely **index clamping**, lost key event, or redraw between steps.

---

## Background (low-level track)

- **CSI Down** / **SS3 Down** slow-tail tests already assert `read_raw_key()` returns `"down"` when the final `B` arrives after a long gap (see existing runner + tests).
- **No automated test** currently asserts the symmetric **`"up"`** path (`CSI … A` / `SS3 … A`) under the same PTY timing stress.
- If **Up** tests **fail** while **Down** tests **pass**, investigation should focus on **`read_raw_key`** (A-path, case, or tail parsing). If **Up** tests **pass** but the **table** test fails, focus on **`run_rich_pre_run_editor`**, Rich redraw, or parsing.

## Proposed artifacts — low-level track (implementation phase)

| Artifact | Purpose |
|----------|---------|
| New runner, e.g. [`osx/tests/read_raw_key_up_pty_child_runner.py`](../../osx/tests/read_raw_key_up_pty_child_runner.py) | Same lifecycle as `csi_pty_child_runner.py`: handshake, child `import macos_mouse_click` → `read_raw_key()`, parent injects bytes. **Modes:** e.g. `csi-up` and `ss3-up` (argv), injecting final **`A`** after `_GAP` instead of `B`. |
| New pytest module, e.g. [`osx/tests/test_read_raw_key_up_slow_gap.py`](../../osx/tests/test_read_raw_key_up_slow_gap.py) | Two tests: `_run_runner("csi-up") == "up"`, `_run_runner("ss3-up") == "up"`. **`@pytest.mark.darwin`**, subprocess timeout, assert on returncode + stdout strip. |

**Naming** is illustrative; keep names grep-friendly and distinct from `csi_pty_child_runner` / `test_read_raw_key_csi`.

## Runner behavior (spec) — low-level track

- Reuse the **staggered write** rationale from the Down runner docstring: do **not** write `ESC`+`[` in one syscall then sleep then `A`—use `ESC`, short `_INTER_ESC`, `[` or `O`, `_GAP` (~0.45s), then **`A`**.
- Child prints **`up`** (plus newline) on success—the test asserts string equality to `"up"` (strip newline in test, same as Down tests).

## Interpretation guide (low-level vs table)

| Down tests | New Up tests | Table Down test (`C`==`B`) | Likely focus |
|------------|--------------|------------------------------|--------------|
| pass | pass | fail | `run_rich_pre_run_editor`, Rich output parsing, or redraw—not `read_raw_key` A/B. |
| pass | fail | n/a | `read_raw_key` bug for **A** tail / SS3 **A**. |
| pass | pass | pass | End-to-end OK for this scenario. |

## Proposed artifacts — table track (implementation phase)

| Artifact | Purpose |
|----------|---------|
| New pytest module (and/or new runner script) | **Two** test functions: (1) case 1 — parse **`A`**, **`B`**, send one Down, parse **`C`**, assert **`C` == `B`**; (2) case 2 — preconditions then **Mode → Count → Delay (s)** after two Downs under learn/at-cursor-only CLI constraints. Keep **separate** from `test_read_raw_key_csi.py` and from the low-level Up runner unless a shared library is introduced deliberately. |

## Optional follow-ups

- **Up arrow table test:** same pattern: capture **`A`**, row **above** **`B'`**, send Up, capture **`C'`**; assert **`C'` == `B'`** (new highlight equals prior row-above).
- **Factor shared PTY helpers** into `osx/tests/` only after runners stabilize (aligns with [`docs/plans/agent/osx-dry-refactor.plan.md`](osx-dry-refactor.plan.md)).

## Success criteria

**Phase 1**

- New tests and harnesses exist as specified; **no** edits to `osx/macos_mouse_click.py` (production), including no debug logging.
- Existing DEF-006 tests and [`csi_pty_child_runner.py`](../../osx/tests/csi_pty_child_runner.py) remain **unchanged** and still pass if collected.

**Phase 2**

- Gated **TUI state** logging exists per **Debugging visibility** (stderr when `MACOS_MOUSE_CLICK_DEBUG_TUI` on; optional file duplicate when `MACOS_MOUSE_CLICK_DEBUG_TUI_LOG` set); default **off** / no default file path; no intentional navigation/`read_raw_key` behavior change.
- **Logging meta-tests** pass (checklist **Expected test cases (validate logging is wired correctly)**).
- Table-navigation tests run subprocess with debug env **on**, optionally set **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`** to a **unique** path, **assert** parsed `MACOS_MOUSE_CLICK_TUI_STATE` fields match **expected** highlight **Setting** / **Value** (from stderr and/or log file), **delete** the log file in teardown when used.
- New tests may still **fail** overall until Phase 3; stderr/file correlation assertions should **pass** once logging is correct and expectations are aligned—if those assertions fail while logging is present, fix test expectations or log payload before Phase 3 functional work.

**Phase 3**

- `make -C osx test-quick` passes on macOS with new tests **enabled** (no `xfail` / marker skip unless intentionally kept for unrelated reasons).
- Production fixes are minimal and tied to failing assertions; existing DEF-006 coverage still green.

## Out of scope (this plan document)

- **Markdown-only:** further edits to this file do not change `osx/` code; **Phase 2–3** production work is tracked when those phases run.
- Merging the new low-level runner into `csi_pty_child_runner.py`.
