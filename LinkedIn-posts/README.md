# LinkedIn Posts Automation

This directory contains scripts and tools for automating LinkedIn post creation, including the `post-to-linkedin.py` script and its comprehensive test suite.

## Quick Start

```bash
# Install test dependencies (first time only)
make install-test-deps

# Run all fast tests
make test

# Run tests with coverage report
make test-coverage
```

## Using the Makefile

The Makefile provides convenient wrappers for testing, linting, and development tasks. All targets automatically install missing dependencies.

### Test Targets

#### Running Tests

- **`make test`** - Run all fast tests (excludes real API tests)
  - Automatically installs pytest if needed
  - Runs unit tests and mocked integration tests
  - Fast execution (~0.1-0.3 seconds)

- **`make test-unit`** - Run unit tests only (fastest)
  - Tests pure functions: `validate_content`, `read_post_file`, `get_post_url`, `update_markdown_archive`
  - No API calls, no network dependencies
  - Typically runs in <0.1 seconds

- **`make test-integration`** - Run integration tests with mocked API
  - Tests API interactions using mocked HTTP responses
  - Uses `responses` library to mock LinkedIn API calls
  - Fast execution, no real API calls

- **`make test-integration-real`** - Run integration tests with real LinkedIn API
  - **Requires:** `LINKEDIN_TEST_ENABLED=1` environment variable
  - Creates real posts on LinkedIn (manual cleanup required)
  - Use with caution - only for final verification
  - Example: `LINKEDIN_TEST_ENABLED=1 make test-integration-real`

- **`make test-fast`** - Run fast tests (excludes real API tests)
  - Same as `make test` - alias for convenience

- **`make test-verbose`** - Run tests with verbose output
  - Shows detailed test execution information
  - Useful for debugging test failures

- **`make test-coverage`** - Run tests with coverage report
  - Generates HTML coverage report in `htmlcov/`
  - Generates XML coverage report (`coverage.xml`)
  - Shows terminal coverage summary
  - Open `htmlcov/index.html` in browser to view detailed report

#### Test Dependencies

- **`make install-test-deps`** - Install all test dependencies
  - Installs: `pytest`, `pytest-cov`, `responses`, `pytest-mock`
  - Run this first time or when dependencies are missing

- **`make install-pytest`** - Install pytest and pytest-cov only
  - Minimal installation for basic testing

- **`make check-deps`** - Check if required dependencies are installed
  - Verifies all test dependencies are available
  - Exits with error if dependencies are missing

### Code Quality Targets

- **`make lint`** - Run code quality checks
  - Runs `pylint` and `flake8` on `scripts/post-to-linkedin.py`
  - Automatically installs tools if missing

- **`make type-check`** - Run type checking
  - Runs `mypy` with `--check-untyped-defs` flag
  - Automatically installs mypy if missing

### Maintenance Targets

- **`make clean`** - Clean test artifacts
  - Removes: `.pytest_cache/`, `htmlcov/`, `.coverage`, `coverage.xml`
  - Removes Python cache files: `__pycache__/`, `*.pyc`, `*.pyo`
  - Removes type checking cache: `.mypy_cache/`

- **`make help`** - Show all available targets
  - Default target when running `make` without arguments

## Test Organization

### Test Structure

```
LinkedIn-posts/
├── tests/
│   ├── __init__.py              # Package initialization
│   ├── conftest.py              # Pytest configuration and fixtures
│   └── test_post_to_linkedin.py # Main test file
├── Makefile                     # Test execution wrapper
└── scripts/
    └── post-to-linkedin.py      # Script under test
```

### Test Categories

Tests are organized into three categories using pytest markers:

#### 1. Unit Tests (No Marker)
- **Purpose:** Test pure functions with no external dependencies
- **Functions tested:**
  - `validate_content()` - Content validation logic
  - `read_post_file()` - File reading operations
  - `get_post_url()` - URL construction from post IDs
  - `update_markdown_archive()` - Archive file updates
- **Characteristics:**
  - Fast execution (<0.1 seconds)
  - No API calls
  - No network dependencies
  - Isolated and deterministic

#### 2. Integration Tests (Mocked) - `@pytest.mark.integration`
- **Purpose:** Test API interactions using mocked HTTP responses
- **Functions tested:**
  - `get_person_urn()` - Person URN retrieval
  - `create_ugc_post()` - Post creation
  - `refresh_access_token()` - Token refresh
  - `complete_oauth_flow()` - OAuth flow
  - Complete workflow tests
- **Characteristics:**
  - Fast execution (~0.1-0.3 seconds)
  - Uses `responses` library to mock HTTP calls
  - No real API calls
  - Tests error handling and edge cases

#### 3. Integration Tests (Real API) - `@pytest.mark.integration_real`
- **Purpose:** Test with actual LinkedIn API (optional, for final verification)
- **Requirements:**
  - `LINKEDIN_TEST_ENABLED=1` environment variable
  - Valid LinkedIn API credentials
- **Characteristics:**
  - Slow execution (network-dependent)
  - Creates real posts on LinkedIn
  - Manual cleanup required (LinkedIn API doesn't support post deletion)
  - Use sparingly for final verification

### Test Fixtures

Fixtures are defined in `tests/conftest.py` and provide reusable test data:

#### Content Fixtures
- `sample_post_content` - Valid post content string
- `long_post_content` - Content exceeding character limit (3001 chars)
- `empty_post_content` - Empty string
- `whitespace_only_post` - Content with only whitespace

#### File Fixtures
- `sample_post_file` - Temporary post file with valid content
- `archive_file` - Empty archive file for testing
- `existing_archive_file` - Archive file with existing entries

#### Mock Fixtures
- `mock_credentials` - Mocked LinkedIn credentials
- `mock_person_urn` - Mock person URN string
- `mock_post_response` - Mock successful post creation response
- `mock_duplicate_post_response` - Mock duplicate post response
- `mock_requests_get` - Mocked `requests.get` function
- `mock_requests_post` - Mocked `requests.post` function
- `mock_webbrowser_open` - Mocked `webbrowser.open` function

#### Real API Fixtures
- `real_credentials` - Real LinkedIn credentials (requires `LINKEDIN_TEST_ENABLED=1`)

### Test Classes

Tests are organized into classes by functionality:

#### Unit Test Classes
- `TestValidateContent` - Content validation tests
- `TestReadPostFile` - File reading tests
- `TestGetPostUrl` - URL construction tests
- `TestUpdateMarkdownArchive` - Archive update tests

#### Integration Test Classes (Mocked)
- `TestGetPersonUrn` - Person URN retrieval tests
- `TestCreateUgcPost` - Post creation tests
- `TestRefreshAccessToken` - Token refresh tests
- `TestCompleteOAuthFlow` - OAuth flow tests
- `TestPostCreationWorkflow` - Complete workflow tests

#### Integration Test Classes (Real API)
- `TestRealApi` - Real API interaction tests

### Running Specific Tests

You can run specific tests using pytest directly:

```bash
# Run a specific test class
pytest tests/test_post_to_linkedin.py::TestValidateContent

# Run a specific test method
pytest tests/test_post_to_linkedin.py::TestValidateContent::test_valid_content

# Run tests matching a pattern
pytest -k "test_valid"

# Run only unit tests (exclude integration)
pytest -m "not integration and not integration_real"

# Run only mocked integration tests
pytest -m "integration and not integration_real"
```

## Test Coverage

Current test coverage: **29%** (core functionality covered)

The test suite focuses on:
- ✅ All pure functions (100% coverage)
- ✅ API interaction logic (mocked)
- ✅ Error handling paths
- ✅ Edge cases and boundary conditions

Areas with lower coverage:
- Interactive setup functions (require complex mocking)
- Main function (requires full workflow simulation)

To view detailed coverage:
```bash
make test-coverage
# Then open htmlcov/index.html in your browser
```

## Development Workflow

### Adding New Tests

1. **Unit Tests:** Add to appropriate test class in `test_post_to_linkedin.py`
   - No markers needed
   - Use fixtures from `conftest.py`

2. **Integration Tests (Mocked):** Add with `@pytest.mark.integration`
   - Use `@responses.activate` decorator for HTTP mocking
   - Mock API responses using `responses.add()`

3. **Integration Tests (Real API):** Add with `@pytest.mark.integration_real`
   - Include `@pytest.mark.skipif` to require `LINKEDIN_TEST_ENABLED=1`
   - Document manual cleanup requirements

### Running Tests During Development

```bash
# Quick feedback loop - run unit tests only
make test-unit

# Before committing - run all fast tests
make test

# Before pushing - run with coverage
make test-coverage
```

## Dependencies

### Required for Testing
- `pytest` - Test framework
- `pytest-cov` - Coverage plugin
- `responses` - HTTP mocking library
- `pytest-mock` - Enhanced mocking utilities

### Optional
- `pylint` - Code quality (auto-installed by `make lint`)
- `flake8` - Style checker (auto-installed by `make lint`)
- `mypy` - Type checker (auto-installed by `make type-check`)

All dependencies are automatically installed by the Makefile targets when needed.

## See Also

- [Testing Strategy Documentation](docs/TESTING-STRATEGY.md) - Detailed testing strategy and examples
- [LinkedIn Style Guide](LinkedIn-style-guide.md) - Post formatting guidelines
- [LinkedIn Setup Guide](docs/LINKEDIN_SETUP_GUIDE.md) - API credential setup
