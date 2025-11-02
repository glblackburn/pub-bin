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

## AI Coding Standards

When AI agents are used to modify or create files in this repository:

- **No trailing spaces**: Do not leave trailing spaces on any line in any file. Trailing whitespace should be removed.

## Scripts

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
