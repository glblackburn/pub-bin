#!/usr/bin/env bash
# Note: This script is designed to be sourced, not executed directly
# Usage: . ./load-ssh-key.sh [options]
# or:    source ./load-ssh-key.sh [options]

# Use set -u and -o pipefail, but not -e since script is sourced
set -u -o pipefail

script_name=$(basename ${BASH_SOURCE[0]})
script_dir=$(dirname ${BASH_SOURCE[0]})

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
# Reset KEY_LIST to ensure clean state when script is sourced multiple times
unset KEY_LIST
KEY_LIST=""

################################################################################
# State tracking
################################################################################
error_count=0

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
Usage: . ${script_name} [-hqlvK] [-t <timeout>] [-d <ssh_dir>] [-c <config>] [-k <key_list>]

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
  -K               : Kill current SSH agent and start a new one
  -l               : List currently loaded SSH keys and exit
  -q               : Quiet mode. Output as little as possible.
  -v               : Verbose output. Show detailed information.

Example:
. ${script_name} -t 3600
. ${script_name} -K  # Kill current agent and reload all keys
. ${script_name} -l  # List currently loaded keys
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

function is-key-loaded {
    local fingerprint=$1
    local loaded_keys=""
    local key_count=0

    loaded_keys=$(ssh-add -l 2>/dev/null || echo "")
    key_count=$(echo "${loaded_keys}" | grep -F "${fingerprint}" | grep -v '^$' | wc -l | tr -d ' ')

    if [[ "${key_count}" -ge 1 ]] ; then
	return 0
    else
	return 1
    fi
}

function is-valid-ssh-key {
    local key_file=$1
    local fingerprint=""

    # Try to get fingerprint - if it fails, file is not a valid SSH key
    fingerprint=$(ssh-keygen -l -E sha256 -f "${key_file}" 2>/dev/null | awk '{print $2}' || echo "")
    
    if [[ -z "${fingerprint}" ]] ; then
	return 1
    else
	return 0
    fi
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

    # Check if file is a valid SSH key before processing
    if ! is-valid-ssh-key "${key_file}" ; then
	${VERBOSE} && echo "Skipping non-key file: ${key_file}" >&2
	return 0  # Return success - not an error, just skip it
    fi

    fingerprint=$(get-key-fingerprint "${key_file}")
    if [[ -z "${fingerprint}" ]] ; then
	# This should not happen if is-valid-ssh-key passed, but handle it anyway
	${VERBOSE} && echo "Warning: Could not get fingerprint for: ${key_file}" >&2
	return 0  # Skip it, don't count as error
    fi

    ${VERBOSE} && cat<<EOF >&2
key_file=[${key_file}]
KEY_CHECK=[${fingerprint}]
EOF

    if is-key-loaded "${fingerprint}" ; then
	${QUIET} || echo "Key already loaded: ${key_basename}" >&2
	${QUIET} || echo "Listing all loaded keys:" >&2
	${QUIET} || ssh-add -l >&2 || true
	return 0
    fi

    ${VERBOSE} && echo "Key not found. Listing all loaded keys:" >&2
    ${VERBOSE} && ssh-add -l >&2 || true

    ${QUIET} || echo "Adding SSH key to agent: ${key_basename}" >&2
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

function list-loaded-keys {
    local loaded_keys=""
    local key_count=0

    # If SSH_AUTH_SOCK is already set in environment, verify the agent is actually running
    # If not, try to load from config file
    if [[ ! -z "${SSH_AUTH_SOCK:-}" ]] && [[ ! -z "${SSH_AGENT_PID:-}" ]] ; then
	# Check if the agent from environment is actually running
	if ! ps -p "${SSH_AGENT_PID}" >/dev/null 2>&1 ; then
	    # Environment points to dead agent, clear it and try config file
	    unset SSH_AUTH_SOCK
	    unset SSH_AGENT_PID
	fi
    fi

    # If SSH_AUTH_SOCK is not set or was cleared, try to load from config file
    if [[ -z "${SSH_AUTH_SOCK:-}" ]] ; then
	if [[ -e "${CONFIG}" ]] ; then
	    # Parse config file and export variables explicitly
	    # This works when script is executed directly (not sourced)
	    while IFS= read -r line ; do
		if [[ "${line}" =~ ^SSH_AUTH_SOCK= ]] ; then
		    eval "export ${line}"
		elif [[ "${line}" =~ ^SSH_AGENT_PID= ]] ; then
		    eval "export ${line}"
		fi
	    done < "${CONFIG}" 2>/dev/null || true
	fi
    fi

    # If still no SSH_AUTH_SOCK, try to find it from running agents
    if [[ -z "${SSH_AUTH_SOCK:-}" ]] ; then
	# Try to find ssh-agent socket from common locations
	local possible_sockets=""
	possible_sockets=$(find /tmp /var/folders -name "agent.*" -user $(id -u) 2>/dev/null | head -1 || echo "")
	if [[ ! -z "${possible_sockets}" ]] ; then
	    export SSH_AUTH_SOCK="${possible_sockets}"
	    # Try to find the PID
	    local agent_pids=""
	    agent_pids=$(ps -fe | grep "[s]sh-agent" | awk '{print $2}' | head -1 || echo "")
	    if [[ ! -z "${agent_pids}" ]] ; then
		export SSH_AGENT_PID="${agent_pids}"
	    fi
	fi
    fi

    # Check if agent is running
    if ! check-ssh-agent-running ; then
	echo "SSH agent is not running" >&2
	return 1
    fi

    # Get list of loaded keys
    loaded_keys=$(ssh-add -l 2>/dev/null || echo "")
    key_count=$(echo "${loaded_keys}" | grep -v '^$' | wc -l | tr -d ' ')

    if [[ "${key_count}" -eq 0 ]] ; then
	echo "No SSH keys are currently loaded in the agent" >&2
	return 0
    fi

    echo "Currently loaded SSH keys (${key_count}):" >&2
    ssh-add -l 2>/dev/null || {
	echo "Error: Failed to list SSH keys" >&2
	return 1
    }

    return 0
}

################################################################################
# get command line options
################################################################################
# Reset OPTIND in case script is sourced multiple times
OPTIND=1
while getopts ":t:d:c:k:hqlvK" opt; do
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

# Get list of keys to load
${VERBOSE} && echo "KEY_LIST before check: [${KEY_LIST}]" >&2

if [[ -z "${KEY_LIST}" ]] ; then
    ${VERBOSE} && echo "KEY_LIST is empty, finding all keys..." >&2
    KEY_LIST=$(find-ssh-keys "${SSH_DIR}") || {
	echo "Error: Failed to find SSH keys" >&2
	return 1 2>/dev/null || exit 1
    }
    ${VERBOSE} && echo "Found keys: [${KEY_LIST}]" >&2
    # Load each key from find output (newline-separated)
    echo "${KEY_LIST}" | while IFS= read -r key_file ; do
	if [[ -z "${key_file}" ]] ; then
	    continue
	fi
	if ! load-ssh-key "${key_file}" "${KEY_TIMEOUT}" ; then
	    ((error_count++))
	fi
    done
else
    ${VERBOSE} && echo "KEY_LIST is set: [${KEY_LIST}], processing specified keys..." >&2
    # Convert comma-separated list and load each key
    echo "${KEY_LIST}" | tr ',' '\n' | while IFS= read -r key_file ; do
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
	    ((error_count++))
	fi
    done
fi

# Show status
show-ssh-agent-status

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
