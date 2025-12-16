# Trufflehog Script Implementation Plan

## Goal Description
Create a Bash script `trufflehog-local-git-repos.sh` to recursively find and scan git repositories within a target directory using `trufflehog`.

## User Review Required
> [!IMPORTANT]
> - **Script Name**: `trufflehog-local-git-repos.sh`
> - **Logic**: Recursively finds `.git` directories to identify repositories.
> - **Output**: Saves output to a single file in the target directory named `trufflehog-<directory_name>-<timestamp>.txt`.
> - **Style**: Strictly follows `shell-template.sh` patterns (getopts, error handling, logging).

## Proposed Changes

### Trufflehog Directory
#### [NEW] [trufflehog-local-git-repos.sh](file:///path/to/trufflehog/trufflehog-local-git-repos.sh)
- **Language**: Bash
- **CLI Parameters**:
    - `-d <directory>`: Target directory to scan (Required).
- **Implementation Details**:
    - Use `find` to locate `.git` directories.
    - Iterate over found repositories.
    - Run `trufflehog filesystem` on each repo.
    - Redirect output to the log file.
    - Log file naming: `trufflehog-$(basename target_dir)-$(date +%Y%m%d_%H%M%S).txt`.

## Verification Plan

### Automated Tests
- **Syntax**: `bash -n trufflehog/trufflehog-local-git-repos.sh`
- **Standards**: `grep -n '[[:space:]]$' trufflehog/trufflehog-local-git-repos.sh`

### Manual Verification
1.  **Test Run**:
    ```bash
    ./trufflehog/trufflehog-local-git-repos.sh -d /path/to/target/directory
    ```
2.  **Verify**: Check that multiple `trufflehog-*.txt` files appear in the target directory, one for each repo found.

---
Created using Google Antigravity.
