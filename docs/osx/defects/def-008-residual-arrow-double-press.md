---
id: DEF-008
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
  - ../plans/agent/plan-agent-arrow-key-double-press-analysis.plan.md
---

### DEF-008: Residual Up/Down double press (investigation)
- **Analysis plan (in-repo):** [`plan-agent-arrow-key-double-press-analysis.plan.md`](../plans/agent/plan-agent-arrow-key-double-press-analysis.plan.md)
- **Frontmatter todo:** `defect-def-008-tui-arrow-double-press-residual` (**pending**).
- **Status:** **Open** — investigation; overlaps **DEF-006** (CSI timing) but covers **post-fix** reports and **debug log** semantics.
- **Severity:** Medium — table highlight still does not move on first physical press in some environments, or operators misread **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`** because **`after_key`** is emitted **before** **`selected`** is updated for **Up**/**Down**.

**Observed / hypotheses**

- See analysis plan: classify **Case A** (`last_key` is **`down`** / **`up`**, next **`draw`** moves) vs **Case B** (first press **`other`**, real stdin loss).
- Rich **`console.clear()`** + PTY may still interact badly with stdin (**Phase 1** scratch: [`osx/tests/_scratch_phase1_rich_table_pty.md`](../../../osx/tests/_scratch_phase1_rich_table_pty.md)).

**Resolution (when implemented)**

- Depends on Case A vs B (logging order vs **`read_raw_key`** / drain). Record **Fix commit** and **Manual verification** here when closed.

**Regression check**

- **MT-01** / **MT-02** + **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`**: one **Down** → one row move; log lines match intent.
