#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
config_dir=$(dirname $0)

################################################################################
# Load config library
################################################################################
. ${config_dir}/config.sh

################################################################################
# Functions
################################################################################
function read-config-values {
    cat<<EOF
================================================================================
Configuration Setup
================================================================================
This script will create a configuration file for pub-bin scripts.
Press Enter to use defaults or provide custom values.
EOF

    # Email (optional)
    if [ -z "${email:-}" ] ; then
        echo "Enter email (optional, press Enter to skip):"
        read email
    fi

    # Name (optional)
    if [ -z "${name:-}" ] ; then
        echo "Enter name (optional, press Enter to skip):"
        read name
    fi

    # Screenshot directory (required for clean-screenshots.sh)
    if [ -z "${screenshot_dir:-}" ] ; then
        default_screenshot_dir="${HOME}/Pictures/Screenshots"
        echo "Enter screenshot directory (default: ${default_screenshot_dir}):"
        read screenshot_dir
        screenshot_dir="${screenshot_dir:-${default_screenshot_dir}}"
    fi
}

function save-config {
    ensure-config-dir

    cat<<EOF
================================================================================
Saving config to ${config_file}
================================================================================
EOF

    {
        if [ ! -z "${email:-}" ] ; then
            echo "email=\"${email}\""
        fi
        if [ ! -z "${name:-}" ] ; then
            echo "name=\"${name}\""
        fi
        if [ ! -z "${screenshot_dir:-}" ] ; then
            echo "screenshot_dir=\"${screenshot_dir}\""
        fi
    } > "${config_file}"

    chmod 600 "${config_file}"

    cat<<EOF
Config saved successfully.
EOF
    show-config
}

################################################################################
# Main script logic
################################################################################

read-config-values
save-config

cat<<EOF
================================================================================
Configuration complete!
================================================================================
EOF
