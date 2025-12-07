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
Usage: ${script_name} <target>

Record network port scanning results using nmap.

Options
  -h               : Display this help message.

Arguments
  <target>         : IP address or hostname to scan (required)

Example:
$ ${script_name} 192.168.1.1
$ ${script_name} example.com
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
    usage "Target IP address or hostname is required"
    exit 1
fi

target=${1}
outfile="${target}_nmap_oG_${ts}.txt"

nmap -Pn -oG ${outfile} ${target}

#outfile="${target}_nmap_o_${ts}.txt"
#nmap -o ${outfile} ${target}
