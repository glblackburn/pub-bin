#!/usr/bin/env bash
# Helper functions for loading test key configuration from secure directory
# Follows the pattern from create-set-api-key.sh

################################################################################
# Load Test Key Configuration
################################################################################

# Load test key configuration from secure directory
# Usage: load_test_key_config
# Returns: 0 on success, 1 on failure
load_test_key_config() {
    local secure_dir="${HOME}/.secure"
    local config_file="${secure_dir}/load-ssh-key-test-keys.sh"
    
    # Check if config file exists
    if [ ! -f "${config_file}" ]; then
        echo "ERROR: Test key configuration file not found: ${config_file}" >&2
        echo "Please run: ./tests/load-ssh-key/archive/setup-test-keys-secure.sh" >&2
        echo "Or create it manually in ${secure_dir}/" >&2
        return 1
    fi
    
    # Temporarily disable set -u to safely source
    set +u
    source "${config_file}" 2>/dev/null || {
        echo "ERROR: Failed to load config file: ${config_file}" >&2
        set -u
        return 1
    }
    set -u
    
    # Verify required variables are set
    if [ -z "${TEST_KEY_NO_PASSPHRASE:-}" ] || [ -z "${TEST_KEY_WITH_PASSPHRASE:-}" ]; then
        echo "ERROR: Required test key variables not set in config file" >&2
        echo "Required: TEST_KEY_NO_PASSPHRASE, TEST_KEY_WITH_PASSPHRASE" >&2
        return 1
    fi
    
    # Export for use in scripts
    export TEST_KEY_NO_PASSPHRASE
    export TEST_KEY_WITH_PASSPHRASE
    export TEST_KEY_2="${TEST_KEY_2:-}"
    export TEST_KEY_3="${TEST_KEY_3:-}"
    
    return 0
}

# Get full path to a test key
# Usage: get_test_key_path <key_name>
# Returns: Full path to key file in ~/.ssh/
get_test_key_path() {
    local key_name="$1"
    if [ -z "${key_name}" ]; then
        echo "ERROR: Key name is required" >&2
        return 1
    fi
    
    # Expand ~ and resolve relative paths
    local key_path="${key_name/#\~/$HOME}"
    if [[ ! "${key_path}" =~ ^/ ]] ; then
        # Relative path - make it relative to ~/.ssh
        key_path="${HOME}/.ssh/${key_path}"
    fi
    
    echo "${key_path}"
}

# Verify test key configuration is loaded
# Usage: verify_test_key_config
# Returns: 0 if valid, 1 if invalid
verify_test_key_config() {
    if [ -z "${TEST_KEY_NO_PASSPHRASE:-}" ] || [ -z "${TEST_KEY_WITH_PASSPHRASE:-}" ]; then
        return 1
    fi
    return 0
}
