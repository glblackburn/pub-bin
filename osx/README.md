# macOS mouse click (`osx/`)

Synthetic left-click automation for macOS (see `macos_mouse_click.py` and repo root docs).

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

### Tests

- `osx/tests/test_debug_tui_logging_meta.py` — behavior of the TUI debug logger (gates, JSON, file vs stderr, append across processes, etc.).
- `osx/tests/test_rich_table_nav_down_pty.py` — Rich table navigation (uses debug log under `tmp_path` for correlation when enabled).
- `osx/tests/test_def009_rich_table_layout_pty.py` — **DEF-009** layout corruption heuristics on PTY transcripts (see `docs/osx/defects/def-009-rich-pre-run-tui-table-layout-corruption.md`).

See `docs/osx/plans/agent/plan-agent-new-test-up-down-navigation.plan.md` for the full Phase 2 design.
