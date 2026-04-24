<!-- Cursor agent plan (canonical copy in-repo; do not use ~/.cursor/plans/). -->
<!-- Tracked as DEF-008 in docs/osx/plans/plan-002-macos-mouse-click-terminal-ux.md -->
---
todos:
  - id: "repro-classify"
    content: "Reproduce with user argv; classify first Down as Case A (last_key down, next draw moves) vs B (last_key other or no move)"
    status: pending
  - id: "fix-log-order"
    content: "If Case A: adjust after_key payload order/fields so selected matches post-key state (docs + tests)"
    status: pending
  - id: "fix-input"
    content: "If Case B: instrument or extend read_raw_key CSI handling / optional safe drain after Rich clear; add PTY regression"
    status: pending
isProject: false
---
# Arrow Up/Down double press — log + code analysis


**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).

## Reproduction command

Interactive fixed mode (Rich pre-run editor when stdin/stdout are TTY and Rich is installed):

```bash
MACOS_MOUSE_CLICK_DEBUG_TUI=yes MACOS_MOUSE_CLICK_DEBUG_TUI_LOG=debug.json \
  ./osx/macos_mouse_click.py -n 10 -d 0 -x 1563.4 -y 4.0
```

After the table appears, press **Down** once, then again, and inspect **`debug.json`** (and stderr) for `MACOS_MOUSE_CLICK_TUI_STATE` lines.

Analysis below is from reading [`osx/macos_mouse_click.py`](../../../../osx/macos_mouse_click.py) and [`osx/tests/_scratch_phase1_rich_table_pty.md`](../../../../osx/tests/_scratch_phase1_rich_table_pty.md).

---

## What the code does (editor loop)

In [`run_rich_pre_run_editor`](../../../../osx/macos_mouse_click.py) each iteration is:

1. Build table, **`console.clear()`**, **`console.print(Panel(...))`**
2. **`_debug_tui_emit(..., event="draw")`** — logs current `selected_index` / row
3. **`key = read_raw_key()`** — raw TTY read (see below)
4. **`_debug_tui_emit(..., event="after_key", last_key=key)`** — still uses **the same `selected` as step 2** (selection is **not** updated yet)
5. Branch on `key`; for **`down` / `up`**, update `selected` and `continue`

So for a **successful** single Down you should see **three** lines per loop:

- `draw` — highlight row *N*
- `after_key` — `last_key` is `down`, but **`selected_index` is still *N*** (stale relative to the key just read)
- Next iteration: `draw` — highlight row *N+1*

That **`after_key` uses pre-navigation `selected`** is easy to misread as “Down did nothing” if you only look at `selected_index` on the `after_key` line. The **next** `draw` is the ground truth for whether navigation ran.

---

## What `read_raw_key` does (why the first press might not be `down`)

[`read_raw_key`](../../../../osx/macos_mouse_click.py) (approx. lines 277–355):

- Puts stdin in **raw** mode, reads **one byte**
- On **`ESC`**, waits up to **0.4s** for the next byte; empty → **`other`**
- **CSI** (`ESC [`): reads up to 32 tail bytes until deadline **1s** or a terminator in `ABCDEFGHZab~` (includes **`A`/`B`** for Up/Down)
- Returns **`up`/`down`** only if the assembled tail **ends with `A` or `B`**
- Otherwise returns **`other`**; for unknown `ESC` prefixes it calls **`_drain_stdin_burst()`** and returns **`other`**

So any **incomplete** arrow sequence, **non-standard** CSI (e.g. focus events, kitty extended keys), or **split delivery** where the first `read_raw_key` call does not assemble a tail ending in `A`/`B` yields **`other`** → **`selected` unchanged** → user must press again → feels like “double press”.

Phase 1 scratch already noted PTY/Rich timing issues: [`osx/tests/_scratch_phase1_rich_table_pty.md`](../../../../osx/tests/_scratch_phase1_rich_table_pty.md) hypothesizes **`console.clear()` + redraw** vs stdin as a stress case for whether navigation bytes are seen cleanly.

---

## What to look for in `debug.json`

After a **single** physical Down:

- **Case A (navigation worked):** `after_key` has `"last_key":"down"` (or `"up"`), and the **following** `draw` shows the expected new row (`row_key` / `setting_label` moved).
- **Case B (first byte lost / mis-parsed):** `after_key` has `"last_key":"other"` (or missing arrow), and the **next** `draw` still shows the **same** row as before — second Down then shows `down` and selection advances.

If you see **Case B**, the fix space is **input decoding / timing / draining**, not Rich row math (the `if key == "down"` block is trivial).

If you see **Case A** but felt the UI did not move: re-check **`draw`** lines, not **`selected_index` on `after_key`**.

---

## Recommendations (ordered)

1. **Confirm with logs:** For one failing Down, capture whether `last_key` is `down` vs `other` on the first press (stderr or file). That splits “real missed key” vs “log misleading.”

2. **Reduce log confusion (low risk):** Emit **`after_key` after applying** `up`/`down` to `selected` (or add fields like `selected_index_after` / `last_key_raw`) so each line matches mental model “key then state.” This does not fix stdin but makes Phase 3 debugging faster.

3. **If `last_key` is often `other` on first press:**
   - Add **targeted diagnostics** (dev-only or env-gated): when returning `other` after `ESC`, log hex/length of buffered tail (not for production noise).
   - Revisit **CSI assembly**: extended/modifier arrows (`… ; 2 B`), focus CSI (`… I` / `… O`), or **slow tail** (already has DEF-006 deadline loop).
   - Evaluate **stdin drain** immediately before `read_raw_key` after `console.clear()` / Rich output (risky: could eat a legitimate key; needs a short idle-based drain or “only drain non-arrow garbage” policy).

4. **If logs show `down` but UI lags:** Shift investigation to **Rich redraw** (terminal size, `console.clear`, alternate screen) rather than `read_raw_key` classification.

5. **Tests:** Extend PTY coverage (Phase 3 direction) so arrow bytes are injected deterministically and **`debug.json`** is parsed for `draw`/`after_key` correlation (partially prepared in local edits to [`osx/tests/test_rich_table_nav_down_pty.py`](../../../../osx/tests/test_rich_table_nav_down_pty.py)).

---

## Summary

| Observation | Implication |
|-------------|-------------|
| `after_key` logs **before** `selected` updates | `selected_index` on `after_key` lags one step; use next `draw` to verify movement. |
| `read_raw_key` returns `other` unless CSI/SS3 tail ends with `A`/`B` | First physical Down can be swallowed as `other` if bytes are split or non-standard. |
| Scratch notes + plan | Rich + PTY + `clear` may exacerbate timing; worth correlating with `last_key` in logs. |

**Next step:** Run the reproduction command once, reproduce one Down, and classify **Case A vs B** from `last_key` in `debug.json`. That determines whether the first fix is **logging/order** (misread) or **stdin decoding / drain / CSI** (real double-press).
