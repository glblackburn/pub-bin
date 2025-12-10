#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(dirname $0)

################################################################################
# CLI Parameters
################################################################################
QUIET=false
VERBOSE=false
INTERVAL=60
SHOW_REPO_NAME=false
SHOW_WORK_METRIC=false
SHOW_WORK_PATH=false
SHOW_PROCESSES=false
AUDIO_CHANGES_ONLY=false
WORKING_DIR="/tmp"

################################################################################
# State tracking
################################################################################
prev_work_count=""
prev_diff_count=""
prev_status_count=""
prev_process_count=""
prev_repo_name=""
prev_branch_name=""

################################################################################
# Functions
################################################################################
function usage {
    message=${1:-}
    if [ ! -z "${message}" ] ; then
	echo "Message: ${message}"
    fi
    cat<<EOF
Usage: ${script_name} [-hqrvwWpc] [-i <interval>] [-t <working_dir>]

Monitor AI agent activity by tracking working directory files and git changes with
audio feedback.

Options
  -h               : Display this help message.
  -i <interval>    : Update interval in seconds (Default: ${INTERVAL})
  -p               : Show process count monitoring.
  -q               : Quiet mode. Output as little as possible.
  -r               : Show repository name in diff and status output.
  -t <dir>         : Working/scratch directory to monitor (Default: ${WORKING_DIR})
  -v               : Verbose output.
  -w               : Show work metric monitoring.
  -W               : Show working directory path in work output (requires -w).
  -c               : Audio only for changes. Only announce when metrics are increasing or decreasing.

Example:
$ ${script_name} -i 30
EOF
}

function get-status {
    local current=$1
    local previous=$2
    local status=""

    if [ ! -z "${previous}" ] ; then
	if [ "${current}" -gt "${previous}" ] ; then
	    status="increasing"
	elif [ "${current}" -lt "${previous}" ] ; then
	    status="decreasing"
	else
	    status="stable"
	fi
    else
	status="new"
    fi

    echo "${status}"
}

function center-text {
    local text=$1
    local width=$2
    local text_len=${#text}
    local padding=$(( (width - text_len) / 2 ))
    local left_pad=""
    local right_pad=""

    # Create left padding
    for ((i=0; i<padding; i++)); do
	left_pad="${left_pad} "
    done

    # Create right padding (account for odd widths)
    local right_padding=$((width - text_len - padding))
    for ((i=0; i<right_padding; i++)); do
	right_pad="${right_pad} "
    done

    echo "${left_pad}${text}${right_pad}"
}

function format-work-output {
    local work_count=$1
    local status=$2
    local working_dir=$3
    local status_centered=$(center-text "${status}" 10)

    if [ "${SHOW_WORK_PATH}" = true ] ; then
	printf "%-10s %6s (%s) (%s)\n" "work:" "${work_count}" "${status_centered}" "${working_dir}"
    else
	printf "%-10s %6s (%s)\n" "work:" "${work_count}" "${status_centered}"
    fi
}

function format-diff-output {
    local diff_lines=$1
    local status=$2
    local status_centered=$(center-text "${status}" 10)

    printf "%-10s %6s (%s)\n" "diff:" "${diff_lines}" "${status_centered}"
}

function format-status-output {
    local status_count=$1
    local status=$2
    local status_centered=$(center-text "${status}" 10)

    printf "%-10s %6s (%s)\n" "status:" "${status_count}" "${status_centered}"
}

function format-process-output {
    local process_count=$1
    local status=$2
    local status_centered=$(center-text "${status}" 10)

    printf "%-10s %6s (%s)\n" "processes:" "${process_count}" "${status_centered}"
}

function show-timestamp {
    # Get repository name and branch if in git repo (FEATURE-6)
    local repo_info=""
    local repo_root=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
    if [ -n "${repo_root}" ] ; then
	local repo_name=$(basename "${repo_root}" 2>/dev/null || echo "unknown")
	local branch_name=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
	# Handle detached HEAD state
	if [ "${branch_name}" = "HEAD" ] ; then
	    branch_name=$(git rev-parse --short HEAD 2>/dev/null || echo "detached")
	fi
	repo_info=" [${repo_name}:${branch_name}]"
    fi
    echo "$(date)${repo_info}"
}

function has-status-changes {
    local work_status=$1
    local diff_status=$2
    local status_status=$3
    local process_status=$4

    # Check if any status is "increasing" or "decreasing"
    if [ "${work_status}" = "increasing" ] || [ "${work_status}" = "decreasing" ] ; then
	return 0
    fi
    if [ "${diff_status}" = "increasing" ] || [ "${diff_status}" = "decreasing" ] ; then
	return 0
    fi
    if [ "${status_status}" = "increasing" ] || [ "${status_status}" = "decreasing" ] ; then
	return 0
    fi
    if [ -n "${process_status}" ] && ( [ "${process_status}" = "increasing" ] || [ "${process_status}" = "decreasing" ] ) ; then
	return 0
    fi

    # No changes detected
    return 1
}

################################################################################
# get command line options
################################################################################
while getopts ":i:t:hqrvwWpc" opt; do
    case ${opt} in
	i )
            INTERVAL=$OPTARG
            ;;
	t )
            WORKING_DIR=$OPTARG
            ;;
	q )
            QUIET=true
            ;;
	r )
            SHOW_REPO_NAME=true
            ;;
	v )
            VERBOSE=true
            ;;
	w )
            SHOW_WORK_METRIC=true
            ;;
	W )
            SHOW_WORK_PATH=true
            ;;
	p )
            SHOW_PROCESSES=true
            ;;
	c )
            AUDIO_CHANGES_ONLY=true
            ;;
	h )
            usage
            exit 0
            ;;
	\? )
            usage "Invalid Option: -$OPTARG"
            exit 1
            ;;
    esac
done
shift $((OPTIND -1))

################################################################################
# Validation
################################################################################
if [ -z "${INTERVAL}" ] || [ "${INTERVAL}" -le 0 ] ; then
    usage "Interval must be a positive number"
    exit 1
fi

# Validate working directory exists
work_dir_resolved=$(readlink -f "${WORKING_DIR}" 2>/dev/null || echo "${WORKING_DIR}")
if [ ! -d "${work_dir_resolved}" ] ; then
    echo "Error: Working directory does not exist: ${WORKING_DIR}" >&2
    echo "Resolved path: ${work_dir_resolved}" >&2
    exit 1
fi

################################################################################
# Main script logic
################################################################################

${VERBOSE} && cat<<EOF
================================================================================
Starting AI agent progress monitor
Interval: ${INTERVAL} seconds
Working directory: ${WORKING_DIR}
Quiet mode: ${QUIET}
Show repo name: ${SHOW_REPO_NAME}
Show work metric: ${SHOW_WORK_METRIC}
Show work path: ${SHOW_WORK_PATH}
Show processes: ${SHOW_PROCESSES}
Audio changes only: ${AUDIO_CHANGES_ONLY}
Verbose mode: ${VERBOSE}
================================================================================
EOF

while true ; do
    show-timestamp

    # Get repository name and branch if needed
    repo_name=""
    branch_name=""
    if [ "${SHOW_REPO_NAME}" = true ] ; then
	repo_root=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
	if [ -n "${repo_root}" ] ; then
	    repo_name=$(basename "${repo_root}" 2>/dev/null || echo "unknown")
	    branch_name=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
	else
	    repo_name="unknown"
	    branch_name="unknown"
	fi
    fi

    # Check if repository name or branch has changed (for audio output)
    repo_info_changed=false
    if [ "${SHOW_REPO_NAME}" = true ] ; then
	if [ "${repo_name}" != "${prev_repo_name}" ] || [ "${branch_name}" != "${prev_branch_name}" ] ; then
	    repo_info_changed=true
	fi
    fi

    # Get current counts
    # Resolve symlinks and use find -L to follow symlinks
    # Directory is validated at startup, so we can safely run find here
    diff_lines=$(git diff 2>/dev/null | wc -l | tr -d '[:space:]' || echo "0")

    # Get work count only if work metric is enabled
    work_count=0
    if [ "${SHOW_WORK_METRIC}" = true ] ; then
	work_dir_resolved=$(readlink -f "${WORKING_DIR}" 2>/dev/null || echo "${WORKING_DIR}")
	work_count=$(find -L "${work_dir_resolved}" 2>/dev/null | wc -l | tr -d '[:space:]' || echo "0")
    fi

    # Count git status accurately (FEATURE-1)
    # Count modified/staged files (M, A, D, R, C in first column for staged, or space+M/D in second column for unstaged)
    # Format: "XY filename" where X=staged, Y=unstaged
    # Matches: M, A, D, R, C in first column OR M, D in second column (unstaged changes)
    modified_count=$(git status --porcelain 2>/dev/null | grep -E "^[MADRC].|^.[MD]" | wc -l | tr -d '[:space:]' || echo "0")

    # Count untracked files accurately using find
    untracked_count=0
    # Get untracked items, handling paths with spaces properly
    # git status --porcelain format: "?? path" or "?? "path with spaces""
    untracked_items=$(git status --porcelain 2>/dev/null | grep "^??" | sed 's/^?? //' || true)

    if [ -n "${untracked_items}" ] ; then
	while IFS= read -r item; do
	    if [ -n "${item}" ] ; then
		# Remove quotes if present (git quotes paths with spaces)
		item=$(echo "${item}" | sed 's/^"//;s/"$//')
		if [ -d "${item}" ] ; then
		    # Directory - count all files recursively
		    count=$(find "${item}" -type f 2>/dev/null | wc -l | tr -d '[:space:]' || echo "0")
		    untracked_count=$((untracked_count + count))
		else
		    # File - count as 1
		    untracked_count=$((untracked_count + 1))
		fi
	    fi
	done <<< "${untracked_items}"
    fi

    # Total status count is modified + untracked
    status_count=$((modified_count + untracked_count))

    # Get process count (FEATURE-2) - only if enabled
    process_count=0
    process_status=""
    if [ "${SHOW_PROCESSES}" = true ] ; then
	# Cross-platform process counting
	if command -v ps >/dev/null 2>&1 ; then
	    # Try ps -e first (more portable, shows all processes)
	    process_count=$(ps -e 2>/dev/null | wc -l | tr -d '[:space:]' || echo "0")
	    # Subtract header line if count > 0
	    if [ "${process_count}" -gt 0 ] ; then
		process_count=$((process_count - 1))
	    fi
	fi
	process_status=$(get-status "${process_count}" "${prev_process_count}")
    fi

    # Calculate status for each metric
    diff_status=$(get-status "${diff_lines}" "${prev_diff_count}")
    status_status=$(get-status "${status_count}" "${prev_status_count}")

    # Calculate work status only if work metric is enabled
    work_status=""
    if [ "${SHOW_WORK_METRIC}" = true ] ; then
	work_status=$(get-status "${work_count}" "${prev_work_count}")
    fi

    # Generate formatted output messages
    diff_output=$(format-diff-output "${diff_lines}" "${diff_status}")
    status_output=$(format-status-output "${status_count}" "${status_status}")

    # Update previous values for next iteration
    prev_diff_count="${diff_lines}"
    prev_status_count="${status_count}"
    # Update work_count only if work metric is enabled
    if [ "${SHOW_WORK_METRIC}" = true ] ; then
	prev_work_count="${work_count}"
    fi

    # Combine outputs and display/speak together
    combined_message="${diff_output}
${status_output}"

    # Add work output only if enabled
    if [ "${SHOW_WORK_METRIC}" = true ] ; then
	work_output=$(format-work-output "${work_count}" "${work_status}" "${WORKING_DIR}")
	combined_message="${work_output}
${combined_message}"
    fi

    # Add process output only if enabled
    if [ "${SHOW_PROCESSES}" = true ] ; then
	process_output=$(format-process-output "${process_count}" "${process_status}")
	combined_message="${combined_message}
${process_output}"
	prev_process_count="${process_count}"
    fi
    echo "${combined_message}"
    if [ "${QUIET}" != true ] ; then
	# Check if we should announce based on changes-only flag
	should_announce=true
	if [ "${AUDIO_CHANGES_ONLY}" = true ] ; then
	    # Get work_status if work metric is enabled, otherwise use empty string
	    work_status_for_check=""
	    if [ "${SHOW_WORK_METRIC}" = true ] ; then
		work_status_for_check="${work_status}"
	    fi
	    # Get process_status if process metric is enabled, otherwise use empty string
	    process_status_for_check=""
	    if [ "${SHOW_PROCESSES}" = true ] ; then
		process_status_for_check="${process_status}"
	    fi
	    if ! has-status-changes "${work_status_for_check}" "${diff_status}" "${status_status}" "${process_status_for_check}" ; then
		should_announce=false
	    fi
	    # If repo name changed, we should announce (even if other metrics are stable)
	    if [ "${SHOW_REPO_NAME}" = true ] && [ "${repo_info_changed}" = true ] ; then
		should_announce=true
	    fi
	fi

	if [ "${should_announce}" = true ] ; then
	    # Build audio message
	    audio_message="${combined_message}"
	    # Add repository and branch info to audio if -r flag is enabled
	    if [ "${SHOW_REPO_NAME}" = true ] ; then
		# Follow -c option: only say repo/branch if it changed (when -c is set) or always (when -c is not set)
		if [ "${AUDIO_CHANGES_ONLY}" != true ] || [ "${repo_info_changed}" = true ] ; then
		    audio_message="${audio_message}
repository: ${repo_name} branch: ${branch_name}"
		fi
	    fi
	    echo "${audio_message}" | say || true
	fi
    fi

    # Update previous repository name and branch for next iteration
    if [ "${SHOW_REPO_NAME}" = true ] ; then
	prev_repo_name="${repo_name}"
	prev_branch_name="${branch_name}"
    fi

    sleep ${INTERVAL}
done
