#!/usr/bin/env bash
# Helper functions specific to record*.sh scripts

################################################################################
# Script Execution Helpers
################################################################################

# Run a record script and capture output
# Usage: run_record_script "network-tools/diagnostics/record-netstat.sh" [args...]
run_record_script() {
    local script_path=$(get_script_path "$1")
    shift
    run bash "${script_path}" "$@"
}

# Run a record script in the test output directory
# Usage: run_record_script_in_output_dir "network-tools/diagnostics/record-netstat.sh" [args...]
run_record_script_in_output_dir() {
    local script_path=$(get_script_path "$1")
    shift
    cd "${TEST_OUTPUT_DIR}"
    run bash "${script_path}" "$@"
    cd "${PROJECT_ROOT}" || true
}

################################################################################
# Command Availability Helpers
################################################################################

# Check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Skip test if command doesn't exist
skip_if_command_missing() {
    local cmd="$1"
    if ! command_exists "${cmd}"; then
        skip "${cmd} is not installed"
    fi
}

# Skip test if not on macOS (for macOS-specific commands like 'log')
skip_if_not_macos() {
    if [[ "$(uname -s)" != "Darwin" ]]; then
        skip "This test is macOS-specific"
    fi
}

################################################################################
# Output File Helpers
################################################################################

# Find the first output file matching a pattern
# Usage: find_output_file "record-netstat_*.txt"
find_output_file() {
    local pattern="$1"
    find "${TEST_OUTPUT_DIR}" -name "${pattern}" 2>/dev/null | head -1
}

# Get all output files matching a pattern
# Usage: find_all_output_files "record-netstat_*.txt"
find_all_output_files() {
    local pattern="$1"
    find "${TEST_OUTPUT_DIR}" -name "${pattern}" 2>/dev/null
}

# Count output files matching a pattern
count_output_files() {
    local pattern="$1"
    find "${TEST_OUTPUT_DIR}" -name "${pattern}" 2>/dev/null | wc -l | tr -d ' '
}
