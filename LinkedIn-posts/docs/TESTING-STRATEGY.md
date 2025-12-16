# Testing Strategy for post-to-linkedin.py

**Date:** December 16, 2025  
**Script:** `LinkedIn-posts/scripts/post-to-linkedin.py`  
**Purpose:** Comprehensive testing strategy for LinkedIn posting automation

---

## Technology Stack

### Primary Framework: **pytest**

**Why pytest:**
- Already used in project (see `network-tools/capture/tests/`)
- Excellent mocking capabilities
- Fast test execution
- Rich assertion messages
- Fixture system for test setup/teardown
- Markers for test categorization

### Required Dependencies

```bash
# Core testing framework
pip install pytest pytest-cov

# HTTP mocking (fast, no real API calls)
pip install responses

# Advanced mocking (alternative to responses)
pip install pytest-mock

# Optional: for better test output
pip install pytest-xdist  # Parallel test execution
pip install pytest-html   # HTML test reports
```

**Installation:**
```bash
cd LinkedIn-posts

# Using Makefile (recommended)
make install-test-deps

# Or manually
pip install --user pytest pytest-cov responses pytest-mock
```

---

## Test Structure

```
LinkedIn-posts/
├── scripts/
│   ├── post-to-linkedin.py
│   └── linkedin_credentials.py
└── tests/
    ├── conftest.py                    # Pytest configuration and fixtures
    ├── test_post_to_linkedin.py       # Main test file
    ├── fixtures/                      # Test data files
    │   ├── sample-post.txt            # Sample post content
    │   ├── long-post.txt              # Post exceeding character limit
    │   └── empty-post.txt             # Empty post file
    └── mocks/                          # Mock response data
        ├── api_responses.json         # Mock API responses
        └── oauth_responses.json       # Mock OAuth responses
```

---

## Testing Strategy: Three-Tier Approach

### Tier 1: Unit Tests (Fast, No API Calls) ⚡

**Goal:** Test individual functions in isolation with mocked dependencies

**Technologies:**
- `pytest` with `pytest-mock` or `unittest.mock`
- `responses` library for HTTP mocking

**What to Test:**
1. **Content Validation** (`validate_content`)
   - Empty content
   - Content exceeding 3000 characters
   - Valid content
   - Edge cases (exactly 3000 characters)

2. **File Reading** (`read_post_file`)
   - File exists
   - File not found
   - Encoding issues
   - Empty file

3. **URL Construction** (`get_post_url`)
   - UGC Post URN format
   - Share URN format
   - Invalid URN formats
   - Numeric ID extraction

4. **Archive Updates** (`update_markdown_archive`)
   - Adding new post to archive
   - Date extraction from filename
   - Markdown formatting

**Example Unit Test:**
```python
import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import sys

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from post_to_linkedin import validate_content, read_post_file, get_post_url

class TestValidateContent:
    """Test content validation function"""
    
    def test_valid_content(self):
        """Test valid content passes validation"""
        content = "This is a valid post" * 50  # ~950 chars
        is_valid, error = validate_content(content)
        assert is_valid is True
        assert error is None
    
    def test_empty_content(self):
        """Test empty content fails validation"""
        is_valid, error = validate_content("")
        assert is_valid is False
        assert "empty" in error.lower()
    
    def test_content_too_long(self):
        """Test content exceeding limit fails"""
        content = "x" * 3001  # Exceeds 3000 char limit
        is_valid, error = validate_content(content)
        assert is_valid is False
        assert "exceeds" in error.lower()
        assert "3000" in error
    
    def test_exact_limit(self):
        """Test content at exact limit passes"""
        content = "x" * 3000  # Exactly 3000 chars
        is_valid, error = validate_content(content)
        assert is_valid is True
```

---

### Tier 2: Integration Tests with Mocked API (Fast, No Real Posts) 🚀

**Goal:** Test full workflow with mocked HTTP responses

**Technologies:**
- `responses` library to mock `requests` calls
- Mock credentials loading

**What to Test:**
1. **OAuth Flow** (mocked)
   - Token refresh
   - Person URN retrieval
   - Error handling

2. **Post Creation** (mocked)
   - Successful post creation
   - Duplicate post detection
   - API errors (401, 403, 422, 500)
   - Network timeouts

3. **End-to-End Workflow** (mocked)
   - Read file → Validate → Post → Get URL
   - Error handling at each step

**Example Integration Test with Mocked API:**
```python
import pytest
import responses
from unittest.mock import patch, Mock
from pathlib import Path
import json

@responses.activate
def test_create_post_success(mock_credentials, tmp_path):
    """Test successful post creation with mocked API"""
    # Create test post file
    post_file = tmp_path / "test-post.txt"
    post_file.write_text("Test post content")
    
    # Mock API responses
    responses.add(
        responses.POST,
        "https://api.linkedin.com/v2/ugcPosts",
        json={"id": "urn:li:ugcPost:1234567890"},
        status=201
    )
    
    # Mock credentials
    with patch('post_to_linkedin.load_linkedin_credentials') as mock_creds:
        mock_creds.return_value = {
            'LINKEDIN_ACCESS_TOKEN': 'test_token',
            'LINKEDIN_REFRESH_TOKEN': 'test_refresh'
        }
        
        # Mock get_person_urn
        with patch('post_to_linkedin.get_person_urn') as mock_urn:
            mock_urn.return_value = "urn:li:person:123456"
            
            # Test post creation
            result = create_ugc_post("test_token", "urn:li:person:123456", "Test content")
            
            assert result is not None
            assert result['id'] == "urn:li:ugcPost:1234567890"
            assert len(responses.calls) == 1

@responses.activate
def test_create_post_duplicate(mock_credentials):
    """Test duplicate post detection"""
    responses.add(
        responses.POST,
        "https://api.linkedin.com/v2/ugcPosts",
        json={
            "message": "Content is a duplicate of urn:li:share:9876543210"
        },
        status=422
    )
    
    result = create_ugc_post("token", "urn:li:person:123", "Duplicate content")
    
    assert result is not None
    assert result.get('duplicate') is True
    assert '9876543210' in result.get('existing_share_id', '')
```

---

### Tier 3: Integration Tests with Real API (Slow, Creates Real Posts) 🐌

**Goal:** Test against real LinkedIn API (optional, for final verification)

**Technologies:**
- Real API calls (use test/sandbox account if available)
- Automatic cleanup (delete posts after test)
- Test markers to skip by default

**What to Test:**
1. **Real Post Creation**
   - Create actual post
   - Verify post appears on LinkedIn
   - Get post URL
   - Delete post (cleanup)

2. **Real OAuth Flow**
   - Complete OAuth authorization
   - Token refresh
   - Error scenarios

**Important:** These tests should:
- Be marked with `@pytest.mark.integration_real` (distinct from mocked integration tests)
- Require environment variable to run: `LINKEDIN_TEST_ENABLED=1`
- Note: LinkedIn API doesn't support post deletion, so cleanup is manual
- Use test/sandbox LinkedIn account (not production)

**Example Real API Test:**
```python
import pytest
import os
from pathlib import Path

@pytest.mark.integration_real
@pytest.mark.skipif(
    not os.getenv('LINKEDIN_TEST_ENABLED'),
    reason="Requires LINKEDIN_TEST_ENABLED=1 and real credentials"
)
def test_real_post_creation_and_cleanup(tmp_path, real_credentials):
    """Test creating and deleting a real post (requires credentials)"""
    # Create test post
    post_file = tmp_path / "test-real-post.txt"
    post_file.write_text("TEST POST - Please ignore. Will be deleted.")
    
    # Create post
    result = create_real_post(post_file)
    post_id = result['id']
    
    try:
        # Verify post was created
        assert post_id is not None
        
        # Get post URL
        post_url = get_post_url(post_id)
        assert "linkedin.com" in post_url
        
    finally:
        # Cleanup: Delete the post
        delete_post(post_id)
```

---

## Fast Test Execution Strategy

### 1. Mock All External Dependencies

**Use `responses` library for HTTP mocking:**
```python
import responses

@responses.activate
def test_fast_api_call():
    """Mock HTTP calls - executes in milliseconds"""
    responses.add(
        responses.POST,
        "https://api.linkedin.com/v2/ugcPosts",
        json={"id": "urn:li:ugcPost:123"},
        status=201
    )
    
    # Test executes instantly, no network delay
    result = create_ugc_post("token", "urn", "content")
    assert result is not None
```

### 2. Use pytest Markers to Skip Slow Tests

```python
# conftest.py
def pytest_configure(config):
    config.addinivalue_line("markers", "integration: integration tests with mocked API")
    config.addinivalue_line("markers", "integration_real: integration tests with real API")
    config.addinivalue_line("markers", "slow: slow running tests")

# Run only fast tests (excludes real API tests)
pytest -m "not integration_real"

# Run all tests including real API ones
LINKEDIN_TEST_ENABLED=1 pytest -m integration_real
```

### 3. Parallel Test Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest -n 4

# Auto-detect CPU cores
pytest -n auto
```

### 4. Test Fixtures for Reusable Setup

```python
# conftest.py
import pytest
from pathlib import Path
from unittest.mock import Mock

@pytest.fixture
def mock_credentials():
    """Mock credentials for all tests"""
    with patch('post_to_linkedin.load_linkedin_credentials') as mock:
        mock.return_value = {
            'LINKEDIN_ACCESS_TOKEN': 'test_token',
            'LINKEDIN_REFRESH_TOKEN': 'test_refresh_token',
            'LINKEDIN_CLIENT_ID': 'test_client_id',
            'LINKEDIN_CLIENT_SECRET': 'test_client_secret'
        }
        yield mock

@pytest.fixture
def sample_post_file(tmp_path):
    """Create a sample post file for testing"""
    post_file = tmp_path / "sample-post.txt"
    post_file.write_text("Sample LinkedIn post content for testing.")
    return post_file

@pytest.fixture
def mock_api_responses():
    """Mock all LinkedIn API endpoints"""
    with responses.RequestsMock() as rsps:
        # Mock userinfo endpoint
        rsps.add(
            responses.GET,
            "https://api.linkedin.com/v2/userinfo",
            json={"sub": "123456"},
            status=200
        )
        yield rsps
```

---

## Testing Post Creation and Deletion

### Mocked Tests (Fast) ⚡

```python
@responses.activate
def test_post_creation_workflow(mock_credentials, sample_post_file):
    """Test complete post creation workflow with mocked API"""
    # Mock: Get person URN
    responses.add(
        responses.GET,
        "https://api.linkedin.com/v2/userinfo",
        json={"sub": "123456"},
        status=200
    )
    
    # Mock: Create post
    responses.add(
        responses.POST,
        "https://api.linkedin.com/v2/ugcPosts",
        json={"id": "urn:li:ugcPost:1234567890"},
        status=201
    )
    
    # Execute workflow
    with patch('post_to_linkedin.get_person_urn') as mock_urn:
        mock_urn.return_value = "urn:li:person:123456"
        
        result = create_ugc_post("token", "urn:li:person:123456", "Test")
        
        assert result['id'] == "urn:li:ugcPost:1234567890"
        assert len(responses.calls) == 2  # userinfo + ugcPosts
```

### Real API Tests (Slow, Requires Credentials) 🐌

**Note:** LinkedIn API doesn't provide a delete endpoint for UGC posts. Posts cannot be deleted via API. For testing:

1. **Use Test Account:** Create posts on a dedicated test LinkedIn account
2. **Manual Cleanup:** Delete posts manually after tests
3. **Test Markers:** Use unique test markers in post content for easy identification
4. **Skip by Default:** Only run when explicitly enabled

```python
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv('LINKEDIN_TEST_ENABLED'),
    reason="Requires LINKEDIN_TEST_ENABLED=1"
)
def test_real_post_creation(real_credentials, tmp_path):
    """Create a real post (requires credentials and manual cleanup)"""
    # Create test post with unique marker
    import uuid
    test_marker = f"TEST-{uuid.uuid4().hex[:8]}"
    post_content = f"TEST POST {test_marker} - Will be manually deleted"
    
    post_file = tmp_path / "real-test-post.txt"
    post_file.write_text(post_content)
    
    # Create post
    result = create_real_post(post_file)
    post_id = result['id']
    post_url = get_post_url(post_id)
    
    # Verify
    assert post_id is not None
    assert "linkedin.com" in post_url
    
    # Note: Post must be deleted manually via LinkedIn UI
    # Test marker helps identify test posts for cleanup
    print(f"\n⚠️  Test post created: {post_url}")
    print(f"⚠️  Marker: {test_marker}")
    print(f"⚠️  Please delete manually after verification")
```

---

## Test File Structure

### Pytest Configuration (conftest.py)

```python
"""
Pytest configuration and shared fixtures for post-to-linkedin tests
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, patch

# Add scripts directory to Python path
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Register custom pytest marks to avoid warnings
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "integration: integration tests with mocked API")
    config.addinivalue_line("markers", "integration_real: integration tests with real LinkedIn API")
    config.addinivalue_line("markers", "slow: slow running tests")

# Shared fixtures
@pytest.fixture
def mock_credentials():
    """Mock credentials for all tests"""
    with patch('post_to_linkedin.load_linkedin_credentials') as mock:
        mock.return_value = {
            'LINKEDIN_ACCESS_TOKEN': 'test_token',
            'LINKEDIN_REFRESH_TOKEN': 'test_refresh_token',
            'LINKEDIN_CLIENT_ID': 'test_client_id',
            'LINKEDIN_CLIENT_SECRET': 'test_client_secret'
        }
        yield mock

@pytest.fixture
def sample_post_file(tmp_path):
    """Create a sample post file for testing"""
    post_file = tmp_path / "sample-post.txt"
    post_file.write_text("Sample LinkedIn post content for testing.")
    return post_file
```

### Complete Test File Example

```python
"""
Test suite for post-to-linkedin.py

Run fast tests (mocked):
    pytest tests/test_post_to_linkedin.py -v

Run all tests including integration:
    LINKEDIN_TEST_ENABLED=1 pytest tests/test_post_to_linkedin.py -m integration
"""

import sys
import pytest
import responses
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import json

# Add scripts directory to Python path
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# Import functions to test
from post_to_linkedin import (
    validate_content,
    read_post_file,
    get_post_url,
    create_ugc_post,
    get_person_urn,
    refresh_access_token
)

################################################################################
# Unit Tests - Fast, No API Calls
################################################################################

class TestValidateContent:
    """Test content validation"""
    
    def test_valid_content(self):
        content = "Valid post content" * 50
        is_valid, error = validate_content(content)
        assert is_valid is True
        assert error is None
    
    def test_empty_content(self):
        is_valid, error = validate_content("")
        assert is_valid is False
        assert "empty" in error.lower()
    
    def test_too_long(self):
        content = "x" * 3001
        is_valid, error = validate_content(content)
        assert is_valid is False
        assert "3000" in error

class TestReadPostFile:
    """Test file reading"""
    
    def test_read_existing_file(self, tmp_path):
        post_file = tmp_path / "test.txt"
        post_file.write_text("Test content")
        
        content = read_post_file(post_file)
        assert content == "Test content"
    
    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            read_post_file(Path("/nonexistent/file.txt"))

class TestGetPostUrl:
    """Test URL construction"""
    
    def test_ugc_post_urn(self):
        url = get_post_url("urn:li:ugcPost:1234567890")
        assert url == "https://www.linkedin.com/feed/update/1234567890"
    
    def test_share_urn(self):
        url = get_post_url("urn:li:share:9876543210")
        assert url == "https://www.linkedin.com/feed/update/9876543210"

################################################################################
# Integration Tests - Mocked API (Fast)
################################################################################

@responses.activate
class TestCreateUgcPost:
    """Test post creation with mocked API"""
    
    def test_successful_post(self):
        responses.add(
            responses.POST,
            "https://api.linkedin.com/v2/ugcPosts",
            json={"id": "urn:li:ugcPost:123"},
            status=201
        )
        
        result = create_ugc_post("token", "urn:li:person:123", "Content")
        assert result['id'] == "urn:li:ugcPost:123"
    
    def test_duplicate_post(self):
        responses.add(
            responses.POST,
            "https://api.linkedin.com/v2/ugcPosts",
            json={"message": "Content is a duplicate of urn:li:share:456"},
            status=422
        )
        
        result = create_ugc_post("token", "urn:li:person:123", "Duplicate")
        assert result.get('duplicate') is True
    
    def test_api_error(self):
        responses.add(
            responses.POST,
            "https://api.linkedin.com/v2/ugcPosts",
            json={"message": "Unauthorized"},
            status=401
        )
        
        result = create_ugc_post("token", "urn:li:person:123", "Content")
        assert result is None

@responses.activate
class TestGetPersonUrn:
    """Test person URN retrieval"""
    
    def test_successful_retrieval(self):
        responses.add(
            responses.GET,
            "https://api.linkedin.com/v2/userinfo",
            json={"sub": "123456"},
            status=200
        )
        
        urn = get_person_urn("token")
        assert urn == "urn:li:person:123456"
    
    def test_invalid_token(self):
        responses.add(
            responses.GET,
            "https://api.linkedin.com/v2/userinfo",
            json={"error": "Invalid token"},
            status=401
        )
        
        urn = get_person_urn("invalid_token")
        assert urn is None

################################################################################
# Integration Tests - Real API (Slow, Optional)
################################################################################

@pytest.mark.integration_real
@pytest.mark.skipif(
    not os.getenv('LINKEDIN_TEST_ENABLED'),
    reason="Requires LINKEDIN_TEST_ENABLED=1 and real credentials"
)
class TestRealApi:
    """Test with real LinkedIn API (requires credentials)"""
    
    def test_real_post_creation(self, real_credentials, tmp_path):
        """Create a real post (manual cleanup required)"""
        import uuid
        marker = f"TEST-{uuid.uuid4().hex[:8]}"
        post_file = tmp_path / "real-test.txt"
        post_file.write_text(f"TEST POST {marker} - Delete after test")
        
        # This would call the real API
        # result = create_real_post(post_file)
        # assert result is not None
        
        # Note: Post deletion not available via API
        # Must be deleted manually via LinkedIn UI
        pytest.skip("Real API tests require manual implementation and cleanup")
```

---

## Running Tests

### Using Makefile (Recommended)

The project includes a `Makefile` that provides convenient test targets:

```bash
cd LinkedIn-posts

# Show all available targets
make help

# Install test dependencies (first time setup)
make install-test-deps

# Run all fast tests (mocked, default)
make test

# Run specific test categories
make test-unit              # Unit tests only (fastest)
make test-integration       # Integration tests with mocked API (fast)
make test-integration-real  # Real API tests (slow, requires LINKEDIN_TEST_ENABLED=1)

# Run with coverage report
make test-coverage

# Run with verbose output
make test-verbose

# Check if dependencies are installed
make check-deps

# Code quality checks
make lint
make type-check

# Clean test artifacts
make clean
```

### Direct pytest Commands

You can also run pytest directly:

```bash
# Run all fast tests (mocked)
cd LinkedIn-posts
pytest tests/ -v

# Run specific test file
pytest tests/test_post_to_linkedin.py -v

# Run specific test class
pytest tests/test_post_to_linkedin.py::TestValidateContent -v

# Run with coverage
pytest tests/ --cov=scripts/post_to_linkedin --cov-report=html
```

### Slow/Integration Tests

```bash
# Run integration tests with real API (requires credentials)
cd LinkedIn-posts
LINKEDIN_TEST_ENABLED=1 make test-integration-real

# Or with pytest directly
LINKEDIN_TEST_ENABLED=1 pytest tests/ -m integration_real

# Skip slow tests
pytest tests/ -m "not integration_real"
```

### Parallel Execution

```bash
# Install pytest-xdist for parallel execution
pip install --user pytest-xdist

# Run tests in parallel (faster)
pytest tests/ -n auto

# Specific number of workers
pytest tests/ -n 4
```

---

## Test Coverage Goals

**Target Coverage:**
- **Unit Tests:** 90%+ coverage of pure functions
- **Integration Tests (Mocked):** 80%+ coverage of API interaction logic
- **Integration Tests (Real):** Critical paths only (10-20% of codebase)

**Functions to Test:**
- ✅ `validate_content` - 100% coverage
- ✅ `read_post_file` - 100% coverage
- ✅ `get_post_url` - 100% coverage
- ✅ `create_ugc_post` - 90%+ coverage (mocked)
- ✅ `get_person_urn` - 90%+ coverage (mocked)
- ✅ `refresh_access_token` - 90%+ coverage (mocked)
- ✅ `update_markdown_archive` - 80%+ coverage
- ⚠️ `main` function - 70%+ coverage (complex, test key paths)

---

## Best Practices

1. **Fast Tests First:** Write mocked tests for speed
2. **Isolate Dependencies:** Mock all external calls (API, file system, credentials)
3. **Test Error Paths:** Don't just test happy paths
4. **Use Fixtures:** Reusable test setup/teardown
5. **Mark Slow Tests:** Use `@pytest.mark.slow` or `@pytest.mark.integration`
6. **Clean Up:** Always clean up test artifacts (files, mocks)
7. **Test Data:** Use fixtures directory for test post files
8. **Parallel Safe:** Ensure tests can run in parallel (no shared state)

---

## Example Test Execution Times

**Expected Performance:**
- **Unit Tests:** < 1 second total (50+ tests)
- **Mocked Integration Tests:** < 2 seconds total (20+ tests)
- **Real API Tests:** 5-10 seconds per test (network dependent)

**Total Fast Test Suite:** < 3 seconds for 70+ tests

---

## Next Steps

1. ✅ Create `Makefile` for test setup and execution
2. Create `tests/` directory structure
3. Create `conftest.py` with fixtures
4. Write unit tests for pure functions
5. Write mocked integration tests
6. Add real API tests (optional, marked as `integration_real`)
7. Set up CI/CD to run fast tests automatically (`make test`)
8. Document test markers and environment variables

## Makefile Usage

The `Makefile` provides convenient wrappers for all test operations:

**Quick Start:**
```bash
cd LinkedIn-posts
make install-test-deps  # First time only
make test               # Run all fast tests
```

**Test Categories:**
- `make test-unit` - Fast unit tests only
- `make test-integration` - Mocked API integration tests
- `make test-integration-real` - Real API tests (requires `LINKEDIN_TEST_ENABLED=1`)
- `make test-fast` - All fast tests (excludes real API)

**Development:**
- `make test-coverage` - Generate coverage report
- `make lint` - Code quality checks
- `make type-check` - Type checking
- `make clean` - Clean test artifacts

---

**Testing Strategy Created:** December 16, 2025  
**Status:** Ready for implementation
