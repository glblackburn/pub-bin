#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
config_dir=$(dirname $0)

################################################################################
# Load config library
################################################################################
. ${config_dir}/config.sh

################################################################################
# Default values
################################################################################
bin_config=${HOME}/.bin_config

################################################################################
# Functions
################################################################################
function check-legacy-config {
    if [ -e "${bin_config}" ] && [ ! -e "${config_file}" ] ; then
        cat<<EOF
================================================================================
Legacy config file found: ${bin_config}
================================================================================
EOF
        cat "${bin_config}"
        cat<<EOF

Would you like to migrate this config to the new location? (Y/n)
EOF
        read migrate
        if [ -z "${migrate}" ] || [ "${migrate}" = "y" ] || [ "${migrate}" = "Y" ] ; then
            ${config_dir}/migrate-config.sh
            exit 0
        fi
    fi
}

function read-config-values {
    cat<<EOF
================================================================================
Configuration Setup
================================================================================
This script will create a configuration file for pub-bin scripts.
Press Enter to use defaults or provide custom values.
EOF

    # Screenshot directory (required for clean-screenshots.sh)
    if [ -z "${screenshot_dir:-}" ] ; then
        screenshot_dir=$(setup-config-value "screenshot_dir" \
            "Enter the directory where screenshots should be archived. This directory will contain timestamped subdirectories for each cleanup session." \
            "${HOME}/Pictures/Screenshots" \
            "false")
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

check-legacy-config
read-config-values
save-config

cat<<EOF
================================================================================
Configuration complete!
================================================================================
EOF
