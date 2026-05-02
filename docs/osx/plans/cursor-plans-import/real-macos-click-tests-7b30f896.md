<!-- 7b30f896-9430-4faf-ae44-92b593896e92 -->
---
todos:
  - id: "tier1-helpers"
    content: "Implement `_fake_qz` + recorders in `osx/tests/test_post_start_clicks.py` (or split modules)"
    status: pending
  - id: "tier1-synthetic-loop"
    content: "Unit tests for `run_synthetic_loop`: N, delays, shutdown 130, infinite until shutdown"
    status: pending
  - id: "tier1-learn-flows"
    content: "Tests for `run_learn_flow` and `run_learn_collect_flow` with monkeypatched seams"
    status: pending
  - id: "tier2-observer"
    content: "Minimal CGEventTap observer (subprocess or `multiprocessing`) + NDJSON protocol per plan doc"
    status: pending
  - id: "tier2-pytest"
    content: "One smoke test: observer + `macos_mouse_click.py` subprocess, env-gated marker + skip reason"
    status: pending
isProject: false
---
# Real macOS click validation (Plan 13 extension)

## Canonical doc

Design is written in [`docs/osx/plans/agent/plan-agent-13-post-start-click-tests.plan.md`](docs/osx/plans/agent/plan-agent-13-post-start-click-tests.plan.md) under **“Real macOS click validation (integration design)”**, with two new frontmatter todos (`real-quartz-design`, `real-quartz-harness`) and an updated mermaid diagram (unit / optional mocked `main` / **realMac** opt-in).

Index row updated in [`docs/osx/plans/agent/README.md`](docs/osx/plans/agent/README.md).

## Architecture (Tier 2)

- **SUT:** subprocess running `osx/macos_mouse_click.py` with fixed **`-x/-y -n K -d 0 -Y`** (minimal moving parts; no learn tap in this slice).
- **Observer:** separate process (or proven-safe thread) with **`CGEventTap`** on **`kCGEventLeftMouseDown`** / **`kCGEventLeftMouseUp`**, logging **`CGEventGetLocation`** + timestamps as **NDJSON** (stdout, fifo, or queue).
- **Parent pytest:** starts observer → starts clicker → reads lines until **2K** events or timeout → asserts **down/up pairs**, coordinates within **epsilon**, ordering.
- **Learn / learn_collect:** explicitly **phase 2** (tap conflict + anchor injection); not required for first real-click smoke.

## Gating and CI

- **`@pytest.mark.real_quartz`** (or equivalent) + **`RUN_REAL_QUARTZ_CLICKS=1`** so **`make -C osx test`** stays off by default.
- Document **Accessibility** requirement and **GitHub Actions** uncertainty (skip with clear message if tap creation fails).

## Tier 1 unchanged

Mocked **`post_synthetic_click` / `sleep_interruptible` / `wait_for_anchor_click`** tests remain the fast, default path per existing plan sections.
