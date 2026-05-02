<!-- 7b30f896-9430-4faf-ae44-92b593896e92 -->
---
todos:
  - id: "profile-delay-keys"
    content: "Add optional profile keys (cookie_click_delay_seconds, post_cookie_settle_seconds) + schema/defaults"
    status: pending
  - id: "loop-wire-delay"
    content: "Wire macos_mouse_click_loop.sh click_target / cookie path to -d from profile with 0 escape hatch"
    status: pending
  - id: "docs-stop-ux"
    content: "Document Ctrl+C, terminal focus, and interaction of delay vs interrupt in osx/README.md"
    status: pending
  - id: "optional-chunking"
    content: "If needed: chunked cookie burst + bash SIGINT trap between chunks"
    status: pending
isProject: false
---
# Cookie burst rate control and user breakout

## Scope (read this first)

- **Planning and design only — no code changes** in this phase unless a separate message explicitly requests implementation.
- **Todos** in YAML are backlog for a future pass; **“Files likely touched”** / **“Acceptance criteria”** apply only when that pass runs.
- Canonical copy in the workspace: `docs/osx/plans/agent/plan-agent-cookie-clicker-rate-control.plan.md`.

## Current behavior (baseline)

In [`osx/macos_mouse_click_loop.sh`](osx/macos_mouse_click_loop.sh), `click_target` always runs:

```bash
"${mouse_click}" -d 0 -x "${target_x}" -y "${target_y}" -n "${target_n}" -Y
```

So **every synthetic click is immediate** (no `sleep_interruptible` between clicks when delay is 0; see [`run_synthetic_loop`](osx/macos_mouse_click.py) and [`sleep_interruptible`](osx/macos_mouse_click.py): `seconds <= 0` returns immediately).

[`preview_defaults`](osx/config/cookie_clicker_profile.defaults.json) / profile supplies `cookie_click_count` (e.g. 3000) and `cycle_sleep_seconds` (e.g. 30). The **30s sleep runs only after the entire `run_once`** (ladder + cookie burst), so it **does not throttle** delivery during the 3000-click burst. That matches “next cycle starts before the previous run is processed” if the game is still draining a backlog when the next cycle begins.

**Interrupt path today:** `macos_mouse_click.py` checks `shutdown_requested()` each loop iteration and uses interruptible sleeps **only when delay &gt; 0**. With `-d 0`, the inner loop is a tight loop (two `CGEventPost` calls per click); **SIGINT can still stop the process**, but there is **less natural yielding** than with a positive delay, so stopping can feel less responsive under load.

---

## Design goal

Balance three forces:

1. **UI throughput:** do not enqueue clicks faster than the browser/game can apply them.
2. **Operator escape:** return control quickly (terminal focus, Ctrl+C, or explicit cancel).
3. **Throughput / session length:** avoid making a 3000-click “session” unnecessarily long.

No single constant works across hardware, browser, and game state; the plan favors **configurable policy** plus optional **post-burst settle**.

---

## Options (pros / cons)

### A. Per-click delay (`-d` &gt; 0) from profile or CLI

Wire `click_target` (or cookie-only path) to pass `-d "${COOKIE_CLICK_DELAY}"` from `preview_defaults` (e.g. `cookie_click_delay_seconds: 0.015`).

| Pros | Cons |
|------|------|
| Uses existing `sleep_interruptible` → **better SIGINT responsiveness** between clicks | Total burst time grows linearly (`count × delay`); 3000 × 15ms ≈ 45s before overhead |
| Simple to implement and reason about | “Optimal” value is **machine- and load-dependent**; needs doc + sane defaults |
| Predictable load on event queue | Ladder clicks might also need separate delay knob |

### B. Chunked bursts (micro-batches + short pause)

e.g. 100 clicks, `sleep 0.05`, repeat until count reached (implemented in loop script or a small Python helper calling the clicker with `-n 100` repeatedly).

| Pros | Cons |
|------|------|
| Lets the UI **drain between gutters** without per-click syscall overhead | More moving parts (batch size, pause length); preview/manifest must stay consistent if counts split |
| Natural **checkpoints** for `shutdown_requested` / subprocess boundaries | Edge cases: partial batch on interrupt; hash/preview if split across invocations |

### C. Target clicks-per-second (CPS) in profile

Store `cookie_target_cps: 40` → derive `delay = 1/cps - measured_overhead` (or cap).

| Pros | Cons |
|------|------|
| Operator tunes **intent** (“~40 CPS”) not raw seconds | Still empirical; overhead varies |
| Easy to document | Same implementation as A under the hood |

### D. Post-burst / pre-cycle settle sleep

Add `post_cookie_settle_seconds` (or increase effective gap before ladder or before next cycle) so the **game finishes animating** before the next phase.

| Pros | Cons |
|------|------|
| Directly addresses “**next cycle** starts too soon” | Does **not** fix intra-burst backlog if delay stays 0 |
| Composable with A/B/C | Another magic number |

### E. Adaptive rate (game feedback)

Infer backlog from DOM/screenshot delta, audio, or timer heuristics.

| Pros | Cons |
|------|------|
| Theoretically optimal | **High complexity**, fragile, likely browser-specific; poor fit for v1 |

### F. Lower `cookie_click_count` + more cycles

Many shorter bursts with `cycle_sleep_seconds` between them.

| Pros | Cons |
|------|------|
| Spreads load in time; easier to interrupt between cycles | Changes **game semantics** (fewer clicks per “visit” to cookie); may not match operator intent |

---

## Recommended direction (phased — when implemented)

1. **Short term:** Add **profile + CLI** fields for **cookie inter-click delay** (Option A) defaulting to a small non-zero value (e.g. 5–20ms) for experimentation; keep `0` as explicit “max speed” escape hatch. Document interaction with `sleep_interruptible` and **Ctrl+C** in [`osx/README.md`](osx/README.md).

2. **Same release or follow-up:** Add optional **post-cookie settle** (Option D) before the next cycle (and optionally before ladder if order matters).

3. **If A is insufficient:** Add **chunked** cookie mode (Option B) behind a flag or profile key `cookie_burst_chunk_size` + `cookie_burst_chunk_pause_seconds`.

4. **Defer:** Adaptive (E).

---

## User breakout (explicit requirements)

| Mechanism | Notes |
|-----------|--------|
| **Ctrl+C in terminal** | Kills / interrupts the **foreground** process; with subprocess per `click_target`, signal hits the **child** `macos_mouse_click.py`. Document: **terminal must have focus** (or use `kill -INT <pid>` from another shell). |
| **Positive `-d`** | Restores periodic yielding → **faster interrupt** between clicks than `-d 0` hot loop. |
| **Chunked runs** | Stopping between child processes requires **loop script** to trap SIGINT and not start the next chunk (bash `trap` + optional **PID file** for `kill`). |
| **Non-interactive `-Y`** | No TUI confirmation; stopping is **signal-only** — document clearly. |
| **Optional watchdog** | Future: max wall-clock per cycle, or “grace period” after burst before continuing. |

---

## Files likely touched (implementation pass only)

- [`osx/macos_mouse_click_loop.sh`](osx/macos_mouse_click_loop.sh) — pass delay; optional chunking / trap.
- [`osx/config/cookie_clicker_profile.defaults.json`](osx/config/cookie_clicker_profile.defaults.json) + schema — new optional keys.
- [`osx/cookie_clicker_preview_plan.py`](osx/cookie_clicker_preview_plan.py) / manifest — if burst is split, align `targets` or document that manifest is “logical” clicks not subprocess count.
- [`osx/README.md`](osx/README.md) — operator guidance: tuning delay, settle, and how to stop.

---

## Acceptance criteria (implementation pass only)

- With default non-zero cookie delay, Cookie Clicker **does not fall multiple seconds behind** event injection on a reference machine (subjective + optional simple counter screenshot delta).
- **Ctrl+C** stops automation within **O(delay)** or **O(chunk_pause)** time (document expected bound).
- `cycle_sleep_seconds` and new **settle** knobs are documented and independent.
