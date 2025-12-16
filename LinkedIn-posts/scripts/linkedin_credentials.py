"""
linkedin_credentials.py - Credential loader module for LinkedIn API

This module handles loading LinkedIn API credentials using a three-tier priority system:
1. Command-line arguments (highest priority)
2. Environment variables
3. Secure credentials file (~/.secure/linkedin-set-api-key.sh)

If the credentials file doesn't exist, it automatically runs the setup script.
"""

import re
from pathlib import Path
from typing import Dict

################################################################################
# Constants
################################################################################

SECURE_DIR = Path.home() / '.secure'
CREDENTIALS_FILE = SECURE_DIR / 'linkedin-set-api-key.sh'

################################################################################
# Functions
################################################################################


def load_linkedin_credentials() -> Dict[str, str]:
    """
    Load credentials from secure file.

    This function will:
    1. Check if credentials file exists
    2. Parse and return credentials from the file
    3. Returns empty dict if file doesn't exist (caller handles setup)

    Returns:
        Dictionary with credential keys (LINKEDIN_CLIENT_ID, etc.)
        Empty dictionary if file doesn't exist
    """
    # Parse bash export file
    credentials = {}
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE, 'r') as f:
            for line in f:
                # Match: export VARIABLE_NAME="value" or export VARIABLE_NAME=value
                # Also handle empty values: export VARIABLE_NAME=""
                match = re.match(r'export\s+(\w+)="?([^"]*)"?', line.strip())
                if match:
                    var_name, var_value = match.groups()
                    # Only add non-empty values
                    if var_value:
                        credentials[var_name] = var_value

    return credentials
