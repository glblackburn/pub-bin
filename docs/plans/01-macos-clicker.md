---
todos:
  - id: add-macos-mouse-click-py
    content: "Add osx/macos_mouse_click.py: modes, CGEventTap + synthetic loop, signals, --interactive/--yes + confirm"
    status: pending
  - id: deps-doc
    content: "Document pip, Accessibility, Ctrl+C, interactive prompts, confirmation sheet, --help examples"
    status: pending
  - id: sanity-check
    content: "Tests: --yes learn; --interactive partial CLI; confirm path; Ctrl+C; SIGTERM"
    status: pending
isProject: false
---

# Plan 01: macOS clicker utility

## Design decision: implementation language (v1)

**Use Python 3** for the first shipped version: a single script under `osx/` that drives **Quartz** mouse events through **PyObjC** (`CGEvent` create + post for left button down/up). Same underlying macOS mechanism as Swift; tradeoff is a **pip-installed** dependency (`pyobjc-framework-Quartz`) in exchange for fast iteration and readable code.

**Future:** the same CLI semantics can be reimplemented in **Swift**, **Rust**, or a **bash + cliclick** wrapper in this repo if you want a zero-runtime or single-binary variant later. Keep flag names and behavior aligned across language versions when you add them.

---

## Terminal-facing script name

| Candidate | Verdict |
|-----------|---------|
| `macos_mouse_click.py` | **Chosen for v1.** Self-documenting in `ls` and in shell history; leaves no doubt the tool is macOS-specific. |
| `mclick.py` | Shorter for daily typing; keep as a possible future symlink or thin wrapper if you want both. |
| `clicker.py` | Clear but generic; easy to confuse with unrelated “clicker” tools. |

**Path:** `osx/macos_mouse_click.py`

**How users run it (document in script docstring / `--help`):**

```bash
python3 osx/macos_mouse_click.py --help
# Learn mode: confirmation sheet (Proceed?) then wait for first real click; Ctrl+C stops repeats
python3 osx/macos_mouse_click.py --learn
# Skip prompts and confirmation (automation / scripts)
python3 osx/macos_mouse_click.py --learn -Y
# Prompt for anything omitted on the CLI, then confirmation sheet
python3 osx/macos_mouse_click.py --interactive
# Fixed coordinates, finite count, non-interactive
python3 osx/macos_mouse_click.py -x 400 -y 300 -n 3 -Y
```

The script is executable (`chmod +x osx/macos_mouse_click.py`) with shebang `#!/usr/bin/env python3`, so **`./osx/macos_mouse_click.py …`** also works. Use **`python3 …`** when the file is not marked executable.

---

## Language / runtime options (reference and roadmap)

All options require **Accessibility** for the process that runs the tool (Terminal, iTerm, Cursor’s terminal, etc.). **Listen-then-click** (learn mode) also needs a **CGEventTap** while listening; same permission bucket. **Screen Recording** is not required for v1.

| Language / stack | Typical approach | Tradeoff | Roadmap |
|------------------|------------------|----------|---------|
| **Python** + PyObjC | `Quartz` / `CGEvent` + event tap | Needs `pip` + PyObjC; Python runtime | **v1 (this plan)** |
| **Swift** | `CGEvent` CLI, `swiftc` | No pip; needs Xcode CLT | Future alternate |
| **Objective-C / C** | Same Quartz APIs via `clang` | More boilerplate | Future / unlikely |
| **Rust** | `enigo` or `core-graphics` | Static binary; `cargo` for build | Future alternate |
| **Go** | CGEvent via cgo-style libs | Build fragility on macOS | Future if needed |
| **Node.js** | Native addons or shell out to tools | High friction | Unlikely |
| **AppleScript / JXA** | `System Events` | Brittle; coordinate quirks | Future one-off only |
| **Bash** | Wrapper around **`cliclick`** | No compile; depends on Homebrew binary | Future thin wrapper |

---

## Goal (v1)

Ship **`osx/macos_mouse_click.py`** that can:

1. **Learn mode:** Wait for the user’s **first physical left click** (real hardware click), record its **global Quartz coordinates**, then emit **synthetic left clicks** at that point **repeatedly** until the user stops the program cleanly.
2. **Fixed mode:** When **`-x` and `-y`** are given, emit synthetic clicks at that point (finite count or repeat-until-abort per flags below).
3. **Optional “current cursor snapshot” mode** (no `-x/-y`, no `--learn`): read mouse location **once** at start and click there (scripting convenience); document as secondary to learn mode.

Requirements across modes:

- **Delay between synthetic clicks:** **`-d` / `--delay` seconds, default `5.0`** so the user can switch apps, reach for the trackpad, or hit **Ctrl+C** in the terminal between automated clicks.
- **Clean abort:** cooperative shutdown (see below) so the process exits predictably and does not leave a stuck mouse-down.
- **Interactive configuration** and **pre-flight confirmation** (see next major section): optional stdin prompts for missing flags; **`--yes`** to skip both prompts and confirmation for scripting; without **`--yes`**, always show a **resolved-parameter summary** and require confirmation before any event tap or synthetic clicking begins.
- Clear **`--help`**, stderr errors, nonzero exit on misuse.

---

## Operating modes (behavior matrix)

| Mode | How target point is chosen | Repeat behavior |
|------|------------------------------|-----------------|
| **Learn** (`--learn`; **required flag** for v1 so a bare `python3 …/macos_mouse_click.py` does not silently arm an event tap) | Install a **temporary `CGEventTap`**; on the **first `kCGEventLeftMouseDown`**, read **`CGEventGetLocation`**, then **remove/disable the tap immediately** inside the callback so **synthetic** clicks are never mistaken for the anchor click | After a **warmup** sleep (see below), loop: synthetic click → sleep **`delay`** → repeat until **abort** or **`-n` cap** |
| **Fixed** (`-x` and `-y`) | Use the given coordinates | Loop **`-n`** times (`-n` default **`1`**). **`-n 0`** means **infinite** until abort (optional but useful for “spam this button”). Between each pair of synthetics, sleep **`delay`** (no sleep after the final click when `-n` is finite and > 0) |
| **Snapshot cursor** (optional; e.g. `--at-cursor` if learn is not the default) | Read current mouse location once, no tap | Same as fixed with regard to `-n` / `-d` |

**Targeting mode resolution (v1):** Exactly one of **`--learn`**, **fixed `-x` and `-y`**, or **`--at-cursor`** must be selected—either **on the CLI** or **during `--interactive` prompts** (see below). If after parsing + optional interactive fill-in the mode is still unset, print **usage** and exit nonzero. **`--yes`** requires a **fully specified mode on the CLI`** (no stdin); if mode is still missing with **`--yes`**, exit with a clear error.

**Warmup after learn:** After the tap captures the anchor point and before the **first** synthetic click, **`time.sleep(delay)`** once (reuse **`-d`** default **5**). Rationale: user can move the cursor away, focus the terminal, or prepare to press **Ctrl+C** before automation starts.

**Synthetic click atomicity:** Post **mouse down** then **mouse up** back-to-back; only **between** completed clicks insert **`time.sleep(delay)`** and check **shutdown flag** so abort never splits a click.

---

## Clean abort: how the user stops the app

Primary mechanism (must implement and document prominently in docstring and **`--help`**):

1. **Ctrl+C in the terminal** → **SIGINT**. Install a **`signal.signal(signal.SIGINT, …)`** handler that sets a module-level **`shutdown_requested = True`** (or similar). The main loop checks this flag **after each full synthetic click** and **before each `time.sleep(delay)`** (or use short sleeps in chunks if you want sub-second reaction while keeping long delay—optional v2). Also use **`try` / `except KeyboardInterrupt`** around `main()` as a backstop.
2. **SIGTERM** (e.g. `kill <pid>` from another terminal, or stopping the process from Activity Monitor “Quit”) → same handler via **`signal.signal(signal.SIGTERM, …)`** where practical so shutdown is symmetric.

On shutdown path:

- Print a short line to **stderr** (e.g. `Stopped.`) so the user knows the exit was intentional.
- Exit **`130`** if you want conventional “interrupted by SIGINT” semantics, or **`0`** if you treat user stop as success—**pick one and document**.

**Do not** rely on a second physical click to stop (that would fight the learn semantics). Optional future: **`--listen-quit`** with a second tap sequence is out of scope for v1.

**Safety valve (recommended in plan):** **`--max-clicks`** (or cap `-n`) so a typo does not create an infinite storm if the user forgets Ctrl+C—optional; if omitted, **`-n 0` + learn** still means infinite until signal.

---

## Interactive prompts and pre-flight confirmation

Three layers; implement in this order after initial **`argparse`** parse.

### 1. `--interactive` (optional)

- When present: for every **configurable parameter** that was **not** set on the CLI (mode, `-x/-y` when mode is fixed, `-n`, `-d`, etc.), **prompt on stdin** with a clear label and the **effective default** shown (e.g. `Delay between synthetic clicks in seconds [5.0]: `). Empty input accepts the default.
- **stdin must be a TTY** when `--interactive` is used; otherwise print an error to stderr and exit nonzero (avoid blocking on EOF in pipes).
- **Mutually exclusive with `--yes`:** if both are passed, exit with a clear error (scripting vs interactive are opposite intents).

### 2. Defaults for anything still unset

- After CLI and optional **`--interactive`** pass, apply **documented defaults** for any remaining optional fields (e.g. **`delay=5.0`**, mode-specific **`count`** defaults).

### 3. Confirmation sheet unless `--yes`

- If **`--yes`** / **`-Y`** is **not** passed: print a **human-readable summary** of **every** resolved parameter (mode, coordinates if any, count, delay, and any other options), each with its **source**: **`cli`**, **`default`**, or **`prompt`** (if **`--interactive`** supplied that value).
- Then print **`Proceed? [y/N]`** (default **N**). Only if the user enters a clear affirmative (**`y`**, **`yes`**, case-insensitive per your preference—document the exact accepted tokens) continue to **event tap / synthetic** execution. Anything else → exit **`0`** without performing clicks (treat as “cancelled,” not an error), or exit **`1`** if you prefer “cancelled” distinct from success—**pick one and document**.
- If **`--yes`** is passed: **skip** the confirmation sheet entirely and proceed immediately after validation (still print a **one-line stderr summary** of mode + anchor strategy optional but useful for logs).

**Summary table**

| Flags | stdin prompts for missing args? | Confirmation sheet before clicks? |
|-------|----------------------------------|-------------------------------------|
| *(neither)* | No | **Yes** — list all resolved values + sources, then **Proceed?** |
| `--interactive` | **Yes** (TTY required) | **Yes** (unless you later add `--yes`—with both forbidden) |
| `-Y` / `--yes` | No | **No** — run immediately; all required targeting must come from CLI |

**Scripting contract:** **`--learn -Y`** / **`--learn --yes`** (or fixed coords + **`-Y`/`--yes`**) is the supported non-interactive entry point for automation. Short form is **`-Y`** (not **`-y`**, which is the Y coordinate).

---

## CLI (argparse) — revised

| Flag | Meaning |
|------|---------|
| `-h` / `--help` | Help and exit 0 |
| `--learn` | Wait for first **real** left click (event tap), then repeat synthetics at that point until abort or `-n` cap |
| `-x` / `--x`, `-y` / `--y` | Fixed coordinates (both required together) |
| `-n` / `--count` | Number of **synthetic** clicks after anchor is known: default **`1`** in fixed/snapshot modes; **`0` = infinite** until abort. In **learn** mode, **`0` (default)** = infinite until abort; **`N > 0`** = stop after **N** synthetics |
| `-d` / `--delay` | Seconds **between synthetic clicks** (and **warmup** after learn = one interval of **`delay`** before first synthetic). **Default: `5.0`** |
| `--at-cursor` | One-shot or repeat from current position without tap—optional |
| `--interactive` | Prompt on stdin for any option **not** given on CLI; TTY required; **incompatible with `--yes`** |
| `-Y` / `--yes` | Non-interactive: no missing-arg prompts, **no** confirmation sheet; **requires** targeting mode (and coordinates if fixed) **fully on CLI** |

**Validation:** exactly one targeting mode after resolution; reject invalid combos with stderr + exit **2**. **`--yes`** without a resolved mode (or fixed coords incomplete) → stderr + exit **2**.

---

## Click and tap implementation notes

1. **Learn:** `CGEventTapCreate` listening at **`kCGHIDEventTap`** (or session tap per Quartz docs) for **`kCGEventLeftMouseDown`**. In callback: copy location, **invalidate/disable tap**, store `CGPoint`, return event unchanged (so the user’s real click still reaches the OS—do not swallow unless you intentionally `None` the event; document behavior: usually **pass through** so their click also “lands” on the UI).
2. **Warmup:** `sleep(delay)`.
3. **Synthetic loop:** for each iteration until shutdown or count exhausted: post down+up at anchor; if another iteration pending, check shutdown; if not aborted, `sleep(delay)`.
4. **Posting synthetics:** same as before: **`CGEventPost`** with **`kCGHIDEventTap`**, left button down/up at stored `CGPoint`.

---

### Runtime and dependencies

- **Python:** 3.9+; document minimum in file header.
- **Install:**

  ```bash
  python3 -m pip install pyobjc-framework-Quartz
  ```

- **Imports:** `argparse`, `sys`, `time`, `signal`, **`Quartz`** (PyObjC).

### Structure and style

- **Single module:** `osx/macos_mouse_click.py`.
- **`main()`** parses args → optional **`run_interactive_prompts()`** → apply defaults → unless **`--yes`**, **`confirm_resolved_config()`** → dispatch mode, install handlers, run loop.
- **Quality:** no trailing whitespace; newline at EOF; no secrets / no network.

### macOS permissions (user-facing copy)

- **Accessibility** for the app running `python3 osx/macos_mouse_click.py`.
- **Screen Recording:** not required for v1.

### Coordinates and Retina

Global Quartz **points**; multi-monitor quirks documented briefly in docstring.

---

## Files to add (v1)

- **`osx/macos_mouse_click.py`**
- Optional: commit **`docs/plans/01-macos-clicker.md`** with the script.

---

## Implementation order

1. Docstring + **`argparse`** (all flags including **`--interactive`**, **`--yes`**; defaults: **`delay=5.0`**, mode-specific **`count`**).
2. **`--interactive`** prompts (TTY check) + **`--yes`** / mutual exclusion + **confirmation sheet** (sources: cli / default / prompt).
3. **Signal handlers** + main loop **shutdown checks**.
4. **Learn tap** + **warmup** + **synthetic loop**; then **fixed/snapshot** paths.
5. Manual tests: **`--learn -Y`**; partial CLI + confirm **N**; **`--interactive`** fill + confirm **Y**; **`-Y`/`--yes`** + missing mode → error.
6. Git per **`README-AI-CODING-STANDARDS.md`**.

---

## Out of scope (v1)

- Right-click, drag, modifiers, UI element queries
- Avoiding Accessibility
- stdin “press q to quit” (optional future if stdin is a tty)
- Swallowing vs forwarding the anchor click (document chosen behavior; no extra modes)

---

## Consistency review: `osx/macos_mouse_click.py` vs this plan

Captured review comparing the implemented script to this document.

### Aligned with the plan

| Plan area | Script behavior |
|-----------|------------------|
| Single file `osx/macos_mouse_click.py` | Yes |
| Python 3 + `pyobjc-framework-Quartz`, install hint | Yes (Quartz imported only when running, after confirm / validation) |
| Modes: `--learn`, fixed `-x`/`-y`, `--at-cursor` | Yes; mutually exclusive + validation |
| `CGEventTapCreate` at `kCGHIDEventTap`, first `kCGEventLeftMouseDown`, disable tap in callback, return event (pass-through) | Yes |
| Synthetic: `CGEventCreateMouseEvent` + `CGEventPost` HID tap, down then up | Yes |
| Default `-d` **5.0**; used for inter-click delay and learn warmup | Yes (`sleep_interruptible` for warmup and delays; still honors shutdown) |
| `-n`: **0** = infinite; default **0** learn, **1** fixed / at-cursor | Yes |
| Loop: full click, then sleep between; no sleep after last finite click | Yes |
| SIGINT + SIGTERM → flag; checks around loop + interruptible sleep; `KeyboardInterrupt` → 130 | Yes |
| stderr `Stopped.` on cooperative stop; exit **130** on interrupt-style paths | Yes |
| `--interactive`: TTY check; prompts mode, x/y (fixed), count, delay when missing | Yes |
| `--yes` incompatible with `--interactive` | Yes |
| `--yes` requires targeting mode fully on CLI | Yes (`mode_fully_on_cli`) |
| Without `--yes`: summary + sources + `Proceed? [y/N]`; `y`/`yes`; cancel **exit 0** | Yes (plan allowed exit 0 for cancel) |
| With `--yes`: one-line stderr summary, no confirmation | Yes |
| Accessibility error when tap is `None` | Yes |

### Intentional deviation (plan doc updated above)

1. **`--yes` short form**  
   The plan CLI table previously said **`--yes` / `-y`**, but **`-y` is already Y coordinate** in the same table. The script correctly uses **`-Y` / `--yes`** and explains that in the docstring and epilog.  
   **Verdict:** implementation is right; the **plan text was corrected** to use **`-Y`** for the short “yes” flag.

2. **Examples in the plan**  
   Examples now use **`./osx/…` and `-Y`** where appropriate alongside `python3 …`.  
   **Verdict:** cosmetic doc alignment; behavior matches **`--yes`** or **`-Y`**.

### Optional / minor gaps (plan allowed or underspecified)

| Item | Notes |
|------|--------|
| **`--max-clicks` safety valve** | Plan calls it optional (“recommended”); **not implemented** — consistent with “optional v1”. |
| **Confirmation sheet “every” option** | Plan mentions “any other options”; sheet lists **mode, x/y (fixed), count, delay** only — not `--interactive` / `-Y`. Small omission. |
| **“Print usage” when mode missing** | Plan suggests usage or `--help` hint; script prints a **short error** instead of `parser.print_usage()`. Same intent, slightly different UX. |
| **Plan frontmatter todos** | Still **pending** while the script exists — tracking only, not a script/plan logic mismatch. |

### Summary

**Behaviorally**, the script matches the plan: modes, Quartz usage, defaults, learn warmup, infinite `count`, signals, interactive flow, confirmation, and **`-Y`/`--yes`** semantics (with **`-y` reserved** for the Y coordinate).

**Documentation:** this plan’s CLI table and examples now use **`-Y`/`--yes`** consistently with **`osx/macos_mouse_click.py`**.
