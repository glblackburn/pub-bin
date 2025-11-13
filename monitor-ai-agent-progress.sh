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
WORKING_DIR="/tmp"

################################################################################
# State tracking
################################################################################
prev_work_count=""
prev_diff_count=""
prev_status_count=""

################################################################################
# Functions
################################################################################
function usage {
    message=${1:-}
    if [ ! -z "${message}" ] ; then
	echo "Message: ${message}"
    fi
    cat<<EOF
Usage: ${script_name} [-hqrv] [-i <interval>] [-t <working_dir>]

Monitor AI agent activity by tracking working directory files and git changes with
audio feedback.

Options
  -h               : Display this help message.
  -i <interval>    : Update interval in seconds (Default: ${INTERVAL})
  -q               : Quiet mode. Output as little as possible.
  -r               : Show repository name in diff and status output.
  -t <dir>         : Working/scratch directory to monitor (Default: ${WORKING_DIR})
  -v               : Verbose output.

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

    printf "work:   %6s (%s) (%s)\n" "${work_count}" "${status_centered}" "${working_dir}"
}

function format-diff-output {
    local diff_lines=$1
    local status=$2
    local repo_name=$3
    local status_centered=$(center-text "${status}" 10)

    if [ "${SHOW_REPO_NAME}" = true ] ; then
	printf "diff:   %6s (%s) (%s)\n" "${diff_lines}" "${status_centered}" "${repo_name}"
    else
	printf "diff:   %6s (%s)\n" "${diff_lines}" "${status_centered}"
    fi
}

function format-status-output {
    local status_count=$1
    local status=$2
    local repo_name=$3
    local status_centered=$(center-text "${status}" 10)

    if [ "${SHOW_REPO_NAME}" = true ] ; then
	printf "status: %6s (%s) (%s)\n" "${status_count}" "${status_centered}" "${repo_name}"
    else
	printf "status: %6s (%s)\n" "${status_count}" "${status_centered}"
    fi
}

function show-timestamp {
    date
}

################################################################################
# get command line options
################################################################################
while getopts ":i:t:hqrv" opt; do
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
    work_dir_resolved=$(readlink -f "${WORKING_DIR}" 2>/dev/null || echo "${WORKING_DIR}")
    work_count=$(find -L "${work_dir_resolved}" 2>/dev/null | wc -l | tr -d ' ')
    diff_lines=$(git diff 2>/dev/null | wc -l | tr -d ' ')
    status_count=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')

    # Calculate status for each metric
    work_status=$(get-status "${work_count}" "${prev_work_count}")
    diff_status=$(get-status "${diff_lines}" "${prev_diff_count}")
    status_status=$(get-status "${status_count}" "${prev_status_count}")

    # Generate formatted output messages
    work_output=$(format-work-output "${work_count}" "${work_status}" "${WORKING_DIR}")
    sleep 2
    diff_output=$(format-diff-output "${diff_lines}" "${diff_status}" "${repo_name}")
    sleep 2
    status_output=$(format-status-output "${status_count}" "${status_status}" "${repo_name}")

    # Update previous values for next iteration
    prev_work_count="${work_count}"
    prev_diff_count="${diff_lines}"
    prev_status_count="${status_count}"

    # Combine outputs and display/speak together
    combined_message="${work_output}
${diff_output}
${status_output}"
    echo "${combined_message}"
    if [ "${QUIET}" != true ] ; then
	echo "${combined_message}" | say || true
    fi

    sleep ${INTERVAL}
done
