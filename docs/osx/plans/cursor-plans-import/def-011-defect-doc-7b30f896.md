<!-- 7b30f896-9430-4faf-ae44-92b593896e92 -->
---
todos:
  - id: "write-def-011-defect"
    content: "Add docs/osx/defects/def-011-mouse-move-abort-arm-threshold-annulus.md (canonical defect: frontmatter, observed, repro, root cause, fix directions, DEF-010 link, optional mermaid)"
    status: pending
  - id: "canonical-agent-plan"
    content: "Add docs/osx/plans/agent/plan-agent-def-011-mouse-move-abort-annulus.plan.md — YAML todos + short summary linking to ../../defects/def-011-….md; register in docs/osx/plans/agent/README.md"
    status: pending
  - id: "defects-readme-row"
    content: "Extend docs/osx/defects/README.md to DEF-011; Document column → def-011-mouse-move-abort-arm-threshold-annulus.md"
    status: pending
  - id: "plan-002-row"
    content: "Add DEF-011 row + manual verification line in plan-002; detail link → ../defects/def-011-….md"
    status: pending
  - id: "rate-control-crosslink"
    content: "One-line DEF-011 pointer in plan-agent-cookie-clicker-rate-control.plan.md (link defect + optional agent plan)"
    status: pending
isProject: false
---
# DEF-011: False mouse-move abort on buy ladder (arm vs threshold annulus)

## Canonical locations (repo rules)

| Artifact | Path (repo root) | Notes |
|----------|------------------|--------|
| **DEF-011 defect (canonical)** | **`docs/osx/defects/def-011-mouse-move-abort-arm-threshold-annulus.md`** | Same pattern as **DEF-001–DEF-010**: `def-###-….md` under **`./docs/osx/defects/`**. Full narrative lives here. |
| **Agent session plan** | **`docs/osx/plans/agent/plan-agent-def-011-mouse-move-abort-annulus.plan.md`** | **`plan-agent-`** prefix per **`.cursorrules`**; YAML `todos` + brief scope + **link** to the defect file (no duplicate long-form defect body required). |
| **Indexes** | `docs/osx/plans/agent/README.md`, `docs/osx/defects/README.md`, `docs/osx/plans/plan-002-macos-mouse-click-terminal-ux.md` | README table **Document** for DEF-011 → **`def-011-….md`** under defects. |

**Not canonical:** `~/.cursor/plans/` — copy substance into the repo paths above.

## Why this is a defect (root cause)

In [`osx/macos_mouse_click.py`](osx/macos_mouse_click.py), `run_synthetic_loop` does **both** checks on **every** iteration **before** `post_synthetic_click`:

```1459:1476:osx/macos_mouse_click.py
    while True:
        ...
        if abort_mouse:
            cx, cy = get_mouse_location(qz)
            d_sq = _dist_sq(cx, cy, float(x), float(y))
            if not armed and d_sq <= arm_sq:
                armed = True
            if armed and d_sq > thr_sq:
                request_shutdown()
                print(
                    "Stopped (cursor moved away from click target beyond "
                    "--mouse-move-threshold-px).",
                    ...
                )
                return 130
        post_synthetic_click(qz, x, y)
```

With defaults from [`_effective_mouse_arm_radius_px`](osx/macos_mouse_click.py) (`max(60, 2×threshold)`) and [`osx/macos_mouse_click_loop.sh`](osx/macos_mouse_click_loop.sh) passing `--mouse-move-threshold-px 20`:

- **Arm radius** `arm_r` = **60** px (distance to target to set `armed`).
- **Abort** when distance **> 20** px from target.

So any cursor position with **20 < d ≤ 60** is in an **annulus**: the loop **arms** (`d ≤ arm_r`) and **immediately aborts** (`d > thr`) on the **same** `get_mouse_location` sample, **before the first synthetic click** of that burst.

This is **not** “the user moved the mouse”; it is inconsistent geometry between “close enough to arm” and “far enough to count as left”.

## Why the ladder reproduces it

[`osx/macos_mouse_click_loop.sh`](osx/macos_mouse_click_loop.sh) invokes each ladder row as a **separate** `macos_mouse_click.py` process (`click_target` with fixed `-x/-y`). **`armed` resets each invocation.**

[`osx/config/cookie_clicker_profile.defaults.json`](osx/config/cookie_clicker_profile.defaults.json) uses **`row_spacing` 63.5** px between store rows. After clicking **portal** (`y ≈ -48.8`), the pointer is near that row; **alchemy_lab** target is **`y ≈ -103.6`**, so **Δy ≈ 55 px** — inside **(20, 60]**. That matches the transcript: first two rows complete, third row aborts with `Stopped (cursor moved away from click target beyond --mouse-move-threshold-px).`

Changing `anchor_y` per line is **expected** (different buildings); the defect is the **abort logic / default radii**, not the JSON alone.

## Deliverables (documentation only)

1. **`docs/osx/defects/def-011-mouse-move-abort-arm-threshold-annulus.md`** — canonical defect: frontmatter `id: DEF-011`, `related_plans`, status **Open**, **Observed** (operator log), **Reproduction**, **Root cause**, **Expected**, **Fix directions** (bullets only), cross-link **DEF-010**, optional mermaid (see below).

2. **`docs/osx/plans/agent/plan-agent-def-011-mouse-move-abort-annulus.plan.md`** — agent plan: YAML todos + one-paragraph summary + link to **`../../defects/def-011-mouse-move-abort-arm-threshold-annulus.md`** (optional short duplicate of root cause).

3. **`docs/osx/plans/agent/README.md`** — new table row for the agent plan file.

4. **`docs/osx/defects/README.md`** — index **DEF-001–DEF-011**; DEF-011 **Document** → **`def-011-mouse-move-abort-arm-threshold-annulus.md`**.

5. **`docs/osx/plans/plan-002-macos-mouse-click-terminal-ux.md`** — Defect summary row + manual verification blurb; detail link → **`../defects/def-011-mouse-move-abort-arm-threshold-annulus.md`**.

6. **`docs/osx/plans/agent/plan-agent-cookie-clicker-rate-control.plan.md`** — one-line DEF-011 pointer (defect + agent plan as needed).

## Out of scope for this plan

- Code changes to `run_synthetic_loop`, defaults, or `macos_mouse_click_loop.sh` (documentation only unless you ask for a follow-up fix).

## Optional diagram (embed in the defect file body)

```mermaid
flowchart LR
  target[ClickTarget]
  inner[thr_inner]
  outer[arm_outer]
  target --> inner
  inner --> outer
```

Narrative: abort ring **inner radius = thr**; arm ring **outer radius = arm_r**; if **arm_r > thr**, the band between them is **armed-and-abort** in one tick.
