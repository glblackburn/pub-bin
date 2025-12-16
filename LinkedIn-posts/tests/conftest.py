"""
Pytest configuration and shared fixtures for post-to-linkedin tests
"""

import sys
import importlib.util
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add scripts directory to Python path
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Import the module with hyphens in filename
SCRIPT_PATH = SCRIPTS_DIR / "post-to-linkedin.py"
spec = importlib.util.spec_from_file_location("post_to_linkedin", SCRIPT_PATH)
post_to_linkedin = importlib.util.module_from_spec(spec)
sys.modules["post_to_linkedin"] = post_to_linkedin
spec.loader.exec_module(post_to_linkedin)

# Register custom pytest marks to avoid warnings
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "integration: integration tests with mocked API")
    config.addinivalue_line("markers", "integration_real: integration tests with real LinkedIn API")
    config.addinivalue_line("markers", "slow: slow running tests")


@pytest.fixture
def mock_credentials():
    """Mock credentials for all tests"""
    with patch('post_to_linkedin.load_linkedin_credentials') as mock:
        mock.return_value = {
            'LINKEDIN_ACCESS_TOKEN': 'test_access_token_12345',
            'LINKEDIN_REFRESH_TOKEN': 'test_refresh_token_67890',
            'LINKEDIN_CLIENT_ID': 'test_client_id',
            'LINKEDIN_CLIENT_SECRET': 'test_client_secret',
            'LINKEDIN_REDIRECT_URI': 'http://localhost:8080'
        }
        yield mock


@pytest.fixture
def sample_post_file(tmp_path):
    """Create a sample post file for testing"""
    post_file = tmp_path / "sample-post.txt"
    post_file.write_text("Sample LinkedIn post content for testing.\nThis is a test post with multiple lines.")
    return post_file


@pytest.fixture
def sample_post_content():
    """Sample post content as string"""
    return "Sample LinkedIn post content for testing.\nThis is a test post with multiple lines."


@pytest.fixture
def long_post_content():
    """Post content that exceeds character limit"""
    return "x" * 3001  # Exceeds MAX_POST_LENGTH of 3000


@pytest.fixture
def empty_post_content():
    """Empty post content"""
    return ""


@pytest.fixture
def whitespace_only_post():
    """Post content with only whitespace"""
    return "   \n\t  \n  "


@pytest.fixture
def mock_person_urn():
    """Mock person URN"""
    return "urn:li:person:123456789"


@pytest.fixture
def mock_post_response():
    """Mock successful post creation response"""
    return {
        'id': 'urn:li:ugcPost:987654321',
        'activity': 'https://www.linkedin.com/feed/update/987654321',
        'shareUrl': 'https://www.linkedin.com/feed/update/987654321'
    }


@pytest.fixture
def mock_duplicate_post_response():
    """Mock duplicate post response"""
    return {
        'id': 'urn:li:share:1234567890',
        'duplicate': True,
        'existing_share_id': '1234567890'
    }


@pytest.fixture
def archive_file(tmp_path):
    """Create a temporary archive file for testing"""
    archive = tmp_path / "LinkedIn-posts.md"
    archive.write_text("# LinkedIn Posts Archive\n\n")
    return archive


@pytest.fixture
def existing_archive_file(tmp_path):
    """Create an archive file with existing entries"""
    archive = tmp_path / "LinkedIn-posts.md"
    content = """# LinkedIn Posts Archive

## [December 10, 2025](https://www.linkedin.com/feed/update/111111)

**LinkedIn:** [https://www.linkedin.com/feed/update/111111](https://www.linkedin.com/feed/update/111111)

---

"""
    archive.write_text(content)
    return archive


@pytest.fixture
def mock_requests_get(monkeypatch):
    """Mock requests.get for API calls"""
    def mock_get(*args, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'sub': '123456789'}
        mock_response.raise_for_status = MagicMock()
        return mock_response
    monkeypatch.setattr('post_to_linkedin.requests.get', mock_get)
    return mock_get


@pytest.fixture
def mock_requests_post(monkeypatch):
    """Mock requests.post for API calls"""
    def mock_post(*args, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 'urn:li:ugcPost:987654321',
            'activity': 'https://www.linkedin.com/feed/update/987654321'
        }
        mock_response.raise_for_status = MagicMock()
        return mock_response
    monkeypatch.setattr('post_to_linkedin.requests.post', mock_post)
    return mock_post


@pytest.fixture
def mock_webbrowser_open(monkeypatch):
    """Mock webbrowser.open to prevent actual browser opening"""
    mock_open = MagicMock()
    monkeypatch.setattr('post_to_linkedin.webbrowser.open', mock_open)
    return mock_open


@pytest.fixture
def real_credentials(monkeypatch):
    """Fixture for real API tests - requires LINKEDIN_TEST_ENABLED=1"""
    import os
    if not os.getenv('LINKEDIN_TEST_ENABLED'):
        pytest.skip("Real API tests require LINKEDIN_TEST_ENABLED=1")
    
    # Load actual credentials from environment or secure file
    from post_to_linkedin import load_linkedin_credentials
    creds = load_linkedin_credentials()
    
    if not all([
        creds.get('LINKEDIN_CLIENT_ID'),
        creds.get('LINKEDIN_CLIENT_SECRET'),
        creds.get('LINKEDIN_ACCESS_TOKEN')
    ]):
        pytest.skip("Real API tests require valid credentials")
    
    return creds
