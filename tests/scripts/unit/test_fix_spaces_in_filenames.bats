#!/usr/bin/env bats
# Test file for fix-spaces-in-filenames.sh

load '../test_helper.bash'

@test "fix-spaces-in-filenames.sh: script exists and is executable" {
    local script_path=$(get_script_path "fix-spaces-in-filenames.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "fix-spaces-in-filenames.sh: has valid bash syntax" {
    skip_if_command_missing "bash"
    local script_path=$(get_script_path "fix-spaces-in-filenames.sh")
    run bash -n "${script_path}"
    assert_success
}

@test "fix-spaces-in-filenames.sh: processes files from stdin" {
    # Create test files with spaces
    local test_file1="${TEST_TMPDIR}/test file 1.txt"
    local test_file2="${TEST_TMPDIR}/test file 2.txt"
    echo "content1" > "${test_file1}"
    echo "content2" > "${test_file2}"
    
    # Run script with files from stdin
    echo -e "${test_file1}\n${test_file2}" | run bash -c "$(get_script_path "fix-spaces-in-filenames.sh")"
    
    # Files should be renamed
    [ ! -f "${test_file1}" ]
    [ ! -f "${test_file2}" ]
    [ -f "${TEST_TMPDIR}/test_file_1.txt" ]
    [ -f "${TEST_TMPDIR}/test_file_2.txt" ]
}

@test "fix-spaces-in-filenames.sh: processes directory" {
    # Create test directory with files containing spaces
    local test_dir="${TEST_TMPDIR}/test_dir"
    mkdir -p "${test_dir}"
    echo "content1" > "${test_dir}/file with spaces.txt"
    echo "content2" > "${test_dir}/another file.txt"
    
    run_script "fix-spaces-in-filenames.sh" "${test_dir}"
    
    assert_success
    # Files should be renamed
    [ -f "${test_dir}/file_with_spaces.txt" ]
    [ -f "${test_dir}/another_file.txt" ]
}

@test "fix-spaces-in-filenames.sh: handles non-existent directory" {
    run_script "fix-spaces-in-filenames.sh" "/nonexistent/dir"
    assert_failure
    assert_output_contains "not a directory"
}
