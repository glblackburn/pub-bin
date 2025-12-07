#!/usr/bin/env bash
# Test runner for record*.sh tests

set -eu

################################################################################
# Script Setup
################################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="${SCRIPT_DIR}"
UNIT_TEST_DIR="${TEST_DIR}/unit"
INTEGRATION_TEST_DIR="${TEST_DIR}/integration"

################################################################################
# Configuration
################################################################################

BATS_CMD="bats"
VERBOSE=false
TEST_PATTERN=""
RUN_UNIT=true
RUN_INTEGRATION=false

################################################################################
# Usage
################################################################################

usage() {
    cat<<EOF
Usage: $0 [OPTIONS]

Run BATS tests for record*.sh scripts

Options:
  -h, --help          Show this help message
  -v, --verbose       Run tests with verbose output
  -f, --filter PATTERN  Run only tests matching PATTERN
  -u, --unit          Run unit tests (default)
  -i, --integration   Run integration tests
  -a, --all           Run all tests (unit + integration)
  --bats PATH         Path to bats executable (default: bats)

Examples:
  $0                  # Run all unit tests
  $0 -v               # Run all unit tests with verbose output
  $0 -i               # Run integration tests
  $0 -a               # Run all tests (unit + integration)
  $0 -f "netstat"     # Run only tests matching "netstat"
  $0 --bats /usr/local/bin/bats  # Use custom bats path
EOF
}

################################################################################
# Parse Arguments
################################################################################

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -f|--filter)
            TEST_PATTERN="$2"
            shift 2
            ;;
        -u|--unit)
            RUN_UNIT=true
            RUN_INTEGRATION=false
            shift
            ;;
        -i|--integration)
            RUN_UNIT=false
            RUN_INTEGRATION=true
            shift
            ;;
        -a|--all)
            RUN_UNIT=true
            RUN_INTEGRATION=true
            shift
            ;;
        --bats)
            BATS_CMD="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage
            exit 1
            ;;
    esac
done

################################################################################
# Check Dependencies
################################################################################

# Check if bats is installed
if ! command -v "${BATS_CMD}" >/dev/null 2>&1; then
    echo "Error: bats is not installed or not in PATH" >&2
    echo "" >&2
    echo "Installation:" >&2
    echo "  macOS:   brew install bats-core" >&2
    echo "  Linux:   sudo apt-get install bats" >&2
    echo "  Source:  https://github.com/bats-core/bats-core" >&2
    exit 1
fi

################################################################################
# Find Test Files
################################################################################

find_test_files() {
    if [ "$RUN_UNIT" = true ] && [ -d "$UNIT_TEST_DIR" ]; then
        find "$UNIT_TEST_DIR" -name "*.bats" -type f | sort
    fi
    
    if [ "$RUN_INTEGRATION" = true ] && [ -d "$INTEGRATION_TEST_DIR" ]; then
        find "$INTEGRATION_TEST_DIR" -name "*.bats" -type f | sort
    fi
}

################################################################################
# Main
################################################################################

main() {
    echo "=========================================="
    echo "record*.sh Test Suite"
    echo "=========================================="
    echo ""
    echo "BATS version: $(${BATS_CMD} --version)"
    echo "Test directory: ${TEST_DIR}"
    if [ "$RUN_INTEGRATION" = true ] && [ "$RUN_UNIT" = true ]; then
        echo "Mode: All Tests (Unit + Integration)"
    elif [ "$RUN_INTEGRATION" = true ]; then
        echo "Mode: Integration Tests"
    else
        echo "Mode: Unit Tests (Default)"
    fi
    echo ""
    
    # Find all test files
    local test_files=()
    while IFS= read -r file; do
        [ -n "$file" ] && test_files+=("$file")
    done < <(find_test_files)
    
    if [ ${#test_files[@]} -eq 0 ]; then
        echo "No test files found" >&2
        exit 1
    fi
    
    echo "Found ${#test_files[@]} test file(s)"
    echo ""
    
    # Build bats command
    local bats_args=()
    
    if [ "$VERBOSE" = true ]; then
        bats_args+=(-v)
    fi
    
    if [ -n "$TEST_PATTERN" ]; then
        bats_args+=(-f "$TEST_PATTERN")
    fi
    
    # Run tests and capture output
    local bats_output
    local bats_exit_code=0
    local tests_failed=false
    
    # Run bats and capture both stdout and stderr, preserving exit code
    set +e  # Don't exit on error
    bats_output=$("${BATS_CMD}" "${bats_args[@]}" "${test_files[@]}" 2>&1)
    bats_exit_code=$?
    set -e  # Re-enable exit on error
    
    # Display bats output
    echo "$bats_output"
    
    # Parse test results from output
    local total_line=$(echo "$bats_output" | grep -E "^[0-9]+\.\.[0-9]+" | head -1)
    local total_tests=0
    if [ -n "$total_line" ]; then
        total_tests=$(echo "$total_line" | awk -F'\.\.' '{print $2}' | head -1 | tr -d '[:space:]')
    fi
    
    # Count passed and failed tests
    local passed_tests=$(echo "$bats_output" | grep -c "^ok " 2>/dev/null || echo "0")
    local failed_tests=$(echo "$bats_output" | grep -c "^not ok " 2>/dev/null || echo "0")
    
    # Ensure we have valid numeric values
    if ! [[ "$total_tests" =~ ^[0-9]+$ ]]; then
        total_tests=0
    fi
    if ! [[ "$passed_tests" =~ ^[0-9]+$ ]]; then
        passed_tests=0
    fi
    if ! [[ "$failed_tests" =~ ^[0-9]+$ ]]; then
        failed_tests=0
    fi
    
    # If total_tests is 0, try to calculate from passed + failed
    if [ "$total_tests" -eq 0 ]; then
        total_tests=$((passed_tests + failed_tests))
    fi
    
    # Check for test failures in output
    if echo "$bats_output" | grep -q "not ok"; then
        tests_failed=true
    fi
    
    # Calculate percentage passed
    local percent_passed=0
    if [ "$total_tests" -gt 0 ]; then
        percent_passed=$((passed_tests * 100 / total_tests))
    fi
    
    # Determine final exit code
    local final_exit_code=0
    if [ $bats_exit_code -ne 0 ] || [ "$tests_failed" = true ]; then
        final_exit_code=1
    fi
    
    echo ""
    echo "=========================================="
    if [ $final_exit_code -eq 0 ]; then
        echo "All tests passed!"
    else
        echo "Some tests failed"
        if [ $bats_exit_code -ne 0 ]; then
            echo "BATS exit code: $bats_exit_code"
        fi
    fi
    echo "------------------------------------------"
    echo "Test Summary:"
    echo "  Passed:  $passed_tests"
    echo "  Failed:  $failed_tests"
    echo "  Total:   $total_tests"
    echo "  Success: ${percent_passed}%"
    echo "=========================================="
    
    exit $final_exit_code
}

main "$@"
