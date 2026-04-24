---
id: DEF-002
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
---

### DEF-002: Arrow keys mis-read as cancel (Escape)

**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).

- **Frontmatter todo:** `defect-def-002-arrow-misread-as-esc` (completed when fix landed).
- **Status:** Fixed in [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py).
- **Manual verification:** **Passed** — **2026-04-18**, operator on `yoda.local`. `./osx/macos_mouse_click.py --learn -n 5000 -d 0`: **Up**/**Down** repeatedly across rows — no crash, no spurious exit. **Enter** edits: stray / special characters could appear in the prompt buffer; **input validation** rejected invalid values (**DEF-004** / **[plan 07](plan-007-macos-mouse-click-tui-field-edit-input.md)** track cleaner input handling when prioritized).
- **Severity:** High — looks like an accidental cancel; also **Count** flipped from CLI **`-n 200`** to learn default **infinite** after re-confirming mode.
- **Environment (reporter):** `yoda.local`, 2026-04-18 06:33, repo `…/pub-bin`.

**Reproduction (pre-fix)**

```bash
osx/macos_mouse_click.py --learn -n 200 -d 0
```

1. **Enter** on **Mode**, **Enter** again for default learn, **Enter** at “Press Enter to return…”.
2. Press **Down** on the main table.

**Observed**

- Stderr printed `Cancelled.` and the process exited **0** even though the user did not press **Q** or **Esc** intentionally.
- After the mode prompt, **Count** showed **infinite** with source **default** instead of **200** / **cli** — `_edit_row` for mode always did `sources.pop("count")` + `apply_defaults`, wiping a CLI count when mode did not actually change.

**Root cause**

1. `read_raw_key` used `select(..., 0.05)` after the first **ESC** byte. Arrow keys arrive as **CSI** `ESC [ A` / `ESC [ B` (sometimes with extra numeric/separator bytes). If **`[`** was not readable within **50 ms**, the reader treated the key as **lone Escape** → cancel (**DEF-002**).
2. Unconditional `cfg.sources.pop("count", None)` after any mode edit re-applied learn’s default count (0 = infinite) whenever the user re-saved **learn**, clobbering **`-n`**.

**Resolution**

1. Wait longer after **ESC** for the next byte; read a full **CSI** tail (up to 32 bytes) ending in a terminator, then map **endswith `A`/`B`** to **Up**/**Down**; support **SS3** `ESC O A` / `ESC O B`.
2. Only `pop("count")` and call `apply_defaults` when **mode actually changes** (`cfg.mode != old_mode` before/after the prompt).
3. Panel subtitle originally said **Esc alone** = cancel; **DEF-003** removed **Esc** from cancel (wheel / CSI noise). Subtitle now: **Q**, **Ctrl+D**, **Ctrl+C** only.
4. **Git:** `2319207007b2c65703e192250e3cb13ae54a16a6` (includes **DEF-001** in the same commit).
5. **Files:** [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py)

**Regression check**

- **MT-01** / **MT-02**: after mode edit + return, **Down**/**Up** only move the row; **S** starts the run; **Q**, **Ctrl+C**, or **Ctrl+D** cancels with exit **0** (**Esc** does not cancel; see **DEF-003**).
- Re-run with **`-n 200`**, edit mode with default learn, confirm **Count** stays **200** / **cli** (unless you change mode or count).
