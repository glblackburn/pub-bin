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
output_dir=""

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
Usage: ${script_name} [-hqv] -d <directory> [-o <output_directory>]

Find all .git directories in the given directory tree and run trufflehog on each
parent directory. Output is saved to a file in the target directory or specified output directory.

Options
  -h               : Display this help message.
  -d <directory>   : Target directory to scan (Required).
  -o <directory>   : Output directory for reports (Default: target directory).
  -q               : Quiet mode. Output as little as possible.
  -v               : Verbose output.

Example:
$ ${script_name} -d /path/to/repos
$ ${script_name} -d /path/to/repos -o /tmp/logs
EOF
}

################################################################################
# get command line options
################################################################################
while getopts ":d:o:hqv" opt; do
    case ${opt} in
	d )
            target_dir=$OPTARG
            ;;
	o )
            output_dir=$OPTARG
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

# Handle output directory
if [ -z "${output_dir}" ]; then
    output_dir="${target_dir}"
else
    # Create output directory if it doesn't exist
    if [ ! -d "${output_dir}" ]; then
        mkdir -p "${output_dir}" || {
            echo "ERROR: Could not create output directory: ${output_dir}" >&2
            exit 1
        }
    fi
    output_dir=$(cd "${output_dir}" && pwd)
fi

if [ ${QUIET} != true ] ; then
    echo "Scanning directory: ${target_dir}"
    echo "Output directory: ${output_dir}"
fi

# Check if trufflehog is installed
if ! command -v trufflehog &> /dev/null; then
    echo "trufflehog command not found" >&2
    # Try to install using Makefile if it exists
    if [ -f "${script_dir}/Makefile" ]; then
        echo "Attempting to install trufflehog using Makefile..." >&2
        if (cd "${script_dir}" && make install-trufflehog); then
            echo "✓ trufflehog installed successfully" >&2
            # Re-check if trufflehog is now in PATH
            if ! command -v trufflehog &> /dev/null; then
                echo "WARNING: trufflehog was installed but is not in PATH" >&2
                echo "You may need to add the install directory to your PATH" >&2
                echo "Run 'make check' in ${script_dir} for details" >&2
                exit 1
            fi
        else
            echo "ERROR: Failed to install trufflehog using Makefile" >&2
            echo "Please install trufflehog manually:" >&2
            echo "  1. Run 'make install-trufflehog' in ${script_dir}" >&2
            echo "  2. Install manually: https://github.com/trufflesecurity/trufflehog#installation" >&2
            exit 1
        fi
    else
        echo "ERROR: trufflehog command not found and no Makefile available" >&2
        echo "Please install trufflehog manually:" >&2
        echo "  https://github.com/trufflesecurity/trufflehog#installation" >&2
        exit 1
    fi
fi

# Find git repos and run trufflehog
find "${target_dir}" -type d -name ".git" | while read -r git_dir; do
    repo_dir=$(dirname "${git_dir}")
    repo_name=$(basename "${repo_dir}")
    output_file="${output_dir}/trufflehog-${repo_name}-${ts}.txt"
    
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
         # If the error is "command not found", we should have caught it earlier, but check anyway
         if grep -q "command not found" "${output_file}" 2>/dev/null; then
             echo "ERROR: trufflehog command not found when scanning ${repo_dir}" >&2
             echo "Please install trufflehog first. Run 'make install-trufflehog' in ${script_dir}." >&2
             exit 1
         fi
         # Otherwise, it's likely just secrets found (exit code 1), which is expected
    fi
done

if [ ${QUIET} != true ] ; then
    echo "Scan complete. Results saved to ${output_dir}"
fi
