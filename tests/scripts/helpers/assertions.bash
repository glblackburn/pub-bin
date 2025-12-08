#!/usr/bin/env bash
# Custom assertion functions for general script BATS tests

################################################################################
# Output Assertions
################################################################################

# Assert that output contains a string
assert_output_contains() {
    local expected="$1"
    if [[ ! "$output" =~ $expected ]]; then
        echo "Expected output to contain: $expected" >&2
        echo "Actual output: $output" >&2
        return 1
    fi
}

# Assert that output does not contain a string
assert_output_not_contains() {
    local unexpected="$1"
    if [[ "$output" =~ $unexpected ]]; then
        echo "Expected output NOT to contain: $unexpected" >&2
        echo "Actual output: $output" >&2
        return 1
    fi
}

# Assert that stderr contains a string
assert_stderr_contains() {
    local expected="$1"
    if [[ ! "$stderr" =~ $expected ]]; then
        echo "Expected stderr to contain: $expected" >&2
        echo "Actual stderr: $stderr" >&2
        return 1
    fi
}

################################################################################
# Exit Code Assertions
################################################################################

# Assert exit code is success (0)
assert_success() {
    if [ "$status" -ne 0 ]; then
        echo "Expected exit code 0, got $status" >&2
        echo "Output: $output" >&2
        echo "Stderr: $stderr" >&2
        return 1
    fi
}

# Assert exit code is failure (non-zero)
assert_failure() {
    if [ "$status" -eq 0 ]; then
        echo "Expected non-zero exit code, got 0" >&2
        echo "Output: $output" >&2
        return 1
    fi
}

# Assert exit code equals expected
assert_exit_code() {
    local expected="$1"
    if [ "$status" -ne "$expected" ]; then
        echo "Expected exit code $expected, got $status" >&2
        echo "Output: $output" >&2
        echo "Stderr: $stderr" >&2
        return 1
    fi
}

################################################################################
# File Assertions
################################################################################

# Assert that a file exists
assert_file_exists() {
    local file_path="$1"
    if [ ! -f "${file_path}" ]; then
        echo "Expected file '${file_path}' to exist" >&2
        return 1
    fi
}

# Assert that a file does not exist
assert_file_not_exists() {
    local file_path="$1"
    if [ -f "${file_path}" ]; then
        echo "Expected file '${file_path}' NOT to exist" >&2
        return 1
    fi
}

# Assert that a file contains a string
assert_file_contains() {
    local file_path="$1"
    local expected="$2"
    
    if [ ! -f "${file_path}" ]; then
        echo "File '${file_path}' does not exist" >&2
        return 1
    fi
    
    if ! grep -q "${expected}" "${file_path}" 2>/dev/null; then
        echo "Expected file '${file_path}' to contain: ${expected}" >&2
        echo "File contents:" >&2
        head -20 "${file_path}" >&2 || true
        return 1
    fi
}

# Assert that a file is not empty
assert_file_not_empty() {
    local file_path="$1"
    
    if [ ! -f "${file_path}" ]; then
        echo "File '${file_path}' does not exist" >&2
        return 1
    fi
    
    if [ ! -s "${file_path}" ]; then
        echo "Expected file '${file_path}' to be non-empty" >&2
        return 1
    fi
}

# Assert that a directory exists
assert_dir_exists() {
    local dir_path="$1"
    if [ ! -d "${dir_path}" ]; then
        echo "Expected directory '${dir_path}' to exist" >&2
        return 1
    fi
}
