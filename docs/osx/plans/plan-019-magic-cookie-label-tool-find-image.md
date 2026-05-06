# Plan 019 — Magic cookie label tool: find image by stem / path

**Status:** Shipped — [`osx/magic_cookie_label_tool.py`](../../../osx/magic_cookie_label_tool.py).

**Related:** [plan-016 — screenshot label tool](plan-016-magic-cookie-screenshot-label-tool.md) (v1 corpus walk), [plan-017 / plan-018](plan-017-magic-cookie-detector-eval-and-tuning.md) (eval stems).

---

## Problem

Operators review hundreds of **`golden-sweeper-*-f*.png`** files. Linear **Prev/Next** is slow when resuming research on a **known stem** (e.g. `golden-sweeper-20260504-223259-223436-f00001`). **Next unlabeled** only keys off “no JSONL row,” not filename.

An earlier uncommitted implementation (session rollback) added **Find image…**, **Ctrl+F**, and **F3**; it was lost from the tree. This plan restores that behavior as the repo norm.

## Goals

1. **Jump by substring:** case-insensitive match on PNG **basename** (e.g. `223259-223436` or full stem prefix).
2. **Jump by path:** if the query resolves to an **existing file** that is the same file as one of the corpus entries (`path.resolve()` equality), select that frame.
3. **Repeat matches:** **F3** cycles through all matches for the **last successful** query (wrap).
4. **Startup shortcut:** **`--jump-query SUBSTRING`** opens the tool on the first matching PNG (stderr warning if none).
5. **Tests:** pure helpers only (no Qt head).

## Non-goals

- Full-text search inside images.
- Regex query syntax (substring only unless we add later).

## Behavior (normative)

| Action | Result |
|--------|--------|
| **Find image…** / **Ctrl+F** | Dialog with line edit. **OK** or **Enter** runs query: first match in **sorted** `gather_png_paths` order becomes current frame. Stores match list for **F3**. |
| **F3** | If a prior query produced ≥1 match, go to **next** match (wrap). If no prior query or empty match list, same as **Ctrl+F** (open dialog). |
| **`--jump-query`** | Before showing UI, set initial index to first `png_indices_matching_query` hit; if none, print warning and start at **0**. |

## Implementation

- Module-level **`png_path_matches_search_query`**, **`png_indices_matching_query`** (typed `Sequence[Path]`).
- **`MainWindow`:** `_find_query`, `_find_match_indices`, `_find_match_cursor`; `_on_find_image`, `_on_find_next`, `_apply_find_query`.
- **`QDialog`** + **`QLineEdit`** + **`QDialogButtonBox`** (PySide6).
- Help text and status bar mention Find / **Ctrl+F** / **F3** / **`--jump-query`**.

## Acceptance

- [x] Find dialog + button + **Ctrl+F** / **F3** work on a multi-file corpus directory.
- [x] **`--jump-query`** lands on the expected frame when the stem exists.
- [x] **`pytest`** covers substring match, resolved path match, and empty query.
