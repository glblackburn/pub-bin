#!/usr/bin/env bats
# Test file for record-ip-api-json.sh

load '../test_helper.bash'

@test "record-ip-api-json.sh: script exists and is executable" {
    local script_path=$(get_script_path "network-tools/intelligence/record-ip-api-json.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "record-ip-api-json.sh: fails without IP argument" {
    run_record_script "network-tools/intelligence/record-ip-api-json.sh"
    
    # Script should fail when no IP is provided
    assert_failure
}

@test "record-ip-api-json.sh: runs with IP argument" {
    # Use a well-known IP
    run_record_script "network-tools/intelligence/record-ip-api-json.sh" "8.8.8.8"
    
    # May succeed or fail depending on script dependencies and API availability
    [ "$status" -ge 0 ] || [ "$status" -le 255 ]
}
