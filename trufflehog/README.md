# Trufflehog Scripts

## trufflehog-local-git-repos.sh

A utility script to recursively find and scan git repositories for secrets using Trufflehog.

**What it does:**
- Recursively searches for `.git` directories in the target directory
- Runs `trufflehog` on each identified repository
- Captures scan results to separate timestamped log files for each repository
- Uses `trufflehog git file://...` URI format for scanning
- Filters results to show only `verified` and `unknown` secrets

**Usage:**
```bash
./trufflehog-local-git-repos.sh [-hqv] -d <directory> [-o <output_directory>]
```

**Options:**
- `-h` : Display help message
- `-d <directory>` : Target directory to scan (Required)
- `-o <directory>` : Output directory for reports (Default: target directory)
- `-q` : Quiet mode (output as little as possible)
- `-v` : Verbose output

**Details:**
- The script identifies repositories by looking for `.git` directories.
- It executes `trufflehog git file://<repo_path> --results=verified,unknown`.
- Output files are saved in the target directory with the naming convention: `trufflehog-<repo_name>-<timestamp>.txt`.
- Follows shell-template.sh patterns: proper error handling, CLI options, functions, and structure.

**Examples:**
```bash
# Scan all repos in ~/projects
./trufflehog-local-git-repos.sh -d ~/projects

# Verbose mode
./trufflehog-local-git-repos.sh -v -d ~/projects
```

**Dependencies:**
- `trufflehog` - Required for scanning (must be in PATH)
- `git` - Required for repository operations

**Installation:**

The script requires `trufflehog` to be installed. You can install it using the provided Makefile:

```bash
# Check if trufflehog is installed
make check

# Install trufflehog automatically (detects OS and architecture)
make install

# Force reinstall (overwrites existing installation)
make install-force

# Update to latest version
make update

# Uninstall trufflehog
make uninstall

# Install to a custom directory
INSTALL_DIR=/usr/local/bin make install
```

The Makefile will:
- Detect your OS (Linux, macOS, Windows) and architecture (amd64, arm64)
- Automatically fetch the latest version from GitHub (if `curl` and `jq` are available)
- Download and install trufflehog to `~/bin` by default
- Verify the installation works correctly
- Check if the install directory is in your PATH
- Provide clear error messages if installation fails

**Makefile Targets:**
- `make check` - Check if trufflehog is installed and show version
- `make install` - Install trufflehog (skips if already installed)
- `make install-force` - Force reinstall (overwrites existing)
- `make update` - Update to the latest version
- `make uninstall` - Remove trufflehog binary
- `make clean` - Clean up temporary installation files
- `make test` - Test the script syntax and help output

If trufflehog is not installed, the script will display a clear error message with installation instructions.

---

## trufflehog-tokenize-secrets.py

A Python script that replaces secret values in trufflehog output files with reversible tokens. This allows AI agents and other automated tools to process sanitized files without exposing actual secrets, while maintaining the ability to recover the original values when needed.

**What it does:**
- Scans trufflehog output files for "Raw result:" lines containing secrets
- Replaces secret values with consistent tokens (same secret → same token across all files)
- Generates a JSON lookup table mapping tokens back to original secrets
- Preserves all other information in the files (repository names, file paths, detector types, etc.)

**Usage:**
```bash
./trufflehog-tokenize-secrets.py [-h] [-v] [-q] [-n] [--in-place]
    -d <directory> 
    [-o <output_directory>] 
    [-l <lookup_table_path>]
    [-p <file_pattern>]
    [--hash-length <n>]
    [--suffix-length <n>]
```

**Options:**
- `-d, --directory` : Target directory containing files to tokenize (Required)
- `-o, --output` : Output directory for tokenized files (Default: `<input_dir>_tokenized_<timestamp>`)
- `-l, --lookup-table` : Path to lookup table file (Default: `secrets_lookup_<timestamp>.json` in output directory)
- `-p, --pattern` : File pattern to match (Default: `trufflehog-*.txt`)
- `--hash-length` : Length of hash prefix in token (Default: 8)
- `--suffix-length` : Length of random suffix in token (Default: 8 hex chars)
- `--in-place` : Overwrite original files (REQUIRES EXPLICIT CONFIRMATION)
- `-v, --verbose` : Verbose output
- `-q, --quiet` : Quiet mode
- `-n, --dry-run` : Show what would be done without making changes
- `-h, --help` : Show help message

**Details:**
- Token format: `TOKEN_<hash_prefix>_<random_suffix>` (e.g., `TOKEN_a3f2b1c4_9e8d7f6a`)
- Same secret values always map to the same token across all files (deterministic via hash)
- Lookup table is saved as JSON with restrictive permissions (600)
- Default output directory includes timestamp to prevent accidental overwrites
- If lookup table file already exists, script stops with an error
- In-place mode displays a warning banner and requires typing "YES" to confirm

**Examples:**
```bash
# Basic usage (creates timestamped output directory)
./trufflehog-tokenize-secrets.py -d ./scan_results

# Custom output and lookup table
./trufflehog-tokenize-secrets.py -d ./scan_results \
    -o ./tokenized_results \
    -l ./secrets_lookup.json

# Dry run to see what would happen
./trufflehog-tokenize-secrets.py -d ./scan_results -n -v

# In-place tokenization (with confirmation prompt)
./trufflehog-tokenize-secrets.py -d ./scan_results --in-place
```

**Dependencies:**
- Python 3.6+ (uses standard library only: argparse, json, hashlib, secrets, pathlib, re, datetime, os)

**Security:**
- Lookup table contains actual secrets and should be protected
- File permissions are set to 600 (owner read/write only)
- Store lookup table in a secure location separate from tokenized files
- If lookup table is lost, secrets cannot be recovered from tokenized files

---

## trufflehog-detokenize-secrets.py

A Python script that restores original secret values from tokenized trufflehog output files using a lookup table.

**What it does:**
- Reads tokenized files and identifies tokens
- Uses lookup table to map tokens back to original secrets
- Replaces tokens with original secret values
- Validates that all tokens are present in lookup table
- Outputs restored files with original secrets

**Usage:**
```bash
./trufflehog-detokenize-secrets.py [-h] [-v] [-q] [-n] [--continue-on-missing]
    -d <directory>
    [-l <lookup_table_path>]
    [-o <output_directory>]
    [-p <file_pattern>]
```

**Options:**
- `-d, --directory` : Directory containing tokenized files (Required)
- `-l, --lookup-table` : Path to lookup table JSON file (Default: auto-detect in `-d` directory)
- `-o, --output` : Output directory for detokenized files (Default: `<input_dir>_restored_<timestamp>`)
- `-p, --pattern` : File pattern to match (Default: `trufflehog-*.txt`)
- `-v, --verbose` : Verbose output
- `-q, --quiet` : Quiet mode
- `-n, --dry-run` : Show what would be done without making changes
- `--continue-on-missing` : Continue processing even if some tokens are missing from lookup table
- `-h, --help` : Show help message

**Details:**
- Automatically searches for lookup table files matching `secrets_lookup_*.json` in the input directory if `-l` is not specified
- If multiple lookup tables are found, uses the most recent one (by modification time)
- Reports missing tokens and exits with error unless `--continue-on-missing` is used
- Default output directory includes timestamp to prevent accidental overwrites

**Examples:**
```bash
# Restore secrets (auto-detects lookup table in directory)
./trufflehog-detokenize-secrets.py -d ./tokenized_results -o ./restored_results

# Specify lookup table explicitly
./trufflehog-detokenize-secrets.py -d ./tokenized_results \
    -l ./secrets_lookup.json \
    -o ./restored_results

# Dry run to see what would happen
./trufflehog-detokenize-secrets.py -d ./tokenized_results -n -v

# Continue even if some tokens are missing
./trufflehog-detokenize-secrets.py -d ./tokenized_results \
    --continue-on-missing
```

**Dependencies:**
- Python 3.6+ (uses standard library only: argparse, json, pathlib, re, os, sys)

---

## Complete Workflow Example

```bash
# 1. Run trufflehog scans on local repositories
./trufflehog-local-git-repos.sh -d ~/repos -o ./scan_results

# 2. Tokenize the results (masks secrets for safe processing)
./trufflehog-tokenize-secrets.py -d ./scan_results \
    -o ./tokenized_results \
    -l ./secrets_lookup.json

# 3. Process tokenized files with AI agent or other tools
# (secrets are masked as tokens, safe for external processing)
# ... AI processing happens here ...

# 4. Restore secrets when needed (auto-detects lookup table)
./trufflehog-detokenize-secrets.py -d ./tokenized_results \
    -o ./restored_results
```

**Important Notes:**
- Keep the lookup table secure - it contains the actual secrets
- If the lookup table is lost, secrets cannot be recovered from tokenized files
- Tokenized files are safe to share or process externally
- The same secret always maps to the same token across all files

---
Created using Google Antigravity.
