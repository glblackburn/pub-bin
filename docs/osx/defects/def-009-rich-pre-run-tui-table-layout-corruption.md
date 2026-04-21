---
id: DEF-009
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
---

### DEF-009: Rich pre-run table / panel layout corruption (double borders, misaligned grid)

- **Status:** **Reported** — no fix commit yet; visual regression on the main **review / edit** screen (`Panel` + `Table` in `run_rich_pre_run_editor` / `_run_rich_pre_run_editor_loop`).
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

- **None yet.** When fixed, add **Fix commit** (full SHA) here and in **[`plan-002` Defect summary](../plans/plan-002-macos-mouse-click-terminal-ux.md)**; prefer one commit citing **DEF-009**.

**Regression check (after fix)**

- **Automated (in-repo):** [`osx/tests/test_def009_rich_table_layout_pty.py`](../../../osx/tests/test_def009_rich_table_layout_pty.py) — synthetic Rich sanity checks, corrupt fixture lines, and a **darwin** + **`table_nav`** PTY case with **`MACOS_MOUSE_CLICK_DEBUG_TUI=1`** (stderr + stdout merge) that scans the transcript for doubled vertical rules (`││` / `┃┃`), doubled ASCII `||`, and **`MACOS_MOUSE_CLICK_TUI_STATE`** embedded inside a table row. Heuristics live in [`osx/tests/def009_layout_heuristics.py`](../../../osx/tests/def009_layout_heuristics.py). The heuristics are conservative; extend them if new corruption shapes appear in screenshots.
- From a real TTY, open the Rich pre-run editor; confirm **single** column rules, continuous horizontal rules, **no** pipes outside the cyan frame, and stable layout with **`MACOS_MOUSE_CLICK_DEBUG_TUI=1`** on and off.
- Optional: narrow/wide terminal spot-check; relate findings to **DEF-005** / plan 06 if resize still misbehaves separately.
