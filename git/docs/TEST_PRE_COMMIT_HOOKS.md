# Pre-Commit Hooks Testing Guide

This document demonstrates how to trigger and test different violations that will be blocked by the pre-commit hooks.

## Installation

First, install the hooks:

```bash
cd /Users/lblackb/data/lblackb/git/pub-bin
./git/install-hooks.sh
```

## Test Cases

### Test 1: Trailing Whitespace Violation

**Purpose:** Verify that files with trailing whitespace are blocked.

**Steps:**
```bash
# Create a test file with trailing whitespace
echo "def test_function(): " > test_trailing_space.py
echo "    return True " >> test_trailing_space.py

# Stage the file
git add test_trailing_space.py

# Try to commit (should fail)
git commit -m "Test: file with trailing whitespace"
```

**Expected Result:**
```
Checking code quality...
ERROR: test_trailing_space.py contains trailing whitespace
  1:def test_function():
  2:    return True
Pre-commit checks failed. Fix issues above before committing.
```

**Fix:**
```bash
# Remove trailing whitespace
sed -i '' 's/[[:space:]]*$//' test_trailing_space.py
git add test_trailing_space.py
git commit -m "Test: file with trailing whitespace"
# Should now succeed
```

---

### Test 2: Missing Newline Violation

**Purpose:** Verify that files not ending with newline are blocked.

**Steps:**
```bash
# Create a file without trailing newline
printf "def test():\n    pass" > test_no_newline.py

# Stage the file
git add test_no_newline.py

# Try to commit (should fail)
git commit -m "Test: file without newline"
```

**Expected Result:**
```
Checking code quality...
ERROR: test_no_newline.py does not end with newline
Pre-commit checks failed. Fix issues above before committing.
```

**Fix:**
```bash
# Add newline
echo "" >> test_no_newline.py
git add test_no_newline.py
git commit -m "Test: file without newline"
# Should now succeed
```

---

### Test 3: Sensitive Data in File (AWS Key)

**Purpose:** Verify that files containing AWS keys are blocked.

**Steps:**
```bash
# Create a file with an AWS key
cat > test_aws_key.py << 'EOF'
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
EOF

# Stage the file
git add test_aws_key.py

# Try to commit (should fail)
git commit -m "Test: file with AWS key"
```

**Expected Result:**
```
Scanning for sensitive data...
ERROR: test_aws_key.py contains sensitive data!
  API keys found
SENSITIVE_DATA_FOUND: test_aws_key.py
Pre-commit checks failed. Fix issues above before committing.
```

**Fix:**
```bash
# Remove the sensitive data or use tokenization
rm test_aws_key.py
# Or use trufflehog-tokenize-secrets.py to tokenize it first
```

---

### Test 4: Sensitive Data in File (GitHub Token)

**Purpose:** Verify that files containing GitHub tokens are blocked.

**Steps:**
```bash
# Create a file with a GitHub token
cat > test_github_token.py << 'EOF'
GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz
EOF

# Stage the file
git add test_github_token.py

# Try to commit (should fail)
git commit -m "Test: file with GitHub token"
```

**Expected Result:**
```
Scanning for sensitive data...
ERROR: test_github_token.py contains sensitive data!
  Tokens found
SENSITIVE_DATA_FOUND: test_github_token.py
Pre-commit checks failed. Fix issues above before committing.
```

---

### Test 5: Sensitive Data in Commit Message

**Purpose:** Verify that commit messages containing sensitive data are blocked.

**Steps:**
```bash
# Create a clean file
echo "def test(): pass" > test_clean.py
git add test_clean.py

# Try to commit with sensitive data in message (should fail)
git commit -m "Added AWS key: AKIAIOSFODNN7EXAMPLE"
```

**Expected Result:**
```
Checking commit message for sensitive data...
ERROR: Commit message contains sensitive data!
  API keys found
SENSITIVE_DATA_FOUND: /tmp/git-commit-msg-XXXXXX
ERROR: Commit message contains sensitive data!
Please remove sensitive information from commit message.
```

**Fix:**
```bash
# Use a safe commit message
git commit -m "Added configuration file"
# Should now succeed
```

---

### Test 6: Password in File

**Purpose:** Verify that files containing passwords are blocked.

**Steps:**
```bash
# Create a file with a password
cat > test_password.py << 'EOF'
DATABASE_PASSWORD=mySecretPassword123
EOF

# Stage the file
git add test_password.py

# Try to commit (should fail)
git commit -m "Test: file with password"
```

**Expected Result:**
```
Scanning for sensitive data...
ERROR: test_password.py contains sensitive data!
  Passwords found
SENSITIVE_DATA_FOUND: test_password.py
Pre-commit checks failed. Fix issues above before committing.
```

---

### Test 7: Multiple Violations

**Purpose:** Verify that multiple violations are all caught.

**Steps:**
```bash
# Create a file with multiple issues
cat > test_multiple.py << 'EOF'
AWS_KEY=AKIAIOSFODNN7EXAMPLE
def test(): pass
EOF
# Note: line 1 has trailing space, line 2 has no newline, and contains AWS key

# Stage the file
git add test_multiple.py

# Try to commit (should fail with all issues)
git commit -m "Test: multiple violations"
```

**Expected Result:**
```
Checking code quality...
ERROR: test_multiple.py contains trailing whitespace
  1:AWS_KEY=AKIAIOSFODNN7EXAMPLE
ERROR: test_multiple.py does not end with newline
Scanning for sensitive data...
ERROR: test_multiple.py contains sensitive data!
  API keys found
Pre-commit checks failed. Fix issues above before committing.
```

---

### Test 8: Clean Commit (Should Succeed)

**Purpose:** Verify that clean files commit successfully.

**Steps:**
```bash
# Create a clean file
cat > test_clean.py << 'EOF'
def test_function():
    return True
EOF

# Stage the file
git add test_clean.py

# Commit (should succeed)
git commit -m "Test: clean file"
```

**Expected Result:**
```
Checking code quality...
Scanning for sensitive data...
[commit succeeds]
```

---

## Bypassing Hooks (Use with Caution)

If you need to bypass hooks (emergency situations only):

```bash
git commit --no-verify -m "message"
```

**Warning:** Only use `--no-verify` if you fully understand the risks and have a legitimate reason.

---

## Verification Commands

### Test audit-sensitive-data.py directly:

```bash
# Test single file check mode
python3 audit-sensitive-data.py --file test_file.py --check

# Test commit message mode
echo "Added key: AKIAIOSFODNN7EXAMPLE" > /tmp/test_msg.txt
python3 audit-sensitive-data.py --file /tmp/test_msg.txt --check --message
```

### Test helper functions directly:

```bash
# Source the helpers
source git/hooks/pre-commit-helpers.sh

# Test code quality check
check_code_quality

# Test sensitive data check
check_sensitive_data_files

# Test commit message check
check_commit_message /tmp/test_commit_msg.txt
```

---

## Expected Behavior Summary

| Violation Type | Hook | Blocks Commit? | Error Message |
|---------------|------|----------------|---------------|
| Trailing whitespace | pre-commit | Yes | "ERROR: file contains trailing whitespace" |
| Missing newline | pre-commit | Yes | "ERROR: file does not end with newline" |
| AWS key in file | pre-commit | Yes | "ERROR: file contains sensitive data!" |
| GitHub token in file | pre-commit | Yes | "ERROR: file contains sensitive data!" |
| Password in file | pre-commit | Yes | "ERROR: file contains sensitive data!" |
| Secret in commit message | pre-commit-msg | Yes | "ERROR: Commit message contains sensitive data!" |
| Backup files (*~) | pre-commit | No (warning only) | "WARNING: Backup files found" |
| Clean files | pre-commit | No | Commit succeeds |

---

## Troubleshooting

### Hook not running?
```bash
# Check if hooks are installed
ls -la .git/hooks/pre-commit .git/hooks/pre-commit-msg

# Reinstall hooks
./install-hooks.sh
```

### audit-sensitive-data.py not found?
```bash
# Check path in helpers
grep "audit-sensitive-data.py" git/hooks/pre-commit-helpers.sh

# Update path if needed (should be: ${project_root}/trufflehog/audit-sensitive-data.py)
```

### False positives?
- Review the detected pattern
- Consider adding to exclusion list in audit-sensitive-data.py
- Use `--no-verify` only if absolutely necessary
