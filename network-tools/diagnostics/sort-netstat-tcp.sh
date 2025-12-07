#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(dirname $0)

netstat_file=${1:-record-netstat_2025-12-05_225356.txt}

sort_file=${netstat_file%.*}_tcp_sort.txt

cat ${netstat_file} | grep "^tcp" | sort | tee ${sort_file}
