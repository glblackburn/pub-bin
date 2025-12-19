# Trufflehog Results Analyzer - Dual Mode Design

## Purpose

Extend the trufflehog results analyzer to support analyzing both **tokenized** and **raw** trufflehog output files. This allows the same analysis tool to work with:
- Tokenized files (secrets replaced with `TOKEN_*` placeholders)
- Raw files (actual secret values present)

## Script Renaming

**Current Name:** `trufflehog-analyze-tokenized.py`  
**New Name:** `trufflehog-analyze-results.py`

**Rationale:**
- Current name implies it only works with tokenized files
- New name is more generic and reflects dual-mode capability
- Better describes the script's purpose (analyzing trufflehog results)
- Aligns with the script's expanded functionality

**Migration:**
- Keep old script name as symlink or wrapper for backward compatibility
- Update all documentation to reference new name
- Add deprecation notice in old script (if kept)

## Current State

The current `trufflehog-analyze-tokenized.py` script:
- Only processes files with `TOKEN_*` patterns in "Raw result:" lines
- Skips files that don't contain tokens (line 62-64)
- Assumes all input files are tokenized

## Use Cases

1. **Mixed Analysis**: Analyze a directory containing both tokenized and raw files
2. **Raw File Analysis**: Analyze raw trufflehog output without tokenization step
3. **Backward Compatibility**: Continue to work with existing tokenized files
4. **Flexible Workflow**: Support workflows that don't always tokenize first

## Requirements

### Core Functionality

1. **Auto-Detection**: Automatically detect whether a file contains tokenized or raw results
2. **Dual Parsing**: Parse both tokenized (`TOKEN_*`) and raw (actual secrets) formats
3. **Consistent Analysis**: Use the same analysis logic for both modes
4. **Identifier Generation**: For raw files, generate consistent identifiers from secrets
5. **Backward Compatibility**: Existing tokenized file workflows continue to work

### Detection Strategy

**Tokenized File Detection:**
- Pattern: `Raw result: TOKEN_<hash>_<suffix>`
- Regex: `^Raw result:\s*(TOKEN_\S+)$`

**Raw File Detection:**
- Pattern: `Raw result: <actual_secret_value>`
- Regex: `^Raw result:\s*(.+)$` (not matching `TOKEN_` pattern)
- Secret values are typically:
  - Long strings (20+ characters for API keys/tokens)
  - Base64 encoded strings
  - Hex strings
  - Various formats depending on detector type

### Identifier Strategy for Raw Files

**Option 1: Hash-Based Identifier (Recommended)**
- Generate SHA256 hash of the raw secret value
- Use first 8 characters as identifier prefix
- Format: `RAW_<hash_prefix>_<short_hash_suffix>`
- Example: `RAW_a3f2b1c4_9e8d7f6a`
- **Pros**: Consistent, reversible (if you store the mapping), no secret exposure
- **Cons**: Requires hash computation

**Option 2: Truncated Secret with Hash**
- Use first 4 characters + last 4 characters + hash
- Format: `RAW_<first4>_<hash>_<last4>`
- Example: `RAW_xoxb_a3f2b1c4_9e8d`
- **Pros**: More readable, partial secret visible
- **Cons**: Exposes partial secret in reports (security risk)

**Option 3: Full Hash Only**
- Use full SHA256 hash
- Format: `RAW_<full_hash>`
- Example: `RAW_a3f2b1c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b`
- **Pros**: Most secure, no secret exposure
- **Cons**: Very long identifiers, less readable

**Recommendation: Option 1 (Hash-Based Identifier)**
- Balance between security and usability
- Consistent with token format (`TOKEN_<hash>_<suffix>`)
- **No lookup table needed** - raw files already contain the secrets

### Why No Lookup Table for Raw Files?

**Lookup tables are NOT needed for raw files because:**

1. **Raw files contain original secrets**: The source files already have the actual secret values
2. **Re-parsing is sufficient**: If you need the secrets later, you can re-parse the raw files
3. **Different use case**: Lookup tables are only needed for tokenized files where secrets are replaced with tokens
4. **Redundancy**: Creating a lookup table for raw files would duplicate data that already exists

**Comparison:**
- **Tokenized files**: Secrets replaced → Need lookup table to recover secrets
- **Raw files**: Secrets present → No lookup table needed (secrets are in the files)

## Architecture Changes

### File Detection

```python
def detect_file_type(file_path: Path) -> str:
    """
    Detect if file contains tokenized or raw results.
    Returns: 'tokenized', 'raw', or 'unknown'
    """
    # Sample first few result blocks
    # If any "Raw result:" line contains TOKEN_ pattern → tokenized
    # If any "Raw result:" line exists but no TOKEN_ pattern → raw
    # If no "Raw result:" lines → unknown
"""

def detect_directory_type(directory: Path) -> Tuple[str, int, int]:
    """
    Detect file types in a directory.
    Returns: (mode, tokenized_count, raw_count)
    - mode: 'tokenized', 'raw', 'mixed', or 'unknown'
    - tokenized_count: Number of tokenized files found
    - raw_count: Number of raw files found
    """
    # Scan files and count types
    # Return summary for confirmation prompt
```

### Raw File Confirmation

```python
def confirm_raw_file_processing(raw_count: int, skip_prompt: bool = False) -> bool:
    """
    Prompt user to confirm processing raw files.
    
    Args:
        raw_count: Number of raw files detected
        skip_prompt: If True, skip prompt and return True
    
    Returns:
        True if processing should continue, False otherwise
    """
    if skip_prompt:
        return True
    
    print(f"\n{'='*70}", file=sys.stderr)
    print(f"WARNING: {raw_count} raw trufflehog file(s) detected", file=sys.stderr)
    print(f"{'='*70}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Raw files contain ACTUAL SECRETS (not tokenized).", file=sys.stderr)
    print("", file=sys.stderr)
    print("Processing raw files will:", file=sys.stderr)
    print("  - Generate hash-based identifiers from secrets", file=sys.stderr)
    print("  - Create analysis report (secrets NOT included by default)", file=sys.stderr)
    print("  - Potentially expose secret patterns in report metadata", file=sys.stderr)
    print("", file=sys.stderr)
    print("Continue? [y/N]: ", end='', file=sys.stderr)
    
    response = input().strip().lower()
    return response in ('y', 'yes')
```

### Dual Parsing

```python
def parse_file(file_path: Path, file_type: str = None) -> List[Dict]:
    """
    Parse a trufflehog output file (tokenized or raw).
    
    Args:
        file_path: Path to the file
        file_type: 'tokenized', 'raw', or None (auto-detect)
    
    Returns:
        List of occurrences with 'identifier' field (token or raw identifier)
    """
    if file_type is None:
        file_type = detect_file_type(file_path)
    
    if file_type == 'tokenized':
        return parse_tokenized_file(file_path)
    elif file_type == 'raw':
        return parse_raw_file(file_path)
    else:
        return []
```

### Raw File Parsing

```python
def parse_raw_file(file_path: Path) -> List[Dict]:
    """
    Parse a raw trufflehog output file.
    Generates hash-based identifiers for raw secrets.
    
    Note: No lookup table is generated for raw files because:
    - The original secrets are already in the source files
    - If you need the secrets, you can re-parse the raw files
    - Lookup tables are only needed for tokenized files (where secrets are replaced)
    """
    import hashlib
    
    occurrences = []
    # ... parse result blocks ...
    
    # Extract Raw result (actual secret)
    raw_match = re.search(r'^Raw result:\s*(.+)$', block, re.MULTILINE)
    if raw_match:
        raw_secret = raw_match.group(1).strip()
        
        # Generate identifier from hash
        secret_hash = hashlib.sha256(raw_secret.encode()).hexdigest()
        identifier = f"RAW_{secret_hash[:8]}_{secret_hash[8:16]}"
        
        occurrence['identifier'] = identifier
        occurrence['is_tokenized'] = False
        # Do NOT store raw_secret - it's not needed for analysis
        # The raw files themselves contain the secrets if needed
    # ... rest of parsing ...
```

### Identifier Unification

**Current Structure:**
```python
occurrence = {
    'token': 'TOKEN_abc123_def456',
    'detector_type': 'AWS',
    'repository_name': 'example-repo',
    'file_path': 'config.json',
    'line_number': 42
}
```

**New Structure:**
```python
occurrence = {
    'identifier': 'TOKEN_abc123_def456',  # or 'RAW_a3f2b1c4_9e8d7f6a'
    'is_tokenized': True,  # or False
    'detector_type': 'AWS',
    'repository_name': 'example-repo',
    'file_path': 'config.json',
    'line_number': 42
    # Note: raw_secret is NOT stored - secrets remain in source files
}
```

### Analysis Logic Updates

**Token Index Building:**
- Change from `token_index[token]` to `token_index[identifier]`
- All analysis logic remains the same
- Report generation uses `identifier` instead of `token`

**Report Output:**
- Use "Identifier" or "Secret ID" instead of "Token" in reports
- Indicate whether each identifier is from tokenized or raw file
- Optionally show file type in summary statistics

## CLI Changes

### New Options

```bash
--mode {auto,tokenized,raw}
    Analysis mode:
    - auto: Auto-detect file type (default)
    - tokenized: Only process tokenized files
    - raw: Only process raw files

--include-raw-secrets
    Include actual secret values in report (default: False)
    WARNING: Only use if report will be kept secure

--skip-raw-confirmation
    Skip confirmation prompt when raw files are detected (default: False)
    Use with caution - raw files contain actual secrets
```

### Raw File Detection and Confirmation

**Auto-Detection:**
- Script automatically detects if files contain tokenized or raw results
- Detection happens during initial file scan

**Confirmation Prompt:**
- When raw files are detected, prompt user for confirmation:
  ```
  WARNING: Raw trufflehog files detected (contain actual secrets).
  
  Processing raw files will:
  - Generate hash-based identifiers from secrets
  - Create analysis report (secrets NOT included by default)
  - Potentially expose secret patterns in report metadata
  
  Continue? [y/N]:
  ```

**Bypass Option:**
- `--skip-raw-confirmation`: Skip the prompt (useful for automation)
- Should be used with caution - ensures user is aware of raw file processing

### Backward Compatibility

- Default behavior: `--mode auto` (detects both)
- Existing workflows continue to work (tokenized files)
- No breaking changes to existing options

## Output Format Changes

### Summary Table

**Current:**
```
| Token | Occurrences | Repositories | Files | Detector Type |
|-------|-------------|--------------|-------|---------------|
| [TOKEN_abc123_def456](#token-abc123-def456) | 5 | 2 | 3 | AWS |
```

**New:**
```
| Identifier | Type | Occurrences | Repositories | Files | Detector Type |
|------------|------|-------------|--------------|-------|---------------|
| [TOKEN_abc123_def456](#token-abc123-def456) | Token | 5 | 2 | 3 | AWS |
| [RAW_a3f2b1c4_9e8d7f6a](#raw-a3f2b1c4-9e8d7f6a) | Raw | 3 | 1 | 2 | GitHub |
```

### Section Headers

**Current:**
```
## Tokens Summary
### <a id="token-abc123-def456"></a>TOKEN_abc123_def456
```

**New:**
```
## Identifiers Summary
### <a id="token-abc123-def456"></a>TOKEN_abc123_def456 (Tokenized)
### <a id="raw-a3f2b1c4-9e8d7f6a"></a>RAW_a3f2b1c4_9e8d7f6a (Raw)
```

### Statistics

Add to summary:
- Total tokenized identifiers
- Total raw identifiers
- Files processed (tokenized vs raw)

## Security Considerations

### Raw Secret Handling

1. **Default Behavior**: Never include raw secrets in reports
2. **No Lookup Table Needed**: Raw files already contain secrets - no lookup table required
3. **Confirmation Prompt**: Always prompt user when raw files are detected
4. **Warning**: Clear warnings when processing raw files
5. **Bypass Option**: `--skip-raw-confirmation` for automation (use with caution)

### Report Generation

- **Safe by Default**: Reports only contain identifiers, not secrets
- **Optional Flag**: `--include-raw-secrets` requires explicit opt-in
- **Warnings**: Display warnings when processing raw files

## Implementation Plan

### Phase 0: Script Renaming
1. Rename `trufflehog-analyze-tokenized.py` → `trufflehog-analyze-results.py`
2. Create symlink or wrapper script for backward compatibility (optional)
3. Update all references in documentation (see "Files to Update" section below)
4. Update imports/dependencies if any
5. Update script's internal description/docstring

## Files to Update for Script Rename

### Documentation Files

1. **README.md**
   - Add new section for `trufflehog-analyze-results.py`
   - Update workflow examples
   - Note backward compatibility with old name

2. **trufflehog-analyze-tokenized-design.md**
   - Update script name in component descriptions
   - Update CLI examples (lines 300, 351, 354, 360, 365, 370)
   - Update script reference in architecture section (line 40)

3. **trufflehog-analyze-tokenized-design-analysis.md**
   - Check for any script name references
   - Update if workflow examples are present

4. **trufflehog-analyze-tokenized-design-dual-mode.md** (this file)
   - Already updated with new name
   - Keep references to old name for migration context

5. **TOOL_COMPARISON.md**
   - Check if script is mentioned in comparison
   - Update if workflow examples reference it

### Script Files

6. **trufflehog-analyze-tokenized.py** (to be renamed)
   - Rename file to `trufflehog-analyze-results.py`
   - Update script's docstring (lines 3-6: "Trufflehog Tokenized Results Analyzer" → "Trufflehog Results Analyzer")
   - Update argparse description (line 513: `description='Analyze tokenized...'` → `'Analyze trufflehog results...'`)
   - Update any internal comments referencing the script name
   - Update shebang if needed (should remain `#!/usr/bin/env python3`)

7. **Backward Compatibility Wrapper** (new file, optional)
   - Create `trufflehog-analyze-tokenized.py` as symlink or wrapper
   - Include deprecation notice if wrapper approach used

### Git History

8. **Git Commit Messages**
   - Previous commits reference old name (in `.git/logs/`)
   - No action needed (history preserved)
   - Future commits will use new name

### Other Files

9. **Makefile** (if exists)
   - Check for script references in targets
   - Update if script is part of installation/execution

10. **Shell Scripts** (if any reference the script)
    - `trufflehog-local-git-repos.sh` - Check for references
    - `trufflehog-show-raw-results.sh` - Check for references
    - `trufflehog-sum-uniq-raw-results.sh` - Check for references

11. **Workflow Documentation**
    - Any workflow guides or examples
    - Integration documentation
    - CI/CD pipeline configurations (if applicable)

### Summary Checklist

**Script File:**
- [ ] Rename script file: `trufflehog-analyze-tokenized.py` → `trufflehog-analyze-results.py`
- [ ] Update script's docstring (lines 3-6: "Trufflehog Tokenized Results Analyzer")
- [ ] Update argparse description (line 513: `description='Analyze tokenized...'`)

**Documentation Files:**
- [ ] Update `README.md` - Add new section for `trufflehog-analyze-results.py`
- [ ] Update `trufflehog-analyze-tokenized-design.md` (6 locations: lines 40, 300, 351, 354, 360, 365, 370)
- [ ] Check `trufflehog-analyze-tokenized-design-analysis.md` for references
- [ ] Check `TOOL_COMPARISON.md` for references (if any)

**Backward Compatibility:**
- [ ] Create backward compatibility symlink/wrapper (optional)
- [ ] Test backward compatibility (if symlink/wrapper created)

**Other Files:**
- [ ] Check shell scripts (`trufflehog-*.sh`) for references
- [ ] Check Makefile for references (if exists)
- [ ] Update any workflow documentation or examples
- [ ] Check CI/CD configurations (if applicable)

### Phase 1: Detection and Parsing
1. Add `detect_file_type()` function
2. Add `detect_directory_type()` function
3. Add `confirm_raw_file_processing()` function
4. Add `parse_raw_file()` function
5. Update `parse_tokenized_file()` to use unified structure
6. Add identifier generation for raw files

### Phase 2: Analysis Updates
1. Update token index to use `identifier` instead of `token`
2. Update all analysis functions to work with identifiers
3. Add file type tracking (tokenized vs raw)

### Phase 3: CLI and Output
1. Add `--mode` option
2. Add `--include-raw-secrets` option
3. Add `--skip-raw-confirmation` option
4. Integrate confirmation prompt into main workflow
5. Update report generation to show identifier types
6. Update summary statistics

### Phase 4: Testing and Documentation
1. Test with tokenized files (backward compatibility)
2. Test with raw files
3. Test with mixed directories
4. Update README.md with new options
5. Add examples for both modes

## Migration Path

### Script Renaming

**Old Name:** `trufflehog-analyze-tokenized.py`  
**New Name:** `trufflehog-analyze-results.py`

**Migration Options:**

1. **Symlink Approach** (Recommended)
   ```bash
   # Create symlink for backward compatibility
   ln -s trufflehog-analyze-results.py trufflehog-analyze-tokenized.py
   ```

2. **Wrapper Script Approach**
   ```bash
   # Create wrapper that calls new script
   #!/bin/bash
   exec "$(dirname "$0")/trufflehog-analyze-results.py" "$@"
   ```

3. **Direct Rename** (Breaking Change)
   - Simply rename the file
   - Update all scripts/workflows that reference it
   - Update documentation

**Recommendation:** Use symlink approach for smooth transition, remove after deprecation period.

### For Existing Users

**No changes required:**
- Existing tokenized files continue to work
- Default behavior detects both types
- All existing options remain valid
- Old script name continues to work (via symlink/wrapper)

### For New Users

**Can use either:**
```bash
# Analyze tokenized files (existing workflow)
./trufflehog-analyze-results.py -d ./tokenized --org example

# Analyze raw files (new capability)
./trufflehog-analyze-results.py -d ./raw --org example --mode raw

# Analyze mixed directory (auto-detect)
./trufflehog-analyze-results.py -d ./mixed --org example --mode auto

# Analyze raw files with confirmation prompt (default)
./trufflehog-analyze-results.py -d ./raw --org example --mode raw

# Analyze raw files without confirmation (automation)
./trufflehog-analyze-results.py -d ./raw --org example --mode raw --skip-raw-confirmation

# Backward compatibility (if symlink/wrapper kept)
./trufflehog-analyze-tokenized.py -d ./tokenized --org example
```

## Open Questions

1. **Naming**: Should script be renamed to `trufflehog-analyze-results.py`?
   - **Decision**: YES - Rename to `trufflehog-analyze-results.py`
   - **Rationale**: Current name is misleading (implies tokenized-only)
   - **Migration**: Keep old name as symlink/wrapper for backward compatibility
   - **Timeline**: Rename as part of Phase 0 (before other changes)

2. **Lookup Table for Raw Files**: Do we need a lookup table for raw files?
   - **Decision**: NO - Lookup tables are not needed for raw files
   - **Reasoning**: 
     - Raw files already contain the original secrets
     - If you need the secrets, you can re-parse the raw files
     - Lookup tables are only needed for tokenized files (where secrets are replaced with tokens)
     - Generating a lookup table for raw files would be redundant
   - **Removed**: `--raw-lookup-table` option from design

3. **Report Naming**: Should reports indicate if they contain raw identifiers?
   - **Recommendation**: Yes, add indicator in report header/metadata

4. **Performance**: Hash computation for large raw files?
   - **Consideration**: Hash computation is fast, but may add overhead for very large files
   - **Mitigation**: Only hash when needed, cache results

## Success Criteria

1. ✅ Script renamed to `trufflehog-analyze-results.py`
2. ✅ Backward compatibility maintained (symlink/wrapper if needed)
3. ✅ Can analyze tokenized files (backward compatible)
4. ✅ Can analyze raw files
5. ✅ Can analyze mixed directories (auto-detect)
6. ✅ Auto-detection of file types
7. ✅ Confirmation prompt for raw files (with bypass option)
8. ✅ Reports clearly indicate identifier types
9. ✅ No raw secrets in reports by default
10. ✅ All existing functionality preserved
11. ✅ Clear documentation and examples
