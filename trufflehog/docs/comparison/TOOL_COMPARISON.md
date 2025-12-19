# Tool Comparison: Trufflehog vs audit-sensitive-data.py

## Overview

Both tools scan for sensitive information, but they serve **different purposes** and detect **different types** of sensitive data.

---

## Trufflehog

### Purpose
**Detects actual secrets/credentials** that could be used to access systems or services.

### What It Detects
- **Active secrets**: API keys, tokens, passwords that can authenticate to services
- **Verified secrets**: Can actually test if secrets are valid/active
- **Known patterns**: AWS keys, GitHub tokens, database passwords, Slack tokens, etc.
- **High-value targets**: Things that directly grant access

### How It Works
1. Scans git repositories (commits, branches, diffs)
2. Uses pattern matching for known secret formats
3. **Verifies secrets** by attempting to authenticate (optional but powerful)
4. Reports which secrets are "verified" (actually work) vs "unknown"

### Example Output
```
✅ Found verified result 🐷🔑
Detector Type: AWS
Raw result: AKIAIOSFODNN7EXAMPLE
File: config.json
Line: 42
Repository: file:///path/to/repo
```

### Use Case
**"Do we have any active secrets in our code that could be exploited?"**

---

## audit-sensitive-data.py

### Purpose
**Detects identifying information and metadata** that could expose details about you, your organization, or infrastructure.

### What It Detects
- **Email addresses**: Personal/work emails that identify individuals
- **GitHub references**: Org/repo names that reveal organization structure
- **File paths**: User-specific paths (`/Users/username/...`) that identify machines/users
- **Metadata**: Information that could be used for reconnaissance or social engineering
- **Potential secrets**: Basic pattern matching (but no verification)

### How It Works
1. Scans **all files** in the repository (not just git history)
2. Uses regex patterns to find identifying information
3. **No verification** - just pattern matching
4. Reports what information is exposed, not whether it's exploitable

### Example Output
```
## Email Addresses
- `user@example.com`
- `username@github.com`

## File Paths
- `/path/to/repository`
- `/home/user/data/github-backup/repos/...`
```

### Use Case
**"Do we have any information that could identify us or expose our infrastructure details?"**

---

## Key Differences

| Aspect | Trufflehog | audit-sensitive-data.py |
|--------|-----------|------------------------|
| **Primary Focus** | Active secrets/credentials | Identifying information/metadata |
| **Verification** | ✅ Can verify if secrets work | ❌ No verification |
| **Scope** | Git repositories (commits, diffs) | All files + git history |
| **Detection** | Known secret patterns + verification | Regex pattern matching |
| **Risk Level** | **HIGH** - Direct access to systems | **MEDIUM** - Information disclosure |
| **Action Required** | Rotate compromised secrets immediately | Sanitize/sanitize identifying info |
| **False Positives** | Lower (verification helps) | Higher (pattern matching only) |

---

## When to Use Each

### Use Trufflehog When:
- ✅ You want to find **actual secrets** that need rotation
- ✅ You need to know if secrets are **still active**
- ✅ You're scanning **git repositories** for leaked credentials
- ✅ You want **verified results** (secrets that actually work)
- ✅ You need to comply with security policies about credential exposure

### Use audit-sensitive-data.py When:
- ✅ You want to find **identifying information** (emails, paths, org names)
- ✅ You're preparing code for **public release** (sanitization)
- ✅ You want to check **all files**, not just git history
- ✅ You need to find **metadata leaks** (file paths, usernames)
- ✅ You're doing a **comprehensive privacy audit**

---

## Complementary Use

**They work best together:**

1. **Trufflehog** finds the secrets that need immediate rotation
2. **audit-sensitive-data.py** finds the identifying information that should be sanitized before public release

### Example Workflow:
```bash
# Step 1: Find active secrets (Trufflehog)
./trufflehog-local-git-repos.sh -d ./repos

# Step 2: Find identifying information (audit script)
./audit-sensitive-data.py -d .

# Step 3: Tokenize secrets (if needed for AI processing)
./trufflehog-tokenize-secrets.py -d ./scan_results

# Step 4: Sanitize identifying info before public release
# (manual process based on audit report)
```

---

## Summary

- **Trufflehog** = "What secrets can attackers use to break in?"
- **audit-sensitive-data.py** = "What information reveals who we are and how we work?"

Both are important for security, but they address different aspects:
- **Trufflehog**: Operational security (active threats)
- **audit-sensitive-data.py**: Privacy and information disclosure (metadata leaks)
