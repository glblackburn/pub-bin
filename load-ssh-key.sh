#!/usr/bin/env bash
# Note: This script is designed to be sourced, not executed directly
# Usage: . ./load-ssh-key.sh [options]
# or:    source ./load-ssh-key.sh [options]

# Use set -u and -o pipefail, but not -e since script is sourced
set -u -o pipefail

script_name=$(basename ${BASH_SOURCE[0]})
script_dir=$(dirname ${BASH_SOURCE[0]})
# Canonical dir is needed because the script is sourced from an arbitrary cwd
script_real_dir=$(cd "${script_dir}" 2>/dev/null && pwd) || script_real_dir="${script_dir}"

################################################################################
# Style Conventions
################################################################################
# - Use ${variable} braces for all variable references
# - Use ${HOME} instead of ~
# - Use $(command) instead of backticks for command substitution
################################################################################

################################################################################
# CLI Parameters
################################################################################
QUIET=false
VERBOSE=false
KILL_AGENT=false
LIST_KEYS=false
KEY_TIMEOUT=28800
SSH_DIR="${HOME}/.ssh"
CONFIG="${SSH_DIR}/ssh-agent.config"
# KeePassXC passphrase lookup.  Every value is reassigned unconditionally on each
# sourcing so a previous sourcing cannot leak into this run.
USE_KEEPASS=true
KEEPASS_DB=""
KEEPASS_DB_FROM_CLI=false
KEEPASS_GROUP=""
KEEPASS_CLI=""
PUB_BIN_CONFIG="${HOME}/.config/pub-bin/config"
ASKPASS_HELPER="${script_real_dir}/load-ssh-key-askpass.sh"
# Reset KEY_LIST to ensure clean state when script is sourced multiple times
unset KEY_LIST
KEY_LIST=""

################################################################################
# State tracking
################################################################################
error_count=0
# KeePassXC runtime state.  kp_db_password / kp_key_passphrase hold secrets and
# are cleared by clear-key-secrets on every exit path (this script is sourced,
# so leftovers would persist in the caller's interactive shell).
KEEPASS_ENABLED=false
keepassxc_cli=""
kp_db_password=""
kp_key_passphrase=""

################################################################################
# Functions
################################################################################
function usage {
    local message=${1:-}
    if [[ ! -z "${message}" ]] ; then
	echo "Error: ${message}" >&2
	echo "" >&2
    fi
    cat<<EOF
Usage: . ${script_name} [-hqlvKN] [-t <timeout>] [-d <ssh_dir>] [-c <config>] [-k <key_list>]
       [-D <keepass_db>] [-G <keepass_group>]

Load SSH keys from ~/.ssh into the SSH agent. This script must be sourced
(using . or source) to load the SSH agent environment variables into your
current shell session.

Note: The -l option can be used when executed directly (without sourcing).

Options
  -h               : Display this help message.
  -t <timeout>     : Key timeout in seconds (Default: ${KEY_TIMEOUT})
  -d <dir>         : SSH directory to search for keys (Default: ${SSH_DIR})
  -c <config>      : SSH agent config file path (Default: ${CONFIG})
  -k <key_list>    : Comma-separated list of specific keys to load (Default: auto-detect all)
  -D <keepass_db>  : KeePassXC .kdbx database used to look up key passphrases
                     (Default: keepassxc_db in ${PUB_BIN_CONFIG})
  -G <group>       : KeePassXC group holding the key entries (Default: database root)
  -N               : No KeePassXC. Prompt interactively for key passphrases.
  -K               : Kill current SSH agent and start a new one
  -l               : List currently loaded SSH keys and exit
  -q               : Quiet mode. Output as little as possible.
  -v               : Verbose output. Show detailed information (never prints secrets).

KeePassXC passphrase lookup is used automatically when keepassxc-cli and a
database are available. Each KeePassXC entry title must match the private key
file name; the master password is prompted for once per run. Without KeePassXC
the script falls back to ssh-add prompting for each passphrase.

Example:
. ${script_name} -t 3600
. ${script_name} -K  # Kill current agent and reload all keys
. ${script_name} -l  # List currently loaded keys
. ${script_name} -D ${HOME}/keepassxc.kdbx -G ssh-keys
. ${script_name} -N  # Skip KeePassXC, type passphrases interactively
${script_name} -l    # List keys (can be executed directly)
EOF
}

function start-ssh-agent {
    local config_file=$1

    ${VERBOSE} && echo "Starting SSH agent..." >&2
    ssh-agent > "${config_file}" || {
	echo "Error: Failed to start SSH agent" >&2
	return 1
    }
    ${VERBOSE} && echo "Loading agent config" >&2
    . "${config_file}" || {
	echo "Error: Failed to load agent config" >&2
	return 1
    }
}

function check-ssh-agent-running {
    local agent_pid=${SSH_AGENT_PID:-}
    local ps_check=""
    local ps_count=0

    if [[ -z "${agent_pid}" ]] ; then
	return 1
    fi

    ps_check=$(ps -fe | grep " ${agent_pid} " | grep ssh-agent || true)
    ps_count=$(echo "${ps_check}" | grep -v '^$' | wc -l | tr -d ' ')

    ${VERBOSE} && echo "PS_CHECK=[${ps_check}]" >&2
    ${VERBOSE} && echo "PS_COUNT=[${ps_count}]" >&2

    if [[ "${ps_count}" -eq 1 ]] ; then
	return 0
    else
	return 1
    fi
}

function kill-ssh-agent {
    local agent_pid=${SSH_AGENT_PID:-}
    local max_wait=5
    local wait_count=0

    # Remove the config file first to prevent reloading
    if [[ -e "${CONFIG}" ]] ; then
	${VERBOSE} && echo "Removing SSH agent config file: ${CONFIG}" >&2
	rm -f "${CONFIG}" 2>/dev/null || true
    fi

    if [[ -z "${agent_pid}" ]] ; then
	${VERBOSE} && echo "No SSH agent PID found in environment" >&2
	# Still try to find and kill any ssh-agent processes
	local all_agents=""
	all_agents=$(ps -fe | grep "[s]sh-agent" | awk '{print $2}' || echo "")
	if [[ ! -z "${all_agents}" ]] ; then
	    ${QUIET} || echo "Found ssh-agent processes, killing them" >&2
	    echo "${all_agents}" | while read pid ; do
		[[ ! -z "${pid}" ]] && kill "${pid}" 2>/dev/null || true
	    done
	    sleep 1
	fi
	unset SSH_AGENT_PID
	unset SSH_AUTH_SOCK
	return 0
    fi

    # Try to kill the agent, even if check says it's not running
    # (the check might be wrong if the socket is stale)
    ${QUIET} || echo "Killing SSH agent (PID: ${agent_pid})" >&2
    if ps -p "${agent_pid}" >/dev/null 2>&1 ; then
	kill "${agent_pid}" 2>/dev/null || {
	    ${VERBOSE} && echo "Warning: Failed to kill SSH agent PID ${agent_pid}" >&2
	}
    else
	${VERBOSE} && echo "SSH agent PID ${agent_pid} is not running" >&2
    fi

    # Wait for the agent to actually terminate
    wait_count=0
    while [[ ${wait_count} -lt ${max_wait} ]] ; do
	if ! ps -p "${agent_pid}" >/dev/null 2>&1 ; then
	    break
	fi
	sleep 0.5
	((wait_count++))
    done

    # Force kill if still running
    if ps -p "${agent_pid}" >/dev/null 2>&1 ; then
	${VERBOSE} && echo "Agent still running, force killing (PID: ${agent_pid})" >&2
	kill -9 "${agent_pid}" 2>/dev/null || true
	sleep 0.5
    fi

    # Unset the environment variables
    unset SSH_AGENT_PID
    unset SSH_AUTH_SOCK

    return 0
}

function find-ssh-keys {
    local ssh_dir=$1
    local key_list=""

    if [[ ! -d "${ssh_dir}" ]] ; then
	echo "Error: SSH directory does not exist: ${ssh_dir}" >&2
	return 1
    fi

    key_list=$(find "${ssh_dir}" -type f \
	-not -name "*.pub" \
	-not -name "known_hosts*" \
	-not -name "ssh-agent.config" \
	-not -name "config" \
	-not -name "config~" \
	-not -name "authorized_keys" \
	-not -path "*/ssh-copy-id.*/*" 2>/dev/null)

    echo "${key_list}"
}

function get-key-fingerprint {
    local key_file=$1
    local fingerprint=""

    fingerprint=$(ssh-keygen -l -E sha256 -f "${key_file}" 2>/dev/null | awk '{print $2}' || echo "")
    echo "${fingerprint}"
}

function get-agent-key-list {
    # Single place that asks the agent what it holds.  ssh-add -l exits 1 and
    # prints "The agent has no identities." for an empty agent, so callers must
    # look for SHA256: lines rather than trusting the exit code or line count.
    ssh-add -l 2>/dev/null || true
}

function count-lines-matching {
    # Count matching lines from stdin.  grep -c exits 1 when the count is zero
    # and still prints "0", so the status is swallowed rather than replaced with
    # a second "0" - which would make the caller compare "0\n0" as a number.
    local pattern=$1
    local count=""

    count=$(grep -c -- "${pattern}" 2>/dev/null || true)
    count=$(echo "${count}" | tr -d '[:space:]')

    echo "${count:-0}"
}

function count-agent-keys {
    local loaded_keys=$1

    echo "${loaded_keys}" | count-lines-matching "SHA256:"
}

function is-key-loaded {
    local fingerprint=$1
    local key_count=0

    key_count=$(get-agent-key-list | count-lines-matching "${fingerprint}")

    if [[ "${key_count}" -ge 1 ]] ; then
	return 0
    else
	return 1
    fi
}

function is-valid-ssh-key {
    local key_file=$1

    # A file is a key exactly when a fingerprint can be read from it
    if [[ -z "$(get-key-fingerprint "${key_file}")" ]] ; then
	return 1
    else
	return 0
    fi
}

function read-pub-bin-config-value {
    local key=$1
    local value=""

    if [[ ! -e "${PUB_BIN_CONFIG}" ]] ; then
	echo ""
	return 0
    fi

    # Only the simple key="value" form written by config/config.sh is supported.
    # Read with grep instead of sourcing: this script is sourced into the user's
    # interactive shell and must not execute or export the whole config file.
    value=$(grep -E "^[[:space:]]*${key}=" "${PUB_BIN_CONFIG}" 2>/dev/null \
	| tail -1 \
	| cut -d '=' -f 2- \
	| sed -e 's/^"//' -e 's/"$//' || echo "")

    echo "${value}"
}

function find-keepassxc-cli {
    local candidate=""
    local candidates=""

    if [[ ! -z "${KEEPASS_CLI}" ]] ; then
	if [[ -x "${KEEPASS_CLI}" ]] ; then
	    echo "${KEEPASS_CLI}"
	    return 0
	fi
	echo "Error: keepassxc_cli is not executable: ${KEEPASS_CLI}" >&2
	return 1
    fi

    candidate=$(command -v keepassxc-cli 2>/dev/null || echo "")
    if [[ ! -z "${candidate}" ]] ; then
	echo "${candidate}"
	return 0
    fi

    # keepassxc-cli ships inside the macOS app bundle and is not on PATH
    candidates="/Applications/KeePassXC.app/Contents/MacOS/keepassxc-cli
${HOME}/Applications/KeePassXC.app/Contents/MacOS/keepassxc-cli
/opt/homebrew/bin/keepassxc-cli
/usr/local/bin/keepassxc-cli"

    while IFS= read -r candidate ; do
	if [[ -x "${candidate}" ]] ; then
	    echo "${candidate}"
	    return 0
	fi
    done < <(echo "${candidates}")

    return 1
}

function key-requires-passphrase {
    local key_file=$1

    # rc 0 (plus the public key on stdout) when the key has no passphrase;
    # rc 255 ("incorrect passphrase supplied") when it does.  A key ssh-keygen
    # cannot parse also reports "protected" here; load-ssh-key already gates on
    # is-valid-ssh-key, so the worst case is a pointless KeePassXC lookup
    # followed by the normal interactive prompt.
    if ssh-keygen -y -P "" -f "${key_file}" >/dev/null 2>&1 ; then
	return 1
    fi

    return 0
}

function clear-key-secrets {
    # Overwrite before dropping the names.  This script is sourced, so a secret
    # left behind would live in the caller's interactive shell.
    kp_db_password=""
    kp_key_passphrase=""
    unset kp_db_password
    unset kp_key_passphrase

    return 0
}

function ensure-keepassxc-unlocked {
    local max_attempts=3
    local attempt=0
    local saved_stty=""
    local entered=""

    ${KEEPASS_ENABLED} || return 1
    if [[ ! -z "${kp_db_password:-}" ]] ; then
	return 0
    fi

    # db-info is the only reliable master-password check: with -q, keepassxc-cli
    # is silent and returns 1 for both a bad password and a missing entry, so a
    # per-entry failure cannot be classified unless the password is known good.
    if [[ ! -z "${LOAD_SSH_KEY_DB_PASSWORD:-}" ]] ; then
	# Non-interactive path (tests, automation): one attempt, never prompt
	kp_db_password="${LOAD_SSH_KEY_DB_PASSWORD}"
	if printf '%s\n' "${kp_db_password}" \
	    | "${keepassxc_cli}" db-info -q "${KEEPASS_DB}" >/dev/null 2>&1 ; then
	    ${VERBOSE} && echo "KeePassXC unlocked using LOAD_SSH_KEY_DB_PASSWORD" >&2
	    return 0
	fi
	kp_db_password=""
	cat<<EOF >&2
Error: LOAD_SSH_KEY_DB_PASSWORD did not unlock the KeePassXC database
KEEPASS_DB=[${KEEPASS_DB}]
Falling back to interactive ssh-add passphrase prompts.
EOF
	KEEPASS_ENABLED=false
	return 1
    fi

    if [[ ! -r /dev/tty ]] ; then
	${VERBOSE} && echo "No /dev/tty available for the KeePassXC prompt" >&2
	KEEPASS_ENABLED=false
	return 1
    fi

    while [[ ${attempt} -lt ${max_attempts} ]] ; do
	attempt=$((attempt + 1))
	saved_stty=$(stty -g < /dev/tty 2>/dev/null || echo "")
	# Restore terminal echo if the read is interrupted.  The trap is removed
	# again below: a lingering trap would live on in the caller's shell.
	trap 'stty "${saved_stty}" < /dev/tty 2>/dev/null || stty echo < /dev/tty 2>/dev/null ; trap - INT' INT
	stty -echo < /dev/tty
	echo -n "KeePassXC master password for $(basename "${KEEPASS_DB}"): " >&2
	IFS= read -r entered < /dev/tty || entered=""
	stty echo < /dev/tty
	if [[ ! -z "${saved_stty}" ]] ; then
	    stty "${saved_stty}" < /dev/tty 2>/dev/null || true
	fi
	trap - INT
	echo "" >&2

	if [[ -z "${entered}" ]] ; then
	    echo "Empty password entered; skipping KeePassXC lookups" >&2
	    KEEPASS_ENABLED=false
	    return 1
	fi

	if printf '%s\n' "${entered}" \
	    | "${keepassxc_cli}" db-info -q "${KEEPASS_DB}" >/dev/null 2>&1 ; then
	    kp_db_password="${entered}"
	    entered=""
	    ${VERBOSE} && echo "KeePassXC database unlocked" >&2
	    return 0
	fi

	entered=""
	echo "Error: could not unlock KeePassXC database (attempt ${attempt} of ${max_attempts})" >&2
    done

    cat<<EOF >&2
Error: KeePassXC database could not be unlocked after ${max_attempts} attempts
KEEPASS_DB=[${KEEPASS_DB}]
Falling back to interactive ssh-add passphrase prompts.
EOF
    KEEPASS_ENABLED=false
    clear-key-secrets
    kp_db_password=""
    kp_key_passphrase=""

    return 1
}

function keepassxc-get-passphrase {
    local entry_title=$1
    local group=""
    local entry_path=""

    kp_key_passphrase=""

    ensure-keepassxc-unlocked || return 1

    group="${KEEPASS_GROUP}"
    group="${group#/}"
    group="${group%/}"
    entry_path="${entry_title}"
    if [[ ! -z "${group}" ]] ; then
	entry_path="${group}/${entry_title}"
    fi

    ${VERBOSE} && echo "KeePassXC lookup: entry_path=[${entry_path}]" >&2

    # printf is a bash builtin, so the master password never appears in argv.
    # A here-string (<<<) is deliberately NOT used: bash implements it with a
    # temp file, which would write the secret to disk.
    kp_key_passphrase=$(printf '%s\n' "${kp_db_password}" \
	| "${keepassxc_cli}" show -q -s -a Password "${KEEPASS_DB}" "${entry_path}" 2>/dev/null \
	|| echo "")

    if [[ -z "${kp_key_passphrase}" ]] && [[ ! -z "${group}" ]] ; then
	# Retry at the database root in case the entry is not filed in the group
	${VERBOSE} && echo "KeePassXC lookup: retrying entry_path=[${entry_title}]" >&2
	kp_key_passphrase=$(printf '%s\n' "${kp_db_password}" \
	    | "${keepassxc_cli}" show -q -s -a Password "${KEEPASS_DB}" "${entry_title}" 2>/dev/null \
	    || echo "")
    fi

    if [[ -z "${kp_key_passphrase}" ]] ; then
	kp_key_passphrase=""
	return 1
    fi

    return 0
}

function add-key-with-askpass {
    local key_file=$1
    local timeout=$2

    if [[ ! -x "${ASKPASS_HELPER}" ]] ; then
	echo "Error: askpass helper is not executable: ${ASKPASS_HELPER}" >&2
	return 1
    fi

    # The passphrase is a per-command environment assignment: it is set only in
    # ssh-add's environment (and inherited by the askpass child), never exported
    # into the caller's sourced shell.  DISPLAY is set for OpenSSH < 8.4, which
    # ignores SSH_ASKPASS_REQUIRE.  </dev/null keeps ssh-add off the tty.
    SSH_ASKPASS="${ASKPASS_HELPER}" \
	SSH_ASKPASS_REQUIRE=force \
	DISPLAY="${DISPLAY:-:0}" \
	LOAD_SSH_KEY_PASSPHRASE="${kp_key_passphrase}" \
	ssh-add -t "${timeout}" "${key_file}" < /dev/null
}

function find-key-file-by-fingerprint {
    local fingerprint=$1
    local candidate=""
    local candidate_fingerprint=""

    if [[ -z "${fingerprint}" ]] || [[ ! -d "${SSH_DIR}" ]] ; then
	echo ""
	return 1
    fi

    while IFS= read -r candidate ; do
	if [[ -z "${candidate}" ]] ; then
	    continue
	fi
	candidate_fingerprint=$(get-key-fingerprint "${candidate}")
	if [[ "${candidate_fingerprint}" == "${fingerprint}" ]] ; then
	    # Report the path relative to SSH_DIR so keys in subdirectories stay
	    # distinguishable without printing the whole path
	    echo "${candidate#${SSH_DIR}/}"
	    return 0
	fi
    done < <(find-ssh-keys "${SSH_DIR}" 2>/dev/null)

    echo ""
    return 1
}

function load-ssh-key {
    local key_file=$1
    local timeout=$2
    local fingerprint=""
    local key_basename=""

    key_basename=$(basename "${key_file}")

    if [[ ! -e "${key_file}" ]] ; then
	echo "Error: Key file does not exist: ${key_file}" >&2
	return 1
    fi

    # One fingerprint read doubles as the "is this really a key?" check
    fingerprint=$(get-key-fingerprint "${key_file}")
    if [[ -z "${fingerprint}" ]] ; then
	${VERBOSE} && echo "Skipping non-key file: ${key_file}" >&2
	return 0  # Return success - not an error, just skip it
    fi

    ${VERBOSE} && cat<<EOF >&2
key_file=[${key_file}]
KEY_CHECK=[${fingerprint}]
EOF

    # The agent contents are reported once at the end of the run by
    # show-loaded-keys, not after every individual key.
    if is-key-loaded "${fingerprint}" ; then
	${QUIET} || echo "Key already loaded: ${key_basename}" >&2
	return 0
    fi

    ${VERBOSE} && echo "Key not in agent yet: ${key_basename}" >&2

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
}

function show-ssh-agent-status {
    ${VERBOSE} && cat<<EOF
Only one ssh-agent should be running
SSH_AGENT_PID=[${SSH_AGENT_PID:-}]
EOF

    ${VERBOSE} && echo "SSH agents:" >&2
    ${VERBOSE} && ps -fe | grep -e ssh-agent -e "PID" >&2 || true
}

function resolve-agent-env {
    local possible_sockets=""
    local agent_pids=""

    # A dead agent in the environment is worse than none at all
    if [[ ! -z "${SSH_AUTH_SOCK:-}" ]] && [[ ! -z "${SSH_AGENT_PID:-}" ]] ; then
	if ! ps -p "${SSH_AGENT_PID}" >/dev/null 2>&1 ; then
	    unset SSH_AUTH_SOCK
	    unset SSH_AGENT_PID
	fi
    fi

    # Fall back to the agent config file.  Sourcing it is what the main flow
    # does; the file exports the variables itself, so this works whether the
    # script was sourced or executed directly.
    if [[ -z "${SSH_AUTH_SOCK:-}" ]] && [[ -e "${CONFIG}" ]] ; then
	. "${CONFIG}" >/dev/null 2>&1 || true
    fi

    # Last resort: look for an orphaned agent socket on disk
    if [[ -z "${SSH_AUTH_SOCK:-}" ]] ; then
	possible_sockets=$(find /tmp /var/folders -name "agent.*" -user $(id -u) 2>/dev/null | head -1 || echo "")
	if [[ ! -z "${possible_sockets}" ]] ; then
	    export SSH_AUTH_SOCK="${possible_sockets}"
	    agent_pids=$(ps -fe | grep "[s]sh-agent" | awk '{print $2}' | head -1 || echo "")
	    if [[ ! -z "${agent_pids}" ]] ; then
		export SSH_AGENT_PID="${agent_pids}"
	    fi
	fi
    fi

    if ! check-ssh-agent-running ; then
	return 1
    fi

    return 0
}

function show-loaded-keys {
    local loaded_keys=""
    local key_count=0
    local key_line=""
    local key_fingerprint=""
    local key_file=""

    loaded_keys=$(get-agent-key-list)
    key_count=$(count-agent-keys "${loaded_keys}")

    if [[ "${key_count}" -eq 0 ]] ; then
	echo "No SSH keys are currently loaded in the agent" >&2
	return 0
    fi

    # ssh-add -l reports each key's comment, which is often identical across
    # keys, so map every fingerprint back to the file it came from.  The file
    # name is appended rather than prefixed so the ssh-add columns stay aligned.
    echo "Currently loaded SSH keys (${key_count}) in ${SSH_DIR}:" >&2
    while IFS= read -r key_line ; do
	if [[ "${key_line}" != *SHA256:* ]] ; then
	    continue
	fi
	key_fingerprint=$(echo "${key_line}" | awk '{print $2}')
	key_file=$(find-key-file-by-fingerprint "${key_fingerprint}") || key_file=""
	if [[ -z "${key_file}" ]] ; then
	    key_file="<unknown key file>"
	fi
	echo "${key_line} : ${key_file}"
    done < <(echo "${loaded_keys}")

    return 0
}

function list-loaded-keys {
    # -l entry point: find an agent to talk to, then print what it holds
    if ! resolve-agent-env ; then
	echo "SSH agent is not running" >&2
	return 1
    fi

    show-loaded-keys
}


################################################################################
# get command line options
################################################################################
# Reset OPTIND in case script is sourced multiple times
OPTIND=1
while getopts ":t:d:c:k:D:G:hqlvKN" opt; do
    case ${opt} in
	t )
            KEY_TIMEOUT=$OPTARG
            ;;
	d )
            SSH_DIR=$OPTARG
            CONFIG="${SSH_DIR}/ssh-agent.config"
            ;;
	c )
            CONFIG=$OPTARG
            ;;
	k )
            KEY_LIST=$OPTARG
            ${VERBOSE} && echo "DEBUG: -k option parsed, KEY_LIST set to: [${KEY_LIST}]" >&2
            ;;
	D )
            KEEPASS_DB=$OPTARG
            KEEPASS_DB_FROM_CLI=true
            ;;
	G )
            KEEPASS_GROUP=$OPTARG
            ;;
	N )
            USE_KEEPASS=false
            ;;
	K )
            KILL_AGENT=true
            ;;
	q )
            QUIET=true
            ;;
	l )
            LIST_KEYS=true
            ;;
	v )
            VERBOSE=true
            ;;
	h )
            usage
            return 0 2>/dev/null || exit 0
            ;;
	\? )
            usage "Invalid Option: -$OPTARG"
            return 1 2>/dev/null || exit 1
            ;;
    esac
done
shift $((OPTIND -1))

################################################################################
# KeePassXC configuration
################################################################################
# CLI options win over the config file.  Neither the database path nor the group
# name is a secret, so both live in the public pub-bin config.
if [[ -z "${KEEPASS_DB}" ]] ; then
    KEEPASS_DB=$(read-pub-bin-config-value keepassxc_db)
fi
if [[ -z "${KEEPASS_GROUP}" ]] ; then
    KEEPASS_GROUP=$(read-pub-bin-config-value keepassxc_group)
fi
if [[ -z "${KEEPASS_CLI}" ]] ; then
    KEEPASS_CLI=$(read-pub-bin-config-value keepassxc_cli)
fi
KEEPASS_DB="${KEEPASS_DB/#\~/${HOME}}"

# Activate KeePassXC only when everything it needs is present.  Every other case
# falls back to ssh-add prompting interactively, which is the historic behavior.
if ! ${USE_KEEPASS} ; then
    ${VERBOSE} && echo "KeePassXC disabled by -N" >&2
elif [[ -z "${KEEPASS_DB}" ]] ; then
    ${VERBOSE} && echo "KeePassXC not configured (keepassxc_db unset)" >&2
elif [[ ! -e "${KEEPASS_DB}" ]] ; then
    if ${KEEPASS_DB_FROM_CLI} ; then
	usage "KeePassXC database does not exist: ${KEEPASS_DB}"
	return 1 2>/dev/null || exit 1
    fi
    echo "Warning: keepassxc_db does not exist: ${KEEPASS_DB}" >&2
elif ! keepassxc_cli=$(find-keepassxc-cli) ; then
    ${QUIET} || echo "Warning: keepassxc-cli not found; passphrases will be prompted for" >&2
elif [[ ! -x "${ASKPASS_HELPER}" ]] ; then
    # Repo root is on PATH via setup-path.sh, so try that before giving up
    ASKPASS_HELPER=$(command -v load-ssh-key-askpass.sh 2>/dev/null || echo "")
    if [[ -x "${ASKPASS_HELPER}" ]] ; then
	KEEPASS_ENABLED=true
    else
	${QUIET} || echo "Warning: load-ssh-key-askpass.sh not found; passphrases will be prompted for" >&2
    fi
else
    KEEPASS_ENABLED=true
fi

################################################################################
# Validation
################################################################################
if [[ -z "${KEY_TIMEOUT}" ]] || [[ "${KEY_TIMEOUT}" -le 0 ]] ; then
    usage "KEY_TIMEOUT must be a positive number"
    return 1 2>/dev/null || exit 1
fi

################################################################################
# Main script logic
################################################################################

${VERBOSE} && cat<<EOF
================================================================================
SSH Key Loader
================================================================================
KEY_TIMEOUT=[${KEY_TIMEOUT}]
CONFIG=[${CONFIG}]
SSH_DIR=[${SSH_DIR}]
KILL_AGENT=[${KILL_AGENT}]
KEEPASS_ENABLED=[${KEEPASS_ENABLED}]
KEEPASS_DB=[${KEEPASS_DB}]
KEEPASS_GROUP=[${KEEPASS_GROUP}]
keepassxc_cli=[${keepassxc_cli}]
ASKPASS_HELPER=[${ASKPASS_HELPER}]
================================================================================
EOF

# List keys and exit if requested (can work when executed directly)
if [[ "${LIST_KEYS}" == true ]] ; then
    list-loaded-keys
    list_exit_code=$?
    # When sourced, return works. When executed, exit works.
    if [[ "${BASH_SOURCE[0]}" == "${0}" ]] ; then
	exit ${list_exit_code}
    else
	return ${list_exit_code}
    fi
else

# Check if script is being sourced (required for all other operations)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]] ; then
    cat<<EOF >&2
Warning: This script should be sourced, not executed directly.
Usage: . ${script_name} [options]
or:    source ${script_name} [options]

Note: The -l option can be used when executed directly.
EOF
    exit 1
fi

# Kill current agent if requested
if [[ "${KILL_AGENT}" == true ]] ; then
    # Load config first to get current agent PID if it exists
    old_agent_pid=""
    old_auth_sock=""
    if [[ -e "${CONFIG}" ]] ; then
	. "${CONFIG}" 2>/dev/null || true
	old_agent_pid="${SSH_AGENT_PID:-}"
	old_auth_sock="${SSH_AUTH_SOCK:-}"
    fi
    kill-ssh-agent
    # Ensure environment variables are unset in this scope
    unset SSH_AGENT_PID
    unset SSH_AUTH_SOCK
    # Also kill any other ssh-agent processes that might be running
    # (kill-ssh-agent should have killed the one from config, but kill all to be sure)
    all_agents=""
    all_agents=$(ps -fe | grep "[s]sh-agent" | awk '{print $2}' || echo "")
    if [[ ! -z "${all_agents}" ]] ; then
	${QUIET} || echo "Killing all remaining ssh-agent processes" >&2
	# Collect PIDs into array to avoid subshell issues
	pids_to_kill=()
	while IFS= read -r pid ; do
	    [[ ! -z "${pid}" ]] && pids_to_kill+=("${pid}")
	done <<< "${all_agents}"
	
	# Kill all processes
	for pid in "${pids_to_kill[@]}" ; do
	    ${VERBOSE} && echo "Killing ssh-agent PID: ${pid}" >&2
	    kill "${pid}" 2>/dev/null || true
	done
	sleep 1
	
	# Force kill any that are still running
	all_agents=$(ps -fe | grep "[s]sh-agent" | awk '{print $2}' || echo "")
	if [[ ! -z "${all_agents}" ]] ; then
	    ${QUIET} || echo "Force killing remaining ssh-agent processes" >&2
	    pids_to_kill=()
	    while IFS= read -r pid ; do
		[[ ! -z "${pid}" ]] && pids_to_kill+=("${pid}")
	    done <<< "${all_agents}"
	    
	    for pid in "${pids_to_kill[@]}" ; do
		${VERBOSE} && echo "Force killing ssh-agent PID: ${pid}" >&2
		kill -9 "${pid}" 2>/dev/null || true
	    done
	    sleep 1
	fi
    fi
    
    # Poll until all ssh-agent processes are actually gone (with timeout)
    max_wait=5
    wait_count=0
    while [[ ${wait_count} -lt ${max_wait} ]] ; do
	all_agents=$(ps -fe | grep "[s]sh-agent" | awk '{print $2}' || echo "")
	if [[ -z "${all_agents}" ]] ; then
	    break
	fi
	sleep 0.5
	((wait_count++))
    done
    
    # Final check - if any remain, try one more force kill
    all_agents=$(ps -fe | grep "[s]sh-agent" | awk '{print $2}' || echo "")
    if [[ ! -z "${all_agents}" ]] ; then
	${VERBOSE} && echo "Final cleanup: force killing any remaining ssh-agent processes" >&2
	pids_to_kill=()
	while IFS= read -r pid ; do
	    [[ ! -z "${pid}" ]] && pids_to_kill+=("${pid}")
	done <<< "${all_agents}"
	
	for pid in "${pids_to_kill[@]}" ; do
	    kill -9 "${pid}" 2>/dev/null || true
	done
	sleep 1
    fi
fi

# Load or start SSH agent
if [[ -e "${CONFIG}" ]] && [[ "${KILL_AGENT}" != true ]] ; then
    ${VERBOSE} && echo "Loading agent config" >&2
    . "${CONFIG}" || {
	echo "Error: Failed to load agent config" >&2
	return 1 2>/dev/null || exit 1
    }
else
    ${VERBOSE} && echo "Starting agent for the first time" >&2
    start-ssh-agent "${CONFIG}" || {
	echo "Error: Failed to start SSH agent" >&2
	return 1 2>/dev/null || exit 1
    }
fi

# Check if agent is running
if ! check-ssh-agent-running ; then
    ${QUIET} || echo "SSH agent not running. Starting agent" >&2
    start-ssh-agent "${CONFIG}" || {
	echo "Error: Failed to start SSH agent" >&2
	return 1 2>/dev/null || exit 1
    }
else
    ${VERBOSE} && echo "SSH agent is running" >&2
fi

# Clear secrets if the run is interrupted while keys are being loaded.  Only
# an INT trap is used: an EXIT trap installed while sourcing would fire at
# the end of the caller's shell session and could clobber the user's own trap.
trap 'clear-key-secrets ; trap - INT' INT

# Get list of keys to load
${VERBOSE} && echo "KEY_LIST before check: [${KEY_LIST}]" >&2

if [[ -z "${KEY_LIST}" ]] ; then
    ${VERBOSE} && echo "KEY_LIST is empty, finding all keys..." >&2
    KEY_LIST=$(find-ssh-keys "${SSH_DIR}") || {
	echo "Error: Failed to find SSH keys" >&2
	return 1 2>/dev/null || exit 1
    }
    ${VERBOSE} && echo "Found keys: [${KEY_LIST}]" >&2
    # Load each key from find output (newline-separated).  Process substitution
    # keeps the loop body in this shell so error_count and the KeePassXC master
    # password are not confined to a subshell.  The list is read on FD 3 so that
    # ssh-add (which inherits stdin) cannot consume the remaining key names.
    while IFS= read -r key_file <&3 ; do
	if [[ -z "${key_file}" ]] ; then
	    continue
	fi
	if ! load-ssh-key "${key_file}" "${KEY_TIMEOUT}" ; then
	    error_count=$((error_count + 1))
	fi
    done 3< <(echo "${KEY_LIST}")
else
    ${VERBOSE} && echo "KEY_LIST is set: [${KEY_LIST}], processing specified keys..." >&2
    # Convert comma-separated list and load each key.  FD 3 keeps ssh-add from
    # consuming the remaining key names off stdin.
    while IFS= read -r key_file <&3 ; do
	if [[ -z "${key_file}" ]] ; then
	    continue
	fi
	# Expand ~ and resolve relative paths
	key_file="${key_file/#\~/$HOME}"
	if [[ ! "${key_file}" =~ ^/ ]] ; then
	    # Relative path - make it relative to SSH_DIR
	    key_file="${SSH_DIR}/${key_file}"
	fi
	${VERBOSE} && echo "Processing key from KEY_LIST: [${key_file}]" >&2
	if ! load-ssh-key "${key_file}" "${KEY_TIMEOUT}" ; then
	    error_count=$((error_count + 1))
	fi
    done 3< <(echo "${KEY_LIST}" | tr ',' '\n')
fi

# Secrets are no longer needed.  This script is sourced, so clearing them
# here is what keeps a passphrase out of the caller's interactive shell.
clear-key-secrets
trap - INT

# Show status
show-ssh-agent-status

# Report the agent contents once for the whole run
${QUIET} || show-loaded-keys

# Report results
if [[ ${error_count} -gt 0 ]] ; then
    echo "Error: Failed to load ${error_count} key(s)" >&2
    return 1 2>/dev/null || exit 1
else
    ${QUIET} || echo "Successfully loaded all SSH keys" >&2
    ${VERBOSE} && date >&2
    return 0
fi

fi  # End of else block for LIST_KEYS check
