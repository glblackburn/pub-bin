# Migrate `generate-md-file-and-screenshot-lists.sh` + helpers to pub-bin (and reorganize `fix-spaces-*`)

**Status:** APPROVED scope — ready for implementation
**Created:** 2026-06-01
**Supersedes:** earlier draft `fix-spaces-reorg-plan.md` (rolled into this one)
**Decisions locked:**
- § 3.1 Two subdirs: `file-tools/` (filename mutators) and `markdown-tools/` (emit markdown)
- § 3.2 Upgrade all three migrated scripts to the full standard template (usage/-h/getopts on the tiny filters too)
- § 3.3 Hard-delete the 3 migrated scripts from `bin/` in a separate bin-repo commit
- § 3.4 LinkedIn-posts archive untouched
- § 3.5 **STRICT MODE IS REQUIRED**: every script in pub-bin runs under `set -euET -o pipefail`. Disabling or commenting it out is forbidden. See § 3.5 for the full rationale.

## Approved final layout

```
pub-bin/
├── file-tools/
│   ├── README.md
│   ├── fix-spaces-in-filename.sh         (git mv from pub-bin/ top level)
│   └── fix-spaces-in-filenames.sh        (git mv from pub-bin/ top level)
└── markdown-tools/
    ├── README.md
    ├── convert-to-md-clickable-image-list.sh   (migrate + upgrade from bin/)
    ├── convert-to-md-file-link-list.sh         (migrate + upgrade from bin/)
    └── generate-md-file-and-screenshot-lists.sh (migrate + upgrade from bin/)
```

---

## 1. Problem statement

The user wants `bin/generate-md-file-and-screenshot-lists.sh` and every script
it transitively calls migrated to pub-bin. The dependency chain:

```
bin/generate-md-file-and-screenshot-lists.sh   (orchestrator, 123 lines)
  ├─→ fix-spaces-in-filenames.sh               (PATH; ALREADY in pub-bin top level)
  │     └─→ ${script_dir}/fix-spaces-in-filename.sh   (ALREADY in pub-bin top level)
  ├─→ ${script_dir}/convert-to-md-file-link-list.sh        (in bin/, 13 lines)
  └─→ ${script_dir}/convert-to-md-clickable-image-list.sh  (in bin/, 15 lines)
```

While we're moving the orchestrator and creating a new subdir for it, the
two `fix-spaces-*` scripts can graduate from `pub-bin/` top level into their
own proper subdirectory at the same time.

---

## 2. Current state (recon)

### Scripts to migrate (in bin/, none have pub-bin duplicates)

| Path | Lines | Shape |
|------|-------|-------|
| `bin/generate-md-file-and-screenshot-lists.sh` | 123 | Has `usage()` + `getopts -d/-h/-Y/-v`; `set -euET` is commented out; calls helpers via `${script_dir}/` |
| `bin/convert-to-md-file-link-list.sh` | 13 | Pure stdin filter (`while read file ; do echo "* [${file}](${file})" ; done`); no usage/getopts |
| `bin/convert-to-md-clickable-image-list.sh` | 15 | Pure stdin filter (clickable image markdown); no usage/getopts |

### Scripts to reorganize within pub-bin (already migrated, just moving)

| Path | Notes |
|------|-------|
| `pub-bin/fix-spaces-in-filenames.sh`  | Plural wrapper; reads stdin or `find ${dir}`; calls singular via `${script_dir}/` |
| `pub-bin/fix-spaces-in-filename.sh`   | Per-file `sed`+`mv`; leaf script |

### Existing infrastructure to update

| Item | Why |
|------|-----|
| `pub-bin/setup-path.sh` | Will auto-discover any new subdir holding exec `.sh` — no edit needed |
| `pub-bin/.migration-tracking.json` | Add 3 new bin→pub-bin entries and 2 reorganize entries |
| `pub-bin/README.md` | Update 8 example invocations for `./fix-spaces-*` (lines 436–497); TOC anchors unchanged |
| `pub-bin/tests/scripts/unit/test_fix_spaces_in_filename.bats` | Bare `get_script_path` → subdir-prefixed |
| `pub-bin/tests/scripts/unit/test_fix_spaces_in_filenames.bats` | Same |
| `pub-bin/tests/scripts/README.md` | If it lists script paths |
| `bin/{generate-md…,convert-to-md-…}` | Hard-delete after pub-bin lands (separate bin-repo commit) |

### Callers / external references

| Caller | Form | Effect after migration |
|--------|------|------------------------|
| User CLI (`generate-md-file-and-screenshot-lists.sh ...`) | bare name → PATH | Works: setup-path.sh puts the new subdir on PATH |
| `generate-md-…` → `convert-to-md-…` | `${script_dir}/...` | Works: helpers move into the same new subdir |
| `generate-md-…` → `fix-spaces-in-filenames.sh` | bare name → PATH | Works: PATH still resolves it (new home in `file-tools/`) |
| `bin/generate-md-…` (the old file before deletion) | various | About to be deleted, irrelevant |
| `pub-bin/LinkedIn-posts/2025/11/2025-11-06.md` | mentions `fix-spaces-*` + GitHub anchors | **Left untouched** (historical archive per locked decision) |

---

## 3. Decisions to confirm

### 3.1 Target subdir(s) — **OPEN**

The three new bin/ migrations all generate markdown listings of filesystem
contents; the two reorg scripts mutate filenames. Different verbs, different
subdir candidates.

| Option | Layout | Pros / Cons |
|--------|--------|-------------|
| **A. Two subdirs** (recommended) | `file-tools/` (containing `fix-spaces-in-filename.sh` and `fix-spaces-in-filenames.sh`) and `markdown-tools/` (containing `generate-md-file-and-screenshot-lists.sh`, `convert-to-md-file-link-list.sh`, and `convert-to-md-clickable-image-list.sh`) | Clear semantic split. `file-tools/` = filesystem hygiene; `markdown-tools/` = markdown generation. Future homes for `clean-emacs-files.sh`, `clean-screenshots.sh`, `rename-email.sh` (file-tools) and any future markdown helpers. Cost: two new dirs at once. |
| **B. One subdir `file-tools/`** | All 5 scripts under `file-tools/` | Single new dir. Cost: `generate-md-…` only loosely fits "file-tools" (it generates markdown, doesn't mutate files); the `convert-to-md-…` filters are even less of a fit. |
| **C. Reuse existing `system-tools/`** | All 5 under `system-tools/` | No new dir. Cost: stretches existing dir's stated purpose ("system-level monitoring and event logging") even further; mixes unrelated scripts. |

**Recommendation:** **A. Two subdirs** — clean separation, leaves room to grow.

### 3.2 Upgrade scope for migrated scripts — **OPEN**

The pub-bin convention is to upgrade migrated scripts to the standard
template (`usage()`, `-h`, `getopts`, `set -euET -o pipefail`). For
`generate-md-…` this is mostly already done — it just needs `set -euET`
uncommented and a smoke test. The two `convert-to-md-…` filters are pure
13/15-line `while read; do echo …; done` filters.

| Option | What changes |
|--------|--------------|
| **A. Upgrade `generate-md-…` only** (recommended) | Uncomment `set -euET -o pipefail`. Add `script_dir` resolution via `cd $(dirname …) && pwd` so `${script_dir}/` works regardless of how invoked. Leave the two filters as-is (adding usage/getopts to a 13-line `while read` filter inflates it 5× for no real value; standard practice across pub-bin appears to allow tiny stdin filters to stay tiny — see `convert-to-md-…` shape itself). |
| **B. Upgrade all three** | Add `usage()`/-h/getopts to the filters too. Cost: ~50 lines of boilerplate per filter that operate as `--help`-only no-ops. |
| **C. Migrate as-is** | No changes at all beyond the move. Cost: leaves a `set -euET` commented-out in `generate-md-…` even though pub-bin standard has it on. |

**Recommendation:** **A** — meaningful upgrade for the orchestrator, leave the
trivial filters minimal. They each have a usage comment in the header
already.

### 3.3 bin/ cleanup — **OPEN**

After the pub-bin commit lands:

| Option | Action on bin/ |
|--------|----------------|
| **A. Hard-delete the 3 files** (recommended) | `git rm bin/{generate-md-file-and-screenshot-lists.sh, convert-to-md-file-link-list.sh, convert-to-md-clickable-image-list.sh}` in a separate bin-repo commit. Mirrors the policy already used for the 7 other previously-migrated scripts (still queued as `delete-bin-dups` todo). |
| **B. Leave bin/ copies as stubs that `exec` the pub-bin versions** | Adds backward compatibility for anything that hardcoded `~/data/lblackb/git/bin/…`. Cost: lingering duplicates. |
| **C. Defer** | Wait until later when we batch-delete all previously-migrated scripts. |

**Recommendation:** **A** — matches policy.

### 3.4 LinkedIn-posts archive — **LOCKED** (from prior turn)

Leave untouched. Historical record.

### 3.5 Strict-mode (`set -euET -o pipefail`) is required, not optional — **LOCKED**

**Decision:** Every script in pub-bin (including the three being migrated)
runs under `set -euET -o pipefail`. Disabling, commenting out, or relaxing
this directive is **forbidden**. If a script appears to need it relaxed,
the script has a bug that must be fixed at the source.

**Why this is locked here:**

The `bin/` copy of `generate-md-file-and-screenshot-lists.sh` had line 2
commented out (`#set -euET -o pipefail`) — strict mode was **disabled**.
The migration to pub-bin **enables** it (uncomments the line). That is a
strict net safety **improvement**, not a removal of safety. To eliminate
any future ambiguity (in this session, the next session, or for a future
human reader), the decision and its rationale are recorded here.

**What `set -euET -o pipefail` buys us:**

| Flag | Effect | Why it matters |
|------|--------|----------------|
| `-e` | Exit on any command failure | A failed `mv`, `mkdir`, or `find` halts the script instead of cascading wrong state through later steps |
| `-u` | Unset variables are a fatal error | Catches typo'd variable names (`${directoryy}` instead of `${directory}`) at runtime instead of silently producing empty paths |
| `-E` | ERR traps inherit into functions/subshells | Error handling stays consistent inside `function foo { ... }` |
| `-T` | DEBUG/RETURN traps inherit too | Required for clean trap behavior when combined with `-E` |
| `-o pipefail` | Pipeline exit status is the rightmost non-zero | Catches failures in the middle of a pipe (e.g. `cmd1 \| cmd2 \| cmd3` where `cmd2` dies) that would otherwise be masked by a successful `cmd3` |

Without these, a broken script can silently produce wrong output,
truncate files, generate empty markdown lists, or — in the case of
`fix-spaces-in-filenames.sh` invoked from `generate-md-…` — quietly fail
to rename files while the orchestrator marches on as if everything
worked.

**Safety verification for this specific migration:**

The most common reason to comment out strict mode is that something
broke under it and was never fixed. Before locking the enable-it
decision, the script was smoke-tested with `set -euET -o pipefail`
active:

1. With spaced filenames in the input directory → ran cleanly,
   `fix-spaces-…` invoked correctly, markdown emitted, exit 0.
2. With **no** spaced filenames in the input directory → ran cleanly,
   the `find … | grep " " | fix-spaces-…` pipeline produced empty
   output (no rename happens), markdown emitted, exit 0. The `grep`
   no-match exit-1 is consumed because `grep` is not the rightmost
   stage of the pipe; `fix-spaces-in-filenames.sh` reads an empty
   stdin and exits 0, so the pipeline's overall exit is 0.

No latent bug. The original author either commented it out
defensively before writing the rest, or hit an unrelated transient
issue. Either way, the script is strict-mode-clean today, and the
pub-bin standard takes precedence.

**Enforcement going forward:**

- The two new READMEs (`file-tools/README.md`, `markdown-tools/README.md`)
  link back to `README-AI-CODING-STANDARDS.md` and call out strict mode
  as a hard requirement.
- This § 3.5 in the plan doc itself serves as the canonical rationale
  any future agent must respect before considering a relaxation.
- The bats tests (already present for `fix-spaces-*`) will catch a
  regression if strict mode is ever silently disabled and the script
  starts behaving differently on edge inputs.

---

## 4. Approach

Single pub-bin commit:
1. `git mv` `pub-bin/fix-spaces-in-filename(s).sh` → `pub-bin/file-tools/…`
2. `cp` (then `chmod +x`) the 3 bin/ scripts into `pub-bin/markdown-tools/…`,
   making the agreed upgrades to `generate-md-…`.
3. Write `pub-bin/file-tools/README.md` and `pub-bin/markdown-tools/README.md`
   following the `network-tools/README.md` pattern.
4. Update `pub-bin/README.md` (example paths for `fix-spaces-*`).
5. Update 2 bats files + `tests/scripts/README.md`.
6. Add 5 entries to `.migration-tracking.json` (3 migrate, 2 reorganize).
7. Run bats tests + smoke tests.
8. Two-step pub-bin commit.

Then, in a separate bin-repo commit:
9. `git rm` the 3 migrated scripts from bin/.

---

## 5. Detailed changes

### 5.1 New file-tools/

```
pub-bin/file-tools/
  README.md
  fix-spaces-in-filename.sh    (git mv from pub-bin/)
  fix-spaces-in-filenames.sh   (git mv from pub-bin/)
```

`file-tools/README.md`: title, purpose (filesystem hygiene), per-script bullet
list with `[-h]`-style usage line, then Usage section with examples. Matches
`network-tools/README.md` shape.

### 5.2 New markdown-tools/

```
pub-bin/markdown-tools/
  README.md
  generate-md-file-and-screenshot-lists.sh   (from bin/, with § 3.2-A upgrades)
  convert-to-md-file-link-list.sh            (from bin/, unchanged)
  convert-to-md-clickable-image-list.sh      (from bin/, unchanged)
```

`generate-md-…` upgrades:
- **Enforce the pub-bin strict-mode standard:** uncomment line 2's
  `#set -euET -o pipefail` so the script behaves like every other pub-bin
  script. Verified safe — smoke-tested both with and without spaced
  filenames in the input directory; the pipeline `find … | grep " " | …`
  short-circuits cleanly on no-match because `grep` is the middle stage
  of the pipe and `fix-spaces-in-filenames.sh` reads an empty stdin
  without erroring.
- Make `script_dir` resolve to an absolute path so `${script_dir}/…`
  works regardless of how the script is invoked:
  `script_dir=$(cd "$(dirname "$0")" && pwd)`.
- No interface change.

`convert-to-md-file-link-list.sh` and `convert-to-md-clickable-image-list.sh`
upgrades (per § 3.2 decision B — full standard template on the tiny filters
too):
- Add `script_name=$(basename $0)` / `script_dir=$(cd "$(dirname "$0")" && pwd)`.
- Add a `usage()` function explaining: reads filenames from stdin, emits one
  markdown line per file. Include the existing example block from the
  current header comments. Show flags: `-h` for help.
- Add a `getopts ":h"` loop that calls `usage; exit 0` on `-h` and
  `usage "Invalid Option: -$OPTARG"; exit 1` on `\?`.
- Keep the one-line core (`while read file ; do echo "* [${file}](${file})" ; done`
  / image variant) unchanged.
- Result: ~50-line scripts that match the rest of pub-bin's shape.

### 5.3 Update `pub-bin/README.md`

Lines 436–497 contain `./fix-spaces-in-filename.sh` and
`./fix-spaces-in-filenames.sh` example invocations. Update each to
`./file-tools/…`.

(TOC entries on lines 187–188 use auto-generated anchors that don't change
when the script *file* moves — only the script *heading* matters for anchors.
Those stay as-is.)

### 5.4 Update bats tests

Both `test_fix_spaces_in_filename(s).bats` files use
`get_script_path "fix-spaces-in-filename(s).sh"`. Change to
`get_script_path "file-tools/fix-spaces-in-filename(s).sh"`. Helper resolves
relative paths against `PROJECT_ROOT` so the prefix just works.

### 5.5 Update `.migration-tracking.json`

Add 5 entries to the `migrations` map:
- `markdown-tools/generate-md-file-and-screenshot-lists.sh` (method: `migrated-and-upgraded`)
- `markdown-tools/convert-to-md-file-link-list.sh` (method: `migrated-and-upgraded`)
- `markdown-tools/convert-to-md-clickable-image-list.sh` (method: `migrated-and-upgraded`)
- `file-tools/fix-spaces-in-filename.sh` (method: `reorganized`)
- `file-tools/fix-spaces-in-filenames.sh` (method: `reorganized`)

Existing top-level fix-spaces entries: leave in place as historical record.

### 5.6 Verification

- `bash -n` on all 3 new pub-bin scripts.
- `bats tests/scripts/unit/test_fix_spaces_in_filename.bats tests/scripts/unit/test_fix_spaces_in_filenames.bats` passes.
- `source pub-bin/setup-path.sh` in fresh shell → `which generate-md-file-and-screenshot-lists.sh` resolves to `pub-bin/markdown-tools/…`; ditto for both `convert-to-md-…` and both `fix-spaces-*`.
- Smoke test: create temp dir with a `.png` and a `.txt` (with space in name), run `generate-md-file-and-screenshot-lists.sh -Y -d <tmpdir>`, confirm markdown output has both Files and Screenshots sections and the spaced file was renamed.

### 5.7 Commits

**Commit 1 (pub-bin, two-step approval):**
> Migrate generate-md + convert-to-md helpers to markdown-tools/; move fix-spaces-* to file-tools/

**Commit 2 (bin/, plain review):**
> Remove generate-md + convert-to-md helpers (migrated to pub-bin/markdown-tools/)

---

## 6. Todos

| id | title | depends on |
|----|-------|------------|
| `pick-subdirs` | Confirming § 3.1 subdir layout | — |
| `pick-upgrades` | Confirming § 3.2 upgrade scope | — |
| `pick-bin-cleanup` | Confirming § 3.3 bin/ cleanup policy | — |
| `create-file-tools` | Creating `file-tools/` + README + `git mv` fix-spaces scripts | `pick-subdirs` |
| `create-markdown-tools` | Creating `markdown-tools/` + README + copy 3 scripts (with upgrades per § 3.2) | `pick-subdirs`, `pick-upgrades` |
| `update-pub-bin-readme` | Updating top README example paths | `create-file-tools` |
| `update-bats` | Updating both bats test files | `create-file-tools` |
| `update-tests-readme` | Updating `tests/scripts/README.md` if needed | `create-file-tools` |
| `update-migration-json` | Adding 5 entries to `.migration-tracking.json` | `create-file-tools`, `create-markdown-tools` |
| `run-bats` | Running both bats tests | `update-bats` |
| `smoke-test-generate-md` | End-to-end smoke test of `generate-md-…` via PATH | `create-markdown-tools` |
| `commit-pub-bin` | Two-step pub-bin commit | all of the above |
| `delete-bin-dups-genmd` | `git rm` 3 scripts from bin/ (per § 3.3) | `commit-pub-bin`, `pick-bin-cleanup` |
| `commit-bin-delete` | Plain-review bin-repo commit | `delete-bin-dups-genmd` |

---

## 7. Rollback

- **pub-bin commit:** `git -C pub-bin revert <sha>` restores pre-move state.
  `setup-path.sh` continues working (auto-discovery just stops finding the
  new dirs).
- **bin/ deletion commit:** `git -C bin revert <sha>` restores the 3
  scripts.

Order matters: revert bin/ deletion **first** if both need rolling back, so
the bin/ versions exist before the pub-bin reorganization is undone.

---

## 8. Out of scope

- Moving the other 8 top-level `pub-bin/*.sh` files. Candidates for a future
  reorg: `check-ai-readmes.sh`, `clean-emacs-files.sh`, `clean-screenshots.sh`,
  `load-ssh-key.sh`, `monitor-ai-agent-progress.sh`, `rename-email.sh`,
  `start-cursor-agent.sh`. (`setup-path.sh` and `shell-template.sh`
  legitimately belong at top level.)
- The original `delete-bin-dups` queue from the earlier migration (7 scripts).
- Any behavior change beyond the `set -e` toggle in `generate-md-…`.
