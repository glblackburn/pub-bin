#!/bin/bash
# Test script for git hooks
# Verifies that pre-commit and commit-msg hooks are working correctly

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Get project root
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
TEST_DIR="${PROJECT_ROOT}/git/test_hooks"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Cleanup function
cleanup() {
    # Unstage any test files
    git reset HEAD "${TEST_DIR}/"*.py 2>/dev/null || true
    # Remove test files created during testing
    rm -f "${TEST_DIR}/test_hook_"*.py
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Print test header
print_header() {
    echo "=========================================="
    echo "Git Hooks Test Suite"
    echo "=========================================="
    echo ""
}

# Print test result
print_result() {
    local test_name="$1"
    local status="$2"
    local message="$3"

    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓${NC} ${test_name}: ${message}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} ${test_name}: ${message}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Check if hooks are installed
check_hooks_installed() {
    echo "Checking hook installation..."

    if [ ! -f "${PROJECT_ROOT}/.git/hooks/pre-commit" ]; then
        echo -e "${RED}ERROR:${NC} pre-commit hook not found"
        echo "   Run: make install-hooks"
        return 1
    fi

    if [ ! -f "${PROJECT_ROOT}/.git/hooks/commit-msg" ]; then
        echo -e "${RED}ERROR:${NC} commit-msg hook not found"
        echo "   Run: make install-hooks"
        return 1
    fi

    echo -e "${GREEN}✓${NC} Hooks are installed"
    echo ""
    return 0
}

# Test 1: Pre-commit hook blocks file with AWS key
test_precommit_blocks_aws_key() {
    local test_file="${TEST_DIR}/test_hook_aws_key.py"
    mkdir -p "$TEST_DIR"

    echo "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE" > "$test_file"
    git add "$test_file" 2>/dev/null || true

    if git commit -m "Test: verify hooks" 2>&1 | grep -q "contains sensitive data"; then
        print_result "pre-commit blocks AWS key" "PASS" "File with AWS key was blocked"
        git reset HEAD "$test_file" 2>/dev/null || true
        rm -f "$test_file"
        return 0
    else
        print_result "pre-commit blocks AWS key" "FAIL" "File with AWS key was NOT blocked"
        git reset HEAD "$test_file" 2>/dev/null || true
        rm -f "$test_file"
        return 1
    fi
}

# Test 2: Pre-commit hook blocks file with trailing whitespace
test_precommit_blocks_trailing_whitespace() {
    local test_file="${TEST_DIR}/test_hook_trailing.py"
    mkdir -p "$TEST_DIR"

    echo "def test(): " > "$test_file"
    git add "$test_file" 2>/dev/null || true

    if git commit -m "Test: trailing whitespace" 2>&1 | grep -q "trailing whitespace"; then
        print_result "pre-commit blocks trailing whitespace" "PASS" "File with trailing whitespace was blocked"
        git reset HEAD "$test_file" 2>/dev/null || true
        rm -f "$test_file"
        return 0
    else
        print_result "pre-commit blocks trailing whitespace" "FAIL" "File with trailing whitespace was NOT blocked"
        git reset HEAD "$test_file" 2>/dev/null || true
        rm -f "$test_file"
        return 1
    fi
}

# Test 3: Pre-commit hook blocks file without newline
test_precommit_blocks_no_newline() {
    local test_file="${TEST_DIR}/test_hook_no_newline.py"
    mkdir -p "$TEST_DIR"

    printf "def test():\n    pass" > "$test_file"
    git add "$test_file" 2>/dev/null || true

    if git commit -m "Test: no newline" 2>&1 | grep -q "does not end with newline"; then
        print_result "pre-commit blocks missing newline" "PASS" "File without newline was blocked"
        git reset HEAD "$test_file" 2>/dev/null || true
        rm -f "$test_file"
        return 0
    else
        print_result "pre-commit blocks missing newline" "FAIL" "File without newline was NOT blocked"
        git reset HEAD "$test_file" 2>/dev/null || true
        rm -f "$test_file"
        return 1
    fi
}

# Test 4: Commit-msg hook blocks commit message with AWS key
test_commitmsg_blocks_aws_key() {
    local test_file="${TEST_DIR}/test_hook_clean.py"
    mkdir -p "$TEST_DIR"

    echo "def test(): pass" > "$test_file"
    git add "$test_file" 2>/dev/null || true

    if git commit -m "Added AWS key: AKIAIOSFODNN7EXAMPLE" 2>&1 | grep -q "Commit message contains sensitive data"; then
        print_result "commit-msg blocks AWS key" "PASS" "Commit message with AWS key was blocked"
        git reset HEAD "$test_file" 2>/dev/null || true
        rm -f "$test_file"
        return 0
    else
        print_result "commit-msg blocks AWS key" "FAIL" "Commit message with AWS key was NOT blocked"
        git reset HEAD "$test_file" 2>/dev/null || true
        rm -f "$test_file"
        return 1
    fi
}

# Test 5: Clean commit is allowed
test_clean_commit_allowed() {
    local test_file="${TEST_DIR}/test_hook_clean2.py"
    mkdir -p "$TEST_DIR"

    echo "def test(): pass" > "$test_file"
    git add "$test_file" 2>/dev/null || true

    if git commit -m "Test: clean commit" 2>&1 | grep -q "\[.*\] Test: clean commit"; then
        print_result "clean commit allowed" "PASS" "Clean commit was allowed"
        git reset HEAD~1 --hard 2>/dev/null || true
        rm -f "$test_file"
        return 0
    else
        print_result "clean commit allowed" "FAIL" "Clean commit was blocked (unexpected)"
        git reset HEAD "$test_file" 2>/dev/null || true
        rm -f "$test_file"
        return 1
    fi
}

# Print summary
print_summary() {
    echo ""
    echo "=========================================="
    echo "Test Summary"
    echo "=========================================="
    echo "Total tests:  $TESTS_TOTAL"
    echo -e "${GREEN}Passed:${NC}      $TESTS_PASSED"
    echo -e "${RED}Failed:${NC}      $TESTS_FAILED"
    echo ""

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}✗ Some tests failed${NC}"
        return 1
    fi
}

# Main execution
main() {
    print_header

    # Check hooks are installed
    if ! check_hooks_installed; then
        exit 1
    fi

    # Run tests
    echo "Running tests..."
    echo ""

    test_precommit_blocks_aws_key || true
    test_precommit_blocks_trailing_whitespace || true
    test_precommit_blocks_no_newline || true
    test_commitmsg_blocks_aws_key || true
    test_clean_commit_allowed || true

    # Print summary and exit with appropriate code
    if print_summary; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
