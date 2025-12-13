#!/usr/bin/env python3
"""
create-set-linkedin-credentials.py - Interactive setup script for LinkedIn API credentials

This script guides users through setting up LinkedIn API credentials for automated posting.
It creates a secure credentials file at ~/.secure/linkedin-set-api-key.sh with proper permissions.
"""

import getpass
import os
import stat
import sys
from pathlib import Path

################################################################################
# Constants
################################################################################

SECURE_DIR = Path.home() / '.secure'
CREDENTIALS_FILE = SECURE_DIR / 'linkedin-set-api-key.sh'
CREATE_API_KEY_URL = "https://www.linkedin.com/developers/apps"

################################################################################
# Functions
################################################################################


def main() -> int:
    """Main function to set up LinkedIn API credentials."""
    # Check if credentials file already exists
    if CREDENTIALS_FILE.exists():
        print(f"WARNING: {CREDENTIALS_FILE} already exists.")
        response = input("Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Exiting without changes.")
            return 0

    print("=" * 80)
    print(f"Credentials file: {CREDENTIALS_FILE}")
    print(f"LinkedIn Developer Portal: {CREATE_API_KEY_URL}")
    print("=" * 80)
    print()
    print("Go get your LinkedIn API credentials from the link above.")
    print("Press Enter to open the URL (or 'N' to skip and enter manually).")
    response = input()

    if response.lower() != 'n':
        try:
            import webbrowser
            webbrowser.open(CREATE_API_KEY_URL)
        except Exception as e:
            print(f"Could not open browser: {e}")
            print(f"Please open manually: {CREATE_API_KEY_URL}")

    # Collect credentials
    print("\nEnter your LinkedIn API credentials:")
    client_id = input("Client ID: ").strip()
    if not client_id:
        print("ERROR: Client ID is required", file=sys.stderr)
        return 1

    client_secret = getpass.getpass("Client Secret (hidden): ").strip()
    if not client_secret:
        print("ERROR: Client Secret is required", file=sys.stderr)
        return 1

    access_token = getpass.getpass("Access Token (hidden): ").strip()
    if not access_token:
        print("ERROR: Access Token is required", file=sys.stderr)
        return 1

    refresh_token = getpass.getpass("Refresh Token (hidden): ").strip()
    if not refresh_token:
        print("ERROR: Refresh Token is required", file=sys.stderr)
        return 1

    # Create secure directory
    print(f"\nCreating secure directory: {SECURE_DIR}")
    SECURE_DIR.mkdir(mode=0o700, exist_ok=True)

    # Write credentials file
    print(f"Creating credentials file: {CREDENTIALS_FILE}")
    with open(CREDENTIALS_FILE, 'w') as f:
        f.write(f'export LINKEDIN_CLIENT_ID="{client_id}"\n')
        f.write(f'export LINKEDIN_CLIENT_SECRET="{client_secret}"\n')
        f.write(f'export LINKEDIN_ACCESS_TOKEN="{access_token}"\n')
        f.write(f'export LINKEDIN_REFRESH_TOKEN="{refresh_token}"\n')

    # Set permissions: 400 (read-only for owner)
    os.chmod(CREDENTIALS_FILE, stat.S_IRUSR)

    print("=" * 80)
    print("Credentials file created successfully!")
    print(f"File: {CREDENTIALS_FILE}")
    print(f"Permissions: {oct(CREDENTIALS_FILE.stat().st_mode)[-3:]}")
    print("=" * 80)

    return 0


if __name__ == '__main__':
    sys.exit(main())
