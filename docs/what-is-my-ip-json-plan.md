# Plan — `what-is-my-ip.sh` enhancement + IP-script migration to pub-bin

## 0. Quick answers to Lee's questions

> **Q: Is `~/data/lblackb/git/pub-bin/network-tools/intelligence/record-ip-api-json.sh` a duplicate?**

**Yes.** Two copies exist of `record-ip-api-json.sh`:

| Location | Size | Notes |
| --- | --- | --- |
| `bin/record-ip-api-json.sh` | 1086 B | older, simpler — no `-h`, no usage(), no validation |
| `pub-bin/network-tools/intelligence/record-ip-api-json.sh` | 2081 B | upgraded — `-h` help, `usage()`, `getopts`, validation. **Already tracked** in `pub-bin/.migration-tracking.json`. **Already has a bats test** at `pub-bin/tests/record-scripts/unit/test_record_ip_api_json.bats`. |

**The pub-bin version is canonical.** The `bin/` copy is stale and should be deleted — no merge needed.

> **Q: Do the old scripts still exist in `bin/`?**

**Yes, all three:**

| Script in `bin/` | Size | Exists in `pub-bin/`? |
| --- | --- | --- |
| `bin/ip-api-json.sh` | 523 B | ❌ **missing** — needs migration |
| `bin/record-ip-api-json.sh` | 1086 B | ✅ exists (newer copy) — bin/ is the **stale dup**, delete it |
| `bin/what-is-my-ip.sh` | 1121 B | ❌ **missing** — needs migration |

Confirms Lee's "pub-bin is where I want this stuff" direction — all three need to end up under `pub-bin/network-tools/` and the bin/ copies removed.

### 0.1 Immediate quick win — delete the 5 stale `bin/` scripts already migrated to pub-bin

Per Lee's policy: **pub-bin is the go-forward location** for everything that has been migrated from bin. Anything in `bin/` that already has a (newer, upgraded) twin in `pub-bin/` is a stale duplicate and should be removed.

A full sweep of `bin/` against `pub-bin/` found **5** such duplicates. All are already tracked in `pub-bin/.migration-tracking.json`, all are smaller/older than the pub-bin canonical version, and **none have hard-coded `bin/…` path callers** (verified by grep across `bin/`, `pub-bin/`, and shell rc files):

| bin/ script (to delete) | bin size | pub-bin canonical | pub size |
| --- | --- | --- | --- |
| `bin/record-ip-api-json.sh` | 1086 B | `pub-bin/network-tools/intelligence/record-ip-api-json.sh` | 2081 B |
| `bin/record-log-show.sh` | 684 B | `pub-bin/system-tools/record-log-show.sh` | 2446 B |
| `bin/record-nmap.sh` | 224 B | `pub-bin/network-tools/scanning/record-nmap.sh` | 2089 B |
| `bin/record-nslookup.sh` | 1076 B | `pub-bin/network-tools/diagnostics/record-nslookup.sh` | 2069 B |
| `bin/record-whois.sh` | 1070 B | `pub-bin/network-tools/intelligence/record-whois.sh` | 2047 B |

➡ **Action:** delete all 5 from `bin/` in one commit. No prep, no dependencies, no callers to update.

```
rm /Users/lee.blackburn2/data/lblackb/git/bin/record-ip-api-json.sh \
   /Users/lee.blackburn2/data/lblackb/git/bin/record-log-show.sh \
   /Users/lee.blackburn2/data/lblackb/git/bin/record-nmap.sh \
   /Users/lee.blackburn2/data/lblackb/git/bin/record-nslookup.sh \
   /Users/lee.blackburn2/data/lblackb/git/bin/record-whois.sh
```

(Detail at § 5.3.)

---

## 1. Goal

Two interlocking pieces of work:

1. **Enhancement** (original ask) — give `what-is-my-ip.sh` a `--json` output mode and have it also fetch geo/ISP info via the `ip-api-json.sh` helper.
2. **Migration** (added by Lee) — move `what-is-my-ip.sh`, `ip-api-json.sh`, and the older bin/ copy of `record-ip-api-json.sh` from `~/data/lblackb/git/bin/` to `~/data/lblackb/git/pub-bin/`, matching the existing migration pattern already established for the rest of the `record-*` scripts.

Doing the migration **first** means the enhancement work happens against the canonical pub-bin copy (with help/usage/getopts already in the template), and we do not have to redo it later.

---

## 2. Analysis — bin/ vs pub-bin/ landscape

### 2.1 The three target scripts (in `bin/`)

| Script | Size | Status in pub-bin | Action |
| --- | --- | --- | --- |
| `bin/ip-api-json.sh` | 523 B | **MISSING** | migrate to `pub-bin/network-tools/intelligence/` (upgrade to template) |
| `bin/record-ip-api-json.sh` | 1086 B | **EXISTS** as `pub-bin/network-tools/intelligence/record-ip-api-json.sh` (2081 B, upgraded) — already tracked in `.migration-tracking.json` | delete the `bin/` duplicate (older copy) |
| `bin/what-is-my-ip.sh` | 1121 B | **MISSING** | migrate to `pub-bin/network-tools/diagnostics/` (upgrade + add `--json` + geo) |

### 2.2 Why those target directories?

`pub-bin/network-tools/` is already organized into four subfolders that match how scripts get categorized in `docs/record-scripts-analysis.md`:

```
network-tools/
├── capture/        record-tcpdump, analyze-tcpdump, sanitize-analysis-ipmask
├── diagnostics/    record-netstat, record-network-config, record-nslookup, sort-netstat-tcp
├── intelligence/   record-ip-api-json, record-whois
└── scanning/       record-nmap
```

- `what-is-my-ip.sh` → **`diagnostics/`** — discovers facts about *your own* connection. (After we add `--json` + geo it still primarily answers "what is my external IP".)
- `ip-api-json.sh` → **`intelligence/`** — looks up info about *a remote* IP. Same category as `record-ip-api-json.sh` (which it underlies) and `record-whois.sh`.

### 2.3 Migration pattern already in use (sample: `record-nslookup.sh`)

The diff between `bin/record-nslookup.sh` and the migrated `pub-bin/.../record-nslookup.sh` shows the standardization rule used in prior migrations:

- Add structured comment banners (`CLI Parameters`, `functions`, `main script logic`).
- Add a `usage()` function with `-h` flag, options list, arguments list, and example.
- Add `getopts ":h"` loop with `\?` invalid-option handler.
- Keep file name identical to the bin/ original.
- Standard footer / shellcheck-friendly structure.

Source of truth for the template: **`pub-bin/shell-template.sh`**.

### 2.4 Callers / cross-references

| Caller | Reference | Action needed |
| --- | --- | --- |
| `bin/full-recon.sh` line 43 | `ip-api-json.sh ${ip} \| tee ${ip_api_out}` | After migration, this call will fail (PATH only has `pub-bin/` top level — not `pub-bin/network-tools/intelligence/`). **Recommend: update `full-recon.sh` to use absolute path or migrate `full-recon.sh` too.** Out of strict scope; flag as a follow-up. |
| `pub-bin/network-tools/intelligence/record-ip-api-json.sh` | calls `ip-api-json.sh` | Same PATH problem. Already broken today unless ip-api-json.sh happens to be on PATH (it is — from `bin/` top level). After migration, will be broken unless we add the intelligence/ dir to PATH **or** put scripts at pub-bin top level. |
| `pub-bin/tests/record-scripts/unit/test_record_ip_api_json.bats` | tests the pub-bin version of `record-ip-api-json.sh` | nothing to change |
| `pub-bin/network-tools/README.md` | already has entry for `record-ip-api-json.sh`; **missing** entries for `what-is-my-ip.sh` and `ip-api-json.sh` | add two entries |
| `pub-bin/.migration-tracking.json` | already has `record-ip-api-json.sh`; **missing** entries for `what-is-my-ip.sh` and `ip-api-json.sh` | add two entries |

### 2.5 Stray artifacts to clean up

- `pub-bin/docs/ip-api-whois_-h_2026-05-31_181713.txt` — output from Lee running the bin/ version with `-h` (which the bin/ version naively passed through as the IP). Cwd was `docs/` at the time. Safe to delete.

### 2.6 The PATH question (must decide before migration completes)

Today `pub-bin/` top-level is on PATH; subdirs are **not**. So `ip-api-json.sh` cannot be invoked by bare name from `full-recon.sh` (or anywhere else) after it moves into `network-tools/intelligence/`. The same problem already exists today for **every** script under a pub-bin subdir — `record-nmap.sh`, `record-nslookup.sh`, `record-whois.sh`, `record-log-show.sh`, etc. None of them are reachable on PATH. This is almost certainly why Lee "can't find the new scripts" — they are categorized into subdirs but no PATH entry makes them discoverable.

A `find` of pub-bin's script-bearing subdirs surfaces:

```
pub-bin/                                       (already on PATH)
pub-bin/arecibo-message
pub-bin/azure
pub-bin/config
pub-bin/cursor
pub-bin/git
pub-bin/git/hooks                              (internal — exclude)
pub-bin/greynoise
pub-bin/LinkedIn-posts/scripts                 (project-local — exclude?)
pub-bin/network-tools/capture
pub-bin/network-tools/diagnostics
pub-bin/network-tools/intelligence
pub-bin/network-tools/scanning
pub-bin/system-tools
pub-bin/trufflehog/scripts
pub-bin/trufflehog/scripts/credential-loaders  (internal Python lib — exclude)
```

Mixing runnable command-line tools with internal helpers / Python modules / git hooks means a blind `for d in pub-bin/*/; do PATH+=:$d; done` would pollute PATH with the wrong dirs.

#### Recommended approach — auto-discovery loader script in pub-bin (one line in `.bash_profile`)

Per Lee's direction: "I want a script in pub-bin that can be called from `.bash_profile` to update the PATH so that all scripts can be accessed on the PATH. One line include in the `.bash_profile`."

**Design:**

1. **Single sourceable script** lives in the repo at **`pub-bin/setup-path.sh`** (or `pub-bin/config/setup-path.sh` — Lee can pick).

2. **One line in `~/.bash_profile`:**

   ```bash
   . "${HOME}/data/lblackb/git/pub-bin/setup-path.sh"
   ```

   This **replaces** the current `PATH=${PATH}:${HOME}/data/lblackb/git/pub-bin` line — the new script handles the top-level dir too.

3. **The script's job — auto-discover every subdir that holds runnable scripts and add it to PATH**, with a small built-in denylist for dirs that are *known* to be internal (tests, git hooks, importable Python packages, sourceable helpers).

   ```bash
   #!/usr/bin/env bash
   # setup-path.sh — extend PATH with every pub-bin subdir that holds runnable
   # scripts. Sourced from ~/.bash_profile with a single line:
   #   . "${HOME}/data/lblackb/git/pub-bin/setup-path.sh"

   _pub_bin_root="${HOME}/data/lblackb/git/pub-bin"
   [ -d "${_pub_bin_root}" ] || return 0

   # Dirs we never want on PATH (tests, git-hook internals, importable
   # Python packages, sourceable-only helpers).
   _pub_bin_deny_re='/(\.git|tests?|test_hooks|archive|credential-loaders|hooks|config)(/|$)'

   _pub_bin_add() {
       case ":${PATH}:" in
           *":$1:"*) ;;                        # already on PATH
           *) PATH="${PATH}:$1" ;;
       esac
   }

   # Top-level
   _pub_bin_add "${_pub_bin_root}"

   # Every subdir that contains an executable file, minus the denylist.
   while IFS= read -r -d '' dir; do
       case "${dir}" in
           *${_pub_bin_root}*) ;;
       esac
       [[ "${dir}" =~ ${_pub_bin_deny_re} ]] && continue
       _pub_bin_add "${dir}"
   done < <(
       find "${_pub_bin_root}" -mindepth 1 -maxdepth 4 -type f \
           \( -name '*.sh' -o -name '*.py' \) -perm -u+x -print0 2>/dev/null \
           | xargs -0 -n1 dirname \
           | sort -u \
           | tr '\n' '\0'
   )

   export PATH
   unset _pub_bin_root _pub_bin_deny_re
   unset -f _pub_bin_add
   ```

   - **Auto-discovery rule:** any subdir containing at least one executable `*.sh` or `*.py` file is added.
   - **Denylist** (case-insensitive substring on path): `.git/`, `tests/`, `test_hooks/`, `archive/`, `credential-loaders/`, `hooks/`, `config/` — keeps internal stuff out.
   - **Idempotent:** dedup loop means safe to re-source.
   - **Future-proof:** any new subdir Lee adds with executable scripts gets picked up automatically. No `.bash_profile` edits needed. No per-dir markers needed.

4. **Document it** with a short section in `pub-bin/README.md`: "PATH setup: source `pub-bin/setup-path.sh` from your `.bash_profile`. Add new tool subdirs anywhere under pub-bin; they get on PATH automatically. To intentionally keep a subdir off PATH, put it under one of the denylisted names (`tests/`, `hooks/`, `config/`, etc.) or extend the denylist."

#### Why this approach over alternatives

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **A. Auto-discovery loader + one-line source (recommended)** | One line in `.bash_profile`; loader lives in the repo; all scripts on PATH automatically; new migrations need zero PATH work; survives `git clone` on a new machine | Denylist must be maintained if new categories of internal dirs emerge | ✅ best — matches Lee's stated requirement |
| B. `.onpath` marker file + loader (previous proposal) | Explicit opt-in per dir; no denylist | Every new tool subdir needs a marker added; one more thing to forget; doesn't match "all scripts on PATH" framing | ❌ over-engineered |
| C. Blind `for d in pub-bin/*/` in `.bash_profile` | Smallest single edit | Hits depth-1 only (misses `network-tools/intelligence/`); pollutes PATH with `tests/`/`hooks/`; logic lives in dotfile, not repo | ❌ |
| D. Hard-coded explicit subdir list in `.bash_profile` | Simple to read | Every new subdir requires dotfile edit — exactly the failure mode that caused this issue | ❌ |
| E. Promote all scripts back to pub-bin top level | No PATH config needed | Throws away the categorization Lee just established | ❌ |
| F. Symlink each script into pub-bin top level | Scripts stay categorized; bare-name reachable | Symlink sprawl; double-discovery (`which -a` shows duplicates); easy to leave dangling | ❌ |
| G. Update every caller to use absolute paths | Zero PATH config | Brittle; breaks interactive "just type the name" use | ❌ |

**Recommendation: option A.** Matches Lee's stated requirement exactly: one line in `.bash_profile`, script lives in pub-bin, all scripts on PATH.

**Open question for Lee** — accept option A? Two sub-questions if yes:
- **(a)** Loader path: `pub-bin/setup-path.sh` (top level, simple) or `pub-bin/config/setup-path.sh` (alongside existing `config/config.sh`)?
- **(b)** Are the default denylist entries (`tests/`, `hooks/`, `config/`, `archive/`, `credential-loaders/`, `test_hooks/`) the right set?

---

## 3. Scope confirmed earlier (carried forward)

From the original `ask_user` round:

1. Target script to enhance: **`what-is-my-ip.sh`** only.
2. `--json` is **opt-in**; current human/text output stays the default.
3. Geo lookup is **always fetched** (one ip-api.com call per run, ~50 ms) — i.e., regardless of `--json`, we always have geo data to include.
4. **Always** log to `~/log/ip_log/` per current behavior, even when `--json` is used.

Plus current cleanups while we're in the file:

- Fix `IPv6L:` typo on line 32 → `IPv6:`.
- Remove unused CLI param stubs (`QUIET`, `VERBOSE`, `TEST_MODE`, `aws_profile`, `region`).

---

## 4. Proposed end-state

After this plan executes:

```
pub-bin/
├── network-tools/
│   ├── diagnostics/
│   │   └── what-is-my-ip.sh          # NEW — upgraded + --json + geo
│   ├── intelligence/
│   │   ├── ip-api-json.sh            # NEW — upgraded
│   │   ├── record-ip-api-json.sh     # unchanged (already migrated)
│   │   └── record-whois.sh           # unchanged
│   └── README.md                     # +2 entries
├── docs/
│   └── what-is-my-ip-json-plan.md    # this plan
├── tests/record-scripts/unit/
│   ├── test_record_ip_api_json.bats  # unchanged
│   ├── test_what_is_my_ip.bats       # NEW (matching pattern)
│   └── test_ip_api_json.bats         # NEW (matching pattern)
└── .migration-tracking.json          # +2 entries

bin/
├── ip-api-json.sh                    # DELETED (newly migrated to pub-bin)
├── record-ip-api-json.sh             # DELETED (stale dup; canonical = pub-bin)
├── record-log-show.sh                # DELETED (stale dup; canonical = pub-bin)
├── record-nmap.sh                    # DELETED (stale dup; canonical = pub-bin)
├── record-nslookup.sh                # DELETED (stale dup; canonical = pub-bin)
├── record-whois.sh                   # DELETED (stale dup; canonical = pub-bin)
├── what-is-my-ip.sh                  # DELETED (newly migrated to pub-bin)
└── full-recon.sh                     # unchanged (relies on PATH fix from §2.6)
```

---

## 5. Implementation order

Each step is a discrete commit candidate.

### 5.1 Pre-work (read-only)
- Read `pub-bin/.cursorrules`, `pub-bin/README-AI-CODING-STANDARDS.md`, and `pub-bin/shell-template.sh` to confirm commit conventions and template structure.
- Read existing `network-tools/intelligence/record-ip-api-json.sh` + `record-whois.sh` for in-flight conventions.
- Decide PATH question (§2.6) — **needs Lee's answer before §5.4 ships**.

### 5.2 Migrate `ip-api-json.sh`
- Copy `bin/ip-api-json.sh` → `pub-bin/network-tools/intelligence/ip-api-json.sh`.
- Apply the standard upgrade: usage(), `-h` flag, getopts, comment banners. Keep behavior identical (`curl … | jq`).
- Add bats test `tests/record-scripts/unit/test_ip_api_json.bats` (mirroring `test_record_ip_api_json.bats`).
- Add `network-tools/README.md` entry.
- Add `.migration-tracking.json` entry.
- Delete `bin/ip-api-json.sh`.

### 5.3 Reconcile already-migrated stale dups in `bin/` (the quick win, see § 0.1)
- Sweep complete — **5** scripts in `bin/` already have a canonical pub-bin twin: `record-ip-api-json.sh`, `record-log-show.sh`, `record-nmap.sh`, `record-nslookup.sh`, `record-whois.sh`.
- All 5 are already tracked in `pub-bin/.migration-tracking.json`; all 5 are smaller/older than the pub-bin version; **no caller depends on the `bin/` copies** (grep-verified across `bin/`, `pub-bin/`, and shell rc files).
- **Action:** `rm` all 5 in one commit on the `bin/` repo. No pub-bin changes required.
- Ships independently — should land **before** the rest of this plan executes.

### 5.4 Migrate `what-is-my-ip.sh`
- Copy `bin/what-is-my-ip.sh` → `pub-bin/network-tools/diagnostics/what-is-my-ip.sh`.
- Apply standard upgrade (usage + `-h` + getopts + banners).
- Fix `IPv6L:` typo and drop unused stub vars during the upgrade.
- Add bats test `tests/record-scripts/unit/test_what_is_my_ip.bats`.
- Add `network-tools/README.md` entry.
- Add `.migration-tracking.json` entry.
- Delete `bin/what-is-my-ip.sh`.

### 5.5 Enhance `what-is-my-ip.sh` with `--json` + geo (in pub-bin)
- Extend `usage()` to document `--json` (or `-j`) flag.
- Always run geo lookup via `ip-api-json.sh <ipv4>` (the now-migrated helper).
- Default mode: append a short human-readable geo line to existing output ("Location: City, Region, Country — Org: …").
- `--json` mode: emit a single JSON object containing `ipv4`, `ipv6`, and the full `ip-api` payload nested under `geo`.
- Always continue to write the log file under `~/log/ip_log/` (the log captures whichever output mode ran).
- Update bats test to cover both modes.

### 5.6 Address PATH — install the auto-discovery loader (per § 2.6 option A)
- Create **`pub-bin/setup-path.sh`** (top level — easy to find; alternatively `config/setup-path.sh` per § 2.6 sub-question).
- Loader auto-discovers every subdir under pub-bin that contains an executable `*.sh`/`*.py`, minus a built-in denylist (`tests/`, `hooks/`, `config/`, `archive/`, `credential-loaders/`, `test_hooks/`).
- Document the pattern in `pub-bin/README.md`.
- Edit `~/.bash_profile`: **replace** the existing line
  ```bash
  PATH=${PATH}:${HOME}/data/lblackb/git/pub-bin
  ```
  with the single sourcing line
  ```bash
  . "${HOME}/data/lblackb/git/pub-bin/setup-path.sh"
  ```
  **Outside pub-bin repo** — separate dotfile change.
- Verify with `which ip-api-json.sh`, `which record-nmap.sh`, `which record-nslookup.sh` in a fresh shell.

### 5.7 Cleanup
- Delete stray `pub-bin/docs/ip-api-whois_-h_2026-05-31_181713.txt`.
- Smoke test (§7).
- Commit per pub-bin conventions (TBD after §5.1 reads).

### 5.8 Follow-ups (out of scope but worth noting)
- `bin/full-recon.sh` still depends on `ip-api-json.sh` being on PATH. Once PATH fix (§5.6) lands, it keeps working — but the script itself remains in `bin/` and is a candidate for a future migration.

---

## 6. Open questions for Lee

1. **PATH loader location** — `pub-bin/setup-path.sh` (top level, simple) or `pub-bin/config/setup-path.sh` (alongside existing `config/config.sh`)?
2. **PATH denylist** — accept the default denylist (`tests/`, `hooks/`, `config/`, `archive/`, `credential-loaders/`, `test_hooks/`), or want different defaults?
3. **Backward-compat symlinks** — leave any of the deleted bin/ scripts as symlinks pointing into pub-bin, or hard-delete them? (Existing migrations look like hard deletes, but want to confirm.)
4. **Flag name** — `--json` (long) or `-j` (short) or both?

---

## 7. Smoke tests (post-implementation)

Run from anywhere:
- `what-is-my-ip.sh` — default output: IPv4, IPv6, geo line; log file under `~/log/ip_log/`.
- `what-is-my-ip.sh --json` — single JSON blob to stdout; same log file written.
- `ip-api-json.sh 8.8.8.8` — pretty JSON for Google DNS.
- `ip-api-json.sh -h` — usage.
- `record-ip-api-json.sh -h` — usage (already passing today via existing bats test).
- `full-recon.sh <ip>` — confirms PATH fix.
- `bats pub-bin/tests/record-scripts/unit/` — all green.

---

## 8. Risks / notes

- `ip-api.com` rate-limit is 45 req/min unkeyed; non-issue at one call per `what-is-my-ip` invocation but worth noting in script comment.
- `dig` against external resolvers can fail on locked-down networks; current script doesn't handle that and we are not adding handling in this pass.
- PATH change is a global side effect; flag clearly in commit message and dotfile.
