#!/bin/bash
# test-k-option-verbose.sh
# Test verbose output to verify only one key is processed

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
TEST_KEY_NO_PASS_PATH=$(get_test_key_path "${TEST_KEY_NO_PASSPHRASE}")

# Cleanup function to kill ssh-agents
cleanup() {
    printf "\n" | timeout 5 bash -c "source ${SCRIPT_DIR}/load-ssh-key.sh -K -q 2>&1" > /dev/null 2>&1 || true
    pkill -9 ssh-agent 2>/dev/null || true
    sleep 1
    rm -f ~/.ssh/ssh-agent.config 2>/dev/null || true
}

# Set trap to cleanup on exit
trap cleanup EXIT

echo "=== Test: Verbose output analysis ==="
echo ""

# Kill existing agent (pipe input in case of any prompts)
echo "1. Killing existing SSH agent..."
printf "\n" | timeout 5 bash -c "source ${SCRIPT_DIR}/load-ssh-key.sh -K -q 2>&1" > /dev/null 2>&1 || true
sleep 1

# Load single key with verbose output (pipe empty input in case of unexpected prompts)
echo "2. Loading key with verbose output..."
printf "\n" | timeout 10 bash -c "source ${SCRIPT_DIR}/load-ssh-key.sh -k '${TEST_KEY_NO_PASS_PATH}' -v 2>&1" 2>&1 | tee /tmp/test-k-verbose-output.txt || {
    EXIT_CODE=$?
    if [[ ${EXIT_CODE} -eq 124 ]] ; then
	echo "ERROR: Command timed out (may be waiting for input)"
	exit 1
    fi
}

# Analyze output
echo "3. Analyzing output..."
KEY_FILE_COUNT=$(grep -c "key_file=" /tmp/test-k-verbose-output.txt 2>/dev/null || echo "0")
if grep -q "find-ssh-keys" /tmp/test-k-verbose-output.txt 2>/dev/null ; then
    FIND_SSH_KEYS_CALLED="1"
else
    FIND_SSH_KEYS_CALLED="0"
fi
ADDING_KEY_COUNT=$(grep -c "Adding SSH key to agent:" /tmp/test-k-verbose-output.txt 2>/dev/null || echo "0")

echo "  key_file= entries: ${KEY_FILE_COUNT}"
echo "  find-ssh-keys calls: ${FIND_SSH_KEYS_CALLED}"
echo "  Adding SSH key messages: ${ADDING_KEY_COUNT}"

if [[ "${KEY_FILE_COUNT}" != "1" ]] ; then
    echo "ERROR: Expected 1 key_file entry, found ${KEY_FILE_COUNT}"
    echo "Full output:"
    cat /tmp/test-k-verbose-output.txt
    exit 1
fi

if [[ "${FIND_SSH_KEYS_CALLED}" != "0" ]] ; then
    echo "ERROR: find-ssh-keys should not be called when -k is used"
    echo "Full output:"
    cat /tmp/test-k-verbose-output.txt
    exit 1
fi

if [[ "${ADDING_KEY_COUNT}" != "1" ]] ; then
    echo "ERROR: Expected 1 'Adding SSH key' message, found ${ADDING_KEY_COUNT}"
    echo "Full output:"
    cat /tmp/test-k-verbose-output.txt
    exit 1
fi

echo "SUCCESS: Verbose output shows only one key processed"
echo "4. Test completed (cleanup will run automatically via trap)"
exit 0
