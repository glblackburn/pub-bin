# Terminology

Central glossary for **`docs/osx/`** (plans, defects, hand-offs, hub). Other markdown files often repeat the **CSI / SS3 / PTY** block at the top; this page collects **additional** acronyms and tokens used across the clicker documentation.

**Terminology (quick):** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).

## Index of terms

| Token | Topic |
|-------|--------|
| [ANSI](#term-ansi) | Terminal escape / formatting bytes (informal umbrella) |
| [API](#term-api) | Application Programming Interface (library or OS surface) |
| [ASCII](#term-ascii) | 7-bit character set |
| [CGEvent](#term-cgevent) | Quartz API type for synthetic mouse events |
| [CGEventTap](#term-cgeventtap) | Quartz tap for observing input events (tests) |
| [CI](#term-ci) | Continuous Integration |
| [CLI](#term-cli) | Command-Line Interface |
| [CSI](#term-csi) | Control Sequence Introducer (`ESC [` …) |
| [DEF-*nnn*](#term-def) | Defect identifier (`def-###-….md`, **DEF-*nnn*** in tables) |
| [EOF](#term-eof) | End Of File on a stream |
| [JSON](#term-json) | JavaScript Object Notation |
| [MT-*nn*](#term-mt) | Manual test matrix row (**MT-01** … **MT-09** in plan **02**) |
| [NDJSON](#term-ndjson) | Newline-delimited JSON (one JSON object per line) |
| [plan-*nnn*](#term-plan) | Numbered product plan file prefix |
| [plan-agent-* (historical)](#term-plan-agent) | Old clicker session-note prefix — **merged into plan-###** |
| [pty / PTY](#term-pty) | Pseudo-terminal |
| [PyObjC](#term-pyobjc) | Python bridge to Objective-C / Apple frameworks |
| [pytest](#term-pytest) | Python test runner used under **`osx/tests/`** |
| [pexpect](#term-pexpect) | Python library for expect-style PTY driving |
| [Quartz](#term-quartz) | macOS graphics / event subsystem (Core Graphics) |
| [SHA](#term-sha) | Git object id (**commit SHA**, often 40 hex chars) |
| [SIGINT](#term-sigint) | Interrupt signal (**Ctrl+C** default) |
| [SIGTERM](#term-sigterm) | Termination signal (`kill` default) |
| [SIGWINCH](#term-sigwinch) | Window size changed (terminal resize) |
| [SGR](#term-sgr) | Select Graphic Rendition (CSI color/style) |
| [SS3](#term-ss3) | SS3-style `ESC O` … sequences (see SS3 section) |
| [SUT](#term-sut) | System Under Test (the program the test observes) |
| [TTY](#term-tty) | Teletypewriter — Unix terminal interface |
| [TUI](#term-tui) | Text User Interface (here: Rich pre-run table) |
| [UTF-8](#term-utf-8) | Unicode byte encoding |
| [YAML](#term-yaml) | YAML Ain’t Markup Language (plan frontmatter) |

<a id="term-csi"></a>
## CSI — Control Sequence Introducer

**CSI** sequences are a large family of **terminal control** bytes. In 7-bit ASCII they usually **start with `ESC` `[`** (bytes **`0x1B`** **`0x5B`**). Many **arrow keys**, **colors** (**SGR**), cursor moves, and **mouse reporting** modes use CSI.

Examples (simplified): **Up** / **Down** arrows are often **`ESC` `[` `A`** / **`ESC` `[` `B`**, sometimes with extra numeric parameters between **`[`** and the final letter.

<a id="term-ss3"></a>
## SS3 — Single Shift 3 (terminal arrow encoding)

**SS3** historically referred to a **7-bit shift** in **ECMA-35** / **ISO 2022**. In **terminal documentation** for this repo, **“SS3-style”** means **arrow** (and some **function key**) sequences that use the **`ESC` `O`** prefix (**`0x1B`** **`0x4F`**) instead of **`ESC` `[`**.

Examples: **Up** / **Down** may appear as **`ESC` `O` `A`** / **`ESC` `O` `B`** when the terminal is in **application cursor key** style modes.

<a id="term-pty"></a>
## PTY — pseudo-terminal; PTY tests

A **PTY** (**pseudo-terminal**) is a **kernel-provided pair** of character devices (**master** and **slave**) that behave like a **real TTY** to the child process. Parents (**pexpect**, **pytest** subprocess helpers) attach to the **master** and read/write what the child sees on its **controlling terminal**.

**PTY tests** (in **`osx/tests/`**) **spawn `osx/macos_mouse_click.py`** (or helpers) **under a PTY**, inject keys or resize events, and **assert on stdout/stderr transcripts**—often together with **`MACOS_MOUSE_CLICK_DEBUG_TUI`** logging.

<a id="term-tty"></a>
## TTY

**TTY** (*teletypewriter*) is the traditional Unix name for a **terminal session**: a character device with **line discipline**, **window size** (**`LINES`** / **`COLUMNS`**), and **raw** vs **cooked** modes. Docs contrast **“real TTY”** operator sessions with **PTY**-driven automation.

<a id="term-tui"></a>
## TUI

**TUI** (*text user interface*) means an operator-facing **full-terminal** UI here—primarily the **Rich** pre-run **table** / **panels** in **`osx/macos_mouse_click.py`**, as opposed to one-line **stderr** messages or plain **`-Y`** text output.

<a id="term-sgr"></a>
## SGR

**SGR** (*Select Graphic Rendition*) is the **CSI** subfamily that sets **colors**, **bold**, **underline**, etc. Rich and tests strip **SGR** / **CSI** when comparing **“logical”** screen text (e.g. **`def009_layout_heuristics`**).

<a id="term-ndjson"></a>
## NDJSON

**NDJSON** (*newline-delimited JSON*) is a **log format**: each line is one **JSON** object. **`MACOS_MOUSE_CLICK_DEBUG_TUI`** / **`MACOS_MOUSE_CLICK_DEBUG_TUI_LOG`** emit **NDJSON** lines for TUI state and **`after_key`** events.

<a id="term-json"></a>
## JSON

**JSON** (*JavaScript Object Notation*) — structured text for logs, **`MACOS_MOUSE_CLICK_DRY_RUN_JSON`**, and metadata fields in defects/plans.

<a id="term-def"></a>
## DEF-*nnn* (defect ids)

**DEF-*nnn*** labels a **defect** tracked in **[`defects/`](defects/README.md)** (`def-###-….md`) and summarized in **plan-002**’s defect table. **`nnn`** is zero-padded (**DEF-006**, not **DEF-6**).

<a id="term-mt"></a>
## MT-*nn* (manual test rows)

**MT-*nn*** rows (**MT-01** … **MT-09**) are **manual verification** scenarios in **[`plan-002-macos-mouse-click-terminal-ux.md`](plans/plan-002-macos-mouse-click-terminal-ux.md)**. Some have **pytest** or **PTY** automation; others remain **operator-only**.

<a id="term-plan"></a>
## plan-*nnn*

**`plan-###-….md`** files are **numbered product specs** (e.g. **plan-001** core behavior, **plan-002** terminal UX). **`###`** is zero-padded.

<a id="term-plan-agent"></a>
## plan-agent-*

**Historical:** **`plan-agent-….plan.md`** was the filename prefix for **mouse-clicker** Cursor session notes **formerly** under **`docs/osx/plans/agent/`**. That directory was **removed**; material now lives in merge sections under **[`plan-002`](plans/plan-002-macos-mouse-click-terminal-ux.md#operator-loop-cookie-clicker-and-preview-pipeline-merged-context)**, **[`plan-003`](plans/plan-003-macos-mouse-click-tui-automation.md#additional-automation-backlog-session-notes-merge)**, and **[`plan-009`](plans/plan-009-macos-mouse-click-tui-arrow-navigation-narrative.md#appendix-merged-engineering-notes-formerly-split-agent-plans)**. **Non–mouse-clicker** reference plans in this repository live under **[`plans/`](plans/README.md)** (for example **`react2shell-server-test-framework-reference.plan.md`**); the old **`docs/plans/agent/`** directory was **removed**.

<a id="term-cli"></a>
## CLI

**CLI** (*command-line interface*) — flags and positional args to **`osx/macos_mouse_click.py`** (`argparse`), as documented in **`--help`** and the plans.

<a id="term-ci"></a>
## CI

**CI** (*continuous integration*) — automated **pytest** (and related) runs on push/PR; **macOS**-only tests are **skipped** or **marked** on non-darwin hosts per **`osx/pytest.ini`**.

<a id="term-sigint"></a>
## SIGINT

**SIGINT** — the usual signal for **Ctrl+C**. Plan **01** / **02** document cooperative shutdown with **`shutdown_requested`** and exit code **130** where applicable.

<a id="term-sigterm"></a>
## SIGTERM

**SIGTERM** — polite process termination (`kill` default). Handled alongside **SIGINT** for symmetric shutdown in plan **01**.

<a id="term-sigwinch"></a>
## SIGWINCH

**SIGWINCH** — **window changed** signal when a **TTY** is resized. **plan-006** tracks **Rich** reflow / **DEF-005**; the script may not install a **SIGWINCH** handler yet—docs call that out explicitly.

<a id="term-quartz"></a>
## Quartz

**Quartz** — Apple’s **2D graphics / event** layer used here via **`CGEvent`** to post **synthetic mouse** events (**Accessibility** still required).

<a id="term-cgevent"></a>
## CGEvent

**CGEvent** — Core Graphics **event object** (mouse down/up, etc.) created and posted in **`osx/macos_mouse_click.py`**.

<a id="term-cgeventtap"></a>
## CGEventTap

**CGEventTap** — low-level **event tap** API; mentioned in advanced **test** backlog (**[plan-003](plans/plan-003-macos-mouse-click-tui-automation.md#additional-automation-backlog-session-notes-merge)** — post-start observer idea) for observing clicks, **gated** so CI does not require it.

<a id="term-pyobjc"></a>
## PyObjC

**PyObjC** — Python bindings to **Objective-C** frameworks; this repo uses **`pyobjc-framework-Quartz`** for **Quartz** calls.

<a id="term-pytest"></a>
## pytest

**pytest** — the **Python** test runner configured by **`osx/pytest.ini`**; discovers **`osx/tests/test_*.py`**.

<a id="term-pexpect"></a>
## pexpect

**pexpect** — third-party **Python** library used in **PTY tests** to **spawn** the script, **send** bytes, and **match** output patterns.

<a id="term-sha"></a>
## SHA (commit id)

**SHA** in tables usually means the full **Git commit object name** (**40 hex digits** from `git rev-parse HEAD`) recorded as **`Fix commit`** for traceability.

<a id="term-yaml"></a>
## YAML

**YAML** — the **frontmatter** block at the top of some **`.md`** files (`---` … `---`) for **todo** metadata; not all plans use it.

<a id="term-utf-8"></a>
## UTF-8

**UTF-8** — Unicode **encoding** for log files, **NDJSON**, and operator-visible strings (mode names, etc.).

<a id="term-ascii"></a>
## ASCII

**ASCII** — 7-bit **US-ASCII**; terminal bytes and **escape** prefixes are often discussed as **raw bytes** in defects (**CSI** / **SS3**).

<a id="term-ansi"></a>
## ANSI (informal)

**ANSI** (informal) — in this repo, “**ANSI escapes**” usually means **CSI** / **SGR** / cursor controls emitted by **Rich** or the terminal, not a specific standards body section.

<a id="term-api"></a>
## API

**API** — **library** or **OS** surface area (e.g. **Rich** `Console` API, **pexpect** resize **`setwinsize`**, **Quartz** functions).

<a id="term-sut"></a>
## SUT

**SUT** (*system under test*) — the **process** or **module** under automation (often **`macos_mouse_click.py`** as a subprocess).

<a id="term-eof"></a>
## EOF

**EOF** (*end of file*) — reading **stdin** returns **no data** (e.g. piped input closed); plan **01** guards **`--interactive`** when **stdin** is not a **TTY**.

## Why it matters for `read_raw_key`

**CSI** and **SS3** arrow sequences are **several bytes long** and can arrive **split across `read()` calls** with **gaps** between bytes. A reader that **times out per byte** or treats **`ESC`** alone as **Escape** can mis-classify input (**DEF-002**, **DEF-003**, **DEF-006**, **DEF-008** classes in the plan/defect docs).
