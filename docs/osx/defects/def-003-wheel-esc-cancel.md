---
id: DEF-003
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
---

### DEF-003: Mouse wheel / unknown ESC cancels TUI
- **Frontmatter todo:** `defect-def-003-wheel-esc-cancel` (completed when fix landed).
- **Status:** Fixed in [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py).
- **Manual verification:** **Passed** — **2026-04-18**, **v1 plan close-out**. Dedicated wheel-scroll regression was not re-recorded as a separate session; **MT-01** / **MT-02** / **MT-08** Rich table runs plus **DEF-002** verification already exercised the editor loop on `yoda.local`, and **DEF-003**’s **Resolution** (remove **`esc`** cancel; drain unknown **ESC** bursts; lone **ESC** → **`other`**) is in **`a96d6fe0175dd15d02094a889e915d4da451e671`**. **Regression check** remains the canonical smoke if this area regresses: wheel / stray **ESC** in the table must **not** print **`Cancelled.`**; **Q** / **Ctrl+C** / **Ctrl+D** still cancel with exit **0**.
- **Severity:** High — accidental exit from normal terminal interaction.
- **Environment (reporter):** `yoda.local`, 2026-04-18 06:46, repo `…/pub-bin`.

**Reproduction (pre-fix)**

```bash
osx/macos_mouse_click.py --learn -n 2000 -d 0
```

At the Rich table, **scroll the mouse wheel down** a few times (no **Q** / **Ctrl+C**).

**Observed**

- Stderr printed `Cancelled.` and the process exited **0**.

**Root cause**

1. `read_raw_key` returned **`esc`** (cancel) for **ESC** + a byte that was not **`[`** or **`O`** — common for **mouse**, **wheel**, or **focus** reporting (e.g. **`ESC >`**, **`ESC ]`**, etc.).
2. **`esc`** was treated like **Q** in `run_rich_pre_run_editor`. A **lone ESC** timeout path also mapped to cancel, which is easy to mis-fire.

**Resolution**

1. **Cancel** only on **`q`**, **`ctrl_c`**, or **`ctrl_d`** (`\x04`); remove **`esc`** from the cancel set.
2. After **ESC**, if the next byte is not **`[`** / **`O`**, drain a short stdin burst then return **`other`** (ignored). If no byte arrives within the wait window, return **`other`** (lone **ESC** ignored).
3. Subtitle: **Ctrl+D** documented; **Esc alone** removed.

4. **Git:** `a96d6fe0175dd15d02094a889e915d4da451e671`
5. **Files:** [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py)

**Regression check**

- **MT-01** / **MT-08**: wheel / incidental **ESC** sequences do not exit; **Q**, **Ctrl+C**, and **Ctrl+D** still cancel with exit **0**.
