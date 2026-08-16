# Testing Framework for load-ssh-key.sh

## Overview

This testing framework uses **BATS (Bash Automated Testing System)** to test `load-ssh-key.sh`. BATS is a testing framework written in bash, making it perfect for testing bash scripts.

## Framework Structure

```
tests/load-ssh-key/
├── README.md                 # This file
├── test_helper.bash          # BATS helper functions and setup
├── helpers/                   # Test helper functions
│   ├── assertions.bash       # Custom assertion functions
│   ├── ssh-helpers.bash      # SSH-specific helper functions
│   ├── keepassxc-helpers.bash # Mock keepassxc-cli setup
│   └── mock-keepassxc-cli.sh # Mock keepassxc-cli executable
├── unit/                     # Unit tests
│   ├── test_k_option.bats    # Tests for -k option
│   ├── test_list_option.bats # Tests for -l option
│   ├── test_kill_option.bats # Tests for -K option
│   └── test_keepassxc.bats   # Tests for KeePassXC passphrase lookup
├── integration/              # Integration tests (future)
└── test-runs/               # Test output directory (git-ignored)
    └── YYYYMMDD_HHMMSS/      # Timestamped test run folders
```

## Mocking keepassxc-cli

`test_keepassxc.bats` never touches a real KeePassXC database. `create_mock_keepassxc_cli`
(in `helpers/keepassxc-helpers.bash`) copies `helpers/mock-keepassxc-cli.sh` to
`${TEST_TMPDIR}/mockbin/keepassxc-cli` and prepends that directory to `PATH`. `load-ssh-key.sh`
probes `command -v keepassxc-cli` first, so nothing in the script under test needs a hook.

```bash
local kdbx=$(create_mock_kdbx)                       # empty file; only its existence is checked
create_mock_keepassxc_cli "master-pw" "my_key=key-passphrase"
export LOAD_SSH_KEY_DB_PASSWORD="master-pw"          # supplies the master password without a tty
run_load_ssh_key -k "${key}" -D "${kdbx}" -v
cleanup_mock_keepassxc_cli
```

The mock mimics the real CLI closely enough to be meaningful: it reads the database password from
stdin, supports `db-info -q` (password check) and `show -q -s -a Password <db> <entry>`, and fails
silently with exit code 1 - which is exactly why `load-ssh-key.sh` validates the master password up
front rather than trying to classify per-entry failures. `mock_keepassxc_call_count` asserts the
mock was not called at all (used by the `-N` and unencrypted-key tests).

`LOAD_SSH_KEY_DB_PASSWORD` exists so these tests can run without a controllable terminal. Real use
should rely on the interactive prompt.

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

### Using run-tests.sh (Recommended)

The `run-tests.sh` script provides a convenient interface to run tests with options for filtering, verbose output, and test type selection.

```bash
# Run all unit tests (default)
./tests/load-ssh-key/run-tests.sh

# Run with verbose output
./tests/load-ssh-key/run-tests.sh -v

# Run integration tests
./tests/load-ssh-key/run-tests.sh -i

# Run all tests (unit + integration)
./tests/load-ssh-key/run-tests.sh -a

# Filter tests by pattern
./tests/load-ssh-key/run-tests.sh -f "loads only"

# Show help
./tests/load-ssh-key/run-tests.sh -h
```

**Options:**
- `-h, --help` : Show help message
- `-v, --verbose` : Run tests with verbose output
- `-f, --filter PATTERN` : Run only tests matching PATTERN
- `-u, --unit` : Run unit tests (default)
- `-i, --integration` : Run integration tests
- `-a, --all` : Run all tests (unit + integration)

### Using BATS Directly

You can also run BATS directly if you prefer:

```bash
# Run all unit tests
bats tests/load-ssh-key/unit/

# Run specific test file
bats tests/load-ssh-key/unit/test_k_option.bats

# Run with verbose output
bats -v tests/load-ssh-key/unit/

# Run specific test
bats -f "loads only the specified single key" tests/load-ssh-key/unit/test_k_option.bats
```

## Test Structure

Each test file follows this pattern:

```bash
#!/usr/bin/env bats
# Test file for load-ssh-key.sh -k option

load '../test_helper.bash'

@test "load-ssh-key.sh -k: loads only the specified single key" {
    # Setup
    kill_all_ssh_agents
    local test_key=$(create_test_ssh_key "test_key")
    
    # Execute
    run_load_ssh_key -k "${test_key}" -v
    
    # Assert
    assert_success
    assert_single_key_file_entry
    assert_key_count 1
}
```

## Test Helpers

### Assertions (assertions.bash)

- `assert_success()` - Verify exit code is 0
- `assert_failure()` - Verify exit code is non-zero
- `assert_output_contains <string>` - Verify output contains string
- `assert_key_count <n>` - Verify exactly N keys are loaded
- `assert_key_loaded <name>` - Verify specific key is loaded
- `assert_single_key_file_entry()` - Verify only one key processed
- `assert_find_ssh_keys_not_called()` - Verify auto-discovery not used

### SSH Helpers (ssh-helpers.bash)

- `kill_all_ssh_agents()` - Kill all ssh-agent processes
- `create_test_ssh_key <name> [passphrase]` - Create test SSH key
- `get_loaded_key_count()` - Get count of loaded keys
- `get_loaded_keys()` - Get list of loaded keys
- `is_ssh_agent_running()` - Check if agent is running

## Test Categories

### Unit Tests (in `unit/`)

- Use isolated test environment
- Create temporary SSH keys
- Test script logic, argument parsing, error handling
- Fast and reliable
- No dependency on real SSH keys

### Integration Tests (in `integration/`)

- Use real SSH keys from ~/.ssh
- Test against actual SSH agent behavior
- Verify scripts work with real data
- Marked as optional/skippable if keys missing

## Best Practices

1. **One test file per feature** - Keep tests organized
2. **Use descriptive test names** - `@test "script-name: what it tests"`
3. **Isolate test environment** - Use TEST_TMPDIR for test keys
4. **Test both success and failure** - Cover error paths
5. **Keep tests fast** - Use temporary keys, avoid I/O when possible
6. **Clean up after tests** - Use `teardown()` functions
7. **Use helper functions** - Don't duplicate test logic

## Test Output

Test output is saved to `test-runs/` directory with timestamped folders. Each test run creates a new directory containing:

- Test execution logs
- SSH agent state information
- Key loading verification results

## Test Key Configuration

**Note**: The unit tests (run by `run-tests.sh`) create their own temporary test keys and do **not** require any configuration.

The secure configuration setup is only needed for the **archive scripts** which test with real SSH keys from `~/.ssh/`.

### Setup Test Keys (Archive Scripts Only)

If you want to run the archive test scripts, run the setup script to configure your test keys:

```bash
./tests/load-ssh-key/archive/setup-test-keys-secure.sh
```

This will:
1. Create `~/.secure/` directory (if it doesn't exist) with restrictive permissions
2. Prompt for your test key names
3. Create `~/.secure/load-ssh-key-test-keys.sh` with your configuration
4. Set proper file permissions (chmod 400)

The configuration file exports:
- `TEST_KEY_NO_PASSPHRASE` - Key without passphrase (for basic tests)
- `TEST_KEY_WITH_PASSPHRASE` - Key with passphrase (for passphrase tests)
- `TEST_KEY_2` - Optional additional test key
- `TEST_KEY_3` - Optional additional test key

### Using Test Keys in Archive Scripts

The archive test scripts automatically load the configuration:

```bash
# Load test key configuration
source tests/load-ssh-key/helpers/test-key-config.bash
load_test_key_config

# Get full path to a key
TEST_KEY_PATH=$(get_test_key_path "${TEST_KEY_NO_PASSPHRASE}")

# Use the key
source load-ssh-key.sh -k "${TEST_KEY_PATH}"
```

For more details, see `KEY-CONFIG-RECOMMENDATION.md`.

## Migration Notes

The old shell-based test scripts have been moved to `archive/` directory:
- `test-k-option-single.sh`
- `test-k-option-passphrase.sh`
- `test-k-option-verbose.sh`
- `setup-test-keys-secure.sh` (setup script for archive tests)
- `TESTING-PLAN-load-ssh-key-k-option.md`

These scripts have been updated to use the secure configuration system and are kept for reference. They require real SSH keys from `~/.ssh/` and the secure configuration setup. The main unit tests (run by `run-tests.sh`) do not require this setup as they create their own temporary test keys.
