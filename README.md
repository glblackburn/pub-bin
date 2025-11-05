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
- [AI Coding Standards](#ai-coding-standards)
- [Scripts](#scripts)

## Resources

### [tips-and-tricks.md](tips-and-tricks.md)

A collection of useful tips and tricks for common development tasks.

**Contents:**
- Multiple SSH keys for GitHub
- SSH Key Usage Pitfalls
- Apache Infrastructure Downtime Report
- Markdown Viewer Chrome Extension

Refer to [tips-and-tricks.md](tips-and-tricks.md) for detailed instructions on each topic.

## Installation

### Installing cursor-agent

The `start-cursor-agent.sh` script requires the `cursor-agent` command-line tool. Install Cursor IDE from https://cursor.sh/ - the `cursor-agent` command is included with Cursor IDE.

## AI Coding Standards

When AI agents are used to modify or create files in this repository:

- **No trailing spaces**: Do not leave trailing spaces on any line in any file. Trailing whitespace should be removed.
- **Clean up backup files before commits**: Run `./clean-emacs-files.sh` to remove Emacs backup files (files ending with `~`) before creating any commits. This ensures backup files are not accidentally committed to the repository.

## Scripts

- [what-is-left.sh](#what-is-leftsh)
- [shell-template.sh](#shell-templatesh)
- [clean-emacs-files.sh](#clean-emacs-filessh)
- [start-cursor-agent.sh](#start-cursor-agentsh)
- [rename-email.sh](#rename-emailsh)
- [load-ssh-key.sh](#load-ssh-keysh)

### what-is-left.sh

A utility script that helps identify which scripts from the old private repository (`../bin`) have not yet been migrated to this public repository (`pub-bin`).

**What it does:**
- Lists all files in the current `pub-bin` directory (excluding `.git` files)
- Lists all files in the old repository (`../bin`) (excluding `.git` files)
- Performs a diff comparison to show what files exist in the old repository but not in the current one

**Usage:**
```bash
./what-is-left.sh
```

This script is useful during the migration process to track progress and ensure no scripts are missed when migrating from the old repository.

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
- Finds all SSH private keys in `~/.ssh` directory (excludes `.pub`, `known_hosts*`, and `ssh-agent.config`)
- Starts or loads an existing SSH agent configuration
- Checks if each key is already loaded in the agent
- Adds keys to the SSH agent with a timeout (default: 8 hours)
- Verifies keys exist before attempting to load them
- Reports errors if any keys are missing or cannot be loaded

**Usage:**
```bash
. ./load-ssh-key.sh
```
or
```bash
source ./load-ssh-key.sh
```

**Important:** This script must be sourced (using `.` or `source`) to load the SSH agent environment variables into your current shell session.

**Details:**
- **KEY_TIMEOUT**: Default is 28800 seconds (8 hours). Keys are added with this timeout.
- **CONFIG**: SSH agent configuration is stored in `~/.ssh/ssh-agent.config`
- The script automatically finds all private keys in `~/.ssh` directory
- It checks if keys are already loaded before adding them to avoid duplicates
- Returns error code 1 if any keys fail to load

**Behavior:**
1. Checks if SSH agent config exists, loads it if present
2. Starts new SSH agent if config doesn't exist or agent is not running
3. Finds all private keys in `~/.ssh` (excluding public keys and known_hosts)
4. For each key, checks if it's already loaded by comparing fingerprints
5. Adds keys that aren't already loaded to the agent with timeout
6. Reports any errors encountered during the process

This script is useful for automatically loading all SSH keys into your SSH agent session without manually adding each key.

**Related resources:**
- See [SSH Key Usage Pitfalls](tips-and-tricks.md#ssh-key-usage-pitfalls) in [tips-and-tricks.md](tips-and-tricks.md) for information about common SSH key and agent pitfalls.

**TODO - Needed fixes:**
- Add CLI options and usage function
- Add KEY_TIMEOUT CLI option
- Add KEY_LIST CLI option
- Add CONFIG CLI option
