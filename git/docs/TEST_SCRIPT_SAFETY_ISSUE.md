# Test Script Safety Issue and Solution

**Date:** December 18, 2025
**Issue:** Test script (`test-hooks.sh`) caused repository state to drift backward
**Status:** Resolved - Repository synced with origin/main

## Problem Description

### What Happened

The git hooks test script (`git/test-hooks.sh`) was found to be dangerous because it uses `git reset HEAD~1 --hard` to clean up after tests. This caused the local repository HEAD to move backward multiple times, eventually leaving the repository in an inconsistent state.

### Root Cause

**Line 221 in `test-hooks.sh`:**
```bash
git reset HEAD~1 --hard 2>/dev/null || true
```

This command appears in the `test_clean_commit_allowed()` function and moves HEAD backward by one commit. The problems:

1. **Accumulative Effect**: Each test run that includes the "clean commit" test moves HEAD backward by one commit
2. **No State Preservation**: The script doesn't save the initial state before running tests
3. **Incomplete Cleanup**: Only the last test resets, but other tests may have created commits that weren't cleaned up
4. **Interrupt Vulnerability**: If the script is interrupted (Ctrl+C), the repository is left in an inconsistent state

### Symptoms Observed

- Local branch HEAD was 14 commits behind `origin/main`
- The `git/` folder appeared as "untracked" even though it exists in `origin/main`
- `git status` showed: `Untracked files: git/`
- `git log` showed HEAD at commit `5e9d24a` (Dec 16), while `origin/main` was at `0b9e487` (Dec 17)
- Multiple `git reset HEAD~1` entries in reflog showing backward movement

### Impact

- **Low Risk**: No data loss - all commits exist in `origin/main`
- **Medium Risk**: Local development work could be disrupted
- **High Risk**: If tests are run on a branch with uncommitted work, that work could be lost

## Solution: Proposed Safe Test Script Design

### Recommended Approach: Save and Restore Initial State

The test script should preserve the exact repository state and restore it after tests complete, regardless of how many commits were created or if the script is interrupted.

### Implementation Strategy

#### 1. State Preservation (At Start)

```bash
# Save initial state
INITIAL_COMMIT=$(git rev-parse HEAD)
INITIAL_BRANCH=$(git branch --show-current)
INITIAL_WORKING_DIR=$(git status --porcelain)

# Safety checks
if [ -n "$INITIAL_WORKING_DIR" ]; then
    echo "WARNING: Working directory is not clean"
    echo "Uncommitted changes will be lost during test cleanup"
    read -p "Continue? (y/N) " -n 1 -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Set up cleanup trap (runs on any exit)
trap cleanup EXIT INT TERM
```

#### 2. Cleanup Function (At End)

```bash
cleanup() {
    local exit_code=$?

    echo ""
    echo "Cleaning up test artifacts..."

    # Restore to initial commit
    git reset --hard "$INITIAL_COMMIT" 2>/dev/null || true

    # Remove any untracked files created during tests
    git clean -fd "${PROJECT_ROOT}/git/test_hooks/" 2>/dev/null || true
    git clean -fd "${PROJECT_ROOT}/git/docs/test_hook_*.md" 2>/dev/null || true

    # Verify we're back to initial state
    CURRENT_COMMIT=$(git rev-parse HEAD)
    if [ "$CURRENT_COMMIT" != "$INITIAL_COMMIT" ]; then
        echo "WARNING: Could not restore to initial commit"
        echo "Initial: $INITIAL_COMMIT"
        echo "Current: $CURRENT_COMMIT"
    fi

    exit $exit_code
}
```

#### 3. Test Function Modifications

Instead of:
```bash
git reset HEAD~1 --hard  # DANGEROUS
```

Use:
```bash
# Just unstage and remove test file
git reset HEAD "$test_file" 2>/dev/null || true
rm -f "$test_file"
# Let cleanup function handle commit reset
```

### Alternative Approaches Considered

#### Option 2: Temporary Branch
- Create temporary branch from current HEAD
- Run tests on temporary branch
- Switch back to original branch
- Delete temporary branch
- **Pros**: Original branch untouched
- **Cons**: More complex, requires branch management

#### Option 3: Git Worktree
- Create separate worktree for testing
- Run tests in separate worktree
- Delete worktree when done
- **Pros**: Completely isolated
- **Cons**: Requires worktree setup/teardown

#### Option 4: Commit Counting
- Count commits before: `INITIAL_COUNT=$(git rev-list --count HEAD)`
- Count commits after: `FINAL_COUNT=$(git rev-list --count HEAD)`
- Reset by difference: `git reset --hard HEAD~$((FINAL_COUNT - INITIAL_COUNT))`
- **Pros**: Simple calculation
- **Cons**: Doesn't handle interrupted scripts well

### Safety Features to Add

1. **Pre-flight Checks**
   - Verify working directory is clean (or warn user)
   - Check if on protected branch (main/master) and require confirmation
   - Verify initial commit is reachable from origin

2. **Interrupt Handling**
   - Use `trap` to ensure cleanup runs on SIGINT (Ctrl+C), SIGTERM, and EXIT
   - Save state to a file so cleanup can work even if script variables are lost

3. **State Verification**
   - After cleanup, verify HEAD matches initial commit
   - Report any discrepancies
   - Show git status to user

4. **Dry-run Mode**
   - Add `--dry-run` flag to show what would be done without doing it
   - Useful for testing the test script itself

5. **Commit Logging**
   - Optionally log all commits created during tests
   - Helps with debugging if something goes wrong

### Benefits of Recommended Solution

- **Deterministic**: Always returns to exact starting state
- **Interrupt-safe**: Cleanup runs even if script is killed
- **No accumulation**: Multiple test runs don't move HEAD backward
- **Predictable**: Same starting state = same ending state
- **Reversible**: Initial commit hash is known and can be restored

## Resolution

### Actions Taken

1. **Repository Sync**: Reset local branch to match `origin/main`
   ```bash
   git reset --hard origin/main
   ```

2. **State Verification**: Confirmed repository is now in sync
   - HEAD matches `origin/main`
   - `git/` folder is tracked
   - No untracked files

3. **Documentation**: This document created to:
   - Describe the problem
   - Explain the root cause
   - Propose safe solutions
   - Prevent future occurrences

### Next Steps

1. **Implement Safe Test Script**: Refactor `test-hooks.sh` using the recommended approach
2. **Add Safety Checks**: Implement pre-flight checks and cleanup traps
3. **Test the Test Script**: Verify the new implementation works correctly
4. **Update Documentation**: Add warnings about running tests on branches with uncommitted work

## Prevention

To prevent this issue from recurring:

1. **Never use `git reset HEAD~N` in test scripts** - Always use absolute commit hashes
2. **Always save initial state** - Before making any changes, save the starting point
3. **Use traps for cleanup** - Ensure cleanup runs even if script is interrupted
4. **Verify state after cleanup** - Check that repository is back to initial state
5. **Test the test script** - Run the test script multiple times to ensure no accumulation

## References

- Git reflog showing backward movement: `git reflog | head -20`
- Test script location: `git/test-hooks.sh`
- Problematic line: Line 221 - `git reset HEAD~1 --hard`
