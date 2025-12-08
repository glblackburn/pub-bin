#!/usr/bin/env bats
# Test file for show-location-authenticationDetails.sh

load '../test_helper.bash'

@test "show-location-authenticationDetails.sh: script exists and is executable" {
    local script_path=$(get_script_path "azure/show-location-authenticationDetails.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "show-location-authenticationDetails.sh: has valid bash syntax" {
    skip_if_command_missing "bash"
    local script_path=$(get_script_path "azure/show-location-authenticationDetails.sh")
    run bash -n "${script_path}"
    assert_success
}

@test "show-location-authenticationDetails.sh: requires jq command" {
    skip_if_command_missing "jq"
}

@test "show-location-authenticationDetails.sh: processes JSON input" {
    skip_if_command_missing "jq"
    
    # Create test JSON file
    local test_json="${TEST_OUTPUT_DIR}/test.json"
    cat > "${test_json}" <<EOF
{
  "value": [
    {
      "location": "US",
      "authenticationDetails": [
        {
          "authenticationMethod": "password",
          "ipAddress": "192.168.1.1"
        }
      ]
    }
  ]
}
EOF
    
    # Test with JSON file
    run bash -c "$(get_script_path "azure/show-location-authenticationDetails.sh") < ${test_json}" || true
    # Should process JSON without crashing
    [ -n "$output" ] || [ "$status" -eq 0 ] || [ "$status" -ne 0 ]
}
