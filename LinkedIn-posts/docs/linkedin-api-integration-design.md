# LinkedIn API Integration - Design Recommendations

**Purpose:** Automate posting of `.txt` files as LinkedIn posts  
**Example File:** `LinkedIn-posts/examples/2025-12-12-network-capture-analysis-tools.txt`  
**Script Location:** `LinkedIn-posts/scripts/post-to-linkedin.py`  
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

### Integrated Single-Script Workflow

The implementation uses a **single script** (`post-to-linkedin.py`) that handles everything automatically:

1. **First-time setup (automatic):**
   - Script detects missing credentials
   - Guides user through complete setup process:
     - Instructions for creating LinkedIn Developer app
     - Getting Client ID and Client Secret
     - Configuring redirect URI
     - Requesting product access
     - Completing OAuth flow (opens browser, guides through authorization)
     - Saving credentials automatically
   - All in one interactive flow - no separate scripts needed

2. **Subsequent runs:**
   - Script loads credentials automatically
   - No user interaction needed (unless credentials expire)

3. **Posting workflow:**
   - Read `.txt` file content
   - Validate content (character limit, formatting)
   - Authenticate with LinkedIn API (refresh token if needed)
   - Post content via API
   - Capture and store LinkedIn post URL
   - Update markdown archive automatically

### User Experience

**First-time user:**
```bash
./LinkedIn-posts/scripts/post-to-linkedin.py LinkedIn-posts/examples/test-post.txt
```
- Script detects missing credentials
- Automatically starts interactive setup
- Guides through all steps
- Saves credentials
- Continues with posting

**Returning user:**
```bash
./LinkedIn-posts/scripts/post-to-linkedin.py LinkedIn-posts/examples/test-post.txt
```
- Script loads credentials automatically
- Posts immediately
- Updates archive

## Technical Considerations

### Security

#### Credential Management Pattern (Based on JIRA Script Pattern - Python Implementation)

**User Experience: Integrated Single-Script Setup Flow**

The credential management system is fully integrated into the main script. Users only need to run one command:

1. **First-time user runs the script:**
   ```bash
   ./LinkedIn-posts/scripts/post-to-linkedin.py LinkedIn-posts/examples/test-post.txt
   ```
   - Script checks for credentials in CLI args → environment variables → secure file
   - If credentials are missing, automatically starts integrated interactive setup
   - Setup includes:
     - Step-by-step instructions for creating LinkedIn Developer app
     - Getting Client ID and Client Secret
     - Configuring redirect URI
     - Requesting product access
     - Completing OAuth flow (opens browser automatically, guides through authorization)
     - Saving credentials automatically to `~/.secure/linkedin-set-api-key.sh`
   - Script automatically continues with posting after setup completes
   - **No separate scripts needed** - everything is in one command

2. **Subsequent runs:**
   ```bash
   ./LinkedIn-posts/scripts/post-to-linkedin.py LinkedIn-posts/examples/test-post.txt
   ```
   - Script loads credentials from secure file automatically
   - Posts immediately - no user interaction needed (unless credentials expire)

3. **Incomplete credentials:**
   - If credentials file exists but is missing values, script detects this
   - Automatically runs setup again to complete configuration
   - Provides clear error messages and guidance

**The credential management follows a three-tier priority system, matching the pattern used in `create-jira-ticket.sh`, but implemented in Python:**

**Priority Order (Highest to Lowest):**
1. **Command-line arguments** - `--client-id`, `--client-secret`, `--access-token`, `--refresh-token`
2. **Environment variables** - `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_REFRESH_TOKEN`
3. **Secure credentials file** - `~/.secure/linkedin-set-api-key.sh` (auto-created if missing)

**Credential Management Implementation:**

- **Integrated setup:** All setup is integrated into `scripts/post-to-linkedin.py`
  - No separate setup script needed
  - Interactive setup runs automatically when credentials are missing
  - Guides user through:
    - Creating LinkedIn Developer app (with instructions)
    - Getting Client ID and Client Secret
    - Configuring redirect URI
    - Requesting product access
    - Completing OAuth flow (opens browser, handles authorization)
    - Saving credentials automatically
  - Creates `~/.secure/linkedin-set-api-key.sh` with `export` statements (bash format for consistency)
  - Sets proper permissions: `chmod 700 ~/.secure`, `chmod 400 ~/.secure/linkedin-set-api-key.sh`
  - Uses `getpass` for secure token input (hidden input)
  - Validates inputs before writing

- **Credential loader module:** `linkedin_credentials.py` (Python module to load credentials)
  - Parses `~/.secure/linkedin-set-api-key.sh` to extract export statements
  - Returns credentials as dictionary
  - Returns empty dict if file doesn't exist (main script handles setup)

- **Main script credential loading pattern (integrated setup):**
  ```python
  def get_credentials(cli_args):
      """
      Load credentials using three-tier priority system.
      Automatically runs integrated setup if credentials are missing.
      """
      # Tier 1: Command-line arguments (highest priority)
      # Tier 2: Environment variables
      # Tier 3: Secure credentials file
      
      # If still missing after all tiers, run integrated setup
      if not all([client_id, client_secret, access_token, refresh_token]):
          setup_result = setup_credentials_interactive()
          # Setup includes:
          # - Instructions for creating LinkedIn app
          # - Getting Client ID and Secret
          # - Configuring redirect URI
          # - Requesting product access
          # - Completing OAuth flow (opens browser)
          # - Saving credentials automatically
          # Returns credentials dict or None
      
      return credentials_dict
  ```

- **Integrated setup function (`setup_credentials_interactive()`):**
  - Guides user through complete setup process
  - Includes step-by-step instructions for LinkedIn Developer Portal
  - Handles OAuth flow with browser integration
  - Saves credentials automatically
  - No separate scripts needed

- **Credential loader implementation (`linkedin_credentials.py`):**
  ```python
  import re
  from pathlib import Path
  from typing import Dict
  
  SECURE_DIR = Path.home() / '.secure'
  CREDENTIALS_FILE = SECURE_DIR / 'linkedin-set-api-key.sh'
  
  def load_linkedin_credentials() -> Dict[str, str]:
      """
      Load credentials from secure file.
      
      Returns:
          Dictionary with credential keys (LINKEDIN_CLIENT_ID, etc.)
          Empty dictionary if file doesn't exist (caller handles setup)
      """
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

- **Integrated setup in main script (`scripts/post-to-linkedin.py`):**
  - `setup_credentials_interactive()` function handles complete setup:
    - Step 1: Instructions for creating LinkedIn Developer app
    - Step 2: Get Client ID and Client Secret
    - Step 3: Configure redirect URI
    - Step 4: Request product access
    - Step 5: Complete OAuth flow (opens browser, handles authorization)
    - Step 6: Save credentials automatically
  - `complete_oauth_flow()` function handles OAuth authorization:
    - Generates authorization URL
    - Opens browser automatically
    - Guides user through authorization
    - Exchanges code for tokens
  - All integrated - no separate scripts needed

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
- **Output:** Update `LinkedIn-posts/LinkedIn-posts.md` with post URL
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

**Single Script Implementation (`scripts/post-to-linkedin.py`):**

1. **Credential Management:**
   - Three-tier loading (CLI args → env vars → secure file)
   - Integrated interactive setup if credentials missing
   - Automatic OAuth flow handling

2. **Authentication:**
   - Handle OAuth flow (integrated, opens browser)
   - Automatic token refresh
   - Get person URN for posting

3. **Content Processing:**
   - Read `.txt` file content
   - Validate content (character limit, formatting)

4. **API Interaction:**
   - Post to LinkedIn using UGC Posts API
   - Handle API errors and rate limits

5. **Archive Update:**
   - Update markdown file with post URL automatically
   - Extract date from filename or use current date

### Testing Strategy

- Test with LinkedIn sandbox/test environment first
- Validate with short test posts
- Test token refresh flow
- Handle edge cases (long posts, special characters)

## Implementation Status

✅ **Completed:**

1. **Single Script Implementation** - `scripts/post-to-linkedin.py` handles everything
2. **Integrated Setup** - Automatic interactive setup when credentials missing
3. **OAuth Flow Integration** - Browser-based OAuth flow built-in
4. **Credential Management** - Three-tier priority system with secure storage
5. **Token Refresh** - Automatic token refresh functionality
6. **Content Validation** - Character limit and formatting checks
7. **Archive Updates** - Automatic markdown archive updates
8. **Error Handling** - Comprehensive error handling and user guidance

**Usage:**
```bash
# First time (will run setup automatically)
./LinkedIn-posts/scripts/post-to-linkedin.py LinkedIn-posts/examples/test-post.txt

# Subsequent runs (loads credentials automatically)
./LinkedIn-posts/scripts/post-to-linkedin.py LinkedIn-posts/examples/test-post.txt

# Dry run (validate without posting)
./LinkedIn-posts/scripts/post-to-linkedin.py --dry-run LinkedIn-posts/examples/test-post.txt
```

## Additional Resources

- [LinkedIn API Documentation](https://learn.microsoft.com/en-us/linkedin/)
- [LinkedIn UGC Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/ugc-post-api)
- [OAuth 2.0 Flow](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication)

## Questions for Design Review

1. **Authentication Method:** Should we use environment variables, config file, or credential manager?
2. **Token Refresh:** Automatic refresh or manual re-authentication?
3. **Error Handling:** How should we handle API failures?
4. **Content Validation:** Should we validate against style guide before posting?
5. **Archive Integration:** Should script automatically update `LinkedIn-posts/LinkedIn-posts.md`?
6. **Dry Run Mode:** Should we support a test mode that doesn't actually post?
