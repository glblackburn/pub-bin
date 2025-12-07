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
ts=`date +%Y-%m-%d_%H%M%S`

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

Record IP API/WHOIS data in JSON format using ip-api-json.sh.

Options
  -h               : Display this help message.

Arguments
  <ip>             : IP address to lookup (required)

Example:
$ ${script_name} 8.8.8.8
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
output_file=ip-api-whois_${ip}_${ts}.txt

command="ip-api-json.sh ${ip}"
{
    cat<<EOF
ts=[${ts}]
command=[${command}]
output_file=[${output_file}]
EOF
    ${command}
} | tee ${output_file}
