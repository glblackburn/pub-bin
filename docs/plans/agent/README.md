# Agent session plans (`docs/plans/agent/`)


**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).

Cursor (and similar) **session plans** for work that is **not** scoped to the macOS clicker belong **in this repository** under `docs/plans/agent/`, not under `~/.cursor/plans/`.

**Mouse-clicker** session plans (DEF-006 / PTY / Rich table navigation, etc.) live under **[`docs/osx/plans/agent/`](../../osx/plans/agent/README.md)** with the **`plan-agent-`** filename prefix.

## Naming

- Use **ASCII kebab-case** only: `lowercase-words-separated-by-hyphens.plan.md`.
- **No spaces** and no shell-problematic characters (`$`, `` ` ``, `|`, `*`, `?`, `&`, etc.) in file or directory names.

## Contents here

| File | Summary |
|------|---------|
| [react2shell-server-test-framework-reference.plan.md](react2shell-server-test-framework-reference.plan.md) | External **react2shell-server** test/Make layout reference (`file://` paths). |

Numbered product plans **01–10** (`plan-001`…`plan-010`) and clicker agent plans: **[`docs/osx/plans/`](../../osx/plans/README.md)**.
