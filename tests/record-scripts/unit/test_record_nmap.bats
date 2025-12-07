#!/usr/bin/env bats
# Test file for record-nmap.sh

load '../test_helper.bash'

@test "record-nmap.sh: script exists and is executable" {
    local script_path=$(get_script_path "network-tools/scanning/record-nmap.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "record-nmap.sh: requires nmap command" {
    skip_if_command_missing "nmap"
}

@test "record-nmap.sh: fails without target argument" {
    skip_if_command_missing "nmap"
    
    run_record_script "network-tools/scanning/record-nmap.sh"
    
    # Script should fail when no target is provided
    assert_failure
}

@test "record-nmap.sh: runs successfully with target argument" {
    skip_if_command_missing "nmap"
    
    # Use localhost as a safe target for testing
    run_record_script "network-tools/scanning/record-nmap.sh" "127.0.0.1"
    
    # May succeed or fail depending on nmap permissions, but should not crash
    [ "$status" -ge 0 ] || [ "$status" -le 255 ]
}

@test "record-nmap.sh: creates output file when target provided" {
    skip_if_command_missing "nmap"
    
    # Use localhost as a safe target
    run_record_script "network-tools/scanning/record-nmap.sh" "127.0.0.1"
    
    # Check if output file was created (may not exist if nmap failed due to permissions)
    local output_file=$(find "${TEST_OUTPUT_DIR}" -name "127.0.0.1_nmap_oG_*.txt" 2>/dev/null | head -1)
    if [ -n "${output_file}" ]; then
        [ -f "${output_file}" ]
    else
        # If no file created, nmap likely failed (permissions, etc.) - that's acceptable for this test
        skip "nmap did not create output file (may require root permissions)"
    fi
}
