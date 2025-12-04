#!/usr/bin/env bash
# SSH-specific test helper functions

################################################################################
# SSH Agent Management
################################################################################

# Kill all ssh-agent processes (for test cleanup)
kill_all_ssh_agents() {
    pkill -9 ssh-agent 2>/dev/null || true
    unset SSH_AGENT_PID
    unset SSH_AUTH_SOCK
    sleep 0.5
}

# Create a test SSH key
# Usage: create_test_ssh_key <key_name> [passphrase]
create_test_ssh_key() {
    local key_name="$1"
    local passphrase="${2:-}"
    local key_path="${TEST_SSH_DIR}/${key_name}"
    
    if [ -z "$passphrase" ]; then
        ssh-keygen -t ed25519 -f "${key_path}" -N "" -C "test@example.com" >/dev/null 2>&1
    else
        echo -e "${passphrase}\n${passphrase}" | ssh-keygen -t ed25519 -f "${key_path}" -N "${passphrase}" -C "test@example.com" >/dev/null 2>&1
    fi
    
    echo "${key_path}"
}

# Get count of loaded SSH keys
# Usage: get_loaded_key_count
get_loaded_key_count() {
    if [ -z "${SSH_AUTH_SOCK:-}" ]; then
        echo "0"
        return
    fi
    
    local count=$(ssh-add -l 2>/dev/null | grep -c "SHA256:" || echo "0")
    echo "$count"
}

# Get list of loaded SSH keys
# Usage: get_loaded_keys
get_loaded_keys() {
    if [ -z "${SSH_AUTH_SOCK:-}" ]; then
        echo ""
        return
    fi
    
    ssh-add -l 2>/dev/null || echo ""
}

# Check if SSH agent is running
# Returns 0 if running, 1 if not
is_ssh_agent_running() {
    if [ -z "${SSH_AGENT_PID:-}" ]; then
        return 1
    fi
    
    ps -p "${SSH_AGENT_PID}" >/dev/null 2>&1
}

################################################################################
# Test Key Management
################################################################################

# Setup test SSH keys
# Usage: setup_test_keys [key1] [key2] ...
setup_test_keys() {
    local key_names=("$@")
    
    if [ ${#key_names[@]} -eq 0 ]; then
        # Create default test keys
        create_test_ssh_key "test_key_1"
        create_test_ssh_key "test_key_2"
        create_test_ssh_key "test_key_with_passphrase" "testpass123"
    else
        for key_name in "${key_names[@]}"; do
            create_test_ssh_key "${key_name}"
        done
    fi
}

# Cleanup test SSH keys
cleanup_test_keys() {
    rm -f "${TEST_SSH_DIR}"/test_* "${TEST_SSH_DIR}"/*.pub 2>/dev/null || true
}
