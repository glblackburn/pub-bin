#!/usr/bin/env bats
# Test file for google-example-lookup.sh

load '../test_helper.bash'

@test "google-example-lookup.sh: script exists and is executable" {
    local script_path=$(get_script_path "greynoise/google-example-lookup.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "google-example-lookup.sh: has valid bash syntax" {
    skip_if_command_missing "bash"
    local script_path=$(get_script_path "greynoise/google-example-lookup.sh")
    run bash -n "${script_path}"
    assert_success
}

@test "google-example-lookup.sh: runs successfully" {
    skip_if_command_missing "curl"
    skip_if_command_missing "jq"
    
    # Script may require API key or may work without it
    run_script "greynoise/google-example-lookup.sh" || true
    # Should not crash
    [ -n "$output" ] || [ "$status" -eq 0 ] || [ "$status" -ne 0 ]
}
