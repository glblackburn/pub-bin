---
id: DEF-004
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
---

### DEF-004: TUI edit prompts echo or capture special characters

**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).

- **Frontmatter todo:** `defect-def-004-tui-edit-echo-special-chars` (**completed** — filed and **deferred**; no script change in this closure).
- **Status:** **Closed (deferred)** — UX is **acceptable for now** (validation prevents bad config). Implementation when prioritized: **[plan 07 — TUI field-edit input](plan-007-macos-mouse-click-tui-field-edit-input.md)**.
- **Manual verification:** **N/A** — documentation-only deferral, not a code fix. After plan **07** ships, set **Manual verification** to **Passed** when regression is done and record **Fix commit** per **Git workflow** above.
- **Severity:** Medium (UX) — mis-keys or escape artifacts can show up in the cooked `Console.input` line; existing validation blocks invalid **count** / **delay** / coordinates / mode tokens from being applied.
- **Environment (reporter):** `yoda.local`, same **MT-01**-style session as **DEF-002** verification (`--learn -n 5000 -d 0`).

**Observed**

- While editing settings after **Enter** on a row, **special characters** were **captured or echoed** in the prompt. **Input validation** prevented bad values from taking effect.

**Desired behavior (future fix — plan 07)**

- Do not feed raw control / CSI bytes into the visible prompt where possible, or mask/filter input so operators do not see garbage characters while editing **Mode**, **Count**, **Delay**, or fixed **X**/**Y**.

**Resolution (this defect record)**

- **No `Fix commit`.** Tracked under **[plan 07](plan-007-macos-mouse-click-tui-field-edit-input.md)**. When that work lands, update this row to **Fixed** + **Passed** and add the **Git** SHA.

**Regression check (after plan 07)**

- **MT-01** / **MT-02**: **Enter** edits on **Mode**, **Count**, **Delay**, fixed **X**/**Y**; wheel / stray keys during **`Console.input`** do not produce unreadable prompt soup; invalid values still rejected.
