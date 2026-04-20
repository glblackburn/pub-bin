---
id: DEF-001
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
---

### DEF-001: `Console.input(highlight=…)` on older Rich
- **Frontmatter todo:** `defect-def-001-rich-input-highlight` (completed when fix landed).
- **Status:** Fixed in [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py) (`_prompt_cooked`: stop passing `highlight=` so older **Rich** builds work).
- **Manual verification:** **Passed** — **2026-04-18**, operator on `yoda.local`. `./osx/macos_mouse_click.py --learn -n 2000 -d 0`: **Enter** on **Mode** repeatedly (with default/confirm) — no crash, no exit; same for **Count** and **Delay** row edits via **Enter** (aligned with **MT-01**).
- **Severity:** High — TUI unusable as soon as the user presses **Enter** on **Mode** (and would affect any row using the same prompt path).
- **Environment (reporter):** `yoda.local`, repo path `…/pub-bin`, command run from repo root.

**Reproduction (pre-fix)**

```bash
osx/macos_mouse_click.py --learn -n 200 -d 0
```

In the Rich table, press **Enter** on **Mode** (or choose edit mode). On Rich versions where `Console.input()` does not accept `highlight`, Python raises:

```text
TypeError: Console.input() got an unexpected keyword argument 'highlight'
```

Stack pointed to `_prompt_cooked` → `_edit_row` → `run_rich_pre_run_editor`.

**Root cause**

`_prompt_cooked` called `console.input(prompt, highlight=False)`. The `highlight` parameter was added in newer Rich releases; older installs treat it as invalid.

**Resolution**

- Call `console.input(prompt)` only (no `highlight` kwarg), documented in code for compatibility.
- Optional hardening later: document a minimum Rich version in the plan / epilog if we reintroduce kwargs that need newer Rich.
- **Git:** `2319207007b2c65703e192250e3cb13ae54a16a6` — same commit as **DEF-002** (both fixes landed together).
- **Files:** [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py)

**Regression check**

- Re-run **MT-01** / **MT-02**: open editor, **Enter** on Mode, confirm default Enter leaves mode as learn and no traceback.
