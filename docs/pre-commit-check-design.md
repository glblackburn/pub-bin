# Pre-Commit Check Solution - Design Document

## Purpose

Design a comprehensive pre-commit check system that:
1. Enforces AI coding standards (prevents AI assistants from committing)
2. Prevents sensitive data from being committed (files and commit messages)
3. Validates code quality before commits
4. Provides clear feedback and guidance

## Goals

1. **Prevent Policy Violations**: Stop AI assistants from executing forbidden git operations
2. **Protect Sensitive Data**: Block commits containing secrets, keys, or sensitive information
3. **Ensure Code Quality**: Verify formatting, whitespace, and file structure
4. **User-Friendly**: Clear error messages and actionable guidance

## Architecture

### Components

1. **Git Hook Integration**
   - Pre-commit hook that runs before commits
   - Pre-commit-msg hook that validates commit messages
   - Can be installed locally or in CI/CD

2. **Policy Enforcement Module**
   - Checks if operation is allowed per AI coding standards
   - Blocks forbidden git operations
   - Provides policy explanations

3. **Sensitive Data Scanner**
   - Integrates `audit-sensitive-data.py` for file content scanning
   - Scans commit messages for sensitive data
   - Uses pattern matching and heuristics

4. **Code Quality Validator**
   - Trailing whitespace detection
   - File ending validation (newline requirement)
   - Backup file detection

5. **AI Assistant Integration**
   - Pattern recognition for git operation requests
   - Policy check before executing any git command
   - Automatic code quality checks before presenting code

## Pre-Commit Hook Design

### Hook Location
- **Local**: `.git/hooks/pre-commit` (user-specific)
- **Shared**: `hooks/pre-commit` (checked into repo, installed via setup script)
- **CI/CD**: Runs in pipeline before allowing merge

### Hook Structure

```bash
#!/bin/bash
# Pre-commit hook for trufflehog project
# Enforces AI coding standards and prevents sensitive data commits

set -euET -o pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
project_root="$(git rev-parse --show-toplevel)"
hooks_dir="${project_root}/hooks"

# Source helper functions
source "${hooks_dir}/pre-commit-helpers.sh" 2>/dev/null || {
    echo "ERROR: pre-commit-helpers.sh not found" >&2
    exit 1
}

# Run checks
exit_code=0

# 1. Code Quality Checks
if ! check_code_quality; then
    exit_code=1
fi

# 2. Sensitive Data Checks (files)
if ! check_sensitive_data_files; then
    exit_code=1
fi

# 3. Backup File Checks
if ! check_backup_files; then
    exit_code=1
fi

if [ $exit_code -ne 0 ]; then
    echo "" >&2
    echo "Pre-commit checks failed. Fix issues above before committing." >&2
    exit 1
fi

exit 0
```

### Pre-Commit-Msg Hook (Commit Message Validation)

```bash
#!/bin/bash
# Pre-commit-msg hook
# Validates commit messages for sensitive data

set -euET -o pipefail

commit_msg_file="$1"
project_root="$(git rev-parse --show-toplevel)"
hooks_dir="${project_root}/hooks"

# Source helper functions
source "${hooks_dir}/pre-commit-helpers.sh" 2>/dev/null || {
    echo "ERROR: pre-commit-helpers.sh not found" >&2
    exit 1
}

# Check commit message for sensitive data
if ! check_commit_message "${commit_msg_file}"; then
    echo "" >&2
    echo "ERROR: Commit message contains sensitive data!" >&2
    echo "Please remove sensitive information from commit message." >&2
    exit 1
fi

exit 0
```

## Helper Functions

### pre-commit-helpers.sh

```bash
#!/bin/bash
# Pre-commit helper functions

# Check code quality (trailing whitespace, file endings)
check_code_quality() {
    local errors=0
    local files

    # Get staged files
    files=$(git diff --cached --name-only --diff-filter=ACM)

    if [ -z "$files" ]; then
        return 0
    fi

    echo "Checking code quality..." >&2

    # Check for trailing whitespace
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            # Skip binary files
            if git check-attr --all "$file" | grep -q "binary: set"; then
                continue
            fi

            # Check trailing whitespace
            if grep -n '[[:space:]]$' "$file" >/dev/null 2>&1; then
                echo "ERROR: $file contains trailing whitespace" >&2
                grep -n '[[:space:]]$' "$file" | head -5 | sed 's/^/  /' >&2
                errors=1
            fi

            # Check file ending (must end with newline)
            if [ -s "$file" ] && [ "$(tail -c1 "$file" | wc -l)" -eq 0 ]; then
                echo "ERROR: $file does not end with newline" >&2
                errors=1
            fi
        fi
    done <<< "$files"

    return $errors
}

# Check for sensitive data in staged files
check_sensitive_data_files() {
    local errors=0
    local files
    local project_root
    local file

    project_root="$(git rev-parse --show-toplevel)"
    files=$(git diff --cached --name-only --diff-filter=ACM)

    if [ -z "$files" ]; then
        return 0
    fi

    echo "Scanning for sensitive data..." >&2

    # Use audit-sensitive-data.py to scan files
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            # Skip binary files
            if git check-attr --all "$file" 2>/dev/null | grep -q "binary: set"; then
                continue
            fi

            # Run audit-sensitive-data.py on file (check mode)
            # Exit code 0 = clean, 1 = sensitive data found
            if ! python3 "${project_root}/audit-sensitive-data.py" --file "$file" --check --quiet 2>/dev/null; then
                echo "ERROR: $file contains sensitive data!" >&2
                # Show details (without --quiet)
                python3 "${project_root}/audit-sensitive-data.py" --file "$file" --check >&2
                errors=1
            fi
        fi
    done <<< "$files"

    return $errors
}

# Check commit message for sensitive data
check_commit_message() {
    local commit_msg_file="$1"
    local project_root

    project_root="$(git rev-parse --show-toplevel)"

    if [ ! -f "$commit_msg_file" ]; then
        return 1
    fi

    echo "Checking commit message for sensitive data..." >&2

    # Run audit-sensitive-data.py on commit message
    # Use --message flag for commit message specific scanning
    # Exit code 0 = clean, 1 = sensitive data found
    if ! python3 "${project_root}/audit-sensitive-data.py" --file "$commit_msg_file" --check --message --quiet 2>/dev/null; then
        echo "ERROR: Commit message contains sensitive data!" >&2
        # Show details (without --quiet)
        python3 "${project_root}/audit-sensitive-data.py" --file "$commit_msg_file" --check --message >&2
        return 1
    fi

    return 0
}

# Check for backup files
check_backup_files() {
    local errors=0
    local backup_files

    backup_files=$(git ls-files | grep -E '~$|\.bak$|\.backup$' || true)

    if [ -n "$backup_files" ]; then
        echo "WARNING: Backup files found in repository:" >&2
        echo "$backup_files" | sed 's/^/  /' >&2
        echo "Consider removing these files:" >&2
        echo "  find . -name '*~' -delete" >&2
        # Don't fail, just warn
    fi

    return 0
}
```

## Audit-Sensitive-Data Integration

### Current audit-sensitive-data.py Review

**Need to verify:**
- Does it support `--file` and `--check` flags?
- What output format does it use?
- How does it detect sensitive data?

### Integration Requirements

1. **File Scanning Mode**
   ```bash
   audit-sensitive-data.py --file <file> --check
   # Returns exit code 0 if clean, 1 if sensitive data found
   # Outputs: "SENSITIVE_DATA_FOUND" or similar indicator
   ```

2. **Commit Message Scanning**
   - Same tool, different input (commit message file)
   - Must detect secrets in commit messages
   - Patterns: AWS keys, API tokens, passwords, etc.

3. **Output Format**
   - Machine-readable: exit codes, clear indicators
   - Human-readable: line numbers, patterns matched
   - Actionable: suggests what to remove/fix

### Enhanced audit-sensitive-data.py Requirements

If current script doesn't support needed features, add:

```python
# New flags needed:
--file <path>        # Scan single file
--check              # Check mode (exit with code, minimal output)
--message            # Indicate this is a commit message (different patterns)
--quiet              # Minimal output for automation
```

## AI Assistant Integration

### Pattern Recognition

**Detect Git Operation Requests:**
```python
GIT_OPERATION_PATTERNS = {
    'commit': ['commit', 'save changes', 'create commit'],
    'add': ['add', 'stage', 'git add'],
    'push': ['push', 'upload', 'send to remote'],
    'status': ['status', 'what changed', 'show changes'],
    'diff': ['diff', 'show diff', 'what\'s different']
}

def detect_git_operation(user_request: str) -> Optional[str]:
    """Detect if user is requesting a git operation."""
    request_lower = user_request.lower()
    for op, patterns in GIT_OPERATION_PATTERNS.items():
        if any(pattern in request_lower for pattern in patterns):
            return op
    return None
```

### Policy Enforcement

```python
ALLOWED_GIT_OPERATIONS = ['status', 'diff', 'log', 'show', 'branch', 'tag']

def check_git_operation_allowed(operation: str) -> Tuple[bool, str]:
    """
    Check if git operation is allowed per AI coding standards.

    Returns:
        (is_allowed, explanation)
    """
    if operation in ALLOWED_GIT_OPERATIONS:
        return True, ""

    if operation in ['add', 'commit', 'push', 'reset', 'revert']:
        explanation = (
            f"Per AI coding standards, I cannot execute 'git {operation}'. "
            "The user handles ALL git operations (add, commit, push, etc.). "
            "I can only use 'git status' or 'git diff' to show you what changed."
        )
        return False, explanation

    return False, f"Unknown operation: {operation}"
```

### Code Quality Pre-Check

```python
def check_code_quality(file_path: Path) -> List[str]:
    """
    Check code quality before presenting to user.
    Returns list of issues found.
    """
    issues = []

    # Check trailing whitespace
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if line.rstrip() != line and line.strip():  # Has trailing whitespace
                issues.append(f"Line {line_num}: trailing whitespace")

    # Check file ending
    with open(file_path, 'rb') as f:
        f.seek(-1, 2)  # Seek to last byte
        last_byte = f.read(1)
        if last_byte != b'\n':
            issues.append("File does not end with newline")

    return issues
```

## Implementation Phases

### Phase 1: Git Hooks (Local Protection)
1. Create `hooks/pre-commit` script
2. Create `hooks/pre-commit-msg` script
3. Create `hooks/pre-commit-helpers.sh`
4. Create installation script: `install-hooks.sh`
5. Test with sample commits

### Phase 2: Audit Integration
1. Review `audit-sensitive-data.py` capabilities
2. Add required flags if needed (`--file`, `--check`, `--message`)
3. Integrate into pre-commit hooks
4. Test with files containing sensitive data
5. Test with commit messages containing sensitive data

### Phase 3: AI Assistant Integration
1. Implement pattern recognition
2. Implement policy enforcement
3. Implement code quality pre-checks
4. Add to AI assistant workflow
5. Test with various user requests

### Phase 4: Documentation & Setup
1. Create installation instructions
2. Document hook behavior
3. Create troubleshooting guide
4. Add to project README

## File Structure

```
trufflehog/
├── hooks/
│   ├── pre-commit              # Main pre-commit hook
│   ├── pre-commit-msg          # Commit message validation
│   └── pre-commit-helpers.sh   # Helper functions
├── install-hooks.sh            # Hook installation script
├── audit-sensitive-data.py     # Sensitive data scanner (existing)
└── pre-commit-check-design.md  # This document
```

## Usage

### Installation

```bash
# Install hooks
./install-hooks.sh

# Or manually
cp hooks/pre-commit .git/hooks/pre-commit
cp hooks/pre-commit-msg .git/hooks/pre-commit-msg
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit-msg
```

### Testing

```bash
# Test code quality check
echo "test " > test.txt  # Trailing space
git add test.txt
git commit -m "test"  # Should fail

# Test sensitive data check
echo "AKIAIOSFODNN7EXAMPLE" > config.txt
git add config.txt
git commit -m "test"  # Should fail

# Test commit message check
git commit -m "Added AWS key: AKIAIOSFODNN7EXAMPLE"  # Should fail
```

## Sensitive Data Detection

### Patterns to Detect

1. **AWS Keys**
   - Pattern: `AKIA[0-9A-Z]{16}`
   - Example: `AKIAIOSFODNN7EXAMPLE`

2. **GitHub Tokens**
   - Pattern: `ghp_[0-9a-zA-Z]{36}`
   - Pattern: `gho_[0-9a-zA-Z]{36}`
   - Pattern: `ghu_[0-9a-zA-Z]{36}`
   - Pattern: `ghs_[0-9a-zA-Z]{36}`
   - Pattern: `ghr_[0-9a-zA-Z]{36}`

3. **API Keys**
   - Pattern: `[a-zA-Z0-9]{32,}` (long alphanumeric strings)
   - Context: Often in config files, env files

4. **Passwords**
   - Pattern: `password\s*[=:]\s*[^\s]+`
   - Pattern: `passwd\s*[=:]\s*[^\s]+`
   - Pattern: `pwd\s*[=:]\s*[^\s]+`

5. **Private Keys**
   - Pattern: `-----BEGIN.*PRIVATE KEY-----`
   - Pattern: `-----BEGIN RSA PRIVATE KEY-----`
   - Pattern: `-----BEGIN EC PRIVATE KEY-----`

6. **Secrets in Commit Messages**
   - Same patterns as above
   - Also check for: "key:", "token:", "secret:", "password:"

### audit-sensitive-data.py Integration

**Current State:**
- Script exists and has `analyze_file()` function
- Detects: emails, GitHub refs, API keys, passwords, tokens, file paths
- Returns dict with findings or None if clean
- Currently designed for full repository audit, not single-file checks

**Required Enhancements for Pre-Commit Hooks:**

1. **Add `--file` flag for single file scanning:**
```python
parser.add_argument('--file', help='Scan single file (for pre-commit hooks)')
```

2. **Add `--check` mode for exit-code-only output:**
```python
parser.add_argument('--check', action='store_true',
    help='Check mode: exit with code 0 if clean, 1 if sensitive data found')
```

3. **Add `--message` flag for commit message scanning:**
```python
parser.add_argument('--message', action='store_true',
    help='Scan commit message (different sensitivity thresholds)')
```

4. **Add `--quiet` mode for minimal output:**
```python
# Already exists, but ensure it works for check mode
```

5. **Enhance `analyze_file()` for check mode:**
```python
def analyze_file(file_path: Path, exclude_patterns: List[str] = None,
                 check_mode: bool = False) -> Union[Dict, bool]:
    """
    Analyze a single file for sensitive data.

    Args:
        file_path: Path to file to scan
        exclude_patterns: Patterns to exclude
        check_mode: If True, return bool (True=sensitive data found)

    Returns:
        Dict with findings (normal mode) or bool (check mode)
    """
    result = {
        'file': str(file_path),
        'emails': extract_emails(content, str(file_path)),
        'api_keys': extract_api_keys(content, str(file_path)),
        'passwords': extract_passwords(content, str(file_path)),
        'tokens': extract_tokens(content, str(file_path)),
        # ... other patterns
    }

    if check_mode:
        # Return True if any sensitive data found
        has_secrets = any([
            result['api_keys'],
            result['passwords'],
            result['tokens'],
            # For commit messages, also check emails and paths
        ])
        return has_secrets

    # Normal mode - return dict
    if any([result['emails'], result['api_keys'], ...]):
        return result
    return None
```

6. **Add commit message specific patterns:**
```python
# For commit messages, focus on high-risk patterns:
# - API keys (AWS, GitHub tokens, etc.)
# - Passwords
# - Tokens
# - Long alphanumeric strings that look like secrets
# Less strict on emails and file paths (may be legitimate in commit messages)
```

**Integration in Pre-Commit Hook:**
```bash
# Check single file
if python3 audit-sensitive-data.py --file "$file" --check --quiet; then
    echo "ERROR: $file contains sensitive data!" >&2
    python3 audit-sensitive-data.py --file "$file" --check >&2
    exit 1
fi

# Check commit message
if python3 audit-sensitive-data.py --file "$commit_msg_file" --check --message --quiet; then
    echo "ERROR: Commit message contains sensitive data!" >&2
    python3 audit-sensitive-data.py --file "$commit_msg_file" --check --message >&2
    exit 1
fi
```

## Error Messages

### Code Quality Errors

```
ERROR: file.py contains trailing whitespace
  Line 42: def function():
  Line 45:     return value
Fix by removing trailing spaces.

ERROR: file.py does not end with newline
Fix by adding newline at end of file.
```

### Sensitive Data Errors

```
ERROR: config.json contains sensitive data!
  Line 5: AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
  Pattern: AWS Access Key detected

Please remove sensitive data before committing.
Consider using trufflehog-tokenize-secrets.py to tokenize secrets.
```

### Commit Message Errors

```
ERROR: Commit message contains sensitive data!
  Pattern: AWS Access Key detected in commit message

Please remove sensitive information from commit message.
Commit messages are public and should never contain secrets.
```

## Configuration

### .gitattributes (Optional)

```
# Mark files that should be skipped from sensitive data checks
*.example linguist-generated
*.template linguist-generated
```

### Hook Configuration

```bash
# hooks/config.sh (optional)
SKIP_SENSITIVE_DATA_CHECK=false
SKIP_CODE_QUALITY_CHECK=false
ALLOWED_PATTERNS_FILE="hooks/allowed-patterns.txt"
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Pre-commit Checks

on: [push, pull_request]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run pre-commit checks
        run: |
          ./hooks/pre-commit
          ./hooks/pre-commit-msg "$(git log -1 --pretty=%B)"
```

## Benefits

1. **Automatic Protection**: Hooks run automatically, no manual steps
2. **Early Detection**: Catch issues before they're committed
3. **Consistent Enforcement**: Same checks for all contributors
4. **Educational**: Clear error messages teach best practices
5. **Flexible**: Can be bypassed with `--no-verify` if needed (with caution)

## Bypass Mechanism

**When to Allow Bypass:**
- Emergency fixes (with proper justification)
- Administrative operations
- Known false positives (after review)

**How to Bypass:**
```bash
git commit --no-verify -m "message"
```

**Warning:** Bypass should be used sparingly and with full understanding of risks.

## Testing Strategy

### Unit Tests
- Test each helper function independently
- Test pattern matching
- Test error detection

### Integration Tests
- Test full hook execution
- Test with various file types
- Test with various sensitive data patterns
- Test commit message validation

### Manual Testing
- Create test commits with issues
- Verify hooks catch problems
- Verify hooks allow clean commits
- Test bypass mechanism

## Future Enhancements

1. **Whitelist Support**: Allow specific patterns/files
2. **Pattern Customization**: User-defined sensitive data patterns
3. **Auto-fix Mode**: Automatically fix code quality issues
4. **Statistics**: Track what's being caught
5. **Integration with More Tools**: Additional security scanners
6. **Commit Message Templates**: Guide users to write safe messages

## audit-sensitive-data.py Current Capabilities

**Reviewed:** The script has the following capabilities:

**Current Features:**
- `analyze_file(file_path)` - Analyzes single file, returns dict with findings or None
- Detects: emails, GitHub refs, API keys, passwords, tokens, file paths
- Patterns: API_KEY_PATTERN, PASSWORD_PATTERN, TOKEN_PATTERN, etc.
- Safe pattern exclusions (example.com, test.com, etc.)

**Missing for Pre-Commit Integration:**
1. `--file` flag for single file scanning
2. `--check` mode for exit-code-based checking
3. `--message` flag for commit message scanning
4. Integration with pre-commit hooks

**Required Enhancements:**
- Add CLI flags: `--file`, `--check`, `--message`
- Modify `analyze_file()` to support check mode (return bool)
- Add commit message specific pattern matching (focus on high-risk secrets)
- Ensure exit codes: 0 = clean, 1 = sensitive data found

## Open Questions

1. **audit-sensitive-data.py Enhancement Priority**:
   - **Decision**: Enhance script with required flags before implementing hooks
   - **Action**: Add `--file`, `--check`, `--message` flags to script

2. **Hook Installation**: Automatic or manual?
   - **Recommendation**: Provide both options
   - **Default**: Manual (user controls when to install)

3. **False Positives**: How to handle?
   - **Recommendation**: Whitelist mechanism
   - **Process**: Review and add to whitelist if legitimate

4. **Performance**: Impact on commit speed?
   - **Consideration**: Sensitive data scanning can be slow
   - **Mitigation**: Cache results, parallel processing

5. **CI/CD Integration**: Required or optional?
   - **Recommendation**: Required for shared repositories
   - **Implementation**: Add to CI/CD pipeline

## Success Criteria

1. ✅ Hooks prevent commits with sensitive data
2. ✅ Hooks prevent commits with code quality issues
3. ✅ Commit messages are validated for sensitive data
4. ✅ Clear, actionable error messages
5. ✅ Easy installation and setup
6. ✅ Works in CI/CD environments
7. ✅ Minimal performance impact
8. ✅ Handles edge cases gracefully

---

**Design Status**: In Progress
**Next Steps**: Review audit-sensitive-data.py, implement Phase 1
