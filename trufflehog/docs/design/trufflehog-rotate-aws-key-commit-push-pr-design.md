# Trufflehog AWS Key Rotation Script - Commit, Push, and PR Design

**Date:** 2025-12-18
**Purpose:** Design for adding commit, push, and pull request creation functionality to `trufflehog-rotate-aws-key.py`

---

## TL;DR - Quick Start

**What's New:** The script can now push commits and create pull requests automatically, completing the rotation workflow end-to-end.

### Simple Usage Example

**Complete workflow in 3 steps:**

1. **Modify files and commit** (initial run):
   ```bash
   ./trufflehog-rotate-aws-key.py \
       -r report.md \
       -i RAW_abc123_def456 \
       -p \
       --mode commit
   ```
   - Clones repos, creates branches, replaces keys, commits changes
   - Saves state file: `~/.secure/trufflehog-rotate/RAW_abc123_def456-<timestamp>.json`

2. **Push commits** (resume session):
   ```bash
   ./trufflehog-rotate-aws-key.py \
       --resume \
       -i RAW_abc123_def456 \
       --push
   ```
   - Pushes all committed branches to their remotes
   - Updates state file with push status

3. **Create pull requests** (resume session):
   ```bash
   ./trufflehog-rotate-aws-key.py \
       --resume \
       -i RAW_abc123_def456 \
       --create-pr
   ```
   - Creates PRs for all pushed branches
   - Updates state file with PR URLs

**Or combine steps 2 and 3** (push and create PRs in one command):
   ```bash
   ./trufflehog-rotate-aws-key.py \
       --resume \
       -i RAW_abc123_def456 \
       --push \
       --create-pr
   ```
   - Pushes commits, then immediately creates PRs for all pushed branches

**That's it!** Each step can be done separately or combined. The `--resume` flag uses the state file to pick up where you left off.

**Prerequisites:**
- GitHub CLI (`gh`) installed and authenticated, OR
- GitHub API token set in environment variable `GITHUB_TOKEN`

---

## Executive Summary

This document outlines the design for adding commit, push, and pull request creation functionality to `trufflehog-aws-key-rotate.py`. The feature completes the rotation workflow by eliminating manual steps after the script runs.

**Current State:** Script creates branches and commits, but doesn't push or create PRs. Manual push and PR creation is tedious when rotating keys across many repositories.

**Note:** Additional improvements (key validation, parallel processing, etc.) are documented separately in `trufflehog-rotate-aws-key-other-improvements.md`.

---

## Feature: Push Commits and Create Pull Requests
**Current State:** Script creates branches and commits, but doesn't push or create PRs
**Problem:** Manual push and PR creation is tedious when rotating keys across many repositories. Workflow is incomplete without these steps.

**Proposed Solution:**
- Add `--push` flag to push commits to remote repositories
- Add `--create-pr` flag to automatically create pull requests after pushing
- Support resume mode for push/PR operations on previously committed changes
- Support GitHub CLI (`gh`) or GitHub API for PR creation
- Configurable PR title and body templates
- Support for draft PRs (`--draft-pr`)
- Track push and PR status in state file

**Workflow Overview:**

The workflow has **natural stopping points** between stages, allowing you to review at each step. Each stage can be done in a separate session using the `--resume` flag.

**State Transition Diagram:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    INITIAL RUN (dry-run or commit)               │
│  ./trufflehog-rotate-aws-key.py -r report.md -i ID -p --mode   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ Files Modified │
                    │ Branch Created │
                    │ changes_committed: false │
                    │ pushed: false            │
                    │ pr_created: false        │
                    └────────┬─────────────────┘
                             │
                    ═════════╪══════════════════
                    STOP #1  │ Review files
                    ═════════╪══════════════════
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              RESUME SESSION #1: Commit Changes                  │
│  ./trufflehog-rotate-aws-key.py --resume -i ID --mode commit    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ Changes Committed │
                    │ changes_committed: true │
                    │ pushed: false            │
                    │ pr_created: false        │
                    └────────┬─────────────────┘
                             │
                    ═════════╪══════════════════
                    STOP #2  │ Review commits
                    ═════════╪══════════════════
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              RESUME SESSION #2: Push Commits                    │
│  ./trufflehog-rotate-aws-key.py --resume -i ID --push           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ Branch Pushed  │
                    │ changes_committed: true │
                    │ pushed: true             │
                    │ pr_created: false        │
                    └────────┬─────────────────┘
                             │
                    ═════════╪══════════════════
                    STOP #3  │ Verify pushes
                    ═════════╪══════════════════
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│          RESUME SESSION #3: Create Pull Requests                │
│  ./trufflehog-rotate-aws-key.py --resume -i ID --create-pr      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ PRs Created    │
                    │ changes_committed: true │
                    │ pushed: true             │
                    │ pr_created: true         │
                    │ pr_url: "https://..."    │
                    └──────────────────────────┘
                             │
                             ▼
                          DONE!
```

**Detailed Workflow Stages:**

#### Stage 1: Modify Files (Initial Run)

**Command:**
```bash
./trufflehog-rotate-aws-key.py \
    -r report.md \
    -i RAW_abc123_def456 \
    -p \
    --mode dry-run
```

**What Happens:**
- Parses the trufflehog report
- Clones repositories (or reuses existing clones)
- Creates branches
- **Modifies files** with new key values
- **Does NOT commit** (dry-run mode)
- Saves state file: `~/.secure/trufflehog-rotate/RAW_abc123_def456-<timestamp>.json`

**State File After This Stage:**
```json
{
  "identifier": "RAW_abc123_def456",
  "mode": "dry-run",
  "repositories": [{
    "repository_name": "repo1",
    "branch_name": "rotate-aws-key-abc123-20251218-120000",
    "status": "completed",
    "files_modified": ["config/aws.json"],
    "changes_committed": false,    // ← Not committed yet
    "pushed": false,               // ← Not pushed yet
    "pr_created": false            // ← No PR yet
  }]
}
```

**STOP POINT #1:** Review the modified files
- Check the branches locally
- Review diffs: `git diff` in each repository
- Verify the key replacements are correct
- Decide if you want to proceed with committing

#### Stage 2: Commit Changes (Resume Session #1)

**Command:**
```bash
./trufflehog-rotate-aws-key.py \
    --resume \
    -i RAW_abc123_def456 \
    --mode commit
```

**What Happens:**
- Loads state file from Stage 1
- Finds repositories with `changes_committed: false`
- Checks out the rotation branches
- **Commits the changes** (if uncommitted changes exist)
- Updates state file with commit information

**State File After This Stage:**
```json
{
  "repositories": [{
    "repository_name": "repo1",
    "changes_committed": true,      // ← Now committed!
    "commit_hash": "abc123...",
    "pushed": false,                // ← Still not pushed
    "pr_created": false             // ← Still no PR
  }]
}
```

**STOP POINT #2:** Review the commits
- Verify commits were created correctly
- Check commit messages
- Review commit diffs: `git log -p` in each repository
- Decide if you want to proceed with pushing

#### Stage 3: Push Commits (Resume Session #2)

**Command:**
```bash
./trufflehog-rotate-aws-key.py \
    --resume \
    -i RAW_abc123_def456 \
    --push
```

**What Happens:**
- Loads state file from Stage 2
- Finds repositories with `changes_committed: true` and `pushed: false`
- Checks out the rotation branches
- **Pushes branches to remote**: `git push origin <branch-name>`
- Updates state file with push status

**State File After This Stage:**
```json
{
  "repositories": [{
    "repository_name": "repo1",
    "changes_committed": true,
    "commit_hash": "abc123...",
    "pushed": true,                 // ← Now pushed!
    "push_timestamp": "2025-12-18T12:30:00",
    "pr_created": false             // ← Still no PR
  }]
}
```

**STOP POINT #3:** Verify pushes succeeded
- Check branches exist on remote: `git ls-remote origin <branch-name>`
- Verify on GitHub that branches are visible
- Review pushed commits on GitHub
- Decide if you want to proceed with creating PRs

#### Stage 4: Create Pull Requests (Resume Session #3)

**Command:**
```bash
./trufflehog-rotate-aws-key.py \
    --resume \
    -i RAW_abc123_def456 \
    --create-pr \
    --pr-labels "security,automated" \
    --pr-reviewers "alice,bob"
```

**What Happens:**
- Loads state file from Stage 3
- Finds repositories with `pushed: true` and `pr_created: false`
- Creates pull requests using GitHub CLI or API
- Updates state file with PR information

**State File After This Stage:**
```json
{
  "repositories": [{
    "repository_name": "repo1",
    "changes_committed": true,
    "pushed": true,
    "push_timestamp": "2025-12-18T12:30:00",
    "pr_created": true,             // ← PR created!
    "pr_url": "https://github.com/org/repo1/pull/123",
    "pr_number": 123,
    "pr_timestamp": "2025-12-18T12:35:00"
  }]
}
```

**END:** Workflow complete! PRs are ready for review.

**Alternative: Combined Workflows:**
```bash
# Option A: Commit and push together
./trufflehog-rotate-aws-key.py --resume -i RAW_abc123 --mode commit --push

# Option B: All-in-one (after initial review)
./trufflehog-rotate-aws-key.py --resume -i RAW_abc123 \
    --mode commit --push --create-pr
```

**How Resume Mode Works:**

The state file tracks the progress of each repository through these fields:
1. **`changes_committed`**: `false` → `true` when commits are made
2. **`pushed`**: `false` → `true` when branch is pushed
3. **`pr_created`**: `false` → `true` when PR is created

When you run `--resume`, the script:
1. **Loads the state file** (auto-detects most recent for identifier, or use `--state-file`)
2. **Filters repositories** based on what needs to be done:
   - For **commit**: Finds repos with `changes_committed: false`
   - For **push**: Finds repos with `changes_committed: true` and `pushed: false`
   - For **PR**: Finds repos with `pushed: true` and `pr_created: false`
3. **Processes only what's needed** - skips repos that are already done
4. **Updates state file** with new status

**State File Location:**
```
~/.secure/trufflehog-rotate/<identifier>-<timestamp>.json
```

**Example:**
```
~/.secure/trufflehog-rotate/RAW_abc123_def456-20251218-120000.json
```

**Common Workflow Patterns:**

**Pattern 1: Conservative (Recommended for First Time)**
```bash
# 1. Make changes, review carefully
./trufflehog-rotate-aws-key.py -r report.md -i RAW_abc123 -p --mode dry-run

# 2. Review files, then commit
./trufflehog-rotate-aws-key.py --resume -i RAW_abc123 --mode commit

# 3. Review commits, then push
./trufflehog-rotate-aws-key.py --resume -i RAW_abc123 --push

# 4. Review pushes, then create PRs
./trufflehog-rotate-aws-key.py --resume -i RAW_abc123 --create-pr
```

**Pattern 2: Fast Track (After You're Confident)**
```bash
# 1. Make changes and review
./trufflehog-rotate-aws-key.py -r report.md -i RAW_abc123 -p --mode dry-run

# 2. Commit, push, and create PRs in one go
./trufflehog-rotate-aws-key.py --resume -i RAW_abc123 \
    --mode commit --push --create-pr
```

**Pattern 3: Staged Rollout**
```bash
# 1. Make changes for first 5 repos
./trufflehog-rotate-aws-key.py -r report.md -i RAW_abc123 -p --mode dry-run -l 5

# 2. Commit and push first batch
./trufflehog-rotate-aws-key.py --resume -i RAW_abc123 --mode commit --push

# 3. Create PRs for first batch
./trufflehog-rotate-aws-key.py --resume -i RAW_abc123 --create-pr

# 4. Process next 5 repos (resume continues from where it left off)
./trufflehog-rotate-aws-key.py --resume -i RAW_abc123 --mode commit --push -l 5
```

**Benefits of This Workflow:**

1. **Safety**
   - Review changes before committing
   - Review commits before pushing
   - Review pushes before creating PRs
   - Can abort at any stage

2. **Flexibility**
   - Can pause between stages
   - Can resume days/weeks later
   - Can skip problematic repositories
   - Can retry failed operations

3. **Error Recovery**
   - If commit fails, can fix and retry
   - If push fails, can retry without re-committing
   - If PR creation fails, can retry without re-pushing
   - State file tracks what's done vs. what's pending

4. **Partial Operations**
   - Can commit some repos, push others later
   - Can push some repos, create PRs for others later
   - Can skip specific repos with `--skip-repos`

**Troubleshooting:**

**Problem: "No state file found"**
- **Solution:** Specify state file explicitly:
  ```bash
  ./trufflehog-rotate-aws-key.py --resume \
      --state-file ~/.secure/trufflehog-rotate/RAW_abc123_def456-20251218-120000.json
  ```

**Problem: "Local clone path does not exist"**
- **Solution:** Re-run initial command to recreate clones, or use `--reuse-clones`:
  ```bash
  ./trufflehog-rotate-aws-key.py -r report.md -i RAW_abc123 -p --mode dry-run --reuse-clones
  ```

**Problem: Want to skip a problematic repository**
- **Solution:** Use `--skip-repos`:
  ```bash
  ./trufflehog-rotate-aws-key.py --resume -i RAW_abc123 --push --skip-repos "problematic-repo"
  ```

**Problem: Want to retry failed operations**
- **Solution:** Just run resume again - it will retry failed repos:
  ```bash
  ./trufflehog-rotate-aws-key.py --resume -i RAW_abc123 --mode commit
  ```

**CLI Options:**
```bash
# Push Configuration
--push                    # Push commits to remote (requires --mode commit or --resume)
--force-push              # Force push if branch exists on remote (dangerous!)
--push-remote <name>      # Remote name to push to (default: 'origin')
--skip-if-exists          # Skip push if branch already exists on remote
--skip-push <repos>       # Skip pushing for specific repositories (comma-separated)

# PR Configuration
--create-pr               # Create pull request after pushing (requires --push)
--draft-pr                # Create draft PRs (requires --create-pr)
--pr-title <template>     # PR title template (supports {identifier}, {repo}, {branch})
--pr-body <file>          # PR body template file (or use default)
--pr-labels <labels>      # Comma-separated labels (e.g., "security,automated")
--pr-reviewers <users>    # Comma-separated GitHub usernames for review
--pr-assignees <users>    # Comma-separated GitHub usernames to assign
--pr-base-branch <branch> # Base branch for PR (default: from state file or 'main')
--skip-pr <repos>         # Skip PR creation for specific repositories (comma-separated)

# GitHub Authentication
--github-token <token>    # GitHub token for API (alternative to gh CLI)
--use-gh-cli              # Use GitHub CLI (gh) for PR creation (default if available)
--use-github-api          # Use GitHub API directly (requires token)
```

**Default Behavior:**
- **Push**: Only pushes if `--push` is explicitly set (safety)
- **PR Creation**: Only creates PRs if `--create-pr` is explicitly set
- **Authentication**: Prefer GitHub CLI (`gh`), fallback to GitHub API with token
- **Force Push**: Never force push unless `--force-push` is set

**Push Functionality:**
- For each repository with committed changes:
  - Check if branch exists locally
  - Check if branch exists on remote (optional check)
  - Push branch to remote: `git push origin <branch-name>`
  - Handle push failures (authentication, conflicts, etc.)
  - Update state file with push status

**PR Creation Functionality:**
- For each repository with pushed branch:
  - Determine base branch (from state or default to 'main')
  - Generate PR title from template (default: `"Rotate AWS key: {identifier}"`)
  - Generate PR body from template or file
  - Create PR using GitHub CLI or API
  - Extract PR URL and number
  - Update state file with PR information

**PR Body Default Template:**
- Summary of rotation
- List of files modified
- Security context (why rotation is needed)
- Link to original trufflehog report

**Error Handling:**
- **Push failures:**
  - Authentication failure: Skip with clear error, don't retry
  - Branch exists on remote: Skip (or force push if `--force-push`)
  - Network error: Retry with exponential backoff
  - Permission denied: Skip with error message
- **PR creation failures:**
  - Skip repository, continue with others
  - Retry transient errors (network, rate limits)
  - Don't retry permanent errors (auth, permissions)
  - Check if PR already exists, skip if found

**State File Extensions:**
```json
{
  "repositories": [{
    "repository_name": "repo1",
    "branch_name": "rotate-aws-key-abc123-20251218-120000",
    "changes_committed": true,
    "commit_hash": "abc123...",

    // NEW FIELDS:
    "pushed": false,              // Whether branch was pushed
    "push_attempted": false,      // Whether push was attempted
    "push_error": null,            // Error message if push failed
    "push_timestamp": null,       // When push succeeded

    "pr_created": false,          // Whether PR was created
    "pr_attempted": false,         // Whether PR creation was attempted
    "pr_url": null,                // PR URL if created
    "pr_number": null,             // PR number if created
    "pr_error": null,              // Error message if PR creation failed
    "pr_timestamp": null           // When PR was created
  }]
}
```

**Implementation Code Structure:**
```python
def push_branch(repo: Repo, branch_name: str, remote: str = 'origin',
                force: bool = False) -> Tuple[bool, Optional[str]]:
    """Push branch to remote. Returns: (success, error_message)"""
    try:
        if force:
            repo.git.push(remote, branch_name, force=True)
        else:
            repo.git.push(remote, branch_name)
        return True, None
    except GitCommandError as e:
        return False, str(e)

def create_pull_request(org: str, repo: str, branch: str, base: str,
                       title: str, body: str, labels: List[str] = None,
                       reviewers: List[str] = None, draft: bool = False,
                       use_cli: bool = True) -> Tuple[bool, Optional[Dict]]:
    """Create pull request. Returns: (success, pr_info)"""
    if use_cli:
        return create_pr_via_cli(...)
    else:
        return create_pr_via_api(...)
```

**Critical Questions and Decisions:**

1. **Authentication:** Support both GitHub CLI and API, prefer CLI. Token from `GITHUB_TOKEN` env var or keychain.

2. **Push Behavior:** Skip if branch exists on remote by default. Require `--force-push` for force push. Support custom remote name.

3. **PR Creation:** Support both CLI and API, prefer CLI. Check if PR already exists, skip if found. Use branch from state file as base, allow override.

4. **State Management:** Track push/PR status per repository in state file. Only process repos that need push/PR in resume mode.

5. **Error Handling:** Continue on failures, update state file, don't rollback. Retry transient errors, not permanent ones.

6. **Workflow:** Support combined (`--push --create-pr`) and separate operations for flexibility.

**Example Usage:**
```bash
# Full workflow: commit, push, and create PRs
./trufflehog-rotate-aws-key.py -r report.md -i RAW_abc123 -p \
    --mode commit --push --create-pr \
    --pr-labels "security,automated" \
    --pr-reviewers "alice,bob"

# Resume: push and create PRs for previously committed changes
./trufflehog-rotate-aws-key.py --resume --push --create-pr

# Push only
./trufflehog-rotate-aws-key.py --resume --push

# Create PRs for already-pushed branches
./trufflehog-rotate-aws-key.py --resume --create-pr
```

---

## Dependencies

### New Dependencies
- **GitHub CLI (`gh`)**: For PR creation (optional but recommended, simpler auth)
- **PyGithub**: For GitHub API access (alternative to `gh` CLI, requires token)

### Installation
```bash
# Install GitHub CLI (recommended for push/PR features)
brew install gh  # macOS
# or download from https://cli.github.com/
gh auth login    # Authenticate with GitHub

# Install Python dependencies
pip install PyGithub  # For GitHub API (if not using gh CLI)
```

### GitHub Authentication
- **Option 1 (Recommended):** Use GitHub CLI - run `gh auth login` separately
- **Option 2:** Use GitHub API with token from `GITHUB_TOKEN` environment variable
- **Token Permissions:** Requires `repo` scope for private repositories, `public_repo` for public only

---

## Backward Compatibility

All improvements should be **backward compatible**:
- New features are opt-in via flags
- Default behavior remains unchanged
- Existing state files continue to work
- CLI arguments remain compatible

---

## Testing Strategy

### Unit Tests
- PR creation (mocked GitHub API)
- Push functionality (mocked git operations)
- State file serialization for push/PR status

### Integration Tests
- Full rotation with PR creation
- Push and PR creation with resume mode
- Error recovery for push/PR failures

### Manual Testing
- Test with real repositories
- Test PR creation with GitHub CLI and API
- Test push functionality with various scenarios
- Test resume mode for push/PR operations

---

## Security Considerations

### PR Creation
- Use GitHub token from environment or keychain
- Never log or store tokens
- Support GitHub CLI authentication (preferred)

### State File
- Continue storing keys as hashes
- Add PR URLs (public, safe to store)
- Add checksums for verification

---

## Migration Path

### For Existing Users
1. No changes required - script remains compatible
2. New features are opt-in
3. State files remain compatible
4. Documentation updated with new options

### For New Features
1. Implement behind feature flags
2. Add to design document
3. Update README with examples
4. Add to test suite

---

## Success Criteria

1. ✅ Can push commits to remote repositories
2. ✅ Can create pull requests automatically after pushing
3. ✅ Tracks push/PR status in state file for resume operations
4. ✅ Handles push/PR errors gracefully
5. ✅ Provides clear feedback and PR URLs
6. ✅ Maintains backward compatibility
7. ✅ Supports both GitHub CLI and API for PR creation
8. ✅ All features are well-tested

---

## Critical Questions for Push/PR Feature

The push and PR creation feature raises several important questions that need decisions:

### Authentication
- **Q:** How should the script authenticate with GitHub?
- **A:** Support both GitHub CLI (`gh`) and API, prefer CLI. Token from `GITHUB_TOKEN` env var.

### Push Behavior
- **Q:** What if branch already exists on remote?
- **A:** Skip push by default, require `--force-push` flag for force push.

- **Q:** What if local branch is behind remote?
- **A:** Skip push, warn user, suggest manual resolution.

### PR Creation
- **Q:** What if PR already exists for this branch?
- **A:** Check if PR exists, skip if found, log warning.

- **Q:** Should PRs be draft by default?
- **A:** No, ready for review by default. Use `--draft-pr` flag for draft PRs.

- **Q:** How to determine base branch for PR?
- **A:** Use branch from state file (where key was found), allow override with `--pr-base-branch`.

### Error Handling
- **Q:** What if push fails partway through?
- **A:** Continue with remaining repos, update state file, don't rollback.

- **Q:** What if PR creation fails after successful push?
- **A:** Leave branch pushed, update state, allow manual PR creation.

- **Q:** How to handle rate limiting?
- **A:** Detect rate limit errors, wait and retry, or skip and continue.

### Workflow
- **Q:** Should push and PR creation be separate steps?
- **A:** Support both combined (`--push --create-pr`) and separate for flexibility.

- **Q:** How to handle dry-run mode with push/PR?
- **A:** Support `--dry-run` with `--push` and `--create-pr` to preview operations.

## Open Questions

1. **State File Format**: Version state files?
   - **Recommendation**: Yes, add version field

2. **Parallel Push/PR**: Should push/PR operations be parallelized?
   - **Recommendation**: Not in initial implementation, add later when parallel processing is implemented

---

## Next Steps

1. Review and approve design decisions
2. Create implementation plan
3. Begin implementation of push functionality
4. Implement PR creation functionality
5. Update tests and documentation

---

**Document Status:** Draft for Review
**Last Updated:** 2025-12-18
