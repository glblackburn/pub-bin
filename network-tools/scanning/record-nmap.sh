#!/usr/bin/env bash
set -euET -o pipefail

target=${1}
ts=`date +%Y-%m-%d_%H%M%S`

outfile="${target}_nmap_oG_${ts}.txt"
nmap -Pn -oG ${outfile} ${target}

#outfile="${target}_nmap_o_${ts}.txt"
#nmap -o ${outfile} ${target}
