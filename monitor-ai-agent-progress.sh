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

################################################################################
# Functions
################################################################################
function usage {
    message=${1:-}
    if [ ! -z "${message}" ] ; then
	echo "Message: ${message}"
    fi
    cat<<EOF
Usage: ${script_name} [-hqv] [-i <interval>]

Monitor AI agent activity by tracking temp files and git changes with
audio feedback.

Options
  -h               : Display this help message.
  -i <interval>    : Update interval in seconds (Default: ${INTERVAL})
  -q               : Quiet mode. Output as little as possible.
  -v               : Verbose output.

Example:
$ ${script_name} -i 30
EOF
}

function monitor-temp-files {
    local temp_count=$(ls -ltr /tmp/ 2>/dev/null | wc -l | tr -d ' ')
    echo "temp: ${temp_count}" | tee >(say) || true
}

function monitor-git-diff {
    local diff_lines=$(git diff 2>/dev/null | wc -l | tr -d ' ')
    local repo_name=$(basename $(git rev-parse --show-toplevel 2>/dev/null) 2>/dev/null || echo "unknown")
    echo "diff: ${diff_lines} (${repo_name})" | tee >(say) || true
}

function show-status {
    if [ "${QUIET}" != true ] ; then
	date
    fi
}

################################################################################
# get command line options
################################################################################
while getopts ":i:hqv" opt; do
    case ${opt} in
	i )
            INTERVAL=$OPTARG
            ;;
	q )
            QUIET=true
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
Verbose mode: ${VERBOSE}
EOF

while true ; do
    monitor-temp-files
    sleep 2
    monitor-git-diff
    show-status
    sleep ${INTERVAL}
done
