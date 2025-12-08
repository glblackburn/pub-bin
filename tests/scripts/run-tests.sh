#!/usr/bin/env bash
# Run BATS tests for general scripts

set -euo pipefail

# Get script directory using /bin/pwd to avoid any aliases or functions
# Use read to strip any trailing newlines
read -r SCRIPT_DIR < <(cd "$(dirname "${BASH_SOURCE[0]}")" && /bin/pwd)
TEST_DIR="${SCRIPT_DIR}"
UNIT_DIR="${TEST_DIR}/unit"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

################################################################################
# Functions
################################################################################

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Run BATS tests for general scripts.

Options:
  -h, --help          Show this help message
  -v, --verbose       Run tests with verbose output
  -f, --filter PATTERN  Run only tests matching PATTERN
  -u, --unit          Run unit tests (default)
  -a, --all           Run all tests

Examples:
  $0                  # Run all unit tests
  $0 -v               # Run with verbose output
  $0 -f "script exists"  # Run only tests matching pattern
EOF
}

################################################################################
# Main
################################################################################

VERBOSE=false
FILTER=""
TEST_TYPE="unit"

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
            FILTER="$2"
            shift 2
            ;;
        -u|--unit)
            TEST_TYPE="unit"
            shift
            ;;
        -a|--all)
            TEST_TYPE="all"
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

# Check if bats is installed
if ! command -v bats >/dev/null 2>&1; then
    echo -e "${RED}Error: bats is not installed${NC}" >&2
    echo "Install with: brew install bats-core (macOS) or apt-get install bats (Linux)" >&2
    exit 1
fi

# Build bats command as an array
BATS_ARGS=()
if [ "$VERBOSE" = true ]; then
    BATS_ARGS+=("-v")
fi

if [ -n "$FILTER" ]; then
    BATS_ARGS+=("-f" "$FILTER")
fi

# Run tests
echo -e "${GREEN}Running BATS tests for general scripts...${NC}"
echo ""

case $TEST_TYPE in
    unit)
        echo -e "${YELLOW}Running unit tests...${NC}"
        bats "${BATS_ARGS[@]}" "${UNIT_DIR}"
        ;;
    all)
        echo -e "${YELLOW}Running all tests...${NC}"
        bats "${BATS_ARGS[@]}" "${UNIT_DIR}"
        ;;
    *)
        echo "Unknown test type: $TEST_TYPE" >&2
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Tests completed!${NC}"
