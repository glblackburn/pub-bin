# Clone Directory Exists Error - Analysis and Fix

## Problem Summary

The script fails when attempting to clone repositories into directories that already exist from previous runs. All 5 repositories failed with the same error:

```
fatal: destination path '/tmp/trufflehog-rotate/repos/skaivision-<repo-name>' already exists and is not an empty directory.
```

## Root Cause

The `clone_repository()` function in `trufflehog-rotate-aws-key.py` has a logic flaw:

1. **Current Behavior:**
   - If `--reuse-clones` flag is **not** set (default), the function attempts to clone directly
   - If the target directory already exists, `git clone` fails because it won't overwrite existing directories
   - The function only checks for existing directories when `reuse=True`, but doesn't handle the case when `reuse=False` and directory exists

2. **Code Location:**
   - Function: `clone_repository()` (lines ~194-212)
   - Issue: Lines 199-205 only handle the `reuse=True` case
   - Missing: Handling for `reuse=False` when directory exists

3. **Why This Happens:**
   - User runs script multiple times with same identifier
   - Previous runs created clone directories in `/tmp/trufflehog-rotate/repos/`
   - Directories persist between runs (not cleaned up)
   - Next run tries to clone into same paths → fails

## Error Details

**Error Pattern:**
```
Clone failed: Cmd('git') failed due to: exit code(128)
cmdline: git clone -v -- git@github.com:org/repo.git /tmp/trufflehog-rotate/repos/org-repo
stderr: 'fatal: destination path '...' already exists and is not an empty directory.'
```

**Affected Functionality:**
- All repository cloning operations fail
- Script cannot proceed with key rotation
- User must manually clean directories or use `--reuse-clones` flag

## Suggested Fixes

### Option 1: Auto-Detect and Reuse Existing Clones (Recommended)

**Behavior:** If directory exists and `reuse=False`, automatically treat it as an existing clone and update it instead of failing.

**Implementation:**
```python
def clone_repository(repo_url: str, local_path: Path, reuse: bool = False, verbose: bool = False) -> bool:
    """
    Clone repository to local path.
    Returns: True if successful, False otherwise
    """
    # If directory exists, check if it's a valid git repo
    if local_path.exists():
        if local_path.is_dir() and (local_path / '.git').exists():
            # It's an existing git repository
            if verbose:
                print(f"  Using existing clone: {local_path}", file=sys.stderr)
            try:
                repo = Repo(local_path)
                repo.remotes.origin.fetch()
                # Optionally: repo.git.pull() to ensure up-to-date
                return True
            except Exception as e:
                if verbose:
                    print(f"  Failed to use existing clone: {e}", file=sys.stderr)
                # Fall through to remove and re-clone
                if verbose:
                    print(f"  Removing existing directory to re-clone", file=sys.stderr)
                import shutil
                shutil.rmtree(local_path)
        else:
            # Directory exists but isn't a git repo - remove it
            if verbose:
                print(f"  Removing non-git directory: {local_path}", file=sys.stderr)
            import shutil
            shutil.rmtree(local_path)

    # Continue with normal clone process...
```

**Pros:**
- User-friendly: No need to remember `--reuse-clones` flag
- Handles edge cases (corrupted clones, non-git directories)
- Automatically updates existing clones

**Cons:**
- May silently reuse stale clones (mitigated by fetch/pull)
- More complex logic

### Option 2: Clear Error Message with Suggestion

**Behavior:** If directory exists and `reuse=False`, provide clear error message suggesting `--reuse-clones` flag.

**Implementation:**
```python
def clone_repository(repo_url: str, local_path: Path, reuse: bool = False, verbose: bool = False) -> bool:
    """
    Clone repository to local path.
    Returns: True if successful, False otherwise
    """
    if local_path.exists() and not reuse:
        print(f"ERROR: Directory already exists: {local_path}", file=sys.stderr)
        print(f"  Use --reuse-clones to update existing clones, or manually remove the directory", file=sys.stderr)
        return False

    if local_path.exists() and reuse:
        # Existing reuse logic...
```

**Pros:**
- Simple and explicit
- Forces user to make conscious decision
- Clear error message

**Cons:**
- Requires user action (either flag or manual cleanup)
- Less convenient for repeated runs

### Option 3: Remove and Re-clone (Aggressive)

**Behavior:** If directory exists and `reuse=False`, remove it and clone fresh.

**Implementation:**
```python
def clone_repository(repo_url: str, local_path: Path, reuse: bool = False, verbose: bool = False) -> bool:
    """
    Clone repository to local path.
    Returns: True if successful, False otherwise
    """
    if local_path.exists():
        if reuse:
            # Existing reuse logic...
        else:
            # Remove existing directory and clone fresh
            if verbose:
                print(f"  Removing existing directory: {local_path}", file=sys.stderr)
            import shutil
            shutil.rmtree(local_path)

    # Continue with normal clone...
```

**Pros:**
- Always gets fresh clone
- No user intervention needed
- Simple logic

**Cons:**
- Destructive: Removes existing work
- May lose uncommitted changes in clones
- Slower (always re-clones)

### Option 4: Hybrid Approach (Recommended for Production)

**Behavior:** Combine Option 1 and Option 2 - auto-detect valid git repos, but error on invalid directories.

**Implementation:**
```python
def clone_repository(repo_url: str, local_path: Path, reuse: bool = False, verbose: bool = False) -> bool:
    """
    Clone repository to local path.
    Returns: True if successful, False otherwise
    """
    if local_path.exists():
        if (local_path / '.git').exists():
            # Valid git repository - reuse it
            if verbose:
                print(f"  Using existing clone: {local_path}", file=sys.stderr)
            try:
                repo = Repo(local_path)
                repo.remotes.origin.fetch()
                return True
            except Exception as e:
                if verbose:
                    print(f"  Existing clone appears corrupted: {e}", file=sys.stderr)
                    print(f"  Removing and re-cloning...", file=sys.stderr)
                import shutil
                shutil.rmtree(local_path)
        else:
            # Directory exists but isn't a git repo
            print(f"ERROR: Directory exists but is not a git repository: {local_path}", file=sys.stderr)
            print(f"  Please remove it manually or use a different --work-dir", file=sys.stderr)
            return False

    # Continue with normal clone process...
```

**Pros:**
- Best of both worlds: auto-reuse valid clones, error on invalid
- Safe: Won't accidentally remove non-git directories
- User-friendly for common case (repeated runs)

**Cons:**
- Slightly more complex
- Still requires manual cleanup for non-git directories

## Chosen Solution

**Timestamp-based Unique Work Directory (Implemented)**

Instead of reusing the same work directory, the script now creates a unique timestamped directory for each run by default.

**Implementation:**
- Default work directory changed from `/tmp/trufflehog-rotate` to `/tmp/trufflehog-rotate-YYYYMMDD-HHMMSS`
- Timestamp is generated when the script starts (at argument parser creation)
- Format: `/tmp/trufflehog-rotate-20251218-130715` (example)
- Users can still override with `--work-dir` if they want a specific directory

**Code Changes:**
```python
# Generate default work directory with timestamp to avoid conflicts
default_work_dir = f'/tmp/trufflehog-rotate-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
parser.add_argument('--work-dir', default=default_work_dir, help='Working directory for cloning repositories (default: /tmp/trufflehog-rotate-YYYYMMDD-HHMMSS)')
```

**Benefits:**
1. **Eliminates conflicts:** Each run gets its own unique directory
2. **No "directory already exists" errors:** Fresh directory for every execution
3. **Easy identification:** Timestamp in directory name makes it easy to identify runs
4. **Preserves history:** Previous runs remain available for reference
5. **Simple solution:** Minimal code change, no complex logic needed
6. **Backward compatible:** Users can still specify `--work-dir` for custom paths

**Why This Solution:**
- **Simpler than Option 4:** No need to detect/reuse existing clones - just create new ones
- **More reliable:** No edge cases with corrupted clones or non-git directories
- **Better isolation:** Each run is completely isolated from previous runs
- **Easier debugging:** Can compare results across multiple runs by examining different directories

## Alternative Solutions (Not Chosen)

**Option 4 (Hybrid Approach)** was considered but not chosen because:

1. **More complex:** Requires detecting valid git repos, handling corrupted clones, etc.
2. **Potential issues:** Reusing clones might have stale data or unexpected state
3. **Less isolation:** Multiple runs could interfere with each other
4. **More code:** More logic to maintain and test

The timestamp approach is simpler, more reliable, and provides better isolation between runs.

## Additional Considerations

### Cleanup Strategy

Consider adding a cleanup option:
- `--clean-work-dir`: Remove all existing clones before starting
- `--clean-on-exit`: Clean up clones after successful completion
- Automatic cleanup of old clones (older than X days)

### State File Integration

The state file already tracks clone paths. Could use this to:
- Verify clones match expected state
- Clean up clones from previous failed runs
- Resume with existing clones automatically

## Testing Recommendations

1. **Test Case 1:** Run script twice with same identifier
   - First run: Should clone successfully
   - Second run: Should reuse existing clones (with Option 4)

2. **Test Case 2:** Corrupted clone directory
   - Create directory with `.git` but corrupted
   - Should detect and re-clone

3. **Test Case 3:** Non-git directory exists
   - Create regular directory (not a git repo)
   - Should error with clear message

4. **Test Case 4:** `--reuse-clones` flag
   - Should work as before (explicit reuse)

## Related Code Locations

- `clone_repository()` function: Lines ~194-212
- `process_repository()` function: Lines ~283-405 (calls clone_repository)
- `--reuse-clones` argument: Line ~445
- State file tracking: Lines ~715-722

## Workaround (Before Fix)

Before the fix was implemented, users could:

1. **Use `--reuse-clones` flag:**
   ```bash
   ./trufflehog-rotate-aws-key.py ... --reuse-clones
   ```

2. **Manually clean directories:**
   ```bash
   rm -rf /tmp/trufflehog-rotate/repos/*
   ```

3. **Use different work directory:**
   ```bash
   ./trufflehog-rotate-aws-key.py ... --work-dir /tmp/trufflehog-rotate-new
   ```

## Implementation Status

**Status:** ✅ **IMPLEMENTED** (2025-12-18)

The fix has been implemented by changing the default work directory to include a timestamp postfix. Each script execution now automatically creates a unique directory, preventing the "directory already exists" error.

**Files Modified:**
- `trufflehog/trufflehog-rotate-aws-key.py` - Updated default `--work-dir` argument to include timestamp

**Testing:**
- Script now creates unique directories for each run
- No conflicts with previous runs
- Users can still override with `--work-dir` if needed

---

**Date:** 2025-12-18
**Issue:** Clone directory exists error preventing script execution
**Status:** ✅ Fixed - Timestamp-based unique work directories implemented
