#!/usr/bin/env bats
# Test file for record-network-config.sh

load '../test_helper.bash'

@test "record-network-config.sh: script exists and is executable" {
    local script_path=$(get_script_path "network-tools/diagnostics/record-network-config.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "record-network-config.sh: requires ifconfig command" {
    skip_if_command_missing "ifconfig"
}

@test "record-network-config.sh: runs successfully" {
    skip_if_command_missing "ifconfig"
    
    run_record_script "network-tools/diagnostics/record-network-config.sh"
    
    assert_success
}

@test "record-network-config.sh: creates output files" {
    skip_if_command_missing "ifconfig"
    
    run_record_script "network-tools/diagnostics/record-network-config.sh"
    
    assert_success
    # Script creates multiple output files
    local files=$(find "${TEST_OUTPUT_DIR}" -name "net_*.txt" 2>/dev/null | wc -l | tr -d ' ')
    [ "${files}" -gt 0 ]
}
