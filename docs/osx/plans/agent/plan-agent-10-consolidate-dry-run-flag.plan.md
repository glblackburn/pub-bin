<!-- Cursor agent plan 10 (canonical copy in-repo; do not use ~/.cursor/plans/). -->
---
todos:
  - id: "spec-dry-run-learn-json"
    content: "Decide learn-mode anchor policy (user click vs fake from config) and JSON emission timing for Phase 2."
    status: pending
  - id: "phase1-rename-alias"
    content: "Add `--dry-run`, wire to same logic as `--dry-run-after-start`, update README + tests + help."
    status: pending
  - id: "phase2-noop-layer"
    content: "Thread dry_run flag; no-op post_synthetic_click and related paths; adjust Quartz import gate and tests."
    status: pending
  - id: "docs-plans-align"
    content: "Align plan-003 / agent plan wording with `--dry-run` and phased semantics."
    status: pending
isProject: false
---
# Plan 10 — Consolidate dry-run into `--dry-run`

## Goal (from product direction)

- One flag: **`--dry-run`**.
- **Observability:** same (or richer) stderr/debug output as a normal run so operators can see what would happen.
- **Safety:** no synthetic clicks, no mouse moves, no injected keys (and no other UI automation side effects you add later).
- **Motivation:** once a **progress indicator** runs after the user chooses Start, dry-run must be able to **exercise that path** instead of exiting immediately after “Running” (current behavior).

## Current behavior (baseline)

In [`osx/macos_mouse_click.py`](../../../../osx/macos_mouse_click.py), `dry_run_after_start_requested()` gates `main()` so that after resolved-config debug and `emit_dry_run_json_line(cfg)`, the process **exits before `import_quartz()`**. That guarantees **no Quartz** and is relied on by [`osx/tests/test_dry_run.py`](../../../../osx/tests/test_dry_run.py) and [`osx/tests/test_mt09.py`](../../../../osx/tests/test_mt09.py) (e.g. “import_quartz must not be called”).

Side-effecting code today is concentrated around: `import_quartz`, `get_mouse_location`, `post_synthetic_click`, `wait_for_anchor_click` (event tap + pass-through of first mousedown per docstring), and `run_synthetic_loop`.

## Design tension to resolve explicitly

| Concern | Early exit (today) | Full-path dry-run (target) |
|--------|--------------------|----------------------------|
| CI / parsers | Stable `MACOS_MOUSE_CLICK_DRY_RUN_JSON` line on stderr | Still need that contract (or an agreed successor). |
| Quartz | Not loaded | Likely **must load** for realistic branches (e.g. at-cursor position, learn tap) unless you substitute AppleScript/osascript for reads only. |
| Learn anchor | Skipped entirely | Policy: either **still wait for user’s real first click** (user-driven, not synthetic) or **inject a fake anchor** from resolved config / TUI so runs are fully unattended. |

Recommendation for the plan doc: treat **“no synthetic input”** as the hard rule; **optional user-driven anchor** in learn can be a separate checkbox in spec (default for unattended CI: fake anchor from resolved `x,y` after editor).

## Phased implementation (keeps risk bounded)

**Phase 1 — Rename and compatibility**

- Add **`--dry-run`** as the primary argparse flag; keep **`--dry-run-after-start`** as a **deprecated alias** (hidden from help or documented as deprecated) for one release, or map both to the same `Namespace` attribute.
- Optionally mirror env: keep **`MACOS_MOUSE_CLICK_DRY_RUN`** or introduce **`MACOS_MOUSE_CLICK_DRY_RUN=1`** meaning the same as `--dry-run` (single source of truth in `dry_run_requested()`).
- Update help text, [`osx/README.md`](../../../../osx/README.md), and tests to prefer `--dry-run` while assertions still accept the alias if you keep it.

**Phase 2 — Full-path dry-run (enables future progress UI)**

- **Do not** exit before `import_quartz()` when `--dry-run` is set; instead pass a **`dry_run: bool`** (or equivalent) into the functions that perform automation.
- Introduce a **small boundary layer** used by all automation:
  - `post_synthetic_click`: if dry-run, log intended `(x,y)` and return.
  - `run_synthetic_loop`: unchanged control flow, but clicks become no-ops; still honor delay and SIGINT so progress/logging can be observed.
  - `get_mouse_location`: either read-only (if acceptable) or return last resolved anchor from config in dry-run (product choice).
  - `wait_for_anchor_click`: either no-op with configured coordinates, or “listen only” with **no CGEventPost** for synthetic events (verify tap behavior does not move or click on behalf of the user).
- After the run would normally finish (or after N simulated iterations in dry-run), **still emit** `MACOS_MOUSE_CLICK_DRY_RUN_JSON` once if tests need it—or emit it **once at start** and again at end (only if you explicitly want two lines; default: **one line**, same as today, at a single defined milestone to avoid breaking `dry_run_parse.parse_dry_run_json`).

**Phase 3 — Progress indicator**

- When the Rich (or other) progress UI lands **after Start**, gate any spinner/live updates on the same `dry_run` flag if needed (e.g. faster ticks, or identical UX with no Quartz posts).

## Test and CI updates

- [`osx/tests/test_dry_run.py`](../../../../osx/tests/test_dry_run.py): assert `--dry-run` triggers the same JSON contract; add subprocess test that **`import_quartz` may be called** in Phase 2 only if you change the contract—otherwise split tests into “legacy early-exit” vs “full-path dry-run”.
- [`osx/tests/test_debug_tui_logging_meta.py`](../../../../osx/tests/test_debug_tui_logging_meta.py), [`osx/tests/test_mt09.py`](../../../../osx/tests/test_mt09.py): swap argv to `--dry-run` (and keep one test on deprecated alias if retained).
- Document in plan-003 / agent plan that **MT-xx** expectations for “Quartz never imported” apply only to Phase 1 or to a dedicated **`--dry-run-snapshot`** if you split modes (only add a second flag if you reject combining JSON + full path in one flag).

## Optional: single flag vs two internal modes

If you want **both** “CI snapshot, no Quartz” **and** “full rehearsal with Quartz loaded” under one user-facing name, the cleanest UX is often:

- **`--dry-run`** = full rehearsal (Phase 2).
- **`MACOS_MOUSE_CLICK_DRY_RUN_JSON` only / no Quartz** remains env-driven for CI only, **or** you accept Quartz in CI when headless.

Only add **`--dry-run=...` / `--dry-run snapshot`** if product insists one argv covers both incompatible behaviors.

## Documentation

- Update [`docs/osx/plans/`](../) references that mention `--dry-run-after-start` or split “after editor / after start” hooks so they describe **`--dry-run`** and the phased semantics above.
- Per repo rules, store any session-specific agent plan under **`docs/osx/plans/agent/`** with prefix **`plan-agent-`** and link from this folder’s README (`plan-agent-10-consolidate-dry-run-flag.plan.md`).

## Open product choice (capture before coding)

1. In **learn** dry-run, should the script **wait for the user’s real anchor click** (still “no synthetic clicks”) or **use configured coordinates only** so CI never blocks?
2. Should **`MACOS_MOUSE_CLICK_DRY_RUN_JSON`** appear **only at exit**, **only once at start**, or **both** after Phase 2?
