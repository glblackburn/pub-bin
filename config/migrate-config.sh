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
function migrate-config {
    if [ ! -e "${bin_config}" ] ; then
        cat<<EOF
Legacy config file not found: ${bin_config}
Nothing to migrate.
EOF
        exit 0
    fi

    if [ -e "${config_file}" ] ; then
        cat<<EOF
New config file already exists: ${config_file}
Migration would overwrite existing config.

Current new config:
--------------------------------------------------------------------------------
EOF
        cat "${config_file}"
        cat<<EOF

Legacy config:
--------------------------------------------------------------------------------
EOF
        cat "${bin_config}"
        cat<<EOF

Do you want to overwrite the new config with values from legacy config? (y/N)
EOF
        read confirm
        if [ "${confirm}" != "y" ] && [ "${confirm}" != "Y" ] ; then
            echo "Migration cancelled."
            exit 0
        fi
    fi

    cat<<EOF
================================================================================
Migrating config from ${bin_config} to ${config_file}
================================================================================
EOF

    # Source the legacy config to get values
    . "${bin_config}"

    # Ensure config directory exists
    ensure-config-dir

    # Write new config file
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
Migration complete!
================================================================================
New config file created: ${config_file}
--------------------------------------------------------------------------------
EOF
    cat "${config_file}"
    cat<<EOF
================================================================================

You can now safely remove the legacy config file:
  rm ${bin_config}

Or keep it as a backup.
EOF
}

################################################################################
# Main script logic
################################################################################

migrate-config
