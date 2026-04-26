---
todos:
  - id: phase1-in-band-abort
    content: "Phase 1: macos_mouse_click.py — mouse-move and/or CGEventTap panic → shutdown_requested; flags; tests or checklist"
    status: completed
  - id: phase1-docs-operator-stop
    content: "Phase 1: README — in-band abort, Input Monitoring / Accessibility, Escape limits, Ctrl+C when terminal focused"
    status: completed
  - id: phase2-profile-delay-keys
    content: "Phase 2: profile/schema — cookie_click_delay_seconds, post_cookie_settle_seconds, optional chunk keys"
    status: pending
  - id: phase2-loop-wire-delay
    content: "Phase 2: macos_mouse_click_loop.sh — wire -d from profile (cookie path); optional chunking / SIGINT trap"
    status: pending
  - id: phase2-docs-delay-tuning
    content: "Phase 2: README — empirical delay tuning, kill from second shell, effective CPS logging if implemented"
    status: pending
  - id: phase2-optional-chunking
    content: "Phase 2 (if needed): chunked cookie burst + bash trap between chunks"
    status: pending
---

# Cookie burst rate control and user breakout

## Table of contents

- [Scope (read this first)](#scope-read-this-first)
- [Implementation phases (split)](#implementation-phases-split)
- [Current behavior (baseline)](#current-behavior-baseline)
- [Design goal](#design-goal)
- [Phase 1 — In-band abort: mouse movement and Escape (feasibility)](#phase-1-in-band-abort-mouse-movement-and-escape-feasibility)
- [Phase 2 — Finding optimal inter-click delay](#phase-2-finding-optimal-inter-click-delay)
- [Options (pros / cons) — mostly Phase 2](#options-pros-cons-mostly-phase-2)
- [Recommended direction (when implemented)](#recommended-direction-when-implemented)
- [User breakout (explicit requirements)](#user-breakout-explicit-requirements)
- [Files likely touched (implementation pass only)](#files-likely-touched-implementation-pass-only)
- [Acceptance criteria (implementation pass only)](#acceptance-criteria-implementation-pass-only)

## Scope (read this first)

- **This document is planning and design only.** It does not require or imply code changes until a separate, explicit implementation request (e.g. “execute this plan” or a scoped PR).
- Sections **“Files likely touched”** and **“Acceptance criteria”** describe a **future implementation pass**, not current repo obligations.
- The YAML **todos** above are a **backlog checklist** for that future pass; they are not in-progress implementation work while this plan remains in design-only mode.

---

## Implementation phases (split)

Work is intentionally **two phases**. Ship **Phase 1 before** turning on aggressive paced bursts in production: once `-d` > 0 and bursts are long, **terminal Ctrl+C alone is unreliable**; in-band abort closes the “must SSH to kill” hole.

| Phase | Theme | Primary outcome |
|-------|--------|-------------------|
| **Phase 1** | **In-band abort** | Operator can stop synthetic clicking from the **game-focused** session (mouse-move threshold; optional Escape / hotkey via `CGEventTap`) without terminal focus or remote shell. |
| **Phase 2** | **Optimal inter-click delay** | Profile + looper expose pacing (`-d`, settle, optional chunking); README documents **how to choose** delay and optional CPS logging—not a single “optimal” constant. |

**Dependency:** Phase 2 (pacing defaults) should assume Phase 1 abort exists, or keep `-d 0` until Phase 1 lands.

---

## Current behavior (baseline)

In [`osx/macos_mouse_click_loop.sh`](osx/macos_mouse_click_loop.sh), `click_target` always runs:

```bash
"${mouse_click}" -d 0 -x "${target_x}" -y "${target_y}" -n "${target_n}" -Y
```

So **every synthetic click is immediate** (no `sleep_interruptible` between clicks when delay is 0; see [`run_synthetic_loop`](osx/macos_mouse_click.py) and [`sleep_interruptible`](osx/macos_mouse_click.py): `seconds <= 0` returns immediately).

[`preview_defaults`](osx/config/cookie_clicker_profile.defaults.json) / profile supplies `cookie_click_count` (e.g. 3000) and `cycle_sleep_seconds` (e.g. 30). The **30s sleep runs only after the entire `run_once`** (ladder + cookie burst), so it **does not throttle** delivery during the 3000-click burst. That matches “next cycle starts before the previous run is processed” if the game is still draining a backlog when the next cycle begins.

**Interrupt path today:** `macos_mouse_click.py` checks `shutdown_requested()` each loop iteration and uses interruptible sleeps **only when delay > 0**. With `-d 0`, the inner loop is a tight loop (two `CGEventPost` calls per click); **SIGINT can still stop the process**, but there is **less natural yielding** than with a positive delay, so stopping can feel less responsive under load.

---

## Design goal

Balance three forces:

1. **UI throughput:** do not enqueue clicks faster than the browser/game can apply them.
2. **Operator escape:** stop automation **without** requiring the terminal to have focus or SSH from another machine. **Ctrl+C in the terminal is not sufficient** once pacing delays lengthen the burst and the operator returns focus to the game: the mouse is over the browser, the synthetic stream keeps running, and the user may be unable to refocus the shell to deliver SIGINT. Remote `kill` works but is a last resort if another session is unavailable.
3. **Throughput / session length:** avoid making a 3000-click “session” unnecessarily long.

No single constant works across hardware, browser, and game state; the plan favors **Phase 1 in-band abort** first, then **Phase 2 configurable pacing** (delay, settle, optional chunks). See **Implementation phases** above.

---

## Phase 1 — In-band abort: mouse movement and Escape (feasibility)

**Goal:** While `macos_mouse_click.py` is posting synthetic clicks (especially with positive `-d`), the process also watches for **explicit user intent to stop** that does not depend on terminal focus.

**DEF-010 (fixed):** Mouse-move abort now uses **arm radius + distance from click target**; see **[DEF-010](../../defects/def-010-mouse-move-abort-wrong-reference.md)**.

### Is it possible on macOS?

**Yes, with constraints.** Common patterns:

| Approach | Idea | Pros | Cons |
|----------|------|------|------|
| **Mouse position polling** | Between clicks (inside existing `sleep_interruptible` / delay path), read global cursor with `CGEventCreate` + `CGEventGetLocation` (or equivalent). If the cursor moved more than **epsilon pixels** from a stored **reference point** (e.g. position at burst start, or last “stable” position) and the movement is **not** explained by the script repositioning the cursor (today the script may not move the OS cursor at all for pure `CGEventPost` clicks—verify on target OS), treat as **user panic abort** and exit cleanly. | No separate process; works even when game has focus; does not steal keys from the game long-term | **False positives** if the game or OS moves the cursor; **false negatives** if the user uses only the keyboard; epsilon and debouncing need tuning; must not confuse rapid small jitter with intent |
| **CGEventTap (keyDown / flagsChanged)** | Install a **listen-only** or **head-insert** event tap for `kCGEventKeyDown` and detect **Escape** (keycode 53) or a configurable **“panic combo”** (e.g. Ctrl+Shift+Pause). Set the same `shutdown_requested` flag used for SIGINT. | True “hotkey” stop; works from any focus if tap receives the event | **Injection point and tap type** determine whether events reach the game after the tap; **listen-only** taps may not see events **consumed** by the focused app before the tap. **HID/session taps** and **accessibility permissions** (Privacy & Security) are required on modern macOS; user must approve once. Risk of **conflict** with other global utilities. |
| **Dedicated panic monitor subprocess** | Small helper that only registers a tap and signals the clicker via **socket / pipe / file** when Escape or mouse gesture fires. | Isolates tap lifecycle from click posting; easier to reason about shutdown | Two processes to deploy; still needs permissions; IPC complexity |
| **Hardware / driver level** | Not proposed | | Out of scope |

**Practical recommendation for a first implementation pass:**

1. **Mouse polling abort** (default-on when `-d` > 0 or behind `--abort-on-mouse-move`): cheap, no tap permissions in many configurations (location read may still need **Input Monitoring** on some macOS versions—verify current Apple policy for `CGEventCreate` from non-GUI agents). Document clearly.
2. **Escape / hotkey via `CGEventTap`** as optional `--panic-key` / `--panic-mouse-move` flags, off by default until permissions UX is documented.

**Interaction with synthetic clicks:** Clicks are posted at fixed `(x, y)`; they typically **do not** move the user’s logical cursor the way a physical device does, so **“user moved mouse away from cookie”** remains a usable heuristic for “get me out.” If a future mode moves the cursor, subtract that from the heuristic.

**Cookie Clicker / browser note:** Escape may be bound in-game (menus). If the game consumes Escape before a listen-only tap sees it, **mouse-move abort** remains the reliable path; **tap placement** (earlier in the pipeline) may be required for key-based abort—engineering trade-off with system policy.

---

## Phase 2 — Finding optimal inter-click delay

There is **no portable closed-form** for “optimal” delay: it depends on CPU, browser, tab throttling, game phase, and vsync. Treat delay as a **tunable parameter** with a repeatable **calibration procedure**.

### Practical methods (in order of engineering cost)

| Method | Procedure | Pros | Cons |
|--------|-----------|------|------|
| **Stair-step / binary search (operator)** | Start conservative (e.g. 20–30ms between clicks). Run a short burst (`-n 200`). Decrease delay until the **cookie counter or UI visibly lags** or animations stutter; increase ~20% for safety margin. Record in profile. | Simple; no code beyond exposing `-d` / profile | Subjective; session-dependent |
| **Bound by display budget** | Rough cap: delay not much below **1 / refresh_rate** (e.g. ≥8ms for 120Hz) if the goal is “one chance per frame” for the browser to paint—still not exact because JS runs on its own scheduler | Gives a **floor** order-of-magnitude | Browser may batch work; not a true optimum |
| **Wall-clock vs click count** | For fixed `n`, measure total burst duration `T`; effective CPS = `n/T`. Adjust delay until effective CPS matches a **target UI comfort** band | Reproducible numbers in logs | Does not measure **game-internal** queue depth |
| **Screenshot / OCR delta (later)** | Compare cookie count text across spaced screenshots | Objective | Heavy; fragile; deferred (see adaptive rate in main options) |
| **Automatic closed-loop (defer)** | Adaptive controller adjusts delay when lag detected | Best long-term | High complexity; not v1 |

**Default policy suggestion:** ship a **conservative default** (e.g. 10–15ms) in profile when pacing is enabled, document the stair-step procedure in `osx/README.md`, and log **effective CPS** per burst so operators can compare runs.

---

## Options (pros / cons) — mostly Phase 2

The lettered options below address **pacing and backlog** (Phase 2). Phase 1 is orthogonal: abort works even when `-d` is still `0`.

### A. Per-click delay (`-d` > 0) from profile or CLI

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

## Recommended direction (when implemented)

### Phase 1 first

1. **Mouse-move abort** in [`osx/macos_mouse_click.py`](osx/macos_mouse_click.py): poll global cursor between iterations (especially in `sleep_interruptible` gaps); compare to reference + epsilon; call existing shutdown path. Flags: e.g. `--abort-on-mouse-move`, `--mouse-move-threshold-px`.
2. **Optional:** `CGEventTap` for Escape / configurable panic combo; document permissions and “game ate Escape” behavior.
3. **README (Phase 1):** Input Monitoring / Accessibility, recommended “nudge mouse to stop,” and how this combines with SIGINT / second-shell `kill`.

Validate Phase 1 with **`-d 0`** bursts so operator escape does not depend on pacing being merged yet.

### Phase 2 after Phase 1 (or with `-d 0` only until Phase 1 ships)

1. **Option A:** Profile + looper — `cookie_click_delay_seconds` → pass `-d` on cookie (and optionally ladder) path; `0` = max-speed escape hatch.
2. **Option D:** `post_cookie_settle_seconds` (or equivalent) before next cycle / phase as needed.
3. **Option B (if needed):** Chunked bursts + bash `trap` between chunks.
4. **README (Phase 2):** Stair-step / binary search for delay, display-budget floor, optional effective-CPS logging.
5. **Defer:** Adaptive (Option E).

---

## User breakout (explicit requirements)

| Mechanism | Notes |
|-----------|--------|
| **Ctrl+C in terminal** | Still supported when the **terminal is focused**; signal hits the child `macos_mouse_click.py`. **Insufficient alone** when the operator is interacting with the game during a long paced burst—see **in-band abort** above. |
| **`kill -INT` / `kill -TERM` from another local shell** | Does not require terminal focus on the clicker tty; still requires **a second session** (Terminal tab, ssh, Screen Sharing). |
| **Mouse-move abort (planned)** | Poll global cursor between clicks; exit cleanly when movement exceeds threshold (configurable). **Primary game-focused escape** when pacing is on. |
| **Escape / panic hotkey via event tap (planned)** | Optional; depends on tap type and OS permissions; may compete with in-game bindings. |
| **Positive `-d`** | Improves SIGINT **between** clicks vs `-d 0` hot loop; does not fix focus problem by itself. |
| **Chunked runs** | Stopping between child processes requires **loop script** to trap SIGINT and not start the next chunk (bash `trap` + optional **PID file** for `kill`). |
| **Non-interactive `-Y`** | No TUI confirmation; stopping is **signal or in-band abort** — document clearly. |
| **Optional watchdog** | Future: max wall-clock per cycle, or “grace period” after burst before continuing. |

---

## Files likely touched (implementation pass only)

**Phase 1**

- [`osx/macos_mouse_click.py`](osx/macos_mouse_click.py) — mouse polling and/or `CGEventTap` panic path tied to `shutdown_requested`; CLI flags.
- [`osx/README.md`](osx/README.md) — in-band stop, permissions, Escape caveats, SIGINT / `kill` summary.

**Phase 2**

- [`osx/macos_mouse_click.py`](osx/macos_mouse_click.py) — optional logging of effective CPS if implemented here rather than in shell.
- [`osx/macos_mouse_click_loop.sh`](osx/macos_mouse_click_loop.sh) — pass `-d` from profile; optional chunking / `trap`; forward panic flags from profile if desired.
- [`osx/config/cookie_clicker_profile.defaults.json`](osx/config/cookie_clicker_profile.defaults.json) + schema — delay / settle / chunk keys.
- [`osx/cookie_clicker_preview_plan.py`](osx/cookie_clicker_preview_plan.py) / manifest — if burst is split, align `targets` or document logical vs subprocess counts.
- [`osx/README.md`](osx/README.md) — empirical delay tuning, settle knobs, chunking behavior.

---

## Acceptance criteria (implementation pass only)

**Phase 1**

- With game window focused, operator stops a running synthetic burst via **mouse-move abort** within **O(delay)** when `-d` > 0. When `-d` is 0, the implementation must still **check mouse position on every click iteration** (or at worst every *N* clicks with an explicit bound documented) so escape time stays bounded without SSH.
- Optional Escape / hotkey path: documented permissions and known failure when the game consumes the key.
- No reliance on SSH to regain control for the documented default configuration.

**Phase 2**

- With configured non-zero cookie delay, Cookie Clicker does not fall **multiple seconds** behind event injection on a reference setup (subjective and/or simple counter check).
- **Ctrl+C** (terminal focused) and **second-shell `kill -INT`** remain documented; work together with Phase 1.
- README documents **how to pick delay** (stair-step / binary search, optional refresh-rate floor, optional effective CPS in logs).
- `cycle_sleep_seconds` and **settle** knobs are documented and independent of per-click delay.
