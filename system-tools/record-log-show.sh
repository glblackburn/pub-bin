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
log_dir=${HOME}/log
today=`date +%Y-%m-%d`
ts=`date +%Y-%m-%d_%H%M%S`
log=${log_dir}/log-show_${ts}.log

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

Record macOS login/logout events from system logs using log show.

Options
  -h               : Display this help message.

Note: This script is macOS-specific and requires the 'log' command.

Example:
$ ${script_name}
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

log show --start ${today} --style syslog --predicate 'process == "loginwindow"' --debug --info |
    tee ${log}

cat<<EOF
================================================================================
log=[${log}]
================================================================================
EOF
cat ${log} | grep "LWScreenLock startUnlock" | grep "inform UA unlocked"

cat<<EOF
================================================================================
log=[${log}]
================================================================================
EOF
