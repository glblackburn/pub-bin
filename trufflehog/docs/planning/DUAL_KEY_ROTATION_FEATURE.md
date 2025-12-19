# Feature Request: Dual AWS Key Rotation (Access Key + Secret Key)

**Date:** 2025-12-18
**Status:** Planning
**Priority:** High
**Related Script:** `trufflehog/scripts/trufflehog-rotate-aws-key.py`

## Feature Request

### Problem Statement

Currently, `trufflehog-rotate-aws-key.py` only rotates the AWS Access Key ID. However, AWS credentials consist of two parts:
1. **AWS Access Key ID** (e.g., `AKIAIOSFODNN7EXAMPLE`)
2. **AWS Secret Access Key** (e.g., `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)

When rotating AWS credentials, both keys must be replaced simultaneously to maintain functionality. Rotating only the Access Key ID leaves the old Secret Access Key in place, which:
- Creates invalid credential pairs
- Breaks applications that depend on the credentials
- Requires manual intervention to fix
- Defeats the purpose of automated rotation

### Use Case

A user discovers an AWS Access Key ID in a trufflehog scan report. They want to:
1. Generate a new AWS Access Key ID and Secret Access Key pair
2. Replace both the old Access Key ID AND the old Secret Access Key in all repositories
3. Ensure both keys are replaced atomically (together, not separately)
4. Maintain the relationship between Access Key ID and Secret Access Key in the same file/location

### Requirements

1. **Dual Key Replacement:**
   - Replace both Access Key ID and Secret Access Key simultaneously
   - Maintain pairing: new Access Key ID must be paired with new Secret Access Key
   - Both keys must be replaced in the same operation

2. **Key Discovery:**
   - Identify Secret Access Key associated with the Access Key ID being rotated
   - Handle cases where Secret Access Key is in the same file or different location
   - Support various file formats and patterns

3. **Pattern Matching:**
   - Extend current pattern matching to include Secret Access Key patterns
   - Support common formats: environment variables, JSON, YAML, config files
   - Handle both keys in same file or separate files

4. **Backward Compatibility:**
   - Support existing single-key rotation workflow
   - Allow users to opt-in to dual-key rotation
   - Maintain existing CLI interface for single-key operations

5. **Security:**
   - Never log or display Secret Access Keys in output
   - Use secure input methods (getpass) for Secret Access Key entry
   - Store key hashes in state files (not plaintext) - **Rationale:**
     - **State file stores hashes:** Hashes are stored in state file for verification (can verify if key is provided, but cannot be reversed to get the key)
     - **Keys provided at runtime:** Actual key values are provided at runtime (via CLI args, prompt, or environment variable) and used only temporarily for replacements
     - **Hashes used for verification:** When resuming operations, provided keys can be verified against stored hashes to ensure consistency
     - **Plaintext only for replacements:** Plaintext key values are only used temporarily during the replacement operation in source files, never stored
     - **State file is already secured:** State files are stored in `~/.secure/trufflehog-rotate/` with restrictive permissions (600)

## Current Implementation Analysis

### Current Behavior

The script currently:
- Takes a single identifier (TOKEN_* or RAW_*) representing an Access Key ID
- Replaces only the Access Key ID using patterns like:
  - `AWS_ACCESS_KEY_ID=...`
  - `"accessKeyId": "..."`
  - `access_key: ...`
- Does not handle Secret Access Keys at all

### Current Patterns Supported

```python
# From trufflehog-rotate-aws-key.py line ~296-299
patterns = [
    (r'(AWS_ACCESS_KEY_ID\s*[=:]\s*["\']?)' + re.escape(old_key) + r'(["\']?)', ...),
    (r'("accessKeyId"\s*:\s*["\']?)' + re.escape(old_key) + r'(["\']?)', ...),
    (r'("access_key"\s*:\s*["\']?)' + re.escape(old_key) + r'(["\']?)', ...),
    (r'(access_key\s*[=:]\s*["\']?)' + re.escape(old_key) + r'(["\']?)', ...),
]
```

### Limitations

1. **No Secret Key Handling:**
   - Script doesn't look for or replace Secret Access Keys
   - No patterns for `AWS_SECRET_ACCESS_KEY`, `secretAccessKey`, etc.

2. **No Key Pairing:**
   - Doesn't maintain relationship between Access Key ID and Secret Access Key
   - Can't ensure both keys are from the same credential pair

3. **No Discovery Mechanism:**
   - Doesn't attempt to find the Secret Access Key associated with the Access Key ID
   - Relies on user to know where Secret Access Key is located

## Design Options

### Option 1: Automatic Discovery with Pairing (Recommended)

**Approach:** Automatically discover and replace both keys together.

**How It Works:**
1. User provides Access Key ID identifier (as currently)
2. Script searches for associated Secret Access Key in the same file/location
3. User provides new Access Key ID + Secret Access Key pair
4. Script replaces both keys atomically

**Implementation:**
- Add Secret Access Key pattern matching
- Search for Secret Access Key near Access Key ID (same file, nearby lines)
- Replace both keys in single operation
- Validate that both keys are replaced successfully

**Pros:**
- Most user-friendly (automatic discovery)
- Ensures keys stay paired
- Minimal user intervention required
- Handles common cases automatically

**Cons:**
- More complex implementation
- May miss Secret Access Keys in different files
- Requires heuristics for key pairing
- Edge cases where keys are in different locations

**Patterns to Support:**
```python
# Access Key ID patterns (existing)
AWS_ACCESS_KEY_ID=AKIA...
"accessKeyId": "AKIA..."

# Secret Access Key patterns (new)
AWS_SECRET_ACCESS_KEY=wJalr...
"secretAccessKey": "wJalr..."
"secret_key": "wJalr..."
AWS_SECRET_KEY=wJalr...
```

### Option 2: Explicit Dual-Key Mode

**Approach:** Add explicit CLI option for dual-key rotation with user specifying both identifiers.

**How It Works:**
1. User provides two identifiers:
   - Access Key ID identifier (TOKEN_* or RAW_*)
   - Secret Access Key identifier (TOKEN_* or RAW_*)
2. User provides new Access Key ID + Secret Access Key pair
3. Script replaces both keys using their respective identifiers

**Implementation:**
- Add `--secret-identifier` CLI option
- Add `--new-secret-key` or `--prompt-secret` option
- Process both identifiers in same rotation operation
- Replace both keys atomically

**Pros:**
- Explicit control for user
- Works when keys are in different files
- No heuristics needed
- Clear separation of concerns

**Cons:**
- Requires user to know both identifiers
- More complex CLI interface
- User must manually find Secret Access Key identifier
- Less automated than Option 1

**CLI Example:**
```bash
./scripts/trufflehog-rotate-aws-key.py \
    -r report.md \
    -i RAW_abc123_def456 \
    --secret-identifier RAW_xyz789_uvw012 \
    -k AKIANEWKEYEXAMPLE123 \
    --new-secret-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYNEWKEY \
    --mode dry-run
```

### Option 3: Hybrid Approach (Recommended for Flexibility)

**Approach:** Combine automatic discovery with explicit override option.

**How It Works:**
1. By default, attempt automatic discovery (Option 1)
2. If automatic discovery fails or user prefers, allow explicit specification (Option 2)
3. User can opt-in via `--dual-key` flag
4. Falls back to single-key mode if Secret Access Key not found

**Implementation:**
- Add `--dual-key` flag to enable dual-key rotation
- Attempt automatic discovery first
- If discovery fails, prompt user for Secret Access Key identifier
- Support both automatic and explicit modes
- Maintain backward compatibility (single-key mode default)

**Pros:**
- Best of both worlds
- Flexible for different scenarios
- Backward compatible
- User can choose level of automation

**Cons:**
- Most complex implementation
- Requires both discovery and explicit modes
- More code to maintain
- Need to handle fallback scenarios

**CLI Example:**
```bash
# Automatic discovery mode
./scripts/trufflehog-rotate-aws-key.py \
    -r report.md \
    -i RAW_abc123_def456 \
    --dual-key \
    -k AKIANEWKEYEXAMPLE123 \
    --prompt-secret \
    --mode dry-run

# Explicit mode (if auto-discovery fails)
./scripts/trufflehog-rotate-aws-key.py \
    -r report.md \
    -i RAW_abc123_def456 \
    --secret-identifier RAW_xyz789_uvw012 \
    -k AKIANEWKEYEXAMPLE123 \
    --new-secret-key wJalr... \
    --mode dry-run
```

### Option 4: Configuration File Approach

**Approach:** Use configuration file to map Access Key ID to Secret Access Key.

**How It Works:**
1. User creates mapping file: `aws-key-pairs.json`
2. Maps Access Key ID identifiers to Secret Access Key identifiers
3. Script reads mapping and replaces both keys

**Implementation:**
- Add `--key-pair-map` option pointing to JSON file
- JSON format: `{ "RAW_abc123": "RAW_xyz789", ... }`
- Script uses mapping to find Secret Access Key identifier
- Replaces both keys using their identifiers

**Pros:**
- Good for bulk operations
- Reusable mapping file
- Clear separation of key relationships
- Works well for multiple rotations

**Cons:**
- Requires upfront configuration
- Additional file to manage
- Less convenient for one-off rotations
- User must maintain mapping file

**Configuration File Format:**
```json
{
  "RAW_abc123_def456": "RAW_xyz789_uvw012",
  "TOKEN_a1b2c3d4_e5f6g7h8": "TOKEN_i9j0k1l2_m3n4o5p6"
}
```

## Recommended Design: Option 3 (Hybrid Approach)

### Rationale

Option 3 provides the best balance of:
- **Automation:** Handles common cases automatically
- **Flexibility:** Allows explicit control when needed
- **Backward Compatibility:** Doesn't break existing workflows
- **User Experience:** Progressive enhancement (try automatic, fall back to explicit)

### Implementation Plan

#### Phase 1: Core Dual-Key Support
1. Add Secret Access Key pattern matching
2. Add `--dual-key` flag
3. Add `--new-secret-key` and `--prompt-secret` options
4. Extend `replace_key_in_file()` to handle both keys
5. Update state file format to store both key hashes (see Security section for rationale)

#### Phase 2: Automatic Discovery
1. Implement discovery function to find Secret Access Key near Access Key ID
2. Search same file, nearby lines (within N lines of Access Key ID)
3. Match common patterns (AWS_SECRET_ACCESS_KEY, secretAccessKey, etc.)
4. Validate pairing (both keys found in same context)

#### Phase 3: Explicit Mode
1. Add `--secret-identifier` option
2. Support processing two identifiers in same operation
3. Validate both identifiers exist in report
4. Replace both keys atomically

#### Phase 4: Enhanced Features
1. Add validation: ensure both keys replaced successfully
2. Add rollback capability if one key replacement fails
3. Support configuration file approach (Option 4) as alternative
4. Update documentation and examples

### Key Implementation Details

#### Pattern Matching Extension

```python
# Access Key ID patterns (existing)
ACCESS_KEY_PATTERNS = [
    r'(AWS_ACCESS_KEY_ID\s*[=:]\s*["\']?)',
    r'("accessKeyId"\s*:\s*["\']?)',
    r'("access_key"\s*:\s*["\']?)',
    r'(access_key\s*[=:]\s*["\']?)',
]

# Secret Access Key patterns (new)
SECRET_KEY_PATTERNS = [
    r'(AWS_SECRET_ACCESS_KEY\s*[=:]\s*["\']?)',
    r'("secretAccessKey"\s*:\s*["\']?)',
    r'("secret_key"\s*:\s*["\']?)',
    r'(secret_key\s*[=:]\s*["\']?)',
    r'(AWS_SECRET_KEY\s*[=:]\s*["\']?)',
]
```

#### Discovery Algorithm

```python
def find_secret_key_near_access_key(file_path: Path, access_key_line: int,
                                     access_key_id: str) -> Optional[Tuple[int, str]]:
    """
    Find Secret Access Key near Access Key ID in same file.
    Returns: (line_number, secret_key_value) or None
    """
    # Search within N lines of Access Key ID (e.g., ±50 lines)
    # Match Secret Access Key patterns
    # Return first match found
    pass
```

#### State File Extension

**Security Note:** Key hashes are stored in state files (not plaintext keys). This follows the current implementation pattern:

- **State file stores hashes:** Hashes (`old_key_hash`, `new_key_hash`, `old_secret_key_hash`, `new_secret_key_hash`) are stored in state file
- **Hashes for verification:** Hashes can verify if a key is provided (cannot be reversed to get the key)
- **Keys provided at runtime:** Actual key values are provided at runtime via CLI args (`-k`, `--new-secret-key`), prompt (`-p`, `--prompt-secret`), or environment variables
- **Plaintext only for replacements:** Plaintext key values are used temporarily during replacement operations in source files, never stored
- **Resume verification:** When resuming operations, provided keys can be verified against stored hashes to ensure consistency
- **Protection:** State files stored in `~/.secure/trufflehog-rotate/` with restrictive permissions (600)

**Implementation Note:** This matches the current implementation which stores `old_key_hash` and `new_key_hash`. For dual-key rotation, we'll extend this to also store `old_secret_key_hash` and `new_secret_key_hash`.

```python
# Current state file format
{
    "identifier": "RAW_abc123_def456",
    "old_key_hash": "sha256:...",  # hash of old access key
    "new_key_hash": "sha256:...",  # hash of new access key
    ...
}

# Extended format for dual-key
{
    "identifier": "RAW_abc123_def456",
    "old_key_hash": "sha256:...",  # hash of old access key
    "new_key_hash": "sha256:...",  # hash of new access key
    "secret_identifier": "RAW_xyz789_uvw012",  # optional
    "old_secret_key_hash": "sha256:...",  # hash of old secret key
    "new_secret_key_hash": "sha256:...",  # hash of new secret key
    "dual_key_mode": true,
    ...
}

# Note: Actual key values are provided at runtime (via CLI args, prompt, or env vars)
# and used only temporarily for replacements. They are never stored in the state file.
```

## Security Considerations

### Key Storage in State Files

**Decision:** Store key hashes in state files (not plaintext keys).

**How It Works:**

1. **State File Stores Hashes:**
   - State file stores SHA256 hashes of keys: `old_key_hash`, `new_key_hash`, `old_secret_key_hash`, `new_secret_key_hash`
   - Hashes cannot be reversed to get the original key
   - Hashes can verify if a provided key matches (hash the provided key and compare)

2. **Keys Provided at Runtime:**
   - Actual key values are provided at runtime via:
     - CLI arguments: `-k`, `--new-key`, `--new-secret-key`
     - Interactive prompts: `-p`, `--prompt-key`, `--prompt-secret`
     - Environment variables: `TRUFFLEHOG_NEW_AWS_KEY`, `TRUFFLEHOG_NEW_AWS_SECRET_KEY`
   - Keys are used temporarily during replacement operations
   - Keys are never stored in state files

3. **Resume Mode Verification:**
   - When resuming operations, if keys are provided, they are hashed and compared to stored hashes
   - This ensures consistency: the same keys are being used across operations
   - If hashes don't match, a warning is issued (but operation may continue)

4. **Replacement Operations:**
   - Plaintext key values are used temporarily to perform pattern matching and replacements in source files
   - Keys are only in memory during the replacement operation
   - Keys are never written to state files, logs, or output

**Security Measures:**
- ✅ Keys are never logged or displayed in output
- ✅ Secret Access Keys use secure input methods (getpass) for entry
- ✅ State files store only hashes (cannot be reversed)
- ✅ State files stored in secure directory with restrictive permissions (600)
- ✅ State files only readable/writable by owner
- ✅ No keys in commit messages or verbose output
- ✅ Keys only exist in memory during replacement operations

**Note:** This approach follows the current implementation pattern and provides security through hashing while maintaining the ability to verify key consistency across operations.

## Open Questions

1. **Discovery Range:** How many lines away should we search for Secret Access Key? (Recommendation: ±50 lines)

2. **Multiple Matches:** What if multiple Secret Access Keys are found near Access Key ID? (Recommendation: Use first match, warn user)

3. **Different Files:** Should we search in other files in the same repository? (Recommendation: Start with same file only, expand later)

4. **Key Validation:** Should we validate that Access Key ID and Secret Access Key are a valid pair? (Recommendation: No - AWS doesn't provide API for this, would require AWS SDK)

5. **Backward Compatibility:** Should `--dual-key` be opt-in or default? (Recommendation: Opt-in via flag, maintain single-key as default)

6. **Error Handling:** What if Access Key ID is replaced but Secret Access Key replacement fails? (Recommendation: Rollback Access Key ID replacement, or mark as partial failure)

## Success Criteria

1. ✅ Both Access Key ID and Secret Access Key can be replaced in single operation
2. ✅ Automatic discovery works for common file formats (env vars, JSON, YAML)
3. ✅ Explicit mode works when keys are in different files
4. ✅ Backward compatibility maintained (single-key mode still works)
5. ✅ Security: Secret Access Keys never logged or displayed
6. ✅ State file properly stores both key hashes (see Security section for details)
7. ✅ Documentation updated with examples

## Related Documentation

- `trufflehog/scripts/trufflehog-rotate-aws-key.py` - Current implementation
- `trufflehog/docs/design/trufflehog-rotate-aws-key-design.md` - Original design document
- `trufflehog/docs/design/trufflehog-rotate-aws-key-other-improvements.md` - Other improvements (mentions key validation)

## Next Steps

1. Review and approve design option
2. Create detailed implementation plan
3. Implement Phase 1 (core dual-key support)
4. Test with real repositories
5. Iterate based on feedback

---

**Created:** 2025-12-18
**Author:** AI Assistant
**Status:** Awaiting Review
