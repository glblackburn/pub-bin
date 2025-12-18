# Git Hooks Documentation

## Official Git Documentation

The authoritative source for git hooks is:
```bash
git help githooks
```

Or online: https://git-scm.com/docs/githooks

## Key Hooks for Pre-Commit Checks

### pre-commit
- **When:** Runs BEFORE the commit message is obtained and before the commit is created
- **Purpose:** Check the working tree (staged files)
- **Can bypass:** Yes, with `--no-verify` flag
- **Parameters:** None
- **Exit code:** Non-zero to abort commit

**Use case:** Check code quality, scan files for sensitive data, validate file formats

### commit-msg
- **When:** Runs AFTER the commit message is written but BEFORE the commit is finalized
- **Purpose:** Validate or modify the commit message
- **Can bypass:** No (but can use `--no-verify` to skip all hooks)
- **Parameters:** Path to file containing commit message
- **Exit code:** Non-zero to abort commit
- **Can edit:** Yes, the hook can modify the message file

**Use case:** Validate commit message format, check for sensitive data in commit messages, enforce commit message standards

## Hook Execution Order

1. `pre-commit` - Checks staged files
2. Commit message is obtained (from `-m`, editor, or template)
3. `commit-msg` - Validates/modifies commit message
4. Commit is created

## Important Notes

1. **Hook Names Are Fixed:** Git only recognizes specific hook names. You cannot create custom hook names like `pre-commit-msg` - it must be `commit-msg`.

2. **Executable Bit Required:** Hooks must have execute permissions:
   ```bash
   chmod +x .git/hooks/commit-msg
   ```

3. **Working Directory:** Git changes to the repository root before running hooks.

4. **Environment Variables:** Git exports `GIT_DIR`, `GIT_WORK_TREE`, etc. for hooks to use.

5. **Error Handling:** Hooks should exit with non-zero status to abort the operation.

## Testing Hooks

### Test pre-commit hook:
```bash
.git/hooks/pre-commit
```

### Test commit-msg hook:
```bash
echo "Test message" > /tmp/msg.txt
.git/hooks/commit-msg /tmp/msg.txt
echo $?  # Should be 0 for success, 1 for failure
```

### Test with actual commit:
```bash
git add file.txt
git commit -m "Test message"
```

## Common Issues

### Hook Not Running
1. Check hook name is correct (e.g., `commit-msg`, not `pre-commit-msg`)
2. Check hook has execute permissions
3. Check hook is in `.git/hooks/` directory
4. Check for syntax errors in hook script

### Hook Running But Not Blocking
1. Check hook exits with non-zero status on error
2. Check hook writes error messages to stderr
3. Verify hook logic is correct

### Bypassing Hooks
- `--no-verify` or `-n` flag bypasses `pre-commit` and `commit-msg` hooks
- This should be documented and discouraged for security-sensitive hooks

## Our Implementation

- **pre-commit:** Checks code quality and scans files for sensitive data
- **commit-msg:** Validates commit messages for sensitive data

Both hooks must work correctly to prevent sensitive data from entering git history.
