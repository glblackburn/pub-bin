# How to Verify Git Hooks Are Working

## Quick Verification Command

Run this from the repository root:

```bash
cd /Users/lblackb/data/lblackb/git/pub-bin
./git/verify-hooks.sh
```

This script will:
1. ✅ Check that hooks are installed
2. ✅ Test that files with AWS keys are blocked
3. ✅ Test that commit messages with AWS keys are blocked
4. ✅ Test that clean commits are allowed

## Manual Verification

### Test 1: Pre-commit Hook (Blocks Sensitive Data in Files)

```bash
# Create a test file with an AWS key
echo "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE" > /tmp/test_aws.py

# Stage and try to commit (should be blocked)
git add /tmp/test_aws.py
git commit -m "Test: file with AWS key"
```

**Expected Result:** Commit should be BLOCKED with error:
```
ERROR: /tmp/test_aws.py contains sensitive data!
  AWS keys found
Pre-commit checks failed. Fix issues above before committing.
```

### Test 2: Commit-msg Hook (Blocks Sensitive Data in Commit Messages)

```bash
# Create a clean test file
echo "def test(): pass" > /tmp/test_clean.py

# Stage and try to commit with sensitive data in message (should be blocked)
git add /tmp/test_clean.py
git commit -m "Added AWS key: AKIAIOSFODNN7EXAMPLE"
```

**Expected Result:** Commit should be BLOCKED with error:
```
Checking commit message for sensitive data...
ERROR: Commit message contains sensitive data!
  AWS keys found
ERROR: Commit message contains sensitive data!
Please remove sensitive information from commit message.
```

### Test 3: Clean Commit (Should Succeed)

```bash
# Create a clean test file
echo "def test(): pass" > /tmp/test_clean2.py

# Stage and commit with clean message (should succeed)
git add /tmp/test_clean2.py
git commit -m "Test: clean commit message"
```

**Expected Result:** Commit should SUCCEED:
```
Checking code quality...
Scanning for sensitive data...
Checking commit message for sensitive data...
[main abc123] Test: clean commit message
```

## Check Hook Installation

Verify hooks are installed:

```bash
ls -la .git/hooks/pre-commit .git/hooks/commit-msg
```

Both should exist and be executable.

## Test Hooks Directly

### Test pre-commit hook directly:
```bash
.git/hooks/pre-commit
```

### Test commit-msg hook directly:
```bash
echo "Test message" > /tmp/msg.txt
.git/hooks/commit-msg /tmp/msg.txt
echo $?  # Should be 0 for clean message
```

### Test commit-msg hook with sensitive data:
```bash
echo "Added AWS key: AKIAIOSFODNN7EXAMPLE" > /tmp/msg.txt
.git/hooks/commit-msg /tmp/msg.txt
echo $?  # Should be 1 (blocked)
```

## Troubleshooting

### Hooks not running?
1. Check installation: `./git/install-hooks.sh`
2. Check permissions: `ls -la .git/hooks/pre-commit .git/hooks/commit-msg`
3. Check hook names are correct (must be `pre-commit` and `commit-msg`)

### Hooks running but not blocking?
1. Check hook exit codes (should exit 1 on error)
2. Check hook writes to stderr
3. Verify `audit-sensitive-data.py` has `--file`, `--check`, `--message` flags

### False positives?
- Review detected patterns
- Consider adding exclusions to `audit-sensitive-data.py`
