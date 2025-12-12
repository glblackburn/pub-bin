# Makefile for analyze-tcpdump.py testing and development

.PHONY: test test-unit test-integration test-performance test-coverage test-verbose test-fast help lint type-check clean check-deps pytest install-pytest pylint flake8 install-pylint install-flake8 mypy install-mypy

# Configuration
PYTEST = pytest
PYTHON = python3
SCRIPT = analyze-tcpdump.py
# Paths relative to network-tools/capture/ directory
TEST_DIR = tests
TEST_FILE = $(TEST_DIR)/test_analyze_tcpdump.py
TEST_DATA = $(TEST_DIR)/data/tcpdump
# For imports, add capture directory to Python path
CAPTURE_DIR = $(shell pwd)
COV_MODULE = analyze_tcpdump

# Default target
.DEFAULT_GOAL := help

help:
	@echo "Available targets:"
	@echo "  make test              - Run all tests (auto-installs pytest if needed)"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-performance - Run performance tests only"
	@echo "  make test-coverage    - Run tests with coverage report"
	@echo "  make test-verbose     - Run tests with verbose output"
	@echo "  make test-fast        - Run tests excluding performance tests"
	@echo "  make check-deps       - Check if required dependencies are installed"
	@echo "  make install-pytest   - Install pytest and pytest-cov"
	@echo "  make lint             - Run code quality checks (auto-installs pylint/flake8 if needed)"
	@echo "  make type-check       - Run type checking (auto-installs mypy if needed)"
	@echo "  make clean            - Clean test artifacts"

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

# Check if pytest is installed
check-deps:
	@echo "Checking dependencies..."
	@command -v $(PYTEST) >/dev/null 2>&1 && echo "✓ pytest is installed" || (echo "✗ pytest is not installed" && echo "  Install with: make install-pytest" && exit 1)
	@echo "All dependencies are installed."

# Run all tests
# Note: Tests handle Python path in conftest.py or test file itself
# Use python3 -m pytest if pytest command not in PATH
test: pytest
	@if command -v $(PYTEST) >/dev/null 2>&1; then \
		PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTEST) $(TEST_DIR); \
	else \
		PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTHON) -m pytest $(TEST_DIR); \
	fi

# Run unit tests only (exclude integration and performance)
test-unit: pytest
	@if command -v $(PYTEST) >/dev/null 2>&1; then \
		PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTEST) $(TEST_DIR) -m "not integration and not performance"; \
	else \
		PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTHON) -m pytest $(TEST_DIR) -m "not integration and not performance"; \
	fi

# Run integration tests only
test-integration: pytest
	@if command -v $(PYTEST) >/dev/null 2>&1; then \
		PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTEST) $(TEST_DIR) -m integration; \
	else \
		PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTHON) -m pytest $(TEST_DIR) -m integration; \
	fi

# Run performance tests only
test-performance: pytest
	@if command -v $(PYTEST) >/dev/null 2>&1; then \
		PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTEST) $(TEST_DIR) -m performance; \
	else \
		PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTHON) -m pytest $(TEST_DIR) -m performance; \
	fi

# Run tests with coverage report
test-coverage: pytest
	@if command -v $(PYTEST) >/dev/null 2>&1; then \
		PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTEST) --cov=$(COV_MODULE) --cov-report=html --cov-report=term --cov-report=xml $(TEST_DIR); \
	else \
		PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTHON) -m pytest --cov=$(COV_MODULE) --cov-report=html --cov-report=term --cov-report=xml $(TEST_DIR); \
	fi
	@echo "Coverage report generated in htmlcov/"
	@echo "Open htmlcov/index.html in browser to view"

# Run tests with verbose output
test-verbose: pytest
	@if command -v $(PYTEST) >/dev/null 2>&1; then \
		PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTEST) -v $(TEST_DIR); \
	else \
		PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTHON) -m pytest -v $(TEST_DIR); \
	fi

# Run fast tests (exclude performance)
test-fast: pytest
	@if command -v $(PYTEST) >/dev/null 2>&1; then \
		PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTEST) $(TEST_DIR) -m "not performance"; \
	else \
		PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTHON) -m pytest $(TEST_DIR) -m "not performance"; \
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
		mypy $(SCRIPT); \
	else \
		$(PYTHON) -m mypy $(SCRIPT); \
	fi

# Clean test artifacts
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf tests/__pycache__
	rm -rf tests/.pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find tests -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
