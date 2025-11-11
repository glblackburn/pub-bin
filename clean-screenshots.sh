#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(dirname $0)

################################################################################
# CLI Parameters
################################################################################
QUIET=false
VERBOSE=false
DRY_RUN=false
SCREENSHOT_DIR=""
SRC_DIR="${HOME}/Desktop"

################################################################################
# Load config library and settings
################################################################################
. ${script_dir}/config/config.sh
load-config "noerror"
load-script-config "clean-screenshots"

################################################################################
# Default values
################################################################################
# Use config value, CLI override, or default
SCREENSHOT_DIR="${SCREENSHOT_DIR:-${screenshot_dir:-${HOME}/Pictures/Screenshots}}"
SCREENSHOT_PREFIX="Screen*"

################################################################################
# Functions
################################################################################
function usage {
    local message=${1:-}
    if [ ! -z "${message}" ] ; then
	echo "Error: ${message}"
	echo ""
    fi
    cat<<EOF
Usage: ${script_name} [-hqv] [-d <screenshot_dir>] [-s <src_dir>] [-p <prefix>]

Clean up screenshot files from Desktop by moving them to an archived directory
organized by timestamp.

Options
  -h               : Display this help message.
  -d <dir>        : Screenshot archive directory (Default: ${SCREENSHOT_DIR})
  -s <dir>        : Source directory to search (Default: ${SRC_DIR})
  -p <prefix>     : Screenshot filename prefix pattern (Default: ${SCREENSHOT_PREFIX})
  -q               : Quiet mode. Output as little as possible.
  -v               : Verbose output.
  -n               : Dry run mode. Show what would be done without making changes.

Example:
$ ${script_name} -d ~/Pictures/Screenshots -n
EOF
}

function find-screenshots {
    local search_dir=$1
    local prefix=$2
    find "${search_dir}" -maxdepth 1 -name "${prefix}" -type f 2>/dev/null
}

function move-screenshots {
    local src_dir=$1
    local archive_dir=$2
    local prefix=$3
    local count=0

    ${VERBOSE} && cat<<EOF
================================================================================
Searching for screenshots in ${src_dir}
Pattern: ${prefix}
================================================================================
EOF

    # Find screenshots
    local screenshots=$(find-screenshots "${src_dir}" "${prefix}")
    local screenshot_count=$(echo "${screenshots}" | grep -v '^$' | wc -l | tr -d ' ')

    if [ "${screenshot_count}" -eq 0 ] ; then
	${QUIET} || echo "No screenshots found matching pattern: ${prefix}"
	return 0
    fi

    ${QUIET} || cat<<EOF
Found ${screenshot_count} screenshot(s) to move:
--------------------------------------------------------------------------------
EOF

    echo "${screenshots}" | while IFS= read -r screenshot ; do
	if [ ! -z "${screenshot}" ] ; then
	    ${QUIET} || echo "  ${screenshot}"
	fi
    done

    if [ "${DRY_RUN}" = "true" ] ; then
	${QUIET} || cat<<EOF
--------------------------------------------------------------------------------
DRY RUN: Would create archive directory: ${archive_dir}
DRY RUN: Would move ${screenshot_count} screenshot(s) to archive
--------------------------------------------------------------------------------
EOF
	return 0
    fi

    # Create archive directory
    ${VERBOSE} && cat<<EOF
Creating archive directory: ${archive_dir}
EOF
    mkdir -p "${archive_dir}" || {
	echo "Error: Failed to create archive directory: ${archive_dir}" >&2
	return 1
    }

    # Move screenshots
    ${QUIET} || cat<<EOF
Moving screenshots to archive...
EOF

    echo "${screenshots}" | while IFS= read -r screenshot ; do
	if [ ! -z "${screenshot}" ] && [ -f "${screenshot}" ] ; then
	    local basename=$(basename "${screenshot}")
	    if mv "${screenshot}" "${archive_dir}/${basename}" 2>/dev/null ; then
		${VERBOSE} && echo "  Moved: ${basename}"
		((count++))
	    else
		echo "  Error: Failed to move ${basename}" >&2
	    fi
	fi
    done

    ${QUIET} || cat<<EOF
Moved ${screenshot_count} screenshot(s) to ${archive_dir}
EOF

    ${VERBOSE} && cat<<EOF
Archive directory contents:
--------------------------------------------------------------------------------
EOF
    ${VERBOSE} && ls -lh "${archive_dir}" 2>/dev/null || true
}

################################################################################
# get command line options
################################################################################
while getopts ":d:s:p:hqvn" opt; do
    case ${opt} in
	d )
            SCREENSHOT_DIR=$OPTARG
            ;;
	s )
            SRC_DIR=$OPTARG
            ;;
	p )
            SCREENSHOT_PREFIX=$OPTARG
            ;;
	q )
            QUIET=true
            ;;
	v )
            VERBOSE=true
            ;;
	n )
            DRY_RUN=true
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
if [ -z "${SCREENSHOT_DIR}" ] ; then
    usage "screenshot_dir not set. Set via -d option, config file, or run setup-pub-bin-config.sh"
    exit 1
fi

if [ ! -d "${SRC_DIR}" ] ; then
    echo "Error: Source directory does not exist: ${SRC_DIR}" >&2
    exit 1
fi

################################################################################
# Main script logic
################################################################################

timestamp=$(date +%Y-%m-%d_%H%M%S)
archive_dir="${SCREENSHOT_DIR}/${timestamp}"

${VERBOSE} && cat<<EOF
================================================================================
Configuration
================================================================================
src_dir=[${SRC_DIR}]
archive_dir=[${archive_dir}]
screenshot_prefix=[${SCREENSHOT_PREFIX}]
dry_run=[${DRY_RUN}]
================================================================================
EOF

# Change to source directory
original_dir=$(pwd)
cd "${SRC_DIR}" || {
    echo "Error: Failed to change to source directory: ${SRC_DIR}" >&2
    exit 1
}

# Trap to ensure we return to original directory
trap "cd '${original_dir}'" EXIT

# Move screenshots
move-screenshots "${SRC_DIR}" "${archive_dir}" "${SCREENSHOT_PREFIX}"

${QUIET} || echo "Done"
