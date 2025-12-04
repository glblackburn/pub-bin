# Testing Plan: `-k` Option for load-ssh-key.sh

## Problem Statement
The `-k` option should load ONLY the specified key(s), but it appears to be loading additional keys beyond what is specified.

## Current Behavior (Reported Issue)
When running: `. load-ssh-key.sh -k ${HOME}/.ssh/your-key-no-passphrase.pem`
- Expected: Only `your-key-no-passphrase.pem` should be loaded
- Actual: Multiple keys are being loaded

## Test Environment Setup

### Prerequisites
1. Kill existing SSH agent: `. load-ssh-key.sh -K`
2. Verify agent is clean: `. load-ssh-key.sh -l` should show no keys or only expected keys
3. Test keys available:
   - `${HOME}/.ssh/your-key-no-passphrase.pem` (no passphrase)
   - `${HOME}/.ssh/your-key-with-passphrase` (requires passphrase)
   - `${HOME}/.ssh/your-second-key` (requires passphrase)
   - `${HOME}/.ssh/your-third-key` (requires passphrase)

## Test Scenarios

### Test 1: Single Key (No Passphrase)
**Command:** `. load-ssh-key.sh -k ${HOME}/.ssh/your-key-no-passphrase.pem`

**Expected Behavior:**
- Only `your-key-no-passphrase.pem` is loaded
- No passphrase prompts
- `-l` option shows exactly 1 key
- No errors

**Success Criteria:**
- `load-ssh-key.sh -l` shows exactly 1 key matching the specified key
- No "Enter passphrase" prompts appear
- No "Adding SSH key" messages for other keys

### Test 2: Single Key (With Passphrase) - Should Fail Early
**Command:** `. load-ssh-key.sh -k ${HOME}/.ssh/your-key-with-passphrase`

**Expected Behavior:**
- Only `your-key-with-passphrase` should be attempted
- If passphrase is wrong/empty, should fail for THIS key only
- Should NOT attempt to load other keys
- Should exit/return after this key fails

**Success Criteria:**
- Only 1 "Enter passphrase" prompt (for the specified key)
- No "Adding SSH key" messages for other keys
- Script exits after this key fails (doesn't continue to other keys)

### Test 3: Multiple Keys (Comma-separated)
**Command:** `. load-ssh-key.sh -k ${HOME}/.ssh/your-key-no-passphrase.pem,${HOME}/.ssh/your-key-with-passphrase`

**Expected Behavior:**
- Only the 2 specified keys should be loaded
- First key (no passphrase) loads successfully
- Second key prompts for passphrase
- No other keys should be attempted

**Success Criteria:**
- `-l` shows exactly 2 keys (or 1 if second fails)
- Only 2 "Adding SSH key" messages
- No other keys in the list

### Test 4: Verify No Fallback to Auto-Discovery
**Command:** `. load-ssh-key.sh -k ${HOME}/.ssh/your-key-no-passphrase.pem -v`

**Expected Behavior:**
- Should NOT call `find-ssh-keys` function
- Should NOT process keys from `~/.ssh` directory discovery
- Only processes the explicitly specified key

**Success Criteria:**
- Verbose output shows only 1 key_file entry
- No output from `find-ssh-keys` function
- No processing of other keys found in directory

## Test Scripts

### Test Script 1: Basic Single Key Test
```bash
#!/bin/bash
# test-k-option-single.sh

set -e

SCRIPT_DIR="\${HOME}/data/lblackb/git/pub-bin"
cd "${SCRIPT_DIR}"

echo "=== Test: Single key with -k option ==="
echo ""

# Kill existing agent
echo "1. Killing existing SSH agent..."
source load-ssh-key.sh -K -q 2>&1 > /dev/null
sleep 1

# Verify clean state
echo "2. Verifying clean state..."
KEY_COUNT=$(source load-ssh-key.sh -l 2>&1 | grep -c "SHA256:" || echo "0")
if [[ "${KEY_COUNT}" != "0" ]] ; then
    echo "ERROR: Agent not clean. Found ${KEY_COUNT} keys"
    exit 1
fi

# Load single key
echo "3. Loading single key: your-key-no-passphrase.pem"
timeout 5 bash -c "source load-ssh-key.sh -k \${HOME}/.ssh/your-key-no-passphrase.pem 2>&1" || {
    echo "ERROR: Command timed out or failed"
    exit 1
}

# Verify only one key loaded
echo "4. Verifying only one key is loaded..."
KEY_COUNT=$(source load-ssh-key.sh -l 2>&1 | grep -c "SHA256:" || echo "0")
if [[ "${KEY_COUNT}" != "1" ]] ; then
    echo "ERROR: Expected 1 key, found ${KEY_COUNT} keys"
    source load-ssh-key.sh -l
    exit 1
fi

# Verify it's the correct key
if ! source load-ssh-key.sh -l 2>&1 | grep -q "your-key-no-passphrase.pem" ; then
    echo "ERROR: Wrong key loaded"
    source load-ssh-key.sh -l
    exit 1
fi

echo "SUCCESS: Only the specified key is loaded"
```

### Test Script 2: Passphrase Key Test (Should Fail Early)
```bash
#!/bin/bash
# test-k-option-passphrase.sh

set -e

SCRIPT_DIR="\${HOME}/data/lblackb/git/pub-bin"
cd "${SCRIPT_DIR}"

echo "=== Test: Single key with passphrase (should fail early) ==="
echo ""

# Kill existing agent
echo "1. Killing existing SSH agent..."
source load-ssh-key.sh -K -q 2>&1 > /dev/null
sleep 1

# Load key that requires passphrase (with wrong passphrase)
echo "2. Attempting to load key requiring passphrase (will fail)..."
echo "wrongpass" | timeout 3 bash -c "source load-ssh-key.sh -k \${HOME}/.ssh/your-key-with-passphrase 2>&1" 2>&1 | tee /tmp/test-output.txt

# Count how many keys were attempted
ATTEMPT_COUNT=$(grep -c "Adding SSH key to agent:" /tmp/test-output.txt || echo "0")
PASSPHRASE_PROMPTS=$(grep -c "Enter passphrase" /tmp/test-output.txt || echo "0")

echo "3. Verifying only one key was attempted..."
if [[ "${ATTEMPT_COUNT}" != "1" ]] ; then
    echo "ERROR: Expected 1 key attempt, found ${ATTEMPT_COUNT}"
    cat /tmp/test-output.txt
    exit 1
fi

if [[ "${PASSPHRASE_PROMPTS}" != "1" ]] ; then
    echo "ERROR: Expected 1 passphrase prompt, found ${PASSPHRASE_PROMPTS}"
    cat /tmp/test-output.txt
    exit 1
fi

# Verify no other keys were processed
OTHER_KEYS=$(grep "Adding SSH key to agent:" /tmp/test-output.txt | grep -v "your-key-with-passphrase" | wc -l | tr -d ' ')
if [[ "${OTHER_KEYS}" != "0" ]] ; then
    echo "ERROR: Other keys were attempted"
    cat /tmp/test-output.txt
    exit 1
fi

echo "SUCCESS: Only the specified key was attempted"
```

### Test Script 3: Verbose Output Analysis
```bash
#!/bin/bash
# test-k-option-verbose.sh

set -e

SCRIPT_DIR="\${HOME}/data/lblackb/git/pub-bin"
cd "${SCRIPT_DIR}"

echo "=== Test: Verbose output analysis ==="
echo ""

# Kill existing agent
echo "1. Killing existing SSH agent..."
source load-ssh-key.sh -K -q 2>&1 > /dev/null
sleep 1

# Load single key with verbose output
echo "2. Loading key with verbose output..."
timeout 5 bash -c "source load-ssh-key.sh -k \${HOME}/.ssh/your-key-no-passphrase.pem -v 2>&1" 2>&1 | tee /tmp/test-verbose.txt

# Analyze output
echo "3. Analyzing output..."
KEY_FILE_COUNT=$(grep -c "key_file=" /tmp/test-verbose.txt || echo "0")
FIND_SSH_KEYS_CALLED=$(grep -c "find-ssh-keys" /tmp/test-verbose.txt || echo "0")
ADDING_KEY_COUNT=$(grep -c "Adding SSH key to agent:" /tmp/test-verbose.txt || echo "0")

echo "  key_file= entries: ${KEY_FILE_COUNT}"
echo "  find-ssh-keys calls: ${FIND_SSH_KEYS_CALLED}"
echo "  Adding SSH key messages: ${ADDING_KEY_COUNT}"

if [[ "${KEY_FILE_COUNT}" != "1" ]] ; then
    echo "ERROR: Expected 1 key_file entry, found ${KEY_FILE_COUNT}"
    exit 1
fi

if [[ "${FIND_SSH_KEYS_CALLED}" != "0" ]] ; then
    echo "ERROR: find-ssh-keys should not be called when -k is used"
    exit 1
fi

if [[ "${ADDING_KEY_COUNT}" != "1" ]] ; then
    echo "ERROR: Expected 1 'Adding SSH key' message, found ${ADDING_KEY_COUNT}"
    exit 1
fi

echo "SUCCESS: Verbose output shows only one key processed"
```

## Root Cause Analysis Areas

### Potential Issues to Investigate

1. **KEY_LIST variable handling**
   - Is KEY_LIST being properly set from -k option?
   - Is it being cleared or overwritten somewhere?
   - Is the check `if [[ -z "${KEY_LIST}" ]]` working correctly?

2. **Loop processing**
   - Is the `while read` loop processing correctly?
   - Is word splitting causing multiple iterations?
   - Is the pipe creating a subshell that loses variable state?

3. **Fallback logic**
   - Is the script falling back to `find-ssh-keys` when it shouldn't?
   - Is there a logic error in the if/else structure?

4. **Error handling**
   - Does error_count work correctly in the subshell?
   - Are errors causing the script to continue incorrectly?

## Success Criteria Summary

For the command `. load-ssh-key.sh -k ${HOME}/.ssh/your-key-no-passphrase.pem`:

1. ✅ Only 1 key is loaded (verified with `-l` option)
2. ✅ No passphrase prompts appear
3. ✅ No "Adding SSH key" messages for other keys
4. ✅ Verbose output shows only 1 `key_file=` entry
5. ✅ `find-ssh-keys` function is NOT called
6. ✅ Script completes without errors

## Next Steps

1. Create the test scripts above
2. Run each test script and document results
3. Identify the root cause based on test failures
4. Fix the issue
5. Re-run all tests to verify fix
6. Document the solution
