#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(dirname $0)

################################################################################
# CLI Parameters
################################################################################
DRY_RUN=false
SCREENSHOT_DIR=""
SRC_DIR="${HOME}/Desktop"

################################################################################
# Load config library and settings
################################################################################
. ${script_dir}/config/config.sh
load-config "noerror"

################################################################################
# Default values and interactive setup
################################################################################
# Use CLI override first, then config value, or prompt interactively
if [ -z "${SCREENSHOT_DIR}" ] ; then
    if [ -z "${screenshot_dir:-}" ] ; then
        # Config doesn't exist, prompt interactively
        cat<<EOF
================================================================================
Configuration Required
================================================================================
screenshot_dir is not set in config file: ${config_file}
EOF
        SCREENSHOT_DIR=$(setup-config-value "screenshot_dir" \
            "Enter the directory where screenshots should be archived. This directory will contain timestamped subdirectories for each cleanup session." \
            "${HOME}/Pictures/Screenshots" \
            "true")
        save-config-value "screenshot_dir" "${SCREENSHOT_DIR}"
        # Reload config to get the saved value
        load-config "noerror"
    else
        SCREENSHOT_DIR="${screenshot_dir}"
    fi
fi

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
Usage: ${script_name} [-hn] [-d <screenshot_dir>] [-s <src_dir>] [-p <prefix>]

Clean up screenshot files from Desktop by moving them to an archived directory
organized by timestamp.

Options
  -h               : Display this help message.
  -d <dir>        : Screenshot archive directory (Default: ${SCREENSHOT_DIR})
  -s <dir>        : Source directory to search (Default: ${SRC_DIR})
  -p <prefix>     : Screenshot filename prefix pattern (Default: ${SCREENSHOT_PREFIX})
  -n               : Dry run mode. Show what would be done without making changes.

Example:
$ ${script_name} -d ~/Pictures/Screenshots -n
EOF
}

function find-screenshots {
    local prefix=$1
    # Search from current directory (we're already in src_dir)
    find . -maxdepth 1 -name "${prefix}" -type f 2>/dev/null
}

function move-screenshots {
    local src_dir=$1
    local archive_dir=$2
    local prefix=$3

    # Find screenshots (we're already in src_dir, so use relative paths)
    local screenshots=$(find-screenshots "${prefix}")
    local screenshot_count=$(echo "${screenshots}" | grep -v '^$' | wc -l | tr -d ' ')

    cat<<EOF
================================================================================
Searching for screenshots in ${src_dir}
Pattern: ${prefix}
================================================================================
EOF

    if [ "${screenshot_count}" -eq 0 ] ; then
	echo "No screenshots found matching pattern: ${prefix}"
	return 0
    fi

    cat<<EOF
Found ${screenshot_count} screenshot(s) to move:
--------------------------------------------------------------------------------
EOF

    echo "${screenshots}" | while IFS= read -r screenshot ; do
	if [ ! -z "${screenshot}" ] ; then
	    echo "  ${screenshot}"
	fi
    done

    cat<<EOF
Files to move from ${src_dir} to ${archive_dir}
--------------------------------------------------------------------------------
EOF

    # Show files with ls -l details (matching old script)
    find . -name "${prefix}" -exec ls -l {} \;

    if [ "${DRY_RUN}" = "true" ] ; then
	cat<<EOF
--------------------------------------------------------------------------------
DRY RUN: Would create archive directory: ${archive_dir}
DRY RUN: Would move ${screenshot_count} screenshot(s) to archive
--------------------------------------------------------------------------------
EOF
	return 0
    fi

    cat<<EOF
Creating archive directory: ${archive_dir}
EOF
    mkdir -p "${archive_dir}" || {
	echo "Error: Failed to create archive directory: ${archive_dir}" >&2
	return 1
    }

    cat<<EOF
Create archive dir: ${archive_dir}"
--------------------------------------------------------------------------------
EOF

    cat<<EOF
Move screenshots to archive
--------------------------------------------------------------------------------
EOF

    # Move screenshots (matching old script pattern)
    find . -name "${prefix}" | xargs -I {} mv '{}' "${archive_dir}"

    cat<<EOF
Archive Dir List
--------------------------------------------------------------------------------
EOF
    find "${archive_dir}" -type f -exec ls -l {} \;
}

################################################################################
# get command line options
################################################################################
while getopts ":d:s:p:hn" opt; do
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
    usage "screenshot_dir not set. Set via -d option or config file. Script will prompt interactively if config is missing."
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

# Change to source directory
original_dir=$(pwd)
cd "${SRC_DIR}" || {
    echo "Error: Failed to change to source directory: ${SRC_DIR}" >&2
    exit 1
}

# Trap to ensure we return to original directory
trap "cd '${original_dir}'" EXIT

# Show configuration (detailed output)
cat<<EOF
================================================================================
Configuration
================================================================================
src_dir=[${SRC_DIR}]
archive_dir=[${archive_dir}]
screenshot_prefix=[${SCREENSHOT_PREFIX}]
dry_run=[${DRY_RUN}]
================================================================================
EOF

# Show init vars (matching old script)
cat<<EOF
Init vars
--------------------------------------------------------------------------------
src_dir=[${SRC_DIR}]
archive_dir=[${archive_dir}]
screenshot_prefix=[${SCREENSHOT_PREFIX}]
EOF

# Move screenshots
move-screenshots "${SRC_DIR}" "${archive_dir}" "${SCREENSHOT_PREFIX}"

echo "Done"
