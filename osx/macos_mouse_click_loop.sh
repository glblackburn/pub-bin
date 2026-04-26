#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename "$0")
script_dir=$(dirname "$0")

################################################################################
# CLI Parameters
################################################################################
cycle_max=
################################################################################
# default values
################################################################################
mouse_click=${script_dir}/macos_mouse_click.py

################################################################################
# show command usage
################################################################################
function usage {
    message=${1:-}
    if [ ! -z "${message}" ]; then
        echo "Message: ${message}"
    fi
    cat <<EOF
Usage: ${script_name} [-h] [-c <count>]

Operator loop: repeatedly runs a fixed buy ladder then a long cookie burst
via macos_mouse_click.py (see osx/README.md). Coordinates are machine-local.
Omit -c to run until stopped (sleep 30 seconds between cycles).

Options
  -h            : Display this help message.
  -c <count>    : Run exactly this many cycles (buy ladder + cookie burst each),
                 then exit. Example: -c 1 is one cycle; -c 10 runs ten.
                 Each cycle is real automation (clicks), not a dry run.

Example:
  ${script_name} -c 1
  ${script_name} -c 10
  ${script_name}
EOF
}

################################################################################
# get command line options
################################################################################
while getopts ":hc:" opt; do
    case ${opt} in
        h)
            usage
            exit 0
            ;;
        c)
            cycle_max=${OPTARG}
            ;;
        \?)
            usage "Invalid option: -${OPTARG}"
            exit 1
            ;;
        :)
            usage "Option -${OPTARG} requires an argument."
            exit 1
            ;;
    esac
done
shift $((OPTIND - 1))

if [ ! -f "${mouse_click}" ]; then
    usage "Clicker not found: ${mouse_click}"
    exit 1
fi

if [ ! -z "${cycle_max}" ]; then
    if ! [[ "${cycle_max}" =~ ^[1-9][0-9]*$ ]]; then
        usage "Invalid -c value: must be a positive integer (e.g. 1 or 10)."
        exit 1
    fi
fi

################################################################################
# main script logic
################################################################################
function run_once {
    date
    # uncomment export lines for debug output
    export MACOS_MOUSE_CLICK_DEBUG_TUI=yes
    export MACOS_MOUSE_CLICK_DEBUG_TUI_LOG=debug.json

    echo "buy time machine"
    "${mouse_click}" -d 0 -x 2344.4 -y 14.5888 -n 5 -Y
    echo "buy portal"
    "${mouse_click}" -d 0 -x 2344.4 -y -48.8354 -n 5 -Y
    echo "buy alchemy lab"
    "${mouse_click}" -d 0 -x 2344.4 -y -103.6 -n 5 -Y
    echo "buy shipment"
    "${mouse_click}" -d 0 -x 2344.4 -y -177.5 -n 5 -Y
    echo "buy wizard tower"
    "${mouse_click}" -d 0 -x 2344.4 -y -237.3 -n 5 -Y
    echo "buy temple"
    "${mouse_click}" -d 0 -x 2344.4 -y -304.6 -n 5 -Y
    echo "buy bank"
    "${mouse_click}" -d 0 -x 2344.4 -y -368.1 -n 5 -Y
    echo "buy factory"
    "${mouse_click}" -d 0 -x 2344.4 -y -430.9 -n 5 -Y
    echo "buy mine"
    "${mouse_click}" -d 0 -x 2344.4 -y -495.6 -n 5 -Y
    echo "buy farm"
    "${mouse_click}" -d 0 -x 2344.4 -y -558.5 -n 5 -Y
    echo "buy grandma"
    "${mouse_click}" -d 0 -x 2344.4 -y -623.4 -n 5 -Y
    echo "buy cursor"
    "${mouse_click}" -d 0 -x 2344.4 -y -689.3 -n 5 -Y

    echo "click the cookie"
    "${mouse_click}" -d 0 -x 1600.8 -y -410.9 -n 3000 -Y
    date
}

cycle_done=0
while true; do
    run_once
    cycle_done=$((cycle_done + 1))
    if [ ! -z "${cycle_max}" ] && [ "${cycle_done}" -ge "${cycle_max}" ]; then
        break
    fi
    sleep 30
done
