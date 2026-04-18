## April 18, 2026

**LinkedIn draft:** post opens on **Small scope, on purpose.** (scaffolding & plans session; plain text in `2026-04-18-macos-mouse-click-plans-session.txt`).

**Status:** ⏳ Publication pending — LinkedIn URL will be added after posting

**Plain text (posting source):** [`2026-04-18-macos-mouse-click-plans-session.txt`](2026-04-18-macos-mouse-click-plans-session.txt)

**Repo:** [pub-bin / docs/plans](https://github.com/glblackburn/pub-bin/tree/main/docs/plans)

---

## Draft mirror (from `.txt`)

The indented block below is regenerated from the plain-text draft (four leading spaces per line) so this file stays a readable GitHub copy that matches the `.txt` byte-for-byte when you strip the prefix.

    Small scope, on purpose.
    
    I’ve been iterating on a small macOS script to send mouse clicks to Cookie Clicker. For me, this has been scaffolding. I kept the scope narrow on purpose. I wanted something I could hold in my head end to end. That was the shape of practice I needed while I got back into AI-assisted development mode. I’ve been away from that rhythm for a while and needed a concrete, bounded workload to rehearse on. (Links at the end: the main site and the web tab I point the script at.)
    
    The work that actually moved the needle was developing and revising plan documents and a roadmap of features. Each time I touched a plan, I tried to clear the easy wins first: missing rows or bullets, status labels that were out of date, defects where the fix was obvious. Anything that needed more revision or quiet thinking time went to a numbered follow-on and a line on the roadmap as plan or feature items—mostly future change I did not want to drop—so the idea would not get lost.
    
    𝐖𝐡𝐚𝐭 𝐭𝐡𝐚𝐭 𝐥𝐨𝐨𝐤𝐞𝐝 𝐥𝐢𝐤𝐞 𝐢𝐧 𝐭𝐡𝐞 𝐫𝐞𝐩𝐨:  
    
    ▶ Closed plan 02 for v1 once the Rich table UX and manual test rows matched what we had actually run, with “defer” items pointing at specific next plans instead of endless open loops.  
    ▶ Added `docs/plans/README​.md` to separate plan 01 (behavior spec, “Shipped” as reference) from plan 02 (TTY UX program, “Closed (v1)” as a delivery I can set aside until a later revision).  
    ▶ Left longer-horizon automation work sketched (for example a pytest path for a fake-Rich harness) while being explicit about what still needs a human at the keyboard.  
    
    𝐓𝐡𝐞 𝐩𝐮𝐧𝐜𝐡𝐥𝐢𝐧𝐞:  
    
    The automation stays a narrow utility. The plans and roadmap are what helped me settle back into small slices, honest status, and a place to park bigger changes where they stay visible—captured as work to do later, not as something I have to carry in my head.
    
    https://github.com/glblackburn/pub-bin/tree/main/docs/plans  
    
    All OS builds: https://cookieclicker.com/  
    Web tab: https://orteil.dashnet.org/cookieclicker/  
    
    #Python #macOS #OpenSource #Automation #DeveloperExperience #Planning


---

## Revision notes

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
