#!/usr/bin/env bats
# Test file for clean-emacs-files.sh

load '../test_helper.bash'

@test "clean-emacs-files.sh: script exists and is executable" {
    local script_path=$(get_script_path "clean-emacs-files.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "clean-emacs-files.sh: has valid bash syntax" {
    skip_if_command_missing "bash"
    local script_path=$(get_script_path "clean-emacs-files.sh")
    run bash -n "${script_path}"
    assert_success
}

@test "clean-emacs-files.sh: finds emacs backup files" {
    # Create test emacs backup file
    local test_file="${TEST_TMPDIR}/test_file~"
    echo "test content" > "${test_file}"
    
    # Run script (non-interactive, will fail but should find the file)
    cd "${TEST_TMPDIR}"
    run bash -c "echo 'n' | $(get_script_path "clean-emacs-files.sh")" || true
    
    # Script should output the file name
    assert_output_contains "test_file~"
}
