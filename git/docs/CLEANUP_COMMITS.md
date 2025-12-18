# Cleanup Required: Commits with Sensitive Data

## Problem

Three commits were created during testing that contain AWS keys in the commit messages:

- `838903c` - "Added AWS key: AKIAIOSFODNN7EXAMPLE"
- `8d6f9c2` - "Added AWS key: AKIAIOSFODNN7EXAMPLE"
- `df65abf` - "Added AWS key: AKIAIOSFODNN7EXAMPLE"

These commits should have been blocked by the `pre-commit-msg` hook but were not.

## Why This Happened

The `pre-commit-msg` hook works when tested directly, but `git commit -m` may bypass it in some cases, or there may have been an error that was silently ignored during testing.

## Solution Options

### Option 1: Interactive Rebase (Recommended if not pushed)

If these commits haven't been pushed to remote:

```bash
cd /Users/lblackb/data/lblackb/git/pub-bin
git rebase -i HEAD~3
# In the editor, change "pick" to "reword" for the 3 commits
# Change the commit messages to something safe like "Test: commit message validation"
```

### Option 2: Reset and Re-commit (If safe to lose these commits)

```bash
cd /Users/lblackb/data/lblackb/git/pub-bin
# Check what files were changed
git show --stat HEAD~3..HEAD

# Reset to before these commits (keeping changes)
git reset --soft HEAD~3

# Re-commit with safe message
git commit -m "Test: pre-commit hook validation"
```

### Option 3: Amend Last Commit (If only the last one matters)

```bash
cd /Users/lblackb/data/lblackb/git/pub-bin
git commit --amend -m "Test: pre-commit hook validation"
```

## Fixing the Hook Issue

The hook should be working, but we need to ensure it's called properly. The `pre-commit-msg` hook is called by git, but there may be edge cases.

**Note:** These commits demonstrate why the hook is important - they contain sensitive data that should never be in git history.
