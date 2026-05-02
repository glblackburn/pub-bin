---
id: DEF-013
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
  - ../plans/plan-014-macos-mouse-click-loop-cookie-before-ladder.md
isProject: false
---

### DEF-013: **`-k`** multiplies cookie clicks in one burst instead of phased rounds with sleep

**Terminology:** **Profile `cookie_click_count`** — synthetic clicks per “cookie burst” unit in JSON **`preview_defaults`** (loaded as **`COOKIE_CLICK_COUNT`** in [`macos_mouse_click_loop.sh`](../../../osx/macos_mouse_click_loop.sh)). **`CYCLE_SLEEP_SECONDS`** — seconds between **outer** loop cycles **and**, when **`-k` > 1**, between **cookie phases** inside **`run_once`**. Shared **CSI** / **PTY** vocabulary is in **[`README.md`](../README.md)**.

- **Status:** **Fixed** (loop + preview + docs + tests).
- **Severity:** Medium — **`-k`** had folded **K × `COOKIE_CLICK_COUNT`** into one **`macos_mouse_click.py -n`**; operators expect **K** profile-sized bursts with pause between phases.
- **Opened:** 2026-05-02
- **Completed:** 2026-05-02
- **Affects:** [`osx/macos_mouse_click_loop.sh`](../../../osx/macos_mouse_click_loop.sh) (**`-k`**, **`run_phased_cookie_bursts`**, **`click_target`**); [`osx/cookie_clicker_preview_plan.py`](../../../osx/cookie_clicker_preview_plan.py) (**`--post-ladder-cookie-burst-factor`** / **N** **`cookie_burst`** rows); [`osx/README.md`](../../../osx/README.md); [plan-014 v2](../plans/plan-014-macos-mouse-click-loop-cookie-before-ladder.md).

---

### Observed

With **`-k 2`** and profile **`cookie_click_count`** = 3000, the loop runs **one** cookie **`click_target`** that invokes **`macos_mouse_click.py -n 6000 -d 0 …`** — a **single** long synthetic burst.

That is not equivalent to **two** rounds of 3000 clicks separated by a pause: there is **no** sleep between “phases” inside **`run_once`**, and **`macos_mouse_click.py`** does not get a chance to return between the two nominal profile bursts.

---

### Expected behavior

When **`-k` > 1** (and the same semantics for cookie-only **`-S`**):

1. Run **K** separate cookie **`click_target`** invocations (or **K** equivalent **`macos_mouse_click.py`** runs), **each** with **`-n` = `COOKIE_CLICK_COUNT`** (one profile burst per phase), **not** **`-n` = K × `COOKIE_CLICK_COUNT`** in one call.
2. After **each** cookie phase (except possibly the last, if spec says otherwise), apply a **sleep** so operators get pause between bursts — default candidate: **`CYCLE_SLEEP_SECONDS`** from the profile (same value already used **between** outer cycles), unless a dedicated CLI or profile key is introduced.

**Preview / manifest:** Either **K** distinct **`cookie_burst`** targets (same **x/y**, sequential **id**), or one row with metadata that unambiguously encodes **K** phases — must match what the shell actually runs for **`-R`** parity.

---

### Non-goals (for scoping the fix)

- Changing **`macos_mouse_click.py`** internal pacing beyond what **`-d`** already provides, unless the loop chooses a non-zero **`-d`** between phased calls by design.

---

### Regression check (after fix)

- **`-k 2`**: two **`macos_mouse_click.py`** processes (or two **`click_target`** calls) each **`-n` 3000**, with **sleep ≥ 0** between them; not one **`-n` 6000**.
- **`-k 1`**: unchanged from today (one burst, **`COOKIE_CLICK_COUNT`**).
- **`-S -k 2`**: same phased behavior for cookie-only cycles.
- Update **`osx/tests/test_plan014_loop_cookie_burst_factor.py`** and preview tests for new manifest shape if applicable.

---

### Resolution

1. **`macos_mouse_click_loop.sh`:** **`run_phased_cookie_bursts`** loops **`post_ladder_cookie_burst_factor`** times, each **`click_target`** with **`COOKIE_CLICK_COUNT`**; **`sleep "${CYCLE_SLEEP_SECONDS}"`** between phases when **`i < k`** (stderr line before sleep).
2. **`cookie_clicker_preview_plan.py`:** **`_build_targets`** emits **N** **`cookie_burst`** targets (**`cookie_phase_1`** …), each **`click_count`** = profile unit (not **N ×**).
3. **`osx/README.md`**, **plan-014 v2**, **plan-002** / **defects README** — semantics documented; **DEF-013** closed.

**Tests:** [`osx/tests/test_plan014_loop_cookie_burst_factor.py`](../../../osx/tests/test_plan014_loop_cookie_burst_factor.py).

**Git:** — (update this line with the **`git commit`** SHA after the close-out commit lands on **`main`**).
