#!/usr/bin/env bash
# BATS test helper - Setup and common functions for general script tests

################################################################################
# Test Setup
################################################################################

# Get the absolute path to the tests directory
if [ -n "${BATS_TEST_FILENAME:-}" ]; then
    # If loaded from a test file, resolve relative to test file location
    TEST_FILE_DIR="$(cd "$(dirname "${BATS_TEST_FILENAME}")" && pwd)"
    # Go up from unit/ or integration/ to scripts/, or stay in scripts/ if already there
    if [ "$(basename "${TEST_FILE_DIR}")" = "unit" ] || [ "$(basename "${TEST_FILE_DIR}")" = "integration" ]; then
        TEST_DIR="$(cd "${TEST_FILE_DIR}/.." && pwd)"
    else
        TEST_DIR="${TEST_FILE_DIR}"
    fi
else
    # Fallback: assume we're in tests/scripts/ directory
    TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

# PROJECT_ROOT is the directory containing the scripts (parent of tests/)
PROJECT_ROOT="$(cd "${TEST_DIR}/../.." && pwd)"

# Export for use in tests
export TEST_DIR
export PROJECT_ROOT

# Load helper modules
if [ -n "${BATS_TEST_FILENAME:-}" ]; then
    # Test file is loading this, so paths are relative to test file
    load "../helpers/assertions.bash"
else
    # Direct execution (shouldn't happen, but fallback)
    load "${TEST_DIR}/helpers/assertions.bash"
fi

################################################################################
# Setup and Teardown
################################################################################

# Global setup - runs once before all tests in a file
setup_file() {
    # Get test file name for directory naming
    local test_file_name="test"
    if [ -n "${BATS_TEST_FILENAME:-}" ]; then
        # Extract test file name without extension
        test_file_name=$(basename "${BATS_TEST_FILENAME}" .bats)
    fi
    
    # Create temporary directory in /tmp/ with test file name
    export TEST_TMPDIR=$(mktemp -d "/tmp/${test_file_name}.XXXXXX")
    export TEST_OUTPUT_DIR="${TEST_TMPDIR}/output"
    mkdir -p "${TEST_OUTPUT_DIR}"
    
    # Setup test output directory
    setup_test_output_dir
}

# Global teardown - runs once after all tests in a file
teardown_file() {
    # Clean up temporary directories
    if [ -n "${TEST_TMPDIR}" ] && [ -d "${TEST_TMPDIR}" ]; then
        rm -rf "${TEST_TMPDIR}"
    fi
}

# Setup - runs before each test
setup() {
    # Clean up any previous output files
    rm -f "${TEST_OUTPUT_DIR}"/* 2>/dev/null || true
    
    # Change to test output directory for script execution
    cd "${TEST_OUTPUT_DIR}"
}

# Teardown - runs after each test
teardown() {
    # Clean up output files
    rm -f "${TEST_OUTPUT_DIR}"/* 2>/dev/null || true
    
    # Return to original directory
    cd "${PROJECT_ROOT}" || true
}

################################################################################
# Test Output Directory Management
################################################################################

# Setup test output directory (runs once per test file)
setup_test_output_dir() {
    # Get test file name for directory naming
    local test_file_name="test"
    if [ -n "${BATS_TEST_FILENAME:-}" ]; then
        # Extract test file name without extension
        test_file_name=$(basename "${BATS_TEST_FILENAME}" .bats)
    fi
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    # Use test file name in output directory path
    TEST_OUTPUT_DIR="${TEST_DIR}/test-runs/${test_file_name}_${timestamp}"
    mkdir -p "${TEST_OUTPUT_DIR}"
    export TEST_OUTPUT_DIR
    
    # Store in a file so tests can read it
    echo "${TEST_OUTPUT_DIR}" > "${TEST_TMPDIR}/test_output_dir.txt"
    
    # Print to stderr so it shows in test output (BATS file descriptor 3)
    echo "# Test output: ${TEST_OUTPUT_DIR}" >&3
}

# Get test output directory (shared across all tests)
get_test_output_dir() {
    if [ -f "${TEST_TMPDIR}/test_output_dir.txt" ]; then
        cat "${TEST_TMPDIR}/test_output_dir.txt"
    elif [ -n "${TEST_OUTPUT_DIR:-}" ]; then
        echo "${TEST_OUTPUT_DIR}"
    else
        local timestamp=$(date +%Y%m%d_%H%M%S)
        local output_dir="${TEST_DIR}/test-runs/${timestamp}"
        mkdir -p "${output_dir}"
        echo "${output_dir}"
    fi
}

################################################################################
# Utility Functions
################################################################################

# Get absolute path to a script
# Usage: get_script_path "script-name.sh" or "path/to/script.sh"
get_script_path() {
    local script_path="$1"
    # If it's already a full path, use it; otherwise look in PROJECT_ROOT
    if [[ "${script_path}" = /* ]]; then
        echo "${script_path}"
    else
        echo "${PROJECT_ROOT}/${script_path}"
    fi
}

# Run a script
# Usage: run_script "script-name.sh" [args...]
run_script() {
    local script_path=$(get_script_path "$1")
    shift
    run bash "${script_path}" "$@"
}

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

# Skip test if not on macOS (for macOS-specific commands)
skip_if_not_macos() {
    if [[ "$(uname -s)" != "Darwin" ]]; then
        skip "This test is macOS-specific"
    fi
}
