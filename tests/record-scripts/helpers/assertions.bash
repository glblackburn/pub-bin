#!/usr/bin/env bash
# Custom assertion functions for record*.sh BATS tests

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

# Assert that an output file was created
# Usage: assert_output_file_exists "record-netstat_*.txt"
assert_output_file_exists() {
    local pattern="$1"
    local found=$(find "${TEST_OUTPUT_DIR}" -name "${pattern}" 2>/dev/null | wc -l)
    if [ "${found}" -eq 0 ]; then
        echo "Expected output file matching '${pattern}' not found in ${TEST_OUTPUT_DIR}" >&2
        echo "Files in output directory:" >&2
        ls -la "${TEST_OUTPUT_DIR}" >&2 || true
        return 1
    fi
}

# Assert that an output file does not exist
# Usage: assert_output_file_not_exists "record-netstat_*.txt"
assert_output_file_not_exists() {
    local pattern="$1"
    local found=$(find "${TEST_OUTPUT_DIR}" -name "${pattern}" 2>/dev/null | wc -l)
    if [ "${found}" -gt 0 ]; then
        echo "Expected output file matching '${pattern}' NOT to exist, but found ${found} file(s)" >&2
        find "${TEST_OUTPUT_DIR}" -name "${pattern}" >&2
        return 1
    fi
}

# Count output files matching a pattern
count_output_files() {
    local pattern="$1"
    find "${TEST_OUTPUT_DIR}" -name "${pattern}" 2>/dev/null | wc -l | tr -d ' '
}

# Assert that output file contains a string
# Usage: assert_output_file_contains "record-netstat_*.txt" "netstat"
assert_output_file_contains() {
    local pattern="$1"
    local expected="$2"
    local output_file=$(find "${TEST_OUTPUT_DIR}" -name "${pattern}" 2>/dev/null | head -1)
    
    if [ -z "${output_file}" ]; then
        echo "Output file matching '${pattern}' not found" >&2
        return 1
    fi
    
    if ! grep -q "${expected}" "${output_file}" 2>/dev/null; then
        echo "Expected file '${output_file}' to contain: ${expected}" >&2
        echo "File contents:" >&2
        head -20 "${output_file}" >&2 || true
        return 1
    fi
}

# Assert that output file is not empty
# Usage: assert_output_file_not_empty "record-netstat_*.txt"
assert_output_file_not_empty() {
    local pattern="$1"
    local output_file=$(find "${TEST_OUTPUT_DIR}" -name "${pattern}" 2>/dev/null | head -1)
    
    if [ -z "${output_file}" ]; then
        echo "Output file matching '${pattern}' not found" >&2
        return 1
    fi
    
    if [ ! -s "${output_file}" ]; then
        echo "Expected file '${output_file}' to be non-empty" >&2
        return 1
    fi
}
