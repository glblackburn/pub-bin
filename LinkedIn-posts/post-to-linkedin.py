#!/usr/bin/env python3
"""
post-to-linkedin.py - Post .txt files to LinkedIn

Reads a .txt file containing LinkedIn post content and posts it to LinkedIn
using the LinkedIn API v2 UGC Posts API. Automatically updates the markdown
archive with the post URL after successful posting.
"""

import argparse
import getpass
import json
import os
import re
import secrets
import stat
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    import requests
    import webbrowser
except ImportError:
    print("ERROR: 'requests' library is required. Install it with:", file=sys.stderr)
    print("  pip install requests", file=sys.stderr)
    sys.exit(1)

from linkedin_credentials import load_linkedin_credentials

################################################################################
# Constants
################################################################################

LINKEDIN_API_BASE = "https://api.linkedin.com/v2"
MAX_POST_LENGTH = 3000  # LinkedIn character limit for posts
OAUTH_AUTHORIZE_URL = "https://www.linkedin.com/oauth/v2/authorization"
OAUTH_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
DEFAULT_REDIRECT_URI = "http://localhost:8080"
OAUTH_SCOPES = "openid profile w_member_social"
CREATE_API_KEY_URL = "https://www.linkedin.com/developers/apps"

################################################################################
# Functions
################################################################################


def complete_oauth_flow(client_id: str, client_secret: str, redirect_uri: str) -> Optional[Dict[str, str]]:
    """
    Complete OAuth flow to get access and refresh tokens.

    Args:
        client_id: LinkedIn Client ID
        client_secret: LinkedIn Client Secret
        redirect_uri: OAuth redirect URI

    Returns:
        Dictionary with access_token and refresh_token, or None if failed
    """
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Generate authorization URL
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'state': state,
        'scope': OAUTH_SCOPES
    }
    auth_url = f"{OAUTH_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    print("\n" + "=" * 80)
    print("Step 1: Authorize the Application")
    print("=" * 80)
    print()
    print("Opening authorization URL in your browser...")
    
    # Open browser automatically
    try:
        webbrowser.open(auth_url)
        print(f"Opened: {auth_url}")
    except Exception as e:
        print(f"Could not open browser: {e}")
        print(f"\nPlease open this URL manually:\n{auth_url}")
    
    print()
    print("After authorizing, you'll be redirected to a URL like:")
    print(f"  {redirect_uri}?code=AUTHORIZATION_CODE&state={state}")
    print()
    print("Copy the entire redirect URL from your browser's address bar.")
    print()

    print()
    print("=" * 80)
    print("Step 2: Get Authorization Code")
    print("=" * 80)
    print()
    print("After authorizing, you'll be redirected. Copy the ENTIRE redirect URL")
    print("from your browser's address bar and paste it below.")
    print()
    redirect_url = input("Paste the redirect URL here: ").strip()

    if not redirect_url:
        print("ERROR: Redirect URL is required", file=sys.stderr)
        return None

    # Parse redirect URL
    try:
        parsed = urllib.parse.urlparse(redirect_url)
        params = urllib.parse.parse_qs(parsed.query)

        # Check for errors
        if 'error' in params:
            error = params['error'][0]
            error_desc = params.get('error_description', [''])[0]
            print(f"\nERROR: Authorization failed: {error}", file=sys.stderr)
            if error_desc:
                print(f"Description: {error_desc}", file=sys.stderr)
            return None

        # Verify state
        if 'state' not in params or params['state'][0] != state:
            print("WARNING: State mismatch. Continuing anyway...", file=sys.stderr)

        # Get authorization code
        if 'code' not in params:
            print("ERROR: No authorization code in redirect URL", file=sys.stderr)
            print(f"URL: {redirect_url}", file=sys.stderr)
            return None

        authorization_code = params['code'][0]
    except Exception as e:
        print(f"ERROR: Failed to parse redirect URL: {e}", file=sys.stderr)
        return None

    print()
    print("=" * 80)
    print("Step 3: Exchange Code for Tokens")
    print("=" * 80)
    print()
    print("Exchanging authorization code for access and refresh tokens...")

    # Exchange code for tokens
    data = {
        'grant_type': 'authorization_code',
        'code': authorization_code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret
    }

    try:
        response = requests.post(OAUTH_TOKEN_URL, data=data, timeout=10)
        response.raise_for_status()
        token_data = response.json()
    except requests.RequestException as e:
        print(f"ERROR: Failed to exchange code for tokens: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        return None

    if 'access_token' not in token_data:
        print("ERROR: No access token in response", file=sys.stderr)
        return None

    return {
        'access_token': token_data.get('access_token'),
        'refresh_token': token_data.get('refresh_token'),
        'expires_in': token_data.get('expires_in')
    }


def setup_credentials_interactive() -> Optional[Dict[str, str]]:
    """
    Interactive setup for LinkedIn API credentials including OAuth flow.

    Returns:
        Dictionary with all credentials, or None if setup failed/cancelled
    """
    print("\n" + "=" * 80)
    print("LinkedIn API Credential Setup")
    print("=" * 80)
    print()
    print("This will guide you through setting up your LinkedIn API credentials.")
    print("You'll need:")
    print("  1. A LinkedIn Developer app (we'll help you create one)")
    print("  2. Client ID and Client Secret from your app")
    print("  3. Complete OAuth flow to get Access Token and Refresh Token")
    print()
    response = input("Press Enter to continue, or 'q' to quit: ").strip()
    if response.lower() == 'q':
        return None

    # Step 1: Get Client ID and Secret
    print("\n" + "=" * 80)
    print("Step 1: Create LinkedIn Developer App")
    print("=" * 80)
    print()
    print("Opening LinkedIn Developer Portal in your browser...")
    try:
        webbrowser.open(CREATE_API_KEY_URL)
        print(f"Opened: {CREATE_API_KEY_URL}")
    except Exception as e:
        print(f"Could not open browser: {e}")
        print(f"Please open manually: {CREATE_API_KEY_URL}")
    print()
    print("In the browser:")
    print("1. Click 'Create app'")
    print("2. Fill in app details:")
    print("   - App name: Choose a name (e.g., 'My LinkedIn Posts')")
    print("   - LinkedIn Page: Select your page or profile")
    print("   - App use case: Select 'Other'")
    print("   - User agreement URL: (optional, can leave blank)")
    print("   - Privacy policy URL: (optional, can leave blank)")
    print("3. Click 'Create app'")
    print()
    input("Press Enter after you have created the app and are on the app dashboard...")

    print("\n" + "=" * 80)
    print("Step 1b: Get Client ID and Client Secret")
    print("=" * 80)
    print()
    print("In your LinkedIn app dashboard:")
    print("1. Go to the 'Auth' tab")
    print("2. Find your Client ID (copy it)")
    print("3. Find your Client Secret (click 'Show' to reveal it, then copy it)")
    print()
    input("Press Enter when you have copied your Client ID and Client Secret...")

    client_id = input("\nEnter your Client ID: ").strip()
    if not client_id:
        print("ERROR: Client ID is required", file=sys.stderr)
        return None

    client_secret = getpass.getpass("Enter your Client Secret (hidden): ").strip()
    if not client_secret:
        print("ERROR: Client Secret is required", file=sys.stderr)
        return None

    # Step 2: Configure redirect URI
    print("\n" + "=" * 80)
    print("Step 2: Configure Redirect URI")
    print("=" * 80)
    print()
    print("In your LinkedIn app's 'Auth' tab (should still be open in browser):")
    print("1. Scroll to 'Redirect URLs' section")
    print("2. Click 'Add redirect URL' or '+' button")
    print(f"3. Enter: {DEFAULT_REDIRECT_URI}")
    print("4. Click 'Update' or 'Save'")
    print()
    input("Press Enter after you have added the redirect URI...")
    
    redirect_uri = input(f"\nEnter redirect URI (or press Enter for default [{DEFAULT_REDIRECT_URI}]): ").strip()
    if not redirect_uri:
        redirect_uri = DEFAULT_REDIRECT_URI

    # Step 3: Request product access
    print("\n" + "=" * 80)
    print("Step 3: Request Product Access")
    print("=" * 80)
    print()
    print("In your LinkedIn app (should still be open in browser):")
    print("1. Go to the 'Products' tab")
    print("2. Find 'Sign In with LinkedIn using OpenID Connect'")
    print("   - Click 'Request access' button")
    print("3. Find 'Marketing Developer Platform'")
    print("   - Click 'Request access' button")
    print("4. Wait for both to show 'Approved' status")
    print("   (You may need to refresh the page to see updated status)")
    print()
    input("Press Enter when both products show 'Approved' status...")

    # Step 4: Complete OAuth flow
    print("\n" + "=" * 80)
    print("Step 4: Complete OAuth Flow")
    print("=" * 80)
    print()
    token_data = complete_oauth_flow(client_id, client_secret, redirect_uri)
    if not token_data:
        return None

    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')

    if not access_token:
        print("ERROR: Failed to get access token", file=sys.stderr)
        return None

    print()
    print("=" * 80)
    print("SUCCESS: Tokens Obtained")
    print("=" * 80)
    print()
    print(f"Access Token: {access_token[:20]}...")
    if refresh_token:
        print(f"Refresh Token: {refresh_token[:20]}...")
    print()

    # Step 5: Save credentials
    print("=" * 80)
    print("Step 5: Save Credentials")
    print("=" * 80)
    print()

    SECURE_DIR = Path.home() / '.secure'
    CREDENTIALS_FILE = SECURE_DIR / 'linkedin-set-api-key.sh'

    # Create secure directory
    print(f"Creating secure directory: {SECURE_DIR}")
    SECURE_DIR.mkdir(mode=0o700, exist_ok=True)

    # Write credentials file
    print(f"Creating credentials file: {CREDENTIALS_FILE}")
    with open(CREDENTIALS_FILE, 'w') as f:
        f.write(f'export LINKEDIN_CLIENT_ID="{client_id}"\n')
        f.write(f'export LINKEDIN_CLIENT_SECRET="{client_secret}"\n')
        f.write(f'export LINKEDIN_ACCESS_TOKEN="{access_token}"\n')
        if refresh_token:
            f.write(f'export LINKEDIN_REFRESH_TOKEN="{refresh_token}"\n')
        else:
            f.write(f'export LINKEDIN_REFRESH_TOKEN=""\n')

    # Set permissions: 400 (read-only for owner)
    os.chmod(CREDENTIALS_FILE, stat.S_IRUSR)

    print("=" * 80)
    print("Credentials saved successfully!")
    print(f"File: {CREDENTIALS_FILE}")
    print(f"Permissions: {oct(CREDENTIALS_FILE.stat().st_mode)[-3:]}")
    print("=" * 80)
    print()

    return {
        'client_id': client_id,
        'client_secret': client_secret,
        'access_token': access_token,
        'refresh_token': refresh_token
    }


def get_credentials(cli_args: Optional[argparse.Namespace] = None) -> Dict[str, str]:
    """
    Load credentials using three-tier priority system.
    Automatically guides user through setup if credentials are missing.

    Args:
        cli_args: Optional argparse.Namespace with credential arguments
    """
    # Tier 1: Command-line arguments (highest priority)
    client_id = cli_args.client_id if cli_args and cli_args.client_id else None
    client_secret = cli_args.client_secret if cli_args and cli_args.client_secret else None
    access_token = cli_args.access_token if cli_args and cli_args.access_token else None
    refresh_token = cli_args.refresh_token if cli_args and cli_args.refresh_token else None

    # Tier 2: Environment variables
    if not client_id:
        client_id = os.getenv('LINKEDIN_CLIENT_ID')
    if not client_secret:
        client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
    if not access_token:
        access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    if not refresh_token:
        refresh_token = os.getenv('LINKEDIN_REFRESH_TOKEN')

    # Tier 3: Secure credentials file (lowest priority)
    # This will automatically run setup script if file doesn't exist
    if not all([client_id, client_secret, access_token, refresh_token]):
        print("Loading credentials from secure file...")
        creds = load_linkedin_credentials()  # Auto-runs setup if file missing
        if not client_id:
            client_id = creds.get('LINKEDIN_CLIENT_ID')
        if not client_secret:
            client_secret = creds.get('LINKEDIN_CLIENT_SECRET')
        if not access_token:
            access_token = creds.get('LINKEDIN_ACCESS_TOKEN')
        if not refresh_token:
            refresh_token = creds.get('LINKEDIN_REFRESH_TOKEN')

    # If still missing after all tiers, run interactive setup
    if not all([client_id, client_secret, access_token, refresh_token]):
        print("\n" + "=" * 80)
        print("LinkedIn API credentials are missing or incomplete.")
        print("=" * 80)
        print("\nStarting interactive setup...")
        print("This will guide you through the complete setup process.\n")

        try:
            setup_result = setup_credentials_interactive()
            if not setup_result:
                print("\nERROR: Setup was cancelled or failed.", file=sys.stderr)
                sys.exit(1)

            # Use credentials from setup
            client_id = client_id or setup_result.get('client_id')
            client_secret = client_secret or setup_result.get('client_secret')
            access_token = access_token or setup_result.get('access_token')
            refresh_token = refresh_token or setup_result.get('refresh_token')

            # Final validation
            if not all([client_id, client_secret, access_token]):
                print("\nERROR: Setup completed but credentials are still incomplete.", file=sys.stderr)
                sys.exit(1)

            print("Setup complete! Continuing with posting...\n")
        except KeyboardInterrupt:
            print("\n\nSetup cancelled by user.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"\nERROR: Setup failed: {e}", file=sys.stderr)
            sys.exit(1)

    return {
        'client_id': client_id,
        'client_secret': client_secret,
        'access_token': access_token,
        'refresh_token': refresh_token
    }


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> Optional[str]:
    """
    Refresh the LinkedIn access token using the refresh token.

    Args:
        client_id: LinkedIn Client ID
        client_secret: LinkedIn Client Secret
        refresh_token: LinkedIn Refresh Token

    Returns:
        New access token or None if refresh failed
    """
    url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret
    }

    try:
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        return token_data.get('access_token')
    except requests.RequestException as e:
        print(f"ERROR: Failed to refresh access token: {e}", file=sys.stderr)
        return None


def get_person_urn(access_token: str) -> Optional[str]:
    """
    Get the person URN for the authenticated user.

    Args:
        access_token: LinkedIn access token

    Returns:
        Person URN (e.g., "urn:li:person:123456") or None if failed
    """
    url = f"{LINKEDIN_API_BASE}/userinfo"
    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        # The person URN is typically in the 'sub' field
        sub = data.get('sub')
        if sub:
            # Convert to URN format if needed
            if sub.startswith('urn:li:person:'):
                return sub
            return f"urn:li:person:{sub}"
        return None
    except requests.RequestException as e:
        print(f"ERROR: Failed to get person URN: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        return None


def validate_content(content: str) -> Tuple[bool, Optional[str]]:
    """
    Validate post content against LinkedIn requirements.

    Args:
        content: Post content to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not content or not content.strip():
        return False, "Post content is empty"

    if len(content) > MAX_POST_LENGTH:
        return False, f"Post content exceeds {MAX_POST_LENGTH} character limit ({len(content)} characters)"

    return True, None


def read_post_file(file_path: Path) -> str:
    """
    Read post content from a .txt file.

    Args:
        file_path: Path to the .txt file

    Returns:
        File content as string
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Post file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def create_ugc_post(access_token: str, person_urn: str, content: str) -> Optional[Dict]:
    """
    Create a UGC post on LinkedIn.

    Args:
        access_token: LinkedIn access token
        person_urn: Person URN (e.g., "urn:li:person:123456")
        content: Post content text

    Returns:
        Response data with post information or None if failed
    """
    url = f"{LINKEDIN_API_BASE}/ugcPosts"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0'
    }

    # UGC Post payload structure
    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": content
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"ERROR: Failed to create LinkedIn post: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        return None


def get_post_url(post_id: str) -> str:
    """
    Construct LinkedIn post URL from post ID.

    Args:
        post_id: Post ID from API response (e.g., "urn:li:ugcPost:123456")

    Returns:
        LinkedIn post URL
    """
    # Extract numeric ID from URN
    match = re.search(r':(\d+)$', post_id)
    if match:
        numeric_id = match.group(1)
        return f"https://www.linkedin.com/feed/update/{numeric_id}"
    # Fallback: return a generic URL
    return f"https://www.linkedin.com/feed/update/{post_id}"


def update_markdown_archive(post_url: str, post_file: Path, archive_file: Path) -> bool:
    """
    Update the LinkedIn-posts.md archive with the new post.

    Args:
        post_url: LinkedIn post URL
        post_file: Path to the original .txt post file
        archive_file: Path to LinkedIn-posts.md archive file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract date from filename or use current date
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', post_file.name)
        if date_match:
            date_str = date_match.group(1)
            # Parse date and format
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%B %d, %Y')
        else:
            formatted_date = datetime.now().strftime('%B %d, %Y')

        # Read existing archive
        if archive_file.exists():
            with open(archive_file, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = "# LinkedIn Posts Archive\n\n"

        # Create new post entry
        post_entry = f"\n## [{formatted_date}]({post_url})\n\n"
        post_entry += f"**LinkedIn:** [{post_url}]({post_url})\n\n"
        post_entry += "---\n\n"

        # Add to beginning of content (after header if exists)
        if content.startswith('# LinkedIn Posts Archive'):
            # Find where to insert (after header and any intro text)
            lines = content.split('\n')
            insert_pos = 1
            for i, line in enumerate(lines[1:], 1):
                if line.startswith('## '):
                    insert_pos = i
                    break
                if line.strip() and not line.startswith('#'):
                    insert_pos = i + 1
            lines.insert(insert_pos, post_entry)
            content = '\n'.join(lines)
        else:
            content = post_entry + content

        # Write updated archive
        with open(archive_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return True
    except Exception as e:
        print(f"ERROR: Failed to update markdown archive: {e}", file=sys.stderr)
        return False


def main() -> int:
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Post .txt file content to LinkedIn',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s post.txt
  %(prog)s LinkedIn-posts/examples/2025-12-12-network-capture-analysis-tools.txt
  %(prog)s --dry-run post.txt
        """
    )
    parser.add_argument(
        'post_file',
        type=Path,
        help='Path to .txt file containing LinkedIn post content'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate content but do not post to LinkedIn'
    )
    parser.add_argument(
        '--no-archive',
        action='store_true',
        help='Do not update LinkedIn-posts.md archive'
    )
    parser.add_argument(
        '--client-id',
        help='LinkedIn Client ID (overrides env/config)'
    )
    parser.add_argument(
        '--client-secret',
        help='LinkedIn Client Secret (overrides env/config)'
    )
    parser.add_argument(
        '--access-token',
        help='LinkedIn Access Token (overrides env/config)'
    )
    parser.add_argument(
        '--refresh-token',
        help='LinkedIn Refresh Token (overrides env/config)'
    )

    args = parser.parse_args()

    # Load credentials
    try:
        creds = get_credentials(args)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: Failed to load credentials: {e}", file=sys.stderr)
        return 1

    # Read post file
    try:
        content = read_post_file(args.post_file)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: Failed to read post file: {e}", file=sys.stderr)
        return 1

    # Validate content
    is_valid, error_msg = validate_content(content)
    if not is_valid:
        print(f"ERROR: {error_msg}", file=sys.stderr)
        return 1

    print(f"Post content validated ({len(content)} characters)")

    if args.dry_run:
        print("\nDRY RUN: Content is valid. Would post to LinkedIn.")
        print(f"\nFirst 200 characters:\n{content[:200]}...")
        return 0

    # Refresh access token if needed
    access_token = creds['access_token']
    person_urn = get_person_urn(access_token)

    # If getting person URN fails, try refreshing token
    if not person_urn:
        print("Failed to get person URN with current token. Attempting token refresh...")
        new_token = refresh_access_token(
            creds['client_id'],
            creds['client_secret'],
            creds['refresh_token']
        )
        if new_token:
            access_token = new_token
            person_urn = get_person_urn(access_token)

    if not person_urn:
        print("ERROR: Failed to get person URN. Check your access token.", file=sys.stderr)
        return 1

    print(f"Authenticated as: {person_urn}")

    # Create post
    print("Posting to LinkedIn...")
    post_response = create_ugc_post(access_token, person_urn, content)

    if not post_response:
        print("ERROR: Failed to create LinkedIn post.", file=sys.stderr)
        return 1

    # Extract post URL
    post_id = post_response.get('id', '')
    if not post_id:
        print("ERROR: Post created but no post ID in response.", file=sys.stderr)
        print(f"Response: {json.dumps(post_response, indent=2)}", file=sys.stderr)
        return 1

    post_url = get_post_url(post_id)
    print(f"\nSUCCESS: Post created successfully!")
    print(f"Post URL: {post_url}")

    # Update archive
    if not args.no_archive:
        archive_file = Path(__file__).parent / 'LinkedIn-posts.md'
        if update_markdown_archive(post_url, args.post_file, archive_file):
            print(f"Archive updated: {archive_file}")
        else:
            print(f"WARNING: Failed to update archive: {archive_file}", file=sys.stderr)

    return 0


if __name__ == '__main__':
    sys.exit(main())
