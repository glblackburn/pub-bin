#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(cd "$(dirname "$0")" && pwd)

################################################################################
# CLI Parameters
################################################################################
VERBOSE=false
YES=false
directory=.

################################################################################
# show command usage
################################################################################
function usage {
    #default message to blank if not passed
    message=${1:-}
    if [ ! -z "${message}" ] ; then
	echo "Message: ${message}"
    fi
cat<<EOF
Usage: ${script_name} [-hyv] [-d directory]

Generate MarkDown to generate clickable file list and clickable images from the directory.

This script will also rename all file that have spaces in the filename which is why there confirmation prompt is a -Y option to bypass the prompt.

Options
  -d               : Find based on directory.
  -h               : Display this help message.
  -Y               : answer YES and skip prompt. (needs more explination, but I'm too tired for that right now.)
  -v               : Verbose output (may contain sensitive data.  DO NOT use when logging output.)

Example:
$ ${script_name}
$ ${script_name} -Y
EOF
}

################################################################################
# get command line options
################################################################################
while getopts ":d:hYv" opt; do
    case ${opt} in
	d )
            directory=$OPTARG
            ;;
	v )
            VERBOSE=true
            ;;
	Y )
            YES=true
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

################################################################################
# main script logic
################################################################################

if [ -z "${directory}" ] ; then
    cat<<EOF
ERROR: directory cannot be blank.
EOF
    exit 1
fi
if [ ! -d "${directory}" ] ; then
    cat<<EOF
ERROR: directory does not exist: ${directory}
EOF
    exit 2
fi

if [ ${YES} == false ] ; then
    cat<<EOF
WARNING: This script is about to replace all the spaces in the filenames.
directory=[${directory}]
Are you sure you want me to do this?
type 'YES' to make it so.
EOF
    read response
    if [ "YES" == "${response}" ] ; then
	cat<<EOF
Release the hounds........
EOF
    else
	cat<<EOF
Okay.  It's your baby.
Stopping and exiting.
EOF
	exit
    fi
fi

cat<<EOF
================================================================================
Fix filenames with spaces
================================================================================
EOF
find ${directory} -type f | grep " " | fix-spaces-in-filenames.sh

cat<<EOF

## Files
EOF
find ${directory} -type f | sort | ${script_dir}/convert-to-md-file-link-list.sh

cat<<EOF

## Screenshots
EOF
find ${directory} -type f -name "*.png" -o -name "*.jpg" | sort | ${script_dir}/convert-to-md-clickable-image-list.sh
