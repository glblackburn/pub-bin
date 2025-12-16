# Trufflehog Secret Tokenization System - Design Document

## Purpose

Create a tokenization system that replaces secret values in trufflehog output files with reversible tokens. This allows AI agents and other automated tools to process sanitized files without exposing actual secrets, while maintaining the ability to recover the original values when needed.

## Use Cases

1. **AI Agent Processing**: Allow AI agents to analyze trufflehog scan results without exposing secrets to external systems
2. **Secure Sharing**: Share scan results with team members or tools without revealing actual secret values
3. **Audit Trail**: Maintain ability to identify and investigate specific secrets while keeping them masked in reports
4. **Pattern Analysis**: Enable analysis of secret patterns and types without exposing sensitive data

## Core Requirements

1. **Consistent Tokenization**: The same secret value must always map to the same token across all files
2. **Reversibility**: Must be able to decode tokens back to original values using a lookup table
3. **Token Format**: Tokens should be clearly identifiable and distinguishable from actual secrets
4. **Lookup Table**: Secure storage of token-to-secret mappings
5. **Batch Processing**: Process multiple files in a directory
6. **Preserve Context**: Maintain all other information in the files (repository names, file paths, detector types, etc.)

## Architecture

### Components

1. **Tokenization Script** (`trufflehog-tokenize-secrets.py`)
   - Scans files for "Raw result:" lines
   - Extracts secret values
   - Generates consistent tokens
   - Replaces secrets with tokens
   - Generates lookup table

2. **Detokenization Script** (`trufflehog-detokenize-secrets.py`)
   - Reads tokenized files
   - Uses lookup table to restore original secrets
   - Outputs restored files

3. **Lookup Table Format**
   - JSON format for easy parsing and programmatic access
   - Secure storage (permissions, encryption considerations)
   - Metadata (creation date, file count, token count)

## Token Generation Strategy

### Token Format
```
TOKEN_<hash_prefix>_<random_suffix>
```

Where:
- `TOKEN_` - Clear prefix to identify tokens
- `<hash_prefix>` - First 8 characters of SHA256 hash of the secret (for consistency)
- `<random_suffix>` - 8-character random hex string (for uniqueness and security)

Example: `TOKEN_a3f2b1c4_9e8d7f6a`

### Why This Approach?
- **Hash prefix**: Ensures same secret → same token (deterministic)
- **Random suffix**: Prevents rainbow table attacks on the hash alone
- **Clear prefix**: Easy to identify tokens in text
- **Length**: Sufficiently long to avoid collisions

### Alternative: UUID-based with Hash Mapping
- Generate UUID for each unique secret
- Store UUID → secret mapping
- Format: `TOKEN_<uuid>`
- Simpler but less deterministic (requires lookup table for consistency)

## Lookup Table Structure

### JSON Format
```json
{
  "metadata": {
    "version": "1.0",
    "created": "2025-12-04T18:26:09Z",
    "source_directory": "/path/to/scans",
    "file_count": 15,
    "unique_secrets": 42,
    "tool": "trufflehog-tokenize-secrets"
  },
  "tokens": {
    "TOKEN_a3f2b1c4_9e8d7f6a": {
      "secret": "actual_secret_value_here",
      "first_seen": "2025-12-04T18:26:09Z",
      "occurrence_count": 3,
      "files": [
        "trufflehog-repo1-2025-12-04_182609.txt",
        "trufflehog-repo2-2025-12-04_182609.txt"
      ]
    }
  }
}
```

### Security Considerations
- **File Permissions**: Lookup table should have restrictive permissions (600)
- **Location**: Store in secure location, separate from tokenized files
- **Encryption**: Optional encryption for lookup table (future enhancement)
- **Access Control**: Document who should have access to lookup table

### Lookup Table Handling
- **Unique Location**: Lookup table path must be unique (include timestamp in default)
- **Default Naming**: `secrets_lookup_<timestamp>.json` (e.g., `secrets_lookup_20251204_182609.json`)
- **Existence Check**: If lookup table file already exists, stop with error message
- **Output Directory**: Default output directory includes timestamp to avoid overwrites: `<input_dir>_tokenized_<timestamp>`

## File Processing Logic

### Tokenization Process

1. **Scan Phase**
   - Find all files in target directory (non-recursive - see Future Enhancements)
   - Identify files to process (pattern matching: `trufflehog-*.txt`)
   - Extract all "Raw result:" lines with their secret values

2. **Token Generation Phase**
   - For each unique secret value:
     - Calculate SHA256 hash
     - Check if token already exists in lookup table
     - If exists, reuse token
     - If new, generate new token with format above
     - Store in lookup table

3. **Replacement Phase**
   - For each file:
     - Read file content
     - Find all "Raw result:" lines
     - Replace secret value with corresponding token
     - Write to output directory (or in-place with explicit confirmation - see CLI options)

4. **Lookup Table Generation**
   - Save lookup table to specified location (must be unique - see Lookup Table Handling)
   - Include metadata about processing
   - Set restrictive file permissions (600)

### Detokenization Process

1. **Load Lookup Table**
   - Read JSON lookup table
   - Validate format and version

2. **Process Files**
   - Find tokenized files
   - Replace tokens with original secrets from lookup table
   - Output restored files

3. **Validation**
   - Verify all tokens were found in lookup table
   - Report any missing tokens

## CLI Interface

### Tokenization Script

```bash
trufflehog-tokenize-secrets.py [-h] [-v] [-q] [-n] [--in-place]
    -d <directory> 
    [-o <output_directory>] 
    [-l <lookup_table_path>]
    [-p <file_pattern>]
    [--hash-length <n>]
    [--suffix-length <n>]
```

**Options:**
- `-d, --directory`: Target directory containing files to tokenize (Required)
- `-o, --output`: Output directory for tokenized files (Default: `<input_dir>_tokenized_<timestamp>`)
- `-l, --lookup-table`: Path to lookup table file (Default: `secrets_lookup_<timestamp>.json` in output directory)
- `-p, --pattern`: File pattern to match (Default: `trufflehog-*.txt`)
- `--hash-length`: Length of hash prefix in token (Default: 8)
- `--suffix-length`: Length of random suffix in token (Default: 8)
- `--in-place`: Overwrite original files (REQUIRES EXPLICIT CONFIRMATION - see In-Place Tokenization)
- `-v, --verbose`: Verbose output
- `-q, --quiet`: Quiet mode
- `-n, --dry-run`: Show what would be done without making changes
- `-h, --help`: Show help message

**Examples:**
```bash
# Basic usage (creates timestamped output directory)
./trufflehog-tokenize-secrets.py -d ./scan_results

# Custom output and lookup table
./trufflehog-tokenize-secrets.py -d ./scan_results \
    -o ./tokenized_results \
    -l ./secrets_lookup_20251204.json

# Dry run to see what would happen
./trufflehog-tokenize-secrets.py -d ./scan_results -n -v

# In-place tokenization (with confirmation prompt)
./trufflehog-tokenize-secrets.py -d ./scan_results --in-place
```

### Detokenization Script

```bash
trufflehog-detokenize-secrets.py [-h] [-v] [-q] [-n]
    -d <directory>
    -l <lookup_table_path>
    [-o <output_directory>]
    [-p <file_pattern>]
```

**Options:**
- `-d, --directory`: Directory containing tokenized files (Required)
- `-l, --lookup-table`: Path to lookup table JSON file (Required)
- `-o, --output`: Output directory for detokenized files (Default: same as input, with `_restored` suffix)
- `-p, --pattern`: File pattern to match (Default: `trufflehog-*.txt`)
- `-v, --verbose`: Verbose output
- `-q, --quiet`: Quiet mode
- `-n, --dry-run`: Show what would be done without making changes
- `-h, --help`: Show help message

**Examples:**
```bash
# Restore secrets from tokenized files
./trufflehog-detokenize-secrets.py -d ./tokenized_results \
    -l ./secrets_lookup.json \
    -o ./restored_results
```

## Implementation Details

### Python Dependencies
- `argparse` - CLI argument parsing
- `json` - Lookup table serialization
- `hashlib` - SHA256 hashing
- `secrets` - Cryptographically secure random number generation
- `pathlib` - Path handling
- `re` - Regular expressions for pattern matching
- `datetime` - Timestamp generation
- `os` - File operations and permissions

### Key Functions

#### Tokenization Script
- `scan_files(directory, pattern)` - Find files to process
- `extract_secrets(file_path)` - Extract "Raw result:" values from file
- `generate_token(secret, lookup_table)` - Generate or retrieve token for secret
- `tokenize_file(input_path, output_path, token_map)` - Replace secrets with tokens in file
- `save_lookup_table(lookup_table, output_path)` - Save lookup table to JSON
- `set_secure_permissions(file_path)` - Set restrictive file permissions

#### Detokenization Script
- `load_lookup_table(lookup_table_path)` - Load and validate lookup table
- `detokenize_file(input_path, output_path, token_map)` - Replace tokens with secrets
- `validate_tokens(file_path, token_map)` - Check for missing tokens

### Error Handling

1. **File I/O Errors**
   - Check file permissions before reading/writing
   - Handle missing files gracefully
   - Validate JSON format for lookup table

2. **Token Collisions** (extremely unlikely but handle)
   - Detect if hash prefix + suffix combination already exists
   - Regenerate suffix if collision detected

3. **Missing Tokens in Detokenization**
   - Report which tokens are missing
   - Option to continue with partial restoration or fail

4. **Invalid Input**
   - Validate directory exists
   - Validate lookup table format
   - Check for required dependencies

5. **Lookup Table Exists**
   - If lookup table file already exists, display error and exit
   - Do not overwrite existing lookup tables
   - Suggest using different filename or removing existing file

## Security Considerations

1. **Lookup Table Protection**
   - Set file permissions to 600 (owner read/write only)
   - Store in secure location
   - Document access requirements

2. **Token Uniqueness**
   - Use cryptographically secure random for suffix
   - Sufficient length to prevent collisions

3. **Secret Handling**
   - Minimize time secrets are in memory
   - Clear variables after use (if possible in Python)
   - No logging of actual secret values

4. **Access Control**
   - Document who should have access to lookup table
   - Consider encryption for lookup table (future)

## Testing Strategy

1. **Unit Tests**
   - Token generation consistency
   - Hash calculation
   - File parsing and replacement
   - Lookup table serialization

2. **Integration Tests**
   - Full tokenization round-trip
   - Detokenization with valid lookup table
   - Error handling for missing tokens
   - Multiple files with same secrets

3. **Edge Cases**
   - Empty files
   - Files with no secrets
   - Very long secret values
   - Special characters in secrets
   - Missing lookup table
   - Corrupted lookup table

## In-Place Tokenization

### Warning and Confirmation Process

When `--in-place` flag is used, the script must:

1. **Display HUGE WARNING BANNER** before any processing:
   ```
   ╔══════════════════════════════════════════════════════════════════════════════╗
   ║                                                                              ║
   ║                    ⚠️  WARNING: IN-PLACE TOKENIZATION  ⚠️                  ║
   ║                                                                              ║
   ║  This operation will OVERWRITE your original files with tokenized versions. ║
   ║                                                                              ║
   ║  • Original files will be PERMANENTLY MODIFIED                               ║
   ║  • You MUST have the lookup table to restore original secrets               ║
   ║  • If you lose the lookup table, secrets CANNOT be recovered                ║
   ║  • This action CANNOT be undone without the lookup table                    ║
   ║                                                                              ║
   ║  Lookup table will be saved to: <path>                                      ║
   ║  Files to be modified: <count> files                                       ║
   ║                                                                              ║
   ╚══════════════════════════════════════════════════════════════════════════════╝
   ```

2. **Require Explicit Confirmation**:
   - Prompt: "Type 'YES' to confirm in-place tokenization (this cannot be undone): "
   - Only proceed if user types exactly "YES" (case-sensitive)
   - Any other input aborts the operation
   - Display confirmation message showing what will happen

3. **Safety Checks**:
   - Verify lookup table path is specified and unique
   - Show list of files that will be modified (in verbose mode)
   - Double-check that lookup table doesn't already exist

4. **Dry Run Support**:
   - `-n` flag should show what would be overwritten
   - Still show warning banner even in dry-run mode

## Future Enhancements

1. **Recursive Directory Processing**
   - Add `-r, --recursive` flag to process subdirectories
   - Maintain same token consistency across all directories

2. **Encryption**
   - Encrypt lookup table with password/key
   - Support for encrypted storage

3. **Compression**
   - Compress lookup table for large datasets

4. **Incremental Updates**
   - Append to existing lookup table
   - Merge multiple lookup tables

5. **Additional Fields**
   - Tokenize other sensitive fields (e.g., "Secret:", "Verified result:")
   - Configurable field selection

6. **Statistics**
   - Report on tokenization statistics
   - Most common secrets
   - File-by-file breakdown

7. **Validation Tools**
   - Verify tokenized files are properly formatted
   - Check lookup table integrity
   - Compare tokenized vs original file structure

## File Naming Conventions

- **Tokenized files**: Keep original names (in output directory or in-place)
- **Output directory**: `<input_dir>_tokenized_<timestamp>` (e.g., `scan_results_tokenized_20251204_182609`)
- **Lookup table**: `secrets_lookup_<timestamp>.json` (default) or user-specified (must be unique)
- **Restored files**: Add `_restored` suffix or user-specified directory

## Example Workflow

```bash
# 1. Run trufflehog scans
./trufflehog-local-git-repos.sh -d ~/repos -o ./scan_results

# 2. Tokenize the results
./trufflehog-tokenize-secrets.py -d ./scan_results \
    -o ./tokenized_results \
    -l ./secrets_lookup.json

# 3. Process tokenized files with AI agent (secrets are masked)
# ... AI processing happens here ...

# 4. Restore secrets when needed
./trufflehog-detokenize-secrets.py -d ./tokenized_results \
    -l ./secrets_lookup.json \
    -o ./restored_results
```

## Design Decisions

1. **Recursive Processing**: Not implemented initially - saved as Future Enhancement
2. **In-Place Tokenization**: Supported with `--in-place` flag, requires explicit confirmation with HUGE WARNING BANNER
3. **Lookup Table Handling**: Must be unique location, if exists stop with error. Default includes timestamp to avoid overwrites
4. **Fields to Tokenize**: Only "Raw result:" for now - other fields saved as Future Enhancement
5. **Token Format**: `TOKEN_<hash_prefix>_<random_suffix>` - approved design
6. **Lookup Table Location**: Default in output directory with timestamp, user can specify custom unique location

---

**Status**: Design Phase  
**Created**: 2025-12-04  
**Author**: Design Document
