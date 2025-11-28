#!/usr/bin/env bash
set -euET -o pipefail

# Query GreyNoise Community API for IP address information
# Provides threat intelligence data about IP addresses

script_name=$(basename ${BASH_SOURCE[0]})
script_dir=$(dirname ${BASH_SOURCE[0]})

################################################################################
# CLI Parameters
################################################################################
QUIET=false
VERBOSE=false
IP_ADDRESS=""

################################################################################
# Default values
################################################################################
GREYNOISE_API_URL="https://api.greynoise.io/v3/community"

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
Usage: ${script_name} [-hqv] <ip_address>

Query GreyNoise Community API for IP address information. Provides threat
intelligence data about IP addresses including classification, noise status,
and metadata.

Options
  -h               : Display this help message.
  -q               : Quiet mode. Output as little as possible.
  -v               : Verbose output. Show detailed request information.

Arguments
  <ip_address>     : IP address to query (required)

Example:
  ${script_name} 8.8.8.8
  ${script_name} -v 192.168.1.1
  ${script_name} -q 1.1.1.1
EOF
}

function validate-ip-address {
    local ip=$1
    local ip_regex="^([0-9]{1,3}\.){3}[0-9]{1,3}$"

    if [[ -z "${ip}" ]] ; then
	echo "Error: IP address is required" >&2
	return 1
    fi

    if [[ ! "${ip}" =~ ${ip_regex} ]] ; then
	echo "Error: Invalid IP address format: ${ip}" >&2
	return 1
    fi

    # Validate each octet is 0-255
    IFS='.' read -ra ADDR <<< "${ip}"
    for octet in "${ADDR[@]}" ; do
	if [[ "${octet}" -lt 0 ]] || [[ "${octet}" -gt 255 ]] ; then
	    echo "Error: Invalid IP address: ${ip} (octet ${octet} out of range)" >&2
	    return 1
	fi
    done

    return 0
}

function query-greynoise {
    local ip=$1
    local url="${GREYNOISE_API_URL}/${ip}"
    local response=""
    local http_code=0

    ${VERBOSE} && echo "Querying GreyNoise API for IP: ${ip}" >&2
    ${VERBOSE} && echo "URL: ${url}" >&2

    # Make API request
    response=$(curl -i -s -w "\n%{http_code}" "${url}" 2>/dev/null || {
	echo "Error: Failed to connect to GreyNoise API" >&2
	return 1
    })

    # Extract HTTP status code (last line)
    http_code=$(echo "${response}" | tail -n 1)

    # Extract response body (everything except last line)
    response=$(echo "${response}" | head -n -1)

    # Check HTTP status code
    if [[ "${http_code}" -eq 200 ]] ; then
	${QUIET} || echo "${response}"
	return 0
    elif [[ "${http_code}" -eq 404 ]] ; then
	${QUIET} || echo "IP address not found in GreyNoise database: ${ip}" >&2
	${VERBOSE} && echo "${response}" >&2
	return 0
    elif [[ "${http_code}" -eq 429 ]] ; then
	echo "Error: Rate limit exceeded. Please try again later." >&2
	${VERBOSE} && echo "${response}" >&2
	return 1
    elif [[ "${http_code}" -ge 400 ]] && [[ "${http_code}" -lt 500 ]] ; then
	echo "Error: Client error (HTTP ${http_code})" >&2
	${VERBOSE} && echo "${response}" >&2
	return 1
    elif [[ "${http_code}" -ge 500 ]] ; then
	echo "Error: Server error (HTTP ${http_code}). Please try again later." >&2
	${VERBOSE} && echo "${response}" >&2
	return 1
    else
	echo "Error: Unexpected HTTP status code: ${http_code}" >&2
	${VERBOSE} && echo "${response}" >&2
	return 1
    fi
}

################################################################################
# get command line options
################################################################################
while getopts ":hqv" opt; do
    case ${opt} in
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

# Get IP address from positional argument
if [[ $# -eq 0 ]] ; then
    usage "IP address is required"
    exit 1
fi

IP_ADDRESS=$1

################################################################################
# Validation
################################################################################
if ! validate-ip-address "${IP_ADDRESS}" ; then
    exit 1
fi

################################################################################
# Main script logic
################################################################################

${VERBOSE} && cat<<EOF
================================================================================
GreyNoise IP Lookup
================================================================================
IP_ADDRESS=[${IP_ADDRESS}]
API_URL=[${GREYNOISE_API_URL}]
QUIET=[${QUIET}]
VERBOSE=[${VERBOSE}]
================================================================================
EOF

# Query GreyNoise API
if ! query-greynoise "${IP_ADDRESS}" ; then
    exit 1
fi

${QUIET} || echo "Query complete" >&2
