# Thin test orchestration (react2shell-server-style UX): local venv + pytest from repo root.
# From repo root: make -C osx help | test-setup | test | ...

.PHONY: help test-setup check-venv test test-quick test-report test-report-coverage \
	test-coverage coverage coverage-quick test-clean test-timings

.DEFAULT_GOAL := help

OSX_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
REPO_ROOT := $(abspath $(OSX_DIR)/..)
VENV := $(OSX_DIR)/.venv
PY3 := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip
PYTEST := $(PY3) -m pytest
JUNIT := $(OSX_DIR)/tests/reports/junit.xml

# Module name matches conftest sys.path (osx/) + `import macos_mouse_click`.
COV_MODULE := macos_mouse_click
COV_CONFIG := $(OSX_DIR)/.coveragerc
COV_HTML := $(OSX_DIR)/htmlcov
COV_XML := $(OSX_DIR)/coverage.xml
COV_DATA := $(OSX_DIR)/.coverage

PYTEST_BASE := $(PYTEST) osx/tests -c osx/pytest.ini

# Shared pytest-cov flags (paths under osx/ so repo root stays tidy).
PYTEST_COV_FLAGS := --cov=$(COV_MODULE) --cov-config=$(COV_CONFIG) \
	--cov-report=html:$(COV_HTML) \
	--cov-report=term-missing \
	--cov-report=xml:$(COV_XML)

help:
	@echo "osx / macOS mouse click test targets (from repo: make -C osx <target>)"
	@echo "  test-setup   Create .venv under osx/ and pip install requirements-test.txt"
	@echo "  test         Full pytest (verbose)"
	@echo "  test-quick   pytest -q --tb=short (excludes table_nav)"
	@echo "  test-report  JUnit XML -> osx/tests/reports/junit.xml"
	@echo "  test-report-coverage  One pytest: JUnit + coverage (HTML/XML under osx/)"
	@echo "  test-coverage / coverage  pytest --cov (HTML, term-missing, coverage.xml)"
	@echo "  coverage-quick  Same as coverage but excludes table_nav marker"
	@echo "  test-timings Slowest tests (--durations=25)"
	@echo "  test-clean   Drop pytest caches, __pycache__, junit, coverage artifacts"

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
	cd "$(REPO_ROOT)" && $(PYTEST_BASE) -q --tb=short -m "not table_nav"

test-report: check-venv
	@mkdir -p "$(OSX_DIR)/tests/reports"
	cd "$(REPO_ROOT)" && $(PYTEST_BASE) -v --tb=short --junitxml="$(JUNIT)"

# CI / local: single pytest for JUnit + coverage (Plan 11).
test-report-coverage: check-venv
	@mkdir -p "$(OSX_DIR)/tests/reports"
	cd "$(REPO_ROOT)" && COVERAGE_FILE="$(COV_DATA)" $(PYTEST_BASE) -v --tb=short \
		--junitxml="$(JUNIT)" $(PYTEST_COV_FLAGS)
	@echo "Coverage HTML: $(COV_HTML)/index.html"
	@echo "Coverage XML:  $(COV_XML)"

test-coverage coverage: check-venv
	cd "$(REPO_ROOT)" && COVERAGE_FILE="$(COV_DATA)" $(PYTEST_BASE) -v $(PYTEST_COV_FLAGS)
	@echo "Coverage HTML: $(COV_HTML)/index.html"
	@echo "Coverage XML:  $(COV_XML)"

coverage-quick: check-venv
	cd "$(REPO_ROOT)" && COVERAGE_FILE="$(COV_DATA)" $(PYTEST_BASE) -v -m "not table_nav" $(PYTEST_COV_FLAGS)
	@echo "Coverage HTML: $(COV_HTML)/index.html"
	@echo "Coverage XML:  $(COV_XML)"

test-timings: check-venv
	cd "$(REPO_ROOT)" && $(PYTEST_BASE) -q --durations=25

test-clean:
	rm -rf "$(OSX_DIR)/.pytest_cache" "$(OSX_DIR)/tests/.pytest_cache" \
		"$(OSX_DIR)/tests/__pycache__" "$(JUNIT)" \
		"$(COV_HTML)" "$(COV_DATA)" "$(COV_XML)"
