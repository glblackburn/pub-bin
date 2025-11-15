#!/usr/bin/env bash
set -euET -o pipefail

# Process Azure Entra ID user Sign-in log JSON downloads
# Extracts authentication details including location and success status
# Outputs formatted table with selected fields

script_name=$(basename ${BASH_SOURCE[0]})
script_dir=$(dirname ${BASH_SOURCE[0]})

################################################################################
# CLI Parameters
################################################################################
QUIET=false
VERBOSE=false
INPUT_FILE=""
OUTPUT_FORMAT="table"  # table, csv, json

################################################################################
# Default values
################################################################################
# Default fields to extract from Azure Entra ID Sign-in logs
DEFAULT_FIELDS=".createdDateTime, .userPrincipalName, .ipAddress, .location.city, .location.state, .location.country, .authenticationDetails[].succeeded"
fields="${DEFAULT_FIELDS}"

################################################################################
# Functions
################################################################################
function usage {
    local message=${1:-}
    if [[ ! -z "${message}" ]] ; then
	echo "Error: ${message}" >&2
	echo "" >&2
    fi
    cat<<EOF
Usage: ${script_name} [-hqv] [-f <file>] [-o <format>] [<file>]

Process Azure Entra ID user Sign-in log JSON downloads. Extracts authentication
details including location and success status, then outputs the data in a
formatted table.

This script processes JSON files downloaded from Azure Entra ID Sign-in logs
and extracts specific fields for analysis.

Options
  -h               : Display this help message.
  -f <file>        : Input JSON file (required if not provided as positional argument)
  -o <format>      : Output format: table, csv, or json (Default: ${OUTPUT_FORMAT})
  -q               : Quiet mode. Output as little as possible.
  -v               : Verbose output. Show detailed processing information.

Arguments
  <file>           : Input JSON file (alternative to -f option)

Example:
  ${script_name} -f InteractiveSignIns_2023-03-02_2023-03-09.json
  ${script_name} InteractiveSignIns_2023-03-02_2023-03-09.json -o csv
  ${script_name} -f signins.json -v
EOF
}

function check-dependencies {
    if ! command -v jq &> /dev/null ; then
	echo "Error: jq is required but not installed" >&2
	echo "Install with: brew install jq" >&2
	return 1
    fi

    if ! command -v column &> /dev/null ; then
	${VERBOSE} && echo "Warning: column command not found. Table formatting may be limited." >&2
    fi

    return 0
}

function validate-input-file {
    local file=$1

    if [[ -z "${file}" ]] ; then
	usage "Input file is required"
	return 1
    fi

    if [[ ! -f "${file}" ]] ; then
	echo "Error: Input file does not exist: ${file}" >&2
	return 1
    fi

    if [[ ! -r "${file}" ]] ; then
	echo "Error: Input file is not readable: ${file}" >&2
	return 1
    fi

    # Check if file is valid JSON
    if ! jq empty "${file}" 2>/dev/null ; then
	echo "Error: Input file is not valid JSON: ${file}" >&2
	return 1
    fi

    return 0
}

function process-signin-log {
    local file=$1
    local fields=$2
    local format=$3
    local jq_output=""

    ${VERBOSE} && cat<<EOF >&2
Processing Azure Entra ID Sign-in log
file=[${file}]
fields=[${fields}]
format=[${format}]
EOF

    # Extract data using jq
    jq_output=$(jq -r ".[] | [${fields}] | @csv" "${file}" 2>/dev/null)
    if [[ $? -ne 0 ]] ; then
	echo "Error: Failed to process JSON file with jq" >&2
	return 1
    fi

    if [[ -z "${jq_output}" ]] ; then
	${QUIET} || echo "Warning: No data found in JSON file" >&2
	return 0
    fi

    # Format output based on requested format
    case "${format}" in
	table )
	    echo "${jq_output}" | sort | column -t -s ',' 2>/dev/null || echo "${jq_output}" | sort
	    ;;
	csv )
	    echo "${jq_output}" | sort
	    ;;
	json )
	    # Reconstruct as JSON array
	    echo "${jq_output}" | sort | jq -R -s 'split("\n") | map(select(length > 0)) | map(split(",") | {
		createdDateTime: .[0],
		userPrincipalName: .[1],
		ipAddress: .[2],
		city: .[3],
		state: .[4],
		country: .[5],
		authenticationSucceeded: .[6]
	    })' 2>/dev/null || {
		echo "Error: Failed to convert to JSON format" >&2
		return 1
	    }
	    ;;
	* )
	    echo "Error: Unknown output format: ${format}" >&2
	    echo "Supported formats: table, csv, json" >&2
	    return 1
	    ;;
    esac

    return 0
}

################################################################################
# get command line options
################################################################################
while getopts ":f:o:hqv" opt; do
    case ${opt} in
	f )
            INPUT_FILE=$OPTARG
            ;;
	o )
            OUTPUT_FORMAT=$OPTARG
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

# Handle positional argument for file
if [[ -z "${INPUT_FILE}" ]] && [[ $# -gt 0 ]] ; then
    INPUT_FILE=$1
fi

################################################################################
# Validation
################################################################################
if [[ -z "${INPUT_FILE}" ]] ; then
    usage "Input file is required"
    exit 1
fi

if [[ "${OUTPUT_FORMAT}" != "table" ]] && \
   [[ "${OUTPUT_FORMAT}" != "csv" ]] && \
   [[ "${OUTPUT_FORMAT}" != "json" ]] ; then
    usage "Output format must be one of: table, csv, json"
    exit 1
fi

################################################################################
# Main script logic
################################################################################

${VERBOSE} && cat<<EOF
================================================================================
Configuration
================================================================================
INPUT_FILE=[${INPUT_FILE}]
OUTPUT_FORMAT=[${OUTPUT_FORMAT}]
QUIET=[${QUIET}]
VERBOSE=[${VERBOSE}]
fields=[${fields}]
================================================================================
EOF

# Check dependencies
if ! check-dependencies ; then
    exit 1
fi

# Validate input file
if ! validate-input-file "${INPUT_FILE}" ; then
    exit 1
fi

# Process the sign-in log
if ! process-signin-log "${INPUT_FILE}" "${fields}" "${OUTPUT_FORMAT}" ; then
    exit 1
fi

${QUIET} || echo "Processing complete" >&2
