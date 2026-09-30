#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename "$0")

################################################################################
# CLI Parameters
################################################################################
DRY_RUN=false
SRC_DIR="${HOME}/Downloads"
ARCHIVE_NAME="old"

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
Usage: ${script_name} [-hn] [-s <src_dir>]

Clean up the Downloads folder by moving everything in it (except the
archive directory and dot files) into a timestamped archive directory:
<src_dir>/${ARCHIVE_NAME}/YYYY-MM-DD_HHMMSS

Options
  -h               : Display this help message.
  -s <dir>         : Directory to clean (Default: ${SRC_DIR})
  -n               : Dry run mode. Show what would be done without making changes.

Example:
$ ${script_name} -n
EOF
}

function find-downloads {
    # Top-level entries only; skip the archive dir and dot files (.DS_Store, .localized)
    find . -mindepth 1 -maxdepth 1 ! -name "${ARCHIVE_NAME}" ! -name '.*' | sed 's|^\./||' | sort
}

function move-downloads {
    local archive_dir=$1
    local downloads=$(find-downloads)

    if [ -z "${downloads}" ] ; then
	echo "Nothing to move in ${SRC_DIR}"
	return 0
    fi

    local download_count=$(echo "${downloads}" | wc -l | tr -d ' ')

    cat<<EOF
================================================================================
Found ${download_count} item(s) to move from ${SRC_DIR} to ${archive_dir}
================================================================================
EOF
    echo "${downloads}" | while IFS= read -r download ; do
	ls -ld "${download}"
    done

    if [ "${DRY_RUN}" = "true" ] ; then
	cat<<EOF
--------------------------------------------------------------------------------
DRY RUN: Would create ${archive_dir} and move ${download_count} item(s) into it
--------------------------------------------------------------------------------
EOF
	return 0
    fi

    echo "Create archive dir: ${archive_dir}"
    mkdir -p "${archive_dir}"

    echo "Move downloads to archive"
    echo "${downloads}" | while IFS= read -r download ; do
	mv "${download}" "${archive_dir}/"
    done
}

################################################################################
# get command line options
################################################################################
while getopts ":s:hn" opt; do
    case ${opt} in
	s )
            SRC_DIR=$OPTARG
            ;;
	n )
            DRY_RUN=true
            ;;
	h )
            usage
            exit 0
            ;;
	: )
            usage "Option -$OPTARG requires an argument"
            exit 1
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
if [ ! -d "${SRC_DIR}" ] ; then
    echo "Error: Source directory does not exist: ${SRC_DIR}" >&2
    exit 1
fi

################################################################################
# Main script logic
################################################################################
cd "${SRC_DIR}"

timestamp=$(date +%Y-%m-%d_%H%M%S)
archive_dir="${ARCHIVE_NAME}/${timestamp}"

cat<<EOF
================================================================================
Configuration
================================================================================
src_dir=[${SRC_DIR}]
archive_dir=[${archive_dir}]
dry_run=[${DRY_RUN}]
================================================================================
EOF

move-downloads "${archive_dir}"

echo "Done"
