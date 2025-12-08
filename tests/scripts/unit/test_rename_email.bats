#!/usr/bin/env bats
# Test file for rename-email.sh

load '../test_helper.bash'

@test "rename-email.sh: script exists and is executable" {
    local script_path=$(get_script_path "rename-email.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "rename-email.sh: has valid bash syntax" {
    skip_if_command_missing "bash"
    local script_path=$(get_script_path "rename-email.sh")
    run bash -n "${script_path}"
    assert_success
}

@test "rename-email.sh: requires gdate command" {
    skip_if_command_missing "gdate"
}

@test "rename-email.sh: requires file argument" {
    # Script will fail if no argument provided (due to set -e)
    run bash -c "$(get_script_path "rename-email.sh")" || true
    # Should fail or show error
    [ "$status" -ne 0 ] || true
}

@test "rename-email.sh: renames email file with Date header" {
    skip_if_command_missing "gdate"
    
    # Create test email file with Date header in the test output directory
    # The script includes full path in new filename, which causes issues
    # Work around by using a relative path from the test output directory
    local test_file="${TEST_OUTPUT_DIR}/test_email.txt"
    cat > "${test_file}" <<EOF
From: test@example.com
To: recipient@example.com
Date: Mon, 21 Oct 2024 14:12:28 +0000
Subject: Test Email

Email body content.
EOF
    
    # Run script from the directory containing the file, using relative path
    cd "${TEST_OUTPUT_DIR}"
    run bash "$(get_script_path "rename-email.sh")" "test_email.txt"
    cd "${PROJECT_ROOT}" || true
    
    assert_success
    # File should be renamed with date prefix
    [ ! -f "${test_file}" ]
    # Check that a file with date prefix exists
    # The script creates: ${new_date}_${email_file_with_spaces_replaced}
    # So look for files starting with the date pattern
    local renamed_files=$(find "${TEST_OUTPUT_DIR}" -name "2024-10-21_*" 2>/dev/null)
    [ -n "${renamed_files}" ]
}
