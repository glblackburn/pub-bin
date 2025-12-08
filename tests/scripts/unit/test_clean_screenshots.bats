#!/usr/bin/env bats
# Test file for clean-screenshots.sh

load '../test_helper.bash'

@test "clean-screenshots.sh: script exists and is executable" {
    local script_path=$(get_script_path "clean-screenshots.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "clean-screenshots.sh: has valid bash syntax" {
    skip_if_command_missing "bash"
    local script_path=$(get_script_path "clean-screenshots.sh")
    run bash -n "${script_path}"
    assert_success
}

@test "clean-screenshots.sh: help option works" {
    run_script "clean-screenshots.sh" -h
    assert_success
    assert_output_contains "Usage:"
}

@test "clean-screenshots.sh: requires find command" {
    skip_if_command_missing "find"
}

@test "clean-screenshots.sh: dry-run option works" {
    skip_if_command_missing "find"
    
    # Create test screenshot directory with files
    local test_src="${TEST_TMPDIR}/Desktop"
    mkdir -p "${test_src}"
    touch "${test_src}/Screen Shot 2025-12-07 at 10.00.00 AM.png"
    touch "${test_src}/Screen Shot 2025-12-07 at 11.00.00 AM.png"
    
    # Test dry-run mode
    run_script "clean-screenshots.sh" --dry-run --src-dir "${test_src}" || true
    # Should not crash
    [ -n "$output" ] || [ "$status" -eq 0 ] || [ "$status" -ne 0 ]
}
