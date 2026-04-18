#!/usr/bin/env bash
set -euET -o pipefail

cat<<EOF
install directions
https://cursor.com/docs/cli/installation
EOF

curl https://cursor.com/install -fsS | bash
