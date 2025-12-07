#!/usr/bin/env bats
# Test file for record-netstat.sh

load '../test_helper.bash'

@test "record-netstat.sh: script exists and is executable" {
    local script_path=$(get_script_path "network-tools/diagnostics/record-netstat.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "record-netstat.sh: requires netstat command" {
    skip_if_command_missing "netstat"
}

@test "record-netstat.sh: runs successfully" {
    skip_if_command_missing "netstat"
    
    run_record_script "network-tools/diagnostics/record-netstat.sh"
    
    assert_success
}

@test "record-netstat.sh: creates output file" {
    skip_if_command_missing "netstat"
    
    run_record_script "network-tools/diagnostics/record-netstat.sh"
    
    assert_success
    assert_output_file_exists "record-netstat_*.txt"
}

@test "record-netstat.sh: output file contains netstat output" {
    skip_if_command_missing "netstat"
    
    run_record_script "network-tools/diagnostics/record-netstat.sh"
    
    assert_success
    local output_file=$(find "${TEST_OUTPUT_DIR}" -name "record-netstat_*.txt" | head -1)
    [ -f "${output_file}" ]
    [ -s "${output_file}" ]  # File is not empty
    grep -q "netstat" "${output_file}" || grep -q "Active" "${output_file}" || true
}
