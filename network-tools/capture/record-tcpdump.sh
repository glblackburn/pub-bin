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
log_dir=log
log_file=${log_dir}/${script_name%.*}_${ts}.txt

################################################################################
# show command usage
################################################################################
function usage {
    message=${1:-}
    if [ ! -z "${message}" ] ; then
	echo "Message: ${message}"
    fi
    cat<<EOF
Usage: ${script_name}

Record network packet captures using tcpdump. Requires sudo privileges.

Options
  -h               : Display this help message.

Note: This script requires sudo privileges and runs continuously until stopped.

Example:
$ sudo ${script_name}
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

mkdir -p ${log_dir}
sudo tcpdump -n | tee ${log_file}
