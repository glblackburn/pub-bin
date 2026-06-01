#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(cd "$(dirname "$0")" && pwd)

################################################################################
# show command usage
################################################################################
function usage {
    message=${1:-}
    if [ ! -z "${message}" ] ; then
	echo "Message: ${message}"
    fi
    cat<<EOF
Usage: ${script_name} [-h]

Read a list of image paths from stdin (one per line) and emit one
clickable markdown image per line: "[![<file>](<file>)](<file>)".
Clicking the rendered image opens the full-size original.

Options
  -h               : Display this help message.

Example:
\$ find screenshots -type f | ${script_name}
[![screenshots/Screenshot_2024-05-16_at_9.53.49_AM.png](screenshots/Screenshot_2024-05-16_at_9.53.49_AM.png)](screenshots/Screenshot_2024-05-16_at_9.53.49_AM.png)
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
# main script logic
################################################################################
while read file ; do echo "[![${file}](${file})](${file})" ; done
