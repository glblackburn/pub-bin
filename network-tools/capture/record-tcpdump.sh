#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(dirname $0)

ts=`date +%Y-%m-%d_%H%M%S`

log_dir=log
log_file=${log_dir}/${script_name%.*}_${ts}.txt

mkdir -p ${log_dir}
sudo tcpdump -n | tee ${log_file}
