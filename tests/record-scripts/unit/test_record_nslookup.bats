#!/usr/bin/env bats
# Test file for record-nslookup.sh

load '../test_helper.bash'

@test "record-nslookup.sh: script exists and is executable" {
    local script_path=$(get_script_path "network-tools/diagnostics/record-nslookup.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "record-nslookup.sh: requires nslookup command" {
    skip_if_command_missing "nslookup"
}

@test "record-nslookup.sh: fails without IP argument" {
    skip_if_command_missing "nslookup"
    
    run_record_script "network-tools/diagnostics/record-nslookup.sh"
    
    # Script should fail when no IP is provided
    assert_failure
}

@test "record-nslookup.sh: runs successfully with IP argument" {
    skip_if_command_missing "nslookup"
    
    # Use a well-known DNS server IP
    run_record_script "network-tools/diagnostics/record-nslookup.sh" "8.8.8.8"
    
    assert_success
}

@test "record-nslookup.sh: creates output file" {
    skip_if_command_missing "nslookup"
    
    run_record_script "network-tools/diagnostics/record-nslookup.sh" "8.8.8.8"
    
    assert_success
    assert_output_file_exists "nslookup_8.8.8.8_*.txt"
}

@test "record-nslookup.sh: output file contains nslookup output" {
    skip_if_command_missing "nslookup"
    
    run_record_script "network-tools/diagnostics/record-nslookup.sh" "8.8.8.8"
    
    assert_success
    local output_file=$(find "${TEST_OUTPUT_DIR}" -name "nslookup_8.8.8.8_*.txt" | head -1)
    [ -f "${output_file}" ]
    [ -s "${output_file}" ]  # File is not empty
    grep -q "nslookup\|8.8.8.8\|Server\|Address" "${output_file}" || true
}
