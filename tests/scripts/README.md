# Testing Framework for General Scripts

## Overview

This testing framework uses **BATS (Bash Automated Testing System)** to test various scripts in the repository that don't have their own dedicated test directories.

## Framework Structure

```
tests/scripts/
├── README.md                 # This file
├── test_helper.bash          # BATS helper functions and setup
├── helpers/                   # Test helper functions
│   └── assertions.bash       # Custom assertion functions
├── unit/                     # Unit tests
│   ├── test_clean_emacs_files.bats
│   ├── test_clean_screenshots.bats
│   ├── test_check_ai_readmes.bats
│   ├── test_fix_spaces_in_filename.bats
│   ├── test_fix_spaces_in_filenames.bats
│   ├── test_greynoise_lookup.bats
│   ├── test_google_example_lookup.bats
│   ├── test_monitor_ai_agent_progress.bats
│   ├── test_rename_email.bats
│   ├── test_show_location_authentication_details.bats
│   ├── test_sort_netstat_tcp.bats
│   ├── test_start_cursor_agent.bats
│   └── test_trufflehog_local_git_repos.bats
└── test-runs/               # Test output directory (git-ignored)
    └── YYYYMMDD_HHMMSS/      # Timestamped test run folders
```

## Installation

### Install BATS

```bash
# macOS
brew install bats-core

# Linux (Ubuntu/Debian)
sudo apt-get install bats

# Or install from source
git clone https://github.com/bats-core/bats-core.git
cd bats-core
sudo ./install.sh /usr/local
```

### Verify Installation

```bash
bats --version
```

## Running Tests

### Using BATS Directly

```bash
# Run all unit tests
bats tests/scripts/unit/

# Run specific test file
bats tests/scripts/unit/test_clean_screenshots.bats

# Run with verbose output
bats -v tests/scripts/unit/

# Run specific test
bats -f "script exists" tests/scripts/unit/test_clean_screenshots.bats
```

## Test Structure

Each test file follows this pattern:

```bash
#!/usr/bin/env bats
# Test file for script-name.sh

load '../test_helper.bash'

@test "script-name.sh: script exists and is executable" {
    local script_path=$(get_script_path "script-name.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "script-name.sh: has valid bash syntax" {
    skip_if_command_missing "bash"
    local script_path=$(get_script_path "script-name.sh")
    run bash -n "${script_path}"
    assert_success
}

@test "script-name.sh: help option works" {
    run_script "script-name.sh" -h
    assert_success
    assert_output_contains "Usage:"
}
```

## Test Helpers

### Assertions (assertions.bash)

- `assert_success()` - Verify exit code is 0
- `assert_failure()` - Verify exit code is non-zero
- `assert_output_contains <string>` - Verify output contains string
- `assert_file_exists <path>` - Verify file exists
- `assert_file_contains <path> <string>` - Verify file contains string
- `assert_file_not_empty <path>` - Verify file is not empty

### Utility Functions (test_helper.bash)

- `get_script_path <script>` - Get absolute path to script
- `run_script <script> [args...]` - Run a script
- `command_exists <cmd>` - Check if command exists
- `skip_if_command_missing <cmd>` - Skip test if command doesn't exist
- `skip_if_not_macos()` - Skip test if not on macOS

## Test Categories

### Unit Tests (in `unit/`)

- Test script existence and executability
- Test bash syntax validation
- Test help/usage output
- Test basic functionality
- Test error handling
- Use isolated test environment with temporary directories
- Fast and reliable

## Best Practices

1. **One test file per script** - Keep tests organized
2. **Use descriptive test names** - `@test "script-name: what it tests"`
3. **Isolate test environment** - Use TEST_TMPDIR for test files
4. **Test both success and failure** - Cover error paths
5. **Keep tests fast** - Use temporary files, avoid I/O when possible
6. **Clean up after tests** - Use `teardown()` functions
7. **Use helper functions** - Don't duplicate test logic
8. **Skip tests when dependencies missing** - Use `skip_if_command_missing`

## Test Output

Test output is saved to `test-runs/` directory with timestamped folders. Each test run creates a new directory containing:

- Test execution logs
- Temporary test files
- Script output files

## Tested Scripts

The following scripts have BATS tests:

- `clean-emacs-files.sh` - Remove emacs backup files
- `clean-screenshots.sh` - Archive screenshots
- `check-ai-readmes.sh` - Check AI-related READMEs
- `file-tools/fix-spaces-in-filename.sh` - Fix spaces in single filename
- `file-tools/fix-spaces-in-filenames.sh` - Fix spaces in multiple filenames
- `greynoise-lookup.sh` - Query GreyNoise API
- `google-example-lookup.sh` - Example GreyNoise lookup
- `monitor-ai-agent-progress.sh` - Monitor AI agent activity
- `rename-email.sh` - Rename email files by date
- `azure/show-location-authenticationDetails.sh` - Process Azure logs
- `network-tools/diagnostics/sort-netstat-tcp.sh` - Sort netstat TCP output
- `start-cursor-agent.sh` - Start Cursor agent
- `trufflehog/trufflehog-local-git-repos.sh` - Run Trufflehog on git repos
