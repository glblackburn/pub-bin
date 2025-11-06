#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(dirname $0)

################################################################################
# CLI Parameters
################################################################################
VERBOSE=false

################################################################################
# main script logic
################################################################################
file=${1}

if [ -z "${file}" ] ; then
    echo "File is blank."
    exit 1
fi
if [ ! -f "${file}" ] ; then
    echo "Not a file: ${file}"
    exit 1
fi

new_file=$(echo "${file}" | sed "s/[^0-z.\/\-]/_/g" | cat -v)

if [ "${file}" != "${new_file}" ] ; then
    cat<<EOF
file    =[${file}]
new_file=[${new_file}]
mv "${file}" "${new_file}"
EOF
mv "${file}" "${new_file}"
else
    if [ ${VERBOSE} == true ] ; then
	cat<<EOF
SAME NAME: do nothing
file    =[${file}]
new_file=[${new_file}]
EOF
    fi
fi
