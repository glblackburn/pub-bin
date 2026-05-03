---
id: DEF-014
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
  - ../plans/plan-014-macos-mouse-click-loop-cookie-before-ladder.md
  - ../plans/plan-015-cookie-clicker-golden-cookie-sweeper.md
isProject: false
---

### DEF-014: Golden sweeper in `macos_mouse_click_loop.sh` only runs when **`-k` > 1**; two **`CYCLE_SLEEP_SECONDS`** call sites confuse hook placement

**Terminology:** **`CYCLE_SLEEP_SECONDS`** — pause duration loaded from profile **`preview_defaults`** / **`cycle_sleep_seconds`**, used in **[`macos_mouse_click_loop.sh`](../../../osx/macos_mouse_click_loop.sh)** in **two** places. **`golden_sweeper`** — **[`osx/cookie_clicker_golden_sweeper.py`](../../../osx/cookie_clicker_golden_sweeper.py)** (plan-015). **`run_phased_cookie_bursts`** — runs **`post_ladder_cookie_burst_factor`** (**`-k`**) cookie **`click_target`** rounds with optional sleep between rounds (DEF-013). Shared defect vocabulary: **[`README.md`](README.md)**.

- **Status:** **Open** (documented; no fix landed in this change set).
- **Severity:** Medium — operators using **`-k 1`** (the default) never get a looper-triggered golden sweep; behavior contradicts the intent “run the sweeper after the cookie-phase sleep” when that sleep does not exist for **k = 1**.
- **Opened:** 2026-05-03
- **Completed:** —
- **Affects:** [`osx/macos_mouse_click_loop.sh`](../../../osx/macos_mouse_click_loop.sh) (**`golden_sweeper`**, **`run_phased_cookie_bursts`**, main **`while`** loop); operator workflows combining **`-S`** and **`-k 1`**; [plan-015](../plans/plan-015-cookie-clicker-golden-cookie-sweeper.md) (looper integration §7).

---

### Observed

From repo root (example from operator):

```text
osx/macos_mouse_click_loop.sh -P osx/config/cookie_clicker_profile.laptop_only.json -k 1 -S
```

**`-k 1`** is the default when **`-k`** is omitted (**`post_ladder_cookie_burst_factor`** defaults to **1** in the loop script). With **k = 1**, **`run_phased_cookie_bursts`** executes **one** cookie **`click_target`** and **never** enters:

```bash
if [ "${i}" -lt "${k}" ]; then
    echo "sleep between cookie phases: …" >&2
    sleep "${CYCLE_SLEEP_SECONDS}"
    "${golden_sweeper}" …
fi
```

because **`i < k`** is **`1 < 1`** → false. So **`cookie_clicker_golden_sweeper.py`** is **not** invoked for this common invocation.

The stderr line **`sleep between cookie phases: 25.0s`** only appears when **`-k` ≥ 2**; the golden sweeper was wired to the block immediately after **that** sleep, so it is tied to a branch that **`-k 1`** never takes.

---

### Root cause

1. **Conditional hook:** The sweeper runs only inside **`if [ "${i}" -lt "${k}" ]`**, which exists solely to insert a pause **between** cookie burst **i** and **i + 1**. When **k = 1**, there is no “between phases,” so the whole block (sleep + sweeper) is skipped.
2. **Two sleep sites, one duration name:** **`CYCLE_SLEEP_SECONDS`** is used for:
   - **Inner:** between cookie phases when **k > 1** (after phase **i** before phase **i + 1**).
   - **Outer:** between full **`run_once`** cycles when the loop continues (after **`cycle_max`** check).

   Both are legitimate but easy to conflate as “the” sleep; documentation and hook placement did not distinguish **inter-phase** vs **inter-cycle** pause, so automation (golden sweeper) landed on the wrong semantic anchor for **k = 1**.

---

### Expected behavior (product)

Operators expect the golden sweeper to run in normal **`-k 1`** sessions (including **`-S -k 1`** cookie-only cycles), not only when they opt into multi-phase cookie bursts (**`-k` ≥ 2**). Exact timing (immediately after the single cookie burst vs after a pause) should be documented once chosen.

---

### Suggested fix (for approval before coding)

Pick **one** primary “after cookie work” hook so **`-k 1`** and **`-k` > 1** stay consistent:

1. **Recommended:** Invoke **`"${golden_sweeper}" --capture display --dry-run --max-wall-seconds 2`** **once** at the **end** of **`run_phased_cookie_bursts`** (after the **`while`** loop that runs **k** phases), so every **`run_once`** that reaches cookie bursts runs the sweeper **regardless of k**. Remove the invocation from inside **`if [ "${i}" -lt "${k}" ]`** to avoid **two** sweeps per cycle when **k > 1** (unless product explicitly wants both “between bursts” and “after all bursts”).
2. **Alternative:** Keep the post–inter-phase-sleep sweeper for **k > 1**, and **additionally** invoke it when **k = 1** after the single **`click_target`** (e.g. duplicate a one-line call or branch on **k**). This preserves “after that sleep” for multi-**k** but adds a second code path for **k = 1** (higher maintenance burden than a single post-function call).

**Optional doc / clarity:** In **`osx/README.md`** or plan-014 / plan-015, briefly state that **`CYCLE_SLEEP_SECONDS`** drives **both** inter-phase and inter-cycle sleeps, and where automation hooks run.

**Regression check (after fix):**

- **`-k 1 -S`** (and default **`-k`**): after cookie burst(s) for that cycle, sweeper runs (stderr / **`screencapture`** side effects observable with Screen Recording enabled).
- **`-k 2`**: exactly **one** sweeper run per **`run_once`** if following recommendation (1), unless product chooses sweeps between phases as well.

---

### Resolution

— (fill in **Git** SHA and **Status** when a fix is approved and merged.)
