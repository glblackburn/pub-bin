<!-- 552602bb-b601-4403-b549-ac84972da49a -->
---
todos:
  - id: "doc-checklist"
    content: "(Optional) Add “evidence bundle” subsection to plan-009 or osx/README.md for agent QA"
    status: pending
isProject: false
---
# Validation evidence for one-press Up/Down row highlight

## Why repeated descriptions failed validation

Subjective reports (“double press”, “stuck”) mix **three different failure classes**: Esc/cancel policy (**DEF-002/003**), CSI inter-byte timing (**DEF-006**), and **telemetry vs UI mismatch** (**DEF-008**). Without **time-ordered, structured** evidence tied to **one physical keypress**, an agent cannot prove which class occurred or whether the **visible Rich highlight** actually moved.

## What to provide from a running instance (minimum useful bundle)

Collect all of the following from the **same run** and attach as files or paste blocks:

1. **Exact invocation**
   - Full `argv` (command line) and **`TERM`**.
   - **`python3 -V`**, **`pip show rich`** (or equivalent), and **commit SHA** or file mtime of `osx/macos_mouse_click.py` if not from a clean git checkout.

2. **TUI debug log (preferred machine signal)**  
   Enable before launch:
   - `MACOS_MOUSE_CLICK_DEBUG_TUI=1`
   - `MACOS_MOUSE_CLICK_DEBUG_TUI_LOG=/path/to/tui.ndjson` (writable path; one session per file is easiest to parse)

   The script writes **one JSON object per line** (no prefix) to the log file; stderr uses prefix `MACOS_MOUSE_CLICK_TUI_STATE ` plus the same JSON ([`osx/macos_mouse_click.py`](osx/macos_mouse_click.py) `_debug_tui_emit`, [`osx/README.md`](osx/README.md) jq section).

3. **Stderr capture** (even if redundant with the log file)  
   Rich and errors interleave on stderr; grep for `MACOS_MOUSE_CLICK_TUI_STATE` lines if you only want state events.

4. **Operator action transcript (human side)**  
   Short text: e.g. “Launched editor → pressed Down **once** (physical key) → waited 2s → pressed Up **once**.” Timestamps help correlate with log line order.

## How an agent validates the simple use case from that bundle

**Use case:** one **Down** → next row highlighted; one **Up** → previous row highlighted.

**Primary contract (log-based, after DEF-008 fix):** for each physical arrow press, inspect consecutive **`draw` / `after_key`** records:

- Find an **`after_key`** with `"last_key":"down"` (or `"up"`).
- Check **`selected_index`**, **`row_key`**, and **`setting_label`** on that same line: they should describe the **row after** navigation for Down (and **row before** for Up relative to the prior **`draw`**), matching [`run_rich_pre_run_editor`](osx/macos_mouse_click.py) behavior.
- The **next** **`draw`** (same loop iteration) should be **consistent** with that `selected_index` (same row identity).

**Secondary contract (UI ground truth, harder):** a **terminal transcript** or **screenshot/video** showing the **bold “Setting”** cell (the approach in [`osx/tests/test_rich_table_nav_down_pty.py`](osx/tests/test_rich_table_nav_down_pty.py))—this is what the user actually sees, but PTY capture is **flaky** (tests are often `xfail` for that reason).

**Disambiguation:** if **`after_key`** shows `"last_key":"other"` or missing `down`/`up` when the user pressed an arrow, the failure is likely **DEF-006-class** (reader / timing), not “Rich didn’t repaint.” If **`last_key`** is `down` but **`setting_label`** did not advance, compare with prior **`draw`** and any **`Cancelled.`** on stderr to separate cancel vs navigation.

## Optional additions (when logs alone are inconclusive)

- **Raw stdin / escape trace** (not emitted today for every key): a one-off patch or strace-style capture is the next step; today the best proxy is **`after_key` / `draw`** plus **`read_raw_key`** outcomes inferred from `last_key`.
- **Environment context:** local vs SSH, Terminal.app vs iTerm, Bluetooth keyboard, `screen`/`tmux`, high CPU load—paste with the bundle.

## Repo pointers (already implemented)

- Debug env and jq patterns: [`osx/README.md`](osx/README.md) (TUI debug section).
- JSON contract tests: [`osx/tests/test_debug_tui_logging_meta.py`](osx/tests/test_debug_tui_logging_meta.py).
- PTY + highlight parsing (best-effort UI verification): [`osx/tests/test_rich_table_nav_down_pty.py`](osx/tests/test_rich_table_nav_down_pty.py).

## Optional follow-up (documentation only)

If you want this embedded in-repo as a checklist for agents, add a short **“Evidence bundle for arrow QA”** subsection to [`docs/osx/plans/plan-009-macos-mouse-click-tui-arrow-navigation-narrative.md`](docs/osx/plans/plan-009-macos-mouse-click-tui-arrow-navigation-narrative.md) or `osx/README.md`—no code changes required.
