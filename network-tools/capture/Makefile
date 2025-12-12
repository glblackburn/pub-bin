# Makefile for analyze-tcpdump.py testing and development

.PHONY: test test-unit test-integration test-performance test-coverage test-verbose test-fast help lint type-check clean

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
	@echo "  make test              - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-performance - Run performance tests only"
	@echo "  make test-coverage    - Run tests with coverage report"
	@echo "  make test-verbose     - Run tests with verbose output"
	@echo "  make test-fast        - Run tests excluding performance tests"
	@echo "  make lint             - Run code quality checks (pylint/flake8)"
	@echo "  make type-check       - Run type checking (mypy)"
	@echo "  make clean            - Clean test artifacts"

# Run all tests
# Note: Tests handle Python path in conftest.py or test file itself
test:
	PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTEST) $(TEST_DIR)

# Run unit tests only (exclude integration and performance)
test-unit:
	PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTEST) $(TEST_DIR) -m "not integration and not performance"

# Run integration tests only
test-integration:
	PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTEST) $(TEST_DIR) -m integration

# Run performance tests only
test-performance:
	PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTEST) $(TEST_DIR) -m performance

# Run tests with coverage report
test-coverage:
	PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTEST) --cov=$(COV_MODULE) --cov-report=html --cov-report=term --cov-report=xml $(TEST_DIR)
	@echo "Coverage report generated in htmlcov/"
	@echo "Open htmlcov/index.html in browser to view"

# Run tests with verbose output
test-verbose:
	PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTEST) -v $(TEST_DIR)

# Run fast tests (exclude performance)
test-fast:
	PYTHONPATH=$(CAPTURE_DIR):$$PYTHONPATH $(PYTEST) $(TEST_DIR) -m "not performance"

# Run code quality checks
lint:
	@echo "Running pylint..."
	@command -v pylint >/dev/null 2>&1 && pylint $(SCRIPT) || echo "pylint not installed, skipping"
	@echo "Running flake8..."
	@command -v flake8 >/dev/null 2>&1 && flake8 $(SCRIPT) || echo "flake8 not installed, skipping"

# Run type checking
type-check:
	@echo "Running mypy..."
	@command -v mypy >/dev/null 2>&1 && mypy $(SCRIPT) || echo "mypy not installed, skipping"

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
