#!/usr/bin/env bash
# config.sh - Configuration library for pub-bin scripts
# Follows the modular sourcing pattern from set-h3-env.sh

################################################################################
# default values
################################################################################
config_dir=$(dirname $0)
pub_bin_dir=$(dirname ${config_dir})
config_file=${HOME}/.config/pub-bin/config
secure_dir=${HOME}/.secure
secure_config=${secure_dir}/secure-config.sh

################################################################################
# functions
################################################################################

# Load main config file (public settings)
function load-config {
    local noerror=${1:-}
    local verbose=${VERBOSE:-false}

    if [ -e "${config_file}" ] ; then
        . "${config_file}"
        if [ "${verbose}" = "true" ] ; then
            cat<<EOF
Loaded config from ${config_file}
EOF
        fi
    else
        if [ "${noerror}" != "noerror" ] ; then
            cat<<EOF>&2
Config not found: ${config_file}
Please run ${config_dir}/setup-config.sh or ${config_dir}/migrate-config.sh
EOF
            return 1
        fi
    fi
}

# Load secure config (sensitive data like API keys)
function load-secure-config {
    local noerror=${1:-}
    local verbose=${VERBOSE:-false}

    if [ -e "${secure_config}" ] ; then
        . "${secure_config}"
        if [ "${verbose}" = "true" ] ; then
            cat<<EOF
Loaded secure config from ${secure_config}
EOF
        fi
    else
        if [ "${noerror}" != "noerror" ] ; then
            cat<<EOF>&2
Secure config not found: ${secure_config}
Run setup script to create it if needed.
EOF
            return 1
        fi
    fi
}

# Load all configs (public + secure)
function load-all-configs {
    load-config "${1:-}"
    load-secure-config "noerror"  # Don't error if secure config missing
}

# Load script-specific config (e.g., config/clean-screenshots-config.sh)
function load-script-config {
    local script_name=$1
    local config_script="${config_dir}/${script_name}-config.sh"
    local verbose=${VERBOSE:-false}

    if [ -e "${config_script}" ] ; then
        . "${config_script}"
        if [ "${verbose}" = "true" ] ; then
            cat<<EOF
Loaded script config from ${config_script}
EOF
        fi
    fi
}

# Ensure config directory exists
function ensure-config-dir {
    local config_dir_path=$(dirname "${config_file}")
    if [ ! -d "${config_dir_path}" ] ; then
        mkdir -p "${config_dir_path}"
        chmod 700 "${config_dir_path}"
    fi
}

# Ensure secure directory exists
function ensure-secure-dir {
    if [ ! -d "${secure_dir}" ] ; then
        mkdir -p "${secure_dir}"
        chmod 700 "${secure_dir}"
    fi
}

# Show current config values (non-sensitive)
function show-config {
    if [ -e "${config_file}" ] ; then
        cat<<EOF
Public config (${config_file}):
--------------------------------------------------------------------------------
EOF
        cat "${config_file}"
    else
        cat<<EOF
Public config not found: ${config_file}
EOF
    fi
}
