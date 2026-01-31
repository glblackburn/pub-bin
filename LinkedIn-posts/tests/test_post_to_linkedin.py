"""
Tests for post-to-linkedin.py

Test categories:
- Unit tests: Pure functions (validate_content, read_post_file, get_post_url, update_markdown_archive)
- Integration tests (mocked): OAuth flow, API calls with mocked responses
- Integration tests (real API): Actual LinkedIn API calls (requires LINKEDIN_TEST_ENABLED=1)
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import responses
from datetime import datetime

# Import the module under test (imported via conftest.py)
import post_to_linkedin


################################################################################
# Unit Tests - Pure Functions
################################################################################

class TestValidateContent:
    """Test validate_content function"""
    
    def test_valid_content(self, sample_post_content):
        """Test validation of valid content"""
        is_valid, error_msg = post_to_linkedin.validate_content(sample_post_content)
        assert is_valid is True
        assert error_msg is None
    
    def test_empty_content(self, empty_post_content):
        """Test validation of empty content"""
        is_valid, error_msg = post_to_linkedin.validate_content(empty_post_content)
        assert is_valid is False
        assert error_msg == "Post content is empty"
    
    def test_whitespace_only_content(self, whitespace_only_post):
        """Test validation of whitespace-only content"""
        is_valid, error_msg = post_to_linkedin.validate_content(whitespace_only_post)
        assert is_valid is False
        assert error_msg == "Post content is empty"
    
    def test_content_too_long(self, long_post_content):
        """Test validation of content exceeding character limit"""
        is_valid, error_msg = post_to_linkedin.validate_content(long_post_content)
        assert is_valid is False
        assert "exceeds 3000 character limit" in error_msg
        assert "3001 characters" in error_msg
    
    def test_content_at_limit(self):
        """Test validation of content exactly at character limit"""
        content = "x" * 3000  # Exactly at limit
        is_valid, error_msg = post_to_linkedin.validate_content(content)
        assert is_valid is True
        assert error_msg is None
    
    def test_content_one_over_limit(self):
        """Test validation of content one character over limit"""
        content = "x" * 3001  # One over limit
        is_valid, error_msg = post_to_linkedin.validate_content(content)
        assert is_valid is False
        assert "exceeds 3000 character limit" in error_msg

    def test_unguarded_filename_py_fails(self):
        """Test validation fails when content contains unguarded .py filename"""
        content = "I built post-to-linkedin.py to handle OAuth."
        is_valid, error_msg = post_to_linkedin.validate_content(content)
        assert is_valid is False
        assert "post-to-linkedin.py" in error_msg
        assert "auto-link" in error_msg or "zero-width" in error_msg

    def test_unguarded_filename_sh_fails(self):
        """Test validation fails when content contains unguarded .sh filename"""
        content = "Run load-ssh-key.sh to load your key."
        is_valid, error_msg = post_to_linkedin.validate_content(content)
        assert is_valid is False
        assert "load-ssh-key.sh" in error_msg

    def test_guarded_filename_passes(self):
        """Test validation passes when filename has zero-width space before extension"""
        zwsp = "\u200b"
        content = f"I built post-to-linkedin{zwsp}.py to handle OAuth."
        is_valid, error_msg = post_to_linkedin.validate_content(content)
        assert is_valid is True
        assert error_msg is None

    def test_filename_in_url_passes(self):
        """Test validation passes when .py appears only inside a URL"""
        content = "Test suite: https://github.com/glblackburn/pub-bin/tree/main/LinkedIn-posts/tests"
        is_valid, error_msg = post_to_linkedin.validate_content(content)
        assert is_valid is True
        assert error_msg is None

    def test_multiple_unguarded_filenames_fails(self):
        """Test validation fails and lists all unguarded filenames"""
        content = "Use script.py and helper.sh together."
        is_valid, error_msg = post_to_linkedin.validate_content(content)
        assert is_valid is False
        assert "script.py" in error_msg
        assert "helper.sh" in error_msg

    def test_no_filename_extension_passes(self):
        """Test validation passes when no file extensions are present"""
        content = "Sample LinkedIn post content for testing.\nNo scripts or files here."
        is_valid, error_msg = post_to_linkedin.validate_content(content)
        assert is_valid is True
        assert error_msg is None


class TestFindUnguardedFilenames:
    """Test find_unguarded_filenames function"""

    def test_finds_unguarded_py(self):
        """Test that unguarded .py filename is found"""
        content = "I use post-to-linkedin.py for posting."
        found = post_to_linkedin.find_unguarded_filenames(content)
        assert "post-to-linkedin.py" in found

    def test_ignores_guarded_py(self):
        """Test that ZWSP before .py is not reported"""
        zwsp = "\u200b"
        content = f"I use post-to-linkedin{zwsp}.py for posting."
        found = post_to_linkedin.find_unguarded_filenames(content)
        assert "post-to-linkedin.py" not in found
        assert len(found) == 0

    def test_ignores_filename_in_url(self):
        """Test that filename inside URL is not reported"""
        content = "See https://example.com/repo/script.py for code."
        found = post_to_linkedin.find_unguarded_filenames(content)
        assert len(found) == 0

    def test_empty_content_returns_empty(self):
        """Test empty content returns empty list"""
        assert post_to_linkedin.find_unguarded_filenames("") == []
        assert post_to_linkedin.find_unguarded_filenames("   ") == []


class TestReadPostFile:
    """Test read_post_file function"""
    
    def test_read_existing_file(self, sample_post_file):
        """Test reading an existing post file"""
        content = post_to_linkedin.read_post_file(sample_post_file)
        assert content == "Sample LinkedIn post content for testing.\nThis is a test post with multiple lines."
    
    def test_read_nonexistent_file(self, tmp_path):
        """Test reading a non-existent file raises FileNotFoundError"""
        nonexistent_file = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError) as exc_info:
            post_to_linkedin.read_post_file(nonexistent_file)
        assert "not found" in str(exc_info.value).lower()
    
    def test_read_file_with_unicode(self, tmp_path):
        """Test reading file with Unicode characters"""
        unicode_file = tmp_path / "unicode-post.txt"
        unicode_content = "Test post with Unicode: 🚀 📝 ✅"
        unicode_file.write_text(unicode_content, encoding='utf-8')
        
        content = post_to_linkedin.read_post_file(unicode_file)
        assert content == unicode_content
    
    def test_read_file_encoding(self, tmp_path):
        """Test that file is read with UTF-8 encoding"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content", encoding='utf-8')
        
        content = post_to_linkedin.read_post_file(test_file)
        assert content == "Test content"


class TestGetPostUrl:
    """Test get_post_url function"""
    
    def test_ugc_post_urn(self):
        """Test URL construction from UGC post URN"""
        post_id = "urn:li:ugcPost:1234567890"
        url = post_to_linkedin.get_post_url(post_id)
        assert url == "https://www.linkedin.com/feed/update/1234567890"
    
    def test_share_urn(self):
        """Test URL construction from share URN"""
        post_id = "urn:li:share:9876543210"
        url = post_to_linkedin.get_post_url(post_id)
        assert url == "https://www.linkedin.com/feed/update/9876543210"
    
    def test_person_urn_format(self):
        """Test URL construction from person URN format"""
        post_id = "urn:li:person:123456"
        url = post_to_linkedin.get_post_url(post_id)
        assert url == "https://www.linkedin.com/feed/update/123456"
    
    def test_numeric_id(self):
        """Test URL construction from numeric ID"""
        post_id = "1234567890"
        url = post_to_linkedin.get_post_url(post_id)
        assert url == "https://www.linkedin.com/feed/update/1234567890"
    
    def test_urn_with_multiple_colons(self):
        """Test URL construction from URN with multiple colons"""
        post_id = "urn:li:ugcPost:123:456:789"
        url = post_to_linkedin.get_post_url(post_id)
        # Should extract the last numeric part
        assert url == "https://www.linkedin.com/feed/update/789"


class TestUpdateMarkdownArchive:
    """Test update_markdown_archive function"""
    
    def test_create_new_archive(self, tmp_path, sample_post_file):
        """Test creating a new archive file"""
        archive_file = tmp_path / "LinkedIn-posts.md"
        post_url = "https://www.linkedin.com/feed/update/1234567890"
        
        # Create a post file with date in filename
        dated_post_file = tmp_path / "2025-12-15-test-post.txt"
        dated_post_file.write_text("Test post content")
        
        result = post_to_linkedin.update_markdown_archive(
            post_url, dated_post_file, archive_file
        )
        
        assert result is True
        assert archive_file.exists()
        
        content = archive_file.read_text(encoding='utf-8')
        assert "LinkedIn Posts Archive" in content
        assert "December 15, 2025" in content
        assert post_url in content
    
    def test_update_existing_archive(self, existing_archive_file, tmp_path):
        """Test updating an existing archive file"""
        post_url = "https://www.linkedin.com/feed/update/222222"
        
        # Create a post file with date in filename
        dated_post_file = tmp_path / "2025-12-16-test-post.txt"
        dated_post_file.write_text("New test post content")
        
        result = post_to_linkedin.update_markdown_archive(
            post_url, dated_post_file, existing_archive_file
        )
        
        assert result is True
        
        content = existing_archive_file.read_text(encoding='utf-8')
        # Should have both old and new entries
        assert "December 10, 2025" in content
        assert "December 16, 2025" in content
        assert "222222" in content
    
    def test_archive_with_no_date_in_filename(self, archive_file, tmp_path):
        """Test archive update when post file has no date in filename"""
        post_url = "https://www.linkedin.com/feed/update/333333"
        
        # Create a post file without date in filename
        post_file = tmp_path / "test-post.txt"
        post_file.write_text("Test post content")
        
        result = post_to_linkedin.update_markdown_archive(
            post_url, post_file, archive_file
        )
        
        assert result is True
        
        content = archive_file.read_text(encoding='utf-8')
        # Should use current date
        current_date = datetime.now().strftime('%B %d, %Y')
        assert current_date in content
        assert post_url in content
    
    def test_archive_update_failure(self, tmp_path):
        """Test archive update failure handling"""
        post_url = "https://www.linkedin.com/feed/update/444444"
        
        # Create a post file
        post_file = tmp_path / "test-post.txt"
        post_file.write_text("Test post content")
        
        # Create a directory with the archive filename to cause write failure
        archive_file = tmp_path / "LinkedIn-posts.md"
        archive_file.mkdir()  # Make it a directory instead of a file
        
        result = post_to_linkedin.update_markdown_archive(
            post_url, post_file, archive_file
        )
        
        assert result is False


################################################################################
# Integration Tests - Mocked API
################################################################################

@pytest.mark.integration
class TestGetPersonUrn:
    """Test get_person_urn function with mocked API"""
    
    @responses.activate
    def test_successful_person_urn_retrieval(self):
        """Test successful retrieval of person URN"""
        responses.add(
            responses.GET,
            "https://api.linkedin.com/v2/userinfo",
            json={"sub": "123456789"},
            status=200
        )
        
        urn = post_to_linkedin.get_person_urn("test_token")
        assert urn == "urn:li:person:123456789"
    
    @responses.activate
    def test_person_urn_already_in_urn_format(self):
        """Test person URN that's already in URN format"""
        responses.add(
            responses.GET,
            "https://api.linkedin.com/v2/userinfo",
            json={"sub": "urn:li:person:123456789"},
            status=200
        )
        
        urn = post_to_linkedin.get_person_urn("test_token")
        assert urn == "urn:li:person:123456789"
    
    @responses.activate
    def test_invalid_token(self):
        """Test person URN retrieval with invalid token"""
        responses.add(
            responses.GET,
            "https://api.linkedin.com/v2/userinfo",
            json={"error": "Invalid token"},
            status=401
        )
        
        urn = post_to_linkedin.get_person_urn("invalid_token")
        assert urn is None
    
    @responses.activate
    def test_missing_sub_field(self):
        """Test person URN retrieval when 'sub' field is missing"""
        responses.add(
            responses.GET,
            "https://api.linkedin.com/v2/userinfo",
            json={"name": "Test User"},
            status=200
        )
        
        urn = post_to_linkedin.get_person_urn("test_token")
        assert urn is None
    
    @patch('post_to_linkedin.requests.get')
    def test_network_error(self, mock_get):
        """Test person URN retrieval with network error"""
        import requests
        # Mock requests.get to raise an exception
        mock_get.side_effect = requests.RequestException("Network error")
        
        urn = post_to_linkedin.get_person_urn("test_token")
        assert urn is None


@pytest.mark.integration
class TestCreateUgcPost:
    """Test create_ugc_post function with mocked API"""
    
    @responses.activate
    def test_successful_post_creation(self, mock_person_urn):
        """Test successful post creation"""
        responses.add(
            responses.POST,
            "https://api.linkedin.com/v2/ugcPosts",
            json={
                'id': 'urn:li:ugcPost:987654321',
                'activity': 'https://www.linkedin.com/feed/update/987654321'
            },
            status=201
        )
        
        result = post_to_linkedin.create_ugc_post(
            "test_token",
            mock_person_urn,
            "Test post content"
        )
        
        assert result is not None
        assert result['id'] == 'urn:li:ugcPost:987654321'
        
        # Verify request payload
        assert len(responses.calls) == 1
        request = responses.calls[0].request
        assert request.method == 'POST'
        payload = json.loads(request.body)
        assert payload['author'] == mock_person_urn
        assert payload['lifecycleState'] == 'PUBLISHED'
        assert payload['specificContent']['com.linkedin.ugc.ShareContent']['shareCommentary']['text'] == "Test post content"
    
    @responses.activate
    def test_duplicate_post_detection(self, mock_person_urn):
        """Test duplicate post detection"""
        error_message = "Content is a duplicate of urn:li:share:1234567890"
        responses.add(
            responses.POST,
            "https://api.linkedin.com/v2/ugcPosts",
            json={
                'message': error_message,
                'status': 422
            },
            status=422
        )
        
        result = post_to_linkedin.create_ugc_post(
            "test_token",
            mock_person_urn,
            "Duplicate content"
        )
        
        assert result is not None
        assert result.get('duplicate') is True
        assert result.get('existing_share_id') == '1234567890'
        assert result['id'] == 'urn:li:share:1234567890'
    
    @patch('post_to_linkedin.requests.post')
    def test_post_creation_with_network_error(self, mock_post, mock_person_urn):
        """Test post creation with network error"""
        import requests
        # Mock requests.post to raise an exception
        mock_post.side_effect = requests.RequestException("Network error")
        
        result = post_to_linkedin.create_ugc_post(
            "test_token",
            mock_person_urn,
            "Test content"
        )
        
        assert result is None
    
    @responses.activate
    def test_post_creation_with_unauthorized(self, mock_person_urn):
        """Test post creation with unauthorized error"""
        responses.add(
            responses.POST,
            "https://api.linkedin.com/v2/ugcPosts",
            json={"error": "Unauthorized"},
            status=401
        )
        
        result = post_to_linkedin.create_ugc_post(
            "invalid_token",
            mock_person_urn,
            "Test content"
        )
        
        assert result is None


@pytest.mark.integration
class TestRefreshAccessToken:
    """Test refresh_access_token function with mocked API"""
    
    @responses.activate
    def test_successful_token_refresh(self):
        """Test successful token refresh"""
        responses.add(
            responses.POST,
            "https://www.linkedin.com/oauth/v2/accessToken",
            json={
                'access_token': 'new_access_token_12345',
                'expires_in': 3600
            },
            status=200
        )
        
        new_token = post_to_linkedin.refresh_access_token(
            "client_id",
            "client_secret",
            "refresh_token"
        )
        
        assert new_token == 'new_access_token_12345'
    
    @responses.activate
    def test_token_refresh_failure(self):
        """Test token refresh failure"""
        responses.add(
            responses.POST,
            "https://www.linkedin.com/oauth/v2/accessToken",
            json={"error": "invalid_grant"},
            status=400
        )
        
        new_token = post_to_linkedin.refresh_access_token(
            "client_id",
            "client_secret",
            "invalid_refresh_token"
        )
        
        assert new_token is None


@pytest.mark.integration
class TestCompleteOAuthFlow:
    """Test complete_oauth_flow function with mocked inputs"""
    
    @patch('post_to_linkedin.webbrowser.open')
    @patch('post_to_linkedin.input')
    @patch('post_to_linkedin.save_credentials_partial')
    @responses.activate
    def test_successful_oauth_flow(self, mock_save, mock_input, mock_browser):
        """Test successful OAuth flow"""
        # Mock user input for redirect URL
        redirect_url = "http://localhost:8080?code=AUTH_CODE_123&state=STATE_TOKEN"
        mock_input.return_value = redirect_url
        
        # Mock token exchange
        responses.add(
            responses.POST,
            "https://www.linkedin.com/oauth/v2/accessToken",
            json={
                'access_token': 'access_token_123',
                'refresh_token': 'refresh_token_456',
                'expires_in': 3600
            },
            status=200
        )
        
        result = post_to_linkedin.complete_oauth_flow(
            "client_id",
            "client_secret",
            "http://localhost:8080"
        )
        
        assert result is not None
        assert result['access_token'] == 'access_token_123'
        assert result['refresh_token'] == 'refresh_token_456'
        assert mock_save.called
    
    @patch('post_to_linkedin.webbrowser.open')
    @patch('post_to_linkedin.input')
    def test_oauth_flow_with_error_in_redirect(self, mock_input, mock_browser):
        """Test OAuth flow with error in redirect URL"""
        # Mock user input with error
        redirect_url = "http://localhost:8080?error=access_denied&error_description=User%20denied"
        mock_input.return_value = redirect_url
        
        result = post_to_linkedin.complete_oauth_flow(
            "client_id",
            "client_secret",
            "http://localhost:8080"
        )
        
        assert result is None
    
    @patch('post_to_linkedin.webbrowser.open')
    @patch('post_to_linkedin.input')
    def test_oauth_flow_with_empty_redirect(self, mock_input, mock_browser):
        """Test OAuth flow with empty redirect URL"""
        mock_input.return_value = ""
        
        result = post_to_linkedin.complete_oauth_flow(
            "client_id",
            "client_secret",
            "http://localhost:8080"
        )
        
        assert result is None


@pytest.mark.integration
class TestPostCreationWorkflow:
    """Test complete post creation workflow with mocked API"""
    
    @responses.activate
    def test_complete_workflow(self, sample_post_file, mock_credentials):
        """Test complete workflow from file to post"""
        # Mock: Get person URN
        responses.add(
            responses.GET,
            "https://api.linkedin.com/v2/userinfo",
            json={"sub": "123456789"},
            status=200
        )
        
        # Mock: Create post
        responses.add(
            responses.POST,
            "https://api.linkedin.com/v2/ugcPosts",
            json={
                'id': 'urn:li:ugcPost:987654321',
                'activity': 'https://www.linkedin.com/feed/update/987654321'
            },
            status=201
        )
        
        # Execute workflow
        person_urn = post_to_linkedin.get_person_urn("test_token")
        assert person_urn == "urn:li:person:123456789"
        
        content = post_to_linkedin.read_post_file(sample_post_file)
        is_valid, error = post_to_linkedin.validate_content(content)
        assert is_valid is True
        
        result = post_to_linkedin.create_ugc_post(
            "test_token",
            person_urn,
            content
        )
        
        assert result is not None
        assert result['id'] == 'urn:li:ugcPost:987654321'

    @responses.activate
    def test_workflow_fails_when_content_has_unguarded_filename(
        self, mock_credentials, tmp_path
    ):
        """Test that workflow fails and does not call API when content has unguarded filename"""
        post_file = tmp_path / "bad-post.txt"
        post_file.write_text(
            "I built post-to-linkedin.py to handle OAuth and posting.",
            encoding="utf-8",
        )
        # No API mocks added - we expect validation to fail before any request

        with patch("sys.argv", ["post-to-linkedin.py", str(post_file)]):
            exit_code = post_to_linkedin.main()

        assert exit_code == 1
        assert len(responses.calls) == 0

    @responses.activate
    @patch("post_to_linkedin.webbrowser.open")
    def test_workflow_succeeds_when_filename_guarded(
        self, mock_browser, mock_credentials, tmp_path
    ):
        """Test that workflow succeeds when filename has zero-width space"""
        zwsp = "\u200b"
        post_file = tmp_path / "good-post.txt"
        post_file.write_text(
            f"I built post-to-linkedin{zwsp}.py to handle OAuth.",
            encoding="utf-8",
        )
        responses.add(
            responses.GET,
            "https://api.linkedin.com/v2/userinfo",
            json={"sub": "123456789"},
            status=200,
        )
        responses.add(
            responses.POST,
            "https://api.linkedin.com/v2/ugcPosts",
            json={
                "id": "urn:li:ugcPost:987654321",
                "activity": "https://www.linkedin.com/feed/update/987654321",
            },
            status=201,
        )

        with patch("sys.argv", ["post-to-linkedin.py", str(post_file)]):
            exit_code = post_to_linkedin.main()

        assert exit_code == 0
        assert len(responses.calls) == 2  # GET userinfo, POST ugcPosts


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
    
    def test_real_person_urn_retrieval(self, real_credentials):
        """Test getting person URN with real API"""
        access_token = real_credentials.get('LINKEDIN_ACCESS_TOKEN')
        urn = post_to_linkedin.get_person_urn(access_token)
        
        assert urn is not None
        assert urn.startswith('urn:li:person:')
    
    def test_real_post_creation(self, real_credentials, tmp_path):
        """Create a real post (manual cleanup required)"""
        import uuid
        marker = f"TEST-{uuid.uuid4().hex[:8]}"
        post_file = tmp_path / "real-test.txt"
        post_file.write_text(f"TEST POST {marker} - Delete after test\n\nThis is an automated test post.")
        
        access_token = real_credentials.get('LINKEDIN_ACCESS_TOKEN')
        person_urn = post_to_linkedin.get_person_urn(access_token)
        
        assert person_urn is not None
        
        content = post_to_linkedin.read_post_file(post_file)
        is_valid, error = post_to_linkedin.validate_content(content)
        assert is_valid is True
        
        # Create the post
        result = post_to_linkedin.create_ugc_post(
            access_token,
            person_urn,
            content
        )
        
        # Note: Post deletion not available via API
        # Must be deleted manually via LinkedIn UI
        assert result is not None
        assert 'id' in result
        
        print(f"\n⚠️  Created test post: {result.get('id')}")
        print(f"⚠️  Please delete this post manually from LinkedIn")
        print(f"⚠️  Marker: {marker}")
