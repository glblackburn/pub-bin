# Trufflehog AWS Key Rotation Script - Design Document

## Purpose

Create a script to automatically rotate AWS keys found in trufflehog analysis reports. The script will:
- Parse a trufflehog-analyze-results.py markdown report
- Identify all repositories and file locations for a given identifier
- Checkout each repository
- Create timestamped branches
- Replace the old AWS key with a new key value
- Optionally commit changes or leave them uncommitted for verification
- Support resume mode to continue from where it left off

## Use Cases

1. **Automated Rotation**: Rotate an AWS key across all repositories where it's found
2. **Verification Mode**: Make changes without committing, allowing manual review
3. **Resume Mode**: Continue rotation after pausing to verify changes
4. **Selective Rotation**: Rotate a specific identifier (useful when multiple keys are found)
5. **Limited Rotation**: Process a subset of repositories first (using `-l` limit) for testing or staged rollout

## Requirements

### Core Functionality

1. **Report Parsing**
   - Parse markdown report from `trufflehog-analyze-results.py`
   - Extract identifier details (TOKEN_* or RAW_*)
   - Extract GitHub browser URLs from file links (format: `https://github.com/org/repo/blob/branch/file#L42`)
   - Convert browser URLs to SSH clone format: `git@github.com:org/repo.git`
   - Extract file paths and line numbers from URLs
   - Extract actual secret value (for RAW_ identifiers) or use lookup table (for TOKEN_)

2. **Repository Operations**
   - Clone repositories from GitHub using SSH format: `git@github.com:org/repo.git`
   - Clone to temporary working directory (or reuse existing clone)
   - Create timestamped branch: `rotate-aws-key-<identifier-short>-<timestamp>`
   - Verify repository is clean before making changes
   - Handle SSH authentication (use existing SSH keys)
   - Support both fresh clones and existing local clones

3. **Key Replacement**
   - Locate the key in the file (using line number and context)
   - Replace old key with new key value
   - Handle multiple occurrences in same file
   - Preserve file formatting and context

4. **Commit Management**
   - **Dry-run mode**: Make changes but don't commit (for verification)
   - **Commit mode**: Automatically commit changes
   - **Resume mode**: Commit previously made changes (from dry-run)

5. **Progress Tracking**
   - Track which repositories have been processed
   - Track which files have been modified
   - Store state for resume functionality
   - Generate summary report

### Security Considerations

1. **Key Handling**
   - Never log or print the new key value in plain text
   - Prompt for new key securely (masked input or environment variable)
   - Clear sensitive data from memory when possible
   - Store state file with restricted permissions (600)

2. **Repository Access**
   - Verify user has write access to repositories
   - Handle authentication gracefully
   - Don't store credentials in state file

3. **State File Security**
   - Store state in secure location: `~/.secure/trufflehog-rotate/`
   - Create `~/.secure/` directory if it doesn't exist with `chmod 700`
   - Create `~/.secure/trufflehog-rotate/` subdirectory with `chmod 700`
   - Use restrictive file permissions (600) for state files
   - Encrypt sensitive data in state file (optional but recommended)

## Architecture

### Components

1. **Report Parser**
   - Parse markdown report
   - Extract identifier information
   - Build data structure: `{identifier: {repositories: [...], files: [...], locations: [...]}}`

2. **Repository Manager**
   - Handle repository checkout/cloning
   - Branch creation and management
   - Git status verification
   - Path resolution (file:// to local path)

3. **Key Replacer**
   - File content modification
   - Pattern matching and replacement
   - Context-aware replacement (handle different formats)
   - Backup original files

4. **State Manager**
   - Track rotation progress
   - Store state for resume
   - Generate progress reports

5. **CLI Interface**
   - Argument parsing
   - Interactive prompts
   - Progress display
   - Error handling

### Data Structures

```python
# Identifier data structure
identifier_data = {
    'identifier': 'RAW_abc123_def456',
    'secret_value': 'AKIAIOSFODNN7EXAMPLE',  # For RAW_ identifiers
    'detector_type': 'AWS',
    'occurrences': [
        {
            'repository_url': 'git@github.com:org/repo1.git',  # SSH clone URL
            'repository_name': 'repo1',
            'organization': 'org',
            'file_path': 'config/aws.json',
            'line_number': 42,
            'branch': 'main',  # Extracted from browser URL
            'file_url': 'https://github.com/org/repo1/blob/main/config/aws.json#L42',  # Original browser URL
            'local_clone_path': '/tmp/trufflehog-rotate/org-repo1'  # Where repo is cloned
        },
        # ... more occurrences
    ]
}

# Rotation state structure
rotation_state = {
    'identifier': 'RAW_abc123_def456',
    'old_key': 'AKIAIOSFODNN7EXAMPLE',
    'new_key_hash': 'sha256:...',  # Hash for verification, not actual key
    'timestamp': '2025-12-17T14:30:00',
    'mode': 'dry-run',  # or 'commit'
    'work_dir': '/tmp/trufflehog-rotate',  # Working directory for clones
    'repositories': [
        {
            'repository_url': 'git@github.com:org/repo1.git',
            'repository_name': 'repo1',
            'organization': 'org',
            'local_clone_path': '/tmp/trufflehog-rotate/org-repo1',
            'branch_name': 'rotate-aws-key-abc123-20251217-143000',
            'base_branch': 'main',  # Branch extracted from URL
            'status': 'completed',  # or 'pending', 'failed', 'skipped'
            'files_modified': ['config/aws.json'],
            'changes_committed': False,
            'commit_hash': None  # Set when committed
        },
        # ... more repositories
    ]
}
```

## Implementation Language Recommendation

**Recommended: Python 3.8+**

**Rationale:**
1. **Consistency**: Existing trufflehog scripts are in Python
2. **Libraries**: Rich ecosystem for markdown parsing, git operations, file handling
3. **Maintainability**: Easy to maintain alongside existing codebase
4. **Cross-platform**: Works on Linux, macOS, Windows
5. **Git Integration**: `GitPython` library for robust git operations
6. **Markdown Parsing**: `markdown` or `mistune` for parsing reports
7. **Security**: `getpass` for secure password/key input, `keyring` for credential storage

**Alternative Consideration:**
- **Bash/Shell**: Could work but would be more complex for markdown parsing and git operations
- **Go**: Good performance but less consistent with existing codebase

## CLI Design

### Command Structure

```bash
trufflehog-rotate-aws-key.py [-hqv] [-r <report_file>] [-i <identifier>] [-k <new_key>] [-l <limit>] [OPTIONS]
```

### Options

```bash
  -h               : Display this help message.
  -r <report_file> : Path to trufflehog-analyze-results.py markdown report (Required)
  -i <identifier>  : Identifier to rotate (TOKEN_* or RAW_*) (Required)
  -k <new_key>     : New AWS key value (Required, or use -p for prompt)
  -l <limit>       : Limit number of repositories to process (Default: 0 = all)
  -p               : Prompt for new key interactively (masked input)
  -q               : Quiet mode. Output as little as possible.
  -v               : Verbose output (may contain sensitive data. DO NOT use when logging output.)

  --lookup-table <file>
    Path to secrets lookup table (required for TOKEN_ identifiers)

  --mode {dry-run,commit}
    Operation mode: dry-run (make changes, don't commit) or commit (commit changes) (Default: dry-run)

  --resume
    Resume a previous rotation operation (reads from state file)

  --state-file <file>
    Path to state file for resume functionality (Default: ~/.secure/trufflehog-rotate/<identifier>-<timestamp>.json)

  --branch-prefix <prefix>
    Prefix for branch names (Default: rotate-aws-key)

  --commit-message <message>
    Custom commit message (Default: "Rotate AWS key: <identifier>")

  --skip-repos <repo1,repo2,...>
    Comma-separated list of repository names to skip

  --only-repos <repo1,repo2,...>
    Comma-separated list of repository names to process (process only these)

  --verify-changes
    After making changes, show diff and prompt for confirmation before commit

  --work-dir <dir>
    Working directory for cloning repositories (Default: /tmp/trufflehog-rotate)

  --clone-dir <dir>
    Directory within work-dir to clone repositories (Default: <work-dir>/repos)

  --reuse-clones
    Reuse existing clones if found in work-dir (update instead of fresh clone)

  --backup-dir <dir>
    Directory to store backup copies of modified files (Default: ~/.secure/trufflehog-rotate/backups)
```

### Workflow Examples

#### Example 1: Dry-run mode (verify before commit)

```bash
# Step 1: Make changes without committing
./trufflehog-rotate-aws-key.py \
    -r ./trufflehog_report.md \
    -i RAW_abc123_def456 \
    -p \
    --mode dry-run \
    --verify-changes

# Step 2: Review changes, then resume to commit
./trufflehog-rotate-aws-key.py \
    --resume \
    --mode commit
```

#### Example 2: Direct commit mode

```bash
./trufflehog-rotate-aws-key.py \
    -r ./trufflehog_report.md \
    -i RAW_abc123_def456 \
    -k AKIANEWKEYEXAMPLE123 \
    --mode commit
```

#### Example 3: Rotate tokenized identifier (requires lookup table)

```bash
./trufflehog-rotate-aws-key.py \
    -r ./trufflehog_report.md \
    -i TOKEN_abc123_def456 \
    --lookup-table ./secrets_lookup.json \
    -k AKIANEWKEYEXAMPLE123 \
    --mode dry-run
```

#### Example 4: Limit to first 5 repositories

```bash
./trufflehog-rotate-aws-key.py \
    -r ./trufflehog_report.md \
    -i RAW_abc123_def456 \
    -k AKIANEWKEYEXAMPLE123 \
    -l 5 \
    --mode dry-run
```

#### Example 5: Quiet mode with limit (for automation)

```bash
./trufflehog-rotate-aws-key.py \
    -r ./trufflehog_report.md \
    -i RAW_abc123_def456 \
    -k AKIANEWKEYEXAMPLE123 \
    -l 10 \
    -q \
    --mode commit
```

## Implementation Details

### Report Parsing

**Approach:**
1. Parse markdown using regex or markdown parser
2. Find identifier section: `### <a id="..."></a>IDENTIFIER (Type)`
3. Extract "Raw Secret Value" line for RAW_ identifiers
4. Parse "Locations" section to extract:
   - Repository name from "Repository:" line
   - File URLs from markdown links: `[file:line](https://github.com/org/repo/blob/branch/file#L42)`
   - Extract organization, repository, branch, file path, and line number from URL
   - Convert browser URL to SSH clone URL: `https://github.com/org/repo` → `git@github.com:org/repo.git`

**URL Conversion:**
- Input: `https://github.com/org/repo/blob/branch/file#L42`
- Extract: `org`, `repo`, `branch`, `file`, `line_number`
- Output: `git@github.com:org/repo.git`

**Regex Patterns:**
```python
# Identifier section header
IDENTIFIER_HEADER = r'^### <a id="[^"]+"></a>(TOKEN_|RAW_)(\S+) \((Tokenized|Raw)\)'

# Raw secret value
RAW_SECRET_PATTERN = r'\*\*Raw Secret Value:\*\* `([^`]+)`'

# GitHub browser URL pattern
GITHUB_URL_PATTERN = r'https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/([^#]+)#L(\d+)'

# Location entry with file URL
LOCATION_PATTERN = r'(\d+)\. \*\*Repository:\*\* (\S+)\s+.*?\*\*File:\*\* \[([^\]]+)\]\((https://github\.com/[^\)]+)\)\s+\*\*Detector:\*\* (\S+)'

# Convert browser URL to SSH clone URL
def convert_to_ssh_url(browser_url: str) -> str:
    """
    Convert https://github.com/org/repo/blob/branch/file#L42
    to git@github.com:org/repo.git
    """
    match = re.match(r'https://github\.com/([^/]+)/([^/]+)/', browser_url)
    if match:
        org, repo = match.groups()
        return f'git@github.com:{org}/{repo}.git'
    return None
```

### Repository Operations

**Clone and Branch Process:**
1. Convert browser URL to SSH clone URL: `git@github.com:org/repo.git`
2. Determine local clone path: `<work-dir>/repos/<org>-<repo>`
3. Check if repository already cloned:
   - If `--reuse-clones` and clone exists: Update existing clone (fetch, pull)
   - Otherwise: Clone fresh repository
4. Verify SSH access (test `git ls-remote git@github.com:org/repo.git`)
5. Clone repository to local path
6. Check if repository is clean (no uncommitted changes)
7. Fetch latest changes from remote
8. Checkout base branch (extracted from URL, default: main)
9. Create timestamped branch: `rotate-aws-key-<short-id>-<YYYYMMDD-HHMMSS>`
10. Checkout new branch

**Repository Limit Processing:**
- If `-l <limit>` is specified, process only the first N repositories
- Limit applies to the list of repositories found in the report
- Repositories are processed in the order they appear in the report
- Limit is applied before any filtering (skip-repos, only-repos)
- State file tracks total repositories vs. processed count

**SSH Authentication:**
- Use existing SSH keys from `~/.ssh/`
- Support SSH agent forwarding
- Verify access before cloning
- Handle authentication errors gracefully

**Branch Naming:**
- Format: `rotate-aws-key-<identifier-short>-<timestamp>`
- Example: `rotate-aws-key-abc123-20251217-143000`
- Short identifier: First 6-8 characters after TOKEN_/RAW_ prefix

### Key Replacement

**Replacement Strategy:**
1. Read file content
2. Locate line(s) containing the key:
   - Use line number from report as starting point
   - Search for key pattern in surrounding context (±5 lines)
   - Handle multiple formats:
     - `AWS_ACCESS_KEY_ID=AKIA...`
     - `"accessKeyId": "AKIA..."`
     - `access_key: AKIA...`
     - Plain key on line
3. Replace old key with new key:
   - Preserve surrounding context
   - Maintain formatting (quotes, spacing, etc.)
   - Handle multiple occurrences in same file
4. Write modified content
5. Create backup copy (optional but recommended)

**Pattern Matching:**
```python
# Common AWS key patterns
AWS_KEY_PATTERNS = [
    r'(AWS_ACCESS_KEY_ID\s*[=:]\s*["\']?)' + re.escape(old_key) + r'(["\']?)',
    r'("accessKeyId"\s*:\s*["\']?)' + re.escape(old_key) + r'(["\']?)',
    r'("access_key"\s*:\s*["\']?)' + re.escape(old_key) + r'(["\']?)',
    r'(access_key\s*[=:]\s*["\']?)' + re.escape(old_key) + r'(["\']?)',
    # Plain key (as fallback)
    re.escape(old_key)
]
```

### State Management

**State File Location:**
- Default: `~/.secure/trufflehog-rotate/<identifier>-<timestamp>.json`
- Example: `~/.secure/trufflehog-rotate/RAW_abc123_def456-20251217-143000.json`

**Secure Directory Setup (following ~/.secure pattern):**
```python
# Setup secure directory structure
secure_dir = Path.home() / '.secure'
trufflehog_rotate_dir = secure_dir / 'trufflehog-rotate'
backup_dir = trufflehog_rotate_dir / 'backups'

# Create directories with restrictive permissions
secure_dir.mkdir(mode=0o700, exist_ok=True)
trufflehog_rotate_dir.mkdir(mode=0o700, exist_ok=True)
backup_dir.mkdir(mode=0o700, exist_ok=True)

# Set file permissions when creating files
# State files: chmod 600 (owner read/write only)
# Backup files: chmod 600 (owner read/write only)
```

**Note:** Unlike credential storage scripts, this uses `~/.secure/trufflehog-rotate/` for output files (state files and backups) rather than input credentials. The same security pattern applies: restrictive directory (700) and file (600) permissions.

**State File Structure:**
```json
{
    "identifier": "RAW_abc123_def456",
    "old_key": "AKIAIOSFODNN7EXAMPLE",
    "new_key_hash": "sha256:...",
    "timestamp": "2025-12-17T14:30:00",
    "mode": "dry-run",
    "report_file": "/path/to/report.md",
    "work_dir": "/tmp/trufflehog-rotate",
    "repositories": [
        {
            "repository_url": "git@github.com:org/repo1.git",
            "repository_name": "repo1",
            "organization": "org",
            "local_clone_path": "/tmp/trufflehog-rotate/repos/org-repo1",
            "branch_name": "rotate-aws-key-abc123-20251217-143000",
            "base_branch": "main",
            "status": "completed",
            "files_modified": ["config/aws.json"],
            "changes_committed": false,
            "commit_hash": null,
            "backup_files": ["~/.secure/trufflehog-rotate/backups/org-repo1-config-aws.json"]
        }
    ],
    "summary": {
        "total_repositories": 5,
        "completed": 3,
        "pending": 2,
        "failed": 0,
        "skipped": 0
    }
}
```

**Resume Process:**
1. Load state file (specified or auto-detected)
2. Identify repositories with `status: "pending"` or `changes_committed: false`
3. Apply limit (`-l`) if specified (process only first N pending repositories)
4. For each pending repository:
   - Verify local clone still exists
   - Verify branch still exists
   - Check if changes are still present
   - If in commit mode, commit changes
   - Update state file

### Error Handling

**Error Scenarios:**
1. **Repository not found/accessible**: Skip with warning, continue to next
2. **SSH authentication fails**: Prompt user to check SSH keys, skip repository
3. **Clone fails**: Mark as failed, continue to next
4. **Repository not clean**: Prompt user to clean or skip
5. **Branch already exists**: Use existing branch or create with suffix
6. **Key not found in file**: Warn and skip file, continue
7. **Git operation fails**: Rollback changes, mark as failed
8. **Permission denied**: Skip repository, log error
9. **Invalid URL format**: Skip with error message
10. **Network issues during clone**: Retry with exponential backoff, then skip

**Rollback Strategy:**
- Keep backup copies of all modified files
- On error, restore from backup
- Mark repository as failed in state file
- Continue with next repository

### Progress Reporting

**Output Format:**
```
Processing AWS key rotation for identifier: RAW_abc123_def456
Old key: AKIAIOSFODNN7EXAMPLE
New key: ******** (hidden)

Repositories found in report: 10
Repositories to process: 5 (limited by -l 5)
─────────────────────────────────────────────────────────

[1/5] Processing org/repo1...
  ✓ Converted URL: git@github.com:org/repo1.git
  ✓ Cloned repository to: /tmp/trufflehog-rotate/repos/org-repo1
  ✓ Created branch: rotate-aws-key-abc123-20251217-143000
  ✓ Modified file: config/aws.json (line 42)
  ✓ Changes made (not committed - dry-run mode)

[2/5] Processing org/repo2...
  ✓ Converted URL: git@github.com:org/repo2.git
  ✓ Cloned repository to: /tmp/trufflehog-rotate/repos/org-repo2
  ✓ Created branch: rotate-aws-key-abc123-20251217-143000
  ✓ Modified file: .env (line 10)
  ✓ Changes made (not committed - dry-run mode)

...

Summary:
  Total repositories in report: 10
  Repositories processed: 5 (limited by -l 5)
  Completed: 5
  Failed: 0
  Skipped: 0
  Remaining: 5 (not processed due to limit)

State saved to: ~/.secure/trufflehog-rotate/RAW_abc123_def456-20251217-143000.json

To commit changes, run:
  ./trufflehog-rotate-aws-key.py --resume --mode commit

To process remaining repositories, run:
  ./trufflehog-rotate-aws-key.py --resume -l 5
```

## Security Best Practices

1. **Key Input**
   - Use `getpass.getpass()` for interactive input (masked)
   - Support environment variable: `TRUFFLEHOG_NEW_AWS_KEY`
   - Never log or print key values
   - Clear key from memory when done

2. **State File**
   - Store in secure location: `~/.secure/trufflehog-rotate/`
   - Set permissions: 600 (owner read/write only)
   - Don't store actual new key, only hash for verification
   - Encrypt sensitive data (optional enhancement)

3. **Backup Files**
   - Store in secure location
   - Set restrictive permissions
   - Clean up old backups (configurable retention)

4. **Git Operations**
   - Verify user has write access before attempting changes
   - Don't store credentials in state file
   - Use existing git credentials/SSH keys

## Testing Strategy

### Unit Tests
- Report parsing (various markdown formats)
- Key pattern matching (different file formats)
- State file serialization/deserialization
- Branch name generation

### Integration Tests
- Full rotation workflow (dry-run mode)
- Resume functionality
- Error handling scenarios
- Multiple repositories

### Manual Testing
- Test with real trufflehog reports
- Test with various repository structures
- Test with different AWS key formats
- Test resume functionality

## Future Enhancements

1. **Multi-key Rotation**: Rotate multiple identifiers in one run
2. **Key Validation**: Verify new key is valid before rotation
3. **Automated Testing**: Run tests after key rotation
4. **Pull Request Creation**: Create PRs instead of direct commits
5. **Rollback Functionality**: Automated rollback on failure
6. **Notification**: Send notifications on completion/failure
7. **Audit Logging**: Detailed audit trail of all operations
8. **Parallel Processing**: Process multiple repositories in parallel
9. **Key Format Detection**: Auto-detect key format in files
10. **Interactive Mode**: Interactive selection of repositories to process

## Dependencies

### Python Packages
- `GitPython` (>=3.1.0): Git operations
- `markdown` or `mistune`: Markdown parsing
- `pyyaml` (optional): YAML file support
- `cryptography` (optional): State file encryption

### System Requirements
- Python 3.8+
- Git installed and in PATH
- SSH access to GitHub repositories (SSH keys configured)
- Sufficient disk space for cloning repositories (temporary)
- Network access to GitHub

## File Structure

```
trufflehog-rotate-aws-key.py          # Main script
trufflehog-rotate-aws-key-design.md   # This design document
~/.secure/                            # Secure directory (chmod 700)
  └── trufflehog-rotate/             # Rotation state and backups (chmod 700)
      ├── RAW_abc123_def456-20251217-143000.json  # State file (chmod 600)
      └── backups/                    # Backup files (chmod 700)
          ├── org-repo1-config-aws.json  # Backup file (chmod 600)
          └── org-repo2-.env          # Backup file (chmod 600)
/tmp/trufflehog-rotate/              # Working directory (default)
  └── repos/                         # Cloned repositories
      ├── org-repo1/
      └── org-repo2/
```

**Directory Permissions:**
- `~/.secure/`: `700` (owner read/write/execute only)
- `~/.secure/trufflehog-rotate/`: `700` (owner read/write/execute only)
- `~/.secure/trufflehog-rotate/backups/`: `700` (owner read/write/execute only)

**File Permissions:**
- State files: `600` (owner read/write only)
- Backup files: `600` (owner read/write only)

## Implementation Phases

### Phase 1: Core Functionality
1. Report parsing
2. Repository checkout and branch creation
3. Key replacement in files
4. Basic CLI interface

### Phase 2: State Management
1. State file creation and management
2. Resume functionality
3. Progress tracking

### Phase 3: Error Handling & Security
1. Comprehensive error handling
2. Rollback functionality
3. Security hardening
4. Backup management

### Phase 4: Polish & Testing
1. Comprehensive testing
2. Documentation
3. User experience improvements
4. Performance optimization

## Open Questions

1. **Key Format Detection**: Should we auto-detect key format or require user specification?
   - **Recommendation**: Auto-detect with fallback to exact match

2. **Multiple Occurrences**: How to handle same key appearing multiple times in same file?
   - **Recommendation**: Replace all occurrences, show count in output

3. **Commit Message**: Standardized format or customizable?
   - **Recommendation**: Customizable with sensible default

4. **State File Cleanup**: Automatic cleanup of old state files?
   - **Recommendation**: Manual cleanup with optional retention policy

5. **Tokenized Identifiers**: How to handle TOKEN_ identifiers without lookup table?
   - **Recommendation**: Require lookup table, fail gracefully with clear error

6. **Remote Repository Handling**: Support for remote repositories or local only?
   - **Recommendation**: Remote GitHub repositories via SSH (git@github.com format)
   - **Implementation**: Clone repositories to temporary working directory

## Success Criteria

1. ✅ Successfully parse trufflehog report and extract identifier information
2. ✅ Checkout repositories and create branches
3. ✅ Replace AWS keys in files accurately
4. ✅ Support dry-run mode (changes without commit)
5. ✅ Support resume mode to commit changes
6. ✅ Handle errors gracefully with rollback
7. ✅ Maintain security best practices
8. ✅ Provide clear progress reporting
9. ✅ Generate comprehensive state files
10. ✅ Work with both RAW_ and TOKEN_ identifiers

---

**Design Status**: Complete  
**Recommended Language**: Python 3.8+  
**Estimated Implementation Time**: 2-3 days for core functionality, 1 week for full implementation with testing
