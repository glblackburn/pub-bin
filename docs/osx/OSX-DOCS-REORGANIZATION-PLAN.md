# macOS clicker documentation reorganization (review plan)


**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).

This document specifies a **directory and content split** for everything that documents **`osx/macos_mouse_click.py`**: product plans, agent/session plans, and **DEF-xxx** defects (through **DEF-009** in the live tree). The **migration phases below have been executed** in the repo; the body that follows is the historical specification plus checklists (the opening “review artifact until sign-off” wording is **obsolete**—see **Execution status**). For day-to-day navigation, start at **[`README.md`](README.md)** (hub).

## Execution status (as of 2026-04)

| Phase (checklist below) | Status |
|-------------------------|--------|
| Create tree; `git mv` + rename to **`docs/osx/plans/`** (and a later **`plans/agent/`** subtree for clicker session notes) | Done; **2026-04-29** — clicker **`plans/agent/`** session files **merged back** into **`plan-###`** and the empty **`docs/osx/plans/agent/`** tree **removed** |
| Author **`docs/osx/plans/README.md`** and **`docs/osx/defects/README.md`** | Done (indexes extended with dates in READMEs; see those files) |
| Extract **`def-001`…`def-009`**; thin **plan-002** inlined DEF prose where duplicated | Done — detail narratives live under **`def-###`**; **plan-002** keeps the summary table, workflow, and links (no duplicate long-form DEF bodies beyond table rows) |
| Update pointers (**`.cursorrules`**, **`osx/`**, **`docs/plans/README.md`** stub → **`docs/osx/plans/README.md`**) | Done |
| Optional: **Opened/Completed** columns on plan/defect index tables | Done — **`plans/README.md`** and **`defects/README.md`** |

**Residual (optional):** Move this file under **`plans/`** only if you want all meta-plans colocated; keeping it at **`docs/osx/OSX-DOCS-REORGANIZATION-PLAN.md`** is fine.

## Goals

1. **Single osx doc hub** under **`docs/osx/`** so operators and agents do not hunt across **`docs/plans/`** and embedded defect prose.
2. **`docs/osx/plans/`** — all plan-style documents for the clicker (numbered product **`plan-001`…`plan-010`**, handoffs). Session engineering for the clicker is folded into those **`plan-###`** files (no parallel **`plan-agent-*`** directory under **`docs/osx/plans/`**).
3. **`docs/osx/defects/`** — one **detail file per DEF-xxx** (see **DEF-001**–**DEF-009** in [`defects/README.md`](defects/README.md)), extracted from the long-form audit in **plan 02** today.
4. **Cross-links** — each plan that references a defect links to **`../defects/def-###-….md`**; each defect file links back to **owning plan(s)** (e.g. `plan-002`, `plan-003`, `plan-009`).
5. **Index READMEs** — **`docs/osx/plans/README.md`** and **`docs/osx/defects/README.md`** with a **lookup table**: id, date opened, date completed (if any), status, one-line title, **markdown link** to the detail document.
6. **Repository hygiene** — update **all in-repo pointers** (script comments, **`osx/README.md`**, tests, **`.cursorrules`**, thin **`docs/plans/README.md`**) so nothing still points at removed paths.

## Non-goals (this pass)

- Moving **non–mouse-clicker** reference plans into **`docs/osx/`** — optional; small references (e.g. **react2shell-server** test framework) may live as **`*.plan.md`** under **`docs/osx/plans/`** alongside **`plan-###`** files.
- Rewriting plan **content** beyond moving paths, adding cross-links, and stripping duplicated defect bodies from plan 02 after extraction.

## Canonical inventory (after move; `osx/macos_mouse_click.py`)

| Location | Role |
|----------|------|
| [`plans/plan-001-macos-clicker.md`](plans/plan-001-macos-clicker.md) | Core product spec |
| [`plans/plan-002-macos-mouse-click-terminal-ux.md`](plans/plan-002-macos-mouse-click-terminal-ux.md) | UX overlay + **Defect summary** table; **DEF-001–009** narrative in [`defects/`](defects/README.md) |
| [plan-003](plans/plan-003-macos-mouse-click-tui-automation.md) … [plan-008](plans/plan-008-macos-mouse-click-stop-during-run.md) | Follow-on product plans (**003**–**008**) |
| [`plans/plan-handoff-2026-04-18-linkedin-macos-clicker-draft.md`](plans/plan-handoff-2026-04-18-linkedin-macos-clicker-draft.md) | Session handoff (clicker context) |
| [plan-009 appendix](plans/plan-009-macos-mouse-click-tui-arrow-navigation-narrative.md#appendix-merged-engineering-notes-formerly-split-agent-plans) | Merged navigation / DEF-006 / DEF-008 / PTY harness / Phase 3 resume notes |
| [plan-003 § Additional automation backlog](plans/plan-003-macos-mouse-click-tui-automation.md#additional-automation-backlog-session-notes-merge) | Merged automation deep dive, DRY refactor notes, coverage / post-start test ideas |
| [plan-002 § Operator loop / preview](plans/plan-002-macos-mouse-click-terminal-ux.md#operator-loop-cookie-clicker-and-preview-pipeline-merged-context) | Merged looper / Cookie Clicker research / rate control / DEF-012 context |
| [`plans/react2shell-server-test-framework-reference.plan.md`](plans/react2shell-server-test-framework-reference.plan.md) | External **react2shell-server** test / Make layout reference (GitHub) |
| [`../plans/README.md`](../plans/README.md) | Thin **`docs/plans/`** pointer to **`docs/osx/plans/`** (clicker **`plan-###`** + optional reference **`*.plan.md`**) |

**Legacy `docs/plans/` paths:** former **`01`–`08`**.md / **`HANDOFF-…`** / old **`docs/plans/agent/*.plan.md`** names for the clicker were removed after the move; use **[`docs/osx/plans/README.md`](plans/README.md)** as the single plan index; **[`docs/plans/README.md`](../plans/README.md)** is a short pointer for **`docs/plans/`** visitors only.

**Pointers elsewhere (historical sweep; done):** [`osx/macos_mouse_click.py`](../../osx/macos_mouse_click.py), [`osx/README.md`](../../osx/README.md), [`osx/tests/test_rich_table_nav_down_pty.py`](../../osx/tests/test_rich_table_nav_down_pty.py), [`osx/tests/_tmp_tty_probe.py`](../../osx/tests/_tmp_tty_probe.py), [`.cursorrules`](../../.cursorrules) (agent plan path rule) — should reference **`docs/osx/`** for clicker docs.

## File naming convention (required)

**Update (2026-04-29):** The **`docs/osx/plans/agent/`** subtree and **`plan-agent-*`** clicker session files were **merged into `plan-###`** appendices (**plan-002**, **plan-003**, **plan-009**) and **removed**. New mouse-clicker engineering notes belong in the **owning numbered plan**, not a parallel agent directory under **`docs/osx/plans/`**.

- **Plans** — every plan file name **starts with `plan-`**, then:
  - **Numbered product plans (old 01–08, extended to 09–10):** **`plan-###-`** + kebab slug, where **`###`** is the **zero-padded plan number** (`001` … `010`, etc.) so directory sort matches program order.  
    Examples: `plan-001-macos-clicker.md`, `plan-002-macos-mouse-click-terminal-ux.md`, `plan-008-macos-mouse-click-stop-during-run.md`.
  - **Historical — session / agent plans:** **`plan-agent-`** + kebab base name + optional **`.plan.md`** was used briefly under **`docs/osx/plans/agent/`**; content now lives in the merge sections linked from **[`plans/README.md`](plans/README.md)**.
  - **Handoff / narrative docs:** **`plan-handoff-`** + date + short slug (no `###`).  
    Example: `plan-handoff-2026-04-18-linkedin-macos-clicker-draft.md`.
- **Defects** — every defect detail file **starts with `def-`**, then **`###`** = **zero-padded defect id** (`001` … `009`, etc.) + kebab slug.  
  Examples: `def-001-console-input-highlight.md`, `def-006-tui-arrow-multi-press.md`, `def-007-duplicate-n-flag-last-wins.md`, `def-008-residual-arrow-double-press.md`, `def-009-rich-pre-run-tui-table-layout-corruption.md`.  
  Human-readable **DEF-001** spelling stays in document **titles** and README tables; **filenames** use the **`def-###`** prefix for stable sorting and grep.

## Target layout

```text
docs/osx/
  README.md                 # Hub: links to plans/, defects/, osx/README operator doc
  OSX-DOCS-REORGANIZATION-PLAN.md   # This file (optional: move to plans/ after execution)
  plans/
    README.md               # Lookup table for all plans under docs/osx/plans/
    plan-001-macos-clicker.md
    plan-002-macos-mouse-click-terminal-ux.md
    …
    plan-008-macos-mouse-click-stop-during-run.md
    plan-handoff-2026-04-18-linkedin-macos-clicker-draft.md
    # plans/agent/ subtree removed 2026-04-29 — session notes merged into plan-002 / plan-003 / plan-009
  defects/
    README.md               # Lookup table for all defects
    def-001-console-input-highlight.md
    def-002-arrow-misread-as-esc.md
    …
    def-008-residual-arrow-double-press.md
    def-009-rich-pre-run-tui-table-layout-corruption.md
```

Exact **kebab slugs** for `def-###-…` and non-numbered `plan-…` files should mirror the current **DEF-xxx** / plan titles (adjust only for ASCII and length).

## Defect extraction rules

1. **Source of truth** for defects: **`plans/plan-002-macos-mouse-click-terminal-ux.md`** **Defect summary** table (dates, status, fix commit, manual verification) plus matching **`defects/def-###-….md`** detail files (full narrative).
2. **Each `docs/osx/defects/def-###-….md`** should contain:
   - Short YAML frontmatter (optional but recommended): `id`, `opened`, `closed`, `status`, `severity`, `related_plans` (list of relative links).
   - Body: move the existing subsection text **verbatim** first; then tighten in a later edit if desired.
3. **Replace** the inlined DEF bodies in plan **02** (`plan-002-…`) with:
   - One-paragraph summary + **link** `See [DEF-007 (detail)](../defects/def-007-….md).`
   - Keep the **Defect summary table** in 02 **or** shrink it to “see defects README” — recommend **keep a thin table** in 02 that links to each file for continuity with existing “Git workflow (defect fixes)” section.

## Plan index (`docs/osx/plans/README.md`)

Suggested columns:

| Plan id | Title | Opened | Completed | Status | Document |
|---------|-------|--------|-----------|--------|----------|
| plan-001 | macOS clicker core | … | … | active / closed | [plan-001-macos-clicker.md](plan-001-macos-clicker.md) |
| … | … | … | … | … | … |
| *(retired id)* | Nav + logging session notes | — | — | merged | [plan-009 appendix](plans/plan-009-macos-mouse-click-tui-arrow-navigation-narrative.md#appendix-merged-engineering-notes-formerly-split-agent-plans) |

Use **best-known dates** from git log or plan frontmatter where present; use **—** when unknown.

## Defect index (`docs/osx/defects/README.md`)

Suggested columns:

| Id | Title | Opened | Completed | Status | Document |
|----|-------|--------|-----------|--------|----------|
| DEF-007 | Duplicate `-n` last wins | 2026-04-19 | — | Open | [def-007-….md](def-007-….md) |

Populate from the existing summary table in plan 02.

## Cross-link matrix (after files exist)

| From | To |
|------|-----|
| `plan-002-…` defect table row | `../defects/def-###-….md` |
| Each `def-###-….md` | **Plans:** [`plan-002-…`](plans/plan-002-macos-mouse-click-terminal-ux.md); DEF-006 / DEF-008 design context → [plan-009 appendix](plans/plan-009-macos-mouse-click-tui-arrow-navigation-narrative.md#appendix-merged-engineering-notes-formerly-split-agent-plans) |
| DEF-008 | `def-008-…` detail file + plan-009 appendix |
| Table-nav PTY checklist | `plan-002` + `plan-009` appendix + relevant `def-###` files |

## Migration phases (execution checklist)

1. **Create tree** — `mkdir -p docs/osx/plans docs/osx/defects` (historical: a temporary **`plans/agent/`** subtree existed and was later removed after merges).
2. **`git mv`** + **rename** — move numbered **01–08** (later extended to **plan-009** / **plan-010**), **HANDOFF**, and **osx-related** session notes into **`docs/osx/plans/`**, applying the **`plan-###`** / **`plan-handoff-`** rules above. Legacy **`docs/plans/`** stub redirects were **removed**; the plan index and shortcuts live only under **`docs/osx/plans/README.md`** (thin **`docs/plans/README.md`** pointer).
3. **Author** **`docs/osx/plans/README.md`** and **`docs/osx/defects/README.md`** with lookup tables.
4. **Extract defects** — create **`def-001`…`def-009`** (and later ids) detail files; then **replace** long subsections in **`plan-002`** with links (keep workflow text that is not defect-specific).
5. **Update references** — ripgrep for `docs/plans/0[1-8]-macos`, `DEF-00x` anchors; patch **`.cursorrules`** so mouse-clicker session notes merge into **`docs/osx/plans/plan-###-….md`** (no **`docs/osx/plans/agent/`** tree).
6. **`docs/plans/README.md`** — thin pointer to **`docs/osx/plans/README.md`**; non-clicker reference plans live under **`docs/osx/plans/`** when kept in-repo (no **`docs/plans/agent/`** tree).
7. **`docs/osx/README.md`** — hub page linking **Plans**, **Defects**, and [`osx/README.md`](../../osx/README.md) (operator env / jq).
8. **Verify** — e.g. `rg 'plan-002-macos-mouse-click-terminal-ux'` finds **`docs/osx/plans/plan-002-…`**; run link check mentally on relative paths from new files.

## Policy updates

- **`.cursorrules`**: mouse-clicker planning extends **`docs/osx/plans/plan-###-….md`**; non-clicker reference **`*.plan.md`** files may live under **`docs/osx/plans/`** (or a product-specific **`docs/`** tree).

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| External URLs (GitHub, LinkedIn drafts) point at old paths | Prefer **`git mv`**; **`docs/plans/README.md`** remains a short pointer; update LinkedIn drafts only if republished |
| Deep relative links (`../../osx/`) break | Recompute from **`docs/osx/plans/`** depth (often one more `..` than from `docs/plans/`) |
| Duplicate “plan 02” defect workflow vs defects folder | Keep **workflow** in 02; keep **detail narrative** only under **`docs/osx/defects/`** |

## Open decisions (historical)

1. **Flat vs `agent/`** — **Resolved (2026-04-29):** no **`docs/osx/plans/agent/`** tree; session notes merged into **`plan-###`**.
2. **Automation deep-dive** — **Resolved:** content folded into **[plan-003 § Additional automation backlog](plans/plan-003-macos-mouse-click-tui-automation.md#additional-automation-backlog-session-notes-merge)**.
3. **Location of this meta file** — still TBD if moved under **`plans/`**; optional hygiene only.

## Success criteria

- Canonical plan paths and the merged plan index live under **`docs/osx/plans/`** (e.g. **`plan-002-macos-mouse-click-terminal-ux.md`**, **[`README.md`](plans/README.md)**); **`docs/plans/README.md`** is a one-screen pointer only.
- All **DEF-001–009** bodies exist under **`docs/osx/defects/`** as **`def-001`…`def-009`** files with matching README rows (extend the numeric range as new defects are filed).
- **`osx/macos_mouse_click.py`** header comment points at the new navigation plan path.
- **`docs/osx/README.md`** is the single entry point for “where is clicker engineering docs?”

---

**Next step (historical):** ~~Review and sign off, then execute migration~~ — **completed.** Further doc work is incremental (new **`plan-###`**, **`def-###`**) under **`docs/osx/`**; **`docs/plans/README.md`** is a thin entry for **`docs/plans/`** visitors only (no duplicate stub files under **`docs/plans/`** for the clicker).
