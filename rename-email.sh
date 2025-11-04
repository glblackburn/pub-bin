#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(dirname $0)

email_file="${1}"

#Date: Mon, 21 Oct 2024 14:12:28 +0000
#Date: 17 Dec 2024 13:21:32 -0500
#email_date=$(cat "${email_file}" | grep -e "^Date:" | head -1 | sed 's/Date: [A-z]*, //; s/\r//' )
email_date=$(cat "${email_file}" | grep -e "^Date:" | head -1 | sed 's/Date: //; s/\r//' | sed 's/^[A-z]*, //' )
cat<<EOF
email_file=[${email_file}]
email_date=[${email_date}]
EOF

new_date=$(gdate -d "${email_date}" "+%Y-%m-%d_%H%M%S")
new_file=${new_date}_$(echo "${email_file}" | sed "s/ /_/g")

cat<<EOF
new_date  =[${new_date}]
new_file  =[${new_file}]
EOF

mv "${email_file}" "${new_file}"

