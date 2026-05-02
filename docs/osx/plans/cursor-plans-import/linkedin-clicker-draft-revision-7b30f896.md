<!-- 7b30f896-9430-4faf-ae44-92b593896e92 -->
---
todos:
  - id: "inventory-facts"
    content: "Lock factual bullets: docs/osx hub URL, merged index story, optional plan-010/--learn-points, one-line testing cred (55 pytest) if desired"
    status: pending
  - id: "revise-txt"
    content: "Edit 2026-04-18-macos-mouse-click-plans-session.txt (URLs, third bullet, optional 4th bullet); re-check ≤3000 chars and style-guide formatting"
    status: pending
  - id: "sync-md-handoff"
    content: "Regenerate draft .md mirror + revision 5 notes; update plan-handoff-2026-04-18-linkedin-macos-clicker-draft.md pointers; adjust LinkedIn-posts.md repo link if needed"
    status: pending
isProject: false
---
# Revise Apr 18 clicker LinkedIn draft to match current project

## Context: what the draft is today

- **Posting source:** [LinkedIn-posts/drafts/2026-04-18-macos-mouse-click-plans-session.txt](LinkedIn-posts/drafts/2026-04-18-macos-mouse-click-plans-session.txt) (Perspective **#1 — Scaffolding, not software** per [2026-04-18-macos-mouse-click-plans-session.md](LinkedIn-posts/drafts/2026-04-18-macos-mouse-click-plans-session.md)).
- **Archive / mirror / revision history:** same basename `.md`; indexed from [LinkedIn-posts/LinkedIn-posts.md](LinkedIn-posts/LinkedIn-posts.md) (line ~13).
- **Session handoff (engineering):** [docs/osx/plans/plan-handoff-2026-04-18-linkedin-macos-clicker-draft.md](docs/osx/plans/plan-handoff-2026-04-18-linkedin-macos-clicker-draft.md) — still describes `docs/plans/` as backbone; should be updated when the post is revised so marketing and handoff agree.

## Current project state (for post accuracy)

**Documentation and plans**

- Single operator hub: [docs/osx/README.md](docs/osx/README.md) links **Plans** ([docs/osx/plans/README.md](docs/osx/plans/README.md)), **Defects** (`DEF-001`–`DEF-009`), coverage gap notes, reorg plan.
- **Product plans:** **plan-001**–**plan-010** in the dated table; **plan-001** Shipped (core behavior), **plan-002** Closed (v1) (Rich pre-run), **plan-010** Shipped ([`--learn-points`](docs/osx/plans/plan-010-macos-mouse-click-learn-points-collect.md) batch anchor capture); **003–009** remain Roadmap rows.
- **Index consolidation:** former long [docs/plans/README.md](docs/plans/README.md) content is merged into `docs/osx/plans/README.md`; `docs/plans/README.md` is now a **short pointer** only (non-clicker session plans still under [docs/plans/agent/](docs/plans/agent/README.md)).
- **Removed:** one-line redirect stubs under `docs/plans/` (old `01`–`08`, handoff filenames) and legacy clicker stubs under `docs/plans/agent/` — external bookmarks to those paths are dead; GitHub tree links should target `docs/osx/`.

**Implementation touchpoint**

- [osx/macos_mouse_click.py](osx/macos_mouse_click.py) module docstring already points to **`docs/osx/README.md`** for plans/defects/agent notes.

**Testing (factual line you can use sparingly)**

- `make -C osx test-quick` runs the full `osx/tests` pytest tree (recent runs: **55** tests passing). Coverage includes dry-run / JSON, Rich TUI and PTY navigation paths (e.g. `test_rich_table_nav_down_pty.py`, `test_def009_rich_table_layout_pty.py`), learn-collect helpers, open-defect workflows, etc. — good **one phrase** evidence of “small scope, serious feedback loops” without turning the post into a test matrix.

## Style / process rules to preserve ([LinkedIn-style-guide.md](LinkedIn-posts/LinkedIn-style-guide.md))

- **Unicode bold** section lines (not markdown `**`), **▶** bullets, **two trailing spaces** on heading/bullet lines in the `.txt` where the guide requires line breaks for LinkedIn.
- **Zero-width spaces** inside **file names** in the post body (e.g. `README​.md`) so LinkedIn does not auto-link; **URLs stay clean**.
- Re-check **character count ≤ 3000** on the `.txt` after edits (guide + posting script expectation).

## Concrete revision suggestions (content)

1. **Fix stale URLs and repo framing**  
   - Replace `https://github.com/.../tree/main/docs/plans` with the **hub** or plans index, e.g. `.../tree/main/docs/osx` or `.../tree/main/docs/osx/plans` (pick one primary link to avoid clutter).  
   - Keep the **script** blob URL as-is (still correct).

2. **Rewrite the middle bullet that names `docs/plans/README​.md`**  
   - Today that claim is wrong. Options that keep the *story* (index vs semantics): e.g. “folded the plan index into **`docs/osx/plans/README​.md`** so shipped core behavior vs closed UX stay on one page” or “moved clicker docs under **`docs/osx/`** so the hub matches where the code lives.”  
   - Avoid reintroducing heavy plan numbers unless you want a sharper engineering tone (Perspective #1 usually stays light).

3. **Optional fourth ▶ line (only if length allows)**  
   - One concrete **shipped** capability: **`--learn-points`** / plan-010 (batch learn anchors)—grounds “still a narrow utility” in something new readers can grep for.  
   - Alternative: one line on **doc + stub cleanup** (single canonical tree)—fits “honest snapshots” without naming every file.

4. **Optional closing tweak**  
   - If you add plan-010, the closing “narrow utility” sentence still works; you can nod to “pytest-backed regressions” in **six words or fewer** if you want a credibility bump without sounding like a release note.

5. **Companion files to update in the same change**  
   - **[`2026-04-18-macos-mouse-click-plans-session.md`](LinkedIn-posts/drafts/2026-04-18-macos-mouse-click-plans-session.md):** refresh **Repo** link, regenerate the indented mirror from `.txt`, add **Revision 5** notes (what changed vs rev 4).  
   - **[`plan-handoff-2026-04-18-linkedin-macos-clicker-draft.md`](docs/osx/plans/plan-handoff-2026-04-18-linkedin-macos-clicker-draft.md):** update “primary artifact” / pointer bullets so they reference **`docs/osx/`** and the merged README story (no `docs/plans/` as engineering backbone).  
   - **`LinkedIn-posts.md`:** only if you rename files or change paths (optional).

## What not to do unless you change angle

- Do not lean on **Perspective #2** (pure comedy) or **#5** (ToS sermon) unless you intentionally switch arcs—the current draft is **#1**.
- Do not dump **DEF-001–009** or plan tables into LinkedIn; keep the post narrative-first.

## Verification before publish

- `wc -m` (or equivalent) on the `.txt` for **≤ 3000** characters.  
- Quick read against style guide checklist (Unicode headers, ▶, ZWSP on dotted filenames in body).  
- After posting: style-guide workflow—LinkedIn URL into `.md`, update `LinkedIn-posts.md`, mark handoff “published” if you track that there.
