# LinkedIn API Integration - Design Recommendations

**Purpose:** Automate posting of `.txt` files as LinkedIn posts  
**Example File:** `LinkedIn-posts/examples/2025-12-12-network-capture-analysis-tools.txt`  
**Date:** December 2025

## Implementation Decisions

**Selected Language: Python 3** ✅

Python 3 has been selected as the implementation language for the LinkedIn API integration script. This decision is based on:
- OAuth 2.0 complexity requiring robust state management
- Superior JSON handling and API error management
- Consistency with existing Python tools in the codebase (`analyze-tcpdump.py`, `what-is-left.py`)
- Better library ecosystem for HTTP requests and token management
- Easier content processing for Unicode characters and markdown updates

See [Language Recommendation](#language-recommendation) section for detailed rationale.

**Selected API: LinkedIn API v2 (UGC Posts API)** ✅

Option 1 (UGC Posts API) has been selected as the API endpoint for posting to LinkedIn. This decision is based on:
- Official, supported approach with long-term reliability
- Supports text posts with proper formatting
- Can add images later if needed
- Better rate limits compared to legacy endpoints
- Future-proof (legacy Shares API is deprecated)

See [Solution Options](#solution-options) section for detailed comparison.

## Overview

This document outlines requirements, solution options, and recommendations for creating a script to automatically upload `.txt` files as posts to LinkedIn.

## Requirements for LinkedIn API Integration

### 1. LinkedIn API Access

- **API Version:** LinkedIn API v2 (REST API)
- **Authentication:** OAuth 2.0 required
- **Required Permissions:** `w_member_social` (to create posts on behalf of user)

### 2. Authentication Setup

- **LinkedIn Developer Account:** Required
- **Create App:** Must create an app at https://www.linkedin.com/developers/apps
- **OAuth 2.0 Credentials:**
  - Client ID
  - Client Secret
  - Redirect URI
- **Access Token:** User must authorize the app (one-time or periodic)

### 3. API Endpoints

- **POST `/v2/ugcPosts`** (User Generated Content API) - **SELECTED** ✅ - Recommended for text posts
- **POST `/v2/shares`** (Legacy endpoint - simpler but limited, deprecated)

## Solution Options

### Option 1: LinkedIn API v2 (UGC Posts API) - **SELECTED** ✅

**Pros:**
- Official, supported approach
- Supports text posts
- Can add images later if needed
- Better rate limits

**Cons:**
- More complex setup
- Requires OAuth flow
- More API calls (person, organization, etc.)

**Requirements:**
- OAuth 2.0 flow implementation
- Store refresh tokens securely
- Handle token refresh automatically
- Map your LinkedIn profile/person ID

### Option 2: LinkedIn API v2 (Legacy Shares API)

**Pros:**
- Simpler implementation
- Fewer API calls needed

**Cons:**
- Deprecated (may be removed)
- Limited features
- Less reliable long-term

### Option 3: Browser Automation (Selenium/Playwright)

**Pros:**
- No API setup required
- Works with existing LinkedIn account
- Can handle manual steps

**Cons:**
- **Violates LinkedIn Terms of Service**
- Fragile (breaks on UI changes)
- Slower execution
- Risk of account restrictions
- **NOT RECOMMENDED**

### Option 4: Hybrid Approach (Manual + Automation)

**Pros:**
- Validates content before posting
- Uses API for final submission
- Safer workflow

**Cons:**
- Still requires API setup
- More complex implementation

## Recommended Approach

### Phase 1: Manual OAuth Setup (One-Time)

1. Create LinkedIn Developer app at https://www.linkedin.com/developers/apps
2. Get OAuth credentials (Client ID, Client Secret, Redirect URI)
3. Complete OAuth flow to get initial access token and refresh token
4. Run credential setup script: `create-set-linkedin-credentials.sh`
   - Interactive prompts for all credentials
   - Creates `~/.secure/linkedin-set-api-key.sh` with proper permissions
   - Follows same pattern as JIRA credential management

### Phase 2: Script Functionality

1. Read `.txt` file content
2. Validate content (character limit, formatting)
3. Authenticate with LinkedIn API (refresh token if needed)
4. Post content via API
5. Capture and store LinkedIn post URL
6. Update markdown archive automatically

## Technical Considerations

### Security

#### Credential Management Pattern (Based on JIRA Script Pattern - Python Implementation)

**User Experience: Automatic Setup Flow**

The credential management system automatically guides users through setup if credentials are missing:

1. **First-time user runs the script:**
   - Script checks for credentials in CLI args → environment variables → secure file
   - If secure file doesn't exist, automatically runs interactive setup script
   - Setup script opens LinkedIn Developer Portal and prompts for all credentials
   - Credentials are saved to `~/.secure/linkedin-set-api-key.sh` with proper permissions
   - Script automatically reloads credentials and continues

2. **Subsequent runs:**
   - Script loads credentials from secure file automatically
   - No user interaction needed (unless credentials expire)

3. **Incomplete credentials:**
   - If credentials file exists but is missing values, script detects this
   - Automatically prompts to run setup again to complete configuration
   - Provides clear error messages and guidance

**The credential management follows a three-tier priority system, matching the pattern used in `create-jira-ticket.sh`, but implemented in Python:**

**Priority Order (Highest to Lowest):**
1. **Command-line arguments** - `--client-id`, `--client-secret`, `--access-token`, `--refresh-token`
2. **Environment variables** - `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_REFRESH_TOKEN`
3. **Secure credentials file** - `~/.secure/linkedin-set-api-key.sh` (auto-created if missing)

**Credential Setup Script Pattern (Python):**

- **Setup script:** `create-set-linkedin-credentials.py` (interactive one-time setup)
  - Prompts for Client ID, Client Secret, Access Token, Refresh Token
  - Creates `~/.secure/linkedin-set-api-key.sh` with `export` statements (bash format for consistency)
  - Sets proper permissions: `chmod 700 ~/.secure`, `chmod 400 ~/.secure/linkedin-set-api-key.sh`
  - Provides helpful URLs and instructions during setup
  - Uses `getpass` for secure token input (hidden input)
  - Validates inputs before writing

- **Credential loader module:** `linkedin_credentials.py` (Python module to load credentials)
  - Auto-creates credentials file if missing (calls setup script)
  - Parses `~/.secure/linkedin-set-api-key.sh` to extract export statements
  - Returns credentials as dictionary
  - Handles file permissions and security checks

- **Main script credential loading pattern (with auto-setup):**
  ```python
  import os
  import argparse
  import sys
  from pathlib import Path
  from linkedin_credentials import load_linkedin_credentials
  
  def get_credentials():
      """
      Load credentials using three-tier priority system.
      Automatically guides user through setup if credentials are missing.
      """
      parser = argparse.ArgumentParser()
      parser.add_argument('--client-id', help='LinkedIn Client ID')
      parser.add_argument('--client-secret', help='LinkedIn Client Secret')
      parser.add_argument('--access-token', help='LinkedIn Access Token')
      parser.add_argument('--refresh-token', help='LinkedIn Refresh Token')
      args = parser.parse_args()
      
      # Tier 1: Command-line arguments (highest priority)
      client_id = args.client_id
      client_secret = args.client_secret
      access_token = args.access_token
      refresh_token = args.refresh_token
      
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
      
      # If still missing after all tiers, prompt for interactive setup
      if not all([client_id, client_secret, access_token, refresh_token]):
          print("\n" + "=" * 80)
          print("LinkedIn API credentials are missing or incomplete.")
          print("=" * 80)
          print("\nThe setup script will guide you through:")
          print("  1. Creating a LinkedIn Developer app")
          print("  2. Getting OAuth credentials (Client ID, Client Secret)")
          print("  3. Completing OAuth flow to get Access Token and Refresh Token")
          print("\nStarting interactive setup...\n")
          
          from create_set_linkedin_credentials import main as setup_main
          exit_code = setup_main()
          if exit_code != 0:
              print("\nERROR: Setup was cancelled or failed.")
              sys.exit(1)
          
          # Reload credentials after setup
          print("\nReloading credentials...")
          creds = load_linkedin_credentials()
          client_id = client_id or creds.get('LINKEDIN_CLIENT_ID')
          client_secret = client_secret or creds.get('LINKEDIN_CLIENT_SECRET')
          access_token = access_token or creds.get('LINKEDIN_ACCESS_TOKEN')
          refresh_token = refresh_token or creds.get('LINKEDIN_REFRESH_TOKEN')
          
          # Final validation
          if not all([client_id, client_secret, access_token, refresh_token]):
              print("\nERROR: Setup completed but credentials are still incomplete.")
              print("Please run create-set-linkedin-credentials.py manually to fix.")
              sys.exit(1)
      
      return {
          'client_id': client_id,
          'client_secret': client_secret,
          'access_token': access_token,
          'refresh_token': refresh_token
      }
  ```

- **Credential loader implementation (`linkedin_credentials.py`):**
  ```python
  import os
  import re
  import subprocess
  import sys
  from pathlib import Path
  from typing import Dict, Optional
  
  SECURE_DIR = Path.home() / '.secure'
  CREDENTIALS_FILE = SECURE_DIR / 'linkedin-set-api-key.sh'
  SETUP_SCRIPT = Path(__file__).parent / 'create-set-linkedin-credentials.py'
  
  def load_linkedin_credentials() -> Dict[str, str]:
      """
      Load credentials from secure file, automatically running setup if missing.
      
      This function will:
      1. Check if credentials file exists
      2. If missing, automatically run the interactive setup script
      3. Parse and return credentials from the file
      
      Returns:
          Dictionary with credential keys (LINKEDIN_CLIENT_ID, etc.)
      """
      # Auto-create credentials file if missing
      if not CREDENTIALS_FILE.exists():
          print("\n" + "=" * 80)
          print("LinkedIn API credentials not found.")
          print("=" * 80)
          print(f"\nRunning interactive setup script: {SETUP_SCRIPT}")
          print("This will guide you through setting up your LinkedIn API credentials.\n")
          try:
              subprocess.run([sys.executable, str(SETUP_SCRIPT)], check=True)
          except subprocess.CalledProcessError:
              print("\nERROR: Setup script failed. Please run it manually:")
              print(f"  {SETUP_SCRIPT}")
              return {}
          except FileNotFoundError:
              print(f"\nERROR: Setup script not found: {SETUP_SCRIPT}")
              print("Please create the setup script or run it manually.")
              return {}
      
      # Parse bash export file
      credentials = {}
      if CREDENTIALS_FILE.exists():
          with open(CREDENTIALS_FILE, 'r') as f:
              for line in f:
                  # Match: export VARIABLE_NAME="value" or export VARIABLE_NAME=value
                  match = re.match(r'export\s+(\w+)="?([^"]+)"?', line.strip())
                  if match:
                      var_name, var_value = match.groups()
                      credentials[var_name] = var_value
      
      return credentials
  ```

- **Setup script implementation (`create-set-linkedin-credentials.py`):**
  ```python
  #!/usr/bin/env python3
  """Interactive setup script for LinkedIn API credentials."""
  
  import getpass
  import os
  import stat
  from pathlib import Path
  
  SECURE_DIR = Path.home() / '.secure'
  CREDENTIALS_FILE = SECURE_DIR / 'linkedin-set-api-key.sh'
  CREATE_API_KEY_URL = "https://www.linkedin.com/developers/apps"
  
  def main():
      # Check if credentials file already exists
      if CREDENTIALS_FILE.exists():
          print(f"WARNING: {CREDENTIALS_FILE} already exists.")
          response = input("Overwrite? (y/N): ")
          if response.lower() != 'y':
              print("Exiting without changes.")
              return
      
      print("=" * 80)
      print(f"Credentials file: {CREDENTIALS_FILE}")
      print(f"LinkedIn Developer Portal: {CREATE_API_KEY_URL}")
      print("=" * 80)
      print()
      print("Go get your LinkedIn API credentials from the link above.")
      print("Press Enter to open the URL (or 'N' to skip and enter manually).")
      response = input()
      
      if response.lower() != 'n':
          import webbrowser
          webbrowser.open(CREATE_API_KEY_URL)
      
      # Collect credentials
      print("\nEnter your LinkedIn API credentials:")
      client_id = input("Client ID: ").strip()
      if not client_id:
          print("ERROR: Client ID is required")
          return 1
      
      client_secret = getpass.getpass("Client Secret (hidden): ").strip()
      if not client_secret:
          print("ERROR: Client Secret is required")
          return 1
      
      access_token = getpass.getpass("Access Token (hidden): ").strip()
      if not access_token:
          print("ERROR: Access Token is required")
          return 1
      
      refresh_token = getpass.getpass("Refresh Token (hidden): ").strip()
      if not refresh_token:
          print("ERROR: Refresh Token is required")
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
      exit(main())
  ```

**Security Requirements:**
- **Credential Storage:** Store in `~/.secure/linkedin-set-api-key.sh` with restricted permissions (bash format for consistency with existing patterns)
- **Git Safety:** Never commit tokens to git (add to `.gitignore`)
- **Token Management:** Use refresh tokens for long-term access with automatic refresh
- **File Permissions:** `chmod 700 ~/.secure`, `chmod 400` for credential files
- **Directory Structure:** Use `~/.secure/` directory (consistent with existing patterns)
- **Input Security:** Use `getpass.getpass()` for sensitive input in setup script
- **File Parsing:** Parse bash export file using regex to extract values safely

### Error Handling

- **API Rate Limits:** Check LinkedIn's rate limits
- **Token Expiration:** Auto-refresh tokens
- **Network Failures:** Implement retry logic
- **Content Validation:** Check character limits, formatting

### Content Processing

- **File Reading:** Read `.txt` file content
- **Character Count:** Validate against 3,000 character limit
- **Formatting:** Preserve Unicode bold, bullets, etc.
- **Zero-Width Spaces:** Handle correctly (preserve in file names, remove from URLs)
- **Hashtags:** Extract if needed for API

### Integration Points

- **Input:** Read from `LinkedIn-posts/examples/*.txt` or similar
- **Output:** Update `LinkedIn-posts.md` with post URL
- **Style Guide:** Follow existing `LinkedIn-style-guide.md` formatting rules

## Language Recommendation

### **Selected: Python 3** ✅

**Rationale:**
Based on analysis of the codebase patterns and LinkedIn API requirements, **Python 3** is the recommended language for this integration.

**Codebase Context:**
- The repository uses **both shell scripts and Python** strategically
- **Shell scripts** (35+ files) are used for: simple automation, system commands, basic API calls with `curl`, file operations
- **Python scripts** (15 files) are used for: complex data processing, structured code with type hints, library dependencies, tools requiring rich output (`rich` library)

**Why Python for LinkedIn API:**

1. **OAuth 2.0 Complexity:**
   - OAuth flow requires state management, token refresh logic, and secure credential handling
   - Python's `requests` library and OAuth libraries make this significantly easier
   - Shell script OAuth implementation would be complex and error-prone

2. **JSON Handling:**
   - LinkedIn API uses JSON for all requests/responses
   - Python's built-in `json` module is robust and well-tested
   - Shell scripts require `jq` dependency and complex JSON parsing

3. **Error Handling:**
   - Python's exception handling is better suited for API error scenarios
   - Can handle HTTP status codes, rate limits, and retries more elegantly
   - Type hints help catch errors early

4. **Library Ecosystem:**
   - `requests` library for HTTP calls (standard, well-maintained)
   - `python-linkedin-v2` or direct REST calls both viable
   - Can leverage existing patterns from `analyze-tcpdump.py` and `what-is-left.py`

5. **Token Management:**
   - Easier to implement secure token storage and refresh logic
   - Can integrate with existing config system (`config/config.sh`) or use Python-specific credential management

6. **Content Processing:**
   - Better string manipulation for Unicode characters (bold text, bullets)
   - Easier to validate character counts and formatting
   - Can leverage `pathlib` for file operations (already used in codebase)

7. **Markdown Updates:**
   - Python can easily read/parse/update markdown files
   - Can use libraries like `markdown` or simple string manipulation
   - Shell scripts would require complex `sed`/`awk` patterns

**Consistency with Codebase:**
- Follows pattern of using Python for complex integrations (see `analyze-tcpdump.py`, `what-is-left.py`)
- Can follow existing Python patterns: type hints, argparse, error handling
- Can use `rich` library for enhanced output (already used in `what-is-left.py`)

**Recommended Python Libraries:**
- `requests` - HTTP client for API calls
- `python-dotenv` - Environment variable management (optional)
- `rich` - Enhanced terminal output (already used in codebase)
- Standard library: `json`, `pathlib`, `argparse`, `typing`

### Alternative: Shell Script (Not Recommended)

**When to Consider:**
- If you want consistency with the majority of scripts in the repository
- If you prefer minimal dependencies

**Challenges:**
- OAuth 2.0 flow is complex in shell scripts
- JSON parsing requires `jq` dependency
- Token refresh logic is error-prone
- Error handling is more verbose
- Markdown file updates require complex text manipulation

**If Using Shell Script:**
- Would need `curl`, `jq`, and potentially `gdate` (GNU date)
- Follow patterns from `greynoise/greynoise-lookup.sh` for API calls
- Use `config/config.sh` for credential management
- More complex to maintain long-term

### Alternative: Node.js (Not Recommended)

**When to Consider:**
- If you're already using Node.js in other projects
- If you prefer JavaScript ecosystem

**Challenges:**
- Not currently used in this codebase
- Would require Node.js runtime dependency
- Less consistent with existing patterns

## Implementation Recommendations

### Language/Tools

- **Python 3 (SELECTED):** `requests` library + direct REST calls or `python-linkedin-v2`
  - Primary implementation language
  - See [Language Recommendation](#language-recommendation) for detailed rationale
- **Shell Script (Alternative):** `curl` + `jq` with OAuth handling (more complex, not recommended)
- **Node.js (Alternative):** `node-linkedin-v2` or direct REST calls (not currently used in codebase)

### Script Structure

1. **Configuration:** Load credentials from secure storage
2. **Authentication:** Handle OAuth flow and token refresh
3. **Content Processing:** Read and validate `.txt` file
4. **API Interaction:** Post to LinkedIn
5. **Archive Update:** Update markdown file with URL

### Testing Strategy

- Test with LinkedIn sandbox/test environment first
- Validate with short test posts
- Test token refresh flow
- Handle edge cases (long posts, special characters)

## Next Steps

1. **Create LinkedIn Developer App**
2. **Set up OAuth 2.0 Flow**
3. **Test API Access** with simple post
4. **Build Script** to read `.txt` and post
5. **Add Archive Update** functionality

## Additional Resources

- [LinkedIn API Documentation](https://learn.microsoft.com/en-us/linkedin/)
- [LinkedIn UGC Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/ugc-post-api)
- [OAuth 2.0 Flow](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication)

## Questions for Design Review

1. **Authentication Method:** Should we use environment variables, config file, or credential manager?
2. **Token Refresh:** Automatic refresh or manual re-authentication?
3. **Error Handling:** How should we handle API failures?
4. **Content Validation:** Should we validate against style guide before posting?
5. **Archive Integration:** Should script automatically update `LinkedIn-posts.md`?
6. **Dry Run Mode:** Should we support a test mode that doesn't actually post?
