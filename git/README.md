# Git Hooks

This directory contains git hooks and utilities for enforcing code quality and security checks before commits.

## Quick Start

### Installation

Install the git hooks using the Makefile:

```bash
cd git/
make install-hooks
```

Or manually:

```bash
cd git/
./install-hooks.sh
```

The hooks will be installed to `.git/hooks/` in the repository root.

### Testing

Run the test suite to verify hooks are working:

```bash
cd git/
make test
```

## What the Hooks Do

### pre-commit Hook

Runs before each commit and checks:

- **Sensitive Data Detection**: Scans ALL staged files (NO EXCEPTIONS) for:
  - AWS access keys (AKIA pattern)
  - GitHub tokens (ghp_/gh[oprsu]_ pattern)
  - API keys, passwords, and tokens

  **SECURITY POLICY: NO SAFE FILE TYPES OR PATHS**
  - ALL files are checked, including `.md`, `docs/`, `test_hooks/`, etc.
  - Only binary files (detected by git attributes) are skipped
  - Sensitive data will NEVER be allowed in commits, regardless of file type or location

- **Code Quality**:
  - Trailing whitespace on lines
  - Missing newline at end of file
  - Backup files (*~, *.bak, *.backup)

### commit-msg Hook

Validates commit messages for:
- AWS access keys
- GitHub tokens
- API keys, passwords, and tokens

## Files

- `hooks/` - Git hook scripts
  - `pre-commit` - Pre-commit hook entry point
  - `commit-msg` - Commit message validation hook
  - `pre-commit-helpers.sh` - Shared helper functions
- `test-hooks.sh` - Test suite for hooks
- `Makefile` - Build and test automation
- `install-hooks.sh` - Hook installation script

## Usage

### Manual Hook Execution

You can manually test hooks:

```bash
# Test pre-commit hook
.git/hooks/pre-commit

# Test commit-msg hook
echo "Test message" | .git/hooks/commit-msg /tmp/msg.txt
```

### Bypassing Hooks (Not Recommended)

To bypass hooks (use with caution):

```bash
git commit --no-verify -m "message"
```

## Configuration

### Security Policy

**CRITICAL: NO EXCEPTIONS FOR SENSITIVE DATA**

- ALL files are checked for sensitive data, regardless of:
  - File extension (`.md`, `.py`, `.sh`, `.txt`, etc.)
  - File location (`docs/`, `test_hooks/`, root, etc.)
  - File purpose (documentation, tests, scripts, etc.)

- Only binary files (detected by git attributes) are skipped because they cannot be checked as text

- If you need to commit example/test patterns, use placeholder values like:
  - `AKIAEXAMPLE12345678` (invalid format)
  - `ghp_EXAMPLE_TOKEN_123456789012345678901234567890` (invalid format)
  - Or clearly mark them as examples in comments

### Customizing Checks

Edit `hooks/pre-commit-helpers.sh` to modify:
- Error messages
- Additional sensitive data patterns
- Code quality checks

**WARNING:** Do not add skip logic for file types or paths - this creates security vulnerabilities.

## Troubleshooting

### Hooks Not Running

1. Verify hooks are installed:
   ```bash
   ls -la .git/hooks/pre-commit .git/hooks/commit-msg
   ```

2. Check hook permissions:
   ```bash
   chmod +x .git/hooks/pre-commit .git/hooks/commit-msg
   ```

3. Reinstall hooks:
   ```bash
   cd git/
   make install-hooks
   ```

## Development

### Running Tests

```bash
cd git/
make test
```

### Adding New Checks

1. Add detection logic to `pre-commit-helpers.sh`
2. Update tests in `test-hooks.sh`
3. Run `make test` to verify

## Documentation

For detailed documentation, see:
- `git/docs/` - Additional documentation files
- `git help githooks` - Official git hooks documentation
