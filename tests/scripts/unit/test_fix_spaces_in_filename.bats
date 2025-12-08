#!/usr/bin/env bats
# Test file for fix-spaces-in-filename.sh

load '../test_helper.bash'

@test "fix-spaces-in-filename.sh: script exists and is executable" {
    local script_path=$(get_script_path "fix-spaces-in-filename.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "fix-spaces-in-filename.sh: has valid bash syntax" {
    skip_if_command_missing "bash"
    local script_path=$(get_script_path "fix-spaces-in-filename.sh")
    run bash -n "${script_path}"
    assert_success
}

@test "fix-spaces-in-filename.sh: requires file argument" {
    # Script uses set -e, so unbound variable will cause failure before "File is blank" check
    run_script "fix-spaces-in-filename.sh"
    assert_failure
    # Script will fail with unbound variable error due to set -e
    assert_output_contains "unbound variable" || assert_output_contains "File is blank"
}

@test "fix-spaces-in-filename.sh: handles non-existent file" {
    run_script "fix-spaces-in-filename.sh" "/nonexistent/file"
    assert_failure
    assert_output_contains "Not a file"
}

@test "fix-spaces-in-filename.sh: renames file with spaces" {
    # Create test file with spaces
    local test_file="${TEST_TMPDIR}/test file with spaces.txt"
    echo "test content" > "${test_file}"
    
    run_script "fix-spaces-in-filename.sh" "${test_file}"
    
    assert_success
    # File should be renamed (spaces replaced with underscores)
    [ ! -f "${test_file}" ]
    [ -f "${TEST_TMPDIR}/test_file_with_spaces.txt" ]
}

@test "fix-spaces-in-filename.sh: does not rename file without spaces" {
    # Create test file without spaces
    local test_file="${TEST_TMPDIR}/testfile.txt"
    echo "test content" > "${test_file}"
    
    run_script "fix-spaces-in-filename.sh" "${test_file}"
    
    assert_success
    # File should still exist with original name
    [ -f "${test_file}" ]
}
