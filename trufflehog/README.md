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
./scripts/trufflehog-local-git-repos.sh [-hqv] -d <directory> [-o <output_directory>]
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
./scripts/trufflehog-local-git-repos.sh -d ~/projects

# Verbose mode
./scripts/trufflehog-local-git-repos.sh -v -d ~/projects
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
./scripts/trufflehog-tokenize-secrets.py [-h] [-v] [-q] [-n] [--in-place]
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
./scripts/trufflehog-tokenize-secrets.py -d ./scan_results

# Custom output and lookup table
./scripts/trufflehog-tokenize-secrets.py -d ./scan_results \
    -o ./tokenized_results \
    -l ./secrets_lookup.json

# Dry run to see what would happen
./scripts/trufflehog-tokenize-secrets.py -d ./scan_results -n -v

# In-place tokenization (with confirmation prompt)
./scripts/trufflehog-tokenize-secrets.py -d ./scan_results --in-place
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
./scripts/trufflehog-detokenize-secrets.py [-h] [-v] [-q] [-n] [--continue-on-missing]
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
./scripts/trufflehog-detokenize-secrets.py -d ./tokenized_results -o ./restored_results

# Specify lookup table explicitly
./scripts/trufflehog-detokenize-secrets.py -d ./tokenized_results \
    -l ./secrets_lookup.json \
    -o ./restored_results

# Dry run to see what would happen
./scripts/trufflehog-detokenize-secrets.py -d ./tokenized_results -n -v

# Continue even if some tokens are missing
./scripts/trufflehog-detokenize-secrets.py -d ./tokenized_results \
    --continue-on-missing
```

**Dependencies:**
- Python 3.6+ (uses standard library only: argparse, json, pathlib, re, os, sys)

---

## trufflehog-analyze-results.py

A Python script that analyzes trufflehog output files (both tokenized and raw) to generate comprehensive markdown reports. The script supports dual-mode operation, automatically detecting whether files contain tokenized secrets (with `TOKEN_*` placeholders) or raw secrets (actual secret values).

**What it does:**
- Analyzes trufflehog output files (tokenized or raw)
- Auto-detects file types (tokenized vs raw)
- Generates hash-based identifiers for raw secrets (no lookup table needed)
- Counts unique identifiers and their occurrences
- Identifies where each identifier appears (repositories, files, line numbers)
- Generates GitHub URLs for easy navigation
- Creates comprehensive markdown reports with statistics and detailed location information

**Usage:**
```bash
./scripts/trufflehog-analyze-results.py [-h] [-v] [-q] [--no-browser]
    -d <directory>
    --org <organization>
    [-o <output_file>]
    [-p <file_pattern>]
    [--mode {auto,tokenized,raw}]
    [--include-raw-secrets]
    [--skip-raw-confirmation]
    [--branch <branch>]
    [--repo-map <json_file>]
    [--github-base <url>]
```

**Options:**
- `-d, --directory` : Directory containing trufflehog output files (Required)
- `--org` : GitHub organization/user name (Required)
- `-o, --output` : Output markdown file path (Default: `/tmp/tokenized_analysis_<timestamp>.md`)
- `-p, --pattern` : File pattern to match (Default: `trufflehog-*.txt`)
- `--mode` : Analysis mode: `auto` (detect), `tokenized` (only tokenized files), or `raw` (only raw files) (Default: `auto`)
- `--include-raw-secrets` : Include actual secret values in report (WARNING: Only use if report will be kept secure)
- `--skip-raw-confirmation` : Skip confirmation prompt when raw files are detected (use with caution)
- `--branch` : Default git branch to use in URLs (Default: `main`)
- `--repo-map` : JSON file for repo-specific org/branch overrides
- `--github-base` : Base GitHub URL (Default: `https://github.com/`)
- `--no-browser` : Do not open report in browser
- `-v, --verbose` : Verbose output
- `-q, --quiet` : Quiet mode
- `-h, --help` : Show help message

**Details:**
- **Auto-Detection**: Automatically detects whether files contain tokenized or raw results
- **Dual Parsing**: Parses both tokenized (`TOKEN_*`) and raw (actual secrets) formats
- **Identifier Generation**: For raw files, generates consistent hash-based identifiers (`RAW_<hash>_<suffix>`)
- **Security**: Raw secrets are never stored in memory or reports (only hash-based identifiers)
- **Confirmation Prompt**: Prompts user when raw files are detected (can be skipped with `--skip-raw-confirmation`)
- **Backward Compatible**: Existing tokenized file workflows continue to work unchanged

**Examples:**
```bash
# Analyze tokenized files (auto-detect)
./scripts/trufflehog-analyze-results.py -d ./tokenized_results --org example-org

# Analyze raw files (with confirmation prompt)
./scripts/trufflehog-analyze-results.py -d ./raw_results --org example-org --mode raw

# Analyze mixed directory (auto-detect both types)
./scripts/trufflehog-analyze-results.py -d ./mixed_results --org example-org --mode auto

# Analyze raw files without confirmation (for automation)
./scripts/trufflehog-analyze-results.py -d ./raw_results --org example-org \
    --mode raw --skip-raw-confirmation

# Custom output location and branch
./scripts/trufflehog-analyze-results.py -d ./results --org example-org \
    -o ./analysis_report.md --branch develop
```

**Dependencies:**
- Python 3.6+ (uses standard library only: argparse, json, hashlib, pathlib, re, subprocess, sys, urllib.parse)

**Security:**
- Raw secrets are never included in reports by default
- Hash-based identifiers are generated for raw secrets (no lookup table needed)
- Raw files already contain secrets - no additional storage required
- Use `--include-raw-secrets` only if report will be kept secure

---

## trufflehog-rotate-aws-key.py

A Python script that automatically rotates AWS keys (and other paired secrets) found in trufflehog analysis reports across multiple repositories. The script clones repositories, creates branches, replaces keys, and optionally commits changes.

**What it does:**
- Parses markdown reports from `trufflehog-analyze-results.py`
- Identifies all repositories and file locations for a given identifier (TOKEN_* or RAW_*)
- Clones repositories and creates timestamped branches
- Replaces old AWS keys with new key values
- **NEW:** Supports paired secret rotation (rotates both primary and paired secrets together, e.g., AWS Access Key ID + Secret Access Key)
- Supports dry-run mode (changes without commit) and commit mode
- Supports resume mode to continue from where it left off
- Atomic replacement with rollback on failure (for paired secrets in same file)

**Usage:**
```bash
./scripts/trufflehog-rotate-aws-key.py [-hqv] [-r <report_file>] [-i <identifier>] [-k <new_key>] [-l <limit>] [OPTIONS]
```

**Options:**
- `-r, --report` : Path to trufflehog-analyze-results.py markdown report (Required for initial run)
- `-i, --identifier` : Identifier to rotate (TOKEN_* or RAW_*) (Required)
- `-k, --new-key` : New AWS key value (or use -p for prompt)
- `-p, --prompt-key` : Prompt for new key interactively (masked input)
- `--credential-loader` : Path to credential loader script (Python module with `load_credentials()` function). Default: `scripts/credential-loaders/file_loader.py` if exists. Can also be set via `TRUFFLEHOG_CREDENTIAL_LOADER` env var.
- `-l, --limit` : Limit number of repositories to process (Default: 0 = all)
- `--lookup-table` : Path to secrets lookup table (required for TOKEN_ identifiers)
- `--mode` : Operation mode: `dry-run` (make changes, don't commit) or `commit` (commit changes) (Default: dry-run)
- `--resume` : Resume a previous rotation operation (reads from state file)
- `--branch-prefix` : Prefix for branch names (Default: rotate-aws-key)
- `--commit-message` : Custom commit message
- `--skip-repos` : Comma-separated list of repository names to skip
- `--only-repos` : Comma-separated list of repository names to process
- `--work-dir` : Working directory for cloning repositories (Default: /tmp/trufflehog-rotate-YYYYMMDD-HHMMSS)
- `--reuse-clones` : Reuse existing clones if found
- `--backup-dir` : Directory to store backup copies of modified files
- `-v, --verbose` : Verbose output (may contain sensitive data)
- `-q, --quiet` : Quiet mode
- `-h, --help` : Show help message

**Paired Secret Rotation Options:**
- `--paired-secret` : Enable paired secret rotation (rotates both primary and paired secrets together)
- `--paired-secret-identifier` : Paired secret identifier (TOKEN_* or RAW_*) for explicit mode (if the paired secret has its own identifier in the report)
- `--prompt-paired-secret` : Prompt for new paired secret interactively (masked input) - this is the default if not set via environment variable
- **Environment Variables:**
  - `TRUFFLEHOG_NEW_AWS_SECRET_KEY` : New paired secret value (for automation)
  - `TRUFFLEHOG_OLD_AWS_SECRET_KEY` : Old paired secret value (required - will prompt if not set)

**Credential Loading Priority:**
The script loads credentials in the following priority order (highest to lowest):
1. **CLI arguments** (`-k` / `--new-key`) - ⚠️ Insecure (visible in shell history)
2. **Interactive prompts** (`-p` / `--prompt-key`) - ✅ Secure for manual use
3. **Credential loader scripts** (`--credential-loader`) - ✅ Secure, pluggable (NEW)
4. **Environment variables** (`TRUFFLEHOG_NEW_AWS_KEY`) - ⚠️ Visible in process lists
5. **Automatic prompt** - ✅ Secure default if none of above provided

**Pluggable Credential Loaders:**
The script supports pluggable credential loaders that can read credentials from external sources (files, vaults, etc.). Loader scripts are Python modules that define a `load_credentials()` function returning a dictionary with `new_aws_key` and `new_aws_secret_key` keys.

**Default File Loader:**
The script includes a default file-based loader (`scripts/credential-loaders/file_loader.py`) that reads from `~/.secure/trufflehog-aws-keys.sh`:
```bash
export TRUFFLEHOG_NEW_AWS_KEY="AKIA..."
export TRUFFLEHOG_NEW_AWS_SECRET_KEY="wJalr..."
```

**Using Custom Loaders:**
```bash
# Use default file loader (if exists)
./scripts/trufflehog-rotate-aws-key.py -r report.md -i RAW_abc123

# Use custom loader
./scripts/trufflehog-rotate-aws-key.py -r report.md -i RAW_abc123 \
    --credential-loader /path/to/my-loader.py

# Use loader via environment variable
export TRUFFLEHOG_CREDENTIAL_LOADER=/path/to/my-loader.py
./scripts/trufflehog-rotate-aws-key.py -r report.md -i RAW_abc123
```

**Security Note:** Secrets should never be passed via CLI arguments as they appear in shell history and process lists. Use credential loaders or interactive prompts for secure credential handling.

**Providing the Old Paired Secret:**
The old paired secret **must** be provided explicitly. The script will always prompt if not provided:
1. **Explicit Identifier Mode:** Use `--paired-secret-identifier RAW_xxx` if the paired secret has its own identifier in the report
2. **Environment Variable:** Set `TRUFFLEHOG_OLD_AWS_SECRET_KEY` environment variable (recommended for automation)
3. **Interactive Prompt:** The script will automatically prompt you to enter the old paired secret (masked input) if not provided via the above methods

**Note:** Automatic discovery has been disabled due to fragility. The discovery code has been isolated for future development. You must explicitly provide the old paired secret value.

**Providing the New Paired Secret:**
The new paired secret can be provided in two ways:
1. **Environment Variable:** Set `TRUFFLEHOG_NEW_AWS_SECRET_KEY` environment variable (for automation)
2. **Interactive Prompt:** The script will automatically prompt if the environment variable is not set (most secure default for manual use)

**Examples:**

**Single Secret Rotation (Default):**
```bash
# Dry-run mode (make changes without committing)
./scripts/trufflehog-rotate-aws-key.py \
    -r ./trufflehog_report.md \
    -i RAW_abc123_def456 \
    -p \
    --mode dry-run

# Commit mode (automatically commit changes)
./scripts/trufflehog-rotate-aws-key.py \
    -r ./trufflehog_report.md \
    -i RAW_abc123_def456 \
    -k AKIANEWKEYEXAMPLE123 \
    --mode commit

# Resume a previous rotation to commit changes
./scripts/trufflehog-rotate-aws-key.py \
    --resume \
    -i RAW_abc123_def456 \
    --mode commit
```

**Paired Secret Rotation:**
```bash
# Using prompts for both secrets (most secure for manual use)
./scripts/trufflehog-rotate-aws-key.py \
    -r ./trufflehog_report.md \
    -i RAW_abc123_def456 \
    --paired-secret \
    -p \
    --mode dry-run
# Will prompt for:
# - New primary key (if not in env var)
# - New paired secret (if not in env var)
# - Old paired secret (if not in env var)

# Explicit mode using environment variable (when automatic discovery fails)
# Set the old paired secret value via environment variable
export TRUFFLEHOG_OLD_AWS_SECRET_KEY="wJalrXUt...your-old-secret-key"
export TRUFFLEHOG_NEW_AWS_SECRET_KEY="wJalrXUt...your-new-secret-key"
./scripts/trufflehog-rotate-aws-key.py \
    -r ./trufflehog_report.md \
    -i RAW_abc123_def456 \
    --paired-secret \
    -p \
    --mode dry-run \
    --debug

# Explicit mode (when paired secret has its own identifier in report)
./scripts/trufflehog-rotate-aws-key.py \
    -r ./trufflehog_report.md \
    -i RAW_abc123_def456 \
    --paired-secret \
    --paired-secret-identifier RAW_xyz789_uvw012 \
    -p \
    --mode dry-run

# Using environment variables for automation
# Note: Environment variables are visible in process lists, but safer than CLI arguments
export TRUFFLEHOG_NEW_AWS_KEY="AKIANEWKEYEXAMPLE123"
export TRUFFLEHOG_OLD_AWS_SECRET_KEY="wJalrXUt...OLD_SECRET_KEY"
export TRUFFLEHOG_NEW_AWS_SECRET_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYNEWKEY"
./scripts/trufflehog-rotate-aws-key.py \
    -r ./trufflehog_report.md \
    -i RAW_abc123_def456 \
    --paired-secret \
    --mode dry-run

# Using environment variables for both old and new paired secrets (recommended for automation)
export TRUFFLEHOG_OLD_AWS_SECRET_KEY="wJalrXUt...your-old-secret-access-key"
export TRUFFLEHOG_NEW_AWS_SECRET_KEY="wJalrXUt...your-new-secret-access-key"
./scripts/trufflehog-rotate-aws-key.py \
    -r ./trufflehog_report.md \
    -i RAW_abc123_def456 \
    --paired-secret \
    -p \
    --mode dry-run \
    --debug

# Resume paired secret rotation
./scripts/trufflehog-rotate-aws-key.py \
    --resume \
    -i RAW_abc123_def456 \
    --paired-secret \
    --mode commit
```

**How Paired Secret Rotation Works:**

1. **Automatic Discovery Mode (Default):**
   - Script automatically searches for paired secret near primary secret (within ±50 lines in same file)
   - Uses pattern matching to find AWS Secret Access Key patterns (e.g., `AWS_SECRET_ACCESS_KEY=...`, `"secretAccessKey": "..."`)
   - Works when paired secret is in the same file as primary secret
   - If discovery fails, file is skipped with a warning (use explicit mode to handle)

2. **Explicit Mode (Override):**
   - User provides both identifiers: primary secret (`-i`) and paired secret (`--paired-secret-identifier`)
   - Script validates both identifiers exist in the report
   - Works for secrets in same file or different files
   - Use when automatic discovery fails or secrets are in different files
   - State file tracks both secret hashes and discovery method

**Key Features:**
- **Atomic Replacement:** When both secrets are in the same file, they're replaced together with automatic rollback on failure
- **Cross-File Support:** Handles secrets in different files (replaces both, but not atomic across files)
- **Security:** Paired secrets never logged or displayed, uses secure input (getpass), stores only hashes in state files
- **Mode Validation:** Resume mode validates that state file mode matches operation mode (prevents incompatible operations)
- **Extensible:** Designed to support other secret types (username/password, API key/secret, etc.) in the future

**State File Format:**

Single-secret mode state file:
```json
{
    "identifier": "RAW_abc123_def456",
    "old_key_hash": "sha256:...",
    "new_key_hash": "sha256:...",
    "timestamp": "2025-12-24T10:00:00",
    "mode": "dry-run",
    "repositories": [...]
}
```

Paired-secret mode state file:
```json
{
    "identifier": "RAW_abc123_def456",
    "old_key_hash": "sha256:...",
    "new_key_hash": "sha256:...",
    "paired_secret_mode": true,
    "secret_type": "aws",
    "secret_discovery_method": "explicit",
    "paired_secret_identifier": "RAW_xyz789_uvw012",
    "old_paired_secret_hash": "sha256:...",
    "new_paired_secret_hash": "sha256:...",
    "timestamp": "2025-12-24T10:00:00",
    "mode": "dry-run",
    "repositories": [...]
}
```

**Important Notes:**
- Paired secret mode is opt-in via `--paired-secret` flag (single-secret mode is default)
- State files are mode-specific: cannot resume paired-secret state with single-secret mode (and vice versa)
- Secrets are stored as hashes in state files (never plaintext)
- Actual secret values are provided at runtime (CLI args, prompts, or environment variables)

**Dependencies:**
- Python 3.8+
- GitPython (install with: `make install-deps` or `pip install GitPython`)
- Git installed and in PATH
- SSH access to GitHub repositories (SSH keys configured)

**Security:**
- State files stored in `~/.secure/trufflehog-rotate/` with restrictive permissions (600)
- Old keys stored as hashes in state files (not plain text)
- New keys never logged or printed in plain text
- Backup files stored with restrictive permissions (600)
- Supports masked input for new key entry

**Workflow:**
1. Generate trufflehog analysis report using `trufflehog-analyze-results.py`
2. Review the report to identify which keys need rotation
3. Run rotation script in dry-run mode to verify changes
4. Review changes in the created branches
5. Resume with commit mode to commit the changes
6. Create pull requests or push branches as needed

**See also:**
- `docs/design/trufflehog-rotate-aws-key-design.md` - Complete design document
- `docs/reviews/REVIEW-trufflehog-rotate-aws-key.md` - Code review and recommendations

---

## trufflehog-show-raw-results.sh

A utility script to extract raw secret results from trufflehog output files.

**What it does:**
- Scans a directory for trufflehog output files
- Extracts lines containing "Repository:", "File:", and "Raw result:" from all files
- Outputs the extracted information to stdout

**Usage:**
```bash
./scripts/trufflehog-show-raw-results.sh <directory>
```

**Arguments:**
- `<directory>` : Directory containing trufflehog output files (Required)

**Details:**
- Finds all files in the specified directory recursively
- Concatenates all files and filters for relevant lines
- Useful for quickly viewing raw results across multiple scan files

**Example:**
```bash
./scripts/trufflehog-show-raw-results.sh ./scan_results
```

---

## trufflehog-sum-uniq-raw-results.sh

A utility script to count and sum unique raw results from trufflehog output files.

**What it does:**
- Scans trufflehog output files for "Raw result:" lines
- Counts unique occurrences of each raw result
- Masks secret values in output for safety
- Outputs count and sum statistics

**Usage:**
```bash
./scripts/trufflehog-sum-uniq-raw-results.sh <directory>
```

**Arguments:**
- `<directory>` : Directory containing trufflehog output files (Required)

**Details:**
- Filters for files matching a specific timestamp pattern (hardcoded in script)
- Sorts and counts unique raw results
- Masks actual secret values in output
- Outputs count and sum of occurrences

**Note:** This script appears to be a helper script with hardcoded timestamp patterns. It may need customization for your specific use case.

---

## audit-sensitive-data.py

A Python script that audits the repository and git history for sensitive information that should not be committed.

**What it does:**
- Scans all files in the repository for sensitive patterns
- Analyzes git history for sensitive data
- Detects email addresses, GitHub org/repo names, file paths, API keys, tokens, and passwords
- Generates a markdown report with findings
- Excludes known safe patterns (example.com, system paths, etc.)

**Usage:**
```bash
./scripts/audit-sensitive-data.py [-h] [-d DIRECTORY] [-o OUTPUT]
    [--exclude EXCLUDE] [--no-git] [-v] [-q]
```

**Options:**
- `-d, --directory` : Directory to analyze (Default: current directory)
- `-o, --output` : Output markdown file (Default: `sensitive_data_audit_<timestamp>.md`)
- `--exclude EXCLUDE` : Patterns to exclude from analysis (can be used multiple times)
- `--no-git` : Skip git history analysis
- `-v, --verbose` : Verbose output
- `-q, --quiet` : Quiet mode
- `-h, --help` : Show help message

**Details:**
- Scans for email addresses (excluding example/test domains)
- Detects GitHub organization and repository references
- Identifies user-specific file paths (especially `/Users/` paths)
- Finds potential API keys, tokens, and passwords
- Analyzes git history for sensitive data in past commits
- Generates comprehensive markdown report with categorized findings

**Examples:**
```bash
# Audit current directory
./scripts/audit-sensitive-data.py

# Audit specific directory with custom output
./scripts/audit-sensitive-data.py -d ~/projects -o audit_report.md

# Skip git history analysis
./scripts/audit-sensitive-data.py --no-git

# Exclude specific patterns
./scripts/audit-sensitive-data.py --exclude "*.log" --exclude "*.tmp"
```

**Dependencies:**
- Python 3.6+ (uses standard library only: argparse, re, subprocess, sys, collections, datetime, pathlib, typing)

**Security:**
- This script helps identify sensitive data that should not be in the repository
- Use before making repositories public or sharing code
- Review findings carefully and remove or sanitize sensitive data

---

## Complete Workflow Example

```bash
# 1. Run trufflehog scans on local repositories
./scripts/trufflehog-local-git-repos.sh -d ~/repos -o ./scan_results

# 2. Tokenize the results (masks secrets for safe processing)
./scripts/trufflehog-tokenize-secrets.py -d ./scan_results \
    -o ./tokenized_results \
    -l ./secrets_lookup.json

# 3. Analyze the results (works with both tokenized and raw files)
# Option A: Analyze tokenized files
./scripts/trufflehog-analyze-results.py -d ./tokenized_results --org example-org

# Option B: Analyze raw files directly (with confirmation)
./scripts/trufflehog-analyze-results.py -d ./scan_results --org example-org --mode raw

# Option C: Analyze mixed directory (auto-detects both types)
./scripts/trufflehog-analyze-results.py -d ./scan_results --org example-org --mode auto

# 4. Process tokenized files with AI agent or other tools
# (secrets are masked as tokens, safe for external processing)
# ... AI processing happens here ...

# 5. Restore secrets when needed (auto-detects lookup table)
./scripts/trufflehog-detokenize-secrets.py -d ./tokenized_results \
    -o ./restored_results

# 6. Rotate AWS keys found in the analysis (optional)
# First, review the analysis report to identify keys to rotate
./scripts/trufflehog-rotate-aws-key.py \
    -r ./analysis_report.md \
    -i RAW_abc123_def456 \
    -p \
    --mode dry-run

# After reviewing changes, commit them
./scripts/trufflehog-rotate-aws-key.py \
    --resume \
    --mode commit
```

**Important Notes:**
- Keep the lookup table secure - it contains the actual secrets
- If the lookup table is lost, secrets cannot be recovered from tokenized files
- Tokenized files are safe to share or process externally
- The same secret always maps to the same token across all files

---
Created using Google Antigravity.
