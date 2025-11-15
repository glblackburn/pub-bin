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
KEY_TIMEOUT=28800
SSH_DIR="${HOME}/.ssh"
CONFIG="${SSH_DIR}/ssh-agent.config"
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
Usage: . ${script_name} [-hqvK] [-t <timeout>] [-d <ssh_dir>] [-c <config>] [-k <key_list>]

Load SSH keys from ~/.ssh into the SSH agent. This script must be sourced
(using . or source) to load the SSH agent environment variables into your
current shell session.

Options
  -h               : Display this help message.
  -t <timeout>     : Key timeout in seconds (Default: ${KEY_TIMEOUT})
  -d <dir>         : SSH directory to search for keys (Default: ${SSH_DIR})
  -c <config>      : SSH agent config file path (Default: ${CONFIG})
  -k <key_list>    : Comma-separated list of specific keys to load (Default: auto-detect all)
  -K               : Kill current SSH agent and start a new one
  -q               : Quiet mode. Output as little as possible.
  -v               : Verbose output. Show detailed information.

Example:
. ${script_name} -t 3600
. ${script_name} -K  # Kill current agent and reload all keys
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

    if [[ -z "${agent_pid}" ]] ; then
	${VERBOSE} && echo "No SSH agent PID found to kill" >&2
	return 0
    fi

    if check-ssh-agent-running ; then
	${QUIET} || echo "Killing SSH agent (PID: ${agent_pid})" >&2
	kill "${agent_pid}" 2>/dev/null || {
	    ${VERBOSE} && echo "Warning: Failed to kill SSH agent PID ${agent_pid}" >&2
	}
	# Wait a moment for the agent to terminate
	sleep 0.5
	# Unset the environment variables
	unset SSH_AGENT_PID
	unset SSH_AUTH_SOCK
    else
	${VERBOSE} && echo "SSH agent (PID: ${agent_pid}) is not running" >&2
    fi

    # Remove the config file if it exists
    if [[ -e "${CONFIG}" ]] ; then
	${VERBOSE} && echo "Removing SSH agent config file: ${CONFIG}" >&2
	rm -f "${CONFIG}" 2>/dev/null || true
    fi

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

################################################################################
# get command line options
################################################################################
while getopts ":t:d:c:k:hqvK" opt; do
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
            ;;
	K )
            KILL_AGENT=true
            ;;
	q )
            QUIET=true
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

# Check if script is being sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]] ; then
    cat<<EOF >&2
Warning: This script should be sourced, not executed directly.
Usage: . ${script_name} [options]
or:    source ${script_name} [options]
EOF
    exit 1
fi

# Kill current agent if requested
if [[ "${KILL_AGENT}" == true ]] ; then
    # Load config first to get current agent PID if it exists
    if [[ -e "${CONFIG}" ]] ; then
	. "${CONFIG}" 2>/dev/null || true
    fi
    kill-ssh-agent
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
if [[ -z "${KEY_LIST}" ]] ; then
    KEY_LIST=$(find-ssh-keys "${SSH_DIR}") || {
	echo "Error: Failed to find SSH keys" >&2
	return 1 2>/dev/null || exit 1
    }
else
    # Convert comma-separated list to newline-separated
    KEY_LIST=$(echo "${KEY_LIST}" | tr ',' '\n')
fi

# Load each key
for key_file in ${KEY_LIST} ; do
    if [[ -z "${key_file}" ]] ; then
	continue
    fi

    if ! load-ssh-key "${key_file}" "${KEY_TIMEOUT}" ; then
	((error_count++))
    fi
done

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
