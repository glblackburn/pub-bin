# Thin test orchestration (react2shell-server-style UX): local venv + pytest from repo root.
# From repo root: make -C osx help | test-setup | test | ...

.PHONY: help test-setup check-venv test test-quick test-report test-clean test-timings

.DEFAULT_GOAL := help

OSX_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
REPO_ROOT := $(abspath $(OSX_DIR)/..)
VENV := $(OSX_DIR)/.venv
PY3 := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip
PYTEST := $(PY3) -m pytest
JUNIT := $(OSX_DIR)/tests/reports/junit.xml

PYTEST_BASE := $(PYTEST) osx/tests -c osx/pytest.ini

help:
	@echo "osx / macOS mouse click test targets (from repo: make -C osx <target>)"
	@echo "  test-setup   Create .venv under osx/ and pip install requirements-test.txt"
	@echo "  test         Full pytest (verbose)"
	@echo "  test-quick   pytest -q --tb=short"
	@echo "  test-report  JUnit XML -> osx/tests/reports/junit.xml"
	@echo "  test-timings Slowest tests (--durations=25)"
	@echo "  test-clean   Drop pytest caches, __pycache__, junit.xml"

check-venv:
	@if [ ! -x "$(PY3)" ]; then \
		echo >&2 "No venv at $(VENV). Run: make -C osx test-setup"; \
		exit 1; \
	fi

test-setup:
	python3 -m venv "$(VENV)"
	"$(PIP)" install -U pip
	"$(PIP)" install -r "$(OSX_DIR)/requirements-test.txt"

test: check-venv
	cd "$(REPO_ROOT)" && $(PYTEST_BASE) -v

test-quick: check-venv
	cd "$(REPO_ROOT)" && $(PYTEST_BASE) -q --tb=short

test-report: check-venv
	@mkdir -p "$(OSX_DIR)/tests/reports"
	cd "$(REPO_ROOT)" && $(PYTEST_BASE) -v --tb=short --junitxml="$(JUNIT)"

test-timings: check-venv
	cd "$(REPO_ROOT)" && $(PYTEST_BASE) -q --durations=25

test-clean:
	rm -rf "$(OSX_DIR)/.pytest_cache" "$(OSX_DIR)/tests/.pytest_cache" \
		"$(OSX_DIR)/tests/__pycache__" "$(JUNIT)"
