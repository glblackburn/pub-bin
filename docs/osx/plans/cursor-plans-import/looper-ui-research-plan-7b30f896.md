<!-- 7b30f896-9430-4faf-ae44-92b593896e92 -->
---
todos:
  - id: "write-research-plan-md"
    content: "Add plan-agent-looper-cookie-clicker-ui-research.plan.md with terminology, looper summary, screenshot table, deltas, feature backlog, non-goals, optional mermaid."
    status: pending
  - id: "index-readme-row"
    content: "Append README.md table row in docs/osx/plans/agent/ for the new research plan."
    status: pending
isProject: false
---
# Research plan: Looper features from Cookie Clicker UI evidence

## Deliverable (after you approve this plan)

1. **New file:** [`docs/osx/plans/agent/plan-agent-looper-cookie-clicker-ui-research.plan.md`](docs/osx/plans/agent/plan-agent-looper-cookie-clicker-ui-research.plan.md) — same house style as other agent plans (HTML canonical comment, optional YAML `todos` with `completed` items for “research written”, **`isProject: false`**), standard **Terminology** paragraph for consistency.
2. **Index:** Add one row to [`docs/osx/plans/agent/README.md`](docs/osx/plans/agent/README.md) (Summary ~1 line, Status **Done**, Created/Updated from `git log` after commit or same calendar date on first add).

**Do not edit** the Cursor-generated plan file under `~/.cursor/plans/`.

---

## 1. What the looper does today (high level)

Source: [`osx/macos_mouse_click_loop.sh`](osx/macos_mouse_click_loop.sh).

- **Orchestration:** A **`while true`** outer loop calls **`run_once`** each “cycle”, increments a counter, optionally exits after **`-c <count>`**, otherwise **`sleep 30`** between cycles.
- **`run_once`:** Forces **`MACOS_MOUSE_CLICK_DEBUG_TUI`** / log env for the Python clicker, optionally runs **`run_buy_ladder`**, then runs a **long fixed burst** (**`-n 3000`**) on one screen coordinate pair (big cookie).
- **`run_buy_ladder`:** A **fixed vertical list** of twelve buildings (time machine → cursor). Each step: **five** **`macos_mouse_click.py`** invocations at **hard-coded** **`-x/-y`** (same **x**, stepped **y**), **`-n 5`**, **`-Y`**.
- **CLI:** **`-h`**, **`-c`** finite cycles, **`-S`** skips the ladder (cookie burst only).
- **Implicit assumptions:** Absolute **display** coordinates; game window position/size unchanged; no reading of on-screen prices, bulk mode, or button enabled state; no golden cookies, upgrades row, or scrolling.

---

## 2. Screenshot set analyzed

Path: **`docs/osx/screenshots/cookie-clicker/`** (four PNGs captured 2026-04-25; filenames are default macOS **`Screenshot_*.png`** pattern).

| File (time) | Notable UI / economy state |
|---------------|----------------------------|
| `…8.20.52_PM.png` | Late mid-game: **~202T** cookies, **~8.1B** CpS; store shows **single-buy** style prices (~**60–163T** per next unit); scrollbar on store; big cookie + cursor swarm. |
| `…8.21.09_PM.png` | **~203T** cookies but **~56.8B** CpS (large CpS jump vs prior); store bulk selector **x100**; displayed costs **quintillions+**; **all rows greyed** (cannot afford x100). |
| `…8.21.38_PM.png` | **~207T** cookies, same **~56.8B** CpS and **x100** store; **+843B** float text on cookie (active gains); still unaffordable at x100. |
| `…8.23.38_PM.png` | **~213T** cookies, **CpS back to ~8.1B**; store back to **single-unit** prices (~**60–163T**); buildings **affordable** again (except priciest visible tier). |

**Note:** The repo’s file search did not list this folder (likely **cursorignore** or similar); the directory **does exist** on disk with these four files. The written plan should name each file so evidence stays traceable even if tracking policy changes.

---

## 3. Key differences across screenshots (automation-relevant)

1. **Bulk purchase mode (x1 / x10 / x100 / buy all)** dominates whether the ladder’s blind **5× clicks** do anything: at **x100**, prices in the shots are astronomically above banked cookies → **greyed** store; at **x1**, same bank can **afford** many rows. The script does **not** set or detect this control.
2. **CpS swings** (**~8B** vs **~56B**) imply **buffs, golden cookies, wrinklers, pantheon, dragon**, etc.—the loop has **no phase** tied to “high value window” vs idle.
3. **Fixed Y ladder** assumes a **static store layout**; the **scrollbar** indicates more tiers below—clicks may miss or hit the wrong row after unlocks, zoom, or window resize.
4. **Economy ordering** in the store is **not strictly “top = cheapest next”** (e.g. some higher-tier items can be cheaper than mid-list); a **fixed top-to-bottom** buy order is **not** the same as “best next purchase.”
5. **Middle column** exposes **Grimoire** / **building specials**—untouched by the current ladder (possible high-value clicks).
6. **Golden cookies** and **upgrade tiles** (when visible) are high-leverage; the script only spams the **big cookie** coordinate.

---

## 4. Suggested feature backlog (for your ideas to refine)

Group loosely by **effort / dependency**; the saved plan doc will expand each with one-line rationale tied to the screenshots above.

**Config and ergonomics**

- **External config** (YAML/JSON or env): ladder **coordinates**, **per-step `-n`**, cookie **burst count**, **inter-cycle sleep**, optional **TUI debug** defaults—avoid editing the script per machine.
- **CLI flags** for **`-n`**, sleep, and paths to a **ladder definition file** (keep bash thin; optional Python helper later).

**Store / buys**

- **Bulk-mode strategy:** parameterize **x1/x10/x100** (click the control before the ladder, or document “operator must leave on x1”).
- **Affordability-aware ladder:** skip or shorten clicks when the UI is greyed (needs **vision**, **accessibility API**, or **operator rule** “only run ladder when x1”).
- **Scroll-aware ladder:** scroll the store panel to anchor rows before clicking (coordinate helper or repeated PageDown region).
- **Value-based purchasing:** replace fixed order with **heuristic** (e.g. click **brightest** / **lowest-row affordable** / user-ranked list)—still research-heavy without OCR.

**Cookie burst and timing**

- **Variable burst length** or **time-bounded** burst (run N seconds of clicks, not fixed 3000).
- **Buff-aware burst:** detect high-CpS window (same vision problem) and extend burst or shorten inter-cycle sleep.

**Game events (high impact, higher complexity)**

- **Golden cookie sweep:** secondary loop clicking **candidate screen regions** or random offsets within a safe bbox.
- **Upgrade strip:** optional click pass on a configured **rectangle** above the building list.
- **Mini-game hooks:** optional **Grimoire** / spell sequence (very game-version-sensitive).

**Safety and observability**

- **Dry-run / “move only”** ladder mode (if/when supported by `macos_mouse_click.py` consistently for these paths).
- **Structured cycle log** (timestamp, flags, optional screenshot path) for correlating with Cookie’s own stats.

**Non-goals (for the research doc)**

- Full **OCR** of cookie counts or optimal play AI (call out as future if ever).
- Cheating multiplayer or violating game ToS (note **personal automation** disclaimer only).

---

## 5. Optional diagram for the plan markdown

Mermaid **flowchart**: **`run_cycle`** → **`set_bulk_mode?`** → **`run_buy_ladder`** vs **`skip`** → **`cookie_burst`** → **`sleep`** — parallel note node **`game_buffs`** affecting **CpS** and **golden_cookie** — emphasizes **UI state** not modeled today.

---

## 6. Verification

- No code changes required for the **research-only** doc; optional **`bash -n osx/macos_mouse_click_loop.sh`** if any cross-links prompt script edits later.
- If screenshots should be **versioned**, confirm they are **git-tracked** (and consider **`NN-kebab-case.png`** rename per [`docs/osx/plans/DEVELOPMENT_NARRATIVE.md`](docs/osx/plans/DEVELOPMENT_NARRATIVE.md) Phase 15 pattern)—can be a **follow-up** commit separate from the plan text.
