# macOS clicker documentation reorganization (review plan)

This document specifies a **directory and content split** for everything that documents **`osx/macos_mouse_click.py`**: product plans, agent/session plans, and **DEF-xxx** defects. It is a **review artifact** only until stakeholders sign off; implementation should follow the phases below in order.

## Goals

1. **Single osx doc hub** under **`docs/osx/`** so operators and agents do not hunt across **`docs/plans/`**, **`docs/plans/agent/`**, and embedded defect prose.
2. **`docs/osx/plans/`** — all plan-style documents for the clicker (numbered **01–08**, handoffs, and former **`docs/plans/agent/`** files that belong to this program).
3. **`docs/osx/defects/`** — one **detail file per DEF-xxx**, extracted from the long-form audit in **plan 02** today.
4. **Cross-links** — each plan that references a defect links to **`../defects/def-###-….md`**; each defect file links back to **owning plan(s)** (e.g. `plan-002`, `plan-003`, agent design plan).
5. **Index READMEs** — **`docs/osx/plans/README.md`** and **`docs/osx/defects/README.md`** with a **lookup table**: id, date opened, date completed (if any), status, one-line title, **markdown link** to the detail document.
6. **Repository hygiene** — update **all in-repo pointers** (script comments, **`osx/README.md`**, tests, **`.cursorrules`**, **`docs/plans/README.md`**) so nothing still points at removed paths.

## Non-goals (this pass)

- Moving **non–mouse-clicker** agent plans (e.g. unrelated server test frameworks) into **`docs/osx/`** — they stay under **`docs/plans/agent/`** or move under a different product folder later.
- Rewriting plan **content** beyond moving paths, adding cross-links, and stripping duplicated defect bodies from plan 02 after extraction.

## Canonical inventory (after move; `osx/macos_mouse_click.py`)

| Location | Role |
|----------|------|
| [`plans/plan-001-macos-clicker.md`](plans/plan-001-macos-clicker.md) | Core product spec |
| [`plans/plan-002-macos-mouse-click-terminal-ux.md`](plans/plan-002-macos-mouse-click-terminal-ux.md) | UX overlay + **Defect summary** table; **DEF-001–008** narrative in [`defects/`](defects/README.md) |
| [plan-003](plans/plan-003-macos-mouse-click-tui-automation.md) … [plan-008](plans/plan-008-macos-mouse-click-stop-during-run.md) | Follow-on product plans (**003**–**008**) |
| [`plans/plan-handoff-2026-04-18-linkedin-macos-clicker-draft.md`](plans/plan-handoff-2026-04-18-linkedin-macos-clicker-draft.md) | Session handoff (clicker context) |
| [`plans/agent/plan-agent-new-test-up-down-navigation.plan.md`](plans/agent/plan-agent-new-test-up-down-navigation.plan.md) | Agent plan: navigation tests + Phase 2 logging |
| [`plans/agent/plan-agent-def-006-tui-arrow-keys.plan.md`](plans/agent/plan-agent-def-006-tui-arrow-keys.plan.md) | Agent plan: DEF-006 CSI design |
| [`plans/agent/plan-agent-arrow-key-double-press-analysis.plan.md`](plans/agent/plan-agent-arrow-key-double-press-analysis.plan.md) | Analysis: DEF-008 |
| [`plans/agent/plan-agent-osx-dry-refactor.plan.md`](plans/agent/plan-agent-osx-dry-refactor.plan.md) | Agent plan: osx test DRY |
| [`plans/agent/plan-agent-automation-deep-dive.plan.md`](plans/agent/plan-agent-automation-deep-dive.plan.md) | Plan 03 automation deep dive (clicker-scoped) |
| [`../plans/README.md`](../plans/README.md) / [`../plans/agent/README.md`](../plans/agent/README.md) | Top-level **`docs/plans/`** index + non-clicker agent plans |

**Redirects:** old paths under **`docs/plans/`** (e.g. `01-macos-clicker.md`, **`docs/plans/agent/new-test-…`**) are **stub files** pointing here — see **[`docs/plans/README.md`](../plans/README.md)**.

**Pointers elsewhere (must update after move):** [`osx/macos_mouse_click.py`](../../osx/macos_mouse_click.py), [`osx/README.md`](../../osx/README.md), [`osx/tests/test_rich_table_nav_down_pty.py`](../../osx/tests/test_rich_table_nav_down_pty.py), [`osx/tests/_tmp_tty_probe.py`](../../osx/tests/_tmp_tty_probe.py), [`.cursorrules`](../../.cursorrules) (agent plan path rule).

## File naming convention (required)

- **Plans** — every plan file name **starts with `plan-`**, then:
  - **Numbered product plans (old 01–08):** **`plan-###-`** + kebab slug, where **`###`** is the **zero-padded plan number** (`001` … `008`) so directory sort matches program order.  
    Examples: `plan-001-macos-clicker.md`, `plan-002-macos-mouse-click-terminal-ux.md`, `plan-008-macos-mouse-click-stop-during-run.md`.
  - **Session / agent plans (no program number):** **`plan-agent-`** + kebab base name + optional **`.plan.md`**.  
    Examples: `plan-agent-new-test-up-down-navigation.plan.md`, `plan-agent-def-006-tui-arrow-keys.plan.md`, `plan-agent-arrow-key-double-press-analysis.plan.md`, `plan-agent-osx-dry-refactor.plan.md`.
  - **Handoff / narrative docs:** **`plan-handoff-`** + date + short slug (no `###`).  
    Example: `plan-handoff-2026-04-18-linkedin-macos-clicker-draft.md`.
- **Defects** — every defect detail file **starts with `def-`**, then **`###`** = **zero-padded defect id** (`001` … `008`) + kebab slug.  
  Examples: `def-001-console-input-highlight.md`, `def-006-tui-arrow-multi-press.md`, `def-007-duplicate-n-flag-last-wins.md`, `def-008-residual-arrow-double-press.md`.  
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
    agent/                  # optional: keep agent/ subtree to mirror old layout
      README.md
      plan-agent-new-test-up-down-navigation.plan.md
      plan-agent-def-006-tui-arrow-keys.plan.md
      plan-agent-arrow-key-double-press-analysis.plan.md
      plan-agent-osx-dry-refactor.plan.md
      plan-agent-automation-deep-dive.plan.md   # if retained (rename from plan-03-automation-deep-dive to avoid "plan-agent-plan-03" stutter)
  defects/
    README.md               # Lookup table for all defects
    def-001-console-input-highlight.md
    def-002-arrow-misread-as-esc.md
    …
    def-008-residual-arrow-double-press.md
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
| plan-agent-new-test-up-down-navigation | Phase 1–3 nav + logging | … | … | in progress | [agent/plan-agent-new-test-up-down-navigation.plan.md](agent/plan-agent-new-test-up-down-navigation.plan.md) |

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
| Each `def-###-….md` | **Plans:** [`plan-002-…`](plans/plan-002-macos-mouse-click-terminal-ux.md), plus e.g. DEF-006 → [`plan-agent-def-006-tui-arrow-keys.plan.md`](plans/agent/plan-agent-def-006-tui-arrow-keys.plan.md) |
| `plan-agent-arrow-key-double-press-analysis.plan.md` | `def-008-…` detail file |
| `plan-agent-new-test-up-down-navigation.plan.md` | Phase 2 checklist → `plan-002` + relevant `def-###` files |

## Migration phases (execution checklist)

1. **Create tree** — `mkdir -p docs/osx/plans/agent docs/osx/defects`.
2. **`git mv`** + **rename** — move numbered **01–08**, **HANDOFF**, and **osx-related** `docs/plans/agent/*.plan.md` into **`docs/osx/plans/`** (and **`docs/osx/plans/agent/`**), applying the **`plan-###`** / **`plan-agent-`** / **`plan-handoff-`** rules above.
3. **Author** **`docs/osx/plans/README.md`** and **`docs/osx/defects/README.md`** with lookup tables.
4. **Extract defects** — create **`def-001`…`def-008`** files; then **replace** long subsections in **`plan-002`** with links (keep workflow text that is not defect-specific).
5. **Update references** — ripgrep for `docs/plans/0[1-8]-macos`, `docs/plans/agent/` (osx files), `DEF-00x` anchors; patch **`.cursorrules`** to state canonical agent plans for clicker live under **`docs/osx/plans/agent/`** (or flat under `docs/osx/plans/`).
6. **`docs/plans/README.md`** — add a prominent **“macOS clicker docs moved to `docs/osx/`”** stanza with link to **`docs/osx/README.md`**; keep non-clicker plans listed in `docs/plans/`.
7. **`docs/osx/README.md`** — hub page linking **Plans**, **Defects**, and [`osx/README.md`](../../osx/README.md) (operator env / jq).
8. **Verify** — `rg 'docs/plans/02-macos|plan-002-macos'` from repo root; run link check mentally on relative paths from new files.

## Policy updates

- **`.cursorrules`**: replace “store under `docs/plans/agent/`” with “store **mouse-clicker** session plans under **`docs/osx/plans/agent/`** (kebab-case); other products may keep **`docs/plans/agent/`** until they get their own tree.”
- **`docs/plans/agent/README.md`**: note that **clicker-specific** plans have moved; leave non-clicker plans indexed there **or** split README.

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| External URLs (GitHub, LinkedIn drafts) point at old paths | Prefer **`git mv`**; add short **redirect note** in old `docs/plans/README.md`; update LinkedIn drafts only if republished |
| Deep relative links (`../../osx/`) break | Recompute from **`docs/osx/plans/`** depth (often one more `..` than from `docs/plans/`) |
| Duplicate “plan 02” defect workflow vs defects folder | Keep **workflow** in 02; keep **detail narrative** only under **`docs/osx/defects/`** |

## Open decisions (resolve before implementation)

1. **Flat vs `agent/` under `docs/osx/plans/`** — recommend **`docs/osx/plans/agent/`** for session plans to minimize churn in **`.cursorrules`** wording.
2. **`plan-agent-automation-deep-dive.plan.md`** (ex-`plan-03-automation-deep-dive`) — treated as **clicker-scoped**; it lives under **`plans/agent/`** with the other **`plan-agent-*`** files.
3. **Whether this review file stays at `docs/osx/OSX-DOCS-REORGANIZATION-PLAN.md` or moves to `docs/osx/plans/`** after execution.

## Success criteria

- `rg "docs/plans/02-macos-mouse-click-terminal-ux"` from repo still finds **at least one** valid path **or** a stub redirect in `docs/plans/` if you choose stub pattern.
- All **DEF-001–008** bodies exist under **`docs/osx/defects/`** as **`def-001`…`def-008`** files with matching README rows.
- **`osx/macos_mouse_click.py`** header comment points at the new navigation plan path.
- **`docs/osx/README.md`** is the single entry point for “where is clicker engineering docs?”

---

**Next step:** Review this plan; after sign-off, execute **Migration phases** in one or more focused commits (docs-only first, then pointer sweep).
