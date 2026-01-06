#!/usr/bin/env python3
"""
File-based credential loader for trufflehog-rotate-aws-key.py

Reads credentials from ~/.secure/trufflehog-aws-keys.sh
Format: export TRUFFLEHOG_NEW_AWS_KEY="AKIA..."
        export TRUFFLEHOG_NEW_AWS_SECRET_KEY="wJalr..."
"""

import re
from pathlib import Path
from typing import Dict, Optional


SECURE_DIR = Path.home() / '.secure'
CREDENTIALS_FILE = SECURE_DIR / 'trufflehog-aws-keys.sh'


def load_credentials() -> Dict[str, Optional[str]]:
    """
    Load credentials from secure file.
    
    Reads from ~/.secure/trufflehog-aws-keys.sh in bash export format:
        export TRUFFLEHOG_NEW_AWS_KEY="AKIA..."
        export TRUFFLEHOG_NEW_AWS_SECRET_KEY="wJalr..."
    
    Returns:
        Dictionary with keys:
        - 'new_aws_key': New AWS Access Key ID (or None if not found)
        - 'new_aws_secret_key': New AWS Secret Access Key (or None if not found)
    """
    credentials = {
        'new_aws_key': None,
        'new_aws_secret_key': None
    }
    
    if not CREDENTIALS_FILE.exists():
        return credentials
    
    try:
        with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                # Match: export TRUFFLEHOG_NEW_AWS_KEY="value"
                # or: export TRUFFLEHOG_NEW_AWS_KEY=value
                # or: export TRUFFLEHOG_NEW_AWS_KEY='value'
                match = re.match(
                    r'export\s+(TRUFFLEHOG_NEW_AWS_KEY|TRUFFLEHOG_NEW_AWS_SECRET_KEY)=["\']?([^"\']+)["\']?',
                    line.strip()
                )
                if match:
                    var_name = match.group(1)
                    var_value = match.group(2)
                    if var_name == 'TRUFFLEHOG_NEW_AWS_KEY':
                        credentials['new_aws_key'] = var_value
                    elif var_name == 'TRUFFLEHOG_NEW_AWS_SECRET_KEY':
                        credentials['new_aws_secret_key'] = var_value
    except Exception:
        # Silently fail - caller will fall back to other methods
        pass
    
    return credentials


if __name__ == '__main__':
    # Allow running as executable script (outputs JSON)
    import json
    import sys
    creds = load_credentials()
    print(json.dumps(creds))
    sys.exit(0)
