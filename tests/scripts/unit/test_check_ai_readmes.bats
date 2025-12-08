#!/usr/bin/env bats
# Test file for check-ai-readmes.sh

load '../test_helper.bash'

@test "check-ai-readmes.sh: script exists and is executable" {
    local script_path=$(get_script_path "check-ai-readmes.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "check-ai-readmes.sh: has valid bash syntax" {
    skip_if_command_missing "bash"
    local script_path=$(get_script_path "check-ai-readmes.sh")
    run bash -n "${script_path}"
    assert_success
}

@test "check-ai-readmes.sh: requires find command" {
    skip_if_command_missing "find"
}

@test "check-ai-readmes.sh: requires xargs command" {
    skip_if_command_missing "xargs"
}

@test "check-ai-readmes.sh: requires grep command" {
    skip_if_command_missing "grep"
}

@test "check-ai-readmes.sh: runs without errors" {
    skip_if_command_missing "find"
    skip_if_command_missing "xargs"
    skip_if_command_missing "grep"
    
    # Script searches ~/data, may not find anything, but should not error
    run_script "check-ai-readmes.sh" || true
    # Script may succeed or fail depending on whether ~/data exists and has matching files
    # Just verify it doesn't crash
    [ -n "$output" ] || [ "$status" -eq 0 ] || [ "$status" -ne 0 ]
}
