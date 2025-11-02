#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(dirname $0)

################################################################################
# main script logic
################################################################################

temp_dir=`mktemp -d /tmp/${script_name}.XXXXXX` || exit 1
trap "rm -rf ${temp_dir}" EXIT
old_bin_list=`mktemp ${temp_dir}/old_bin_list.XXXXXX` || exit 1
pub_bin_list=`mktemp ${temp_dir}/pub_bin_list.XXXXXX` || exit 1

cat<<EOF
================================================================================
find pub-bin
================================================================================
EOF
find . -type f | grep -v '\.git' | sort | tee ${pub_bin_list}

cat<<EOF
================================================================================
find old-bin
================================================================================
EOF
pushd ../bin
find . -type f | grep -v '\.git' | sort | tee ${old_bin_list}

cat<<EOF
================================================================================
diff: 
================================================================================
EOF
diff ${old_bin_list} ${pub_bin_list}
