# Trufflehog AWS Key Rotation Script - Additional Design Improvements

**Date:** 2025-12-18
**Purpose:** Additional design improvements for `trufflehog-rotate-aws-key.py` beyond the commit/push/PR workflow

---

## Executive Summary

This document outlines additional design improvements for `trufflehog-rotate-aws-key.py` that complement the commit/push/PR workflow. These improvements focus on validation, verification, performance, error handling, and extending functionality.

**Note:** The commit/push/PR workflow is documented separately in `trufflehog-rotate-aws-key-commit-push-pr-design.md`.

---

## Improvement Categories

### 1. **Key Validation** (High Priority)
**Current State:** No validation of new key before rotation
**Problem:** Invalid keys cause failures across all repositories

**Proposed Solution:**
- Validate AWS key format before starting rotation
- Optional: Test key validity with AWS API (if credentials available)
- Validate key format matches old key format (access key vs secret key)
- Early exit with clear error if validation fails

**CLI Options:**
```bash
--validate-key          # Validate new key format (default: true)
--skip-validation       # Skip validation (not recommended)
--test-key              # Test key with AWS API (requires AWS credentials)
```

**Validation Rules:**
- AWS Access Key ID: Must start with `AKIA` and be 20 characters
- AWS Secret Access Key: Must be 40 characters (base64-like)
- Pattern matching for common formats
- Warn if key format doesn't match old key format

**Implementation:**
```python
def validate_aws_key(key: str, key_type: str = 'access') -> Tuple[bool, str]:
    """
    Validate AWS key format.
    Returns: (is_valid, error_message)
    """
    if key_type == 'access':
        if not key.startswith('AKIA'):
            return False, "AWS Access Key ID must start with 'AKIA'"
        if len(key) != 20:
            return False, f"AWS Access Key ID must be 20 characters (got {len(key)})"
    elif key_type == 'secret':
        if len(key) != 40:
            return False, f"AWS Secret Access Key must be 40 characters (got {len(key)})"
    return True, ""
```

---

### 2. **Better Diff Viewing and Verification** (Medium Priority)
**Current State:** `--verify-changes` mentioned in design but not implemented
**Problem:** Users want to review changes before committing

**Proposed Solution:**
- Implement `--verify-changes` option
- Show diff for each file before replacement
- Interactive confirmation per file or per repository
- Summary diff view showing all changes
- Option to skip specific files/repos during verification

**CLI Options:**
```bash
--verify-changes        # Show diff and prompt before making changes
--verify-interactive    # Interactive mode: confirm each file/repo
--verify-summary        # Show summary of all changes before starting
--skip-verify           # Skip verification (for automation)
```

**Output Format:**
```
[1/5] Repository: org/repo1
  File: config/aws.json (line 42)
  Old: AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
  New: AWS_ACCESS_KEY_ID=AKIANEWKEYEXAMPLE123
  Apply this change? [y/N/skip]:
```

**Implementation:**
- Use `git diff` to show changes
- Support both per-file and per-repo confirmation
- Store verification results in state file
- Resume mode should respect previous verifications

---

### 3. **Parallel Processing** (Medium Priority)
**Current State:** Processes repositories sequentially
**Problem:** Slow when rotating keys across many repositories

**Proposed Solution:**
- Add `--parallel <N>` option to process N repositories concurrently
- Use Python's `concurrent.futures.ThreadPoolExecutor` or `ProcessPoolExecutor`
- Thread-safe state file updates
- Progress reporting for parallel operations
- Limit concurrent clones to avoid rate limiting

**CLI Options:**
```bash
--parallel <N>          # Process N repositories in parallel (default: 1)
--max-parallel <N>      # Maximum parallel operations (default: 5)
```

**Implementation Considerations:**
- Thread-safe logging
- Atomic state file updates (use file locking)
- Handle SSH connection limits
- Respect GitHub rate limits (5000 requests/hour)
- Progress bar or status updates

**Example:**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=args.parallel) as executor:
    futures = {
        executor.submit(process_repository, repo_info, ...): repo_info
        for repo_info in repo_list
    }
    for future in as_completed(futures):
        status = future.result()
        # Update state file atomically
```

---

### 4. **Enhanced Error Recovery and Retry Logic** (Medium Priority)
**Current State:** Basic error handling, no retry logic
**Problem:** Network issues cause failures that could be retried

**Proposed Solution:**
- Exponential backoff retry for network operations
- Configurable retry counts and delays
- Resume from specific failure points
- Better error categorization (transient vs permanent)
- Automatic retry for transient failures

**CLI Options:**
```bash
--retry <count>         # Number of retries for failed operations (default: 3)
--retry-delay <sec>    # Initial retry delay in seconds (default: 5)
--retry-backoff <mult> # Retry delay multiplier (default: 2.0)
--skip-failed          # Skip repositories that fail after retries
```

**Retry Strategy:**
- Clone failures: Retry with exponential backoff
- Network timeouts: Retry with backoff
- Authentication errors: Don't retry (permanent)
- Permission errors: Don't retry (permanent)
- Branch conflicts: Don't retry (requires manual resolution)

**Implementation:**
```python
def retry_operation(func, max_retries=3, delay=5, backoff=2.0):
    """Retry operation with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except TransientError as e:
            if attempt < max_retries - 1:
                time.sleep(delay * (backoff ** attempt))
                continue
            raise
        except PermanentError as e:
            raise  # Don't retry permanent errors
```

---

### 5. **Support for Multiple Secret Types** (Medium Priority)
**Current State:** Only supports AWS keys
**Problem:** Users may want to rotate other types of secrets

**Proposed Solution:**
- Make secret type configurable
- Support common secret types: AWS keys, GitHub tokens, API keys, etc.
- Type-specific validation and replacement patterns
- Extensible pattern system

**CLI Options:**
```bash
--secret-type <type>    # Secret type: aws-key, github-token, api-key, etc.
--custom-pattern <re>   # Custom regex pattern for replacement
```

**Secret Types:**
- `aws-key`: AWS Access Key ID (current implementation)
- `aws-secret`: AWS Secret Access Key
- `github-token`: GitHub personal access token
- `api-key`: Generic API key
- `custom`: User-defined pattern

**Implementation:**
```python
SECRET_PATTERNS = {
    'aws-key': [
        r'(AWS_ACCESS_KEY_ID\s*[=:]\s*["\']?)' + re.escape(old_key) + r'(["\']?)',
        # ... existing patterns
    ],
    'github-token': [
        r'(GITHUB_TOKEN\s*[=:]\s*["\']?)' + re.escape(old_key) + r'(["\']?)',
        r'("github_token"\s*:\s*["\']?)' + re.escape(old_key) + r'(["\']?)',
    ],
    # ...
}
```

---

### 6. **Interactive Mode** (Low Priority)
**Current State:** Fully automated or fully manual
**Problem:** Users may want to selectively process repositories

**Proposed Solution:**
- Interactive selection of repositories to process
- Per-repository confirmation
- Ability to skip specific repos during execution
- Preview of changes before processing

**CLI Options:**
```bash
--interactive           # Interactive mode: select repos to process
--interactive-filter   # Filter repos before interactive selection
```

**Interactive Flow:**
```
Found 10 repositories with key RAW_abc123_def456:

[1] org/repo1 (3 files)
[2] org/repo2 (1 file)
[3] org/repo3 (2 files)
...
[10] org/repo10 (1 file)

Select repositories to process (comma-separated, 'all', or 'none'):
> 1,3,5-7

Processing selected repositories...
```

---

### 7. **Rollback Functionality** (Low Priority)
**Current State:** No rollback capability
**Problem:** If rotation fails partway through, difficult to undo

**Proposed Solution:**
- Store original key values in secure backup
- `--rollback` command to undo changes
- Rollback specific repositories or all
- Verify rollback success

**CLI Options:**
```bash
--rollback              # Rollback changes from state file
--rollback-repos <list> # Rollback specific repositories only
--rollback-verify       # Verify rollback was successful
```

**Rollback Process:**
1. Load state file
2. For each repository with changes:
   - Checkout the rotation branch
   - Restore files from backup
   - Commit rollback changes
   - Optionally delete branch
3. Update state file with rollback status

**Implementation:**
```python
def rollback_rotation(state_file: Path, repos: Optional[List[str]] = None):
    """Rollback rotation changes."""
    state = load_state(state_file)
    for repo_status in state['repositories']:
        if repos and repo_status['repository_name'] not in repos:
            continue
        # Restore from backup and commit
        ...
```

---

### 8. **Enhanced Reporting** (Low Priority)
**Current State:** Basic summary output
**Problem:** Need better visibility into rotation progress and results

**Proposed Solution:**
- Detailed progress reporting
- JSON output option for automation
- Summary statistics
- Per-repository status details
- Time tracking

**CLI Options:**
```bash
--output-format <fmt>   # Output format: text, json, markdown (default: text)
--report-file <file>    # Write detailed report to file
--show-stats            # Show detailed statistics
```

**Report Contents:**
- Total repositories processed
- Success/failure counts
- Files modified per repository
- Time taken
- PR URLs created
- Errors encountered
- Recommendations

**JSON Output Example:**
```json
{
  "identifier": "RAW_abc123_def456",
  "timestamp": "2025-12-18...",
  "summary": {
    "total_repositories": 10,
    "completed": 8,
    "failed": 1,
    "skipped": 1,
    "prs_created": 8
  },
  "repositories": [...],
  "duration_seconds": 245.3
}
```

---

### 9. **State File Improvements** (Low Priority)
**Current State:** Basic state tracking
**Problem:** State file could be more useful for tracking and debugging

**Proposed Enhancements:**
- Add timestamps for each operation
- Track retry attempts
- Store error details with context
- Add checksums for verification
- Support state file merging (for parallel operations)

**Enhanced State Structure:**
```json
{
  "identifier": "...",
  "metadata": {
    "created": "2025-12-18...",
    "last_updated": "2025-12-18...",
    "version": "1.0"
  },
  "repositories": [{
    "status": "completed",
    "timestamps": {
      "cloned": "2025-12-18...",
      "branch_created": "2025-12-18...",
      "files_modified": "2025-12-18...",
      "committed": "2025-12-18...",
      "pr_created": "2025-12-18..."
    },
    "retry_count": 0,
    "errors": []
  }]
}
```

---

## Implementation Priority

### Phase 1: Critical Improvements (Immediate)
1. ✅ **Key validation before rotation** - Prevent invalid key failures
2. ✅ **Enhanced error recovery and retry logic** - Handle transient failures

### Phase 2: High-Value Features (Next Sprint)
3. ✅ **Diff viewing and verification (`--verify-changes`)** - Review before committing
4. ✅ **Parallel processing** - Speed up large rotations
5. ✅ **Enhanced reporting** - Better visibility and automation support

### Phase 3: Nice-to-Have (Future)
6. ✅ **Support for multiple secret types** - Extend beyond AWS keys
7. ✅ **Interactive mode** - Selective repository processing
8. ✅ **Rollback functionality** - Undo changes if needed
9. ✅ **State file enhancements** - Better tracking and debugging

---

## Dependencies

### New Dependencies
- **boto3** (optional): For AWS key validation/testing
- **tqdm** (optional): For progress bars in parallel mode

### Installation
```bash
# Install Python dependencies
pip install boto3     # For AWS key validation (optional)
pip install tqdm      # For progress bars (optional)
```

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
- Key validation logic
- Retry logic
- State file serialization

### Integration Tests
- Parallel processing
- Rollback functionality
- Error recovery

### Manual Testing
- Test parallel processing with rate limits
- Test rollback with various failure scenarios
- Test key validation with various formats

---

## Security Considerations

### Key Validation
- Validation should not expose keys
- AWS API testing requires credentials (optional)
- Validate format only by default

### State File
- Continue storing keys as hashes
- Add checksums for verification

---

## Success Criteria

1. ✅ Validates keys before starting rotation
2. ✅ Can view diffs before committing changes
3. ✅ Processes multiple repos in parallel
4. ✅ Handles errors gracefully with retries
5. ✅ Provides detailed reporting
6. ✅ Maintains backward compatibility
7. ✅ All features are well-tested

---

## Open Questions

1. **Parallel Processing**: Threads or processes?
   - **Recommendation**: Threads (I/O bound operations)

2. **Key Validation**: Test with AWS API or format only?
   - **Recommendation**: Format by default, API optional

3. **State File Format**: Version state files?
   - **Recommendation**: Yes, add version field

4. **Rollback**: Automatic or manual?
   - **Recommendation**: Manual with `--rollback` flag

---

## Next Steps

1. Review and prioritize improvements
2. Create implementation plan for Phase 1
3. Update design document with approved changes
4. Begin implementation
5. Update tests and documentation

---

**Document Status:** Draft for Review
**Last Updated:** 2025-12-18
