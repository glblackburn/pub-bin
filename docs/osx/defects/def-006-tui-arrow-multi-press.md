---
id: DEF-006
related_plans:
  - ../plans/plan-002-macos-mouse-click-terminal-ux.md
  - ../plans/agent/plan-agent-def-006-tui-arrow-keys.plan.md
---

### DEF-006: Multiple Up/Down presses per row (CSI timeout)

**Terminology:** **CSI** (*Control Sequence Introducer*) — terminal control sequences usually beginning with **`ESC` `[`** (bytes `0x1B 0x5B`), including common **arrow-key** encodings. **SS3** (historically *Single Shift 3*; **arrow** sequences in this doc) — bytes introduced by **`ESC` `O`** (`0x1B 0x4F`) instead of **`ESC` `[`**. **PTY** (*pseudo-terminal*) — a paired **kernel TTY** (master/slave) so test harnesses (**pexpect**, **pytest** subprocess) can attach a fake terminal. **PTY tests** spawn **`osx/macos_mouse_click.py`** under a PTY and assert on captured transcripts (sometimes with stderr merged into the capture).

- **Agent plan (design notes):** [`plan-agent-def-006-tui-arrow-keys.plan.md`](../plans/agent/plan-agent-def-006-tui-arrow-keys.plan.md)
- **Frontmatter todo:** `defect-def-006-tui-arrow-multi-press` (completed when fix landed).
- **Status:** Fixed in [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py) (`read_raw_key`).
- **Manual verification:** **Pending** — run **MT-01** / **MT-02** table navigation on a real TTY when convenient; automated guard: [`osx/tests/test_read_raw_key_csi.py`](../../../osx/tests/test_read_raw_key_csi.py) (`test_read_raw_key_csi_down_slow_inter_byte_gap`).
- **Severity:** Medium — row highlight does not follow **Up**/**Down** reliably; feels “stuck” until the user presses again.
- **Environment:** Reported on macOS Rich pre-run table (`run_rich_pre_run_editor`); worst when the TTY delivers **CSI** bytes slowly (Bluetooth, remote desktop, or scheduling gaps).

**Observed**

- On the **main settings** table, **several** **Up** or **Down** presses are sometimes needed to move the highlight by **one** row.

**Root cause**

1. After **`ESC` `[`**, `read_raw_key` read each following byte with **`wait_char(0.25)`**. If the final **`A`** / **`B`** (arrow) arrived **more than 250 ms** after the previous CSI byte, the loop **timed out**, returned **`other`** (no row move), and left **orphan** bytes for the next read — again **`other`**. Distinct from **DEF-002** (post-**ESC** wait before **`[`**) and **DEF-003** (cancel / wheel policy).

**Resolution**

1. Read the **CSI** tail after **`[`** under a **single ~1 s budget** (`time.monotonic()` deadline), each `select` capped at **0.5 s**, so a **300 ms** gap before **`B`** still completes **`ESC [ B`** as **Down**.
2. Apply the same **deadline** pattern for **SS3** **`ESC O A` / `ESC O B`** (final byte after **`O`**).
3. **Git:** `7cfec5161c20ee36db2fe5f95b2ebe8cc92bfd3c` (script + tests commit; plan row updated in a follow-up docs commit per project workflow).
4. **Files:** [`osx/macos_mouse_click.py`](../../../osx/macos_mouse_click.py), [`osx/tests/test_read_raw_key_csi.py`](../../../osx/tests/test_read_raw_key_csi.py)

**Regression check**

- **pytest** (macOS): `pytest osx/tests/test_read_raw_key_csi.py -c osx/pytest.ini -v`
- **MT-01** / **MT-02**: **Up**/**Down** moves exactly **one** row per key on the main table under normal typing.
