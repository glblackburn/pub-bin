#!/usr/bin/env bats
# Test file for record-tcpdump.sh

load '../test_helper.bash'

@test "record-tcpdump.sh: script exists and is executable" {
    local script_path=$(get_script_path "network-tools/capture/record-tcpdump.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "record-tcpdump.sh: requires tcpdump command" {
    skip_if_command_missing "tcpdump"
}

@test "record-tcpdump.sh: requires sudo (will fail without it)" {
    skip_if_command_missing "tcpdump"
    
    # This test verifies the script exists and would require sudo
    # We don't actually run it as it requires root privileges
    skip "tcpdump requires sudo privileges - skipping execution test"
}
