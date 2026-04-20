---
id: DEF-008
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
  - ../plans/agent/plan-agent-arrow-key-double-press-analysis.plan.md
---

### DEF-008: Residual Up/Down double press (investigation)
- **Analysis plan (in-repo):** [`plan-agent-arrow-key-double-press-analysis.plan.md`](../plans/agent/plan-agent-arrow-key-double-press-analysis.plan.md)
- **Frontmatter todo:** `defect-def-008-tui-arrow-double-press-residual` (**completed** for log semantics).
- **Status:** **Fixed** (script) — **`after_key`** debug lines now use the **post-navigation** **`selected`** row for **Up**/**Down**, so **`selected_index` / `row_key` / `setting_label`** match the highlight the operator sees after one arrow key.
- **Severity:** Medium — table highlight still does not move on first physical press in some environments, or operators misread **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`** because **`after_key`** is emitted **before** **`selected`** is updated for **Up**/**Down**.

**Observed / hypotheses**

- See analysis plan: classify **Case A** (`last_key` is **`down`** / **`up`**, next **`draw`** moves) vs **Case B** (first press **`other`**, real stdin loss).
- Rich **`console.clear()`** + PTY may still interact badly with stdin (**Phase 1** scratch: [`osx/tests/_scratch_phase1_rich_table_pty.md`](../../../osx/tests/_scratch_phase1_rich_table_pty.md)).

**Resolution**

- **`run_rich_pre_run_editor`**: apply **Up**/**Down** to **`selected`** before **`_debug_tui_emit(..., event="after_key")`**; factored helper **`_tui_bump_selected_for_arrow_key`** for tests.
- **Git:** `faeb3d89da6be12decfa39adb7027516c935c98b`
- **Tests:** [`osx/tests/test_open_defects.py`](../../../osx/tests/test_open_defects.py) (unit); PTY / CSI “double press” remains tracked separately if new evidence appears.

**Regression check**

- **MT-01** / **MT-02** + **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`**: one **Down** → one row move; **`after_key`** JSON **`selected_index`** matches the new row (**Pending** on real Mac TTY if not re-run after this change).
