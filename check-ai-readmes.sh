#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(dirname $0)

find ~/data -type f -name "README*.md" |
    xargs grep -l -i "ai " |
    xargs grep -l -i commit |
    grep -v third-party |
    sort |
    while read file ; do
        echo ${file} ;
        dir=$(dirname ${file})
        cat<<EOF
================================================================================
file=[${file}]
dir=[${dir}]
================================================================================
EOF
        pushd ${dir}
        git status
    done
