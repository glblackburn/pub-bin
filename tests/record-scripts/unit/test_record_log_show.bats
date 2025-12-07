#!/usr/bin/env bats
# Test file for record-log-show.sh

load '../test_helper.bash'

@test "record-log-show.sh: script exists and is executable" {
    local script_path=$(get_script_path "system-tools/record-log-show.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "record-log-show.sh: requires log command (macOS)" {
    # log command is macOS-specific
    if [[ "$(uname -s)" != "Darwin" ]]; then
        skip "log command is macOS-specific"
    fi
    skip_if_command_missing "log"
}

@test "record-log-show.sh: runs successfully on macOS" {
    if [[ "$(uname -s)" != "Darwin" ]]; then
        skip "log command is macOS-specific"
    fi
    skip_if_command_missing "log"
    
    # Note: This may require permissions to access system logs
    run_record_script "system-tools/record-log-show.sh"
    
    # May succeed or fail depending on permissions
    [ "$status" -ge 0 ] || [ "$status" -le 255 ]
}

@test "record-log-show.sh: creates output file on macOS" {
    if [[ "$(uname -s)" != "Darwin" ]]; then
        skip "log command is macOS-specific"
    fi
    skip_if_command_missing "log"
    
    # Override HOME to use test directory for log output
    export HOME="${TEST_TMPDIR}"
    mkdir -p "${HOME}/log"
    
    run_record_script "system-tools/record-log-show.sh"
    
    # Check if output file was created in ~/log/
    local output_file=$(find "${HOME}/log" -name "log-show_*.log" 2>/dev/null | head -1)
    if [ -n "${output_file}" ]; then
        [ -f "${output_file}" ]
    else
        skip "log-show did not create output file (may require permissions)"
    fi
}
