# Plan 002 — `secure-volume.sh` mounts secured volumes from a symlink registry

**Status:** **Proposed** (2026-09-01) — not yet implemented. Second plan in the `docs/plans/`
sequence; the `plan-001`..`plan-021` numbering under [`../osx/plans/`](../osx/plans/README.md) is
that product's own frozen sequence and is untouched by this work. Per
[`.cursorrules`](../../.cursorrules) rule 3 this file is the canonical copy — `~/.claude/plans/`
must never be the only one.

## Goal

One command that mounts a secured (FileVault-encrypted APFS) volume from the CLI, driven entirely
off a directory of symlinks so the script contains no volume name, registry path, or other
environment-specific value. The volume passphrase comes from KeePassXC the way `load-ssh-key.sh`
gets SSH key passphrases, falling back to an interactive prompt when no KeePassXC database is
configured. No secret is ever written to the macOS keychain, to disk, to `argv`, or to shell
history.

## Context

A directory of symlinks acts as a registry, each link pointing at a path *inside* a secured volume:

```
<registry>/vault -> /Volumes/vault/vault/
```

Note that the link targets a subdirectory *inside* the volume, not the volume root — so a
successful mount has to be verified against the full target path, not just the mount point.

Today these volumes can only be unlocked by hand (Disk Utility, or `diskutil apfs unlockVolume`
typed out with the right device identifier). There is no tooling for them anywhere in the repo:
`grep -rniE "diskutil|/Volumes|apfs|unlockVolume"` across `*.sh`/`*.py`/`*.md` returns zero code
hits, so this is greenfield.

### Environment facts that shape the design (verified)

The target volumes are **FileVault-encrypted APFS volumes**, which may live in the internal
container rather than being disk images. The volume available for testing reports
`Encryption: true`, `FileVault: true`, `Locked: true`, `MountPoint: ""`, and has exactly one
crypto user of type **Disk User** — i.e. **passphrase-only unlock**, with no account-password or
recovery-key path. That is why `-user disk` is the correct selector.

Platform: macOS 26.6.2, `/bin/bash` is 3.2 → bash-3.2-safe constructs only.

| Fact | Consequence |
| --- | --- |
| `diskutil apfs unlockVolume <dev> -user disk -stdinpassphrase` unlocks **and** mounts | one call handles the locked case |
| `diskutil apfs lockVolume <dev>` unmounts **and** re-locks | backs the `unmount` command |
| APFS device ids (`diskNsM`) are **not** stable across reboots or container changes | resolve the device at runtime; never store or hardcode one |
| `diskutil info -plist <dev>` exposes `Locked` and `MountPoint` | machine-readable state → safe idempotency |
| Volume names genuinely collide (this machine has `Recovery` x3, `Macintosh HD` x2) | must enumerate and **detect ambiguity**, not trust a bare name lookup |
| An attached disk image here mounts under a private `/var/folders/...` path, not `/Volumes/<name>` | mount point is not always `/Volumes/<name>` → verify the real path |
| `jq` and `plutil` are system-provided (`/usr/bin/jq`, `/usr/bin/plutil`) | plist parsing adds no third-party dependency |
| `keepassxc-cli` is **not** on `PATH`; it ships only inside the KeePassXC app bundle | the app-bundle candidate search from `load-ssh-key.sh` is required |

## Design decisions (confirmed with user)

- **Repo and location:** pub-bin, repo root, beside `load-ssh-key.sh`. Root level plus `chmod +x`
  means [`setup-path.sh`](../../setup-path.sh) picks it up automatically — no PATH registration.
- **Name and interface:** `secure-volume.sh` with subcommands `mount` / `unmount` / `status` /
  `setup`. This is a **deliberate deviation from house style** — every other pub-bin script is
  getopts-only — chosen because three verbs read better as subcommands than as mode flags. Flags
  still work on either side of the subcommand.
- **Generic, not site-specific:** no registry path, volume name, or database path appears in the
  script, its usage text, or its defaults. Everything comes from config or a flag.
- **KeePassXC entry lookup:** try both the symlink name and the volume name, each under an optional
  group and then retried at the database root — the group-then-root retry pattern at
  `load-ssh-key.sh:460-483`.
- **Fallback:** when no KeePassXC database is configured (or the entry is missing), prompt for the
  volume passphrase interactively.
- **No keychain**, ever. The passphrase is never persisted anywhere.
- **One shared KeePassXC database.** `keepassxc_db` is the *same* config key `load-ssh-key.sh`
  already reads, deliberately — configuring it here configures both scripts, and no second
  database file is introduced. A volume entry and an SSH key entry simply coexist in the one
  database, which is also why the lookup supports an optional group to keep them tidy.
- **First run prompts for configuration** — the registry folder and the KeePassXC database path.
- **BATS unit test** included, per repo convention.

## Files

| File | Change |
| --- | --- |
| `docs/plans/plan-002-secure-volume-mount.md` | new — this file, canonical plan copy |
| `docs/plans/README.md` | add index-table row for plan-002 |
| `secure-volume.sh` | new, repo root, mode 755 |
| `README.md` | add to the `## Scripts` bullet index + new `### secure-volume.sh` section |
| `tests/scripts/unit/test_secure_volume.bats` | new baseline test |
| `tests/scripts/README.md` | list the new test in the tree diagram |

## Implementation

### 1. Script skeleton (house style)

`#!/usr/bin/env bash`, `set -euET -o pipefail`, `script_name=$(basename $0)` /
`script_dir=$(dirname $0)`, and 80-column `####` banner sections in the order
`CLI Parameters` → `default values` → `functions` → `get command line options` → `Validation` →
`main script logic`, per [`shell-template.sh`](../../shell-template.sh).

Style rules from [`README-AI-CODING-STANDARDS.md`](../../README-AI-CODING-STANDARDS.md):
`${variable}` braces everywhere, `${HOME}` rather than `~`, `$(command)` rather than backticks,
`local` for function variables, `[[ ]]` conditionals, verb-noun function names, functions before
main logic, `tput` colours, errors to `>&2`, no trailing whitespace, file ends with a newline.

`function usage { message=${1:-}; … cat<<EOF … EOF }` with `Usage:`, a description, `Commands`,
`Options`, and `Example:` sections.

### 2. Argument parsing (permuting getopts loop)

Flags must be valid before, between, and after the subcommand and its argument. A single `getopts`
pass cannot do this — `getopts` stops at the first non-option word, so `mount vault -v` would
silently drop `-v`. Two sequential passes have the same defect for anything after the name.

The fix is a **permuting loop**: run `getopts`, consume the one non-option word it stopped on as a
positional, reset `OPTIND`, and re-enter. Verified working on bash 3.2 under
`set -euET -o pipefail`:

```bash
positional_count=0

while [[ $# -gt 0 ]] ; do
    OPTIND=1
    while getopts ":d:D:G:hqvN" opt ; do
        case ${opt} in
            d ) registry_dir=$OPTARG ;;
            D ) keepass_db=$OPTARG ;;
            G ) keepass_group=$OPTARG ;;
            q ) QUIET=true ;;
            v ) VERBOSE=true ;;
            N ) USE_KEEPASS=false ;;
            h ) usage ; exit 0 ;;
            \? ) usage "Invalid option: -${OPTARG}" ; exit 2 ;;
            : ) usage "Option -${OPTARG} requires an argument" ; exit 2 ;;
        esac
    done
    shift $((OPTIND - 1))

    if [[ $# -gt 0 ]] ; then
        positional_count=$((positional_count + 1))
        case ${positional_count} in
            1 ) command_name=$1 ;;
            2 ) entry_name=$1 ;;
            * ) usage "Unexpected argument: $1" ; exit 2 ;;
        esac
        shift
    fi
done
```

Counting positionals into named variables avoids arrays entirely, sidestepping the bash 3.2 `set -u`
empty-array trap that `plan-001` hit with `"${bats_args[@]}"` (fixed there via
`${bats_args[@]+"${bats_args[@]}"}`).

Flags: `-N` skip KeePassXC and prompt (same letter as `load-ssh-key.sh`), `-d <dir>` registry dir,
`-D <db>` database, `-G <group>` group, `-h` help, `-q` quiet, `-v` verbose.

No command defaults to `status`. `mount`/`unmount` without a `<name>` and any unknown command call
`usage "…"` and exit 2.

Prototype results — all verified on `/bin/bash` 3.2.57, flags landing correctly in every position:

| Invocation | Result |
| --- | --- |
| `mount vault` | `command=[mount] name=[vault]` |
| `-v mount vault` | `VERBOSE=[true]` |
| `mount -v vault` | `VERBOSE=[true]` |
| `mount vault -v` | `VERBOSE=[true]` — the case two passes would drop |
| `-d /tmp/reg mount vault -v -N` | dir, verbose, and no-keepass all set |
| `mount -d /tmp/reg vault -G vols` | dir and group set around the name |
| `status` / *(no args)* | `command=[status]` |
| `mount` | exit 2, "mount requires a `<name>`" |
| `mount vault extra` | exit 2, "Unexpected argument: extra" |
| `-x mount vault` | exit 2, "Invalid option: -x" |
| `-d` | exit 2, "Option -d requires an argument" |

### 3. First-run configuration

Load with `. ${script_dir}/config/config.sh` then `load-config "noerror"`, and follow the
`clean-screenshots.sh:17-41` idiom — `setup-config-value` → `save-config-value` →
`load-config "noerror"` to reload.

| Key | Required | Meaning |
| --- | --- | --- |
| `secure_volume_dir` | yes | path to the symlink registry folder |
| `keepassxc_db` | no | path to the KeePassXC database |
| `keepassxc_volume_group` | no | group holding volume entries |

- **First run** is detected by `secure_volume_dir` being unset: run the prompts, save, reload, then
  continue with the requested command.
- `setup` re-runs the prompts on demand. `setup-config-value` already offers the existing value as
  the default, so it doubles as "change my configuration".
- A blank `keepassxc_db` is a supported answer and permanently selects the interactive-passphrase
  path.
- Validation: the registry directory must exist and be a directory; a non-blank `keepassxc_db` must
  exist.
- Configuration runs before any table output, so `save-config-value`'s stdout banner
  (`config/config.sh:214-219`) cannot interleave with parseable output.

### 4. Registry resolution (the generic core)

For a given `name`:

1. `link="${secure_volume_dir}/${name}"` — must exist and be a symlink (`-L`), else exit 3. Read
   the target with `readlink "${link}"`.
2. Match the target against `^/Volumes/([^/]+)(/.*)?$` to capture the volume name, the expected
   mount root `/Volumes/<volume>`, and the full target path that must resolve at the end.
3. Enumerate every device whose volume name matches:

   ```bash
   diskutil list -plist | plutil -convert json -o - - \
     | jq -r --arg n "${volume}" '
         [ .AllDisksAndPartitions[]
           | (.Partitions // []) + (.APFSVolumes // []) | .[]
           | select(.VolumeName == $n) | .DeviceIdentifier ] | .[]'
   ```

   Filter out nested `diskNsMsK` identifiers — those are APFS **snapshots** (the system volume
   appears as both `disk3s1` and `disk3s1s1` under one name) and would otherwise fake a collision.
   Then branch on the match count:

   - 0 matches → volume not present, e.g. a disk image that is not attached → exit 3
   - more than 1 → ambiguous volume name → exit 4
   - exactly 1 → that device identifier

   Verified: this correctly reports 3 devices for `Recovery` on this machine.
4. Read `Locked`, `MountPoint`, and `Encryption` from `diskutil info -plist <dev>`.

### 5. `mount`

| State | Action |
| --- | --- |
| already mounted at the expected root | report and exit 0 (idempotent) |
| mounted somewhere else | warn that the symlink will not resolve, exit 1 |
| locked | acquire passphrase → `diskutil apfs unlockVolume <dev> -user disk -stdinpassphrase` |
| unlocked but unmounted | `diskutil mount <dev>` |

Afterwards re-read `MountPoint`, confirm it matches the expected root, and confirm the full symlink
target exists (`-e`). The mount root alone is not proof, because the link points at a subdirectory
inside the volume.

### 6. `unmount`

`diskutil apfs lockVolume <dev>` for an encrypted volume — that unmounts *and* re-locks, so
on-demand access is revocable on demand. Plain `diskutil unmount <dev>` for a non-encrypted volume.
No-op and exit 0 when already unmounted.

### 7. `status`

Iterate the registry symlinks and print an aligned table. Never touches KeePassXC, never prompts:

```
NAME     VOLUME   DEVICE    LOCKED  MOUNTED
vault    vault    disk3s7   yes     no
archive  archive  -         -       -
```

A dash means the volume is not currently present.

### 8. Passphrase acquisition

Port from `load-ssh-key.sh` rather than inventing new logic:

1. **Find the CLI** — port `find-keepassxc-cli` (`load-ssh-key.sh:305-338`): config `keepassxc_cli`
   → `command -v` → macOS app-bundle candidate list. Required, since `keepassxc-cli` is not on
   `PATH`.
2. **Enable KeePassXC only if** a database is configured *and* exists *and* the CLI was found. Every
   other case falls back to prompting, mirroring `load-ssh-key.sh:773-795`.
3. **Unlock the database once** — port `ensure-keepassxc-unlocked` (`load-ssh-key.sh:366-449`):
   validate the master password with `db-info -q`, up to 3 attempts, reading from `/dev/tty` with
   `stty -echo` and an `INT` trap that restores the saved `stty` state. `db-info` is the only
   reliable check: under `-q`, `keepassxc-cli` returns 1 for both a bad master password and a
   missing entry, so a per-entry failure cannot be classified unless the master password is already
   known good.
4. **Look up the entry** — `show -q -s -a Password <db> <entry>`, first non-empty hit wins, in
   order: `<group>/<name>`, `<name>`, `<group>/<volume>`, `<volume>`.
5. **Fallback prompt** — if KeePassXC is disabled, the entry is absent, or the returned value is
   empty, prompt on `/dev/tty` for the volume passphrase directly. This covers both "no database
   configured" and "volume not filed in the database yet".

### 9. Secret hygiene (non-negotiable)

Three exposure channels matter here — the terminal, shell history, and the `ps` listing — plus disk
as a fourth. They have different mechanisms and different mitigations, so they are listed
separately rather than as one rule. All findings below were measured on this machine.

#### Keep it out of `ps` (argv)

Confirmed severe: argv is world-readable. An unrelated process running
`ps -axww -o args | grep <secret>` retrieves it in full.

- Use `diskutil apfs unlockVolume <dev> -user disk -stdinpassphrase`. **Never**
  `-passphrase <pw>`.
- Feed it as `printf '%s\n' "${secret}" | diskutil …`. `printf` is a shell builtin, so the value is
  never a separate process's argument.
- Never pass a secret as an argument to a helper script. `load-ssh-key.sh` hands its askpass helper
  an environment variable precisely to avoid this.

**How this gets lost:** `-stdinpassphrase` requires stdin, so the regression appears when stdin is
already consumed — e.g. a `while read` loop over registry entries — and `-passphrase "${pass}"`
looks like the easy fix. `plan-001` hit exactly this stdin collision with `ssh-add` and solved it by
moving the loop input to **FD 3** (`while IFS= read -r x <&3 ; do … done 3< <(…)`). Use FD 3 here
too; do not reach for `-passphrase`.

#### Keep it off the screen

- Read with `stty -echo < /dev/tty` around `IFS= read -r`, and restore the saved `stty` state
  afterwards — including on interrupt, via the `INT` trap. Ported from
  `load-ssh-key.sh:404-418`. The trap protects both directions: without it, `Ctrl-C` mid-prompt
  leaves the terminal with echo still *off*.
- Never log the value. No `${VERBOSE} && echo "passphrase=[${pass}]"`. Verbose mode may log which
  lookup path was tried, never what came back.
- Never enable `set -x` around secret handling — it prints every expansion, including the secret, to
  stderr and therefore into scrollback and any `tee`.

#### Keep it out of shell history

History records only what the user *types* interactively; nothing the script does internally can
reach it. So this protection is **structural, not a technique**: the script deliberately provides
**no** way to supply a passphrase non-interactively.

- No `-P <passphrase>`-style flag, ever. `secure-volume.sh -P hunter2 mount vault` would sit in
  `~/.bash_history` verbatim.
- No reading the passphrase from piped stdin.
- **No `LOAD_SSH_KEY_DB_PASSWORD`-style environment-variable escape hatch.** `load-ssh-key.sh` has
  one (`load-ssh-key.sh:380-396`) for test automation. It is deliberately *not* copied: while an
  environment variable is not a `ps` leak on macOS (verified — `ps eww` against another process
  shows nothing), setting it on a command line puts the secret into history, and it is inherited by
  every child process. The baseline BATS test never unlocks a real volume, so nothing needs it.

**How this gets lost:** someone adds one of the above as a convenience for scripting or testing.

#### Keep it off disk

- **Never** use a here-string (`<<<`). Measured: with `<<<`, fd 0 is a *regular file* at
  `/private/var/tmp/sh-thd-<n>` containing the plaintext, where an equivalent `printf |` pipeline
  gives fd 0 as a `PIPE`. Bash does unlink the file immediately, so it is not reachable by path from
  another process — the exposure is that the plaintext bytes are written to the filesystem at all,
  not that a readable file lingers. Lesser than the `ps` exposure, but a real and free-to-avoid
  difference from a pipe.
- No `mktemp` + write of the secret for any reason.

#### Cleanup

A `clear-secrets` function wipes the master password and the volume passphrase, invoked from `EXIT`
and `INT` traps. Both are safe here because this script is **executed**, not sourced —
`load-ssh-key.sh` had to avoid an `EXIT` trap because it would fire at the end of the caller's
interactive shell session and could clobber the user's own trap.

Nothing is written to the keychain. The config file holds paths only.

### 10. Exit codes

| Code | Meaning |
| --- | --- |
| 0 | success, including an idempotent no-op |
| 1 | runtime failure — unlock or mount failed, or mounted at an unexpected path |
| 2 | usage error or missing prerequisite (`diskutil`/`jq`/`plutil` absent, no TTY when one is needed) |
| 3 | registry entry or volume not found |
| 4 | ambiguous volume name |

### 11. Documentation and tests

- [`README.md`](../../README.md): add `- [secure-volume.sh](#secure-volumesh)` to the `## Scripts`
  index, and a `### secure-volume.sh` section in the established block shape —
  `**What it does:**`, `**Usage:**` (fenced bash), `**Options:**` (one bullet per flag, mirroring
  the `usage` text), `**Configuration:**`, `**Details:**`.
- `tests/scripts/unit/test_secure_volume.bats`, following the baseline contract in
  `test_check_ai_readmes.bats:6-40`: the script exists and is executable, `bash -n` passes, `-h`
  prints usage and exits 0, `skip_if_command_missing` for `diskutil`/`jq`/`plutil`, an unknown entry
  name exits 3, and the script runs without crashing. Uses `get_script_path` / `run_script` from
  `tests/scripts/test_helper.bash:132-149`. No real volume is mounted by the tests.
- Add the new test to the tree diagram in `tests/scripts/README.md:14-27`.

## Verification

Run from the repo root against an entry in the configured registry. A locked, unmounted encrypted
volume is available, so this is a genuine end-to-end test.

1. `./secure-volume.sh -h` — usage renders, and contains no environment-specific paths.
2. First-run setup: with `secure_volume_dir` unset, confirm the script prompts for the registry
   folder and the KeePassXC database, saves both, and then proceeds with the requested command.
   Re-run `./secure-volume.sh setup` and confirm existing values are offered as defaults.
3. `./secure-volume.sh` and `./secure-volume.sh status` — the table lists each registry entry with
   its volume, device, and locked/mounted state. Exercises registry parsing and device resolution
   with no secrets involved.
4. `./secure-volume.sh -v mount <name>` — master-password prompt, entry lookup, unlock. Verify
   independently with `diskutil info <dev> | grep -E 'Mounted|Locked'` and by listing the symlink
   path.
5. Re-run the same mount — must report already-mounted and exit 0 (idempotency).
6. `./secure-volume.sh unmount <name>` — confirm `Locked: Yes` and `MountPoint: ""` again, and that
   the symlink no longer resolves.
7. `./secure-volume.sh -N mount <name>` — exercises the fallback prompt with KeePassXC bypassed,
   i.e. the "no database configured" behaviour.
8. Error paths: `mount no-such-entry` exits 3; a registry entry that is a regular file rather than a
   symlink gives a clear error; piping with no TTY fails cleanly without hanging.
9. No leakage: shell history is clean, and the config file contains paths only — no passphrase.
10. `bats tests/scripts/unit/test_secure_volume.bats` — all pass.
11. Code-quality gate: no trailing whitespace, file ends with a newline (enforced by the repo git
    hooks).

## Not doing

- No keychain integration of any kind.
- No changes to existing symlinks, `load-ssh-key.sh`, or `config/config.sh`.
- No commit — per [`.cursorrules`](../../.cursorrules), commits happen only when explicitly asked.
