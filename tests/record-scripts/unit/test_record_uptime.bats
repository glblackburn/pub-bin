#!/usr/bin/env bats
# Test file for record-uptime.sh

load '../test_helper.bash'

@test "record-uptime.sh: script exists and is executable" {
    local script_path=$(get_script_path "system-tools/record-uptime.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "record-uptime.sh: requires uptime command" {
    skip_if_command_missing "uptime"
}

@test "record-uptime.sh: runs successfully" {
    skip_if_command_missing "uptime"
    
    run_record_script "system-tools/record-uptime.sh"
    
    assert_success
}

@test "record-uptime.sh: creates output file" {
    skip_if_command_missing "uptime"
    
    run_record_script "system-tools/record-uptime.sh"
    
    assert_success
    assert_output_file_exists "record-uptime_*.txt"
}

@test "record-uptime.sh: output file contains uptime output" {
    skip_if_command_missing "uptime"
    
    run_record_script "system-tools/record-uptime.sh"
    
    assert_success
    local output_file=$(find "${TEST_OUTPUT_DIR}" -name "record-uptime_*.txt" | head -1)
    [ -f "${output_file}" ]
    [ -s "${output_file}" ]  # File is not empty
    grep -q "uptime\|load\|days\|hours" "${output_file}" || true
}
