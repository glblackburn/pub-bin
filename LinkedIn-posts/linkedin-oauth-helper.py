#!/usr/bin/env python3
"""
linkedin-oauth-helper.py - Helper script for LinkedIn OAuth flow

This script guides you through the OAuth 2.0 authorization flow to obtain
access and refresh tokens for the LinkedIn API.
"""

import getpass
import secrets
import sys
import urllib.parse
from pathlib import Path

try:
    import requests
    import webbrowser
except ImportError:
    print("ERROR: Required libraries not found. Install with:", file=sys.stderr)
    print("  pip install requests", file=sys.stderr)
    sys.exit(1)

################################################################################
# Constants
################################################################################

OAUTH_AUTHORIZE_URL = "https://www.linkedin.com/oauth/v2/authorization"
OAUTH_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
DEFAULT_REDIRECT_URI = "http://localhost:8080"
SCOPES = "openid profile w_member_social"

################################################################################
# Functions
################################################################################


def generate_authorization_url(client_id: str, redirect_uri: str, state: str) -> str:
    """Generate LinkedIn OAuth authorization URL."""
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'state': state,
        'scope': SCOPES
    }
    return f"{OAUTH_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(
    client_id: str,
    client_secret: str,
    authorization_code: str,
    redirect_uri: str
) -> dict:
    """Exchange authorization code for access and refresh tokens."""
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
        return response.json()
    except requests.RequestException as e:
        print(f"ERROR: Failed to exchange code for tokens: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        return {}


def main() -> int:
    """Main function to guide through OAuth flow."""
    print("=" * 80)
    print("LinkedIn OAuth Helper")
    print("=" * 80)
    print()
    print("This script will guide you through the OAuth flow to get access")
    print("and refresh tokens for the LinkedIn API.")
    print()

    # Get credentials
    client_id = input("Enter your LinkedIn Client ID: ").strip()
    if not client_id:
        print("ERROR: Client ID is required", file=sys.stderr)
        return 1

    client_secret = getpass.getpass("Enter your LinkedIn Client Secret (hidden): ").strip()
    if not client_secret:
        print("ERROR: Client Secret is required", file=sys.stderr)
        return 1

    redirect_uri = input(f"Enter redirect URI [{DEFAULT_REDIRECT_URI}]: ").strip()
    if not redirect_uri:
        redirect_uri = DEFAULT_REDIRECT_URI

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Generate authorization URL
    auth_url = generate_authorization_url(client_id, redirect_uri, state)
    print()
    print("=" * 80)
    print("Step 1: Authorize the Application")
    print("=" * 80)
    print()
    print("The authorization URL will open in your browser.")
    print("After authorizing, you'll be redirected to a URL like:")
    print(f"  {redirect_uri}?code=AUTHORIZATION_CODE&state={state}")
    print()
    print("Copy the entire redirect URL from your browser's address bar.")
    print()
    input("Press Enter to open the authorization URL in your browser...")

    # Open browser
    try:
        webbrowser.open(auth_url)
        print(f"\nOpened: {auth_url}")
    except Exception as e:
        print(f"Could not open browser: {e}")
        print(f"\nPlease open this URL manually:\n{auth_url}")

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
        return 1

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
            return 1

        # Verify state
        if 'state' not in params or params['state'][0] != state:
            print("WARNING: State mismatch. Continuing anyway...", file=sys.stderr)

        # Get authorization code
        if 'code' not in params:
            print("ERROR: No authorization code in redirect URL", file=sys.stderr)
            print(f"URL: {redirect_url}", file=sys.stderr)
            return 1

        authorization_code = params['code'][0]
    except Exception as e:
        print(f"ERROR: Failed to parse redirect URL: {e}", file=sys.stderr)
        return 1

    print()
    print("=" * 80)
    print("Step 3: Exchange Code for Tokens")
    print("=" * 80)
    print()
    print("Exchanging authorization code for access and refresh tokens...")

    token_data = exchange_code_for_tokens(
        client_id,
        client_secret,
        authorization_code,
        redirect_uri
    )

    if not token_data or 'access_token' not in token_data:
        print("ERROR: Failed to get tokens", file=sys.stderr)
        return 1

    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')
    expires_in = token_data.get('expires_in', 'unknown')

    print()
    print("=" * 80)
    print("SUCCESS: Tokens Obtained")
    print("=" * 80)
    print()
    print(f"Access Token: {access_token[:20]}...")
    print(f"Refresh Token: {refresh_token[:20] if refresh_token else 'None'}...")
    print(f"Expires In: {expires_in} seconds")
    print()
    print("Next steps:")
    print("1. Run the credential setup script:")
    print("   ./LinkedIn-posts/create-set-linkedin-credentials.py")
    print()
    print("2. When prompted, enter:")
    print(f"   Client ID: {client_id}")
    print(f"   Client Secret: (you already entered it)")
    print(f"   Access Token: {access_token}")
    if refresh_token:
        print(f"   Refresh Token: {refresh_token}")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
