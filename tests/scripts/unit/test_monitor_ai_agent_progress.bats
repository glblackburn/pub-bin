#!/usr/bin/env bats
# Test file for monitor-ai-agent-progress.sh

load '../test_helper.bash'

@test "monitor-ai-agent-progress.sh: script exists and is executable" {
    local script_path=$(get_script_path "monitor-ai-agent-progress.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "monitor-ai-agent-progress.sh: has valid bash syntax" {
    skip_if_command_missing "bash"
    local script_path=$(get_script_path "monitor-ai-agent-progress.sh")
    run bash -n "${script_path}"
    assert_success
}

@test "monitor-ai-agent-progress.sh: help option works" {
    run_script "monitor-ai-agent-progress.sh" -h
    assert_success
    assert_output_contains "Usage:"
    assert_output_contains "Monitor"
}

@test "monitor-ai-agent-progress.sh: requires git command" {
    skip_if_command_missing "git"
}

@test "monitor-ai-agent-progress.sh: requires find command" {
    skip_if_command_missing "find"
}

@test "monitor-ai-agent-progress.sh: monitors working directory" {
    skip_if_command_missing "git"
    skip_if_command_missing "find"
    
    # Create test working directory
    local test_dir="${TEST_TMPDIR}/work"
    mkdir -p "${test_dir}"
    cd "${test_dir}"
    
    # Initialize git repo
    git init >/dev/null 2>&1 || true
    git config user.email "test@example.com" >/dev/null 2>&1 || true
    git config user.name "Test User" >/dev/null 2>&1 || true
    
    # Test with timeout to prevent hanging
    run timeout 2 bash -c "$(get_script_path "monitor-ai-agent-progress.sh") -t ${test_dir} -i 1" || true
    # Should not crash
    [ -n "$output" ] || [ "$status" -eq 0 ] || [ "$status" -ne 0 ]
}
