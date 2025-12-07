# Welcome to the Junk Drawer!

This repository is a collection of utilities that I uses on a daily
basis.  This is a work in progress to migrate scripts from an older
private repository that was not very curated and has quite a bit of
dead code, false starts, and experimental thoughts.  The intention of
this repository is to highlight those scripts that are used regularly.
The last part of the migration will include scripts that are not used
as frequently or no longer used at all.

The idea with the slow migration is to one force a brief description
of each script and two to conduct a review before making public.

I will probably take advantage of AI coding agents to document the
scripts during the migration.  Where an AI agent is used to modify or
create a script, I will specificly note that.

## Table of Contents

- [Resources](#resources)
- [Installation](#installation)
- [Configuration](#configuration)
- [AI Coding Standards](#ai-coding-standards)
- [Scripts](#scripts)

## Resources

### Documentation

- **[tips-and-tricks.md](tips-and-tricks.md)** - Collection of useful tips and tricks for common development tasks
- **[LinkedIn-posts.md](LinkedIn-posts.md)** - Archive of LinkedIn posts documenting project updates and insights
- **[LinkedIn-posts/LinkedIn-style-guide.md](LinkedIn-posts/LinkedIn-style-guide.md)** - Style guide and formatting rules for LinkedIn posts
- **[README-AI-CODING-STANDARDS.md](README-AI-CODING-STANDARDS.md)** - AI coding standards and guidelines

### Category Documentation

- **[network-tools/README.md](network-tools/README.md)** - Network diagnostic, scanning, intelligence, and capture tools
- **[system-tools/README.md](system-tools/README.md)** - System-level monitoring and event logging tools
- **[greynoise/README.md](greynoise/README.md)** - GreyNoise API lookup utilities
- **[trufflehog/README.md](trufflehog/README.md)** - Trufflehog secret scanning scripts
- **[arecibo-message/README.md](arecibo-message/README.md)** - Arecibo Message decoding project
- **[tests/load-ssh-key/README.md](tests/load-ssh-key/README.md)** - BATS test suite documentation for load-ssh-key.sh
- **[tests/record-scripts/README.md](tests/record-scripts/README.md)** - BATS test suite documentation for record*.sh scripts

### [tips-and-tricks.md](tips-and-tricks.md)

A collection of useful tips and tricks for common development tasks.

**Contents:**
- Multiple SSH keys for GitHub
- SSH Key Usage Pitfalls
- Apache Infrastructure Downtime Report
- Markdown Viewer Chrome Extension

Refer to [tips-and-tricks.md](tips-and-tricks.md) for detailed instructions on each topic.

### [LinkedIn-posts.md](LinkedIn-posts.md)

Archive of LinkedIn posts documenting project updates, lessons learned, and technical insights.

**Contents:**
- Posts about script refactoring and improvements
- AI coding assistant experiences and lessons
- Technical project updates and conversions
- Workflow improvements and tooling decisions

Posts are organized by year and month in the `LinkedIn-posts/` directory. See [LinkedIn-posts.md](LinkedIn-posts.md) for the complete post archive with table of contents and quick index.

### [LinkedIn-posts/LinkedIn-style-guide.md](LinkedIn-posts/LinkedIn-style-guide.md)

Style guide and formatting rules for creating LinkedIn posts.

**Contents:**
- Formatting rules (Unicode bold, bullets, trailing spaces)
- URL and file name handling (zero-width spaces)
- Post structure and workflow
- Tone and writing style guidelines
- Verification checklist

Refer to [LinkedIn-posts/LinkedIn-style-guide.md](LinkedIn-posts/LinkedIn-style-guide.md) for complete formatting and style guidelines.

## Installation

### Installing cursor-agent

The `start-cursor-agent.sh` script requires the `cursor-agent` command-line tool. Install Cursor IDE from https://cursor.sh/ - the `cursor-agent` command is included with Cursor IDE.

## Configuration

### [config/config.sh](config/config.sh)

A modular configuration library for pub-bin scripts that provides generic interactive setup and config management.

**What it provides:**
- Generic config loading from `~/.config/pub-bin/config`
- Secure config support from `~/.secure/secure-config.sh`
- Generic interactive setup functions for any config variable
- Config value saving that preserves existing values

**Configuration Files:**
- **Public config**: `~/.config/pub-bin/config` - General configuration values
- **Secure config**: `~/.secure/secure-config.sh` - Sensitive data (API keys, etc.)

**Functions:**

**Config Loading:**
- `load-config [noerror]` - Load public config file
- `load-secure-config [noerror]` - Load secure config file
- `load-all-configs [noerror]` - Load both public and secure configs

**Interactive Setup:**
- `setup-config-value <var_name> <description> <default_value> <required>` - Generic interactive setup for any config variable
  - Shows section headers with separators
  - Displays current value in brackets format
  - Interactive prompts with description
  - Handles required/optional validation
  - Expands ~ paths automatically
  - Outputs prompts to stderr, returns value via stdout
- `save-config-value <var_name> <value>` - Save config value while preserving other values

**Utilities:**
- `ensure-config-dir` - Ensure config directory exists with proper permissions
- `ensure-secure-dir` - Ensure secure directory exists with proper permissions
- `show-config` - Display current config values (non-sensitive)

**Usage in Scripts:**
```bash
#!/usr/bin/env bash
. ${script_dir}/config/config.sh

# Load configs
load-config "noerror"

# Interactive setup if config missing
if [ -z "${my_config_var:-}" ] ; then
    my_config_var=$(setup-config-value "my_config_var" \
        "Description of what this config does" \
        "default_value" \
        "true")
    save-config-value "my_config_var" "${my_config_var}"
    load-config "noerror"
fi
```

This library provides a reusable pattern for any script needing configuration management with interactive setup capabilities. Scripts will automatically prompt for configuration when needed.

## AI Coding Standards

This repository follows standardized AI coding standards. See [README-AI-CODING-STANDARDS.md](README-AI-CODING-STANDARDS.md) for the complete set of rules and guidelines.

The standards include:
- Core Standards (Code Quality, Git Operations, File Creation, Verification)
- General Principles (Readability, Error Handling, DRY, Defensive Programming)
- Bash-Specific Standards (Function Organization, Variable Usage, Error Handling, Code Structure, Best Practices, Script Patterns)
- Common Patterns (Function, Error Handling, Validation)

Refer to [README-AI-CODING-STANDARDS.md](README-AI-CODING-STANDARDS.md) for detailed guidelines.

## Scripts

- [what-is-left.py](#what-is-leftpy)
- [shell-template.sh](#shell-templatesh)
- [clean-emacs-files.sh](#clean-emacs-filessh)
- [start-cursor-agent.sh](#start-cursor-agentsh)
- [rename-email.sh](#rename-emailsh)
- [load-ssh-key.sh](#load-ssh-keysh)
- [fix-spaces-in-filename.sh](#fix-spaces-in-filenamesh)
- [fix-spaces-in-filenames.sh](#fix-spaces-in-filenamessh)
- [check-ai-readmes.sh](#check-ai-readmesh)
- [monitor-ai-agent-progress.sh](#monitor-ai-agent-progresssh)
- [clean-screenshots.sh](#clean-screenshotssh)
- [azure/show-location-authenticationDetails.sh](#azureshow-location-authenticationdetailssh)
- [greynoise/greynoise-lookup.sh](#greynoisegreynoise-lookupsh)
- [trufflehog/trufflehog-local-git-repos.sh](#trufflehogtrufflehog-local-git-repossh)

### what-is-left.py

A Python utility script that provides a color-coded comparison of files between the old private repository (`../bin`) and the current public repository (`pub-bin`). It helps track migration progress and identifies files that need attention.

**What it does:**
- Discovers files in both `pub-bin` and `../bin` directories (with smart filtering)
- Analyzes git history to detect moved files
- Categorizes files into four states with color coding:
  - 🔴 **RED**: Files in both places (need fixing/removal from old repo)
  - 🟡 **YELLOW**: Files to migrate (exist only in old bin)
  - 🟢 **GREEN**: Successfully migrated (detected via git history)
  - 🔵 **BLUE**: New files in pub-bin (not in old repo)
- Filters out non-essential files (cache, images, docs, etc.)
- Provides summary statistics and progress tracking
- Categorizes files by type (scripts, executables, makefiles, configs, other)

**Requirements:**
- Python 3.8+
- `rich` library: `pip install rich`
- Optional: `GitPython` for better git history analysis: `pip install GitPython`

**Usage:**
```bash
./what-is-left.py
```

**Options:**
- `--verbose`: Show verbose output including errors
- `--quiet`: Show summary statistics only
- `--no-new`: Hide new files in pub-bin section
- `--old-bin PATH`: Path to old bin directory (default: `../bin`)
- `--pub-bin PATH`: Path to pub-bin directory (default: `.`)

**Example output:**
The script displays a beautiful color-coded summary with:
- Migration status summary with statistics
- Files in both places (RED) - need fixing
- Files to migrate (YELLOW) - categorized by type
- Successfully migrated files (GREEN) - with move dates
- New files in pub-bin (BLUE)

This script is essential during the migration process to track progress, identify duplicates, and ensure no scripts are missed when migrating from the old repository.

**Note:** The original `what-is-left.sh` bash script has been replaced by this Python implementation, which provides enhanced features including color-coded output, git history analysis, and migration tracking.

### shell-template.sh

A comprehensive bash script template that demonstrates common patterns and best practices for writing bash scripts.

**What it demonstrates:**
- CLI parameter parsing using `getopts` with options for help, quiet, verbose, test mode, AWS profile, and region
- Usage function with formatted help output
- Terminal colors using `tput` commands
- Math operations using `let` command
- Array operations and string splitting (CSV parsing)
- File operations including temporary directories and files with cleanup traps
- Error handling patterns and exit code checking
- Date/time formatting for various use cases (timestamps, Excel-compatible formats, epoch time)
- Input/output patterns (reading secure input, confirmation prompts, reading from commands into arrays)
- Formatting output using `printf` for aligned columns
- Setting terminal window title
- System bell notifications

**Usage:**
```bash
./shell-template.sh [-hqtv] [-p <aws_profile>] [-r <region>]
```

**Options:**
- `-h` : Display help message
- `-p <aws_profile>` : AWS Profile (Default: default-aws-profile)
- `-r <region>` : AWS region (Default: default-region)
- `-q` : Quiet mode (output as little as possible)
- `-t` : Test mode (do not perform actual operations)
- `-v` : Verbose output (may contain sensitive data)

This template serves as a reference for implementing common bash scripting patterns and can be copied and modified when creating new scripts.

### clean-emacs-files.sh

A utility script to find and optionally remove Emacs backup files (files ending with `~`) from the current directory and subdirectories.

**What it does:**
- Searches for all files ending with `~` in the current directory tree using `find`
- Prompts the user for confirmation before deleting any files
- Removes the backup files only if the user confirms with 'y'

**Usage:**
```bash
./clean-emacs-files.sh
```

**Behavior:**
1. Lists all files matching the pattern `*~` in the current directory and subdirectories
2. Prompts: "remove these? [y/n]"
3. If 'y' is entered, removes all matching files
4. If anything else is entered, displays "NOT REMOVED" and exits without deleting files

This script is useful for cleaning up Emacs backup files that accumulate during editing sessions.

### start-cursor-agent.sh

A convenience script to resume a specific Cursor AI agent chat session using the `cursor-agent` command-line tool.

**What it does:**
- Resumes a Cursor AI agent chat session with a predefined session ID
- Uses the `cursor-agent` command with the `--resume` option

**Usage:**
```bash
./start-cursor-agent.sh
```

**Details:**
- The script runs `cursor-agent --resume=<session-id>` where `<session-id>` is a specific chat session identifier
- This allows you to quickly resume a previous conversation with the Cursor AI agent without needing to remember or type the full command each time

This script is useful for quickly continuing work with a specific Cursor AI agent session.

### rename-email.sh

A utility script to rename email files by extracting the Date header and prefixing the filename with a formatted timestamp.

**What it does:**
- Takes an email file as a command-line argument
- Extracts the `Date:` header from the email
- Parses the date and formats it as `YYYY-MM-DD_HHMMSS`
- Replaces spaces in the filename with underscores
- Renames the file with the date prefix: `{date}_{original_filename}`

**Usage:**
```bash
./rename-email.sh <email_file>
```

**Details:**
- The script uses `gdate` (GNU date command) to parse the email date header
- Spaces in the filename are replaced with underscores for better compatibility
- Requires GNU coreutils (typically installed via Homebrew on macOS)

This script is useful for organizing email files chronologically by their sent/received date.

**TODO - Needed fixes:**
- Fix path handling bug: Extract directory and basename separately, normalize spaces only in basename, then reconstruct full path
- Add argument validation: Check if argument is provided
- Add file existence check: Verify the email file exists before processing
- Add Date header validation: Check if Date header exists in the email
- Fix sed pattern: Change `[A-z]` to `[A-Za-z]` (correct ASCII character range)
- Add dependency check: Verify `gdate` is available before using it
- Remove unused variables: `script_name` and `script_dir` are set but never used
- Add usage/help function: Display usage information when no arguments provided or with `-h` flag
- Improve error handling: Add better error messages and handling for edge cases

### load-ssh-key.sh

A utility script to automatically load SSH keys from `~/.ssh` into the SSH agent.

**What it does:**
- Finds all SSH private keys in `~/.ssh` directory (excludes `.pub`, `known_hosts*`, `ssh-agent.config`, `config`, `config~`, `authorized_keys`, and `ssh-copy-id.*` directories)
- Starts or loads an existing SSH agent configuration
- Checks if each key is already loaded in the agent by comparing fingerprints
- Adds keys to the SSH agent with a configurable timeout (default: 8 hours)
- Validates keys before attempting to load them (skips non-key files gracefully)
- Supports loading specific keys or auto-detecting all keys
- Can kill existing agent and start a new one
- Can list currently loaded keys
- Reports errors if any keys are missing or cannot be loaded

**Usage:**
```bash
. ./load-ssh-key.sh [options]
```
or
```bash
source ./load-ssh-key.sh [options]
```

**Important:** This script must be sourced (using `.` or `source`) to load the SSH agent environment variables into your current shell session. The `-l` option can be used when executed directly (without sourcing).

**Options:**
- `-h` : Display help message
- `-t <timeout>` : Key timeout in seconds (Default: 28800)
- `-d <dir>` : SSH directory to search for keys (Default: `~/.ssh`)
- `-c <config>` : SSH agent config file path (Default: `~/.ssh/ssh-agent.config`)
- `-k <key_list>` : Comma-separated list of specific keys to load (Default: auto-detect all)
- `-K` : Kill current SSH agent and start a new one
- `-l` : List currently loaded SSH keys and exit (works when sourced or executed directly)
- `-q` : Quiet mode. Output as little as possible.
- `-v` : Verbose output. Show detailed information.

**Examples:**
```bash
# Load all keys with default timeout
. ./load-ssh-key.sh

# Load all keys with custom timeout (1 hour)
. ./load-ssh-key.sh -t 3600

# Load only specific keys
. ./load-ssh-key.sh -k ~/.ssh/id_ed25519,~/.ssh/id_rsa

# Kill current agent and reload all keys
. ./load-ssh-key.sh -K

# List currently loaded keys (can be executed directly)
./load-ssh-key.sh -l

# Verbose mode to see detailed processing
. ./load-ssh-key.sh -v
```

**Details:**
- **KEY_TIMEOUT**: Default is 28800 seconds (8 hours). Keys are added with this timeout.
- **CONFIG**: SSH agent configuration is stored in `~/.ssh/ssh-agent.config`
- The script automatically finds all private keys in `~/.ssh` directory when `-k` is not specified
- It validates keys using `ssh-keygen -l` before attempting to load them
- It checks if keys are already loaded by comparing fingerprints to avoid duplicates
- Returns error code 1 if any keys fail to load
- The `-K` option kills all existing ssh-agent processes and starts a new one
- The `-l` option works when sourced or executed directly, detecting dead agents gracefully

**Behavior:**
1. Parses CLI options (timeout, directory, config, key list, kill agent, list keys, quiet, verbose)
2. If `-l` option: Lists currently loaded keys and exits
3. If `-K` option: Kills all existing ssh-agent processes, then continues
4. Checks if SSH agent config exists, loads it if present
5. Starts new SSH agent if config doesn't exist or agent is not running
6. If `-k` specified: Loads only the specified keys (comma-separated list)
7. If `-k` not specified: Finds all private keys in `~/.ssh` (excluding public keys, known_hosts, config files)
8. For each key, validates it's a real SSH key file
9. For each valid key, checks if it's already loaded by comparing fingerprints
10. Adds keys that aren't already loaded to the agent with timeout
11. Reports any errors encountered during the process

This script is useful for automatically loading SSH keys into your SSH agent session without manually adding each key, with support for selective key loading and agent management.

**Related resources:**
- See [SSH Key Usage Pitfalls](tips-and-tricks.md#ssh-key-usage-pitfalls) in [tips-and-tricks.md](tips-and-tricks.md) for information about common SSH key and agent pitfalls.
- See [tests/load-ssh-key/README.md](tests/load-ssh-key/README.md) for testing framework documentation.

### fix-spaces-in-filename.sh

A utility script to rename a single file by replacing non-alphanumeric characters (except dots, slashes, and hyphens) with underscores.

**What it does:**
- Takes a single file path as a command-line argument
- Validates that the file exists and is a regular file
- Replaces non-alphanumeric characters (except `.`, `/`, and `-`) with underscores
- Renames the file only if the new name differs from the original
- Displays verbose output when VERBOSE is set to true

**Usage:**
```bash
./fix-spaces-in-filename.sh <file>
```

**Details:**
- The script uses `sed` to replace characters that are not alphanumeric, dots, slashes, or hyphens with underscores
- It validates the file exists before processing
- Only renames the file if the new name is different from the original
- Supports verbose mode (though VERBOSE variable is not currently exposed via CLI)

**Example:**
```bash
./fix-spaces-in-filename.sh "my file name.txt"
# Renames to: my_file_name.txt
```

This script is useful for normalizing filenames by removing spaces and special characters.

### fix-spaces-in-filenames.sh

A utility script to process multiple files and remove spaces from their filenames by calling `fix-spaces-in-filename.sh` for each file.

**What it does:**
- Processes multiple files either from a directory or from stdin
- Finds files with spaces in their names
- Calls `fix-spaces-in-filename.sh` for each file to rename it
- Can process a directory recursively or read file paths from stdin

**Usage:**
```bash
# Process all files with spaces in a directory
./fix-spaces-in-filenames.sh <directory>

# Process files from stdin (e.g., from find command)
find . -type f | grep " " | ./fix-spaces-in-filenames.sh
```

**Details:**
- If a directory is provided as an argument, it finds all files with spaces in that directory
- If no argument is provided, it reads file paths from stdin
- Validates that the directory exists if a directory argument is provided
- Uses `fix-spaces-in-filename.sh` to handle the actual renaming of each file

**Example:**
```bash
# Process all files with spaces in current directory
./fix-spaces-in-filenames.sh .

# Process specific files from find command
find . -type f -name "*.txt" | grep " " | ./fix-spaces-in-filenames.sh
```

This script is useful for batch processing multiple files to normalize their filenames by removing spaces and special characters.

### check-ai-readmes.sh

A utility script to find README files that contain AI coding standards and check their git status across multiple repositories.

**What it does:**
- Searches for all `README*.md` files in `~/data` directory tree
- Filters for files containing "ai " (case-insensitive) and "commit" (case-insensitive)
- Excludes files with "third-party" in the path
- For each matching file, displays the file path and directory
- Runs `git status` in each file's directory to check repository status

**Usage:**
```bash
./check-ai-readmes.sh
```

**Details:**
- The script searches recursively through `~/data` for README files
- It uses `grep` to filter files that mention both "ai" and "commit" (indicating AI coding standards)
- For each matching file, it shows the full path and runs `git status` in that directory
- This helps identify repositories that have AI coding standards documented

**Example output:**
The script will list all README files that contain AI coding standards, showing:
- Full file path
- Directory path
- Git status for each repository

This script is useful for finding and reviewing AI coding standards across multiple projects to ensure consistency.

### monitor-ai-agent-progress.sh

A monitoring script to track AI agent activity by watching working directory files, git changes, and git status with audio feedback.

**What it does:**
- Runs in an infinite loop
- Monitors working directory: counts files and directories in working/scratch directory (default: `/tmp`) and speaks the count with status
- Monitors git changes: counts lines in `git diff` and speaks the count with status
- Monitors git status: counts files with changes (modified, added, deleted, untracked) and speaks the count with status
- Tracks status changes: displays "new", "increasing", "decreasing", or "stable" for all three metrics
- Displays timestamp at the start of each monitoring cycle (always shown, even in quiet mode)
- Configurable update interval (default: 60 seconds)
- Supports quiet and verbose modes
- Optional repository name display in diff and status output (off by default)
- Configurable working directory path

**Usage:**
```bash
./monitor-ai-agent-progress.sh [-hqrv] [-i <interval>] [-t <working_dir>]
```

**Options:**
- `-h` : Display help message
- `-i <interval>` : Update interval in seconds (Default: 60)
- `-q` : Quiet mode (disables audio feedback only, timestamp still shown)
- `-r` : Show repository name in diff and status output
- `-t <dir>` : Working/scratch directory to monitor (Default: `/tmp`)
- `-v` : Verbose output (shows startup configuration with markers)

**Details:**
- Uses `say` command to provide audio feedback for all three metrics combined in a single announcement (prevents audio overlap)
- Tracks status by comparing current counts with previous values:
  - "new" on first run
  - "increasing" when count goes up
  - "decreasing" when count goes down
  - "stable" when count remains the same
- Output format: Column-aligned with centered status values:
  - `work:   <count> (<centered_status>) (<working_dir_path>)`
  - `diff:   <count> (<centered_status>)` or `diff:   <count> (<centered_status>) (<repo_name>)` with `-r` flag
  - `status: <count> (<centered_status>)` or `status: <count> (<centered_status>) (<repo_name>)` with `-r` flag
- All three metrics are displayed and spoken together in one combined message
- Timestamp is always shown at the start of each monitoring cycle
- Updates at configurable intervals (default: 60 seconds)
- Uses `find` to count files and directories in working directory (handles symlinks properly)
- Provides real-time monitoring of AI agent activity through working directory file creation, git changes, and file status
- Follows shell-template.sh patterns: proper error handling, CLI options, functions, and structure

**Examples:**
```bash
# Default: 60 second interval, monitor /tmp
./monitor-ai-agent-progress.sh

# 30 second interval
./monitor-ai-agent-progress.sh -i 30

# Quiet mode with 120 second interval (no audio, timestamp still shown)
./monitor-ai-agent-progress.sh -q -i 120

# Show repository name in diff and status output
./monitor-ai-agent-progress.sh -r

# Monitor different working directory
./monitor-ai-agent-progress.sh -t ~/scratch

# Verbose mode with repository name, custom working dir, and custom interval
./monitor-ai-agent-progress.sh -v -r -t /var/tmp -i 30
```

This script is useful for monitoring AI agent progress when working on long-running tasks, providing audio feedback so you can track activity without constantly watching the terminal. The status tracking helps you understand whether activity is increasing, decreasing, or stable. All three metrics are announced together in a single audio message to prevent overlap.

### clean-screenshots.sh

A utility script to clean up screenshot files from Desktop (or specified source directory) by moving them to an archived directory organized by timestamp.

**What it does:**
- Searches for screenshot files matching a pattern (default: `Screen*`) in the source directory
- Moves screenshots to a timestamped archive directory (e.g., `screenshot_dir/2025-11-11_123456/`)
- Provides detailed output showing files found, moved, and archived
- Supports dry run mode to preview changes without making them
- Uses interactive configuration setup if `screenshot_dir` is not configured

**Usage:**
```bash
./clean-screenshots.sh [-hn] [-d <screenshot_dir>] [-s <src_dir>] [-p <prefix>]
```

**Options:**
- `-h` : Display help message
- `-d <dir>` : Screenshot archive directory (overrides config)
- `-s <dir>` : Source directory to search (Default: `~/Desktop`)
- `-p <prefix>` : Screenshot filename prefix pattern (Default: `Screen*`)
- `-n` : Dry run mode (show what would be done without making changes)

**Configuration:**
- The script uses `screenshot_dir` from `~/.config/pub-bin/config`
- If not configured, the script will prompt interactively to set it up
- Configuration is set up interactively when the script runs if not already configured

**Details:**
- Archive directories are created with timestamp format: `YYYY-MM-DD_HHMMSS`
- Shows detailed output including:
  - Configuration and initialization variables
  - Files found matching the pattern
  - Files moved with `ls -l` details
  - Archive directory listing after move
- Follows shell-template.sh patterns: proper error handling, CLI options, functions, and structure

**Examples:**
```bash
# Default: Move screenshots from Desktop to configured archive directory
./clean-screenshots.sh

# Dry run to see what would be moved
./clean-screenshots.sh -n

# Override archive directory
./clean-screenshots.sh -d ~/Pictures/Screenshots

# Search different source directory
./clean-screenshots.sh -s ~/Downloads

# Custom screenshot pattern
./clean-screenshots.sh -p "Screenshot*"
```

This script is useful for keeping your Desktop clean by automatically organizing screenshots into timestamped archive directories.

### azure/show-location-authenticationDetails.sh

A utility script to process Azure Entra ID user Sign-in log JSON downloads and extract authentication details including location and success status.

**What it does:**
- Processes JSON files downloaded from Azure Entra ID Sign-in logs
- Extracts specific fields: `createdDateTime`, `userPrincipalName`, `ipAddress`, `location.city`, `location.state`, `location.country`, and `authenticationDetails[].succeeded`
- Outputs data in multiple formats: table (default), CSV, or JSON
- Validates input file exists, is readable, and contains valid JSON
- Checks for required dependencies (`jq`, `column`)

**Usage:**
```bash
./azure/show-location-authenticationDetails.sh [-hqv] [-f <file>] [-o <format>] [<file>]
```

**Options:**
- `-h` : Display help message
- `-f <file>` : Input JSON file (required if not provided as positional argument)
- `-o <format>` : Output format: `table`, `csv`, or `json` (Default: `table`)
- `-q` : Quiet mode (output as little as possible)
- `-v` : Verbose output (shows detailed processing information)

**Arguments:**
- `<file>` : Input JSON file (alternative to `-f` option)

**Details:**
- Uses `jq` to extract and format data from Azure Entra ID Sign-in log JSON files
- Default output format is a formatted table using `column -t` for alignment
- CSV format outputs sorted comma-separated values
- JSON format reconstructs the data as a structured JSON array
- Validates JSON structure before processing
- Checks for required dependencies and provides helpful error messages

**Examples:**
```bash
# Process Sign-in log with default table format
./azure/show-location-authenticationDetails.sh -f InteractiveSignIns_2023-03-02_2023-03-09.json

# Process with positional argument
./azure/show-location-authenticationDetails.sh InteractiveSignIns_2023-03-02_2023-03-09.json

# Output as CSV
./azure/show-location-authenticationDetails.sh -f signins.json -o csv

# Verbose mode with JSON output
./azure/show-location-authenticationDetails.sh -f signins.json -o json -v

# Quiet mode
./azure/show-location-authenticationDetails.sh -f signins.json -q
```

**Dependencies:**
- `jq` - Required for JSON processing (install with `brew install jq`)
- `column` - Optional, used for table formatting (typically pre-installed on macOS/Linux)

This script is useful for analyzing Azure Entra ID Sign-in logs to review authentication attempts, locations, and success/failure status. The formatted output makes it easy to identify patterns in sign-in activity.

### greynoise/greynoise-lookup.sh

A utility script to query the GreyNoise Community API for IP address threat intelligence information.

**What it does:**
- Queries GreyNoise Community API for IP address information
- Provides threat intelligence data including classification, noise status, and metadata
- Validates IP address format and octet ranges
- Handles HTTP status codes appropriately (200, 404, 429, 4xx, 5xx)
- Provides clear error messages for different failure scenarios

**Usage:**
```bash
./greynoise/greynoise-lookup.sh [-hqv] <ip_address>
```

**Options:**
- `-h` : Display help message
- `-q` : Quiet mode (output as little as possible)
- `-v` : Verbose output (shows detailed request information)

**Arguments:**
- `<ip_address>` : IP address to query (required)

**Details:**
- Uses GreyNoise Community API (no API key required)
- Validates IP address format (IPv4 dotted decimal notation)
- Validates each octet is in range 0-255
- Handles rate limiting (HTTP 429) with appropriate error messages
- Handles not found (HTTP 404) gracefully
- Provides verbose output showing API URL and request details
- Follows shell-template.sh patterns: proper error handling, CLI options, functions, and structure

**Examples:**
```bash
# Query Google DNS IP
./greynoise/greynoise-lookup.sh 8.8.8.8

# Verbose mode
./greynoise/greynoise-lookup.sh -v 192.168.1.1

# Quiet mode
./greynoise/greynoise-lookup.sh -q 1.1.1.1
```

**Dependencies:**
- `curl` - Required for API requests (typically pre-installed on macOS/Linux)

This script is useful for quickly checking IP addresses against GreyNoise's threat intelligence database to determine if an IP is associated with malicious activity, scanning, or other security concerns.

### trufflehog/trufflehog-local-git-repos.sh

A utility script to recursively find and scan git repositories for secrets using Trufflehog.

See [trufflehog/README.md](trufflehog/README.md) for full documentation.

