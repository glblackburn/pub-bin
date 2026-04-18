---
todos:
  - id: add-plan-07
    content: "Write docs/plans/07-macos-mouse-click-tui-field-edit-input.md"
    status: completed
  - id: phase-07-spec
    content: "Choose approach: filter Console.input vs raw mini-prompt vs Rich API"
    status: pending
  - id: phase-07-implement
    content: "Implement sanitization in _prompt_cooked / row edit path in macos_mouse_click.py"
    status: pending
  - id: phase-07-verify-mt01-mt02
    content: "Re-run MT-01 / MT-02; update DEF-004 in plan 02 with Fix commit + Passed"
    status: pending
  - id: phase-07-automation-plan03
    content: "Optional: extend plan 03 PTY cases for noisy-key injection on field edit"
    status: pending
isProject: false
---

# Plan 07: TUI field-edit input sanitization (**DEF-004**)

This document is the **implementation roadmap** for **[`DEF-004`](02-macos-mouse-click-terminal-ux.md#def-004-tui-edit-prompts-echo-or-capture-special-characters)** in **[`02-macos-mouse-click-terminal-ux.md`](02-macos-mouse-click-terminal-ux.md)** (noisy **`Console.input`** prompts when editing **Mode**, **Count**, **Delay**, or fixed **X**/**Y** in the Rich pre-run table). **Validation already blocks bad values**; the gap is **operator-visible** echo / capture of **control bytes** and **CSI** fragments.

**DEF-004** is **closed (deferred)** in plan **02**: behavior is **acceptable for now**; this plan picks up the **future improvement** without implying an immediate **Fix commit**.

Related: **[`01-macos-clicker.md`](01-macos-clicker.md)** (semantics unchanged), **[`03-macos-mouse-click-tui-automation.md`](03-macos-mouse-click-tui-automation.md)** (post-fix PTY ideas), **[`06-macos-mouse-click-rich-tui-terminal-resize.md`](06-macos-mouse-click-rich-tui-terminal-resize.md)** (separate layout work).

## Table of contents

- [Problem](#problem)
- [Goals](#goals)
- [Implementation touchpoints](#implementation-touchpoints)
- [Design options](#design-options)
- [Phases](#phases)
- [Manual QA](#manual-qa)

## Problem

After **Enter** on a table row, the script uses **Rich** **`Console.input()`** (“cooked” line editing). Stray **terminal events** (focus reporting, partial **CSI** sequences, accidental **arrow** bytes misread as text, paste containing control characters) can **appear in the prompt buffer** or **pollute** the visible line. **DEF-003** stopped wheel-driven **cancel** in the **table**; **field-edit** prompts are a separate surface.

## Goals

1. **Quiet prompts:** operators editing numeric or mode fields should not see **garbage** or **escape soup** in the prompt line when reasonable.
2. **Preserve correctness:** keep existing **validation** and **source** tracking (`cli` / `default` / `prompt` / `tui`); do not widen what values are accepted without explicit product decision.
3. **No regression** on **MT-01** / **MT-02** flows: **Enter** on **Mode** / **Count** / **Delay** / fixed coordinates still works on older **Rich** (no **`highlight=`** regression — see **DEF-001**).
4. **Document** any new minimum **Rich** version only if new APIs are required.

## Implementation touchpoints

- [`osx/macos_mouse_click.py`](../../osx/macos_mouse_click.py): **`_prompt_cooked`**, **`_edit_row`**, and any shared helper used for row edits after **`run_rich_pre_run_editor`** hands off to **`Console.input`**.

## Design options

| Approach | Tradeoff |
|----------|----------|
| **Filter returned string** from `Console.input` (strip / reject non-printable, normalize CSI tails) | Small diff; must not break UTF-8 labels if mode strings ever widen |
| **Short raw read** for field lines only (bypass `readline` quirks) | More code; must not fight **termios** state used by **`read_raw_key`** |
| **Custom prompt widget** (still Rich) with explicit key handling | Larger change; most control over echo |
| **Upstream Rich** issue / version bump | If classed as library bug, document pin or workaround |

**Recommendation:** prototype **filter + reject** on the returned line first; escalate only if real terminals still leak CSI after filtering.

## Phases

### Phase 1 — Specification

- List **forbidden** byte ranges (C0 except tab/newline if ever used, **ESC**-led tails) and how they interact with **international** input (if applicable).
- Decide whether **arrow** keys during `Console.input` should **no-op** vs move cursor (terminal-dependent).

### Phase 2 — Implementation

- Implement sanitization in **`_prompt_cooked`** (or a dedicated helper) with **unit tests** for representative dirty strings.
- Manual smoke: **MT-01**-style **Enter** on each row type.

### Phase 3 — Audit and docs

- Land **Fix commit**; update plan **02** **DEF-004** row (**Fixed** + **Passed** manual verification) per **Git workflow** in plan **02**.
- Trim **[plan 03](03-macos-mouse-click-tui-automation.md)** scope table row that referenced **DEF-004** once automation or manual matrix is updated.

## Manual QA

- **MT-01** / **MT-02**: aggressive **wheel** / incidental keys **while** inside a **`Console.input`** prompt — buffer should stay readable; invalid submissions still rejected.
- **Paste** legitimate values (large count, float delay) — unchanged acceptance.

