# Plan 010 — Learn-point collect (`--learn-points`)

**Status:** Shipped (v1). **Agent engineering notes:** [`agent/plan-agent-12-learn-points-collect.plan.md`](agent/plan-agent-12-learn-points-collect.plan.md).

## Summary

Operators can record **many** anchor positions in one session without rerunning learn or scraping logs. Mode **`--learn-points`** is mutually exclusive with **`--learn`**, **`-x/-y`**, and **`--at-cursor`**.

## Behavior

1. **Rich path** (TTY, Rich, no **`-Y`**): After the usual pre-run table and **`S`**, the UI shows a log region under the settings table. Each **real left mousedown** (same Accessibility rules as learn) appends one colored line (rotating styles). **`Q`** / **`Ctrl+C`** / **`Ctrl+D`** exit with zero or more samples; no synthetics.
2. **Plain text (`-Y`)**: One line per capture: `index x y` with four decimal places on coordinates (see `learn_collect_plain_text_line` in `osx/macos_mouse_click.py`).
3. **Optional cap:** `--learn-points` or `--learn-points N` with **`N >= 1`** stops after **N** captures; omit **`N`** for infinite until user exit.
4. **Dry-run / CI:** `--dry-run-after-start` or **`MACOS_MOUSE_CLICK_DRY_RUN=1`** with **`--learn-points -Y`** prints deterministic fake coordinate lines on stdout and exits **0** without **`import_quartz()`**.

## Exit codes

Aligned with existing cancel vs interrupt behavior (see plan-002): cancel paths vs **`Ctrl+C`** during collect return **130** where applicable.

## References

- Implementation: `osx/macos_mouse_click.py` (`run_learn_collect_flow`, `emit_learn_collect_dry_run_stdout_samples`, argparse **`--learn-points`**).
- Tests: `osx/tests/test_dry_run.py` (dry-run stdout / JSON), `osx/tests/test_open_defects.py` (DEF-007 duplicate flag).
