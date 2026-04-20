---
id: DEF-007
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
---

### DEF-007: Duplicate -n flag uses last value (no error)
- **Frontmatter todo:** `defect-def-007-cli-duplicate-options-silent` (**pending**).
- **Status:** **Open** — no script change yet.
- **Severity:** Medium — operator mistake (**`-n 10 … -n 100 -n 5`**) silently picks **5**; no stderr hint.

**Observed**

```bash
MACOS_MOUSE_CLICK_DEBUG_TUI=yes MACOS_MOUSE_CLICK_DEBUG_TUI_LOG=debug.json \
  osx/macos_mouse_click.py -n 10 -d 0 -x 1563.4 -y 4.0 -Y -n 100 -n 5
```

Process prints **Running** / **`run`** JSON with **`count":5`** (last **`-n`** only). No **`Error:`** exit.

**Root cause**

1. In [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py) **`build_arg_parser`**, **`-n` / `--count`** is registered once (`add_argument(..., default=argparse.SUPPRESS)`). **`argparse`**’s default **store** action **replaces** the destination each time the flag appears; **`parse_args`** does not treat repeated options as an error.
2. **`validate_ns`** / **`namespace_to_cfg`** only read the final namespace — there is **no** check that **`-n`** appeared at most once.

**Desired behavior (future fix)**

- Exit **2** with a clear message, e.g. **`-n` / `--count` may only appear once** (same policy optionally for **`-d`**, **`-x`**, **`-y`** if repeated).

**Resolution (when implemented)**

- Custom **`argparse.Action`** (or post-parse scan of **`sys.argv`**) to detect duplicates; then update this row per **Git workflow** above.

**Regression check**

- Passing **`-n 3`** once still works; duplicate **`-n`** on the same line exits **2**.
