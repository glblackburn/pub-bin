# Trufflehog AWS Key Rotation - Pluggable Credential Loaders Design

**Date:** 2026-01-06  
**Status:** Design  
**Priority:** Medium  
**Related Script:** `trufflehog/scripts/trufflehog-rotate-aws-key.py`

## Overview

This feature adds support for pluggable credential loaders to read "new AWS key" and "new paired secret" values from external sources, following the pattern established in `devops-general-utils/github/clone-org-repos.sh` and `github-credentials.sh`.

## Problem Statement

Currently, the script supports three methods for providing new AWS keys:
1. Interactive prompt (`-p` / `--prompt-key`)
2. Command-line argument (`-k` / `--new-key`) - insecure
3. Environment variable (`TRUFFLEHOG_NEW_AWS_KEY`)

For paired secrets:
1. Interactive prompt (`--prompt-paired-secret`)
2. Environment variable (`TRUFFLEHOG_NEW_AWS_SECRET_KEY`)

**Limitations:**
- Environment variables are visible in process lists
- No support for reading from secure files
- No support for reading from vault systems (Keeper, AWS Secrets Manager, etc.)
- No pluggable architecture for custom credential sources

## Use Cases

1. **File-Based Credentials:** Read keys from a secure file (e.g., `~/.secure/trufflehog-keys.sh`)
2. **Vault Integration:** Read keys from Keeper Vault, AWS Secrets Manager, HashiCorp Vault, etc.
3. **Custom Loaders:** Allow users to create custom credential loaders for their specific infrastructure

## Requirements

1. **Pluggable Architecture:**
   - Support multiple credential loader scripts
   - Loader scripts follow a standard interface
   - Default loader reads from file
   - Additional loaders can be added (Keeper vault, etc.)

2. **Priority Order:**
   - Command-line arguments (highest priority - existing behavior)
   - Interactive prompts (existing behavior)
   - Pluggable credential loader (new)
   - Environment variables (lowest priority - existing behavior)

3. **Loader Script Interface:**
   - Loader scripts are executable Python scripts
   - Loader scripts output credentials in a standard format (JSON or environment variable format)
   - Loader scripts can be specified via environment variable or CLI argument

4. **Security:**
   - Loader scripts should not log credentials
   - Loader scripts should handle errors gracefully
   - Loader scripts should validate their output format

5. **Backward Compatibility:**
   - All existing methods continue to work
   - New feature is opt-in (only used if loader script is specified)
   - No breaking changes to existing workflows

## Design

### Architecture

Following the pattern from `clone-org-repos.sh`:

```bash
# In clone-org-repos.sh (lines 337-349):
github_credentials_script="${GITHUB_CREDENTIALS_SCRIPT:-${script_dir}/github-credentials.sh}"
if [ ! -f "${github_credentials_script}" ] ; then
    echo "ERROR: GitHub credentials script not found: ${github_credentials_script}" >&2
    exit 1
fi
source "${github_credentials_script}"

# Verify required variables are set
if [ -z "${git_org}" ] || [ -z "${bearer}" ] ; then
    echo "ERROR: Credentials script did not set required variables (git_org, bearer)" >&2
    exit 1
fi
```

**Python Equivalent:**
- Loader scripts are Python modules that define a function: `load_credentials() -> Dict[str, str]`
- Loader scripts can also be executable scripts that output JSON to stdout
- Script validates loader exists and required keys are returned

### Loader Script Interface

**Option 1: Python Module Function (Recommended)**
```python
# loader_script.py
def load_credentials() -> Dict[str, Optional[str]]:
    """
    Load credentials from external source.
    
    Returns:
        Dictionary with keys:
        - 'new_aws_key': New AWS Access Key ID (or None)
        - 'new_aws_secret_key': New AWS Secret Access Key (or None)
    """
    # Implementation reads from file, vault, etc.
    return {
        'new_aws_key': 'AKIA...',
        'new_aws_secret_key': 'wJalr...'
    }
```

**Option 2: Executable Script with JSON Output**
```python
#!/usr/bin/env python3
# loader_script.py (executable)
import json
import sys

def main():
    credentials = {
        'new_aws_key': 'AKIA...',
        'new_aws_secret_key': 'wJalr...'
    }
    print(json.dumps(credentials))
    sys.exit(0)

if __name__ == '__main__':
    main()
```

**Option 3: Shell Script with Environment Variables (for compatibility)**
```bash
#!/usr/bin/env bash
# loader_script.sh
export TRUFFLEHOG_NEW_AWS_KEY="AKIA..."
export TRUFFLEHOG_NEW_AWS_SECRET_KEY="wJalr..."
```

### Implementation Approach

**Phase 1: File-Based Loader (Initial Implementation)**

1. Create default file-based loader: `trufflehog-credentials-file.py`
   - Reads from `~/.secure/trufflehog-aws-keys.sh` (bash format for consistency)
   - Parses `export TRUFFLEHOG_NEW_AWS_KEY="..."` format
   - Returns dictionary with credentials

2. Add CLI option: `--credential-loader <script_path>`
   - Optional: specifies path to credential loader script
   - Default: `trufflehog-credentials-file.py` (if exists)

3. Add environment variable: `TRUFFLEHOG_CREDENTIAL_LOADER`
   - Can override default loader script path
   - Follows same pattern as `GITHUB_CREDENTIALS_SCRIPT`

4. Integrate into credential loading logic:
   - Check for loader script
   - Execute loader script
   - Extract credentials from return value
   - Validate credentials are present
   - Use credentials if provided (before falling back to prompts/env vars)

**Phase 2: Keeper Vault Loader (Future)**

1. Create Keeper vault loader: `trufflehog-credentials-keeper.py`
   - Uses Keeper SDK to fetch credentials
   - Returns same dictionary format
   - Handles authentication and errors

2. Users can specify: `--credential-loader trufflehog-credentials-keeper.py`

## File Structure

```
trufflehog/
├── scripts/
│   ├── trufflehog-rotate-aws-key.py (main script)
│   ├── credential-loaders/
│   │   ├── __init__.py
│   │   ├── file_loader.py (reads from ~/.secure/trufflehog-aws-keys.sh)
│   │   └── keeper_loader.py (future - reads from Keeper vault)
│   └── ...
└── docs/
    └── design/
        └── trufflehog-rotate-aws-key-pluggable-credential-loaders-design.md
```

## Loader Script Examples

### File-Based Loader (`file_loader.py`)

```python
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
    
    Returns:
        Dictionary with 'new_aws_key' and 'new_aws_secret_key' keys.
        Values are None if not found.
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
    except Exception as e:
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
```

### Keeper Vault Loader (Future - `keeper_loader.py`)

```python
#!/usr/bin/env python3
"""
Keeper vault credential loader for trufflehog-rotate-aws-key.py

Reads credentials from Keeper Vault.
Requires: keeper-sdk-python
"""

from typing import Dict, Optional
from keepercommander import vault, api

# Configuration (can be overridden via environment variables)
KEEPER_RECORD_UID = os.environ.get('TRUFFLEHOG_KEEPER_RECORD_UID')
KEEPER_FIELD_ACCESS_KEY = 'AWS Access Key ID'
KEEPER_FIELD_SECRET_KEY = 'AWS Secret Access Key'


def load_credentials() -> Dict[str, Optional[str]]:
    """
    Load credentials from Keeper Vault.
    
    Returns:
        Dictionary with 'new_aws_key' and 'new_aws_secret_key' keys.
    """
    credentials = {
        'new_aws_key': None,
        'new_aws_secret_key': None
    }
    
    try:
        # Initialize Keeper API
        # (Implementation details depend on Keeper SDK)
        vault_api = api.KeeperAPI()
        vault_api.login()
        
        # Fetch record
        record = vault_api.get_record(KEEPER_RECORD_UID)
        
        # Extract credentials from record fields
        credentials['new_aws_key'] = record.get_field_value(KEEPER_FIELD_ACCESS_KEY)
        credentials['new_aws_secret_key'] = record.get_field_value(KEEPER_FIELD_SECRET_KEY)
        
    except Exception as e:
        # Silently fail - caller will fall back to other methods
        pass
    
    return credentials


if __name__ == '__main__':
    import json
    import sys
    creds = load_credentials()
    print(json.dumps(creds))
    sys.exit(0)
```

## Integration into Main Script

### Credential Loading Priority

```python
def get_new_aws_key(args, quiet: bool = False) -> Optional[str]:
    """
    Get new AWS key using priority order:
    1. CLI argument (-k / --new-key)
    2. Interactive prompt (-p / --prompt-key)
    3. Credential loader script (--credential-loader)
    4. Environment variable (TRUFFLEHOG_NEW_AWS_KEY)
    5. Automatic prompt (if none of above)
    """
    # Priority 1: CLI argument
    if args.new_key:
        if not quiet:
            print("WARNING: Passing secrets via CLI arguments is insecure...", file=sys.stderr)
        return args.new_key
    
    # Priority 2: Interactive prompt
    if args.prompt_key:
        return getpass.getpass("Enter new AWS key (input will be hidden): ")
    
    # Priority 3: Credential loader (NEW)
    if args.credential_loader:
        loader_creds = load_credentials_from_script(args.credential_loader, quiet)
        if loader_creds and loader_creds.get('new_aws_key'):
            return loader_creds['new_aws_key']
    
    # Priority 4: Environment variable
    new_key = os.environ.get('TRUFFLEHOG_NEW_AWS_KEY')
    if new_key:
        return new_key
    
    # Priority 5: Automatic prompt
    if not args.resume:
        return getpass.getpass("Enter new AWS key (input will be hidden): ")
    
    return None
```

### Loader Script Execution

```python
def load_credentials_from_script(loader_path: str, quiet: bool = False) -> Optional[Dict[str, Optional[str]]]:
    """
    Load credentials from pluggable loader script.
    
    Args:
        loader_path: Path to loader script (Python module or executable)
        quiet: If True, suppress error messages
    
    Returns:
        Dictionary with credentials or None if failed
    """
    loader_path = Path(loader_path)
    
    if not loader_path.exists():
        if not quiet:
            print(f"WARNING: Credential loader not found: {loader_path}", file=sys.stderr)
        return None
    
    try:
        # Try as Python module first
        if loader_path.suffix == '.py':
            # Import as module
            import importlib.util
            spec = importlib.util.spec_from_file_location("credential_loader", loader_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, 'load_credentials'):
                    return module.load_credentials()
        
        # Try as executable script (outputs JSON)
        result = subprocess.run(
            [str(loader_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            credentials = json.loads(result.stdout)
            return credentials
    
    except Exception as e:
        if not quiet:
            print(f"WARNING: Failed to load credentials from {loader_path}: {e}", file=sys.stderr)
        return None
    
    return None
```

## CLI Options

```bash
--credential-loader <path>    # Path to credential loader script
                              # Default: scripts/credential-loaders/file_loader.py (if exists)
                              # Can also be set via TRUFFLEHOG_CREDENTIAL_LOADER env var
```

## Environment Variables

```bash
TRUFFLEHOG_CREDENTIAL_LOADER   # Path to credential loader script (overrides default)
```

## Security Considerations

1. **File Permissions:**
   - Credential files should have restrictive permissions (600)
   - Loader scripts should validate file permissions

2. **Error Handling:**
   - Loader scripts should not expose credentials in error messages
   - Failures should be silent (fall back to other methods)

3. **Validation:**
   - Loader scripts should validate credential format
   - Main script should validate credentials before use

4. **Logging:**
   - Never log credentials
   - Only log loader script path (not contents)

## Backward Compatibility

- All existing methods continue to work unchanged
- New feature is opt-in (only used if `--credential-loader` is specified)
- Default behavior unchanged if no loader script is specified
- Environment variables still work as before

## Testing Strategy

1. **Unit Tests:**
   - Test file loader with various file formats
   - Test loader script execution
   - Test priority order
   - Test error handling

2. **Integration Tests:**
   - Test with actual credential files
   - Test fallback behavior when loader fails
   - Test with missing loader scripts

3. **Security Tests:**
   - Verify credentials are not logged
   - Verify file permissions are checked
   - Verify error messages don't expose credentials

## Implementation Plan

### Phase 1: File-Based Loader (Initial)
1. Create `credential-loaders/` directory
2. Implement `file_loader.py`
3. Add `load_credentials_from_script()` function to main script
4. Add `--credential-loader` CLI option
5. Integrate into credential loading priority
6. Add tests
7. Update documentation

### Phase 2: Keeper Vault Loader (Future)
1. Implement `keeper_loader.py`
2. Add Keeper SDK dependency (optional)
3. Add configuration options
4. Add tests
5. Update documentation

## Success Criteria

1. ✅ File-based loader reads credentials from `~/.secure/trufflehog-aws-keys.sh`
2. ✅ Loader scripts follow standard interface
3. ✅ Priority order works correctly (CLI > prompt > loader > env > auto-prompt)
4. ✅ Backward compatibility maintained
5. ✅ Error handling is graceful (falls back to other methods)
6. ✅ Security requirements met (no credential logging, proper permissions)
7. ✅ Documentation updated

## Related Documentation

- `trufflehog/scripts/trufflehog-rotate-aws-key.py` - Main script
- `devops-general-utils/github/clone-org-repos.sh` - Example of pluggable credentials pattern
- `devops-general-utils/github/github-credentials.sh` - Example credential loader

---

**Status:** Design Complete - Ready for Implementation  
**Last Updated:** 2026-01-06
