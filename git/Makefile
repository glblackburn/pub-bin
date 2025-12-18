# Makefile for git hooks testing and management
# Pattern follows: network-tools/capture/Makefile and LinkedIn-posts/Makefile

.PHONY: help test test-verbose install-hooks check-hooks clean check-deps

# Configuration
SHELL = /bin/bash
PROJECT_ROOT = $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)
GIT_DIR = $(PROJECT_ROOT)/git
HOOKS_DIR = $(GIT_DIR)/hooks
GIT_HOOKS_DIR = $(PROJECT_ROOT)/.git/hooks
TEST_SCRIPT = $(GIT_DIR)/test-hooks.sh
INSTALL_SCRIPT = $(GIT_DIR)/install-hooks.sh

# Default target
.DEFAULT_GOAL := help

help: ## show this help message
	@echo "Git Hooks - Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  make test              - Run all git hook tests"
	@echo "  make test-verbose     - Run tests with verbose output"
	@echo "  make install-hooks    - Install git hooks to .git/hooks/"
	@echo "  make check-hooks      - Check if hooks are installed"
	@echo "  make check-deps       - Check if required dependencies are installed"
	@echo "  make clean            - Clean test artifacts"
	@echo ""
	@echo "Examples:"
	@echo "  make install-hooks    # Install hooks"
	@echo "  make test             # Run tests"
	@echo "  make check-hooks      # Verify hooks are installed"

test: check-hooks ## run all git hook tests
	@echo "Running git hook tests..."
	@echo ""
	@if [ ! -f "$(TEST_SCRIPT)" ]; then \
		echo "ERROR: Test script not found: $(TEST_SCRIPT)"; \
		exit 1; \
	fi
	@bash "$(TEST_SCRIPT)"

test-verbose: check-hooks ## run tests with verbose output
	@echo "Running git hook tests (verbose)..."
	@echo ""
	@if [ ! -f "$(TEST_SCRIPT)" ]; then \
		echo "ERROR: Test script not found: $(TEST_SCRIPT)"; \
		exit 1; \
	fi
	@bash -x "$(TEST_SCRIPT)"

install-hooks: ## install git hooks to .git/hooks/
	@echo "Installing git hooks..."
	@if [ ! -f "$(INSTALL_SCRIPT)" ]; then \
		echo "ERROR: Install script not found: $(INSTALL_SCRIPT)"; \
		exit 1; \
	fi
	@if [ ! -d "$(GIT_HOOKS_DIR)" ]; then \
		echo "ERROR: Not a git repository. .git/hooks directory not found."; \
		exit 1; \
	fi
	@bash "$(INSTALL_SCRIPT)"

check-hooks: ## check if hooks are installed
	@echo "Checking git hooks installation..."
	@if [ ! -d "$(GIT_HOOKS_DIR)" ]; then \
		echo "✗ Not a git repository. .git/hooks directory not found."; \
		exit 1; \
	fi
	@if [ -f "$(GIT_HOOKS_DIR)/pre-commit" ]; then \
		echo "✓ pre-commit hook is installed"; \
	else \
		echo "✗ pre-commit hook is NOT installed"; \
		echo "  Run: make install-hooks"; \
		exit 1; \
	fi
	@if [ -f "$(GIT_HOOKS_DIR)/commit-msg" ]; then \
		echo "✓ commit-msg hook is installed"; \
	else \
		echo "✗ commit-msg hook is NOT installed"; \
		echo "  Run: make install-hooks"; \
		exit 1; \
	fi
	@echo "✓ All hooks are installed"

check-deps: ## check if required dependencies are installed
	@echo "Checking dependencies..."
	@if ! command -v python3 >/dev/null 2>&1; then \
		echo "✗ python3 is not installed"; \
		echo "  Install Python 3.8+ to use git hooks"; \
		exit 1; \
	fi
	@PYTHON_VERSION=$$(python3 --version 2>&1 | awk '{print $$2}'); \
	echo "✓ Python version: $$PYTHON_VERSION"
	@if [ ! -f "$(PROJECT_ROOT)/trufflehog/audit-sensitive-data.py" ]; then \
		echo "✗ audit-sensitive-data.py not found"; \
		echo "  Expected at: $(PROJECT_ROOT)/trufflehog/audit-sensitive-data.py"; \
		exit 1; \
	fi
	@echo "✓ audit-sensitive-data.py found"
	@echo "✓ All dependencies are available"

clean: ## clean test artifacts
	@echo "Cleaning test artifacts..."
	@# Unstage any test files
	@git reset HEAD "$(GIT_DIR)/test_hooks/"*.py 2>/dev/null || true
	@# Remove test files created during testing
	@rm -f "$(GIT_DIR)/test_hooks/test_hook_"*.py 2>/dev/null || true
	@echo "✓ Cleanup complete"
