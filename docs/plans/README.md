# Plans

> **Active plan (2026-05-06):** [plan-020 — uber true-up](../osx/plans/plan-020-uber-true-up.md). It is the **only** plan currently accepting edits. All other plans under [`../osx/plans/`](../osx/plans/README.md) (`plan-001`..`plan-019` plus the two hand-offs and `cursor-plans-import/`) are **Frozen — superseded by plan-020** and read-only.

**macOS mouse click** — full plan index (frozen specs + the active plan-020), hand-offs, status legend, and agent routing: **[`../osx/plans/README.md`](../osx/plans/README.md)** (canonical).

**Other work** — cross-repo reference notes in this repository live under **[`../osx/plans/`](../osx/plans/README.md)** (for example [`react2shell-server-test-framework-reference.plan.md`](../osx/plans/react2shell-server-test-framework-reference.plan.md)).

## Plans in this directory

Plans filed here use their own **`plan-###-….md`** sequence, independent of the `plan-001`..`plan-021` numbering under [`../osx/plans/`](../osx/plans/README.md) (that sequence belongs to the macOS clicker product).

| Plan | Status | Summary |
| --- | --- | --- |
| [plan-001 — load-ssh-key.sh KeePassXC passphrases](plan-001-load-ssh-key-keepassxc-passphrase.md) | **Implemented** (2026-08-16) | `load-ssh-key.sh` fetches each key's passphrase from KeePassXC via `keepassxc-cli` and feeds it to `ssh-add` through an `SSH_ASKPASS` helper — one master-password prompt per run, graceful fallback to today's interactive prompt. |

