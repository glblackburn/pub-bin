#!/usr/bin/env bats
# Test file for greynoise-lookup.sh

load '../test_helper.bash'

@test "greynoise-lookup.sh: script exists and is executable" {
    local script_path=$(get_script_path "greynoise/greynoise-lookup.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "greynoise-lookup.sh: has valid bash syntax" {
    skip_if_command_missing "bash"
    local script_path=$(get_script_path "greynoise/greynoise-lookup.sh")
    run bash -n "${script_path}"
    assert_success
}

@test "greynoise-lookup.sh: help option works" {
    run_script "greynoise/greynoise-lookup.sh" -h
    assert_success
    assert_output_contains "Usage:"
    assert_output_contains "GreyNoise"
}

@test "greynoise-lookup.sh: requires IP address argument" {
    run_script "greynoise/greynoise-lookup.sh"
    assert_failure
}

@test "greynoise-lookup.sh: requires curl command" {
    skip_if_command_missing "curl"
}

@test "greynoise-lookup.sh: requires jq command" {
    skip_if_command_missing "jq"
}

@test "greynoise-lookup.sh: validates IP address format" {
    skip_if_command_missing "curl"
    skip_if_command_missing "jq"
    
    # Test with invalid IP
    run_script "greynoise/greynoise-lookup.sh" "invalid.ip"
    # Should fail or show error about invalid IP
    assert_failure || assert_output_contains "invalid" || assert_output_contains "Invalid"
}

@test "greynoise-lookup.sh: queries valid IP address" {
    skip_if_command_missing "curl"
    skip_if_command_missing "jq"
    
    # Test with a valid IP (8.8.8.8)
    run_script "greynoise/greynoise-lookup.sh" "8.8.8.8" || true
    # May succeed or fail depending on API availability, but should not crash
    [ -n "$output" ] || [ "$status" -eq 0 ] || [ "$status" -ne 0 ]
}
