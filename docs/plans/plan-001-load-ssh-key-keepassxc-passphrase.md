# Plan 001 — `load-ssh-key.sh` reads SSH key passphrases from KeePassXC

**Status:** **Implemented** (2026-08-16) — all 32 unit tests pass (16 pre-existing + 16 new);
real-database end-to-end run still pending the user. First plan in the `docs/plans/` sequence; the
`plan-001`..`plan-021` numbering under [`docs/osx/plans/`](../osx/plans/README.md) is that product's
own frozen sequence and is untouched by this work. Per [`.cursorrules`](../../.cursorrules) rule 3
this file is the canonical copy — `~/.claude/plans/` must never be the only one.

## Implementation notes (what differed from the plan)

- **Key lists are read on FD 3** (`while IFS= read -r key_file <&3 ; do … done 3< <(…)`), not on
  stdin. Moving the loop body into the current shell exposed a real bug: the fallback `ssh-add`
  inherits the loop's stdin and swallowed the remaining key names, so a passphrase-protected key
  early in the list silently prevented every later key from loading. FD 3 keeps the list out of
  reach of anything the loop invokes. Caught by the "wrong master password" test.
- **An `INT` trap** (`trap 'clear-key-secrets ; trap - INT' INT`) wraps the key-loading section and
  is removed afterwards, so `Ctrl-C` mid-run cannot leave a passphrase in the sourced shell. An
  `EXIT` trap is still deliberately avoided — it would fire at the end of the caller's shell
  session and could clobber the user's own trap.
- **No `test_helper.bash` edit was needed.** `run_load_ssh_key` uses `run bash -c "…"`, which
  inherits exported variables, so prepending the mock to `PATH` and exporting
  `LOAD_SSH_KEY_DB_PASSWORD` in a test is enough.
- **`tests/load-ssh-key/run-tests.sh` had a pre-existing blocker**: `"${bats_args[@]}"` on an empty
  array trips `set -u` under bash 3.2, so the runner failed before running anything. Fixed with
  `${bats_args[@]+"${bats_args[@]}"}`.
- **`assert_output_contains` matches with `=~` (regex)**, so `[` and `]` in expected strings are
  character classes; the new tests escape them.
- **Pre-existing quirk left alone** (out of scope, worth a future fix): `list-loaded-keys` counts
  lines of `ssh-add -l` output, so an empty agent reports
  `Currently loaded SSH keys (1): The agent has no identities.`

## Goal

One `ssh-add` run that loads every passphrase-protected key in `${HOME}/.ssh` with a single
KeePassXC master-password prompt, no per-key passphrase typing, and no secret written to disk,
argv, or the caller's shell environment.

## Context

`load-ssh-key.sh` finds every private key in `${HOME}/.ssh` and adds it to the agent with
`ssh-add -t <timeout> <key>` (`load-ssh-key.sh:268`). For passphrase-protected keys — which is
every real key on this machine — `ssh-add` stops and prompts on the tty, so the script cannot
complete unattended and the passphrase gets retyped on every agent restart.

The passphrases already live in KeePassXC. This change teaches the script to fetch each key's
passphrase from that database and hand it to `ssh-add` without the secret ever touching disk,
argv, or the user's shell environment. One master-password prompt per run replaces one
passphrase prompt per key.

Verified on this machine:

- `keepassxc-cli` 2.7.12 at `/Applications/KeePassXC.app/Contents/MacOS/keepassxc-cli`
  (**not** on `PATH`).
- `keepassxc-cli show` reads the DB password from stdin when stdin is a pipe; the entry password
  goes to **stdout**, the unlock prompt and all errors go to **stderr**.
- With `-q`, stderr is silenced entirely and both "wrong master password" and "entry not found"
  are a silent `rc=1` — failures cannot be told apart. Hence the master password is validated
  **once** up front with `keepassxc-cli db-info -q`, after which any per-entry failure can safely
  be read as an entry problem.
- `ssh-keygen -y -P "" -f <key>` → rc 0 for unprotected keys, rc 255
  (`incorrect passphrase supplied`) for protected ones. Clean protected-key detector; use rc only.
- OpenSSH 10.3p1 → `SSH_ASKPASS_REQUIRE=force` is supported, so no `DISPLAY` workaround is
  strictly needed (`DISPLAY` is still set defensively for OpenSSH < 8.4).
- `ps -E` cannot read another process's environment on macOS, so a per-command env assignment
  scoped to the `ssh-add` invocation is an acceptable channel for the passphrase.
- The only bash on this box is `/bin/bash` 3.2.57 (what `#!/usr/bin/env bash` resolves to), which
  always backs here-strings and heredocs with a temp file — hence the `printf | cmd` pipes below.
  Process substitution `< <(...)` is available in 3.2, so the loop fix in step 7 is safe.
- Repo root is on `PATH` via `setup-path.sh`, so a committed helper at the repo root is reachable
  both through `${script_dir}` and `command -v`.
- `script_dir` (`load-ssh-key.sh:10`) is currently defined but unused — free to build on.
- Indentation in `load-ssh-key.sh` is emacs-style: 4 spaces at level 1, **hard tab** at level 2.
  Match it exactly in every hunk.

## Design decisions (confirmed with user)

| Decision | Choice |
| --- | --- |
| DB master password | Prompted once per run from `/dev/tty` with `stty -echo`; held in a shell variable; cleared on every exit path |
| Entry lookup | Convention — entry title == private key basename, under an optional configurable group |
| Passphrase to ssh-add | `SSH_ASKPASS` helper + `SSH_ASKPASS_REQUIRE=force`, value passed as a per-command env assignment |
| Activation | Automatic when `keepassxc-cli` + a configured DB exist; otherwise fallback to today's interactive prompt |

Two supporting decisions worth stating explicitly:

**Committed askpass helper, not a `mktemp` one.** The repo standard for temp files is
`mktemp` + `trap … EXIT`, but `load-ssh-key.sh` is **sourced**, so a trap installed while sourcing
lands in the user's interactive shell and fires at shell exit — it would either never clean up
during the run or clobber a trap the user already has. A generated helper without a trap leaks a
file on every failure path. A committed helper contains no secret (it only reads an env var),
needs no cleanup, is greppable, and is independently testable.

**Read the two config keys directly; do not source `config/config.sh`.** Sourcing it would
permanently define `load-config`, `save-config-value`, `show-config`, … plus `config_file`,
`secure_dir` in the user's interactive shell — a real footgun for the one script in this repo that
is always sourced (a stray `save-config-value` typed at the prompt would rewrite the user's
config). `config/config.sh:7` (`config_dir=$(dirname $0)`) is also already wrong under sourcing,
`load-config` *executes* the whole config file when we need two scalars, and `load-ssh-key.sh`
currently has zero repo dependencies — `tests/load-ssh-key/test_helper.bash:195-205` sources it
in a bare `bash -c`, which adding a dependency would couple to the repo layout.

## Files

- `load-ssh-key.sh` — main change (new functions, new options, modified `load-ssh-key`, loop fix).
- `load-ssh-key-askpass.sh` — **new**, ~15 lines, the `SSH_ASKPASS` helper, mode 755.
- `README.md` — extend the `### load-ssh-key.sh` section (~lines 349-435).
- `tests/load-ssh-key/unit/test_keepassxc.bats` and
  `tests/load-ssh-key/helpers/keepassxc-helpers.bash` — **new**.
- `tests/load-ssh-key/test_helper.bash` — one edit: `run_load_ssh_key` builds an explicit
  `bash -c` string, so the mock's `PATH` and env must be exported into it.
- `tests/load-ssh-key/README.md`, `tips-and-tricks.md` — doc updates.
- `docs/plans/README.md` — pointer to this document (done).

## Implementation

### 1. New file: `load-ssh-key-askpass.sh` (repo root, mode 755)

Standard repo header (`#!/usr/bin/env bash`, `set -u -o pipefail`, Style Conventions banner) and:

```bash
if [[ -z "${LOAD_SSH_KEY_PASSPHRASE:-}" ]] ; then
    echo "Error: ${script_name}: LOAD_SSH_KEY_PASSPHRASE is not set" >&2
    exit 1
fi

printf '%s\n' "${LOAD_SSH_KEY_PASSPHRASE}"
exit 0
```

The trailing newline is what OpenSSH's `read_passphrase` expects from an askpass program (it
reads one line and strips it). Deliberately **no** getopts/`-h` block: `ssh-add` passes the prompt
text as `$1`, so option parsing here would be actively wrong. Comment that. The helper never logs,
echoes to a tty, or writes to disk.

### 2. `load-ssh-key.sh` — header, defaults, state

After lines 9-10, add a canonical dir (the script is sourced from an arbitrary cwd):

```bash
script_real_dir=$(cd "${script_dir}" 2>/dev/null && pwd) || script_real_dir="${script_dir}"
```

CLI Parameters block — every one reassigned unconditionally on each sourcing, for the same reason
`KEY_LIST` is explicitly `unset` at line 23 (a previous sourcing must not leak in):

```bash
USE_KEEPASS=true
KEEPASS_DB=""
KEEPASS_DB_FROM_CLI=false
KEEPASS_GROUP=""
KEEPASS_CLI=""
PUB_BIN_CONFIG="${HOME}/.config/pub-bin/config"
ASKPASS_HELPER="${script_real_dir}/load-ssh-key-askpass.sh"
```

State-tracking block:

```bash
# KeePassXC runtime state.  kp_db_password / kp_key_passphrase hold secrets and
# are cleared by clear-key-secrets on every exit path (this script is sourced,
# so leftovers would persist in the caller's interactive shell).
KEEPASS_ENABLED=false
keepassxc_cli=""
kp_db_password=""
kp_key_passphrase=""
```

There is **no env override for the DB path or group** — only for the master password (step 4.5),
for testability.

### 3. `usage` (lines 40-65)

Synopsis gains `[-hqlvKN] … [-D <keepass_db>] [-G <keepass_group>]`, and Options gain:

```
  -D <keepass_db>  : KeePassXC .kdbx database used to look up key passphrases
                     (Default: keepassxc_db in ${PUB_BIN_CONFIG})
  -G <group>       : KeePassXC group holding the key entries (Default: database root)
  -N               : No KeePassXC. Prompt interactively for key passphrases.
```

Plus an example. `usage` runs before config resolution, which is why `-D`'s help names the config
key rather than a resolved path.

### 4. New functions (between `is-valid-ssh-key`, ends line 224, and `load-ssh-key`, line 226)

**4.1 `read-pub-bin-config-value <key>`** — `grep` the exact `key="value"` form written by
`config/config.sh:209`, `tail -1`, `cut -d '=' -f 2-`, strip surrounding quotes. Document that only
that simple form is supported. Reading rather than sourcing is the whole point (see above).

**4.2 `find-keepassxc-cli`** — honour an explicit `${KEEPASS_CLI}` (error if not executable), then
`command -v keepassxc-cli`, then probe in order:
`/Applications/KeePassXC.app/Contents/MacOS/keepassxc-cli`,
`${HOME}/Applications/KeePassXC.app/…`, `/opt/homebrew/bin/keepassxc-cli`,
`/usr/local/bin/keepassxc-cli`. Echo the winner; return 1 if none.

**4.3 `key-requires-passphrase <key_file>`**

```bash
    # rc 0 + public key on stdout when the key has no passphrase;
    # rc 255 ("incorrect passphrase supplied") when it does.
    if ssh-keygen -y -P "" -f "${key_file}" >/dev/null 2>&1 ; then
	return 1
    fi
    return 0
```

In-line caveat: an unparseable key also reports "protected". `load-ssh-key` already gates on
`is-valid-ssh-key` (line 240), and the worst case is a pointless lookup followed by today's prompt.

**4.4 `clear-key-secrets`** — assign `""` then `unset`, so the value is overwritten in place
before the name is dropped. Later references use `${kp_db_password:-}` guards for `set -u`.

**4.5 `ensure-keepassxc-unlocked`** — lazy, once per run, 3 attempts:

```bash
    # Non-interactive / test path: single attempt, never prompt.
    if [[ ! -z "${LOAD_SSH_KEY_DB_PASSWORD:-}" ]] ; then
	kp_db_password="${LOAD_SSH_KEY_DB_PASSWORD}"
	if printf '%s\n' "${kp_db_password}" |
	    "${keepassxc_cli}" db-info -q "${KEEPASS_DB}" >/dev/null 2>&1 ; then
	    return 0
	fi
	kp_db_password=""
	KEEPASS_ENABLED=false
	return 1
    fi

    [[ -r /dev/tty ]] || { KEEPASS_ENABLED=false ; return 1 ; }

    while [[ ${attempt} -lt ${max_attempts} ]] ; do
	attempt=$((attempt + 1))
	saved_stty=$(stty -g < /dev/tty 2>/dev/null || echo "")
	# Restore terminal echo if the user interrupts the read
	trap 'stty "${saved_stty}" < /dev/tty 2>/dev/null || stty echo < /dev/tty 2>/dev/null ; trap - INT' INT
	stty -echo < /dev/tty
	echo -n "KeePassXC master password for $(basename "${KEEPASS_DB}"): " >&2
	IFS= read -r entered < /dev/tty || entered=""
	stty echo < /dev/tty
	[[ ! -z "${saved_stty}" ]] && { stty "${saved_stty}" < /dev/tty 2>/dev/null || true ; }
	trap - INT
	echo "" >&2

	if printf '%s\n' "${entered}" |
	    "${keepassxc_cli}" db-info -q "${KEEPASS_DB}" >/dev/null 2>&1 ; then
	    kp_db_password="${entered}"
	    entered=""
	    return 0
	fi
	entered=""
	echo "Error: could not unlock KeePassXC database (attempt ${attempt} of ${max_attempts})" >&2
    done
    # give up: message, KEEPASS_ENABLED=false, clear secrets, fall back
```

Details that matter: `db-info -q` is the only way to separate a bad master password from a missing
entry; reading from `/dev/tty` (not stdin) is mandatory because the caller's stdin may be a pipe
and, after step 7, the loop's stdin is a process substitution; the `INT` trap is installed **and
removed** around the read, because a persistent trap would live on in the user's shell; an empty
entry disables KeePassXC rather than looping.

`LOAD_SSH_KEY_DB_PASSWORD` is the one documented env hook — required to make the feature testable
under bats (no controllable tty) and usable in automation. One attempt, no prompt, no re-prompt;
on failure, fall back. README documents "prefer the tty prompt".

**4.6 `keepassxc-get-passphrase <entry_title>`** — normalize `${KEEPASS_GROUP}` (strip leading and
trailing `/`), build `group/title`, then:

```bash
    # printf is a bash builtin, so the master password never appears in argv.
    # A here-string (<<<) is deliberately NOT used: bash implements it with a
    # temp file, which would write the secret to disk.
    kp_key_passphrase=$(printf '%s\n' "${kp_db_password}" |
	"${keepassxc_cli}" show -q -s -a Password "${KEEPASS_DB}" "${entry_path}" 2>/dev/null || echo "")
```

If empty and a group was set, retry once at the database root (entry filed outside the group).
Empty after that → `return 1`, caller falls back for that key only. Two limitations to document:
command substitution strips trailing newlines, so a passphrase with meaningful trailing whitespace
cannot be handled; an entry with an empty `Password` is indistinguishable from a missing entry.

**4.7 `add-key-with-askpass <key_file> <timeout>`**

```bash
    # The passphrase is a per-command environment assignment: it is set only in
    # ssh-add's environment (and inherited by the askpass child), never exported
    # into the caller's sourced shell.  DISPLAY is set for OpenSSH < 8.4, which
    # ignores SSH_ASKPASS_REQUIRE.  </dev/null keeps ssh-add off the tty.
    SSH_ASKPASS="${ASKPASS_HELPER}" \
	SSH_ASKPASS_REQUIRE=force \
	DISPLAY="${DISPLAY:-:0}" \
	LOAD_SSH_KEY_PASSPHRASE="${kp_key_passphrase}" \
	ssh-add -t "${timeout}" "${key_file}" < /dev/null
```

`ssh-add` is an external command, so the prefix assignments apply to that process only. Never run
`set -x` around this line.

### 5. getopts, config resolution, activation

getopts string → `":t:d:c:k:D:G:hqlvKN"`; `D )` sets `KEEPASS_DB` and `KEEPASS_DB_FROM_CLI=true`,
`G )` sets `KEEPASS_GROUP`, `N )` sets `USE_KEEPASS=false`.

New "KeePassXC configuration" section immediately after `shift $((OPTIND -1))` (so CLI wins) and
before `Validation`: fill any empty `KEEPASS_DB` / `KEEPASS_GROUP` / `KEEPASS_CLI` from
`read-pub-bin-config-value keepassxc_db` / `keepassxc_group` / `keepassxc_cli`, then expand a
leading `~` in `KEEPASS_DB`. Neither key is a secret — only a path and a group name — so the
**public** config (`${HOME}/.config/pub-bin/config`) is the right home and no `${HOME}/.secure`
work is needed.

Activation ladder, in order: `-N` → verbose note; no `KEEPASS_DB` → verbose note; `KEEPASS_DB`
missing on disk → **hard error via `usage` if it came from `-D`** (explicit user intent),
otherwise a warning; `find-keepassxc-cli` fails → warn unless `-q`; askpass helper not executable
→ retry via `command -v load-ssh-key-askpass.sh`, else warn; otherwise `KEEPASS_ENABLED=true`.

This is what keeps the existing bats suite green unchanged: `setup()` sets
`HOME="${TEST_TMPDIR}"`, so the config file is absent and `KEEPASS_DB` stays empty even though
`keepassxc-cli` exists on this machine.

Verbose banner gains `KEEPASS_ENABLED`, `KEEPASS_DB`, `KEEPASS_GROUP`, `keepassxc_cli`,
`ASKPASS_HELPER` in the existing `VAR=[${VAR}]` format — never a secret.

### 6. Rewrite the tail of `load-ssh-key` (replaces lines 267-273)

```bash
    ${QUIET} || echo "Adding SSH key to agent: ${key_basename}" >&2

    if ${KEEPASS_ENABLED} && key-requires-passphrase "${key_file}" ; then
	if keepassxc-get-passphrase "${key_basename}" ; then
	    ${VERBOSE} && echo "Using KeePassXC passphrase for: ${key_basename}" >&2
	    if add-key-with-askpass "${key_file}" "${timeout}" ; then
		kp_key_passphrase=""
		return 0
	    fi
	    kp_key_passphrase=""
	    cat<<EOF >&2
Error: Failed to add key to agent: ${key_file}
The KeePassXC passphrase for entry [${key_basename}] was rejected by ssh-add.
Update the entry, or re-run with -N to type the passphrase.
EOF
	    return 1
	fi
	kp_key_passphrase=""
	${QUIET} || cat<<EOF >&2
No KeePassXC entry found for: ${key_basename}
KEEPASS_GROUP=[${KEEPASS_GROUP}]
Falling back to interactive passphrase prompt.
EOF
    fi

    ssh-add -t "${timeout}" "${key_file}" || {
	echo "Error: Failed to add key to agent: ${key_file}" >&2
	return 1
    }

    return 0
```

Everything above line 267 — existence check, `is-valid-ssh-key`, fingerprint, `is-key-loaded`
short-circuit (line 261) — is unchanged. That short-circuit is what makes the master-password
prompt lazy: already-loaded keys return before anything is asked.

### 7. Loop restructure, `error_count`, cleanup on every exit path

Both load loops are `echo "${KEY_LIST}" | while … done`, so `((error_count++))` (lines 568, 586)
runs in a subshell and `error_count` at line 595 is always 0 — the "Failed to load N key(s)"
report and its `return 1` are dead code (`test_k_option.bats:202-217` documents this as a known
wart). Once passphrases are automated, a silent "entry not in KeePassXC / passphrase rejected"
failure is exactly what the user must be told about, so accurate counting becomes load-bearing.
Convert both to process substitution so the body runs in the current shell:

```bash
    while IFS= read -r key_file ; do
	if [[ -z "${key_file}" ]] ; then
	    continue
	fi
	if ! load-ssh-key "${key_file}" "${KEY_TIMEOUT}" ; then
	    error_count=$((error_count + 1))
	fi
    done < <(echo "${KEY_LIST}")
```

and `done < <(echo "${KEY_LIST}" | tr ',' '\n')` for the `-k` path. Use
`error_count=$((error_count + 1))`, not `((error_count++))`: post-increment from 0 returns exit
status 1, harmless today only because `-e` is off. Running the body in the parent is also what
lets one master-password unlock serve every key and lets the final clear actually clear the
variable the loop used.

Call `clear-key-secrets` before `show-ssh-agent-status` (line 592) and at every `return`/`exit`
site (531, 537, 546, 559, 597, 601, and the new step-5 error path). At most of those no secret
exists yet, but calling it uniformly means a future insertion above them cannot leak. **Because
the script is sourced, this is the only thing standing between the run and a passphrase sitting in
the user's interactive shell for the rest of the day — treat it as the primary security invariant
and assert it in tests.**

Secret-hygiene checklist for review: nothing secret in argv (`printf` builtin + per-command env,
never a `--password` flag); nothing secret on disk (no `<<<`, no here-doc, no `mktemp`); no secret
in any `${VERBOSE} &&` line (only entry paths and key basenames); `stty -g` save/restore with a
scoped `INT` trap; `LOAD_SSH_KEY_PASSPHRASE` exists only in `ssh-add`'s and the helper's
environment; `kp_*` cleared on all paths.

### 8. Error-behavior matrix

| Situation | Behavior |
| --- | --- |
| `keepassxc-cli` absent | KeePassXC off, warn unless `-q`, interactive `ssh-add` (today's behavior). Not an error |
| `keepassxc_db` unset | KeePassXC off, verbose note only. Not an error |
| `keepassxc_db` set but missing | Warning + KeePassXC off; `-D` to a missing path → hard error via `usage` |
| Askpass helper missing | Warning, KeePassXC off |
| Wrong master password | 3 tty attempts (1 with `LOAD_SSH_KEY_DB_PASSWORD`), then message, KeePassXC off for the rest of the run, secrets cleared, keys still load interactively. Never re-prompted later |
| DB open in the KeePassXC GUI | Read-only `show`/`db-info` work fine (they ignore the `.lock`); any failure funnels into the unlock-failure path |
| Entry missing / empty Password | Per-key message + interactive prompt for that key only; KeePassXC stays on for remaining keys |
| Entry found, passphrase stale | `ssh-add` retries the askpass 3× internally, then fails → explicit error, `error_count` incremented, **no** automatic interactive retry (deterministic; cannot hang a non-interactive caller); message points at `-N` |
| Key not passphrase-protected | KeePassXC never consulted, no prompt |
| Key already loaded | Returns at line 261 before anything is asked |
| `-N` given | KeePassXC skipped entirely |

### 9. Tests (`tests/load-ssh-key/`)

New `helpers/keepassxc-helpers.bash`, loaded from `test_helper.bash:36-42` beside the existing
two: `create_mock_keepassxc_cli <master_password> <entry_path>=<passphrase> …` writes a bash stub
into `${TEST_TMPDIR}/mockbin` and prepends it to `PATH`. The stub reads the DB password from stdin,
mimics `-q` silence and `rc=1`, supports `db-info` (password check only) and
`show -q -s -a Password`. `PATH` prepending is sufficient because `find-keepassxc-cli` probes
`command -v keepassxc-cli` first — no code hook needed. Also `create_mock_kdbx()` →
`touch "${TEST_TMPDIR}/test.kdbx"` (only `-e` is checked). One existing-harness edit:
`run_load_ssh_key` (`test_helper.bash:195-205`) builds an explicit `bash -c` string, so the mock's
`PATH`, `MOCK_STATE`, and `LOAD_SSH_KEY_DB_PASSWORD` must be exported into that heredoc.

New `unit/test_keepassxc.bats`:

1. `-h` lists `-D`, `-G`, `-N`; `bash -n` clean for both scripts.
2. No mock, no config → unprotected key loads, success, output contains no KeePassXC strings
   (regression guard for "no behavior change when not configured").
3. **Headline test:** mock + `-D ${kdbx}` + `LOAD_SSH_KEY_DB_PASSWORD` + a protected key from
   `create_test_ssh_key "k" "testpass123"` → success, `-l` shows 1 key, output contains
   `Using KeePassXC passphrase`. Must pass with **no tty and no stdin**.
4. `-G ssh-keys` with the entry filed as `ssh-keys/<basename>` → success; and the root-retry path
   (entry filed bare while `-G` set) → success.
5. Entry missing → `No KeePassXC entry found for`, interactive fallback fails fast (`< /dev/null`),
   `error_count` propagates → status 1. Also proves the step-7 loop fix.
6. Wrong `LOAD_SSH_KEY_DB_PASSWORD` → `did not unlock` + `Falling back to interactive`, no hang
   (wrap in `timeout 10`), and an unprotected key in the same run still loads.
7. Secret hygiene: case 3 with `-v`, `assert_output_not_contains "testpass123"` and the master.
8. Sourced-shell hygiene: `bash -c 'source load-ssh-key.sh -D … ; echo "[${kp_db_password:-UNSET}]" ; echo "[${kp_key_passphrase:-UNSET}]" ; env | grep -c LOAD_SSH_KEY_PASSPHRASE || true'`
   → both `UNSET`, count 0.
9. Askpass helper in isolation: `LOAD_SSH_KEY_PASSPHRASE=abc123` prints `abc123`, rc 0; unset →
   rc 1 with an error on stderr.
10. `-N` with a working mock → KeePassXC never invoked.

Existing suite passes unchanged (HOME is redirected, so the feature auto-disables). One thing to
re-check after the loop fix: `test_k_option.bats:202-217` currently *warns* when the script returns
0 for a nonexistent key; with `error_count` propagating, that path returns 1, so the warning branch
stops firing — assertions still hold, but note the change in the test-suite README.

### 10. Documentation

1. `README.md` (~349-435): add `-D`/`-G`/`-N` to Options; a **KeePassXC passphrase integration**
   subsection covering the entry-title-equals-key-basename convention, the optional group (e.g.
   `ssh-keys/<key-basename>`), the `keepassxc_db` / `keepassxc_group` / `keepassxc_cli` config keys
   with a sample config snippet, the one-prompt-per-run + `stty -echo` model, the full fallback
   matrix, the `LOAD_SSH_KEY_DB_PASSWORD` hook with its caveat, a note that each protected key
   costs one DB unlock (Argon2, ~1s), and the trailing-whitespace-in-passphrase limitation. List
   `load-ssh-key-askpass.sh` as a helper that is never run by hand, and note the corrected error
   reporting.
2. `tests/load-ssh-key/README.md`: add the new bats file and helper to the structure tree plus a
   "mocking keepassxc-cli" paragraph.
3. `tips-and-tricks.md` "SSH Key Usage Pitfalls": one line on `SSH_ASKPASS_REQUIRE=force` needing
   OpenSSH ≥ 8.4, and on `ps -E` not exposing other processes' env on macOS.

## Suggested commit sequencing

1. `load-ssh-key-askpass.sh` + its unit test (self-contained, no behavior change).
2. Loop fix + `error_count` propagation + `clear-key-secrets` scaffolding (pre-existing-bug fix,
   reviewable on its own).
3. KeePassXC functions + getopts/config/activation + the `load-ssh-key` branch.
4. Tests + mock helpers.
5. Docs.

## Verification

1. `tests/load-ssh-key/run-tests.sh` — full suite, including the new `test_keepassxc.bats`.
2. `SSH_KEY_PASSPHRASE`-free helper check: `LOAD_SSH_KEY_PASSPHRASE=abc ./load-ssh-key-askpass.sh "prompt"`
   prints `abc`; unset → exit 1.
3. Real end-to-end (manual; needs a KeePassXC entry titled with the key's basename and
   `keepassxc_db` set in `${HOME}/.config/pub-bin/config`):
   ```bash
   . ./load-ssh-key.sh -K -v          # kill agent, reload; expect ONE master-password prompt
   ssh-add -l                         # key present
   ssh -T git@<host>                  # agent actually authenticates
   ```
4. Fallback intact — `. ./load-ssh-key.sh -K -N`, and a run with `keepassxc_db` unset, behave
   exactly as before.
5. No leaks — after a successful sourced run,
   `set | grep -i -e passphrase -e kp_db_password -e kp_key_passphrase` shows no secret value, and
   `env | grep LOAD_SSH_KEY_PASSPHRASE` is empty.
6. Standards — `bash -n` on both scripts, `shellcheck` if available, `./check-ai-readmes.sh`, no
   trailing whitespace, files end with a newline.
