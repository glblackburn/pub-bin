#!/bin/bash
# test-k-option-passphrase.sh
# Test that -k option only attempts the specified key (even if it requires passphrase)

set -e
# Don't exit on pipe failures (timeout may cause this)
set +o pipefail

# Calculate paths before changing directories
ARCHIVE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$(cd "${ARCHIVE_DIR}/.." && pwd)"
SCRIPT_DIR="$(cd "${TEST_DIR}/../.." && pwd)"
cd "${SCRIPT_DIR}"

# Load test key configuration from secure directory
TEST_KEY_CONFIG="${TEST_DIR}/helpers/test-key-config.bash"
if [ -f "${TEST_KEY_CONFIG}" ]; then
    source "${TEST_KEY_CONFIG}"
    load_test_key_config || {
        echo "ERROR: Failed to load test key configuration" >&2
        exit 1
    }
else
    echo "ERROR: Test key config helper not found: ${TEST_KEY_CONFIG}" >&2
    exit 1
fi

# Get full paths to test keys
TEST_KEY_WITH_PASS_PATH=$(get_test_key_path "${TEST_KEY_WITH_PASSPHRASE}")

# Cleanup function to kill ssh-agents
cleanup() {
    printf "\n" | timeout 5 bash -c "source ${SCRIPT_DIR}/load-ssh-key.sh -K -q 2>&1" > /dev/null 2>&1 || true
    pkill -9 ssh-agent 2>/dev/null || true
    sleep 1
    rm -f ~/.ssh/ssh-agent.config 2>/dev/null || true
}

# Set trap to cleanup on exit
trap cleanup EXIT

echo "=== Test: Single key with passphrase (should fail early) ==="
echo ""

# Kill existing agent (pipe input in case of any prompts)
echo "1. Killing existing SSH agent..."
printf "\n" | timeout 5 bash -c "source ${SCRIPT_DIR}/load-ssh-key.sh -K -q 2>&1" > /dev/null 2>&1 || true
sleep 1

# Load key that requires passphrase (with wrong passphrase, then blank to break out)
echo "2. Attempting to load key requiring passphrase (will fail)..."
# Use verbose mode to capture key_file entries, send wrong pass, then blank lines to break out
(printf "wrongpass\n\n\n\n" | timeout 8 bash -c "source ${SCRIPT_DIR}/load-ssh-key.sh -k '${TEST_KEY_WITH_PASS_PATH}' -v 2>&1" 2>&1 || true) | tee /tmp/test-k-passphrase-output.txt

# Count how many keys were attempted
ATTEMPT_COUNT=$(grep -c "Adding SSH key to agent:" /tmp/test-k-passphrase-output.txt 2>/dev/null || echo "0")
PASSPHRASE_PROMPTS=$(grep -c "Enter passphrase" /tmp/test-k-passphrase-output.txt 2>/dev/null || echo "0")
KEY_FILE_COUNT=$(grep -c "key_file=" /tmp/test-k-passphrase-output.txt 2>/dev/null || echo "0")

echo "3. Verifying only one key was attempted..."
echo "  Attempt count: ${ATTEMPT_COUNT}"
echo "  Passphrase prompts: ${PASSPHRASE_PROMPTS}"
echo "  key_file entries: ${KEY_FILE_COUNT}"

if [[ "${ATTEMPT_COUNT}" != "1" ]] ; then
    echo "ERROR: Expected 1 key attempt, found ${ATTEMPT_COUNT}"
    echo "Full output:"
    cat /tmp/test-k-passphrase-output.txt
    exit 1
fi

if [[ "${KEY_FILE_COUNT}" != "1" ]] ; then
    echo "ERROR: Expected 1 key_file entry, found ${KEY_FILE_COUNT}"
    echo "Full output:"
    cat /tmp/test-k-passphrase-output.txt
    exit 1
fi

# Verify no other keys were processed (check that only one key was attempted)
# We already verified ATTEMPT_COUNT == 1 above
if [[ "${OTHER_KEYS}" != "0" ]] ; then
    echo "ERROR: Other keys were attempted"
    echo "Full output:"
    cat /tmp/test-k-passphrase-output.txt
    exit 1
fi

# Note: Passphrase prompt may not be captured if it goes to /dev/tty
# But we can verify only one key was attempted by checking key_file entries

echo "SUCCESS: Only the specified key was attempted"
echo "4. Test completed (cleanup will run automatically via trap)"
exit 0
