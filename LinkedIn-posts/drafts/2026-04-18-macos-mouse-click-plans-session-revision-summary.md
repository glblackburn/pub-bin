# Revision summary: `2026-04-18-macos-mouse-click-plans-session.txt`

Companion to the LinkedIn plain-text draft in **`2026-04-18-macos-mouse-click-plans-session.txt`**. Built from **`git log --follow`** on that path; each row is a **committed** snapshot. **Narrative delta** is what changed versus the **previous** row.

**Note:** Draft notes in **`2026-04-18-macos-mouse-click-plans-session.md`** describe a **seventh** and **eighth** wording pass; both land in commit **`48ac33e`** relative to **`b416aaa`** because only one commit updated the `.txt` after the em-dash cleanup.

| Ver | Commit | One-line summary | Narrative delta (vs previous) |
|-----|--------|------------------|--------------------------------|
| **1** | `4c9d3c7` | **Footgun / honesty** — long `--learn -Y`, terminal not frontmost, weak `Ctrl+C`; code works, “done” does not; teases plan **08** stop-during-run. | *Baseline.* Incident-led, **CLI-heavy**; Cookie **not** the hook. |
| **2** | `d18b68d` | **Cookie + “back into AI”** — confessional opener, rediscovery, **both** Cookie URLs; then “yes, the script is real” and the **same** footgun block. | **Personal + game hook**; **links**; still **second half = technical fear** / roadmap. |
| **3** | `e8e40be` | **“Small scope, on purpose” / scaffolding** — Cookie named as click target; **center of gravity = plan docs + roadmap** (easy wins vs numbered follow-ons). | **Genre change:** **plans/roadmap practice** replaces **sprint-style footgun** opener; Cookie as **bounded workload**, not joke or hazard lead. |
| **4** | `65adb80` | **Cookie as deliberate small target** — prestige line; **end-to-end** practice; needle = **plans + roadmap**; outcome bullets + lesson (narrow utility + plans / parking lot). | **Tighter bounded metaphor**; **outcome-shaped repo bullets** (Rich v1 closure, index, roadmap); **lesson** about **settling back** via plans. |
| **5** | `0fa46bf` | **Opener unchanged from v4**; **bullets + lesson + links** align with tree move: **`docs/osx/`**, merged index, **`--learn-points`**, **pytest**; `docs/plans` link retired. | **Evidence refresh only:** shipped work + **tests** named + **canonical doc path**; story spine **unchanged**. |
| **6** | `f5d47e4` | **Agent-led doc story** — opener = **practice with an AI agent**; plans drive **simple app** (utility aside); Cookie = **automation target**; **you vs agent** on doc churn; bullets = **terminology (CSI named)**, narrative doc, screenshots; extra `DEVELOPMENT_NARRATIVE` URL. | **New through-line:** **planning/design vs implementation grunt** + **living docs**; **deeper repo internals** in bullets; **some terminal jargon** for insiders. |
| **7** | `b416aaa` | **Same story, cleaner surface** — drops mid-sentence **utility aside**; breaks Cookie and lesson into **shorter sentences**; **parens/colon** instead of **em-dash chains**; mirror + notes updated. | **Rhythm / punctuation only**; **CSI/SS3/PTY bullet still present**; meaning **unchanged** from v6. |
| **8** | `48ac33e` | **Outcomes + tests + plain docs** — **planning for functional outcomes** + **automated suite as guardrails**; **you** on behavior + failing tests, **agent** on long doc edits; bullets **jargon-free**; Cookie line **without “platform rewrite”**; lesson = **intent + tests + docs that ship**. | **Re-center thesis:** **functional outcomes + automated tests**, not **numbered-plan mechanics**; **strip CSI-style detail**; **human vs agent** explicit; **lesson** elevated above any single file. |

To regenerate this table from git later:

```bash
git log --oneline --follow -- LinkedIn-posts/drafts/2026-04-18-macos-mouse-click-plans-session.txt
```
