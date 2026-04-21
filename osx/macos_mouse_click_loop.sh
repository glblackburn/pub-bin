#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(dirname $0)

################################################################################
# CLI Parameters
################################################################################
################################################################################
# default values
################################################################################
mouse_click=${script_dir}/macos_mouse_click.py
################################################################################
# main script logic
################################################################################
while (true) ; do
    date
    # uncomment export lines for debug output
    export MACOS_MOUSE_CLICK_DEBUG_TUI=yes
    export MACOS_MOUSE_CLICK_DEBUG_TUI_LOG=debug.json
    echo "buy alchemy lab"
    ${mouse_click} -d 0 -x 2344.4 -y -103.6 -n 5 -Y
    echo "buy shipment"
    ${mouse_click} -d 0 -x 2344.4 -y -177.5 -n 5 -Y
    echo "buy wizard tower"
    ${mouse_click} -d 0 -x 2344.4 -y -237.3 -n 5 -Y
    echo "buy temple"
    ${mouse_click} -d 0 -x 2344.4 -y -304.6 -n 5 -Y
    echo "click the cookie"
    ${mouse_click} -d 0 -x 1600.8 -y -410.9 -n 3000 -Y
    date
    sleep 25
done
