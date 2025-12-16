# LinkedIn API Setup Guide

This guide walks you through setting up LinkedIn API credentials for automated posting.

## Prerequisites

- LinkedIn account
- Python 3.8+ installed
- `requests` library: `pip install requests`

## Step 1: Create LinkedIn Developer App

1. **Navigate to LinkedIn Developer Portal:**
   - Go to [https://www.linkedin.com/developers/apps](https://www.linkedin.com/developers/apps)
   - You'll see the "My apps" page with a header showing:
     - "Simplify Your Development with LinkedIn API Client Libraries"
     - Navigation: Products, Docs and tools, Resources, My apps
   - If you don't have any apps yet, you'll see "Ready to create your first app?"

2. **Click "Create app" button:**
   - The button is typically in the top-right area or as a prominent button on the page
   - You may see a message like "Need some guidance? Check out our help pages" - you can ignore this for now

3. **Fill in the app creation form:**
   - **App name**: 
     - Enter a descriptive name (e.g., "My LinkedIn Posts", "Automated LinkedIn Posting")
     - This name will be visible to users when they authorize your app
   
   - **LinkedIn Page**: 
     - Select your LinkedIn company page or personal profile
     - If you don't have a company page, select your personal profile
     - This associates the app with your LinkedIn presence
   
   - **App use case**: 
     - Select **"Other"** from the dropdown
     - This is appropriate for personal automation tools
   
   - **User agreement URL**: 
     - Optional field - you can leave blank or use a placeholder like `https://example.com/terms`
     - Only required if you're building a public-facing app
   
   - **Privacy policy URL**: 
     - Optional field - you can leave blank or use a placeholder like `https://example.com/privacy`
     - Only required if you're building a public-facing app

4. **Review and create:**
   - Review the information you entered
   - Check the terms and conditions checkbox (if present)
   - Click **"Create app"** button at the bottom of the form

5. **Wait for app creation:**
   - LinkedIn will create your app (usually instant)
   - You'll be redirected to your app's dashboard
   - You should see tabs like: Overview, Auth, Products, Analytics, etc.

## Step 2: Configure OAuth Settings

1. **Navigate to Auth tab:**
   - In your app dashboard, click on the **"Auth"** tab in the top navigation
   - This is where you'll configure OAuth 2.0 settings

2. **Add Redirect URLs:**
   - Scroll down to the **"Redirect URLs"** section
   - Click **"Add redirect URL"** or the **"+"** button
   - Enter: `http://localhost:8080`
     - This is the default redirect URI for local testing
     - Must match exactly what you use in the OAuth flow
   - Click **"Update"** or **"Save"** to save the redirect URL
   - You can add multiple redirect URLs if needed (e.g., production URL)

3. **Request Product Access:**
   - Click on the **"Products"** tab in the top navigation
   - You'll see a list of available LinkedIn API products
   - Find and click on **"Sign In with LinkedIn using OpenID Connect"**:
     - Click **"Request access"** button
     - This is required for getting user profile information (person URN)
     - Approval is usually instant for basic access
   - Find and click on **"Share on LinkedIn"** (Default Tier):
     - Description: "Amplify your content by sharing it on LinkedIn"
     - Click **"Request access"** button
     - This is required for creating posts via the UGC Posts API
     - Approval is usually instant for Default Tier products
   - Wait for both products to show **"Approved"** status
     - You may need to refresh the page to see updated status
     - If approval is pending, wait a few minutes and refresh

4. **Verify settings:**
   - Go back to the **"Auth"** tab
   - Verify your redirect URL is saved
   - Note your **Client ID** and **Client Secret** (you'll need these next)

## Step 3: Get OAuth Credentials

1. **Navigate to Auth tab:**
   - In your app dashboard, click on the **"Auth"** tab
   - This is where your OAuth credentials are displayed

2. **Find your Client ID:**
   - Look for the **"Client ID"** field
   - It's usually displayed as a long string of characters
   - Click the **copy icon** (📋) next to it, or select and copy the entire value
   - Save this somewhere temporarily (you'll need it for the OAuth flow)

3. **Get your Client Secret:**
   - Look for the **"Client Secret"** field
   - It's initially hidden for security
   - Click the **"Show"** button or **eye icon** to reveal it
   - Once revealed, click the **copy icon** (📋) or select and copy the entire value
   - **Important**: Copy this immediately - it may hide again after a few seconds
   - Save this somewhere temporarily (you'll need it for the OAuth flow)

4. **Verify you have both:**
   - Client ID: A long string (usually starts with something like numbers/letters)
   - Client Secret: A long string (usually different format than Client ID)
   - Both are required for the OAuth flow

## Step 4: Complete OAuth Flow to Get Tokens

The OAuth flow requires browser interaction. You have two options:

### Option A: Use the OAuth Helper Script (Recommended)

We provide a helper script to guide you through the OAuth flow:

```bash
./LinkedIn-posts/scripts/linkedin-oauth-helper.py
```

This script will:
1. Generate the OAuth authorization URL
2. Open it in your browser
3. Guide you through the authorization process
4. Help you extract the authorization code
5. Exchange it for access and refresh tokens

### Option B: Manual OAuth Flow

1. **Generate Authorization URL:**
   ```
   https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8080&state=random_state_string&scope=openid profile w_member_social
   ```
   Replace `YOUR_CLIENT_ID` with your actual Client ID.

2. **Open URL in Browser:**
   - Copy the URL and open it in your browser
   - You'll be asked to authorize the app
   - After authorization, you'll be redirected to `http://localhost:8080?code=AUTHORIZATION_CODE&state=random_state_string`
   - Copy the `code` parameter from the URL

3. **Exchange Authorization Code for Tokens:**
   Use the `linkedin-oauth-helper.py` script or make a POST request:
   ```bash
   curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
     -d "grant_type=authorization_code" \
     -d "code=AUTHORIZATION_CODE" \
     -d "redirect_uri=http://localhost:8080" \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET"
   ```
   
   The response will contain:
   - `access_token`: Use this for API calls
   - `refresh_token`: Use this to get new access tokens when they expire
   - `expires_in`: Token expiration time in seconds

## Step 5: Run Setup Script

Once you have all credentials (Client ID, Client Secret, Access Token, Refresh Token):

```bash
./LinkedIn-posts/create-set-linkedin-credentials.py
```

**What to expect:**

1. **The script will check for existing credentials:**
   - If credentials already exist, it will ask if you want to overwrite
   - Type `y` to overwrite or `N` to cancel

2. **Browser will open (optional):**
   - The script will offer to open the LinkedIn Developer Portal
   - Press Enter to open, or type `N` to skip
   - This is just for reference - you should already have your credentials

3. **Enter your credentials one by one:**
   - **Client ID**: Paste the Client ID you copied from the Auth tab
   - **Client Secret (hidden)**: Paste the Client Secret (input will be hidden for security)
   - **Access Token (hidden)**: Paste the Access Token from the OAuth flow (input will be hidden)
   - **Refresh Token (hidden)**: Paste the Refresh Token from the OAuth flow (input will be hidden)

4. **Script will save credentials:**
   - Creates `~/.secure/` directory if it doesn't exist (with 700 permissions)
   - Creates `~/.secure/linkedin-set-api-key.sh` file (with 400 permissions - read-only)
   - Displays confirmation with file path and permissions

5. **You're done!**
   - Credentials are now saved securely
   - You can now use the posting script without entering credentials each time

## Step 6: Test the Integration

### Test with Dry Run First

Before posting to LinkedIn, validate your setup with a dry run:

```bash
./LinkedIn-posts/scripts/post-to-linkedin.py --dry-run LinkedIn-posts/test/test-post.txt
```

**What the dry run does:**
- Loads your credentials (will auto-run setup if missing)
- Reads the post file
- Validates content length (must be ≤ 3,000 characters)
- Checks formatting
- **Does NOT post to LinkedIn**
- Shows you what would be posted (first 200 characters)

**Expected output:**
```
Loading credentials from secure file...
Post content validated (XXX characters)

DRY RUN: Content is valid. Would post to LinkedIn.

First 200 characters:
[Your post content preview...]
```

### Post for Real

If the dry run passes, post to LinkedIn:

```bash
./LinkedIn-posts/scripts/post-to-linkedin.py LinkedIn-posts/test/test-post.txt
```

**What happens:**
1. Loads credentials
2. Validates content
3. Gets your LinkedIn person URN (may refresh token if needed)
4. Posts to LinkedIn via API
5. Displays the post ID and opens your LinkedIn activity page
6. Archive updates are currently manual (see root `LinkedIn-posts.md`)

**Expected output:**
```
Loading credentials from secure file...
Post content validated (XXX characters)
Authenticated as: urn:li:person:XXXXX
Posting to LinkedIn...

SUCCESS: Post created successfully!
Post ID: urn:li:share:XXXXX
Note: Post URL not available from API.
To get the post URL, go to your LinkedIn feed and find the post.
Click on the post timestamp or '...' menu to copy the URL.

Opening your LinkedIn recent activity page...
Opened: https://www.linkedin.com/in/glblackburn/recent-activity/all/
```

## Troubleshooting

### "LinkedIn API credentials not found"
- This means the credentials file doesn't exist
- The script will automatically run the setup script
- Follow the prompts to enter your credentials
- Make sure you've completed the OAuth flow first (Step 4)

### "Invalid redirect URI"
- **Error**: "redirect_uri does not match"
- **Solution**: 
  - Make sure the redirect URI in your OAuth request matches exactly what you configured in the LinkedIn app Auth tab
  - Check for typos, trailing slashes, or protocol mismatches (http vs https)
  - Common redirect URIs: `http://localhost:8080` or `https://yourdomain.com/callback`
  - The redirect URI must be added in the Auth tab before using it

### "Invalid client credentials"
- **Error**: "Invalid client_id or client_secret"
- **Solution**:
  - Double-check your Client ID and Client Secret from the Auth tab
  - Make sure there are no extra spaces when copying
  - Try copying again from the LinkedIn Developer Portal
  - Verify you're using the correct app's credentials

### "Insufficient permissions" or "Not enough permissions"
- **Error**: "Insufficient permissions to access: POST /ugcPosts"
- **Solution**:
  - Go to the **Products** tab in your app
  - Make sure you've requested access to **"Share on LinkedIn"** (Default Tier)
  - Wait for approval if status shows "Pending"
  - Refresh the page to check approval status
  - Approval is usually instant for Default Tier products

### "Token expired" or "Invalid access token"
- **Error**: "The token used in the request has expired"
- **Solution**:
  - Access tokens expire after a period (usually 60 days)
  - The script will automatically refresh tokens using the refresh token
  - If automatic refresh fails, you'll need to complete the OAuth flow again (Step 4)
  - Run the OAuth helper script again to get new tokens

### "Failed to get person URN"
- **Error**: "Failed to get person URN" or "401 Unauthorized"
- **Solution**:
  - Your access token may be expired or invalid
  - The script will try to refresh automatically
  - If refresh fails, complete the OAuth flow again
  - Make sure you requested "Sign In with LinkedIn using OpenID Connect" product access

### "Post content exceeds 3000 character limit"
- **Error**: "Post content exceeds 3000 character limit"
- **Solution**:
  - LinkedIn posts have a 3,000 character limit
  - Edit your post file to shorten the content
  - Remove unnecessary text or break into multiple posts

### Setup script can't find credentials file
- **Error**: "Credentials file not found" or permission errors
- **Solution**:
  - Make sure `~/.secure/` directory exists and has proper permissions (700)
  - Run the setup script again: `./LinkedIn-posts/scripts/create-set-linkedin-credentials.py`
  - The script will create the directory and file automatically

## Security Notes

- Never commit credentials to git
- The credentials file (`~/.secure/linkedin-set-api-key.sh`) has restricted permissions (read-only for owner)
- Keep your Client Secret and tokens secure
- Refresh tokens can be used to get new access tokens - keep them secure

## Additional Resources

- [LinkedIn API Documentation](https://learn.microsoft.com/en-us/linkedin/)
- [LinkedIn UGC Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/ugc-post-api)
- [OAuth 2.0 Flow Documentation](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authentication)
