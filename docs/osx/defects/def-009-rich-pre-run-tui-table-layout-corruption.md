---
id: DEF-009
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
---

### DEF-009: Rich pre-run table / panel layout corruption (double borders, misaligned grid)

- **Status:** **Fixed** (script) — root cause was Rich’s default ``Table`` box (**``HEAVY_HEAD``**, heavy U+2501 header rules) visually merging with the ``Panel`` light top border on tight TTYs; mitigated with **``box.ROUNDED``** and stdout flush before stderr debug lines.
- **Severity:** Medium (UX) — readability and trust in the UI; logic and debug NDJSON can still be correct while the frame looks broken.
- **Opened:** 2026-04-21
- **Environment (reporter):** `yoda.local`, Terminal.app-style session, Rich pre-run editor (e.g. `./osx/macos_mouse_click.py --learn --interactive` without `-Y`, `rich` installed).
- **Screenshot (canonical):** [`osx/tests/screenshots/Screenshot_2026-04-21_at_1.18.36_AM.png`](../../../osx/tests/screenshots/Screenshot_2026-04-21_at_1.18.36_AM.png)

**Observed**

The cyan **macOS mouse click — review / edit** panel renders, but the **Setting / Value / Source** table grid is visually corrupted:

1. **Double vertical rules** — Column separators appear as **paired** pipe characters (`| |`) instead of a single column boundary between **Setting**, **Value**, and **Source**.
2. **Extra vertical bars at the frame** — Inside the cyan outer border, **left and right** edges show **duplicate** or offset vertical pipe columns so the table looks “double-walled.”
3. **Broken horizontal rules** — Header/rule rows built from `-` / `+` junctions **do not meet** the vertical pipes cleanly; the grid has **gaps** and misaligned intersections.
4. **Stray columns outside the panel** — On the **far right**, vertical pipe characters appear **outside** the cyan `Panel` border, aligned with data rows (artifact of mis-measured width or mixed streams).
5. **Row highlight continuity** — The **Mode** row shows the expected cyan selection, but the highlight reads as **segmented** or interrupted where misaligned pipes cut through it.

**Context**

- A **debug JSON** line below the panel (stderr / copy-paste) can still show coherent state (e.g. `"setting_label":"Mode"`, `"event":"draw"`), i.e. this defect is **layout / paint**, not necessarily selection logic.
- **DEF-005** covers **terminal resize / reflow** (deferred to plan 06). **DEF-009** is distinct: corruption visible **without** invoking resize, suggesting **width / box drawing / stdout+stderr interleaving / Rich Table+Panel** interaction rather than SIGWINCH alone.

**Hypotheses (for investigation)**

- **`Console` width** vs actual terminal columns (padding, `legacy_windows`, or `TERM` quirks).
- **`console.clear()`** + rapid **stderr** lines (debug `MACOS_MOUSE_CLICK_DEBUG_TUI`) interleaving with **stdout** table bytes on the same TTY.
- **Rich** `Table` box style vs `Panel` border: duplicate box-drawing layers or `expand=True` reflow at an odd width.
- Prior experiment: aggressive **`sys.stdout`/`sys.stderr` `flush()`** around `clear()`/`print()` reportedly caused **input stalls** under PTY; any future layout fix should avoid reintroducing that without isolating TTY vs file sinks.

**Resolution**

- **`_build_editor_table`:** pass **`box=box.ROUNDED`** so inner table rules stay light-only and align with the ``Panel`` frame (no **``HEAVY_HEAD``** / U+2501 on the nested table).
- **`_run_rich_pre_run_editor_loop`:** call **`_flush_stdout_safe()`** after **`console.clear()`** and after the main **`console.print(Panel(...))`**, before **`_debug_tui_emit`**, so ``MACOS_MOUSE_CLICK_TUI_STATE`` on stderr cannot interleave mid-frame on a single TTY.
- **Git:** `3bd517d6adb4e0d3fa112cb7b6a6f39aeee9317a`
- Mirror the **Fix commit** row in **[`plan-002` Defect summary](../plans/plan-002-macos-mouse-click-terminal-ux.md)**.

**Regression check (after fix)**

- **Automated (in-repo):** [`osx/tests/test_def009_rich_table_layout_pty.py`](../../../osx/tests/test_def009_rich_table_layout_pty.py) + [`osx/tests/def009_layout_heuristics.py`](../../../osx/tests/def009_layout_heuristics.py). Heuristics cover **structural** fusion (``╭`` on the same stripped line as inner heavy **━** U+2501), **literal** doubled column rules, and **stderr JSON** merged into a table row. The **darwin** + **`table_nav`** PTY test asserts ``layout_corruption_reason(...) is None`` at **40×120** with debug TUI enabled. Synthetic fixtures keep the detector honest if the layout regresses.
- From a real TTY, open the Rich pre-run editor; confirm **single** column rules, continuous horizontal rules, **no** pipes outside the cyan frame, and stable layout with **`MACOS_MOUSE_CLICK_DEBUG_TUI=1`** on and off.
- Optional: narrow/wide terminal spot-check; relate findings to **DEF-005** / plan 06 if resize still misbehaves separately.
