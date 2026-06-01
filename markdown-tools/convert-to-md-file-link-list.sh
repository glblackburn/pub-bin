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

Read a list of filenames from stdin (one per line) and emit one
markdown bullet link per file: "* [<file>](<file>)".

Options
  -h               : Display this help message.

Example:
\$ ls -1 export* | ${script_name}
* [exported--result-1715263142794.csv](exported--result-1715263142794.csv)
* [exported--result-1715352554980.csv](exported--result-1715352554980.csv)
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
while read file ; do echo "* [${file}](${file})" ; done
