#!/usr/bin/env bash
# BATS test helper - Setup and common functions for load-ssh-key.sh tests

################################################################################
# Test Setup
################################################################################

# Get the absolute path to the tests directory
if [ -n "${BATS_TEST_FILENAME:-}" ]; then
    # If loaded from a test file, resolve relative to test file location
    TEST_FILE_DIR="$(cd "$(dirname "${BATS_TEST_FILENAME}")" && pwd)"
    # Go up from unit/ or integration/ to load-ssh-key/, or stay in load-ssh-key/ if already there
    if [ "$(basename "${TEST_FILE_DIR}")" = "unit" ] || [ "$(basename "${TEST_FILE_DIR}")" = "integration" ]; then
        TEST_DIR="$(cd "${TEST_FILE_DIR}/.." && pwd)"
    else
        TEST_DIR="${TEST_FILE_DIR}"
    fi
else
    # Fallback: assume we're in tests/load-ssh-key/ directory
    TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

# PROJECT_ROOT is the directory containing the scripts (parent of tests/)
PROJECT_ROOT="$(cd "${TEST_DIR}/../.." && pwd)"
SCRIPT_DIR="${PROJECT_ROOT}"

# Export for use in tests
export TEST_DIR
export PROJECT_ROOT
export SCRIPT_DIR

# Load helper modules
# Note: test-key-config.bash is only needed for archive scripts, not unit tests
if [ -n "${BATS_TEST_FILENAME:-}" ]; then
    # Test file is loading this, so paths are relative to test file
    load "../helpers/assertions.bash"
    load "../helpers/ssh-helpers.bash"
else
    # Direct execution (shouldn't happen, but fallback)
    load "${TEST_DIR}/helpers/assertions.bash"
    load "${TEST_DIR}/helpers/ssh-helpers.bash"
fi

################################################################################
# Setup and Teardown
################################################################################

# Global setup - runs once before all tests in a file
setup_file() {
    # Get test file name for directory naming
    local test_file_name="test"
    if [ -n "${BATS_TEST_FILENAME:-}" ]; then
        # Extract test file name without extension (e.g., "test_k_option" from "test_k_option.bats")
        test_file_name=$(basename "${BATS_TEST_FILENAME}" .bats)
    fi
    
    # Create temporary directory in /tmp/ with test file name
    # Format: /tmp/test_k_option.XXXXXX
    export TEST_TMPDIR=$(mktemp -d "/tmp/${test_file_name}.XXXXXX")
    export TEST_SSH_DIR="${TEST_TMPDIR}/.ssh"
    mkdir -p "${TEST_SSH_DIR}"
    export ORIGINAL_HOME="${HOME:-}"
    export ORIGINAL_SSH_AGENT_PID="${SSH_AGENT_PID:-}"
    export ORIGINAL_SSH_AUTH_SOCK="${SSH_AUTH_SOCK:-}"
    
    # Setup test output directory
    setup_test_output_dir
}

# Global teardown - runs once after all tests in a file
teardown_file() {
    # Kill any test ssh-agents
    pkill -9 ssh-agent 2>/dev/null || true
    
    # Clean up temporary directories
    if [ -n "${TEST_TMPDIR}" ] && [ -d "${TEST_TMPDIR}" ]; then
        rm -rf "${TEST_TMPDIR}"
    fi
    
    # Restore original environment
    if [ -n "${ORIGINAL_SSH_AGENT_PID:-}" ]; then
        export SSH_AGENT_PID="${ORIGINAL_SSH_AGENT_PID}"
    else
        unset SSH_AGENT_PID
    fi
    
    if [ -n "${ORIGINAL_SSH_AUTH_SOCK:-}" ]; then
        export SSH_AUTH_SOCK="${ORIGINAL_SSH_AUTH_SOCK}"
    else
        unset SSH_AUTH_SOCK
    fi
}

# Setup - runs before each test
setup() {
    # Backup original HOME and SSH environment
    export ORIGINAL_HOME="${HOME:-}"
    export ORIGINAL_SSH_AGENT_PID="${SSH_AGENT_PID:-}"
    export ORIGINAL_SSH_AUTH_SOCK="${SSH_AUTH_SOCK:-}"
    
    # Override HOME to use test directory
    export HOME="${TEST_TMPDIR}"
    
    # Never let a test block on an interactive passphrase prompt. ssh-add reads
    # the passphrase from /dev/tty, not stdin, so redirecting input is not
    # enough - force it through an askpass program that always fails instead.
    export SSH_ASKPASS="/usr/bin/false"
    export SSH_ASKPASS_REQUIRE="force"
    
    # Kill any existing ssh-agents from previous tests
    pkill -9 ssh-agent 2>/dev/null || true
    unset SSH_AGENT_PID
    unset SSH_AUTH_SOCK
    
    # Clean up any config files
    rm -f "${TEST_SSH_DIR}/ssh-agent.config" 2>/dev/null || true
}

# Teardown - runs after each test
teardown() {
    # Kill any test ssh-agents
    pkill -9 ssh-agent 2>/dev/null || true
    
    # Clean up test config
    rm -f "${TEST_SSH_DIR}/ssh-agent.config" 2>/dev/null || true
    
    # Restore original environment
    if [ -n "${ORIGINAL_HOME:-}" ]; then
        export HOME="${ORIGINAL_HOME}"
    fi
    
    if [ -n "${ORIGINAL_SSH_AGENT_PID:-}" ]; then
        export SSH_AGENT_PID="${ORIGINAL_SSH_AGENT_PID}"
    else
        unset SSH_AGENT_PID
    fi
    
    if [ -n "${ORIGINAL_SSH_AUTH_SOCK:-}" ]; then
        export SSH_AUTH_SOCK="${ORIGINAL_SSH_AUTH_SOCK}"
    else
        unset SSH_AUTH_SOCK
    fi
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

# Get absolute path to load-ssh-key.sh script
get_script_path() {
    echo "${SCRIPT_DIR}/load-ssh-key.sh"
}

# Run load-ssh-key.sh script (sourced)
# Usage: run_load_ssh_key [options...]
run_load_ssh_key() {
    local script_path=$(get_script_path)
    # Source the script in a subshell and capture output
    # Note: When sourced in a subshell, 'return' becomes 'exit'
    # Preserve HOME and SSH environment for the script
    run bash -c "
        export HOME='${HOME:-}'
        export TEST_SSH_DIR='${TEST_SSH_DIR:-}'
        [ -n '${SSH_AGENT_PID:-}' ] && export SSH_AGENT_PID='${SSH_AGENT_PID}'
        [ -n '${SSH_AUTH_SOCK:-}' ] && export SSH_AUTH_SOCK='${SSH_AUTH_SOCK}'
        source '${script_path}' $* 2>&1; exit_code=\$?
        # Export SSH agent vars back (they're set by sourcing the script)
        [ -n \"\${SSH_AGENT_PID:-}\" ] && echo \"SSH_AGENT_PID=\${SSH_AGENT_PID}\" > '${TEST_TMPDIR}/ssh_env.txt'
        [ -n \"\${SSH_AUTH_SOCK:-}\" ] && echo \"SSH_AUTH_SOCK=\${SSH_AUTH_SOCK}\" >> '${TEST_TMPDIR}/ssh_env.txt'
        exit \$exit_code
    "
    # Load SSH agent vars back if they were set
    if [ -f "${TEST_TMPDIR}/ssh_env.txt" ]; then
        source "${TEST_TMPDIR}/ssh_env.txt" 2>/dev/null || true
        rm -f "${TEST_TMPDIR}/ssh_env.txt"
    fi
}

# Run load-ssh-key.sh script (executed directly)
# Usage: run_load_ssh_key_exec [options...]
run_load_ssh_key_exec() {
    local script_path=$(get_script_path)
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
