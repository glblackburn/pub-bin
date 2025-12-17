#!/usr/bin/env python3
"""
Security Audit Script for Sensitive Data

Analyzes all files in the repository and git history for sensitive information:
- Email addresses
- GitHub org/repo names
- File paths (especially user-specific paths)
- API keys, tokens, passwords
- Other sensitive patterns
"""

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple


# Patterns for sensitive data detection
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
GITHUB_ORG_REPO_PATTERN = re.compile(r'(?:github\.com|github\.io)[/:]([A-Za-z0-9_-]+)/([A-Za-z0-9_.-]+)')
GITHUB_USER_PATTERN = re.compile(r'@([A-Za-z0-9_-]+)')
FILE_PATH_PATTERN = re.compile(r'(?:^|[\s"\'`])(/[A-Za-z0-9_/-]+(?:/[A-Za-z0-9_.-]+)+)(?:[\s"\'`]|$)')
USER_PATH_PATTERN = re.compile(r'(?:^|[\s"\'`])(/Users/[A-Za-z0-9_-]+/[^\s"\'`]+)')
API_KEY_PATTERN = re.compile(r'\b(?:api[_-]?key|apikey|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*[:=]\s*["\']?([A-Za-z0-9_-]{20,})["\']?', re.IGNORECASE)
PASSWORD_PATTERN = re.compile(r'\b(?:password|passwd|pwd)\s*[:=]\s*["\']?([^\s"\'`]{8,})["\']?', re.IGNORECASE)
TOKEN_PATTERN = re.compile(r'\b(?:token|bearer)\s*[:=]\s*["\']?([A-Za-z0-9_-]{20,})["\']?', re.IGNORECASE)

# Known safe patterns to exclude
SAFE_EMAILS = {'example.com', 'test.com', 'localhost', 'example.org'}
SAFE_PATHS = {'/usr/', '/etc/', '/var/', '/tmp/', '/opt/', '/bin/', '/sbin/', '/lib/', '/dev/'}
SAFE_GITHUB_ORGS = {'example', 'test', 'demo'}


def extract_emails(content: str, file_path: str) -> Set[str]:
    """Extract email addresses from content."""
    emails = set()
    for match in EMAIL_PATTERN.finditer(content):
        email = match.group(0).lower()
        # Skip safe domains
        if not any(domain in email for domain in SAFE_EMAILS):
            emails.add(email)
    return emails


def extract_github_refs(content: str, file_path: str) -> Set[Tuple[str, str]]:
    """Extract GitHub org/repo references."""
    refs = set()
    # Match github.com/org/repo or github.io/org/repo
    for match in GITHUB_ORG_REPO_PATTERN.finditer(content):
        org = match.group(1)
        repo = match.group(2)
        if org not in SAFE_GITHUB_ORGS:
            refs.add((org, repo))
    return refs


def extract_github_users(content: str, file_path: str) -> Set[str]:
    """Extract GitHub usernames (@username)."""
    users = set()
    for match in GITHUB_USER_PATTERN.finditer(content):
        user = match.group(1)
        if user not in SAFE_GITHUB_ORGS:
            users.add(user)
    return users


def extract_file_paths(content: str, file_path: str) -> Set[str]:
    """Extract file paths, especially user-specific paths."""
    paths = set()
    # User-specific paths (most sensitive)
    for match in USER_PATH_PATTERN.finditer(content):
        path = match.group(1)
        # Skip if it's a safe system path
        if not any(path.startswith(safe) for safe in SAFE_PATHS):
            paths.add(path)
    # Other absolute paths
    for match in FILE_PATH_PATTERN.finditer(content):
        path = match.group(1)
        # Skip safe system paths and already captured user paths
        if not any(path.startswith(safe) for safe in SAFE_PATHS) and not path.startswith('/Users/'):
            # Only include if it looks like a real path (has multiple components)
            if path.count('/') >= 2:
                paths.add(path)
    return paths


def extract_api_keys(content: str, file_path: str) -> List[Tuple[str, str]]:
    """Extract potential API keys and tokens."""
    keys = []
    for match in API_KEY_PATTERN.finditer(content):
        key_type = match.group(0).split(':')[0].split('=')[0].strip()
        key_value = match.group(1)
        if len(key_value) >= 20:  # Reasonable minimum length
            keys.append((key_type, key_value[:50]))  # Truncate for safety
    return keys


def extract_passwords(content: str, file_path: str) -> List[Tuple[str, str]]:
    """Extract potential passwords."""
    passwords = []
    for match in PASSWORD_PATTERN.finditer(content):
        pwd_type = match.group(0).split(':')[0].split('=')[0].strip()
        pwd_value = match.group(1)
        if len(pwd_value) >= 8:
            passwords.append((pwd_type, pwd_value[:30]))  # Truncate for safety
    return passwords


def extract_tokens(content: str, file_path: str) -> List[Tuple[str, str]]:
    """Extract potential tokens."""
    tokens = []
    for match in TOKEN_PATTERN.finditer(content):
        token_type = match.group(0).split(':')[0].split('=')[0].strip()
        token_value = match.group(1)
        if len(token_value) >= 20:
            tokens.append((token_type, token_value[:50]))  # Truncate for safety
    return tokens


def analyze_file(file_path: Path, exclude_patterns: List[str] = None) -> Dict:
    """Analyze a single file for sensitive data."""
    if exclude_patterns:
        for pattern in exclude_patterns:
            if pattern in str(file_path):
                return None
    
    try:
        # Skip binary files
        with open(file_path, 'rb') as f:
            chunk = f.read(512)
            if b'\x00' in chunk:
                return None  # Binary file
        
        # Read as text
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        return {'error': str(e)}
    
    result = {
        'file': str(file_path),
        'emails': extract_emails(content, str(file_path)),
        'github_refs': extract_github_refs(content, str(file_path)),
        'github_users': extract_github_users(content, str(file_path)),
        'file_paths': extract_file_paths(content, str(file_path)),
        'api_keys': extract_api_keys(content, str(file_path)),
        'passwords': extract_passwords(content, str(file_path)),
        'tokens': extract_tokens(content, str(file_path)),
    }
    
    # Only return if there's something found
    if any([result['emails'], result['github_refs'], result['github_users'], 
            result['file_paths'], result['api_keys'], result['passwords'], result['tokens']]):
        return result
    return None


def analyze_git_history(repo_path: Path) -> Dict:
    """Analyze git commit history for sensitive data."""
    results = {
        'commits': [],
        'emails': set(),
        'github_refs': set(),
        'github_users': set(),
        'file_paths': set(),
        'api_keys': [],
        'passwords': [],
        'tokens': [],
    }
    
    try:
        # Get all commit messages and diffs
        cmd = ['git', 'log', '--all', '--pretty=format:%H|%ae|%an|%s', '--name-only']
        output = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=30)
        
        if output.returncode != 0:
            return {'error': f'Git command failed: {output.stderr}'}
        
        lines = output.stdout.split('\n')
        current_commit = None
        
        for line in lines:
            if '|' in line and len(line.split('|')) == 4:
                # Commit header
                parts = line.split('|')
                commit_hash = parts[0]
                author_email = parts[1]
                author_name = parts[2]
                subject = parts[3]
                
                current_commit = {
                    'hash': commit_hash[:8],
                    'email': author_email,
                    'name': author_name,
                    'subject': subject,
                    'files': []
                }
                
                # Extract from commit metadata
                results['emails'].add(author_email.lower())
                results['emails'].update(extract_emails(subject, ''))
                results['github_refs'].update(extract_github_refs(subject, ''))
                results['github_users'].update(extract_github_users(subject, ''))
                
            elif line.strip() and current_commit:
                # File name in commit
                current_commit['files'].append(line.strip())
        
        # Get commit diffs
        cmd = ['git', 'log', '--all', '-p', '--pretty=format:%H']
        output = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=60)
        
        if output.returncode == 0:
            content = output.stdout
            results['emails'].update(extract_emails(content, ''))
            results['github_refs'].update(extract_github_refs(content, ''))
            results['github_users'].update(extract_github_users(content, ''))
            results['file_paths'].update(extract_file_paths(content, ''))
            results['api_keys'].extend(extract_api_keys(content, ''))
            results['passwords'].extend(extract_passwords(content, ''))
            results['tokens'].extend(extract_tokens(content, ''))
        
    except subprocess.TimeoutExpired:
        return {'error': 'Git history analysis timed out'}
    except Exception as e:
        return {'error': f'Error analyzing git history: {e}'}
    
    return results


def generate_report(file_results: List[Dict], git_results: Dict, output_path: Path, repo_path: Path):
    """Generate markdown report."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Aggregate all findings
    all_emails = set()
    all_github_refs = set()
    all_github_users = set()
    all_file_paths = set()
    all_api_keys = []
    all_passwords = []
    all_tokens = []
    
    files_with_emails = []
    files_with_github = []
    files_with_paths = []
    files_with_secrets = []
    
    for result in file_results:
        if result and 'error' not in result:
            if result['emails']:
                all_emails.update(result['emails'])
                files_with_emails.append(result['file'])
            if result['github_refs'] or result['github_users']:
                all_github_refs.update(result['github_refs'])
                all_github_users.update(result['github_users'])
                files_with_github.append(result['file'])
            if result['file_paths']:
                all_file_paths.update(result['file_paths'])
                files_with_paths.append(result['file'])
            if result['api_keys'] or result['passwords'] or result['tokens']:
                all_api_keys.extend(result['api_keys'])
                all_passwords.extend(result['passwords'])
                all_tokens.extend(result['tokens'])
                files_with_secrets.append(result['file'])
    
    # Add git history findings
    if 'error' not in git_results:
        all_emails.update(git_results.get('emails', set()))
        all_github_refs.update(git_results.get('github_refs', set()))
        all_github_users.update(git_results.get('github_users', set()))
        all_file_paths.update(git_results.get('file_paths', set()))
        all_api_keys.extend(git_results.get('api_keys', []))
        all_passwords.extend(git_results.get('passwords', []))
        all_tokens.extend(git_results.get('tokens', []))
    
    # Generate report
    lines = [
        "# Security Audit Report - Sensitive Data Analysis",
        "",
        f"**Generated:** {timestamp}",
        f"**Repository:** {repo_path}",
        f"**Files Analyzed:** {len(file_results)}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"- **Total Email Addresses Found:** {len(all_emails)}",
        f"- **Total GitHub References Found:** {len(all_github_refs)}",
        f"- **Total GitHub Users Found:** {len(all_github_users)}",
        f"- **Total File Paths Found:** {len(all_file_paths)}",
        f"- **Potential API Keys Found:** {len(all_api_keys)}",
        f"- **Potential Passwords Found:** {len(all_passwords)}",
        f"- **Potential Tokens Found:** {len(all_tokens)}",
        f"- **Files with Email Addresses:** {len(files_with_emails)}",
        f"- **Files with GitHub References:** {len(files_with_github)}",
        f"- **Files with File Paths:** {len(files_with_paths)}",
        f"- **Files with Potential Secrets:** {len(files_with_secrets)}",
        "",
        "---",
        "",
    ]
    
    # Email addresses
    if all_emails:
        lines.extend([
            "## Email Addresses",
            "",
            f"**Total Unique Emails:** {len(all_emails)}",
            "",
            "### Email List",
            ""
        ])
        for email in sorted(all_emails):
            lines.append(f"- `{email}`")
        lines.append("")
        lines.extend([
            "### Files Containing Emails",
            ""
        ])
        for file_path in sorted(set(files_with_emails))[:50]:  # Limit to 50
            lines.append(f"- `{file_path}`")
        if len(files_with_emails) > 50:
            lines.append(f"- ... and {len(files_with_emails) - 50} more files")
        lines.append("")
    
    # GitHub references
    if all_github_refs or all_github_users:
        lines.extend([
            "## GitHub References",
            "",
        ])
        if all_github_refs:
            lines.extend([
                f"**Total GitHub Org/Repo References:** {len(all_github_refs)}",
                "",
                "### Organization/Repository References",
                ""
            ])
            for org, repo in sorted(all_github_refs):
                lines.append(f"- `{org}/{repo}`")
            lines.append("")
        if all_github_users:
            lines.extend([
                f"**Total GitHub Users:** {len(all_github_users)}",
                "",
                "### GitHub Users",
                ""
            ])
            for user in sorted(all_github_users):
                lines.append(f"- `@{user}`")
            lines.append("")
        if files_with_github:
            lines.extend([
                "### Files Containing GitHub References",
                ""
            ])
            for file_path in sorted(set(files_with_github))[:50]:
                lines.append(f"- `{file_path}`")
            if len(files_with_github) > 50:
                lines.append(f"- ... and {len(files_with_github) - 50} more files")
            lines.append("")
    
    # File paths
    if all_file_paths:
        lines.extend([
            "## File Paths",
            "",
            f"**Total Unique Paths:** {len(all_file_paths)}",
            "",
            "### Path List",
            ""
        ])
        # Prioritize user-specific paths
        user_paths = [p for p in all_file_paths if p.startswith('/Users/')]
        other_paths = [p for p in all_file_paths if not p.startswith('/Users/')]
        
        if user_paths:
            lines.append("#### User-Specific Paths (High Priority)")
            lines.append("")
            for path in sorted(user_paths)[:100]:
                lines.append(f"- `{path}`")
            if len(user_paths) > 100:
                lines.append(f"- ... and {len(user_paths) - 100} more paths")
            lines.append("")
        
        if other_paths:
            lines.append("#### Other Absolute Paths")
            lines.append("")
            for path in sorted(other_paths)[:100]:
                lines.append(f"- `{path}`")
            if len(other_paths) > 100:
                lines.append(f"- ... and {len(other_paths) - 100} more paths")
            lines.append("")
        
        if files_with_paths:
            lines.extend([
                "### Files Containing Paths",
                ""
            ])
            for file_path in sorted(set(files_with_paths))[:50]:
                lines.append(f"- `{file_path}`")
            if len(files_with_paths) > 50:
                lines.append(f"- ... and {len(files_with_paths) - 50} more files")
            lines.append("")
    
    # Secrets
    if all_api_keys or all_passwords or all_tokens:
        lines.extend([
            "## Potential Secrets",
            "",
            "⚠️ **WARNING:** These may contain actual credentials. Review carefully!",
            "",
        ])
        
        if all_api_keys:
            lines.extend([
                f"### API Keys ({len(all_api_keys)} found)",
                ""
            ])
            # Group by type
            by_type = defaultdict(list)
            for key_type, key_value in all_api_keys:
                by_type[key_type].append(key_value)
            
            for key_type in sorted(by_type.keys()):
                lines.append(f"#### {key_type}")
                lines.append("")
                for key_value in by_type[key_type][:10]:  # Limit per type
                    lines.append(f"- `{key_value}...`")
                if len(by_type[key_type]) > 10:
                    lines.append(f"- ... and {len(by_type[key_type]) - 10} more")
                lines.append("")
        
        if all_passwords:
            lines.extend([
                f"### Passwords ({len(all_passwords)} found)",
                ""
            ])
            for pwd_type, pwd_value in all_passwords[:20]:
                lines.append(f"- `{pwd_type}: {pwd_value}...`")
            if len(all_passwords) > 20:
                lines.append(f"- ... and {len(all_passwords) - 20} more")
            lines.append("")
        
        if all_tokens:
            lines.extend([
                f"### Tokens ({len(all_tokens)} found)",
                ""
            ])
            for token_type, token_value in all_tokens[:20]:
                lines.append(f"- `{token_type}: {token_value}...`")
            if len(all_tokens) > 20:
                lines.append(f"- ... and {len(all_tokens) - 20} more")
            lines.append("")
        
        if files_with_secrets:
            lines.extend([
                "### Files Containing Potential Secrets",
                ""
            ])
            for file_path in sorted(set(files_with_secrets))[:50]:
                lines.append(f"- `{file_path}`")
            if len(files_with_secrets) > 50:
                lines.append(f"- ... and {len(files_with_secrets) - 50} more files")
            lines.append("")
    
    # Git history
    if 'error' not in git_results:
        lines.extend([
            "## Git History Analysis",
            "",
            "### Summary",
            ""
        ])
        if git_results.get('commits'):
            lines.append(f"- **Commits Analyzed:** {len(git_results['commits'])}")
        lines.append(f"- **Emails in History:** {len(git_results.get('emails', set()))}")
        lines.append(f"- **GitHub References in History:** {len(git_results.get('github_refs', set()))}")
        lines.append(f"- **File Paths in History:** {len(git_results.get('file_paths', set()))}")
        lines.append("")
    elif 'error' in git_results:
        lines.extend([
            "## Git History Analysis",
            "",
            f"⚠️ **Error:** {git_results['error']}",
            ""
        ])
    
    # Recommendations
    lines.extend([
        "---",
        "",
        "## Recommendations",
        "",
        "1. **Review all email addresses** - Consider if they should be sanitized or removed",
        "2. **Review GitHub references** - Ensure org/repo names don't expose sensitive information",
        "3. **Review file paths** - User-specific paths should be sanitized to generic paths",
        "4. **Review potential secrets** - If any are real credentials, rotate them immediately",
        "5. **Sanitize git history** - Use `git filter-repo` or similar tools to remove sensitive data from history",
        "6. **Add to .gitignore** - Ensure sensitive files are not tracked",
        "7. **Use environment variables** - Store secrets in environment variables or secret managers",
        ""
    ])
    
    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(
        description='Audit repository for sensitive data',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-d', '--directory', default='.',
                        help='Directory to analyze (default: current directory)')
    parser.add_argument('-o', '--output',
                        help='Output markdown file (default: sensitive_data_audit_<timestamp>.md)')
    parser.add_argument('--exclude', action='append',
                        help='Patterns to exclude from analysis (can be used multiple times)')
    parser.add_argument('--no-git', action='store_true',
                        help='Skip git history analysis')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Quiet mode')
    
    args = parser.parse_args()
    
    repo_path = Path(args.directory).resolve()
    
    if not repo_path.exists():
        print(f"ERROR: Directory not found: {repo_path}", file=sys.stderr)
        sys.exit(1)
    
    # Determine output file
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = repo_path / f"sensitive_data_audit_{timestamp}.md"
    
    exclude_patterns = args.exclude or []
    exclude_patterns.extend(['.git', 'node_modules', '.venv', 'venv', '__pycache__', '.DS_Store'])
    
    if not args.quiet:
        print(f"Analyzing files in: {repo_path}", file=sys.stderr)
    
    # Find all files
    all_files = []
    for file_path in repo_path.rglob('*'):
        if file_path.is_file():
            # Check if excluded
            excluded = False
            for pattern in exclude_patterns:
                if pattern in str(file_path):
                    excluded = True
                    break
            if not excluded:
                all_files.append(file_path)
    
    if not args.quiet:
        print(f"Found {len(all_files)} files to analyze", file=sys.stderr)
    
    # Analyze files
    file_results = []
    for i, file_path in enumerate(all_files, 1):
        if args.verbose and i % 100 == 0:
            print(f"  Processed {i}/{len(all_files)} files...", file=sys.stderr)
        
        result = analyze_file(file_path, exclude_patterns)
        if result:
            file_results.append(result)
    
    if not args.quiet:
        print(f"Found sensitive data in {len(file_results)} files", file=sys.stderr)
    
    # Analyze git history
    git_results = {}
    if not args.no_git:
        if not args.quiet:
            print("Analyzing git history...", file=sys.stderr)
        git_results = analyze_git_history(repo_path)
        if 'error' in git_results and not args.quiet:
            print(f"WARNING: {git_results['error']}", file=sys.stderr)
    
    # Generate report
    if not args.quiet:
        print(f"Generating report...", file=sys.stderr)
    
    generate_report(file_results, git_results, output_path, repo_path)
    
    if not args.quiet:
        print(f"✓ Report saved to: {output_path}", file=sys.stderr)


if __name__ == '__main__':
    main()
