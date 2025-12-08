#!/usr/bin/env bats
# Test file for sort-netstat-tcp.sh

load '../test_helper.bash'

@test "sort-netstat-tcp.sh: script exists and is executable" {
    local script_path=$(get_script_path "network-tools/diagnostics/sort-netstat-tcp.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "sort-netstat-tcp.sh: has valid bash syntax" {
    skip_if_command_missing "bash"
    local script_path=$(get_script_path "network-tools/diagnostics/sort-netstat-tcp.sh")
    run bash -n "${script_path}"
    assert_success
}

@test "sort-netstat-tcp.sh: requires grep command" {
    skip_if_command_missing "grep"
}

@test "sort-netstat-tcp.sh: requires sort command" {
    skip_if_command_missing "sort"
}

@test "sort-netstat-tcp.sh: requires tee command" {
    skip_if_command_missing "tee"
}

@test "sort-netstat-tcp.sh: processes netstat file" {
    skip_if_command_missing "grep"
    skip_if_command_missing "sort"
    skip_if_command_missing "tee"
    
    # Create test netstat file with TCP lines
    local test_file="${TEST_OUTPUT_DIR}/record-netstat_2025-12-05_225356.txt"
    cat > "${test_file}" <<EOF
Active Internet connections
tcp        0      0 192.168.1.1:22          192.168.1.2:54321    ESTABLISHED
tcp        0      0 127.0.0.1:8080         127.0.0.1:54322      LISTEN
tcp        0      0 10.0.0.1:443           10.0.0.2:443         ESTABLISHED
udp        0      0 0.0.0.0:53             0.0.0.0:*            LISTEN
EOF
    
    cd "${TEST_OUTPUT_DIR}"
    run_script "network-tools/diagnostics/sort-netstat-tcp.sh" "${test_file}"
    
    assert_success
    # Should create sorted output file
    local sort_file="${TEST_OUTPUT_DIR}/record-netstat_2025-12-05_225356_tcp_sort.txt"
    [ -f "${sort_file}" ]
    assert_file_not_empty "${sort_file}"
    # Should only contain TCP lines
    assert_file_contains "${sort_file}" "tcp"
}
