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
    date ;
    MACOS_MOUSE_CLICK_DEBUG_TUI=yes \
        MACOS_MOUSE_CLICK_DEBUG_TUI_LOG=debug.json \
        ${mouse_click} -d 0 -x 1600.8 -y -410.9 -n 3000 -Y ;
    date ;
    sleep 25 ;
done
