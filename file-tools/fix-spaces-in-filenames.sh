#!/usr/bin/env bash
set -euET -o pipefail
script_dir=$(dirname $0)
script_name=$(basename $0)

# This script will loop over a list of files read from stdin and remove the spaces from the file name
#
# Example: find . -type f | grep " " | fix-spaces-in-filenames.sh

dir=${1:-}

if [ ! -z "${dir}" ] ; then
    cat<<EOF
do the dir thing: ${dir}
EOF
    if [ ! -d "${dir}" ] ; then
	cat<<EOF
ERROR: not a directory: ${dir}
EOF
	exit 2
    else
	find ${dir} -type f | grep " " |
	    while read file ; do
		${script_dir}/fix-spaces-in-filename.sh "${file}"
	    done
    fi
else
    cat<<EOF
read from stdin
EOF
    while read file ; do
	${script_dir}/fix-spaces-in-filename.sh "${file}"
    done
fi
