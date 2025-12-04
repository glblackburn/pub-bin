#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(dirname $0)

# Created using Google Antigravity.

################################################################################
# CLI Parameters
################################################################################
QUIET=false
VERBOSE=false
target_dir=""

################################################################################
# default values
################################################################################
ts=`date +%Y-%m-%d_%H%M%S`

################################################################################
# show command usage
################################################################################
function usage {
    #default message to blank if not passed
    message=${1:-}
    if [ ! -z "${message}" ] ; then
	echo "Message: ${message}"
    fi
    cat<<EOF
Usage: ${script_name} [-hqv] -d <directory>

Find all .git directories in the given directory tree and run trufflehog on each
parent directory. Output is saved to a file in the target directory.

Options
  -h               : Display this help message.
  -d <directory>   : Target directory to scan (Required).
  -q               : Quiet mode. Output as little as possible.
  -v               : Verbose output.

Example:
$ ${script_name} -d /path/to/repos
EOF
}

################################################################################
# get command line options
################################################################################
while getopts ":d:hqv" opt; do
    case ${opt} in
	d )
            target_dir=$OPTARG
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
# main script logic
################################################################################

# Validation
if [ -z "${target_dir}" ]; then
    usage "Target directory (-d) is required"
    exit 1
fi

if [ ! -d "${target_dir}" ]; then
    echo "ERROR: Directory not found: ${target_dir}" >&2
    exit 1
fi

# Convert to absolute path
target_dir=$(cd "${target_dir}" && pwd)

if [ ${QUIET} != true ] ; then
    echo "Scanning directory: ${target_dir}"
fi

# Find git repos and run trufflehog
find "${target_dir}" -type d -name ".git" | while read -r git_dir; do
    repo_dir=$(dirname "${git_dir}")
    repo_name=$(basename "${repo_dir}")
    output_file="${target_dir}/trufflehog-${repo_name}-${ts}.txt"
    
    if [ ${QUIET} != true ] ; then
        echo "Scanning repository: ${repo_dir}"
        echo "Output: ${output_file}"
    fi

    # Initialize output file for this repo
    cat<<EOF > "${output_file}"
================================================================================
Trufflehog Scan Report
Repository: ${repo_dir}
Date: $(date)
================================================================================
EOF

    # Run trufflehog
    # Using || true to continue even if trufflehog finds issues (exit code 1)
    if ! trufflehog git "file://${repo_dir}" --results=verified,unknown >> "${output_file}" 2>&1; then
         # Check if it failed due to finding secrets (which returns 1) or actual error
         # For now we just capture everything.
         :
    fi
done

if [ ${QUIET} != true ] ; then
    echo "Scan complete. Results saved to ${target_dir}"
fi
