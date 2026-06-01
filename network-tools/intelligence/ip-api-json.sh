#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(dirname $0)

################################################################################
# CLI Parameters
################################################################################

################################################################################
# default values
################################################################################

################################################################################
# show command usage
################################################################################
function usage {
    message=${1:-}
    if [ ! -z "${message}" ] ; then
	echo "Message: ${message}"
    fi
    cat<<EOF
Usage: ${script_name} <ip>

Look up geo, ISP, and ASN information for an IP address using the
ip-api.com public API and pretty-print the JSON response via jq.

Options
  -h               : Display this help message.

Arguments
  <ip>             : IP address to look up (required)

Notes
  - Uses the free ip-api.com endpoint (no API key).
  - Free tier rate limit: 45 requests per minute per source IP.

Example:
\$ ${script_name} 8.8.8.8
EOF
}

################################################################################
# get command line options
################################################################################
while getopts ":h" opt; do
    case ${opt} in
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
# functions
################################################################################

################################################################################
# main script logic
################################################################################

if [ $# -lt 1 ]; then
    usage "IP address is required"
    exit 1
fi

ip=${1}

curl -s "http://ip-api.com/json/${ip}" | jq
