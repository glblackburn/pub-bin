# Feature Request: Paired Secret Rotation (Dual Secret Rotation)

**Date:** 2025-12-18
**Last Updated:** 2025-12-24
**Status:** Design Validated - Ready for Implementation
**Priority:** High
**Related Script:** `trufflehog/scripts/trufflehog-rotate-aws-key.py`

## Overview

This feature enables rotation of **paired secrets** - secrets that must be rotated together to maintain functionality. While the initial implementation focuses on **AWS Access Key ID + Secret Access Key** pairs, the design is extensible to support other paired secret types such as:

- Username/Password pairs
- API Key/Secret pairs
- OAuth Client ID/Secret pairs
- Database credentials
- Custom paired secrets

**Key Design Principle:** The script works with any secret type discovered by trufflehog. Paired secret rotation is a general capability, with AWS credentials as the primary use case and example.

## Table of Contents

- [Feature Request](#feature-request)
  - [Problem Statement](#problem-statement)
  - [Use Case](#use-case)
  - [Requirements](#requirements)
- [Current Implementation Analysis](#current-implementation-analysis)
  - [Current Behavior](#current-behavior)
  - [Current Patterns Supported](#current-patterns-supported)
  - [Limitations](#limitations)
- [Selected Design: Hybrid Approach](#selected-design-hybrid-approach)
  - [Design Scope and Extensibility](#design-scope-and-extensibility)
  - [Rationale](#rationale)
  - [Design Review and Validation](#design-review-and-validation)
  - [Implementation Plan](#implementation-plan)
    - [Phase 1: Core Paired Secret Support + Explicit Mode (AWS Focus)](#phase-1-core-paired-secret-support--explicit-mode-aws-focus)
    - [Phase 2: Automatic Discovery (AWS Focus)](#phase-2-automatic-discovery-aws-focus)
    - [Phase 3: Enhanced Discovery and Extensibility (Future)](#phase-3-enhanced-discovery-and-extensibility-future)
    - [Phase 4: Enhanced Features and Validation](#phase-4-enhanced-features-and-validation)
  - [Key Implementation Details](#key-implementation-details)
    - [Pattern Matching Extension](#pattern-matching-extension)
    - [Discovery Algorithm](#discovery-algorithm)
    - [State File Extension](#state-file-extension)
- [Security Considerations](#security-considerations)
  - [Key Storage in State Files](#key-storage-in-state-files)
- [Design Decisions and Specifications](#design-decisions-and-specifications)
  - [Discovery Range](#discovery-range)
  - [Multiple Matches Handling](#multiple-matches-handling)
  - [Cross-File Discovery](#cross-file-discovery)
  - [Key Validation](#key-validation)
  - [Backward Compatibility](#backward-compatibility)
    - [CLI Interface Compatibility](#cli-interface-compatibility)
    - [State File Compatibility](#state-file-compatibility)
    - [Behavior Compatibility](#behavior-compatibility)
    - [Migration Path](#migration-path)
    - [Examples of Unchanged Behavior](#examples-of-unchanged-behavior)
    - [Compatibility Guarantees](#compatibility-guarantees)
  - [Error Handling Strategy](#error-handling-strategy)
- [Success Criteria](#success-criteria)
- [Related Documentation](#related-documentation)
- [Implementation Approach](#implementation-approach)
  - [Development Strategy](#development-strategy)
  - [Code Organization](#code-organization)
- [Next Steps](#next-steps)
- [Appendix: Alternative Design Options](#appendix-alternative-design-options)
  - [Option 1: Automatic Discovery with Pairing](#option-1-automatic-discovery-with-pairing)
  - [Option 2: Explicit Dual-Key Mode](#option-2-explicit-dual-key-mode)
  - [Option 4: Configuration File Approach](#option-4-configuration-file-approach)

## Feature Request

### Problem Statement

Currently, `trufflehog-rotate-aws-key.py` only rotates a single secret at a time. However, many secrets are part of **paired secret systems** where two secrets must be rotated together to maintain functionality:

**Examples of Paired Secrets:**
1. **AWS Credentials:**
   - AWS Access Key ID (e.g., `AKIAIOSFODNN7EXAMPLE`)
   - AWS Secret Access Key (e.g., `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)

2. **Username/Password:**
   - Username (e.g., `admin`, `service-account`)
   - Password (e.g., `P@ssw0rd123!`)

3. **API Key Pairs:**
   - API Key (e.g., `api_key_abc123`)
   - API Secret (e.g., `secret_xyz789`)

4. **OAuth Credentials:**
   - Client ID (e.g., `client_12345`)
   - Client Secret (e.g., `secret_67890`)

5. **Database Credentials:**
   - Database Username (e.g., `db_user`)
   - Database Password (e.g., `db_pass`)

When rotating paired secrets, both secrets must be replaced simultaneously. Rotating only one secret leaves the old paired secret in place, which:
- Creates invalid credential pairs
- Breaks applications that depend on the credentials
- Requires manual intervention to fix
- Defeats the purpose of automated rotation

**Note:** While this feature is designed to work with any secret type discovered by trufflehog, AWS credentials are the primary use case and will be the initial implementation focus. The design is extensible to support other paired secret types.

### Use Case

A user discovers a secret in a trufflehog scan report that is part of a paired secret system. They want to:
1. Generate a new pair of secrets (e.g., new AWS Access Key ID and Secret Access Key)
2. Replace both the old primary secret AND the old paired secret in all repositories
3. Ensure both secrets are replaced atomically (together, not separately)
4. Maintain the relationship between primary and paired secrets in the same file/location

**Primary Example - AWS Credentials:**
- User discovers AWS Access Key ID in trufflehog report
- User wants to rotate both Access Key ID and Secret Access Key together
- Both must be replaced atomically to maintain valid credential pairs

**Future Examples:**
- Username/Password pairs discovered in reports
- API Key/Secret pairs that need coordinated rotation
- OAuth Client ID/Secret pairs

### Requirements

1. **Paired Secret Replacement:**
   - Replace both primary secret and paired secret simultaneously
   - Maintain pairing: new primary secret must be paired with new paired secret
   - Both secrets must be replaced in the same operation
   - Support any secret type discovered by trufflehog (not limited to AWS keys)

2. **Secret Discovery:**
   - Identify paired secret associated with the primary secret being rotated
   - Handle cases where paired secret is in the same file or different location
   - Support various file formats and patterns
   - Extensible to different secret types (AWS keys, username/password, API keys, etc.)

3. **Pattern Matching:**
   - Extensible pattern matching system for different secret types
   - Initial implementation: AWS Access Key ID + Secret Access Key patterns
   - Support common formats: environment variables, JSON, YAML, config files
   - Handle both secrets in same file or separate files
   - Future: Configurable patterns for other secret types (username/password, API keys, etc.)

4. **Backward Compatibility:**
   - Support existing single-secret rotation workflow
   - Allow users to opt-in to paired-secret rotation
   - Maintain existing CLI interface for single-secret operations
   - Existing scripts and workflows continue to work unchanged

5. **Extensibility:**
   - Design supports multiple secret types (not just AWS keys)
   - Pattern matching system can be extended for new secret types
   - Secret type detection from trufflehog detector information
   - Future: Configurable secret type definitions and patterns

6. **Security:**
   - Never log or display paired secrets in output
   - Use secure input methods (getpass) for secret entry
   - Store secret hashes in state files (not plaintext) - **Rationale:**
     - **State file stores hashes:** Hashes are stored in state file for verification (can verify if secret is provided, but cannot be reversed to get the secret)
     - **Secrets provided at runtime:** Actual secret values are provided at runtime (via CLI args, prompt, or environment variable) and used only temporarily for replacements
     - **Hashes used for verification:** When resuming operations, provided secrets can be verified against stored hashes to ensure consistency
     - **Plaintext only for replacements:** Plaintext secret values are only used temporarily during the replacement operation in source files, never stored
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

## Selected Design: Hybrid Approach

**Status:** ✅ **SELECTED** - This design has been chosen for implementation.

The Hybrid Approach combines automatic discovery with explicit override option, providing the best balance of automation, flexibility, and backward compatibility.

**Approach:** Combine automatic discovery with explicit override option.

**How It Works:**
1. By default, attempt automatic discovery
2. If automatic discovery fails or user prefers, allow explicit specification
3. User can opt-in via `--paired-secret` flag (aliased as `--dual-key` for AWS)
4. Falls back to single-secret mode if paired secret not found

**Implementation:**
- Add `--paired-secret` flag to enable paired secret rotation (aliased as `--dual-key` for AWS)
- Attempt automatic discovery first
- If discovery fails, prompt user for paired secret identifier
- Support both automatic and explicit modes
- Maintain backward compatibility (single-secret mode default)

**Pros:**
- Best of both worlds
- Flexible for different scenarios
- Backward compatible
- User can choose level of automation
- Future-proof (can add more discovery strategies)

**Cons:**
- More complex implementation (but manageable)
- Requires both discovery and explicit modes
- More code to maintain (but well-structured)
- Need to handle fallback scenarios

**CLI Example:**
```bash
# Automatic discovery mode
./scripts/trufflehog-rotate-aws-key.py \
    -r report.md \
    -i RAW_abc123_def456 \
    --paired-secret \
    -k AKIANEWKEYEXAMPLE123 \
    --prompt-paired-secret \
    --mode dry-run

# Explicit mode (if auto-discovery fails or user prefers)
./scripts/trufflehog-rotate-aws-key.py \
    -r report.md \
    -i RAW_abc123_def456 \
    --paired-secret \
    --paired-secret-identifier RAW_xyz789_uvw012 \
    -k AKIANEWKEYEXAMPLE123 \
    --new-paired-secret wJalrXUtnFEMI/K7MDENG/bPxRfiCYNEWKEY \
    --mode dry-run

# If automatic discovery fails, script will prompt:
# "Paired secret not found automatically. Provide identifier manually (--paired-secret-identifier) or run with --paired-secret-identifier to skip discovery."
```

### Design Scope and Extensibility

#### Current Focus: AWS Credentials

The initial implementation focuses on **AWS Access Key ID + Secret Access Key** rotation as the primary use case. This provides:
- Clear, well-defined patterns
- Common real-world use case
- Validation of the paired secret concept

#### Future Extensibility: Other Secret Types

The design is structured to support other paired secret types in the future:

**Potential Extensions:**
- **Username/Password pairs:** Rotate both username and password together
- **API Key/Secret pairs:** Rotate API key and corresponding secret
- **OAuth Client ID/Secret:** Rotate OAuth credentials together
- **Database credentials:** Rotate database username and password
- **Custom paired secrets:** User-defined secret pairs

**Extensibility Mechanisms:**
- Configurable pattern matching per secret type
- Secret type detection from trufflehog detector information
- Pluggable pattern definitions
- Secret type-specific validation rules

**Implementation Strategy:**
- Phase 1: AWS credentials (Access Key ID + Secret Access Key)
- Phase 2: Automatic discovery for AWS credentials
- Phase 3+: Extend to other secret types based on demand

### Rationale

The Hybrid Approach provides the best balance of:
- **Automation:** Handles common cases automatically
- **Flexibility:** Allows explicit control when needed
- **Backward Compatibility:** Doesn't break existing workflows
- **User Experience:** Progressive enhancement (try automatic, fall back to explicit)

### Design Review and Validation

**Review Date:** 2025-12-24
**Status:** Design Validated - Ready for Implementation

After comprehensive review of the design document and current implementation, the Hybrid Approach has been selected for implementation. The following analysis validates this choice:

#### Option Comparison: Option 1 vs Option 3

**Option 1: Automatic Discovery with Pairing**

**Strengths:**
- ✅ Most user-friendly - zero manual configuration for common cases
- ✅ Handles 80-90% of real-world scenarios automatically
- ✅ Simplest user experience
- ✅ Minimal CLI changes

**Weaknesses:**
- ❌ Cannot handle keys in different files (common in some architectures)
- ❌ No fallback when discovery fails
- ❌ May have false positives (matching wrong secret key)
- ❌ Limited to same-file discovery only

**Real-World Scenarios:**
- ✅ **Works well:** `.env` files, JSON configs, YAML files (keys together)
- ❌ **Fails:** Keys in separate files (e.g., `config/access-key.txt` and `config/secret-key.txt`)
- ❌ **Fails:** Keys in different directories
- ❌ **Fails:** Keys managed by different systems

**Option 3: Hybrid Approach**

**Strengths:**
- ✅ Handles both automatic discovery AND explicit specification
- ✅ Progressive enhancement: try automatic, fall back to explicit
- ✅ Works for all scenarios (same file, different files, different repos)
- ✅ Backward compatible (opt-in via `--dual-key` flag)
- ✅ Future-proof (can add more discovery strategies later)

**Weaknesses:**
- ⚠️ More complex implementation (but manageable)
- ⚠️ Requires both discovery and explicit modes
- ⚠️ More code to maintain (but well-structured)

**Real-World Scenarios:**
- ✅ **Works:** All scenarios from Option 1
- ✅ **Also works:** Keys in different files (via `--secret-identifier`)
- ✅ **Also works:** Keys in different directories
- ✅ **Also works:** Complex architectures

#### Why Option 3 is Recommended

1. **Future-Proof:** Option 3 can evolve to support more discovery strategies (cross-file, cross-repo, etc.) without breaking existing workflows.

2. **User Experience:** Most users get automatic discovery (like Option 1), but power users can override when needed.

3. **Real-World Coverage:** Handles edge cases that Option 1 cannot, which are common in enterprise environments.

4. **Implementation Complexity:** The added complexity is justified by the flexibility gained. The code can be structured to keep discovery and explicit modes separate.

5. **Backward Compatibility:** Opt-in via `--dual-key` flag means existing scripts continue to work unchanged.

### Implementation Plan

#### Phase 1: Core Paired Secret Support + Explicit Mode (AWS Focus)
1. Add paired secret pattern matching (AWS Secret Access Key patterns for initial implementation)
2. Add `--paired-secret` flag (opt-in, aliased as `--dual-key` for AWS backward compatibility)
3. Add `--new-paired-secret` and `--prompt-paired-secret` options (aliased as `--new-secret-key` and `--prompt-secret` for AWS)
4. Add `--paired-secret-identifier` option (explicit mode, aliased as `--secret-identifier` for AWS)
5. Extend `replace_key_in_file()` to handle both secrets atomically
6. Update state file format to store both secret hashes and discovery method (see Security section for rationale)
7. Implement error handling: rollback on partial failure (atomic operation)
8. Detect secret type from trufflehog detector information (prepare for future extensibility)

**Rationale:** Explicit mode is simpler to implement than discovery and provides immediate value. Users can use it from day one, and it serves as a fallback when discovery is added later. Initial implementation focuses on AWS credentials, but structure supports future secret types.

**Why include explicit mode in Phase 1?**
- Explicit mode is simpler to implement than discovery
- Users can use it immediately if discovery fails
- Provides immediate value for edge cases
- Discovery can be added incrementally

#### Phase 2: Automatic Discovery (AWS Focus)
1. Implement discovery function to find paired secret near primary secret
2. Search same file, nearby lines (within ±50 lines of primary secret - default, configurable)
3. Match common patterns (AWS_SECRET_ACCESS_KEY, secretAccessKey, etc. for AWS)
4. Validate pairing (both secrets found in same context)
5. Fallback to explicit mode if discovery fails (prompt user for `--paired-secret-identifier`)
6. Use trufflehog detector information to determine secret type and appropriate patterns

#### Phase 3: Enhanced Discovery and Extensibility (Future)
1. Cross-file discovery (search other files in same directory)
2. Configuration file support (Option 4)
3. Multiple match handling with user selection
4. Discovery strategy selection (same-file, cross-file, config-file)
5. **Extend to other secret types:**
   - Username/Password pairs
   - API Key/Secret pairs
   - OAuth Client ID/Secret pairs
   - Configurable pattern definitions for custom secret types

#### Phase 4: Enhanced Features and Validation
1. Add validation: ensure both keys replaced successfully
2. Enhanced error messages and user feedback
3. Support configuration file approach (Option 4) as alternative
4. Multiple match handling with user selection
5. Update documentation and examples

### Key Implementation Details

#### Pattern Matching Extension

**Initial Implementation (AWS Credentials):**

```python
# Primary secret patterns (AWS Access Key ID - existing)
AWS_ACCESS_KEY_PATTERNS = [
    r'(AWS_ACCESS_KEY_ID\s*[=:]\s*["\']?)',
    r'("accessKeyId"\s*:\s*["\']?)',
    r'("access_key"\s*:\s*["\']?)',
    r'(access_key\s*[=:]\s*["\']?)',
]

# Paired secret patterns (AWS Secret Access Key - new)
AWS_SECRET_KEY_PATTERNS = [
    r'(AWS_SECRET_ACCESS_KEY\s*[=:]\s*["\']?)',
    r'("secretAccessKey"\s*:\s*["\']?)',
    r'("secret_key"\s*:\s*["\']?)',
    r'(secret_key\s*[=:]\s*["\']?)',
    r'(AWS_SECRET_KEY\s*[=:]\s*["\']?)',
]
```

**Future Extensibility (Other Secret Types):**

```python
# Pattern definitions by secret type (future)
SECRET_PATTERNS = {
    'aws': {
        'primary': AWS_ACCESS_KEY_PATTERNS,
        'paired': AWS_SECRET_KEY_PATTERNS,
    },
    'username_password': {
        'primary': [
            r'(USERNAME\s*[=:]\s*["\']?)',
            r'("username"\s*:\s*["\']?)',
            r'(user\s*[=:]\s*["\']?)',
        ],
        'paired': [
            r'(PASSWORD\s*[=:]\s*["\']?)',
            r'("password"\s*:\s*["\']?)',
            r'(pass\s*[=:]\s*["\']?)',
        ],
    },
    'api_key_secret': {
        'primary': [
            r'(API_KEY\s*[=:]\s*["\']?)',
            r'("apiKey"\s*:\s*["\']?)',
        ],
        'paired': [
            r'(API_SECRET\s*[=:]\s*["\']?)',
            r'("apiSecret"\s*:\s*["\']?)',
        ],
    },
    # Future: Add more secret types as needed
}
```

#### Discovery Algorithm

```python
def find_paired_secret_near_primary(
    file_path: Path,
    primary_secret_line: int,
    primary_secret_value: str,
    secret_type: str = 'aws',  # Future: Support multiple types
    search_range: int = 50
) -> Optional[Tuple[int, str, str]]:
    """
    Find paired secret near primary secret in same file.

    Args:
        file_path: Path to file containing primary secret
        primary_secret_line: Line number where primary secret was found
        primary_secret_value: The primary secret value (for context validation)
        secret_type: Type of secret pair ('aws', 'username_password', etc.)
        search_range: Number of lines to search before/after (default: 50)

    Returns:
        (line_number, paired_secret_value, pattern_matched) or None

    Strategy:
        1. Determine paired secret patterns based on secret_type
        2. Read file and extract lines [primary_secret_line - search_range : primary_secret_line + search_range]
        3. Match against paired secret patterns for the secret type
        4. Return first match found (closest to primary_secret_line preferred)
        5. If multiple matches, prefer the one closest to primary_secret_line

    Future: Support multiple secret types via pattern registry
    """
    # Get patterns for this secret type
    patterns = SECRET_PATTERNS.get(secret_type, {}).get('paired', [])
    # ... implementation ...
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

# Extended format for paired secrets
{
    "identifier": "RAW_abc123_def456",
    "old_key_hash": "sha256:...",  # hash of old primary secret
    "new_key_hash": "sha256:...",  # hash of new primary secret
    "paired_secret_mode": true,  # Indicates paired secret rotation
    "secret_type": "aws",  # Type of secret pair (aws, username_password, etc.)
    "secret_discovery_method": "automatic" | "explicit" | null,  # How paired secret was found
    "paired_secret_identifier": "RAW_xyz789_uvw012",  # Only if explicit mode was used
    "old_paired_secret_hash": "sha256:...",  # hash of old paired secret
    "new_paired_secret_hash": "sha256:...",  # hash of new paired secret
    ...
}

# Note: "dual_key_mode" is aliased for backward compatibility with AWS-focused naming
# Both "paired_secret_mode" and "dual_key_mode" are supported

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

## Design Decisions and Specifications

### Discovery Range

**Decision:** ±50 lines (default, configurable via `--discovery-range` option in future)

The discovery algorithm searches within 50 lines before and after the Access Key ID location. This range:
- Covers most common file formats where keys are adjacent or nearby
- Balances thoroughness with performance
- Can be configured for edge cases requiring larger search ranges

### Multiple Matches Handling

**Decision:** Use first match found (closest to Access Key ID preferred), warn user

If multiple Secret Access Keys are found near the Access Key ID:
1. Prefer the match closest to the Access Key ID line number
2. Warn the user that multiple matches were found
3. Allow user to override with explicit mode (`--secret-identifier`) if needed

### Cross-File Discovery

**Decision:** Start with same file only, expand later (Phase 3)

Initial implementation focuses on same-file discovery for:
- Simplicity and reliability
- Most common use case (keys in same file)
- Easier validation and testing

Cross-file discovery will be added in Phase 3 as an enhancement.

### Key Validation

**Decision:** No AWS API validation (format validation only)

- AWS doesn't provide a public API to validate key pairs
- Would require AWS SDK and credentials (adds complexity)
- Format validation is sufficient (Access Key ID starts with `AKIA`, Secret Key is 40 characters)
- Users are responsible for ensuring keys are valid pairs

### Backward Compatibility

**Decision:** Opt-in via `--dual-key` flag, maintain single-key as default

Backward compatibility is maintained through an opt-in design where single-key rotation remains the default behavior. This ensures all existing scripts, workflows, and state files continue to work without modification.

#### CLI Interface Compatibility

**All existing CLI arguments remain unchanged and functional:**

```bash
# Existing single-key command - works exactly as before
./trufflehog-rotate-aws-key.py \
    -r report.md \
    -i RAW_abc123_def456 \
    -k AKIANEWKEYEXAMPLE123 \
    --mode dry-run

# All existing options still work:
# -r, --report          (unchanged)
# -i, --identifier      (unchanged)
# -k, --new-key         (unchanged)
# -p, --prompt-key      (unchanged)
# --mode                (unchanged)
# --resume              (unchanged)
# --state-file          (unchanged)
# --push, --create-pr   (unchanged)
# All other options     (unchanged)
```

**New options are additive only:**
- `--dual-key` - Opt-in flag to enable dual-key rotation
- `--new-secret-key` - Only used when `--dual-key` is specified
- `--prompt-secret` - Only used when `--dual-key` is specified
- `--secret-identifier` - Only used when `--dual-key` is specified

**No breaking changes:**
- No existing arguments are removed or changed
- No existing arguments have different behavior in single-key mode
- Default behavior (without `--dual-key`) is identical to current implementation

#### State File Compatibility

**Single-key state files continue to work:**

```json
// Existing state file format - fully supported
{
    "identifier": "RAW_abc123_def456",
    "old_key_hash": "sha256:...",
    "new_key_hash": "sha256:...",
    "timestamp": "2025-12-24T10:00:00",
    "mode": "dry-run",
    "repositories": [...]
}
```

**Dual-key state files are extensions:**

```json
// New dual-key state file format - extends existing format
{
    "identifier": "RAW_abc123_def456",
    "old_key_hash": "sha256:...",
    "new_key_hash": "sha256:...",
    "dual_key_mode": true,                    // NEW: Indicates dual-key mode
    "secret_discovery_method": "explicit",    // NEW: How secret was found
    "secret_identifier": "RAW_xyz789_uvw012", // NEW: Only if explicit mode
    "old_secret_key_hash": "sha256:...",      // NEW: Secret key hash
    "new_secret_key_hash": "sha256:...",      // NEW: Secret key hash
    "timestamp": "2025-12-24T10:00:00",
    "mode": "dry-run",
    "repositories": [...]
}
```

**Resume mode compatibility:**
- Single-key state files can be resumed with single-key mode (unchanged behavior)
- Dual-key state files can be resumed with dual-key mode (new behavior)
- Mixed mode resumption:
  - Resuming dual-key state with single-key mode: **Warning** issued, continues with single-key only
  - Resuming single-key state with dual-key mode: **Error** - incompatible modes

#### Behavior Compatibility

**Single-key mode behavior (default, without `--dual-key`):**
- ✅ Rotates only Access Key ID (exactly as current implementation)
- ✅ Uses same pattern matching for Access Key ID
- ✅ Creates same branch names
- ✅ Uses same commit messages (unless custom)
- ✅ Same error handling and reporting
- ✅ Same state file structure (no dual-key fields)
- ✅ Same resume behavior

**Dual-key mode behavior (opt-in with `--dual-key`):**
- ✅ Rotates both Access Key ID and Secret Access Key
- ✅ Uses extended pattern matching (includes Secret Access Key patterns)
- ✅ Creates same branch names (no change)
- ✅ Uses same commit messages (unless custom)
- ✅ Enhanced error handling (atomic rollback)
- ✅ Extended state file structure (includes dual-key fields)
- ✅ Enhanced resume behavior (validates dual-key state)

#### Migration Path

**For users who want to adopt dual-key rotation:**

1. **No immediate action required:**
   - Existing scripts continue to work unchanged
   - No need to update existing workflows
   - No need to migrate state files

2. **Opt-in when ready:**
   ```bash
   # Add --dual-key flag to existing command
   ./trufflehog-rotate-aws-key.py \
       -r report.md \
       -i RAW_abc123_def456 \
       --dual-key \          # NEW: Add this flag
       -k AKIANEWKEYEXAMPLE123 \
       --prompt-secret \     # NEW: Prompt for secret key
       --mode dry-run
   ```

3. **Gradual adoption:**
   - Can use single-key mode for some rotations
   - Can use dual-key mode for others
   - Mix and match based on needs
   - No forced migration

4. **State file migration:**
   - Single-key state files remain valid
   - New dual-key operations create new state files
   - Can resume old single-key operations with single-key mode
   - No need to convert existing state files

#### Examples of Unchanged Behavior

**Example 1: Existing script continues to work:**
```bash
# This exact command works identically before and after dual-key feature
./trufflehog-rotate-aws-key.py \
    -r report.md \
    -i RAW_abc123_def456 \
    -k AKIANEWKEYEXAMPLE123 \
    --mode commit \
    --push \
    --create-pr
```

**Example 2: Resume existing single-key operation:**
```bash
# Resuming a single-key rotation from before dual-key feature
./trufflehog-rotate-aws-key.py \
    --resume \
    -i RAW_abc123_def456 \
    --push
# Works exactly as before - no dual-key fields in state file, no errors
```

**Example 3: Mixed usage:**
```bash
# Use single-key for one rotation
./trufflehog-rotate-aws-key.py -r report1.md -i RAW_abc123 -k NEWKEY1 --mode commit

# Use dual-key for another rotation
./trufflehog-rotate-aws-key.py -r report2.md -i RAW_def456 --dual-key -k NEWKEY2 --prompt-secret --mode commit

# Both work independently - no conflicts
```

#### Compatibility Guarantees

**Guaranteed compatibility:**
- ✅ All existing CLI commands work without modification
- ✅ All existing state files can be resumed
- ✅ All existing workflows continue to function
- ✅ No breaking changes to API or behavior
- ✅ No required migration or updates

**What changes only when `--dual-key` is used:**
- Pattern matching includes Secret Access Key patterns
- Replacement logic handles both keys atomically
- State file includes dual-key fields
- Error handling includes rollback for partial failures
- Resume mode validates dual-key state compatibility

**Summary:**
- **Default behavior:** Identical to current implementation (single-key only)
- **Opt-in enhancement:** Dual-key rotation requires explicit `--dual-key` flag
- **Zero breaking changes:** All existing code and workflows continue to work
- **Clear migration path:** Users can adopt dual-key rotation when ready, at their own pace

### Error Handling Strategy

**Decision:** Atomic operation with rollback

**Atomic Replacement:**
- Both keys must be replaced in the same file operation
- If Access Key ID replacement succeeds but Secret Access Key fails: **Rollback Access Key ID** (restore original file)
- If both fail: Mark as failed, don't commit
- State file tracks: `replacement_status: "both_succeeded" | "access_only" | "failed" | "rolled_back"`

**Resume Mode Compatibility:**
- If resuming with `--dual-key` but state file has single-key mode: Warn and continue with single-key
- If resuming with single-key but state file has dual-key mode: Error (incompatible modes)
- State file must match the operation mode being resumed

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

## Implementation Approach

### Development Strategy

This approach provides:
- ✅ **Immediate value:** Explicit mode works from day one (Phase 1)
- ✅ **Progressive enhancement:** Automatic discovery added later (Phase 2)
- ✅ **Full coverage:** Handles all scenarios (same file, different files, different repos)
- ✅ **Backward compatibility:** Opt-in flag means existing scripts continue to work
- ✅ **Maintainable code:** Clear separation of concerns between discovery and explicit modes

### Code Organization

The implementation will maintain clear separation:
- **Discovery module:** Handles automatic Secret Access Key discovery
- **Explicit module:** Handles user-specified Secret Access Key identifiers
- **Replacement module:** Handles atomic dual-key replacement
- **State management:** Tracks discovery method and key hashes

This structure allows:
- Independent testing of each module
- Easy addition of new discovery strategies
- Clear error handling and rollback logic

## Next Steps

1. ✅ Design validated and approved (2025-12-24)
2. Begin Phase 1 implementation (core dual-key support + explicit mode)
3. Test with real repositories
4. Implement Phase 2 (automatic discovery)
5. Iterate based on feedback

---

---

## Appendix: Alternative Design Options

The following design options were considered but not selected. They are documented here for reference and potential future consideration.

### Option 1: Automatic Discovery with Pairing

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

**Why Not Selected:**
- Cannot handle keys in different files (common in some architectures)
- No fallback when discovery fails
- Limited to same-file discovery only

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

**Why Not Selected:**
- Less user-friendly (requires manual identifier lookup)
- More complex CLI interface
- The Hybrid Approach includes explicit mode as a fallback option

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

**Why Not Selected:**
- Requires upfront configuration (less convenient for one-off rotations)
- Additional file to manage
- The Hybrid Approach provides automatic discovery which is more user-friendly
- Can be added as an enhancement in Phase 3 if needed

---

**Created:** 2025-12-18
**Last Updated:** 2025-12-24
**Author:** AI Assistant
**Status:** Design Validated - Ready for Implementation
