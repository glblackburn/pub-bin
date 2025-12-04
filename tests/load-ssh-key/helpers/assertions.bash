#!/usr/bin/env bash
# Custom assertion functions for load-ssh-key.sh BATS tests

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
# SSH Key Assertions
################################################################################

# Assert that exactly N keys are loaded
# Usage: assert_key_count <expected_count>
assert_key_count() {
    local expected_count="$1"
    local actual_count=$(echo "$output" | grep -c "SHA256:" || echo "0")
    
    if [ "$actual_count" -ne "$expected_count" ]; then
        echo "Expected $expected_count key(s) loaded, found $actual_count" >&2
        echo "Output: $output" >&2
        return 1
    fi
}

# Assert that a specific key is loaded
# Usage: assert_key_loaded <key_name>
assert_key_loaded() {
    local key_name="$1"
    if ! echo "$output" | grep -q "${key_name}"; then
        echo "Expected key '${key_name}' to be loaded" >&2
        echo "Output: $output" >&2
        return 1
    fi
}

# Assert that a specific key is NOT loaded
# Usage: assert_key_not_loaded <key_name>
assert_key_not_loaded() {
    local key_name="$1"
    if echo "$output" | grep -q "${key_name}"; then
        echo "Expected key '${key_name}' NOT to be loaded" >&2
        echo "Output: $output" >&2
        return 1
    fi
}

# Assert that only one key_file entry appears in verbose output
assert_single_key_file_entry() {
    local count=$(echo "$output" | grep -c "key_file=" || echo "0")
    if [ "$count" -ne 1 ]; then
        echo "Expected 1 key_file entry in verbose output, found $count" >&2
        echo "Output: $output" >&2
        return 1
    fi
}

# Assert that find-ssh-keys was NOT called (when -k option is used)
assert_find_ssh_keys_not_called() {
    if echo "$output" | grep -q "find-ssh-keys\|KEY_LIST is empty, finding all keys"; then
        echo "Expected find-ssh-keys NOT to be called when -k option is used" >&2
        echo "Output: $output" >&2
        return 1
    fi
}
