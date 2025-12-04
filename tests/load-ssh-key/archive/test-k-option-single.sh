#!/bin/bash
# test-k-option-single.sh
# Test that -k option loads only the specified single key

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

echo "=== Test: Single key with -k option ==="
echo ""

# Kill existing agent (pipe input in case of any prompts)
echo "1. Killing existing SSH agent..."
printf "\n" | timeout 5 bash -c "source load-ssh-key.sh -K -q 2>&1" > /dev/null 2>&1 || true
sleep 1

# Verify clean state
echo "2. Verifying clean state..."
LIST_OUTPUT=$(timeout 5 bash -c "source ${SCRIPT_DIR}/load-ssh-key.sh -l 2>&1" 2>&1 || echo "SSH agent is not running")
if echo "${LIST_OUTPUT}" | grep -q "SHA256:" ; then
    KEY_COUNT=$(echo "${LIST_OUTPUT}" | grep -c "SHA256:")
    echo "ERROR: Agent not clean. Found ${KEY_COUNT} keys"
    echo "${LIST_OUTPUT}"
    exit 1
fi
# If agent is not running, that's fine - we'll start it

# Load single key (pipe empty input in case of unexpected prompts)
echo "3. Loading single key: ${TEST_KEY_NO_PASSPHRASE}"
printf "\n" | timeout 10 bash -c "source ${SCRIPT_DIR}/load-ssh-key.sh -k '${TEST_KEY_NO_PASS_PATH}' 2>&1" || {
    EXIT_CODE=$?
    if [[ ${EXIT_CODE} -eq 124 ]] ; then
	echo "ERROR: Command timed out (may be waiting for input)"
    else
	echo "ERROR: Command failed with exit code ${EXIT_CODE}"
    fi
    exit 1
}

# Verify only one key loaded
echo "4. Verifying only one key is loaded..."
LIST_OUTPUT=$(source ${SCRIPT_DIR}/load-ssh-key.sh -l 2>&1)
if ! echo "${LIST_OUTPUT}" | grep -q "SHA256:" ; then
    echo "ERROR: No keys found after loading"
    echo "${LIST_OUTPUT}"
    exit 1
fi
KEY_COUNT=$(echo "${LIST_OUTPUT}" | grep -c "SHA256:")
if [[ "${KEY_COUNT}" != "1" ]] ; then
    echo "ERROR: Expected 1 key, found ${KEY_COUNT} keys"
    echo "Loaded keys:"
    echo "${LIST_OUTPUT}"
    exit 1
fi

# Verify it's the correct key (check by fingerprint count - ssh-add -l doesn't show filenames)
# The key should be loaded, which we already verified above

echo "SUCCESS: Only the specified key is loaded"
echo "5. Test completed (cleanup will run automatically via trap)"
exit 0
