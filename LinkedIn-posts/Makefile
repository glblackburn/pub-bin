# Makefile for post-to-linkedin.py testing and development

.PHONY: test test-unit test-integration test-integration-real test-coverage test-verbose test-fast help lint type-check clean check-deps pytest install-pytest install-test-deps pylint flake8 install-pylint install-flake8 mypy install-mypy

# Configuration
PYTEST = pytest
PYTHON = python3
SCRIPT = scripts/post-to-linkedin.py
# Paths relative to LinkedIn-posts/ directory
TEST_DIR = tests
SCRIPTS_DIR = scripts
# For imports, add scripts directory to Python path
LINKEDIN_POSTS_DIR = $(shell pwd)
COV_MODULE = post_to_linkedin

# Default target
.DEFAULT_GOAL := help

help:
	@echo "Available targets:"
	@echo "  make test                  - Run all fast tests (auto-installs pytest if needed)"
	@echo "  make test-unit            - Run unit tests only (fast, mocked)"
	@echo "  make test-integration     - Run integration tests with mocked API (fast)"
	@echo "  make test-integration-real - Run integration tests with real API (slow, requires LINKEDIN_TEST_ENABLED=1)"
	@echo "  make test-coverage        - Run tests with coverage report"
	@echo "  make test-verbose         - Run tests with verbose output"
	@echo "  make test-fast            - Run fast tests (exclude real API tests)"
	@echo "  make check-deps           - Check if required dependencies are installed"
	@echo "  make install-test-deps    - Install all test dependencies (pytest, responses, pytest-mock, pytest-cov)"
	@echo "  make install-pytest       - Install pytest and pytest-cov only"
	@echo "  make lint                 - Run code quality checks (auto-installs pylint/flake8 if needed)"
	@echo "  make type-check           - Run type checking (auto-installs mypy if needed)"
	@echo "  make clean                - Clean test artifacts"

# Ensure pytest is available - auto-installs if missing
pytest:
	@if ! command -v $(PYTEST) >/dev/null 2>&1 && ! $(PYTHON) -m pytest --version >/dev/null 2>&1; then \
		echo "pytest not found, installing..."; \
		make install-pytest; \
	fi

# Install pytest and pytest-cov
install-pytest:
	@echo "Installing pytest and pytest-cov..."
	@$(PYTHON) -m pip install --user pytest pytest-cov 2>/dev/null || $(PYTHON) -m pip install pytest pytest-cov
	@echo "✓ pytest installed successfully"

# Install all test dependencies
install-test-deps: install-pytest
	@echo "Installing test dependencies..."
	@$(PYTHON) -m pip install --user responses pytest-mock 2>/dev/null || $(PYTHON) -m pip install responses pytest-mock
	@echo "✓ All test dependencies installed successfully"

# Check if required dependencies are installed
check-deps:
	@echo "Checking dependencies..."
	@command -v $(PYTEST) >/dev/null 2>&1 && echo "✓ pytest is installed" || (echo "✗ pytest is not installed" && echo "  Install with: make install-pytest" && exit 1)
	@$(PYTHON) -c "import responses" 2>/dev/null && echo "✓ responses is installed" || (echo "✗ responses is not installed" && echo "  Install with: make install-test-deps" && exit 1)
	@$(PYTHON) -c "import pytest_mock" 2>/dev/null && echo "✓ pytest-mock is installed" || (echo "✗ pytest-mock is not installed" && echo "  Install with: make install-test-deps" && exit 1)
	@echo "All dependencies are installed."

# Run all fast tests (exclude real API integration tests)
# Note: Tests handle Python path in conftest.py or test file itself
# Use python3 -m pytest if pytest command not in PATH
test: pytest
	@if command -v $(PYTEST) >/dev/null 2>&1; then \
		PYTHONPATH=$(LINKEDIN_POSTS_DIR)/$(SCRIPTS_DIR):$$PYTHONPATH $(PYTEST) $(TEST_DIR) -m "not integration_real"; \
	else \
		PYTHONPATH=$(LINKEDIN_POSTS_DIR)/$(SCRIPTS_DIR):$$PYTHONPATH $(PYTHON) -m pytest $(TEST_DIR) -m "not integration_real"; \
	fi

# Run unit tests only (exclude integration tests)
test-unit: pytest
	@if command -v $(PYTEST) >/dev/null 2>&1; then \
		PYTHONPATH=$(LINKEDIN_POSTS_DIR)/$(SCRIPTS_DIR):$$PYTHONPATH $(PYTEST) $(TEST_DIR) -m "not integration and not integration_real"; \
	else \
		PYTHONPATH=$(LINKEDIN_POSTS_DIR)/$(SCRIPTS_DIR):$$PYTHONPATH $(PYTHON) -m pytest $(TEST_DIR) -m "not integration and not integration_real"; \
	fi

# Run integration tests with mocked API only (fast)
test-integration: pytest
	@if command -v $(PYTEST) >/dev/null 2>&1; then \
		PYTHONPATH=$(LINKEDIN_POSTS_DIR)/$(SCRIPTS_DIR):$$PYTHONPATH $(PYTEST) $(TEST_DIR) -m "integration and not integration_real"; \
	else \
		PYTHONPATH=$(LINKEDIN_POSTS_DIR)/$(SCRIPTS_DIR):$$PYTHONPATH $(PYTHON) -m pytest $(TEST_DIR) -m "integration and not integration_real"; \
	fi

# Run integration tests with real API (slow, requires LINKEDIN_TEST_ENABLED=1)
test-integration-real: pytest
	@if [ -z "$$LINKEDIN_TEST_ENABLED" ]; then \
		echo "⚠️  Real API tests require LINKEDIN_TEST_ENABLED=1"; \
		echo "   These tests create real posts on LinkedIn"; \
		echo "   Run with: LINKEDIN_TEST_ENABLED=1 make test-integration-real"; \
		exit 1; \
	fi
	@if command -v $(PYTEST) >/dev/null 2>&1; then \
		PYTHONPATH=$(LINKEDIN_POSTS_DIR)/$(SCRIPTS_DIR):$$PYTHONPATH $(PYTEST) $(TEST_DIR) -m integration_real; \
	else \
		PYTHONPATH=$(LINKEDIN_POSTS_DIR)/$(SCRIPTS_DIR):$$PYTHONPATH $(PYTHON) -m pytest $(TEST_DIR) -m integration_real; \
	fi

# Run tests with coverage report
test-coverage: pytest
	@if command -v $(PYTEST) >/dev/null 2>&1; then \
		PYTHONPATH=$(LINKEDIN_POSTS_DIR)/$(SCRIPTS_DIR):$$PYTHONPATH $(PYTEST) --cov=$(COV_MODULE) --cov-report=html --cov-report=term --cov-report=xml $(TEST_DIR) -m "not integration_real"; \
	else \
		PYTHONPATH=$(LINKEDIN_POSTS_DIR)/$(SCRIPTS_DIR):$$PYTHONPATH $(PYTHON) -m pytest --cov=$(COV_MODULE) --cov-report=html --cov-report=term --cov-report=xml $(TEST_DIR) -m "not integration_real"; \
	fi
	@echo "Coverage report generated in htmlcov/"
	@echo "Open htmlcov/index.html in browser to view"

# Run tests with verbose output
test-verbose: pytest
	@if command -v $(PYTEST) >/dev/null 2>&1; then \
		PYTHONPATH=$(LINKEDIN_POSTS_DIR)/$(SCRIPTS_DIR):$$PYTHONPATH $(PYTEST) -v $(TEST_DIR) -m "not integration_real"; \
	else \
		PYTHONPATH=$(LINKEDIN_POSTS_DIR)/$(SCRIPTS_DIR):$$PYTHONPATH $(PYTHON) -m pytest -v $(TEST_DIR) -m "not integration_real"; \
	fi

# Run fast tests (exclude real API integration tests)
test-fast: pytest
	@if command -v $(PYTEST) >/dev/null 2>&1; then \
		PYTHONPATH=$(LINKEDIN_POSTS_DIR)/$(SCRIPTS_DIR):$$PYTHONPATH $(PYTEST) $(TEST_DIR) -m "not integration_real"; \
	else \
		PYTHONPATH=$(LINKEDIN_POSTS_DIR)/$(SCRIPTS_DIR):$$PYTHONPATH $(PYTHON) -m pytest $(TEST_DIR) -m "not integration_real"; \
	fi

# Ensure pylint is available - auto-installs if missing
pylint:
	@if ! command -v pylint >/dev/null 2>&1 && ! $(PYTHON) -m pylint --version >/dev/null 2>&1; then \
		echo "pylint not found, installing..."; \
		make install-pylint; \
	fi

# Install pylint
install-pylint:
	@echo "Installing pylint..."
	@$(PYTHON) -m pip install --user pylint 2>/dev/null || $(PYTHON) -m pip install pylint
	@echo "✓ pylint installed successfully"

# Ensure flake8 is available - auto-installs if missing
flake8:
	@if ! command -v flake8 >/dev/null 2>&1 && ! $(PYTHON) -m flake8 --version >/dev/null 2>&1; then \
		echo "flake8 not found, installing..."; \
		make install-flake8; \
	fi

# Install flake8
install-flake8:
	@echo "Installing flake8..."
	@$(PYTHON) -m pip install --user flake8 2>/dev/null || $(PYTHON) -m pip install flake8
	@echo "✓ flake8 installed successfully"

# Run code quality checks
lint: pylint flake8
	@echo "Running pylint..."
	@if command -v pylint >/dev/null 2>&1; then \
		pylint $(SCRIPT); \
	else \
		$(PYTHON) -m pylint $(SCRIPT); \
	fi
	@echo "Running flake8..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 $(SCRIPT); \
	else \
		$(PYTHON) -m flake8 $(SCRIPT); \
	fi

# Ensure mypy is available - auto-installs if missing
mypy:
	@if ! command -v mypy >/dev/null 2>&1 && ! $(PYTHON) -m mypy --version >/dev/null 2>&1; then \
		echo "mypy not found, installing..."; \
		make install-mypy; \
	fi

# Install mypy
install-mypy:
	@echo "Installing mypy..."
	@$(PYTHON) -m pip install --user mypy 2>/dev/null || $(PYTHON) -m pip install mypy
	@echo "✓ mypy installed successfully"

# Run type checking
type-check: mypy
	@echo "Running mypy..."
	@if command -v mypy >/dev/null 2>&1; then \
		mypy --check-untyped-defs $(SCRIPT); \
	else \
		$(PYTHON) -m mypy --check-untyped-defs $(SCRIPT); \
	fi

# Clean test artifacts
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf tests/__pycache__
	rm -rf tests/.pytest_cache
	rm -rf scripts/__pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .mypy_cache
	rm -rf .pytest_cache
