# Trufflehog Tokenized Results Analyzer - Design Document

## Purpose

Create an analysis script that processes tokenized trufflehog output files to generate a summary report. The script will count unique tokens, identify where each token appears (which repositories and files), and generate GitHub URLs for easy navigation to the source locations.

## Use Cases

1. **Token Analysis**: Understand how many unique secrets (tokens) were found across all scans
2. **Location Tracking**: Identify which repositories and files contain each secret
3. **Quick Navigation**: Generate clickable GitHub URLs to view the source code
4. **Reporting**: Create markdown reports for sharing analysis results
5. **Audit Trail**: Document where secrets appear for security review

## Core Requirements

1. **Process Tokenized Files**: Read and parse tokenized trufflehog output files
2. **Extract Token Information**: Identify unique tokens and their locations
3. **Count Occurrences**: Count how many times each token appears (total occurrences)
4. **Count Repositories**: Count how many unique repositories contain each token
5. **Repository Mapping**: Extract repository information from files
6. **File Path Extraction**: Extract file paths from scan results
7. **GitHub URL Generation**: Construct GitHub URLs from repo and file path
8. **Markdown Output**: Generate formatted markdown report with counts prominently displayed
9. **Summary Statistics**: Provide overall counts and statistics

### Key Metrics Per Token

For each token, the script will calculate and display:
- **Occurrence Count**: Total number of times the token appears across all scanned files
- **Repository Count**: Number of unique repositories where the token is found
- **File Count**: Number of unique files containing the token
- **Detector Type**: The detector type that identified this token (e.g., AWS, GitHub, Generic API Key)
  - Each token should have exactly one detector type (multiple types is an error condition)

## Architecture

### Components

1. **Analysis Script** (`trufflehog-analyze-results.py`)
   - Scans tokenized or raw files in a directory
   - Extracts identifier (token or raw hash), repository, and file information
   - Builds data structure mapping identifiers to locations
   - Generates GitHub URLs
   - Supports dual-mode: tokenized files (TOKEN_*) and raw files (actual secrets)
   - Outputs markdown report

2. **Data Structure**
   - Token → List of occurrences
   - Each occurrence: repository, file path, line number (if available)
   - Aggregated statistics

3. **Output Format**
   - Markdown file with sections for:
     - Summary statistics
     - Token details with locations
     - GitHub links

## Data Extraction

### Input File Format

Trufflehog output files contain lines like:
```
✅ Found verified result 🐷🔑
Detector Type: Slack
Decoder Type: PLAIN
Raw result: TOKEN_75b12ada_8f678268
Rotation_guide: https://howtorotate.com/docs/tutorials/slack/
Token_type: Slack Bot Token
Team: Example Team
Name: example_name
Commit: abc123def4567890abcdef1234567890abcdef12
Email: user <user@example.com>
File: src/config/example.py
Line: 55
Repository: file:///path/to/repos/example-repo
Repository_local_path: /tmp/trufflehog-XXXXXXXX
Timestamp: 2024-09-04 15:23:00 +0000
Analyze: Run `trufflehog analyze` to analyze this key's permissions
```

### Information to Extract

1. **Repository Path**: From "Repository:" line
   - Format: `file:///path/to/repos/repo-name` (file:// URI)
   - Example: `file:///path/to/repos/example-repo`
   - Extract repository name: Last component of path (e.g., `example-repo`)
   - Repository name maps to GitHub: `https://github.com/{org}/{repo-name}`

2. **File Path**: From "File:" line
   - Format: `aws/lambdas/file.py` (relative to repo root, no line number)
   - Example: `src/config/example.py`
   - Line number is in separate "Line:" field

3. **Line Number**: From "Line:" field (separate from File path)
   - Format: `55` (integer)
   - Used for GitHub URL line anchor: `#L55`

4. **Token**: From "Raw result:" line
   - Format: `TOKEN_<hash>_<suffix>`
   - Example: `TOKEN_75b12ada_8f678268`
   - This is what we count and track

5. **Detector Type**: From "Detector Type:" line
   - Format: `Slack`, `AWS`, `GitHub`, `Generic API Key`, etc.
   - Example: `Detector Type: Slack`
   - Required for summary table display
   - **IMPORTANT**: The same token should only have ONE detector type
   - If the same token appears with different detector types, this is an error condition

### Parsing Strategy

- Read files line by line
- Track current context as we parse each result block:
  - Repository (from "Repository:" line)
  - File path (from "File:" line)
  - Line number (from "Line:" field)
  - Detector Type (from "Detector Type:" line)
  - Token (from "Raw result:" line)
- Each result block starts with "✅ Found verified result" or similar marker
- When "Raw result:" is found, associate token with current repository/file/line/detector type
- Extract repository name from Repository path (last component after `/repos/` or similar)
- Build token → locations mapping with all context information
- Validate that each token has only one detector type (error if multiple)
- Handle multi-line entries and empty lines between result blocks

## GitHub URL Generation

### Repository Path to GitHub URL

**Challenge**: Map `file://` repository paths from trufflehog output to GitHub URLs.

**Mapping Strategy:**

1. **Extract Repository Name**
   - From `Repository: file:///path/to/repos/repo-name`
   - Extract last component: `repo-name` (e.g., `example-repo`)

2. **Build GitHub URL**
   - Format: `{base_url}{org_name}/{repo_name}/blob/{branch}/{file_path}#L{line}`
   - Example: `https://github.com/example-org/example-repo/blob/dev/src/config/example.py#L55`
   - Components:
     - **Base URL**: `https://github.com/` (default, configurable via `--github-base`)
     - **Org Name**: Must be provided via `--org` or `--repo-map` (e.g., `example-org`)
     - **Repo Name**: Extracted from Repository path
     - **Branch**: Detected from git repo or provided via `--branch` (default: `main` or `dev`)
     - **File Path**: From "File:" field
     - **Line**: From "Line:" field (if present)

3. **Configuration Options**
   - `--org <org_name>`: GitHub organization/user name (required if not in repo-map)
   - `--github-base <url>`: Base GitHub URL (default: `https://github.com/`)
   - `--repo-map <file>`: JSON mapping file for repo-specific org/branch overrides
   - `--branch <branch>`: Default branch to use (default: auto-detect or `main`)

4. **Repository Mapping File Format**
   - JSON file for repo-specific overrides:
   ```json
   {
     "example-repo": {
       "org": "example-org",
       "branch": "dev"
     },
     "another-repo": {
       "org": "differentOrg",
       "branch": "main"
     }
   }
   ```
   - If repo not in map, use `--org` and `--branch` defaults

### URL Format

Example from actual trufflehog output:
- Repository: `file:///path/to/repos/example-repo`
- File: `src/config/example.py`
- Line: `55`
- Org: `example-org`
- Branch: `dev`
- Result: `https://github.com/example-org/example-repo/blob/dev/src/config/example.py#L55`

**URL Components:**
- Base: `https://github.com/` (configurable)
- Org: Provided via `--org` or repo-map
- Repo: Extracted from Repository path
- Branch: Detected or provided via `--branch`
- File: From "File:" field
- Line: From "Line:" field (if present, adds `#L{line}`)

**Branch Detection:**
- Try to detect current branch from local repo if Repository path exists locally: `git rev-parse --abbrev-ref HEAD`
- Fall back to `--branch` CLI option (default branch)
- Final fallback: `main` or `dev` (check which exists)
- Can be overridden per-repo via repo-map file
- **Note**: URLs may be broken if repository state changed since scan (branches renamed, files moved, etc.)
  - This is acceptable given we only have `file://` paths, not git remotes
  - Document this limitation clearly in help text and output

## Output Format

### Markdown Structure

```markdown
# Trufflehog Tokenized Results Analysis

**Generated:** 2025-12-04 18:26:09  
**Source Directory:** /path/to/tokenized_results  
**Files Processed:** 15  
**Unique Tokens:** 42  
**Total Occurrences:** 127

---

## Summary Statistics

- **Total Files Scanned:** 15
- **Total Repositories:** 8
- **Unique Tokens Found:** 42
- **Total Token Occurrences:** 127
- **Average Occurrences per Token:** 3.02

---

## Tokens Summary

A clean summary table with clickable links to detailed token sections below.

| Token | Occurrences | Repositories | Files | Detector Type |
|-------|-------------|--------------|-------|---------------|
| [TOKEN_a3f2b1c4_9e8d7f6a](#token-a3f2b1c4-9e8d7f6a) | 5 | 2 | 3 | AWS |
| [TOKEN_b4c3d2e1_f8a7b6c5](#token-b4c3d2e1-f8a7b6c5) | 3 | 1 | 2 | Generic API Key |
| [TOKEN_c5d4e3f2_a9b8c7d6](#token-c5d4e3f2-a9b8c7d6) | 8 | 3 | 5 | AWS |
| ... | ... | ... | ... | ... |

*Click token names to jump to detailed information. Sorted by occurrence count (descending).*  
*Each token should have exactly one detector type. Multiple types for the same token will be flagged as an error.*

---

## Token Details

### <a id="token-a3f2b1c4-9e8d7f6a"></a>TOKEN_a3f2b1c4_9e8d7f6a
**Occurrences:** 5 (total times this token appears)  
**Repositories:** 2 (number of unique repositories containing this token)  
**Files:** 3 (number of unique files containing this token)  
**Detector Type:** Slack

**Locations:**
1. **Repository:** example-repo
   - **File:** [src/config/example.py:55](https://github.com/example-org/example-repo/blob/dev/src/config/example.py#L55)
   - **Detector:** Slack

2. **Repository:** another-repo
   - **File:** [config/api_keys.json:12](https://github.com/example-org/another-repo/blob/dev/config/api_keys.json#L12)
   - **Detector:** Generic API Key

---

### <a id="token-b4c3d2e1-f8a7b6c5"></a>TOKEN_b4c3d2e1_f8a7b6c5
**Occurrences:** 3 (total times this token appears)  
**Repositories:** 1 (number of unique repositories containing this token)  
**Files:** 2 (number of unique files containing this token)  
**Detector Type:** AWS

**Locations:**
1. **Repository:** example-repo
   - **File:** [src/config/example.py:88](https://github.com/example-org/example-repo/blob/dev/src/config/example.py#L88)
   - **File:** [tests/test_config.py:12](https://github.com/example-org/example-repo/blob/dev/tests/test_config.py#L12)
   - **Detector:** AWS

---

[... more tokens ...]

---

## Repositories Summary

| Repository | Tokens | Files | Occurrences |
|------------|--------|-------|-------------|
| [example-repo](https://github.com/example-org/example-repo) | 15 | 8 | 45 |
| [another-repo](https://github.com/example-org/another-repo) | 8 | 5 | 22 |
| ... | ... | ... | ... |

---

## Files Summary

| File | Repository | Tokens | Occurrences |
|------|------------|--------|-------------|
| src/config/example.py | example-repo | 5 | 12 |
| ... | ... | ... | ... |
```

## CLI Interface

### Script Command

```bash
trufflehog-analyze-results.py [-h] [-v] [-q] [--no-browser]
    -d <directory>
    [-o <output_file>]
    [-p <file_pattern>]
    --org <org_name>
    [--mode {auto,tokenized,raw}]
    [--include-raw-secrets]
    [--skip-raw-confirmation]
    [--branch <branch_name>]
    [--repo-map <mapping_file>]
    [--github-base <base_url>]
```

### Options

- `-d, --directory`: Directory containing trufflehog output files (tokenized or raw) (Required)
- `-o, --output`: Output markdown file path (Default: `/tmp/tokenized_analysis_<timestamp>.md`)
- `-p, --pattern`: File pattern to match (Default: `trufflehog-*.txt`)
- `--org`: GitHub organization/user name (Required)
- `--mode`: Analysis mode: `auto` (detect), `tokenized` (only tokenized files), or `raw` (only raw files) (Default: `auto`)
- `--include-raw-secrets`: Include actual secret values in report (WARNING: Only use if report will be kept secure)
- `--skip-raw-confirmation`: Skip confirmation prompt when raw files are detected (use with caution)
- `--branch`: Default git branch to use in URLs (Default: auto-detect from local repo or 'main')
  - Note: URLs may be broken if repository state changed since scan
- `--repo-map`: JSON file for repo-specific org/branch overrides (Optional)
- `--github-base`: Base GitHub URL (Default: `https://github.com/`)
- `--no-browser`: Do not open report in browser
- `-v, --verbose`: Verbose output
- `-q, --quiet`: Quiet mode
- `-h, --help`: Show help message

### Repository Mapping File Format

JSON file for repo-specific organization and branch overrides:

```json
{
  "example-repo": {
    "org": "example-org",
    "branch": "dev"
  },
  "another-repo": {
    "org": "differentOrg",
    "branch": "main"
  }
}
```

- Key: Repository name (extracted from Repository path)
- `org`: GitHub organization/user (overrides `--org` for this repo)
- `branch`: Git branch (overrides `--branch` for this repo)
- If repo not in map, uses `--org` and `--branch` defaults

### Examples

```bash
# Basic usage with tokenized files (auto-detect)
./trufflehog-analyze-results.py -d ./tokenized_results --org example-org

# Analyze raw files (with confirmation prompt)
./trufflehog-analyze-results.py -d ./raw_results --org example-org --mode raw

# Custom output file and branch
./trufflehog-analyze-results.py -d ./tokenized_results \
    --org example-org \
    --branch dev \
    -o ./analysis_report.md

# Use repo mapping file for repo-specific overrides
./trufflehog-analyze-results.py -d ./tokenized_results \
    --org example-org \
    --repo-map ./repo_mapping.json

# Custom GitHub base URL (for GitHub Enterprise)
./trufflehog-analyze-results.py -d ./tokenized_results \
    --org myOrg \
    --github-base https://github.company.com/

# Verbose output
./trufflehog-analyze-results.py -d ./tokenized_results --org example-org -v
```

## Implementation Details

### Python Dependencies
- `argparse` - CLI argument parsing
- `json` - Repository mapping file parsing
- `pathlib` - Path handling
- `re` - Regular expressions for parsing
- `subprocess` - Git commands (remote, branch detection)
- `datetime` - Timestamp generation
- `collections` - defaultdict, Counter for data structures
- `os` - File operations

### Key Functions

#### Data Extraction
- `parse_tokenized_file(file_path)` - Parse a single tokenized file
  - Returns: List of token occurrences with context (repository, file, token, detector_type)
  - Extracts detector type from "Detector Type:" lines
- `extract_repository_info(repo_path)` - DEPRECATED - No longer needed
  - Repository info comes from trufflehog output and --org parameter
  - No git remote access needed
- `parse_file_line(line)` - Parse individual lines from trufflehog output
- `extract_repository_name(repo_path)` - Extract repo name from file:// URI
  - Input: `file:///path/to/repos/repo-name`
  - Output: `repo-name` (last component)
- `extract_line_number(line_field)` - Extract line number from "Line:" field

#### Data Processing
- `build_token_index(occurrences)` - Build token → locations mapping
- `calculate_token_counts(token_index)` - Calculate occurrence, repository, file counts, and detector types per token
  - **Occurrence count**: Total number of times each token appears across all files
  - **Repository count**: Number of unique repositories where each token is found
  - **File count**: Number of unique files where each token is found
  - **Detector type validation**: Each token should have exactly one detector type
    - If same token has multiple detector types, flag as ERROR
    - If detector type is missing, set to "Unknown"
    - Report error for multiple types and continue processing
- `calculate_statistics(token_index)` - Calculate summary statistics
- `group_by_repository(occurrences)` - Group occurrences by repository
- `build_repository_summary(token_index, repo_map, default_org)` - Build repository summary data
  - Groups tokens by repository
  - Calculates counts per repository (tokens, files, occurrences)
  - Prepares data for repository summary table with GitHub URLs

#### URL Generation
- `extract_repo_name_from_path(repo_path)` - Extract repo name from file:// URI path
- `get_repo_config(repo_name, repo_map, default_org, default_branch)` - Get org/branch for repo
  - Check repo-map first, fall back to defaults
- `build_github_file_url(base_url, org, repo_name, branch, file_path, line_number)` - Build complete GitHub URL
  - Format: `{base_url}{org}/{repo_name}/blob/{branch}/{file_path}#L{line}`
- `detect_branch(repo_path, default_branch, branch_cache)` - Detect current git branch from local repo (if path exists)
  - Check branch_cache first to avoid repeated git commands for same repo
  - Try: `git rev-parse --abbrev-ref HEAD` in repo directory (if path exists locally)
  - Cache result in branch_cache for future lookups
  - Fall back to provided default branch
  - Final fallback: `main` or `dev` (check which exists)
  - **Note**: Uses current branch, which may differ from scan-time branch
  - URLs may be broken if repository state changed - document this limitation

#### Output Generation
- `generate_markdown_report(data, output_path)` - Generate markdown file
- `format_tokens_summary_table(token_index)` - Format clean tokens summary table with clickable links
  - Creates markdown table with token names as links to detailed sections
  - Includes occurrence, repository, file counts, and detector type
  - Each token should have exactly one detector type (validated during processing)
  - Sorted by occurrence count (descending)
- `format_token_section(token, occurrences, counts)` - Format token details section with anchor ID
  - Creates anchor ID for linking: `token-<hash>-<suffix>` (lowercase, hyphens, no TOKEN_ prefix)
  - Includes occurrence, repository, file counts, and detector type in summary
  - Lists all locations with GitHub URLs
- `format_summary_table(repositories)` - Format repository/file summary tables
- `format_repository_summary_table(repositories, base_url, org_map)` - Format repository summary table
  - Creates markdown table with clickable repository names linking to GitHub repo URLs
  - Format: `[repo-name](https://github.com/{org}/{repo-name})`
  - Uses org from repo-map or default --org parameter
  - Includes tokens, files, and occurrences counts
- `create_token_anchor_id(token)` - Generate anchor ID from token
  - Converts `TOKEN_abc123_def456` → `token-abc123-def456` (lowercase, remove TOKEN_ prefix, replace underscores with hyphens for markdown compatibility)

### Data Structures

```python
# Token occurrence
{
    "token": "TOKEN_75b12ada_8f678268",
    "repository_path": "file:///path/to/repos/example-repo",
    "repository_name": "example-repo",
    "file_path": "src/config/example.py",
    "line_number": 55,
    "detector_type": "Slack",
    "org": "example-org",
    "branch": "dev",
    "file_url": "https://github.com/example-org/example-repo/blob/dev/src/config/example.py#L55"
}

# Token index with counts
{
    "TOKEN_a3f2b1c4_9e8d7f6a": {
        "occurrences": [
            {occurrence1},
            {occurrence2},
            ...
        ],
        "occurrence_count": 5,  # Total times token appears
        "repository_count": 2,  # Unique repositories containing token
        "file_count": 3,         # Unique files containing token
        "detector_type": "AWS",  # Single detector type (should be consistent for all occurrences)
        "detector_type_error": false,  # True if multiple detector types found (error condition)
        "detector_type_missing": false  # True if any occurrence is missing detector type
    }
}
```

## Error Handling

1. **Missing Repository Paths**
   - If repository path doesn't exist, skip or warn
   - Continue processing other files

2. **Git Remote Detection Failures** (for branch detection only)
   - If git branch detection fails, use default branch from --branch or repo-map
   - No git remote needed - URLs built from --org and repo name extraction
   - Warn user if branch detection fails (verbose mode)

3. **Invalid File Format**
   - Skip malformed lines
   - Report skipped lines in verbose mode
   - Continue processing

4. **Missing Files**
   - Skip missing files with warning
   - Continue processing

5. **URL Generation Failures**
   - If URL can't be generated, show raw path
   - Mark as "URL not available" in output

6. **Branch Detection Limitations**
   - URLs may be broken if repository state changed since scan
   - Branches may have been renamed, files moved, or repository structure changed
   - This is acceptable given we only have `file://` paths, not git remotes
   - Document this limitation in help text and verbose output

7. **Multiple Detector Types for Same Token**
   - If same token appears with different detector types, flag as ERROR
   - Report error with token and conflicting detector types
   - Continue processing but mark token with error flag
   - Show error indicator in output (e.g., "ERROR: Multiple detector types")

8. **Missing Detector Type**
   - If a token occurrence doesn't have a detector type, show as "Unknown"
   - Continue processing (don't skip)
   - Display "Unknown" in summary table and token details
   - Log warning in verbose mode

## Edge Cases

1. **Multiple Remotes**
   - Use 'origin' remote by default
   - Allow override via config

2. **Non-GitHub Repositories**
   - Detect GitLab, Bitbucket, etc.
   - Support via config file mapping
   - Generic fallback format

3. **Bare Repositories**
   - May not have working directory
   - Use config file for mapping

4. **Submodules**
   - Handle nested repositories
   - Track parent repository context

5. **File Path Variations**
   - Absolute vs relative paths
   - Windows vs Unix paths
   - Handle both formats

6. **Line Number Formats**
   - `file.py:42`
   - `file.py:42:15` (line:column)
   - Extract just line number

## Future Enhancements

1. **Detector Type Grouping**
   - Group tokens by detector type
   - Summary by secret type

2. **Time-based Analysis**
   - Track when tokens were first seen
   - Timeline of secret introductions

3. **Comparison Mode**
   - Compare two analysis runs
   - Show new/removed tokens

4. **Export Formats**
   - CSV export
   - JSON export
   - HTML report

5. **Filtering Options**
   - Filter by repository
   - Filter by file pattern
   - Filter by detector type

6. **Visualization**
   - Generate charts/graphs
   - Repository heatmap

7. **Integration**
   - Link back to lookup table
   - Cross-reference with detokenized files

8. **File Summary Table - Detector Type Column** (Deferred)
   - Evaluate after initial working version
   - Consider adding detector type column to file summary table
   - May be redundant if already shown in token details
   - See design analysis document Issue #10

## Design Decisions

1. **Language**: Python (consistent with tokenization scripts)
2. **Output Format**: Markdown (human-readable, version-controllable)
3. **Git Detection**: Try git remotes first (most accurate)
4. **Branch Detection**: Auto-detect with fallback to 'main'
5. **File Pattern**: Default to `trufflehog-*.txt` (consistent with other scripts)
6. **Non-recursive**: Process only files in specified directory (for now)
7. **Error Tolerance**: Continue processing on errors, report issues

## Questions for Review

1. Should we support recursive directory scanning?
2. Should we include the actual secret values (from lookup table) in the report?
3. How should we handle private/internal GitHub instances?
4. Should we support other git hosting services (GitLab, Bitbucket) natively?
5. What level of detail is needed in the markdown output?
6. Should we generate separate reports per repository?
7. How should we handle very large numbers of tokens (pagination, filtering)?

---

**Status**: Design Phase  
**Created**: 2025-12-04  
**Author**: Design Document
