#!/usr/bin/env bats
# Test file for start-cursor-agent.sh

load '../test_helper.bash'

@test "start-cursor-agent.sh: script exists and is executable" {
    local script_path=$(get_script_path "start-cursor-agent.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "start-cursor-agent.sh: has valid bash syntax" {
    skip_if_command_missing "bash"
    local script_path=$(get_script_path "start-cursor-agent.sh")
    run bash -n "${script_path}"
    assert_success
}

@test "start-cursor-agent.sh: requires cursor-agent command" {
    skip_if_command_missing "cursor-agent"
}
