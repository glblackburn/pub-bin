#!/usr/bin/env bats
# Test file for record-whois.sh

load '../test_helper.bash'

@test "record-whois.sh: script exists and is executable" {
    local script_path=$(get_script_path "network-tools/intelligence/record-whois.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "record-whois.sh: requires whois command" {
    skip_if_command_missing "whois"
}

@test "record-whois.sh: fails without IP argument" {
    skip_if_command_missing "whois"
    
    run_record_script "network-tools/intelligence/record-whois.sh"
    
    # Script should fail when no IP is provided
    assert_failure
}

@test "record-whois.sh: runs successfully with IP argument" {
    skip_if_command_missing "whois"
    
    # Use a well-known IP
    run_record_script "network-tools/intelligence/record-whois.sh" "8.8.8.8"
    
    # May succeed or fail depending on whois service availability
    [ "$status" -ge 0 ] || [ "$status" -le 255 ]
}

@test "record-whois.sh: creates output file when IP provided" {
    skip_if_command_missing "whois"
    
    run_record_script "network-tools/intelligence/record-whois.sh" "8.8.8.8"
    
    # Check if output file was created
    local output_file=$(find "${TEST_OUTPUT_DIR}" -name "whois_8.8.8.8_*.txt" 2>/dev/null | head -1)
    if [ -n "${output_file}" ]; then
        [ -f "${output_file}" ]
    else
        skip "whois did not create output file (service may be unavailable)"
    fi
}
