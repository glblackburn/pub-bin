## April 18, 2026

**LinkedIn draft:** opens on **practicing a small build with an AI agent**, then **planning for functional outcomes** plus **automated tests as guardrails**, **Cookie Clicker as a bounded target**, **human vs agent split**, and **maintainable docs** (glossary, narrative, screenshots). Revision **8** drops numbered-plan framing (plain text in `2026-04-18-macos-mouse-click-plans-session.txt`).

**Status:** ⏳ Publication pending — LinkedIn URL will be added after posting

**Plain text (posting source):** [`2026-04-18-macos-mouse-click-plans-session.txt`](2026-04-18-macos-mouse-click-plans-session.txt)

**Repo:** [pub-bin / docs/osx](https://github.com/glblackburn/pub-bin/tree/main/docs/osx)

---

## Draft mirror (from `.txt`)

The indented block below is regenerated from the plain-text draft (four leading spaces per line) so this file stays a readable GitHub copy that matches the `.txt` byte-for-byte when you strip the prefix.

    I wanted to practice building something small with an AI coding agent beside me.
    
    I picked a narrow macOS utility with concrete behavior: easy to describe, easy to break in small ways. The work I cared about was planning that steers good functional outcomes (what should change, what must hold, what done looks like) and an automated test suite that keeps every change honest. Those two are the guardrails; the rest is execution.
    
    Cookie Clicker became the automation target because it is small and bounded. One browser tab and a repetitive loop are enough to stress the tool while keeping the whole problem visible.
    
    A tiny script sends the clicks there.
    
    The shift that mattered was where the time went. Reasoning about behavior and walking failures in the suite stayed with me. The agent was best on the long tail in the repo: many documents, cross-links, and turning "we should update that" into finished prose instead of a branch that only lives in my head.
    
    What that looked like in practice:
    
    ▶ One shared glossary so recurring vocabulary is defined once and reused across the doc tree.
    ▶ A chronological development narrative alongside the specs, so phases and decisions stay traceable as the repo grows.
    ▶ Session screenshots checked in with readable names, so visual evidence sits beside the story instead of dying on a desktop.
    
    The lesson is bigger than any single file. Good functional outcomes need more than clever code. They need clear intent, tests that do not rot, and documentation people will maintain so history and purpose stay aligned with what ships.
    
    https://github.com/glblackburn/pub-bin/tree/main/docs/osx
    https://github.com/glblackburn/pub-bin/blob/main/docs/osx/plans/DEVELOPMENT_NARRATIVE.md
    https://github.com/glblackburn/pub-bin/blob/main/osx/macos_mouse_click.py
    
    Web tab: https://orteil.dashnet.org/cookieclicker/
    
    #Python #macOS #OpenSource #Automation #DeveloperExperience #Planning #AI #Documentation


---

## Revision notes

- **Current `.txt`:** revision **8** below; bullets in this section that mention `-Y` / Ctrl+C describe **earlier** drafts only.
- **Eighth revision (2026-04):** replace **numbered-plans / roadmap** framing with **planning that steers functional outcomes** and **automated tests** as the accountability loop; **split human work** (behavior, failing tests) from **agent work** (long doc edits); bullet **"next to the plans"** → **"alongside the specs"**; lesson closes on **intent + tests + maintainable docs**. Cookie sentence later drops **“platform rewrite”** phrasing for a plainer close (**stress the tool / whole problem visible**). ~2.0k characters (under 3k).
- **Seventh revision (2026-04):** **bigger-picture** pass for LinkedIn: lead with **human vs agent division of labor**, **plans and roadmap as the spine**, **Cookie as bounded practice surface**; **strip low-level terminal jargon** (no **CSI/SS3/PTY** name-check); bullets speak to **glossary / narrative / screenshots** in plain language; lesson stresses **maintainable docs** and **tax on updates**, not file names. ~1973 characters (under 3k).
- **Sixth revision (2026-04):** refocus on **AI agents for planning/design** over rote implementation; **documentation at scale** (central **`TERMINOLOGY.md`** + index, **`DEVELOPMENT_NARRATIVE.md`**, **`docs/osx/screenshots/`** sequence **01–09**); emphasize **cross-referencing** and **design history in sync** with code/tests; add narrative + script links; hashtags add **`#AI`** / **`#Documentation`**; ~2274 characters (under 3k). **Copy tweak:** opener is **“I wanted to practice building something small with an AI coding agent beside me.”** (no **“end-to-end”**); then plans → Cookie as bounded target → script. Dropped the mid-sentence **em-dash aside** on the macOS utility; **replaced long em-dash chains** with short sentences, a colon, or parentheses so the scan is not one long dash rhythm. **Links:** Cookie target is the **web tab** only (`https://orteil.dashnet.org/cookieclicker/`); dropped **`cookieclicker.com`**.
- **Fifth revision (2026-04):** align with repo after **`docs/osx/`** consolidation — GitHub tree link **`docs/osx`** (was **`docs/plans`**); replace stale **`docs/plans/README​.md`** bullet with merged index under **`docs/osx/plans/README​.md`**; add shipped **`--learn-points`** bullet; add fourth roadmap bullet unchanged; **𝐓𝐡𝐞 𝐥𝐞𝐬𝐬𝐨𝐧** gains one short **pytest** clause (~55 tests under **`osx/tests`**); character count still well under 3k.
- **Fourth revision:** scene-first open (Cookie as bounded target); split “needle” ideas into short paragraphs; outcome-shaped bullets (less plan-number jargon); **𝐓𝐡𝐞 𝐥𝐞𝐬𝐬𝐨𝐧** instead of “punchline”; drop parenthetical link aside; add **script** URL next to the **`docs/plans`** tree link (that tree link was later superseded by **`docs/osx`** in rev 5).
- First draft read like a sprint demo (abstract bullets, no hook). Rewrote after re-reading published posts: lead with the `-Y` / Ctrl+C footgun, fake `rich` on `PYTHONPATH`, then `docs/plans/` work.
- Second revision: Cookie Clicker confessional + “back into AI-assisted dev” framing, official and web URLs, shortened link labels for LinkedIn character cap.
- **Third revision:** adopt perspective **1. Scaffolding, not software**—the script as a small focus object; main story is developing and revising plan docs and a feature roadmap, clearing easy fixes per pass and deferring heavier items to numbered follow-ons with real thinking time.
- Earlier “direction check” options are preserved below for reference.

---

## Five possible perspectives (reference)

**Current posting draft follows #1.**

### 1. Scaffolding, not software

The story is getting back into **AI-assisted work**—short loops, a concrete goal, and a toy problem that is allowed to be silly—not Quartz or Cookie Clicker as engineering subjects. The script is evidence you could **sustain attention** on something small again. Technical detail stays minimal or absent; the arc is “I was rusty → I needed a dumb focus object → this was the dumb object.”

### 2. Confession comedy

Lean into Cookie Clicker and the clicker script as **one joke with two layers**: the game that exists to waste time, and the engineer who wastes time *automating* the waste of time. Self-deprecating, not a roadmap. You might still name the repo or stack in passing, but you **do not** sell plan docs, `-Y`, or defect matrices—they read as the wrong genre.

### 3. Honest craft on a tiny surface

A **narrow engineering vignette**: one file, one OS API, one UX problem (for example, “clicking from Python on macOS is easy until it isn’t”). Cookie Clicker is optional color or omitted. The audience is people who like **small tools done carefully**, not “here is my program management system.”

### 4. Tool-maker meets tool-user

You are both author and operator. The story is **using your own automation**—surprises, fear (“I can’t stop this”), boredom, or delight—and what that implies for how you design CLIs and safety rails. Plans and matrices appear only if they serve **that** story (for example, “I scared myself once, so I wrote it down”), not as the main payload.

### 5. Lines in the sand

A calmer angle: **when it is fine to script clicks**, where terms of service and etiquette matter, how you think about load on a site, single-player versus competitive contexts, and macOS accessibility prompts. Cookie Clicker is a **low-stakes** boundary-case example. Keep it personal and specific so it does not read as preaching.
