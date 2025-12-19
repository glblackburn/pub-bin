#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(dirname $0)

################################################################################
# CLI Parameters
################################################################################
dir=${1}
VERBOSE=false

################################################################################
# main script logic
################################################################################

IFS=$'\n'
readarray -t lines < <(
    find ${dir} -type f -name '*-2025-12-04_182609.txt' |
        xargs cat |
        grep -e "Detector Type" -e "Decoder Type" -e "Raw" |
        sort |
        uniq -c |
        grep "Raw result:" |
        sed "s/Raw result:.*$/Raw result:  *secret masked*/" |
        sort -n
)

sum=0
count=0
for line in "${lines[@]}" ; do
    num=$(echo "$line" | awk '{print $1}' | tr -d '[:space:]')
    # Skip empty or non-numeric
    if [[ "$num" =~ ^[0-9]+$ ]]; then
        sum=$((sum + num))
        count=$((count + 1))
    fi
    ${VERBOSE} && cat<<EOF >&2
count=[${count}]
num=[${num}]
sum=[${sum}]
EOF
done

${VERBOSE} && cat<<EOF >&2
count=[${count}]
sum=[${sum}]
EOF

cat<<EOF
${count} ${sum}
EOF
