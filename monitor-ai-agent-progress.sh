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

################################################################################
# State tracking
################################################################################
prev_temp_count=""
prev_diff_count=""

################################################################################
# Functions
################################################################################
function usage {
    message=${1:-}
    if [ ! -z "${message}" ] ; then
	echo "Message: ${message}"
    fi
    cat<<EOF
Usage: ${script_name} [-hqrv] [-i <interval>]

Monitor AI agent activity by tracking temp files and git changes with
audio feedback.

Options
  -h               : Display this help message.
  -i <interval>    : Update interval in seconds (Default: ${INTERVAL})
  -q               : Quiet mode. Output as little as possible.
  -r               : Show repository name in diff output.
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

function monitor-temp-files {
    local temp_count=$(ls -ltr /tmp/ 2>/dev/null | wc -l | tr -d ' ')
    local status=$(get-status "${temp_count}" "${prev_temp_count}")

    echo "temp: ${temp_count} (${status})" | tee >(say) || true

    prev_temp_count="${temp_count}"
}

function monitor-git-diff {
    local diff_lines=$(git diff 2>/dev/null | wc -l | tr -d ' ')
    local status=$(get-status "${diff_lines}" "${prev_diff_count}")
    local message="diff: ${diff_lines} (${status})"

    if [ "${SHOW_REPO_NAME}" = true ] ; then
	local repo_name=$(basename $(git rev-parse --show-toplevel 2>/dev/null) 2>/dev/null || echo "unknown")
	message="${message} (${repo_name})"
    fi

    echo "${message}" | tee >(say) || true

    prev_diff_count="${diff_lines}"
}

function show-status {
    if [ "${QUIET}" != true ] ; then
	date
    fi
}

################################################################################
# get command line options
################################################################################
while getopts ":i:hqrv" opt; do
    case ${opt} in
	i )
            INTERVAL=$OPTARG
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
Starting AI agent progress monitor
Interval: ${INTERVAL} seconds
Quiet mode: ${QUIET}
Show repo name: ${SHOW_REPO_NAME}
Verbose mode: ${VERBOSE}
EOF

while true ; do
    monitor-temp-files
    sleep 2
    monitor-git-diff
    show-status
    sleep ${INTERVAL}
done
