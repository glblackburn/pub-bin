#!/bin/bash
#
# Wrapper script for backward compatibility
# This script now calls run_analysis.sh with --auto flag
#
# DEPRECATED: Use 'run_analysis.sh --auto' instead
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/run_analysis.sh" --auto "$@"
