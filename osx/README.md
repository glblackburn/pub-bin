# macOS mouse click (`osx/`)

**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).

Synthetic left-click automation for macOS (see `macos_mouse_click.py` and repo root docs).

## Operator loop (`macos_mouse_click_loop.sh`)

Long-running **`-Y`** buy ladder + cookie burst for local dogfooding. **`-S`** skips the buy ladder and runs only the cookie burst each cycle. **`-k N`** (integer **≥ 1**, default **1**) runs **N** separate cookie **`click_target`** calls per cycle, **each** with the profile’s **`cookie_click_count`** (not one multiplied **`-n`**). **`CYCLE_SLEEP_SECONDS`** from the profile is used as **sleep between** those cookie phases (not after the last). CLI pattern matches the repo **`shell-template.sh`** (`usage` + **`getopts`**). Coordinates can come from a machine-specific profile JSON (recommended) or fallback defaults in the script.

```bash
./osx/macos_mouse_click_loop.sh -h           # usage
./osx/macos_mouse_click_loop.sh -c 1         # one full cycle (real clicks), then exit
./osx/macos_mouse_click_loop.sh -c 10        # ten cycles, then exit
./osx/macos_mouse_click_loop.sh              # loop until Ctrl+C (30s between cycles)
./osx/macos_mouse_click_loop.sh -S -c 1      # cookie burst only (-n 3000), one cycle
./osx/macos_mouse_click_loop.sh -S           # cookie burst only, loop until Ctrl+C
./osx/macos_mouse_click_loop.sh -k 2 -c 1    # two profile-sized cookie bursts + sleep between
./osx/macos_mouse_click_loop.sh -S -k 2 -c 1 # cookie-only: two bursts + sleep between
```

### CV profile detection + preview safety gate

Detect coordinates from a screenshot, then render an annotated preview before clicks:

```bash
# 1) Detect profile JSON from screenshot (OpenCV-based heuristics)
./osx/cookie_clicker_detect_coords.py \
  --input "docs/osx/screenshots/cookie-clicker/Screenshot_2026-04-25_at_8.28.45_PM.png" \
  --output /tmp/cookie-profile.json

# 2) Render click preview only (annotated PNG + manifest JSON)
./osx/macos_mouse_click_loop.sh -P /tmp/cookie-profile.json -N

# 3) Run real clicks only after review (requires matching preview manifest)
./osx/macos_mouse_click_loop.sh -P /tmp/cookie-profile.json -R -A -c 1
```

The helper scripts auto-reexec with `osx/.venv/bin/python3` when available, so direct `./osx/*.py` runs are the default workflow.

If you prefer explicit interpreter usage:

```bash
./osx/.venv/bin/python3 ./osx/cookie_clicker_detect_coords.py --help
./osx/.venv/bin/python3 ./osx/cookie_clicker_preview_plan.py --help
```

`make -C osx` targets (`setup`, `detect-cookie-clicker`, `preview-cookie-clicker`) already use the venv Python.

Helper scripts:

- **`osx/cookie_clicker_detect_coords.py`**: creates profile JSON with cookie + ladder coordinates and confidence metadata.
- **`osx/cookie_clicker_preview_plan.py`**: renders click targets and per-target click counts into an annotated PNG and JSON manifest.
- **`osx/cookie_clicker_golden_sweeper.py`**: plan-015 **v0** — poll for golden-ish blobs, emit **`x y`** / JSONL (see **`docs/osx/plans/plan-015-cookie-clicker-golden-cookie-sweeper.md`**). Executable like the other `osx/*.py` helpers (shebang + **`osx/.venv`** re-exec). **`--capture display`** uses **`screencapture`**; by default each poll’s PNG is written under **`docs/osx/screenshots/golden-sweeper-captures/`** (that path is **gitignored** — local captures only). When hits are found, the saved PNG is **overwritten** with boxes, centroids, and **confidence** labels. A **JSONL** sidecar with the same basename and **`.json`** (one object per line: `x`, `y`, `confidence`, etc.) is written beside that PNG (or beside **`--input-image`**). Use **`--no-capture-save`** for temp-only captures. Example: `./osx/cookie_clicker_golden_sweeper.py --capture display --dry-run --max-wall-seconds 5 --output json`.

**Roadmap:** **`cookie_clicker_golden_sweeper.py`** is a **v0 heuristic** (HSV blobs); **`macos_mouse_click_loop.sh` integration** (plan-015 §7) is still optional / future. Normative spec: **[plan-015](../docs/osx/plans/plan-015-cookie-clicker-golden-cookie-sweeper.md)**.

Loop flags for profile workflow:

- **`-k <n>`** post-ladder cookie burst **count** (**n ≥ 1**, default **1**). **n** separate cookie **`click_target`** invocations per cycle (profile **`cookie_click_count`** each); **`CYCLE_SLEEP_SECONDS`** sleep between phases. See plan-014 / DEF-013. Works with **`-S`**.
- **`-P <profile_json>`** profile to use for dynamic coordinates. If the path resolves to the same file as the built-in default (`osx/config/cookie_clicker_profile.defaults.json`), the script treats it like **omitting `-P`** (no preview side effects).
- **`-D <image.png>`** detect profile from screenshot before preview/run (requires `-P` output path).
- **`-N`** preview only; do not send clicks.
- **`-R`** require a matching preview manifest before click execution. Regenerate previews with **`-N`** after upgrading if **`options_hash`** changed (manifest now includes **`post_ladder_cookie_burst_factor`**).
- **`-A`** auto-approve preview prompt (for non-interactive runs).
- **`-B <x1|x10|x100>`** optional bulk-mode metadata for operator checks.
- **`-L <layout>`** optional layout-profile metadata (e.g., `desktop-max`).

### In-band stop (mouse move)

`macos_mouse_click_loop.sh` passes **`--abort-on-mouse-move --mouse-move-threshold-px 20`** to every `macos_mouse_click.py` invocation so a long **`-Y`** burst can be stopped **without terminal focus** (DEF-010):

1. **Arm:** the global cursor must come **within** an **arm radius** of the **click target** (`-x`/`-y`). Default radius is **`max(60, 2 × threshold)`** pixels (Euclidean). If the cursor never enters that disk (e.g. it stays over the terminal while clicks hit the browser), mouse-move abort **does not arm** and the burst is **not** stopped by this mechanism—use **Ctrl+C** / **`kill -INT`**, or move the pointer **near the cookie** once so arming can happen.
2. **Stop:** after armed, **once at least one synthetic click has been posted**, and **once** the read cursor has been **within** `--mouse-move-threshold-px` of the **same click target**, if a **later** read is **farther than** that threshold from the target, the script exits **130** with a short stderr message. (That sequence avoids DEF-011: no same-tick arm+abort before the first click, and no false stop on the next iteration when the physical pointer has not yet caught up to the new row while synthetic clicks already moved.)

Optional **`--mouse-arm-radius-px`** overrides the default arm radius (must be **≥** `--mouse-move-threshold-px`).

Direct runs:

```bash
./osx/macos_mouse_click.py -x 100 -y 100 -n 500 -d 0 -Y --abort-on-mouse-move
./osx/macos_mouse_click.py -x 100 -y 100 -n 500 -d 0 -Y \
  --abort-on-mouse-move --mouse-move-threshold-px 30 --mouse-arm-radius-px 80
```

**Permissions:** Accessibility is already required for synthetic clicks. Some macOS versions may also prompt under **Privacy & Security → Input Monitoring** for reading global cursor position; grant access for the terminal (or IDE) running the script if prompted.

**Escape key:** A global **Escape** listener is **not** implemented in Phase 1 (the game or browser may consume Escape first). Use **mouse nudge**, **Ctrl+C** in the terminal when it has focus, or **`kill -INT <pid>`** from another shell.

## Learn-point collect (`--learn-points`)

Record **multiple** real left-button positions in one session (Rich log under the table, or plain text with **`-Y`**). Mutually exclusive with **`--learn`**, **`-x/-y`**, and **`--at-cursor`**. Product spec: **[`docs/osx/plans/plan-010-macos-mouse-click-learn-points-collect.md`](../docs/osx/plans/plan-010-macos-mouse-click-learn-points-collect.md)**.

```bash
./osx/macos_mouse_click.py --learn-points
./osx/macos_mouse_click.py --learn-points -Y
./osx/macos_mouse_click.py --learn-points 5 -Y
./osx/macos_mouse_click.py --learn-points -Y --dry-run-after-start
```

## Debugging options

### Rich pre-run editor: `MACOS_MOUSE_CLICK_DEBUG_TUI`

When the script shows the **Rich** review/edit table (TTY + Rich, not `-Y/--yes`), you can log internal selection state on **stderr** and optionally to a **file**. The **same** payload is used in both places, but the **encoding differs** so log files work cleanly with **`jq`** (see below).

| Variable | Meaning |
|----------|---------|
| `MACOS_MOUSE_CLICK_DEBUG_TUI` | When set to a **truthy** value (`1`, `true`, `yes`, `on`), logging is **on**. Unset or empty: **no** `MACOS_MOUSE_CLICK_TUI_STATE` lines. |
| `MACOS_MOUSE_CLICK_DEBUG_TUI_LOG` | Optional **filesystem path**. When set, each event is written as **one line of JSON only** (UTF-8, newline-terminated). **Unset** = stderr only (no default path). The file is opened in **`"a"`** (append) on **first** log write in that process and **never truncated** on open—lines from earlier runs stay in the file. |

**Line format (two sinks, same JSON object):**

| Sink | Format |
|------|--------|
| **stderr** | **Wall time** (ISO-8601 with ms and numeric offset, e.g. `2026-04-20T15:23:41.527-07:00`), a space, then `MACOS_MOUSE_CLICK_TUI_STATE ` + compact JSON + newline. The JSON repeats **`ts_wall`** and includes **`ts_mono_ns`** (integer, `time.monotonic_ns()`), so operators see a new line at a glance even when the rest of the payload repeats. |
| **log file** (`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`) | **JSON only** + newline — each non-empty line is a single value `jq` can parse (same object as after the `MACOS_MOUSE_CLICK_TUI_STATE ` marker on stderr). |

Payload: compact JSON from `json.dumps(..., separators=(",", ":"))` (no spaces after commas/colons). Every record includes **`ts_wall`** (string) and **`ts_mono_ns`** (int).

- **Rich table** (`event` = `draw` or `after_key`): `selected_index`, `row_key`, `setting_label`, `value_text`, `source`, and on `after_key` also `last_key` (return value of `read_raw_key()` for that wait).
- **Run start** (`event` = `run`): emitted **right after** the **Running:** line for every successful start (Rich TUI after you press **S**, or CLI / `-Y`). Fields: `running_text` (same text as after `Running: `), `mode`, `count`, `delay`, `anchor_x` / `anchor_y` (`null` until known — fixed mode sets them from CLI; learn / at-cursor leave them `null` here).
- **Anchor** (`event` = `anchor`): **learn** — after the user’s anchor click, includes `anchor_x`, `anchor_y`, `message` (same text as stderr, including the warmup line), and `warmup_delay`. **at-cursor** — after reading the cursor position, includes `message` (`Cursor position recorded at (x, y).`).

**When lines are emitted:**

- After each table redraw: `event` = `draw`.
- After each key read: `event` = `after_key`, with `last_key` set.
- **TTY discipline:** while the Rich editor loop runs, stdin stays in **raw** mode so CSI/SS3 arrow bytes are not eaten by canonical line discipline (important under PTY/pexpect); `Console.input()` prompts temporarily restore cooked mode.
- After **Running:** is shown: `event` = `run`.
- **Learn:** when the anchor point is captured, `event` = `anchor`. **at-cursor:** when the pointer position is read, `event` = `anchor`.

So each **wait for a key** in the Rich editor produces **two** lines (`draw` then `after_key`). Moving with arrows, pressing Enter on a row (edit flow), or error messages that sleep and redraw add more `draw` lines.

### Generating a **large** debug log file

1. **Interactive session (most control)**  
   From a real terminal (TTY), enable debug and point the log at a path you own:

   ```bash
   cd /path/to/pub-bin
   export MACOS_MOUSE_CLICK_DEBUG_TUI=1
   export MACOS_MOUSE_CLICK_DEBUG_TUI_LOG="$PWD/tui-debug.ndjson"
   ./osx/macos_mouse_click.py --learn --interactive
   ```

   Stay in the editor and use **Up/Down**, **Enter** (edit row / return), **R** (reset row), etc. Every key cycle adds lines; long sessions produce large files. Exit with **Q** or **Ctrl+D** as usual.

2. **Append across runs**  
   Each new **process** appends to the same path if you reuse it. For **isolated** captures (one session per file), point **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`** at a **fresh path** (e.g. `tui-$(date +%s).ndjson`) or delete/truncate the file yourself before starting.

3. **Automated / stress**  
   A small **pexpect** (or similar) driver that spawns the script under a PTY and sends many arrow keys will generate one line pair per iteration plus any extra redraws. The pytest module `osx/tests/test_debug_tui_logging_meta.py` shows subprocess/PTY patterns.

4. **Unbuffered Python (optional)**  
   `PYTHONUNBUFFERED=1` is already typical for tests; for manual runs it helps stderr and the log file appear promptly line-by-line.

### Capturing stderr only (no log file)

Omit `MACOS_MOUSE_CLICK_DEBUG_TUI_LOG` and tee stderr:

```bash
MACOS_MOUSE_CLICK_DEBUG_TUI=1 ./osx/macos_mouse_click.py --learn --interactive 2> tui-stderr.ndjson
```

### Dry-run JSON (different feature)

Not the Rich table debugger, but useful for **resolved config** without Quartz:

| Mechanism | Meaning |
|-----------|---------|
| `--dry-run-after-start` | After the usual “Running” path, print one `MACOS_MOUSE_CLICK_DRY_RUN_JSON` line on **stderr** and exit (no clicks). |
| `MACOS_MOUSE_CLICK_DRY_RUN` | Env `1` / `true` / `yes` / `on` enables the same behavior when combined with an appropriate argv (see `macos_mouse_click.py` and `osx/tests/test_dry_run.py`). |

### Unwritable log path

If `MACOS_MOUSE_CLICK_DEBUG_TUI_LOG` points to a path that cannot be opened for writing, the script **keeps running** and continues to log on **stderr** only (file writes are skipped after the first failure).

### Parsing with **`jq`** (log file)

The log file is **NDJSON**: each line is one complete JSON object, **no** prefix.

```bash
# One line (e.g. latest event)
tail -1 debug.json | jq .

# First line
head -1 debug.json | jq .

# Whole file as one JSON array (stream all objects into jq)
jq -n '[inputs]' < debug.json | jq .

# Or equivalently
cat debug.json | jq -n '[inputs]' | jq .
```

Plain `cat debug.json | jq .` only parses the **first** value in many `jq` versions; use **`jq -n '[inputs]'`** (or line-at-a-time loops) for the full session.

**stderr** (mixed with Rich and other text): find `MACOS_MOUSE_CLICK_TUI_STATE `, then parse the JSON after it (ignore the leading wall-clock token):

```bash
grep 'MACOS_MOUSE_CLICK_TUI_STATE ' tui-stderr.ndjson | sed 's/^.*MACOS_MOUSE_CLICK_TUI_STATE //' | jq .
```

### Code coverage (Plan 11)

From repo root, with a venv (`make -C osx test-setup` once):

| Target | Purpose |
|--------|---------|
| `make -C osx test-coverage` (alias: `coverage`) | Full pytest with **`pytest-cov`**: terminal **missing lines**, **`osx/htmlcov/`** (open `index.html`), **`osx/coverage.xml`**. Uses **`osx/.coveragerc`**. |
| `make -C osx coverage-quick` | Same pytest/cov flags as **`test-coverage`** (full collection, including **`table_nav`** on darwin; alias for a shorter name in docs). |
| `make -C osx test-report-coverage` | **One** pytest run: **JUnit** (`osx/tests/reports/junit.xml`) **and** the same coverage outputs (used in **CI**). |

Artifacts (`htmlcov/`, `.coverage`, `coverage.xml`) are **gitignored**; download **`coverage-xml`** / **`coverage-html`** from the **macOS mouse click tests** workflow for trends between runs.

Gap analysis template / notes: **`docs/osx/macos-mouse-click-coverage-gap.md`**.

### Tests

- `osx/tests/test_debug_tui_logging_meta.py` — behavior of the TUI debug logger (gates, JSON, file vs stderr, append across processes, etc.).
- `osx/tests/test_rich_table_nav_down_pty.py` — Rich table navigation (uses debug log under `tmp_path` for correlation when enabled).
- `osx/tests/test_def009_rich_table_layout_pty.py` — **DEF-009** layout corruption heuristics on PTY transcripts (see `docs/osx/defects/def-009-rich-pre-run-tui-table-layout-corruption.md`).

See **`docs/osx/plans/plan-009-macos-mouse-click-tui-arrow-navigation-narrative.md`** (appendix: merged engineering notes) for table-nav PTY design context.
