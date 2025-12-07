# Record Scripts BATS Tests

Basic BATS tests for all `record*.sh` scripts in the `pub-bin` repository.

## Test Structure

Tests follow the same pattern as `tests/load-ssh-key/`:
- `test_helper.bash` - Main test helper with setup/teardown
- `helpers/` - Helper modules (assertions, record-specific helpers)
- `unit/` - Unit test files
- `run-tests.sh` - Test runner script

Each `record*.sh` script has a corresponding test file in `unit/`:
- `unit/test_record_netstat.bats` - Tests for `network-tools/diagnostics/record-netstat.sh`
- `unit/test_record_uptime.bats` - Tests for `system-tools/record-uptime.sh`
- `unit/test_record_nmap.bats` - Tests for `network-tools/scanning/record-nmap.sh`
- `unit/test_record_nslookup.bats` - Tests for `network-tools/diagnostics/record-nslookup.sh`
- `unit/test_record_network_config.bats` - Tests for `network-tools/diagnostics/record-network-config.sh`
- `unit/test_record_whois.bats` - Tests for `network-tools/intelligence/record-whois.sh`
- `unit/test_record_ip_api_json.bats` - Tests for `network-tools/intelligence/record-ip-api-json.sh`
- `unit/test_record_tcpdump.bats` - Tests for `network-tools/capture/record-tcpdump.sh`
- `unit/test_record_log_show.bats` - Tests for `system-tools/record-log-show.sh`

## Running Tests

### Using the test runner (recommended):
```bash
./tests/record-scripts/run-tests.sh
```

### Run with verbose output:
```bash
./tests/record-scripts/run-tests.sh -v
```

### Run a specific test file:
```bash
bats tests/record-scripts/unit/test_record_netstat.bats
```

### Run all tests directly with bats:
```bash
bats tests/record-scripts/unit/
```

## Test Coverage

Each test file includes:
- ✅ Script existence and executable check
- ✅ Command availability check (skips if command not installed)
- ✅ Basic execution test
- ✅ Output file creation verification
- ✅ Argument validation (for scripts that require arguments)

## Notes

- Tests use temporary directories (`/tmp/test_*.XXXXXX`) for output files
- Tests automatically skip if required commands are not installed
- Some tests may skip if they require special permissions (e.g., `tcpdump` requires sudo)
- `record-log-show.sh` tests are macOS-specific (uses `log` command)

## Dependencies

- `bats` - Bash Automated Testing System
- Various system commands (netstat, uptime, nmap, nslookup, whois, ifconfig, tcpdump, log)

Install BATS:
```bash
# macOS
brew install bats-core

# Linux
# See: https://github.com/bats-core/bats-core#installation
```
