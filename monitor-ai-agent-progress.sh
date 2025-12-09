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
SHOW_WORKING_DIR=false
SHOW_PROCESSES=false
WORKING_DIR="/tmp"

################################################################################
# State tracking
################################################################################
prev_work_count=""
prev_diff_count=""
prev_status_count=""
prev_process_count=""

################################################################################
# Functions
################################################################################
function usage {
    message=${1:-}
    if [ ! -z "${message}" ] ; then
	echo "Message: ${message}"
    fi
    cat<<EOF
Usage: ${script_name} [-hqrvwp] [-i <interval>] [-t <working_dir>]

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
  -w               : Show working directory path in work output.

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

    if [ "${SHOW_WORKING_DIR}" = true ] ; then
	printf "%-10s %6s (%s) (%s)\n" "work:" "${work_count}" "${status_centered}" "${working_dir}"
    else
	printf "%-10s %6s (%s)\n" "work:" "${work_count}" "${status_centered}"
    fi
}

function format-diff-output {
    local diff_lines=$1
    local status=$2
    local repo_name=$3
    local status_centered=$(center-text "${status}" 10)

    if [ "${SHOW_REPO_NAME}" = true ] ; then
	printf "%-10s %6s (%s) (%s)\n" "diff:" "${diff_lines}" "${status_centered}" "${repo_name}"
    else
	printf "%-10s %6s (%s)\n" "diff:" "${diff_lines}" "${status_centered}"
    fi
}

function format-status-output {
    local status_count=$1
    local status=$2
    local repo_name=$3
    local status_centered=$(center-text "${status}" 10)

    if [ "${SHOW_REPO_NAME}" = true ] ; then
	printf "%-10s %6s (%s) (%s)\n" "status:" "${status_count}" "${status_centered}" "${repo_name}"
    else
	printf "%-10s %6s (%s)\n" "status:" "${status_count}" "${status_centered}"
    fi
}

function format-process-output {
    local process_count=$1
    local status=$2
    local status_centered=$(center-text "${status}" 10)

    printf "%-10s %6s (%s)\n" "processes:" "${process_count}" "${status_centered}"
}

function show-timestamp {
    date
}

################################################################################
# get command line options
################################################################################
while getopts ":i:t:hqrvwp" opt; do
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
            SHOW_WORKING_DIR=true
            ;;
	p )
            SHOW_PROCESSES=true
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
Show working dir: ${SHOW_WORKING_DIR}
Show processes: ${SHOW_PROCESSES}
Verbose mode: ${VERBOSE}
================================================================================
EOF

while true ; do
    show-timestamp

    # Get repository name if needed
    repo_name=""
    if [ "${SHOW_REPO_NAME}" = true ] ; then
	repo_name=$(basename $(git rev-parse --show-toplevel 2>/dev/null) 2>/dev/null || echo "unknown")
    fi

    # Get current counts
    # Resolve symlinks and use find -L to follow symlinks
    # Directory is validated at startup, so we can safely run find here
    work_dir_resolved=$(readlink -f "${WORKING_DIR}" 2>/dev/null || echo "${WORKING_DIR}")
    work_count=$(find -L "${work_dir_resolved}" 2>/dev/null | wc -l | tr -d '[:space:]' || echo "0")
    diff_lines=$(git diff 2>/dev/null | wc -l | tr -d '[:space:]' || echo "0")

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
    work_status=$(get-status "${work_count}" "${prev_work_count}")
    diff_status=$(get-status "${diff_lines}" "${prev_diff_count}")
    status_status=$(get-status "${status_count}" "${prev_status_count}")

    # Generate formatted output messages
    work_output=$(format-work-output "${work_count}" "${work_status}" "${WORKING_DIR}")
    diff_output=$(format-diff-output "${diff_lines}" "${diff_status}" "${repo_name}")
    status_output=$(format-status-output "${status_count}" "${status_status}" "${repo_name}")

    # Update previous values for next iteration
    prev_work_count="${work_count}"
    prev_diff_count="${diff_lines}"
    prev_status_count="${status_count}"

    # Combine outputs and display/speak together
    combined_message="${work_output}
${diff_output}
${status_output}"

    # Add process output only if enabled
    if [ "${SHOW_PROCESSES}" = true ] ; then
	process_output=$(format-process-output "${process_count}" "${process_status}")
	combined_message="${combined_message}
${process_output}"
	prev_process_count="${process_count}"
    fi
    echo "${combined_message}"
    if [ "${QUIET}" != true ] ; then
	echo "${combined_message}" | say || true
    fi

    sleep ${INTERVAL}
done
