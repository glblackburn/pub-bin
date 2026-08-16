#!/usr/bin/env bats
# Test file for load-ssh-key.sh -l option

load '../test_helper.bash'

################################################################################
# Test -l Option: List Keys
################################################################################

@test "load-ssh-key.sh -l: works when executed directly" {
    kill_all_ssh_agents
    
    # Should work when executed (not sourced)
    run_load_ssh_key_exec -l
    
    # Should report agent status (either "not running" or list of keys)
    assert_output_contains "SSH agent|loaded SSH keys|not running"
}

@test "load-ssh-key.sh -l: lists loaded keys correctly" {
    kill_all_ssh_agents
    
    # Create and load a test key
    local test_key=$(create_test_ssh_key "test_list_key")
    run_load_ssh_key -k "${test_key}" -q
    
    # Now list keys
    run_load_ssh_key -l
    
    assert_success
    # ssh-add -l outputs comments, not filenames - check for the comment used when creating the key
    assert_output_contains "test@example.com"
    assert_key_count 1
}

@test "load-ssh-key.sh -l: handles dead agent gracefully" {
    kill_all_ssh_agents
    
    # Set environment variables pointing to non-existent agent
    export SSH_AGENT_PID=99999
    export SSH_AUTH_SOCK="/tmp/nonexistent_socket"
    
    run_load_ssh_key_exec -l
    
    # Should detect dead agent and report appropriately
    # Output might be "SSH agent is not running" or similar
    assert_output_contains "not running|SSH agent|no identities"
}

@test "load-ssh-key.sh -l: names the key file for each loaded key" {
    kill_all_ssh_agents

    # Two keys with the same comment - the comment alone cannot identify them
    local key_one=$(create_test_ssh_key "list_alpha_key")
    local key_two=$(create_test_ssh_key "list_beta_key")
    run_load_ssh_key -k "${key_one},${key_two}" -q

    run_load_ssh_key -l

    assert_success
    assert_key_count 2
    assert_output_contains "list_alpha_key : "
    assert_output_contains "list_beta_key : "
}

@test "load-ssh-key.sh -l: reports an empty agent as zero keys" {
    kill_all_ssh_agents

    # Start an agent with no keys in it
    local test_key=$(create_test_ssh_key "list_empty_key")
    run_load_ssh_key -k "${test_key}" -q
    # run_load_ssh_key sources the agent vars back as plain shell variables,
    # so they must be exported before ssh-add can see the agent
    export SSH_AGENT_PID SSH_AUTH_SOCK
    ssh-add -D >/dev/null 2>&1 || true

    run_load_ssh_key -l

    assert_success
    assert_output_contains "No SSH keys are currently loaded"
    assert_output_not_contains "Failed to list SSH keys"
    assert_key_count 0
}
