#!/usr/bin/env python3
"""
post-to-linkedin.py - Post .txt files to LinkedIn

Reads a .txt file containing LinkedIn post content and posts it to LinkedIn
using the LinkedIn API v2 UGC Posts API. Opens your LinkedIn activity page
after successful posting. Archive updates are currently manual (see root
LinkedIn-posts.md file).
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
    print("If you see an error page, copy that URL too - it contains error information.")
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
            print(f"\n" + "=" * 80, file=sys.stderr)
            print(f"ERROR: Authorization failed: {error}", file=sys.stderr)
            print("=" * 80, file=sys.stderr)
            if error_desc:
                print(f"\nDescription: {error_desc}", file=sys.stderr)
            
            # Provide helpful guidance based on common errors
            if error == 'redirect_uri_mismatch':
                print("\n" + "=" * 80, file=sys.stderr)
                print("TROUBLESHOOTING: Redirect URI Mismatch", file=sys.stderr)
                print("=" * 80, file=sys.stderr)
                print(f"\nThe redirect URI in your OAuth request ({redirect_uri})", file=sys.stderr)
                print("does not match what's configured in your LinkedIn app.", file=sys.stderr)
                print("\nTo fix:", file=sys.stderr)
                print("1. Go to your LinkedIn app's 'Auth' tab", file=sys.stderr)
                print(f"2. Make sure '{redirect_uri}' is added in 'Redirect URLs'", file=sys.stderr)
                print("3. The redirect URI must match EXACTLY (including http vs https)", file=sys.stderr)
                print("4. Click 'Update' or 'Save' after adding it", file=sys.stderr)
            elif error == 'invalid_client':
                print("\n" + "=" * 80, file=sys.stderr)
                print("TROUBLESHOOTING: Invalid Client", file=sys.stderr)
                print("=" * 80, file=sys.stderr)
                print("\nYour Client ID or Client Secret may be incorrect.", file=sys.stderr)
                print("Please verify them in your LinkedIn app's 'Auth' tab.", file=sys.stderr)
            elif error == 'access_denied':
                print("\n" + "=" * 80, file=sys.stderr)
                print("TROUBLESHOOTING: Access Denied", file=sys.stderr)
                print("=" * 80, file=sys.stderr)
                print("\nYou may have cancelled the authorization or the app", file=sys.stderr)
                print("doesn't have the required permissions.", file=sys.stderr)
                print("\nMake sure you:", file=sys.stderr)
                print("1. Click 'Allow' when asked to authorize the app", file=sys.stderr)
                print("2. Have requested access to required products in your app", file=sys.stderr)
            else:
                print(f"\nError code: {error}", file=sys.stderr)
                print("Please check your LinkedIn app configuration.", file=sys.stderr)
            
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

    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')

    # Save tokens immediately
    print("\nSaving Access Token and Refresh Token...")
    save_credentials_partial(access_token=access_token, refresh_token=refresh_token)
    print("✓ Saved")

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': token_data.get('expires_in')
    }


def save_credentials_partial(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    redirect_uri: Optional[str] = None,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None
) -> None:
    """
    Save credentials incrementally to preserve progress.

    Args:
        client_id: Client ID to save (or None to keep existing)
        client_secret: Client Secret to save (or None to keep existing)
        redirect_uri: Redirect URI to save (or None to keep existing)
        access_token: Access Token to save (or None to keep existing)
        refresh_token: Refresh Token to save (or None to keep existing)
    """
    SECURE_DIR = Path.home() / '.secure'
    CREDENTIALS_FILE = SECURE_DIR / 'linkedin-set-api-key.sh'

    # Load existing credentials if file exists
    existing = {}
    if CREDENTIALS_FILE.exists():
        creds = load_linkedin_credentials()
        existing = {
            'client_id': creds.get('LINKEDIN_CLIENT_ID', ''),
            'client_secret': creds.get('LINKEDIN_CLIENT_SECRET', ''),
            'redirect_uri': creds.get('LINKEDIN_REDIRECT_URI', ''),
            'access_token': creds.get('LINKEDIN_ACCESS_TOKEN', ''),
            'refresh_token': creds.get('LINKEDIN_REFRESH_TOKEN', '')
        }

    # Use new values or keep existing
    client_id = client_id if client_id is not None else existing.get('client_id', '')
    client_secret = client_secret if client_secret is not None else existing.get('client_secret', '')
    redirect_uri = redirect_uri if redirect_uri is not None else existing.get('redirect_uri', DEFAULT_REDIRECT_URI)
    access_token = access_token if access_token is not None else existing.get('access_token', '')
    refresh_token = refresh_token if refresh_token is not None else existing.get('refresh_token', '')

    # Create secure directory
    SECURE_DIR.mkdir(mode=0o700, exist_ok=True)

    # If file exists with restricted permissions, temporarily make it writable
    original_mode = None
    if CREDENTIALS_FILE.exists():
        try:
            original_mode = CREDENTIALS_FILE.stat().st_mode
            # Make file writable temporarily (add write permission for owner)
            os.chmod(CREDENTIALS_FILE, stat.S_IRUSR | stat.S_IWUSR)
        except OSError as e:
            print(f"WARNING: Could not change file permissions: {e}", file=sys.stderr)
            # Try to remove and recreate
            try:
                CREDENTIALS_FILE.unlink()
            except OSError:
                raise PermissionError(f"Cannot write to credentials file: {CREDENTIALS_FILE}") from e

    # Write credentials file
    try:
        with open(CREDENTIALS_FILE, 'w') as f:
            if client_id:
                f.write(f'export LINKEDIN_CLIENT_ID="{client_id}"\n')
            if client_secret:
                f.write(f'export LINKEDIN_CLIENT_SECRET="{client_secret}"\n')
            if redirect_uri:
                f.write(f'export LINKEDIN_REDIRECT_URI="{redirect_uri}"\n')
            if access_token:
                f.write(f'export LINKEDIN_ACCESS_TOKEN="{access_token}"\n')
            if refresh_token:
                f.write(f'export LINKEDIN_REFRESH_TOKEN="{refresh_token}"\n')
    except PermissionError as e:
        raise PermissionError(f"Cannot write to credentials file: {CREDENTIALS_FILE}. Check file permissions.") from e

    # Set permissions: 400 (read-only for owner)
    try:
        os.chmod(CREDENTIALS_FILE, stat.S_IRUSR)
    except OSError as e:
        print(f"WARNING: Could not set file permissions to read-only: {e}", file=sys.stderr)


def setup_credentials_interactive(skip_completed: bool = True) -> Optional[Dict[str, str]]:
    """
    Interactive setup for LinkedIn API credentials including OAuth flow.
    Saves progress incrementally so setup can be resumed.

    Returns:
        Dictionary with all credentials, or None if setup failed/cancelled
    """
    SECURE_DIR = Path.home() / '.secure'
    CREDENTIALS_FILE = SECURE_DIR / 'linkedin-set-api-key.sh'

    # Check for existing partial credentials
    existing_creds = {}
    if CREDENTIALS_FILE.exists():
        existing_creds = load_linkedin_credentials()
        has_client_id = bool(existing_creds.get('LINKEDIN_CLIENT_ID'))
        has_client_secret = bool(existing_creds.get('LINKEDIN_CLIENT_SECRET'))
        has_redirect_uri = bool(existing_creds.get('LINKEDIN_REDIRECT_URI'))
        has_access_token = bool(existing_creds.get('LINKEDIN_ACCESS_TOKEN'))
        has_refresh_token = bool(existing_creds.get('LINKEDIN_REFRESH_TOKEN'))
        
        # Check if setup is complete
        all_complete = all([has_client_id, has_client_secret, has_redirect_uri, has_access_token])
        
        if all_complete:
            print("\n" + "=" * 80)
            print("LinkedIn API Credential Setup")
            print("=" * 80)
            print()
            print("All credentials are already configured!")
            print(f"  Client ID: ✓")
            print(f"  Client Secret: ✓")
            print(f"  Redirect URI: ✓")
            print(f"  Access Token: ✓")
            print(f"  Refresh Token: {'✓' if has_refresh_token else '✗ (optional)'}")
            print()
            return {
                'client_id': existing_creds.get('LINKEDIN_CLIENT_ID'),
                'client_secret': existing_creds.get('LINKEDIN_CLIENT_SECRET'),
                'access_token': existing_creds.get('LINKEDIN_ACCESS_TOKEN'),
                'refresh_token': existing_creds.get('LINKEDIN_REFRESH_TOKEN', '')
            }
        
        # Partial credentials found
        print("\n" + "=" * 80)
        print("LinkedIn API Credential Setup")
        print("=" * 80)
        print()
        print("Found existing partial credentials. Current status:")
        print(f"  Client ID: {'✓' if has_client_id else '✗'}")
        print(f"  Client Secret: {'✓' if has_client_secret else '✗'}")
        print(f"  Redirect URI: {'✓' if has_redirect_uri else '✗'}")
        print(f"  Access Token: {'✓' if has_access_token else '✗'}")
        print(f"  Refresh Token: {'✓' if has_refresh_token else '✗'}")
        print()
        if skip_completed:
            print("Will skip steps that are already completed.")
            response = input("Resume setup? (Y/n) or 'q' to quit: ").strip()
        else:
            response = input("Resume setup? (y/N) or 'q' to quit: ").strip()
        if response.lower() == 'q':
            return None
        if response.lower() == 'n':
            # Start fresh
            existing_creds = {}
    else:
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
        print("Note: Progress is saved as you go, so you can stop and resume later.")
        print()
        response = input("Press Enter to continue, or 'q' to quit: ").strip()
        if response.lower() == 'q':
            return None

    # Step 1: Get Client ID and Secret
    has_client_id = bool(existing_creds.get('LINKEDIN_CLIENT_ID'))
    has_client_secret = bool(existing_creds.get('LINKEDIN_CLIENT_SECRET'))
    
    if has_client_id and has_client_secret and skip_completed:
        print("\n" + "=" * 80)
        print("Step 1: Client ID and Client Secret")
        print("=" * 80)
        print()
        print("✓ Already configured - skipping")
        client_id = existing_creds.get('LINKEDIN_CLIENT_ID')
        client_secret = existing_creds.get('LINKEDIN_CLIENT_SECRET')
    else:
        if not has_client_id or not has_client_secret:
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

        # Check if we already have these
        existing_client_id = existing_creds.get('LINKEDIN_CLIENT_ID', '')
        existing_client_secret = existing_creds.get('LINKEDIN_CLIENT_SECRET', '')
        
        if existing_client_id:
            print(f"\nFound existing Client ID: {existing_client_id[:10]}...")
            use_existing = input("Use existing Client ID? (Y/n): ").strip().lower()
            if use_existing != 'n':
                client_id = existing_client_id
            else:
                client_id = input("Enter your Client ID: ").strip()
        else:
            client_id = input("\nEnter your Client ID: ").strip()
        
        if not client_id:
            print("ERROR: Client ID is required", file=sys.stderr)
            return None

        if existing_client_secret:
            print(f"\nFound existing Client Secret: {'*' * 10}...")
            use_existing = input("Use existing Client Secret? (Y/n): ").strip().lower()
            if use_existing != 'n':
                client_secret = existing_client_secret
            else:
                client_secret = getpass.getpass("Enter your Client Secret (hidden): ").strip()
        else:
            client_secret = getpass.getpass("Enter your Client Secret (hidden): ").strip()
        
        if not client_secret:
            print("ERROR: Client Secret is required", file=sys.stderr)
            return None

        # Save Client ID and Secret immediately
        print("\nSaving Client ID and Client Secret...")
        save_credentials_partial(client_id=client_id, client_secret=client_secret)
        print("✓ Saved")

    # Step 2: Configure redirect URI
    has_redirect_uri = bool(existing_creds.get('LINKEDIN_REDIRECT_URI'))
    
    if has_redirect_uri and skip_completed:
        print("\n" + "=" * 80)
        print("Step 2: Configure Redirect URI")
        print("=" * 80)
        print()
        print(f"✓ Already configured: {existing_creds.get('LINKEDIN_REDIRECT_URI')}")
        redirect_uri = existing_creds.get('LINKEDIN_REDIRECT_URI')
    else:
        print("\n" + "=" * 80)
        print("Step 2: Configure Redirect URI")
        print("=" * 80)
        print()
        print("IMPORTANT: The redirect URI must be configured in your LinkedIn app")
        print("BEFORE starting the OAuth flow.")
        print()
        print("In your LinkedIn app's 'Auth' tab (should still be open in browser):")
        print("1. Scroll to 'Redirect URLs' section")
        print("2. Click 'Add redirect URL' or '+' button")
        print(f"3. Enter EXACTLY: {DEFAULT_REDIRECT_URI}")
        print("   (Must match exactly - no trailing slashes, correct protocol)")
        print("4. Click 'Update' or 'Save'")
        print("5. Verify it appears in the list of redirect URLs")
        print()
        input("Press Enter after you have added and saved the redirect URI...")
        
        # Check if we already have redirect URI
        existing_redirect_uri = existing_creds.get('LINKEDIN_REDIRECT_URI', '')
        if existing_redirect_uri:
            print(f"\nFound existing Redirect URI: {existing_redirect_uri}")
            use_existing = input("Use existing Redirect URI? (Y/n): ").strip().lower()
            if use_existing != 'n':
                redirect_uri = existing_redirect_uri
            else:
                redirect_uri = input(f"Enter redirect URI (or press Enter for default [{DEFAULT_REDIRECT_URI}]): ").strip()
                if not redirect_uri:
                    redirect_uri = DEFAULT_REDIRECT_URI
        else:
            redirect_uri = input(f"\nEnter redirect URI (or press Enter for default [{DEFAULT_REDIRECT_URI}]): ").strip()
            if not redirect_uri:
                redirect_uri = DEFAULT_REDIRECT_URI

        # Validate redirect URI format
        if not redirect_uri.startswith('http://') and not redirect_uri.startswith('https://'):
            print(f"WARNING: Redirect URI should start with http:// or https://", file=sys.stderr)
            print(f"Using: {redirect_uri}", file=sys.stderr)

        # Save redirect URI immediately
        print("\nSaving Redirect URI...")
        save_credentials_partial(redirect_uri=redirect_uri)
        print("✓ Saved")
        print(f"\nMake sure '{redirect_uri}' is configured in your LinkedIn app's Redirect URLs!")

    # Step 3: Request product access
    # Note: We can't check if products are approved via API, so we always show this step
    # but allow user to skip if they've already done it
    print("\n" + "=" * 80)
    print("Step 3: Request Product Access")
    print("=" * 80)
    print()
    if skip_completed and (has_client_id and has_redirect_uri):
        print("If you've already requested access to these products, you can skip this step.")
        skip_products = input("Skip product access step? (y/N): ").strip().lower()
        if skip_products == 'y':
            print("✓ Skipping product access step")
        else:
            print("\nIn your LinkedIn app (should still be open in browser):")
            print("1. Go to the 'Products' tab")
            print("2. Find 'Sign In with LinkedIn using OpenID Connect'")
            print("   - If not already added, click 'Request access' button")
            print("   - Wait for 'Approved' status (may be instant)")
            print("3. Find 'Share on LinkedIn' (Default Tier)")
            print("   - Description: 'Amplify your content by sharing it on LinkedIn'")
            print("   - Click 'Request access' button")
            print("   - This is required for posting content to LinkedIn")
            print("4. Wait for both to show 'Approved' status")
            print("   (You may need to refresh the page to see updated status)")
            print()
            print("Note: 'Share on LinkedIn' is the product needed for posting content.")
            print("If you don't see it, make sure you're on the 'Available products' section.")
            print()
            input("Press Enter when both products show 'Approved' status...")
    else:
        print("In your LinkedIn app (should still be open in browser):")
        print("1. Go to the 'Products' tab")
        print("2. Find 'Sign In with LinkedIn using OpenID Connect'")
        print("   - If not already added, click 'Request access' button")
        print("   - Wait for 'Approved' status (may be instant)")
        print("3. Find 'Share on LinkedIn' (Default Tier)")
        print("   - Description: 'Amplify your content by sharing it on LinkedIn'")
        print("   - Click 'Request access' button")
        print("   - This is required for posting content to LinkedIn")
        print("4. Wait for both to show 'Approved' status")
        print("   (You may need to refresh the page to see updated status)")
        print()
        print("Note: 'Share on LinkedIn' is the product needed for posting content.")
        print("If you don't see it, make sure you're on the 'Available products' section.")
        print()
        input("Press Enter when both products show 'Approved' status...")

    # Step 4: Complete OAuth flow
    has_access_token = bool(existing_creds.get('LINKEDIN_ACCESS_TOKEN'))
    has_refresh_token = bool(existing_creds.get('LINKEDIN_REFRESH_TOKEN'))
    
    if has_access_token and skip_completed:
        print("\n" + "=" * 80)
        print("Step 4: Complete OAuth Flow")
        print("=" * 80)
        print()
        print("✓ Access Token already configured - skipping OAuth flow")
        access_token = existing_creds.get('LINKEDIN_ACCESS_TOKEN')
        refresh_token = existing_creds.get('LINKEDIN_REFRESH_TOKEN', '')
        print(f"Access Token: {access_token[:20]}...")
        if refresh_token:
            print(f"Refresh Token: {refresh_token[:20]}...")
    else:
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

    # Step 5: Verify all credentials saved
    print("=" * 80)
    print("Step 5: Setup Complete")
    print("=" * 80)
    print()
    print("All credentials have been saved incrementally.")
    print(f"Credentials file: {CREDENTIALS_FILE}")
    print(f"Permissions: {oct(CREDENTIALS_FILE.stat().st_mode)[-3:]}")
    print("=" * 80)
    print()

    return {
        'client_id': client_id,
        'client_secret': client_secret,
        'access_token': access_token,
        'refresh_token': refresh_token
    }


def get_credentials(cli_args: Optional[argparse.Namespace] = None, skip_completed: bool = True) -> Dict[str, str]:
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
    
    # Also check for redirect URI in environment
    redirect_uri = os.getenv('LINKEDIN_REDIRECT_URI', DEFAULT_REDIRECT_URI)

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
        # Get redirect URI from credentials if available
        saved_redirect_uri = creds.get('LINKEDIN_REDIRECT_URI')
        if saved_redirect_uri:
            redirect_uri = saved_redirect_uri

    # If still missing after all tiers, run interactive setup
    if not all([client_id, client_secret, access_token, refresh_token]):
        print("\n" + "=" * 80)
        print("LinkedIn API credentials are missing or incomplete.")
        print("=" * 80)
        print("\nStarting interactive setup...")
        print("This will guide you through the complete setup process.")
        print("Completed steps will be skipped automatically.\n")

        try:
            setup_result = setup_credentials_interactive(skip_completed=skip_completed)
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
        # Check for duplicate post error (422)
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 422:
                try:
                    error_data = e.response.json()
                    error_message = error_data.get('message', '')
                    
                    # Check if it's a duplicate post error
                    if 'duplicate' in error_message.lower() or 'DUPLICATE_POST' in str(error_data):
                        # Try to extract the existing share URN from the error message
                        # Format: "Content is a duplicate of urn:li:share:1234567890"
                        share_match = re.search(r'urn:li:share:(\d+)', error_message)
                        if share_match:
                            share_id = share_match.group(1)
                            print(f"\nWARNING: Post is a duplicate of existing post.", file=sys.stderr)
                            print(f"Existing post ID: urn:li:share:{share_id}", file=sys.stderr)
                            # Return the existing post info
                            return {
                                'id': f'urn:li:share:{share_id}',
                                'duplicate': True,
                                'existing_share_id': share_id
                            }
                        else:
                            print(f"WARNING: Duplicate post detected but couldn't extract share ID.", file=sys.stderr)
                            print(f"Error message: {error_message}", file=sys.stderr)
                except (json.JSONDecodeError, KeyError):
                    pass
            
            print(f"ERROR: Failed to create LinkedIn post: {e}", file=sys.stderr)
            print(f"Response: {e.response.text}", file=sys.stderr)
        else:
            print(f"ERROR: Failed to create LinkedIn post: {e}", file=sys.stderr)
        return None


def get_post_url(post_id: str) -> str:
    """
    Construct LinkedIn post URL from post ID.

    Args:
        post_id: Post ID from API response (e.g., "urn:li:ugcPost:123456" or "urn:li:share:123456")

    Returns:
        LinkedIn post URL
    """
    # Extract numeric ID from URN
    # URN formats: 
    # - urn:li:ugcPost:1234567890 (UGC Posts API)
    # - urn:li:share:1234567890 (Shares API / existing posts)
    match = re.search(r':(\d+)$', post_id)
    if match:
        numeric_id = match.group(1)
        # LinkedIn post URLs use the numeric ID
        # Format: https://www.linkedin.com/feed/update/NUMERIC_ID
        return f"https://www.linkedin.com/feed/update/{numeric_id}"
    # Fallback: use the post_id as-is (might be numeric already)
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
        '--verbose', '-v',
        action='store_true',
        help='Show verbose output including API responses'
    )
    parser.add_argument(
        '--allow-duplicate',
        action='store_true',
        help='Allow posting duplicate content (by default, duplicates are detected and existing post URL is used)'
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
    parser.add_argument(
        '--skip-completed',
        action='store_true',
        help='Skip setup steps that are already completed (default: auto-detect)'
    )
    parser.add_argument(
        '--no-skip-completed',
        action='store_true',
        help='Do not skip completed steps, re-enter all credentials'
    )

    args = parser.parse_args()

    # Load credentials
    try:
        # Check for CLI flags for skip behavior
        skip_completed = True
        if hasattr(args, 'no_skip_completed') and args.no_skip_completed:
            skip_completed = False
        elif hasattr(args, 'skip_completed') and args.skip_completed:
            skip_completed = True
        creds = get_credentials(args, skip_completed=skip_completed)
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

    # Check if this is a duplicate post
    is_duplicate = post_response.get('duplicate', False)
    if is_duplicate:
        print("\nNOTE: This post already exists (duplicate detected).")
        print("Using the existing post URL.")

    # Extract post information
    post_id = post_response.get('id', '')
    if not post_id:
        print("ERROR: Post created but no post ID in response.", file=sys.stderr)
        print(f"Response: {json.dumps(post_response, indent=2)}", file=sys.stderr)
        return 1

    # Debug: Show full response in verbose mode
    if hasattr(args, 'verbose') and args.verbose:
        print(f"\nAPI Response: {json.dumps(post_response, indent=2)}")

    # Try to get the share URL from the response if available
    # LinkedIn UGC Posts API may return shareUrl or activity in the response
    post_url = None
    if 'shareUrl' in post_response:
        post_url = post_response['shareUrl']
    elif 'activity' in post_response:
        # Sometimes the URL is in an activity field
        activity = post_response.get('activity', {})
        if isinstance(activity, str):
            post_url = activity
        elif isinstance(activity, dict):
            post_url = activity.get('url') or activity.get('shareUrl')
    
    # Note: We don't construct URLs from post IDs because LinkedIn post URLs require
    # a suffix (e.g., -7wgj) that is not available via the API. The constructed URL
    # format (https://www.linkedin.com/feed/update/{ID}) does not work.
    
    print(f"\nSUCCESS: Post created successfully!")
    print(f"Post ID: {post_id}")
    if post_url:
        print(f"Post URL (from API): {post_url}")
    else:
        print()
        print("Note: Post URL not available from API.")
        print("To get the post URL, go to your LinkedIn feed and find the post.")
        print("Click on the post timestamp or '...' menu to copy the URL.")
    
    # TODO: Figure out how to get the username (vanity name) from the LinkedIn API
    # to dynamically construct the activity URL instead of hardcoding it.
    # For now, hardcoding the URL to open the user's recent activity page.
    activity_url = "https://www.linkedin.com/in/glblackburn/recent-activity/all/"
    try:
        print(f"\nOpening your LinkedIn recent activity page...")
        webbrowser.open(activity_url)
        print(f"Opened: {activity_url}")
    except Exception as e:
        print(f"Could not open browser: {e}")
    
    # Show response structure for debugging
    if hasattr(args, 'verbose') and args.verbose:
        print(f"\nFull API response: {json.dumps(post_response, indent=2)}")
    else:
        print(f"\nAPI response keys: {list(post_response.keys())}")
        if 'activity' in post_response:
            print(f"Activity field: {post_response.get('activity')}")

    # Update archive - DISABLED: Keeping archive updates as manual process for now
    # if not args.no_archive:
    #     # Archive file is in the LinkedIn-posts/ directory
    #     archive_file = Path(__file__).parent.parent / 'LinkedIn-posts.md'
    #     if update_markdown_archive(post_url, args.post_file, archive_file):
    #         print(f"Archive updated: {archive_file}")
    #     else:
    #         print(f"WARNING: Failed to update archive: {archive_file}", file=sys.stderr)

    return 0


if __name__ == '__main__':
    sys.exit(main())
