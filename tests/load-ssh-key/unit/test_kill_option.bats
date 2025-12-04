#!/usr/bin/env bats
# Test file for load-ssh-key.sh -K option

load '../test_helper.bash'

################################################################################
# Test -K Option: Kill Agent
################################################################################

@test "load-ssh-key.sh -K: kills existing agent and starts new one" {
    # Start an agent first
    eval "$(ssh-agent -s)" >/dev/null 2>&1
    local original_pid="${SSH_AGENT_PID}"
    
    # Verify agent is running
    ps -p "${original_pid}" >/dev/null 2>&1 || {
        skip "Could not start test ssh-agent"
    }
    
    # Kill and restart
    run_load_ssh_key -K -q
    
    assert_success
    
    # Verify old agent is gone
    if ps -p "${original_pid}" >/dev/null 2>&1; then
        echo "ERROR: Old agent (PID ${original_pid}) is still running" >&2
        return 1
    fi
    
    # Verify new agent is running
    [ -n "${SSH_AGENT_PID:-}" ] || {
        echo "ERROR: New agent PID not set" >&2
        return 1
    }
    
    ps -p "${SSH_AGENT_PID}" >/dev/null 2>&1 || {
        echo "ERROR: New agent (PID ${SSH_AGENT_PID}) is not running" >&2
        return 1
    }
}

@test "load-ssh-key.sh -K: kills all ssh-agent processes" {
    # Start an agent
    kill_all_ssh_agents
    eval "$(ssh-agent -s)" >/dev/null 2>&1
    
    # Give it a moment to start
    sleep 0.1
    
    # Kill all
    run_load_ssh_key -K -q
    
    assert_success
    
    # Give it a moment to kill
    sleep 0.2
    
    # Verify no ssh-agents are running (allow for system agents like Chrome Remote Desktop)
    local agent_count=$(ps -fe | grep -E "[s]sh-agent" | grep -v "ChromeRemoteDesktopHost\|chromoting" | wc -l | tr -d ' ')
    [ "$agent_count" -eq 0 ] || {
        echo "ERROR: Found $agent_count ssh-agent process(es) still running" >&2
        ps -fe | grep -E "[s]sh-agent" | grep -v "ChromeRemoteDesktopHost\|chromoting" >&2
        return 1
    }
}

@test "load-ssh-key.sh -K -k: kills existing agent and loads specified key" {
    # Start an agent first
    kill_all_ssh_agents
    eval "$(ssh-agent -s)" >/dev/null 2>&1
    local original_pid="${SSH_AGENT_PID}"
    
    # Verify agent is running
    ps -p "${original_pid}" >/dev/null 2>&1 || {
        skip "Could not start test ssh-agent"
    }
    
    # Create a test key
    local test_key=$(create_test_ssh_key "test_key_kill_and_load")
    
    # Kill agent and load the specified key
    run_load_ssh_key -K -k "${test_key}" -q
    
    assert_success
    
    # Verify old agent is gone
    if ps -p "${original_pid}" >/dev/null 2>&1; then
        echo "ERROR: Old agent (PID ${original_pid}) is still running" >&2
        return 1
    fi
    
    # Verify new agent is running
    [ -n "${SSH_AGENT_PID:-}" ] || {
        echo "ERROR: New agent PID not set" >&2
        return 1
    }
    
    ps -p "${SSH_AGENT_PID}" >/dev/null 2>&1 || {
        echo "ERROR: New agent (PID ${SSH_AGENT_PID}) is not running" >&2
        return 1
    }
    
    # Verify the specified key is loaded
    run_load_ssh_key -l
    assert_success
    assert_key_count 1
    # Verify the key comment appears in output
    assert_output_contains "test@example.com"
}

@test "load-ssh-key.sh -K -k: works with absolute path to key" {
    # Start an agent first
    kill_all_ssh_agents
    eval "$(ssh-agent -s)" >/dev/null 2>&1
    local original_pid="${SSH_AGENT_PID}"
    
    # Verify agent is running
    ps -p "${original_pid}" >/dev/null 2>&1 || {
        skip "Could not start test ssh-agent"
    }
    
    # Create a test key (this will be in TEST_SSH_DIR, which is an absolute path)
    local test_key=$(create_test_ssh_key "test_key_absolute_path")
    
    # Verify we have an absolute path
    [[ "${test_key}" =~ ^/ ]] || {
        echo "ERROR: Test key path is not absolute: ${test_key}" >&2
        return 1
    }
    
    # Kill agent and load the specified key using absolute path
    # This mimics: . load-ssh-key.sh -K -k ${HOME}/.ssh/your-key.pem
    run_load_ssh_key -K -k "${test_key}" -q
    
    assert_success
    
    # Verify old agent is gone
    if ps -p "${original_pid}" >/dev/null 2>&1; then
        echo "ERROR: Old agent (PID ${original_pid}) is still running" >&2
        return 1
    fi
    
    # Verify new agent is running
    [ -n "${SSH_AGENT_PID:-}" ] || {
        echo "ERROR: New agent PID not set" >&2
        return 1
    }
    
    ps -p "${SSH_AGENT_PID}" >/dev/null 2>&1 || {
        echo "ERROR: New agent (PID ${SSH_AGENT_PID}) is not running" >&2
        return 1
    }
    
    # Verify the specified key is loaded
    run_load_ssh_key -l
    assert_success
    assert_key_count 1
    # Verify the key comment appears in output
    assert_output_contains "test@example.com"
}
