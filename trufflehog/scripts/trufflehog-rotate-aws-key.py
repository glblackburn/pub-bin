#!/usr/bin/env python3
"""
Trufflehog AWS Key Rotation Script

Automatically rotate AWS keys found in trufflehog analysis reports.
Clones repositories, creates branches, replaces keys, and optionally commits changes.
"""

import argparse
import getpass
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TextIO


class TeeOutput:
    """Write to both stderr and a log file."""
    def __init__(self, log_file: Path, quiet: bool = False):
        self.log_file = log_file
        self.quiet = quiet
        self.file_handle: Optional[TextIO] = None
        self.original_stderr = sys.stderr

    def __enter__(self):
        self.file_handle = open(self.log_file, 'a', encoding='utf-8')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file_handle:
            self.file_handle.close()
        sys.stderr = self.original_stderr

    def write(self, text: str):
        """Write to both stderr and log file."""
        if not self.quiet:
            self.original_stderr.write(text)
            self.original_stderr.flush()
        if self.file_handle:
            self.file_handle.write(text)
            self.file_handle.flush()

    def flush(self):
        """Flush both outputs."""
        self.original_stderr.flush()
        if self.file_handle:
            self.file_handle.flush()

try:
    from git import Repo, GitCommandError
except ImportError:
    print("ERROR: GitPython is required.", file=sys.stderr)
    print("Install with: make install-deps", file=sys.stderr)
    print("Or manually: pip install GitPython", file=sys.stderr)
    sys.exit(1)

try:
    from github import Github
    GITHUB_API_AVAILABLE = True
except ImportError:
    GITHUB_API_AVAILABLE = False


def setup_secure_directories() -> Tuple[Path, Path, Path]:
    """
    Setup secure directory structure following ~/.secure pattern.
    Returns: (secure_dir, trufflehog_rotate_dir, backup_dir)
    """
    secure_dir = Path.home() / '.secure'
    trufflehog_rotate_dir = secure_dir / 'trufflehog-rotate'
    backup_dir = trufflehog_rotate_dir / 'backups'

    # Create directories with restrictive permissions
    secure_dir.mkdir(mode=0o700, exist_ok=True)
    trufflehog_rotate_dir.mkdir(mode=0o700, exist_ok=True)
    backup_dir.mkdir(mode=0o700, exist_ok=True)

    return secure_dir, trufflehog_rotate_dir, backup_dir


def convert_to_ssh_url(browser_url: str) -> Optional[str]:
    """
    Convert GitHub browser URL to SSH clone URL.
    Input: https://github.com/org/repo/blob/branch/file#L42
    Output: git@github.com:org/repo.git
    """
    match = re.match(r'https://github\.com/([^/]+)/([^/]+)/', browser_url)
    if match:
        org, repo = match.groups()
        return f'git@github.com:{org}/{repo}.git'
    return None


def extract_url_parts(browser_url: str) -> Optional[Dict]:
    """
    Extract parts from GitHub browser URL.
    Returns: {org, repo, branch, file_path, line_number}
    """
    pattern = r'https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/([^#]+)#L(\d+)'
    match = re.match(pattern, browser_url)
    if match:
        org, repo, branch, file_path, line_num = match.groups()
        return {
            'organization': org,
            'repository': repo,
            'branch': branch,
            'file_path': file_path,
            'line_number': int(line_num)
        }
    return None


# ============================================================================
# AUTOMATIC DISCOVERY FEATURE (ISOLATED FOR FUTURE DEVELOPMENT)
# ============================================================================
# This feature attempts to automatically find paired secrets near primary secrets.
# It is currently DISABLED in the main flow due to fragility. The code is preserved
# here for future development and improvement.
#
# To re-enable: Uncomment the discovery call in process_repository() and ensure
# old_paired_secret is not required when discovery is attempted.
# ============================================================================

def find_paired_secret_near_primary(
    file_path: Path,
    primary_secret_line: int,
    primary_secret_value: str,
    secret_type: str = 'aws',
    search_range: int = 50,
    debug: bool = False
) -> Optional[Tuple[int, str]]:
    """
    [DISABLED] Find paired secret near primary secret in same file.

    This function is isolated for future development. It is not currently used
    in the main processing flow. The main flow now requires explicit provision
    of old_paired_secret via environment variable or interactive prompt.

    Args:
        file_path: Path to file containing primary secret
        primary_secret_line: Line number where primary secret was found
        primary_secret_value: The primary secret value (for context validation)
        secret_type: Type of secret pair ('aws', 'username_password', etc.)
        search_range: Number of lines to search before/after (default: 50)
        debug: If True, print debug information about the search

    Returns:
        (line_number, paired_secret_value) or None if not found

    Strategy:
        1. Determine paired secret patterns based on secret_type
        2. Read file and extract lines [primary_secret_line - search_range : primary_secret_line + search_range]
        3. Match against paired secret patterns for the secret type
        4. Return first match found (closest to primary_secret_line preferred)

    Known Issues:
        - Fragile pattern matching (may miss non-standard formats)
        - Limited search range (50 lines may not be enough)
        - No validation that discovered secret actually belongs to primary secret
        - Pattern library may not cover all file formats
    """
    if secret_type != 'aws':
        # Future: Support other secret types
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Calculate search bounds
        start_line = max(0, primary_secret_line - search_range - 1)  # -1 for 0-indexed
        end_line = min(len(lines), primary_secret_line + search_range)

        # Get patterns for paired secret
        paired_patterns = get_patterns_for_secret_type(secret_type, is_paired=True)

        if debug:
            print(f"  Searching lines {start_line + 1} to {end_line} (range: ±{search_range} from line {primary_secret_line})", file=sys.stderr)
            print(f"  Using {len(paired_patterns)} pattern(s) for paired secret detection", file=sys.stderr)

        # Search for paired secret patterns
        best_match = None
        best_distance = float('inf')
        matches_found = []  # For debug output

        for line_idx in range(start_line, end_line):
            line = lines[line_idx]
            line_num = line_idx + 1  # Convert to 1-indexed

            # Try each pattern
            for pattern_idx, pattern_prefix in enumerate(paired_patterns):
                # Build pattern to match: prefix + secret value
                # AWS Secret Access Keys are typically 40 characters, base64-like
                # Pattern: prefix + (quoted or unquoted secret value)
                # More specific: look for 30-50 character base64-like strings
                pattern = pattern_prefix + r'(["\']?)([A-Za-z0-9+/=]{30,50})(["\']?)'
                try:
                    compiled_pattern = re.compile(pattern)
                    match = compiled_pattern.search(line)
                    if match:
                        secret_value = match.group(2)
                        # Validate: AWS Secret Access Keys are typically 40 chars, base64-like
                        # Exclude values that look like Access Key IDs (start with AKIA)
                        if len(secret_value) >= 30 and len(secret_value) <= 50 and not secret_value.startswith('AKIA'):
                            distance = abs(line_num - primary_secret_line)
                            matches_found.append((line_num, secret_value, pattern_idx, distance))
                            if distance < best_distance:
                                best_distance = distance
                                best_match = (line_num, secret_value)
                except re.error as e:
                    if debug:
                        print(f"  WARNING: Pattern {pattern_idx} compilation error: {e}", file=sys.stderr)

        if debug:
            if matches_found:
                print(f"  Found {len(matches_found)} potential paired secret(s):", file=sys.stderr)
                for line_num, val, pat_idx, dist in matches_found[:5]:  # Show first 5
                    print(f"    Line {line_num}: {val[:8]}...{val[-4:]} (pattern {pat_idx}, distance {dist})", file=sys.stderr)
                if len(matches_found) > 5:
                    print(f"    ... and {len(matches_found) - 5} more", file=sys.stderr)
                if best_match:
                    print(f"  Selected best match: line {best_match[0]}", file=sys.stderr)
            else:
                print(f"  No paired secret patterns matched in search range", file=sys.stderr)

        return best_match

    except Exception as e:
        if debug:
            print(f"  ERROR during discovery: {e}", file=sys.stderr)
        # Silently fail - will fall back to explicit mode or skip file
        return None

# ============================================================================
# END OF AUTOMATIC DISCOVERY FEATURE
# ============================================================================


def detect_secret_type(detector_type: str) -> str:
    """
    Detect secret type from trufflehog detector information.

    Args:
        detector_type: Detector type string from trufflehog

    Returns:
        Secret type string ('aws', 'username_password', etc.)
    """
    detector_lower = detector_type.lower()

    # AWS detectors
    if 'aws' in detector_lower or 'accesskey' in detector_lower:
        return 'aws'

    # Future: Add other secret type detection
    # if 'username' in detector_lower or 'password' in detector_lower:
    #     return 'username_password'
    # if 'api' in detector_lower and 'key' in detector_lower:
    #     return 'api_key_secret'

    # Default to 'aws' for now (Phase 1 focus)
    return 'aws'


def parse_report(report_path: Path) -> Dict:
    """
    Parse trufflehog-analyze-results.py markdown report.
    Returns: {identifier: identifier_data}
    """
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()

    identifiers = {}

    # Find all identifier sections
    identifier_pattern = r'^### <a id="[^"]+"></a>(TOKEN_|RAW_)(\S+) \((Tokenized|Raw)\)'

    for match in re.finditer(identifier_pattern, content, re.MULTILINE):
        prefix = match.group(1)
        identifier_suffix = match.group(2)
        identifier = f"{prefix}{identifier_suffix}"
        type_label = match.group(3)

        # Find the section content
        section_start = match.end()
        next_section = content.find('### <a id="', section_start)
        if next_section == -1:
            section_content = content[section_start:]
        else:
            section_content = content[section_start:next_section]

        # Extract raw secret value for RAW_ identifiers
        secret_value = None
        if identifier.startswith('RAW_'):
            secret_match = re.search(r'\*\*Raw Secret Value:\*\* `([^`]+)`', section_content)
            if secret_match:
                secret_value = secret_match.group(1)

        # Extract occurrences
        # Format is:
        # 1. **Repository:** repo-name
        #    - **File:** [file:line](url)
        #    - **Detector:** detector
        #    - **File:** [file2:line](url2)  (multiple files per repo)
        #    - **Detector:** detector2
        occurrences = []
        # Match repository line, then find File/Detector pairs on subsequent lines
        repo_pattern = r'(\d+)\. \*\*Repository:\*\* (\S+)'

        for repo_match in re.finditer(repo_pattern, section_content):
            repo_num = repo_match.group(1)
            repo_name = repo_match.group(2)

            # Find the content after this repository line
            repo_start = repo_match.end()
            # Find next repository or end of section
            next_repo_match = re.search(r'\n\d+\. \*\*Repository:\*\*', section_content[repo_start:])
            if next_repo_match:
                repo_section = section_content[repo_start:repo_start + next_repo_match.start()]
            else:
                repo_section = section_content[repo_start:]

            # Extract File/Detector pairs - they come in pairs, File then Detector
            # Pattern matches: "   - **File:** [file:line](url)" followed by "   - **Detector:** detector"
            # Allow flexible whitespace (spaces or tabs, multiple lines)
            file_detector_pattern = r'\s+-\s+\*\*File:\*\*\s+\[([^\]]+)\]\((https://github\.com/[^\)]+)\)\s*\n\s+-\s+\*\*Detector:\*\*\s+(\S+)'

            for file_det_match in re.finditer(file_detector_pattern, repo_section):
                file_display = file_det_match.group(1)
                file_url = file_det_match.group(2)
                detector = file_det_match.group(3)

                url_parts = extract_url_parts(file_url)
                if url_parts:
                    ssh_url = convert_to_ssh_url(file_url)
                    if ssh_url:
                        occurrences.append({
                            'repository_url': ssh_url,
                            'repository_name': repo_name,
                            'organization': url_parts['organization'],
                            'file_path': url_parts['file_path'],
                            'line_number': url_parts['line_number'],
                            'branch': url_parts['branch'],
                            'file_url': file_url,
                            'detector_type': detector
                        })

        if occurrences:
            # Detect secret type from first occurrence's detector
            secret_type = 'aws'  # Default
            if occurrences:
                first_detector = occurrences[0].get('detector_type', '')
                secret_type = detect_secret_type(first_detector)

            identifiers[identifier] = {
                'identifier': identifier,
                'secret_value': secret_value,
                'detector_type': occurrences[0].get('detector_type', 'AWS') if occurrences else 'AWS',
                'secret_type': secret_type,
                'occurrences': occurrences
            }

    return identifiers


def generate_branch_name(identifier: str, timestamp: str) -> str:
    """
    Generate timestamped branch name.
    Format: rotate-aws-key-<short-id>-<YYYYMMDD-HHMMSS>
    """
    # Extract short identifier (first 6-8 chars after prefix)
    if identifier.startswith('TOKEN_'):
        short_id = identifier[6:14]  # After TOKEN_
    elif identifier.startswith('RAW_'):
        short_id = identifier[4:12]  # After RAW_
    else:
        short_id = identifier[:8]

    # Format timestamp: 20251217-143000
    dt = datetime.fromisoformat(timestamp.replace('T', ' '))
    timestamp_str = dt.strftime('%Y%m%d-%H%M%S')

    return f"rotate-aws-key-{short_id}-{timestamp_str}"


def clone_repository(repo_url: str, local_path: Path, reuse: bool = False, verbose: bool = False) -> bool:
    """
    Clone repository to local path.
    Returns: True if successful, False otherwise
    """
    if local_path.exists() and reuse:
        if verbose:
            print(f"  Updating existing clone: {local_path}", file=sys.stderr)
        try:
            repo = Repo(local_path)
            repo.remotes.origin.fetch()
            return True
        except Exception as e:
            if verbose:
                print(f"  Failed to update existing clone: {e}", file=sys.stderr)
            return False

    # Verify SSH access first
    try:
        result = subprocess.run(
            ['git', 'ls-remote', repo_url],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            if verbose:
                print(f"  SSH access verification failed: {result.stderr}", file=sys.stderr)
            return False
    except Exception as e:
        if verbose:
            print(f"  SSH access verification error: {e}", file=sys.stderr)
        return False

    # Clone repository
    try:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        Repo.clone_from(repo_url, str(local_path))
        return True
    except Exception as e:
        if verbose:
            print(f"  Clone failed: {e}", file=sys.stderr)
        return False


# Pattern definitions for secret types
AWS_ACCESS_KEY_PATTERNS = [
    r'(AWS_ACCESS_KEY_ID\s*[=:]\s*["\']?)',
    r'("accessKeyId"\s*:\s*["\']?)',
    r'("access_key"\s*:\s*["\']?)',
    r'(access_key\s*[=:]\s*["\']?)',
    r'("[^"]*\.accessKey"\s*:\s*["\']?)',  # JSON keys like "aws.sqs.automotive_que.accessKey"
    r'("[^"]*accessKey[^"]*"\s*:\s*["\']?)',  # Any JSON key containing "accessKey"
    r'("[^"]*\.awsAccessKey"\s*:\s*["\']?)',  # JSON keys like "aws.s3.awsAccessKey"
]

AWS_SECRET_KEY_PATTERNS = [
    r'(AWS_SECRET_ACCESS_KEY\s*[=:]\s*["\']?)',
    r'("secretAccessKey"\s*:\s*["\']?)',
    r'("secret_key"\s*:\s*["\']?)',
    r'(secret_key\s*[=:]\s*["\']?)',
    r'(AWS_SECRET_KEY\s*[=:]\s*["\']?)',
    r'("[^"]*\.secretKey"\s*:\s*["\']?)',  # JSON keys like "aws.sqs.automotive_que.secretKey"
    r'("[^"]*\.awsSecretKey"\s*:\s*["\']?)',  # JSON keys like "aws.s3.awsSecretKey"
    r'("[^"]*secretKey[^"]*"\s*:\s*["\']?)',  # Any JSON key containing "secretKey"
]


def get_patterns_for_secret_type(secret_type: str, is_paired: bool = False) -> List[str]:
    """
    Get patterns for a given secret type.

    Args:
        secret_type: Type of secret ('aws', 'username_password', etc.)
        is_paired: If True, return paired secret patterns; if False, return primary patterns

    Returns:
        List of regex patterns
    """
    if secret_type == 'aws':
        return AWS_SECRET_KEY_PATTERNS if is_paired else AWS_ACCESS_KEY_PATTERNS
    # Future: Add other secret types here
    return []


def replace_key_in_file(file_path: Path, old_key: str, new_key: str, line_number: int,
                        backup_path: Optional[Path] = None, secret_type: str = 'aws',
                        is_paired: bool = False, verbose: bool = False) -> bool:
    """
    Replace AWS key in file.

    Args:
        file_path: Path to file
        old_key: Old key value to replace
        new_key: New key value
        line_number: Line number where key was found (for context)
        backup_path: Optional path to create backup
        secret_type: Type of secret ('aws', etc.)
        is_paired: If True, use paired secret patterns; if False, use primary patterns

    Returns:
        True if replacement was made, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Create backup if requested
        if backup_path:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            backup_path.chmod(0o600)

        # Get patterns based on secret type and whether it's paired
        pattern_prefixes = get_patterns_for_secret_type(secret_type, is_paired)

        # Build patterns with old_key and new_key
        # Compile patterns explicitly to catch errors early and ensure proper raw string handling
        patterns = []
        escaped_old_key = re.escape(old_key)
        # Escape new_key for use in replacement string (escape backslashes and $)
        escaped_new_key = new_key.replace('\\', '\\\\').replace('$', '\\$')

        for prefix in pattern_prefixes:
            # Build pattern: prefix (capture group) + escaped old_key + quote (capture group)
            pattern_str = prefix + escaped_old_key + r'(["\']?)'
            # Compile pattern to catch any syntax errors early and ensure proper handling
            try:
                compiled_pattern = re.compile(pattern_str)
            except re.error as e:
                # Log the error for debugging
                if verbose:
                    print(f"  Pattern compilation failed for prefix '{prefix[:50]}...': {e}", file=sys.stderr)
                # Skip invalid patterns (shouldn't happen with our patterns, but be safe)
                continue
            except Exception as e:
                if verbose:
                    print(f"  Unexpected error compiling pattern: {e}", file=sys.stderr)
                continue

            # Build replacement: \1 (prefix) + new_key (literal) + \2 (quote)
            # In replacement strings, backreferences use \1, \2, etc.
            replacement = r'\1' + escaped_new_key + r'\2'
            patterns.append((compiled_pattern, replacement))

        # Fallback: exact match (no prefix pattern)
        try:
            fallback_pattern = re.compile(re.escape(old_key))
            patterns.append((fallback_pattern, new_key))
        except re.error:
            pass  # Should never fail, but be safe

        modified = False
        for compiled_pattern, replacement in patterns:
            try:
                new_content = compiled_pattern.sub(replacement, content)
                if new_content != content:
                    modified = True
                    content = new_content
                    break
            except Exception as e:
                # Skip this pattern if it fails, try next one
                continue

        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False
    except re.error as e:
        print(f"ERROR: Invalid regex pattern in {file_path}: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        return False
    except Exception as e:
        print(f"ERROR: Failed to replace key in {file_path}: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def replace_paired_secrets_in_file(file_path: Path, old_primary: str, new_primary: str,
                                   old_paired: str, new_paired: str, line_number: int,
                                   backup_path: Optional[Path] = None, secret_type: str = 'aws') -> Tuple[bool, bool]:
    """
    Atomically replace both primary and paired secrets in file.

    Args:
        file_path: Path to file
        old_primary: Old primary secret value
        new_primary: New primary secret value
        old_paired: Old paired secret value
        new_paired: New paired secret value
        line_number: Line number where primary secret was found
        backup_path: Optional path to create backup
        secret_type: Type of secret pair ('aws', etc.)

    Returns:
        (primary_success, paired_success) - Both must be True for success
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = content = f.read()

        # Create backup before any modifications
        if backup_path:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            backup_path.chmod(0o600)

        # Replace primary secret
        primary_success = replace_key_in_file(
            file_path, old_primary, new_primary, line_number,
            backup_path=None, secret_type=secret_type, is_paired=False, verbose=False
        )

        # If primary replacement failed, return immediately
        if not primary_success:
            return False, False

        # Read updated content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace paired secret
        paired_success = replace_key_in_file(
            file_path, old_paired, new_paired, line_number,
            backup_path=None, secret_type=secret_type, is_paired=True, verbose=False
        )

        # If paired replacement failed, rollback primary
        if not paired_success:
            # Restore from backup
            if backup_path and backup_path.exists():
                with open(backup_path, 'r', encoding='utf-8') as f:
                    rollback_content = f.read()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(rollback_content)
                print(f"ERROR: Paired secret replacement failed. Rolled back primary secret replacement in {file_path}", file=sys.stderr)
            return False, False

        return True, True

    except Exception as e:
        print(f"ERROR: Failed to replace paired secrets in {file_path}: {e}", file=sys.stderr)
        # Attempt rollback if backup exists
        if backup_path and backup_path.exists():
            try:
                with open(backup_path, 'r', encoding='utf-8') as f:
                    rollback_content = f.read()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(rollback_content)
            except Exception as rollback_error:
                print(f"ERROR: Failed to rollback {file_path}: {rollback_error}", file=sys.stderr)
        return False, False


def show_file_context(file_path: Path, line_number: int, context_lines: int = 10) -> None:
    """Show file content around a specific line number."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        start_line = max(0, line_number - context_lines - 1)
        end_line = min(len(lines), line_number + context_lines)

        print(f"\nFile Context (lines {start_line + 1}-{end_line}):", file=sys.stderr)
        print("-" * 70, file=sys.stderr)
        for i in range(start_line, end_line):
            line_num = i + 1
            marker = " >>> " if line_num == line_number else "     "
            # Mask potential secrets in output
            line_content = lines[i].rstrip()
            # Simple masking: if line looks like it contains a secret, mask it
            if len(line_content) > 50 and ('"' in line_content or "'" in line_content):
                # Try to mask JSON-like values
                import re
                # Mask values that look like secrets (long alphanumeric strings)
                masked_line = re.sub(r':\s*["\']?([A-Za-z0-9+/=]{20,})["\']?', r': "***MASKED***"', line_content)
                if masked_line != line_content:
                    line_content = masked_line
            print(f"{marker}{line_num:4d}: {line_content}", file=sys.stderr)
        print("-" * 70, file=sys.stderr)
    except Exception as e:
        print(f"  (Could not read file context: {e})", file=sys.stderr)


def confirm_replacement(file_path: Path, old_primary: str, new_primary: str,
                        old_paired: Optional[str] = None, new_paired: Optional[str] = None,
                        primary_line: int = None, paired_line: int = None,
                        show_context: bool = True, discovery_info: Optional[str] = None,
                        confirm_all_ref: Optional[List[bool]] = None) -> bool:
    """
    Show replacement details and wait for user confirmation in debug mode.

    Args:
        file_path: Path to file being modified
        old_primary: Old primary secret value
        new_primary: New primary secret value
        old_paired: Old paired secret value (optional)
        new_paired: New paired secret value (optional)
        primary_line: Line number of primary secret
        paired_line: Line number of paired secret
        show_context: Whether to show file context around the line
        discovery_info: Additional information about discovery process
        confirm_all_ref: Mutable container (list) to track if "all" was selected

    Returns:
        True if user confirms, False otherwise
    """
    # Check if "all" was already selected
    if confirm_all_ref and len(confirm_all_ref) > 0 and confirm_all_ref[0]:
        return True

    print("\n" + "=" * 70, file=sys.stderr)
    print("DEBUG MODE: Replacement Preview", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print(f"File: {file_path}", file=sys.stderr)

    # Show file context around primary secret
    if show_context and primary_line:
        show_file_context(file_path, primary_line)

    print(f"\nPrimary Secret Replacement:", file=sys.stderr)
    print(f"  Old value: {old_primary[:8]}...{old_primary[-4:] if len(old_primary) > 12 else old_primary} (length: {len(old_primary)})", file=sys.stderr)
    print(f"  New value: {new_primary[:8]}...{new_primary[-4:] if len(new_primary) > 12 else new_primary} (length: {len(new_primary)})", file=sys.stderr)
    if primary_line:
        print(f"  Location: Line {primary_line}", file=sys.stderr)

    if old_paired and new_paired:
        print(f"\nPaired Secret Replacement:", file=sys.stderr)
        print(f"  Old value: {old_paired[:8]}...{old_paired[-4:] if len(old_paired) > 12 else old_paired} (length: {len(old_paired)})", file=sys.stderr)
        print(f"  New value: {new_paired[:8]}...{new_paired[-4:] if len(new_paired) > 12 else new_paired} (length: {len(new_paired)})", file=sys.stderr)
        if paired_line:
            print(f"  Location: Line {paired_line}", file=sys.stderr)
            if show_context and paired_line != primary_line:
                show_file_context(file_path, paired_line)
        elif primary_line:
            print(f"  Location: Discovered near line {primary_line}", file=sys.stderr)
    else:
        print(f"\nPaired Secret: NOT FOUND", file=sys.stderr)
        if discovery_info:
            print(f"  {discovery_info}", file=sys.stderr)

    if discovery_info:
        print(f"\nDiscovery Info:", file=sys.stderr)
        print(f"  {discovery_info}", file=sys.stderr)

    print("\n" + "=" * 70, file=sys.stderr)
    response = input("Proceed with this replacement? (yes/no/all/skip): ").strip().lower()
    print("=" * 70 + "\n", file=sys.stderr)

    # Handle "all" option
    if response in ('all', 'a'):
        if confirm_all_ref is not None:
            confirm_all_ref.clear()
            confirm_all_ref.append(True)
        print("INFO: Proceeding with all remaining replacements without confirmation", file=sys.stderr)
        return True

    return response in ('yes', 'y')


def process_repository(repo_info: Dict, old_key: str, new_key: str, work_dir: Path,
                      backup_dir: Path, branch_prefix: str, timestamp: str,
                      mode: str, reuse_clones: bool = False, verbose: bool = False,
                      push: bool = False, force_push: bool = False, push_remote: str = 'origin',
                      skip_if_exists: bool = True, paired_secret_mode: bool = False,
                      old_paired_secret: Optional[str] = None, new_paired_secret: Optional[str] = None,
                      secret_type: str = 'aws', paired_secret_occurrences: Optional[List[Dict]] = None,
                      debug: bool = False, quiet: bool = False,
                      old_paired_secret_ref: Optional[List[str]] = None,
                      confirm_all_ref: Optional[List[bool]] = None) -> Dict:
    """
    Process a single repository: clone, branch, replace key.
    Returns: Status dictionary
    """
    repo_url = repo_info['repository_url']
    repo_name = repo_info['repository_name']
    org = repo_info['organization']

    # Determine local clone path
    local_path = work_dir / 'repos' / f"{org}-{repo_name}"

    status = {
        'repository_url': repo_url,
        'repository_name': repo_name,
        'organization': org,
        'local_clone_path': str(local_path),
        'status': 'pending',
        'files_modified': [],
        'changes_committed': False,
        'commit_hash': None,
        'backup_files': [],
        'pushed': False,
        'push_attempted': False,
        'push_error': None,
        'push_timestamp': None,
        'pr_created': False,
        'pr_attempted': False,
        'pr_url': None,
        'pr_number': None,
        'pr_error': None,
        'pr_timestamp': None,
    }

    try:
        # Clone repository
        if verbose:
            print(f"  Cloning repository: {repo_url}", file=sys.stderr)

        if not clone_repository(repo_url, local_path, reuse=reuse_clones, verbose=verbose):
            status['status'] = 'failed'
            status['error'] = 'Clone failed'
            return status

        # Open repository
        repo = Repo(str(local_path))

        # Check if clean
        if repo.is_dirty():
            status['status'] = 'failed'
            status['error'] = 'Repository not clean'
            return status

        # Fetch latest
        repo.remotes.origin.fetch()

        # Checkout base branch (get from first occurrence)
        base_branch = 'main'
        if repo_info.get('occurrences'):
            base_branch = repo_info['occurrences'][0].get('branch', 'main')
        try:
            repo.git.checkout(base_branch)
            repo.git.pull('origin', base_branch)
        except Exception as e:
            # Try main if specified branch doesn't exist
            if base_branch != 'main':
                try:
                    repo.git.checkout('main')
                    repo.git.pull('origin', 'main')
                    base_branch = 'main'
                except Exception as e2:
                    status['status'] = 'failed'
                    status['error'] = f'Cannot checkout branch {base_branch} or main: {e}, {e2}'
                    return status
            else:
                status['status'] = 'failed'
                status['error'] = f'Cannot checkout branch {base_branch}: {e}'
                return status

        # Create new branch using generate_branch_name function
        identifier = repo_info.get('identifier', 'unknown')
        # generate_branch_name returns "rotate-aws-key-{short_id}-{timestamp}"
        # Extract the short_id-timestamp part and use with configured branch_prefix
        base_branch_name = generate_branch_name(identifier, timestamp)
        # Remove the default prefix "rotate-aws-key-" and use branch_prefix instead
        if base_branch_name.startswith('rotate-aws-key-'):
            short_id_timestamp = base_branch_name[len('rotate-aws-key-'):]
        else:
            # Fallback if format changes
            short_id_timestamp = '-'.join(base_branch_name.split('-')[2:])
        branch_name = f"{branch_prefix}-{short_id_timestamp}"

        try:
            repo.git.checkout('-b', branch_name)
        except GitCommandError:
            # Branch exists - verify it's related to this rotation
            # Check if branch was created for this identifier by checking recent commits
            try:
                branch_commits = list(repo.iter_commits(branch_name, max_count=1))
                if branch_commits and identifier in branch_commits[0].message:
                    # Branch appears to be for this rotation, use it
                    repo.git.checkout(branch_name)
                else:
                    # Branch exists but doesn't match, create unique name
                    branch_name = f"{branch_name}-{int(datetime.now().timestamp())}"
                    repo.git.checkout('-b', branch_name)
            except Exception:
                # If we can't verify, create unique name to be safe
                branch_name = f"{branch_name}-{int(datetime.now().timestamp())}"
                repo.git.checkout('-b', branch_name)

        status['branch_name'] = branch_name
        status['base_branch'] = base_branch

        # Process files
        files_modified = []
        backup_files = []
        processed_files = set()  # Track files we've already processed

        # Use a mutable container for old_paired_secret so we can update it if user provides it
        # If not provided, create a new one; otherwise use the shared one
        if old_paired_secret_ref is None:
            old_paired_secret_ref = [old_paired_secret] if old_paired_secret else []
        elif old_paired_secret and not old_paired_secret_ref:
            # If we have old_paired_secret but ref is empty, populate it
            old_paired_secret_ref.append(old_paired_secret)

        if paired_secret_mode and new_paired_secret:
            # Paired secret mode: process both primary and paired secret occurrences
            primary_occurrences = []
            paired_occurrences = []

            # Collect primary secret occurrences
            for occ in repo_info.get('occurrences', []):
                if occ['repository_name'] == repo_name:
                    primary_occurrences.append(occ)

            # Collect paired secret occurrences if provided (explicit mode)
            if paired_secret_occurrences:
                for occ in paired_secret_occurrences:
                    if occ['repository_name'] == repo_name:
                        paired_occurrences.append(occ)

            # Process primary occurrences
            for primary_occ in primary_occurrences:
                file_path = local_path / primary_occ['file_path']
                if not file_path.exists():
                    continue

                # Get current old_paired_secret value (from ref or None)
                current_old_paired_secret = old_paired_secret_ref[0] if old_paired_secret_ref else None

                # Debug mode: show what we're about to process
                if debug:
                    print(f"\n{'='*70}", file=sys.stderr)
                    print(f"DEBUG: Processing {primary_occ['file_path']} at line {primary_occ['line_number']}", file=sys.stderr)
                    print(f"{'='*70}", file=sys.stderr)
                    print(f"Primary secret (old): {old_key[:8]}...{old_key[-4:] if len(old_key) > 12 else old_key}", file=sys.stderr)
                    print(f"Primary secret (new): {new_key[:8]}...{new_key[-4:] if len(new_key) > 12 else new_key}", file=sys.stderr)
                    if current_old_paired_secret:
                        print(f"Paired secret (old): {current_old_paired_secret[:8]}...{current_old_paired_secret[-4:] if len(current_old_paired_secret) > 12 else current_old_paired_secret}", file=sys.stderr)
                    else:
                        print(f"Paired secret (old): Not provided - will prompt", file=sys.stderr)
                    print(f"Paired secret (new): {new_paired_secret[:8]}...{new_paired_secret[-4:] if len(new_paired_secret) > 12 else new_paired_secret}", file=sys.stderr)

                # Check if we have old paired secret - prompt if not set
                if not current_old_paired_secret:
                    print("\n" + "=" * 70, file=sys.stderr)
                    print("Old paired secret is required for paired secret rotation.", file=sys.stderr)
                    print("Set TRUFFLEHOG_OLD_AWS_SECRET_KEY environment variable to avoid this prompt.", file=sys.stderr)
                    print("=" * 70, file=sys.stderr)
                    prompted_old_paired = getpass.getpass("Enter old paired secret (input will be hidden): ")
                    if prompted_old_paired:
                        # Update old_paired_secret_ref so it persists for remaining files
                        old_paired_secret_ref.clear()
                        old_paired_secret_ref.append(prompted_old_paired)
                        current_old_paired_secret = prompted_old_paired
                        if not quiet:
                            print("INFO: Using prompted old paired secret for remaining files", file=sys.stderr)
                    else:
                        if verbose or debug:
                            print(f"  Skipping {primary_occ['file_path']} - old paired secret not provided", file=sys.stderr)
                        continue

                # Use the old paired secret (from env var or prompt)
                paired_secret_to_use = current_old_paired_secret

                # Debug mode: show replacement details and wait for confirmation
                if debug:
                    if not confirm_replacement(
                        file_path, old_key, new_key,
                        old_paired=paired_secret_to_use, new_paired=new_paired_secret,
                        primary_line=primary_occ['line_number'],
                        paired_line=None,
                        discovery_info="Using explicitly provided old paired secret",
                        confirm_all_ref=confirm_all_ref
                    ):
                        if verbose or debug:
                            print(f"  Skipping {primary_occ['file_path']} - user declined", file=sys.stderr)
                        continue

                # Same file: atomic replacement
                backup_path = backup_dir / f"{org}-{repo_name}-{primary_occ['file_path'].replace('/', '-')}"
                primary_success, paired_success = replace_paired_secrets_in_file(
                    file_path, old_key, new_key, paired_secret_to_use, new_paired_secret,
                    primary_occ['line_number'], backup_path, secret_type
                )
                if primary_success and paired_success:
                    if primary_occ['file_path'] not in processed_files:
                        files_modified.append(primary_occ['file_path'])
                        backup_files.append(str(backup_path))
                        processed_files.add(primary_occ['file_path'])
                elif primary_success and not paired_success:
                    status['status'] = 'failed'
                    status['error'] = f'Paired secret replacement failed in {primary_occ["file_path"]} (rolled back)'
                    return status

            # Process paired secret occurrences that are in different files (explicit mode only)
            if paired_occurrences:
                for paired_occ in paired_occurrences:
                    file_path = local_path / paired_occ['file_path']
                    if not file_path.exists():
                        continue

                    # Skip if already processed (was in same file as primary)
                    if paired_occ['file_path'] in processed_files:
                        continue

                    # Different file: replace paired secret
                    backup_path = backup_dir / f"{org}-{repo_name}-{paired_occ['file_path'].replace('/', '-')}"

                    # Get current old_paired_secret value
                    current_old_paired_secret = old_paired_secret_ref[0] if old_paired_secret_ref else None
                    if not current_old_paired_secret:
                        if verbose or debug:
                            print(f"  WARNING: Old paired secret not available for {paired_occ['file_path']}", file=sys.stderr)
                        continue

                    # Debug mode: show replacement details and wait for confirmation
                    if debug:
                        if not confirm_replacement(
                            file_path, None, None,
                            old_paired=current_old_paired_secret, new_paired=new_paired_secret,
                            paired_line=paired_occ['line_number'],
                            confirm_all_ref=confirm_all_ref
                        ):
                            if verbose or debug:
                                print(f"  Skipping {paired_occ['file_path']} - user declined", file=sys.stderr)
                            continue

                    if replace_key_in_file(file_path, current_old_paired_secret, new_paired_secret, paired_occ['line_number'], backup_path, secret_type=secret_type, is_paired=True, verbose=verbose):
                        files_modified.append(paired_occ['file_path'])
                        backup_files.append(str(backup_path))
                        processed_files.add(paired_occ['file_path'])
        else:
            # Single secret mode: replace only primary secret
            for occ in repo_info.get('occurrences', []):
                if occ['repository_name'] == repo_name:
                    file_path = local_path / occ['file_path']
                    if file_path.exists():
                        backup_path = backup_dir / f"{org}-{repo_name}-{occ['file_path'].replace('/', '-')}"

                        # Debug mode: show replacement details and wait for confirmation
                        if debug:
                            if not confirm_replacement(
                                file_path, old_key, new_key,
                                primary_line=occ['line_number'],
                                confirm_all_ref=confirm_all_ref
                            ):
                                if verbose or debug:
                                    print(f"  Skipping {occ['file_path']} - user declined", file=sys.stderr)
                                continue

                        if replace_key_in_file(file_path, old_key, new_key, occ['line_number'], backup_path, secret_type=secret_type, verbose=verbose):
                            files_modified.append(occ['file_path'])
                            backup_files.append(str(backup_path))

        status['files_modified'] = files_modified
        status['backup_files'] = backup_files

        if not files_modified:
            status['status'] = 'skipped'
            status['error'] = 'No files modified'
            return status

        # Stage changes
        repo.git.add('-A')

        # Commit if in commit mode
        if mode == 'commit':
            if paired_secret_mode:
                commit_message = repo_info.get('commit_message', f"Rotate paired secrets: {identifier}")
            else:
                commit_message = repo_info.get('commit_message', f"Rotate AWS key: {identifier}")
            repo.git.commit('-m', commit_message)
            status['changes_committed'] = True
            status['commit_hash'] = repo.head.commit.hexsha

            # Push if requested
            if push:
                push_success, push_error = push_branch(
                    repo, branch_name, push_remote, force_push, skip_if_exists, verbose
                )
                status['pushed'] = push_success
                status['push_attempted'] = True
                if push_success:
                    status['push_timestamp'] = datetime.now().isoformat()
                    status['push_error'] = None
                else:
                    status['push_error'] = push_error
                    if verbose:
                        print(f"  Push failed: {push_error}", file=sys.stderr)
            else:
                status['pushed'] = False
                status['push_attempted'] = False

        status['status'] = 'completed'

    except Exception as e:
        status['status'] = 'failed'
        status['error'] = str(e)
        if verbose:
            print(f"  Error processing repository: {e}", file=sys.stderr)

    return status


def save_state(state: Dict, state_file: Path) -> None:
    """Save rotation state to file."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
    state_file.chmod(0o600)


def load_state(state_file: Path) -> Dict:
    """Load rotation state from file."""
    with open(state_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def push_branch(repo: Repo, branch_name: str, remote: str = 'origin',
                force: bool = False, skip_if_exists: bool = True,
                verbose: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Push branch to remote repository.
    Returns: (success, error_message)
    """
    try:
        # Check if branch exists on remote (if skip_if_exists is True)
        if skip_if_exists:
            try:
                remote_refs = repo.git.ls_remote('--heads', remote, branch_name)
                if remote_refs.strip():
                    if verbose:
                        print(f"  Branch {branch_name} already exists on {remote}, skipping push", file=sys.stderr)
                    return True, None  # Already exists, consider it success
            except Exception:
                # If ls_remote fails, continue with push attempt
                pass

        # Push branch
        if force:
            repo.git.push(remote, branch_name, force=True)
        else:
            repo.git.push(remote, branch_name)

        return True, None
    except GitCommandError as e:
        error_msg = str(e)
        # Check for common error patterns
        if 'permission denied' in error_msg.lower() or 'authentication failed' in error_msg.lower():
            return False, f"Authentication failed: {error_msg}"
        elif 'already exists' in error_msg.lower() or 'non-fast-forward' in error_msg.lower():
            return False, f"Branch already exists on remote (use --force-push to override): {error_msg}"
        else:
            return False, error_msg
    except Exception as e:
        return False, str(e)


def check_gh_cli_available() -> bool:
    """Check if GitHub CLI (gh) is available and authenticated."""
    try:
        # First check if gh command exists
        subprocess.run(['gh', '--version'], capture_output=True, timeout=2, check=True)
        # Then check if authenticated (don't fail if not authenticated, just warn)
        result = subprocess.run(['gh', 'auth', 'status'], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        return False


def check_gh_cli_installed() -> bool:
    """Check if GitHub CLI (gh) is installed (regardless of auth status)."""
    try:
        subprocess.run(['gh', '--version'], capture_output=True, timeout=2, check=True)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        return False


def validate_repository_exists(org: str, repo: str, github_token: Optional[str] = None,
                               use_cli: bool = True, verbose: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate that a repository exists on GitHub.
    Returns: (exists, error_message)
    """
    # Try GitHub CLI first if available
    if use_cli and check_gh_cli_installed():
        try:
            # Use 'gh repo view' to check if repo exists
            result = subprocess.run(
                ['gh', 'repo', 'view', f'{org}/{repo}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return True, None
            else:
                error_msg = result.stderr.strip()
                error_lower = error_msg.lower()
                # Check for authentication issues
                if 'not logged in' in error_lower or 'authentication' in error_lower or 'unauthorized' in error_lower:
                    return False, f"Authentication required. Run 'gh auth login' or provide --github-token"
                elif 'not found' in error_lower or 'could not resolve' in error_lower:
                    return False, f"Repository {org}/{repo} does not exist on GitHub (or you don't have access)"
                return False, error_msg or "Repository check failed"
        except subprocess.TimeoutExpired:
            return False, "Repository check timed out"
        except Exception as e:
            if verbose:
                print(f"  GitHub CLI check failed: {e}, trying API...", file=sys.stderr)
    
    # Fall back to GitHub API
    if GITHUB_API_AVAILABLE:
        token = github_token or os.environ.get('GITHUB_TOKEN')
        if token:
            try:
                g = Github(token)
                github_repo = g.get_repo(f'{org}/{repo}')
                # If we get here, repo exists
                return True, None
            except Exception as e:
                error_msg = str(e)
                if 'not found' in error_msg.lower() or 'could not resolve' in error_msg.lower():
                    return False, f"Repository {org}/{repo} does not exist on GitHub"
                return False, error_msg
        else:
            return False, "GitHub token required for API validation. Set GITHUB_TOKEN or use --github-token"
    
    # Neither CLI nor API available
    return False, "Neither GitHub CLI nor PyGithub available for validation"


def validate_repositories(repo_list: List[Dict], github_token: Optional[str] = None,
                           use_cli: bool = True, verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Validate that all repositories in the list exist on GitHub.
    Returns: (all_valid, list_of_invalid_repos_with_errors)
    """
    invalid_repos = []
    
    for repo_info in repo_list:
        org = repo_info['organization']
        repo_name = repo_info['repository_name']
        full_name = f"{org}/{repo_name}"
        
        exists, error = validate_repository_exists(org, repo_name, github_token, use_cli, verbose)
        if not exists:
            invalid_repos.append(f"{full_name}: {error}")
    
    return len(invalid_repos) == 0, invalid_repos


def create_pr_via_cli(org: str, repo: str, branch: str, base: str, title: str,
                     body: str, labels: List[str] = None, reviewers: List[str] = None,
                     assignees: List[str] = None, draft: bool = False,
                     verbose: bool = False) -> Tuple[bool, Optional[Dict]]:
    """
    Create pull request using GitHub CLI.
    Returns: (success, pr_info_dict with 'url' and 'number' keys)
    """
    try:
        cmd = ['gh', 'pr', 'create', '--repo', f'{org}/{repo}', '--head', branch,
               '--base', base, '--title', title, '--body', body]

        if draft:
            cmd.append('--draft')
        if labels:
            cmd.extend(['--label', ','.join(labels)])
        if reviewers:
            cmd.extend(['--reviewer', ','.join(reviewers)])
        if assignees:
            cmd.extend(['--assignee', ','.join(assignees)])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            # Check if PR already exists
            if 'already exists' in error_msg.lower() or 'already has a pull request' in error_msg.lower():
                if verbose:
                    print(f"  PR already exists for {branch}, attempting to find it...", file=sys.stderr)
                # Try to find existing PR
                find_cmd = ['gh', 'pr', 'list', '--repo', f'{org}/{repo}', '--head', f'{org}:{branch}', '--json', 'number,url']
                find_result = subprocess.run(find_cmd, capture_output=True, text=True, timeout=10)
                if find_result.returncode == 0:
                    prs = json.loads(find_result.stdout)
                    if prs:
                        pr = prs[0]
                        return True, {'url': pr['url'], 'number': pr['number']}
            # Check for authentication errors
            if 'not logged in' in error_msg.lower() or 'authentication' in error_msg.lower() or 'unauthorized' in error_msg.lower():
                return False, f"GitHub CLI authentication failed: {error_msg}"
            return False, error_msg

        # Parse PR URL from output
        output = result.stdout.strip()
        # gh CLI outputs the PR URL
        pr_url = output
        # Extract PR number from URL
        pr_number_match = re.search(r'/pull/(\d+)', pr_url)
        pr_number = int(pr_number_match.group(1)) if pr_number_match else None

        return True, {'url': pr_url, 'number': pr_number}
    except subprocess.TimeoutExpired:
        return False, "Timeout while creating PR"
    except Exception as e:
        return False, str(e)


def create_pr_via_api(org: str, repo: str, branch: str, base: str, title: str,
                     body: str, labels: List[str] = None, reviewers: List[str] = None,
                     assignees: List[str] = None, draft: bool = False,
                     github_token: Optional[str] = None,
                     verbose: bool = False) -> Tuple[bool, Optional[Dict]]:
    """
    Create pull request using GitHub API.
    Returns: (success, pr_info_dict with 'url' and 'number' keys)
    """
    if not GITHUB_API_AVAILABLE:
        return False, "PyGithub not available. Install with: make install-deps (or: pip install PyGithub)"

    token = github_token or os.environ.get('GITHUB_TOKEN')
    if not token:
        return False, "GitHub token required. Set GITHUB_TOKEN environment variable or use --github-token"

    try:
        g = Github(token)
        github_repo = g.get_repo(f'{org}/{repo}')

        # Check if PR already exists
        existing_prs = github_repo.get_pulls(state='open', head=f'{org}:{branch}')
        for pr in existing_prs:
            if pr.head.ref == branch:
                if verbose:
                    print(f"  PR already exists: {pr.html_url}", file=sys.stderr)
                return True, {'url': pr.html_url, 'number': pr.number}

        # Create PR
        pr = github_repo.create_pull(
            title=title,
            body=body,
            head=branch,
            base=base,
            draft=draft
        )

        # Add labels
        if labels:
            pr.add_to_labels(*labels)

        # Request reviewers
        if reviewers:
            pr.create_review_request(reviewers=reviewers)

        # Add assignees
        if assignees:
            pr.add_to_assignees(*assignees)

        return True, {'url': pr.html_url, 'number': pr.number}
    except Exception as e:
        error_msg = str(e)
        if 'already exists' in error_msg.lower() or '422' in error_msg:
            # Try to find existing PR
            try:
                g = Github(token)
                github_repo = g.get_repo(f'{org}/{repo}')
                existing_prs = github_repo.get_pulls(state='open', head=f'{org}:{branch}')
                for pr in existing_prs:
                    if pr.head.ref == branch:
                        return True, {'url': pr.html_url, 'number': pr.number}
            except Exception:
                pass
        return False, error_msg


def load_credentials_from_script(loader_path: str, quiet: bool = False) -> Optional[Dict[str, Optional[str]]]:
    """
    Load credentials from pluggable loader script.
    
    Loader scripts should be Python modules that define a load_credentials() function
    that returns a dictionary with 'new_aws_key' and 'new_aws_secret_key' keys.
    
    Args:
        loader_path: Path to loader script (Python module)
        quiet: If True, suppress error messages
    
    Returns:
        Dictionary with credentials or None if failed
        Dictionary format: {'new_aws_key': Optional[str], 'new_aws_secret_key': Optional[str]}
    """
    loader_path_obj = Path(loader_path)
    
    if not loader_path_obj.exists():
        if not quiet:
            print(f"WARNING: Credential loader not found: {loader_path_obj}", file=sys.stderr)
        return None
    
    try:
        # Import as Python module
        import importlib.util
        spec = importlib.util.spec_from_file_location("credential_loader", loader_path_obj)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'load_credentials'):
                credentials = module.load_credentials()
                # Validate return type
                if isinstance(credentials, dict):
                    return credentials
                else:
                    if not quiet:
                        print(f"WARNING: Credential loader returned invalid type (expected dict): {type(credentials)}", file=sys.stderr)
                    return None
            else:
                if not quiet:
                    print(f"WARNING: Credential loader does not define load_credentials() function: {loader_path_obj}", file=sys.stderr)
                return None
        else:
            if not quiet:
                print(f"WARNING: Failed to load credential loader as Python module: {loader_path_obj}", file=sys.stderr)
            return None
    
    except Exception as e:
        if not quiet:
            print(f"WARNING: Failed to load credentials from {loader_path_obj}: {e}", file=sys.stderr)
        return None


def create_pull_request(org: str, repo: str, branch: str, base: str, title: str,
                       body: str, labels: List[str] = None, reviewers: List[str] = None,
                       assignees: List[str] = None, draft: bool = False,
                       use_cli: bool = True, github_token: Optional[str] = None,
                       verbose: bool = False) -> Tuple[bool, Optional[Dict]]:
    """
    Create pull request using GitHub CLI or API.
    Returns: (success, pr_info_dict with 'url' and 'number' keys)
    """
    # Prefer GitHub CLI if available and requested
    if use_cli and check_gh_cli_installed():
        # Try CLI first (even if not authenticated, it will give a better error)
        result = create_pr_via_cli(org, repo, branch, base, title, body, labels,
                                  reviewers, assignees, draft, verbose)
        # If CLI fails due to auth issues, try API if available
        if not result[0]:
            error_msg = str(result[1]).lower() if result[1] else ''
            if 'not logged in' in error_msg or 'authentication' in error_msg or 'unauthorized' in error_msg or 'login' in error_msg:
                if verbose:
                    print(f"  GitHub CLI authentication issue, trying API...", file=sys.stderr)
                if GITHUB_API_AVAILABLE or github_token or os.environ.get('GITHUB_TOKEN'):
                    return create_pr_via_api(org, repo, branch, base, title, body, labels,
                                            reviewers, assignees, draft, github_token, verbose)
                else:
                    return False, f"GitHub CLI authentication failed: {result[1]}. Run 'gh auth login' or install PyGithub: make install-deps"
        return result

    # Fall back to API if CLI not installed or explicitly requested
    if not use_cli or not check_gh_cli_installed():
        return create_pr_via_api(org, repo, branch, base, title, body, labels,
                                reviewers, assignees, draft, github_token, verbose)

    # Should not reach here
    return False, "Neither GitHub CLI nor PyGithub available. Install with: make install-deps"


def main():
    parser = argparse.ArgumentParser(
        description='Rotate AWS keys found in trufflehog analysis reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  # Using default credential loader (reads from ~/.secure/trufflehog-aws-keys.sh)
  # First create credentials file using helper script:
  #   ./create-trufflehog-aws-credentials.sh
  # Then run (loader used automatically):
  %(prog)s -r report.md -i RAW_abc123_def456 --mode dry-run

  # Using interactive prompt
  %(prog)s -r report.md -i RAW_abc123_def456 -p --mode dry-run

  # Paired secret rotation with default loader
  %(prog)s -r report.md -i RAW_abc123_def456 --paired-secret --mode dry-run

  # Resume previous rotation
  %(prog)s --resume -i RAW_abc123_def456 --mode commit
'''
    )

    parser.add_argument('-r', '--report', required=False, help='Path to trufflehog-analyze-results.py markdown report (not required for --resume with --push or --create-pr)')
    parser.add_argument('-i', '--identifier', required=True, help='Identifier to rotate (TOKEN_* or RAW_*)')
    parser.add_argument('-k', '--new-key', help='New AWS key value (or use -p for prompt)')
    parser.add_argument('-l', '--limit', type=int, default=0, help='Limit number of repositories to process (Default: 0 = all)')
    parser.add_argument('-p', '--prompt-key', action='store_true', help='Prompt for new key interactively (masked input)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode. Output as little as possible.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output (may contain sensitive data)')
    parser.add_argument('--debug', action='store_true', help='Debug mode: show replacement values and wait for confirmation before proceeding')

    # Paired secret rotation options
    parser.add_argument('--paired-secret', action='store_true', help='Enable paired secret rotation (rotates both primary and paired secrets together)')
    parser.add_argument('--prompt-paired-secret', action='store_true', help='Prompt for new paired secret interactively (masked input)')
    parser.add_argument('--paired-secret-identifier', help='Paired secret identifier (TOKEN_* or RAW_*) for explicit mode (optional - automatic discovery will be attempted if not provided)')

    parser.add_argument('--lookup-table', help='Path to secrets lookup table (required for TOKEN_ identifiers)')
    parser.add_argument('--mode', choices=['dry-run', 'commit'], default='dry-run', help='Operation mode (Default: dry-run)')
    parser.add_argument('--resume', action='store_true', help='Resume a previous rotation operation')
    parser.add_argument('--state-file', help='Path to state file for resume functionality')
    parser.add_argument('--branch-prefix', default='rotate-aws-key', help='Prefix for branch names (Default: rotate-aws-key)')
    parser.add_argument('--commit-message', help='Custom commit message')
    parser.add_argument('--skip-repos', help='Comma-separated list of repository names to skip')
    parser.add_argument('--only-repos', help='Comma-separated list of repository names to process')
    # Generate default work directory with timestamp to avoid conflicts
    default_work_dir = f'/tmp/trufflehog-rotate-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    parser.add_argument('--work-dir', default=default_work_dir, help='Working directory for cloning repositories (default: /tmp/trufflehog-rotate-YYYYMMDD-HHMMSS)')
    parser.add_argument('--reuse-clones', action='store_true', help='Reuse existing clones if found')
    parser.add_argument('--backup-dir', help='Directory to store backup copies of modified files')

    # Push options
    parser.add_argument('--push', action='store_true', help='Push commits to remote (requires --mode commit or --resume)')
    parser.add_argument('--force-push', action='store_true', help='Force push if branch exists on remote (dangerous!)')
    parser.add_argument('--push-remote', default='origin', help='Remote name to push to (default: origin)')
    parser.add_argument('--skip-if-exists', action='store_true', default=True, help='Skip push if branch already exists on remote (default: True)')

    # PR options
    parser.add_argument('--create-pr', action='store_true', help='Create pull request after pushing (requires --push or already pushed)')
    parser.add_argument('--draft-pr', action='store_true', help='Create draft PRs (requires --create-pr)')
    parser.add_argument('--pr-title', help='PR title template (supports {identifier}, {repo}, {branch})')
    parser.add_argument('--pr-body', help='PR body template file (or use default)')
    parser.add_argument('--pr-labels', help='Comma-separated labels (e.g., "security,automated")')
    parser.add_argument('--pr-reviewers', help='Comma-separated GitHub usernames for review')
    parser.add_argument('--pr-assignees', help='Comma-separated GitHub usernames to assign')
    parser.add_argument('--pr-base-branch', help='Base branch for PR (default: from state file or main)')
    parser.add_argument('--skip-pr', help='Comma-separated list of repository names to skip PR creation')

    # GitHub authentication
    parser.add_argument('--github-token', help='GitHub token for API (alternative to gh CLI)')
    parser.add_argument('--use-gh-cli', action='store_true', help='Use GitHub CLI (gh) for PR creation (default if available)')
    parser.add_argument('--use-github-api', action='store_true', help='Use GitHub API directly (requires token)')

    # Credential loader (pluggable)
    script_dir = Path(__file__).parent
    default_loader = script_dir / 'credential-loaders' / 'file_loader.py'
    parser.add_argument('--credential-loader', help=f'Path to credential loader script (Python module with load_credentials() function). Default: {default_loader} if exists. Can also be set via TRUFFLEHOG_CREDENTIAL_LOADER env var.')

    args = parser.parse_args()

    # Setup secure directories
    secure_dir, trufflehog_rotate_dir, default_backup_dir = setup_secure_directories()
    backup_dir = Path(args.backup_dir) if args.backup_dir else default_backup_dir

    # Setup logging to working directory (will be set up in resume mode or initial run)
    log_file: Optional[Path] = None
    tee_output: Optional[TeeOutput] = None

    # Resume mode (check before requiring new key, since resume may not need it)
    if args.resume:
        if args.state_file:
            state_file = Path(args.state_file)
        else:
            # Find most recent state file for identifier
            state_files = sorted(trufflehog_rotate_dir.glob(f"{args.identifier}-*.json"), reverse=True)
            if not state_files:
                print(f"ERROR: No state file found for identifier: {args.identifier}", file=sys.stderr)
                sys.exit(1)
            state_file = state_files[0]

        # Load state to get work_dir for logging
        state = load_state(state_file)
        work_dir_for_log = Path(state.get('work_dir', args.work_dir))
        work_dir_for_log.mkdir(parents=True, exist_ok=True)
        log_file = work_dir_for_log / f"trufflehog-rotate-resume-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
        tee_output = TeeOutput(log_file, args.quiet)
        tee_output.__enter__()
        sys.stderr = tee_output

        if not args.quiet:
            print(f"Resuming from state file: {state_file}", file=sys.stderr)
            print(f"Log file: {log_file}", file=sys.stderr)

        # Validate mode compatibility
        state_paired_mode = state.get('paired_secret_mode', False)
        if state_paired_mode and not args.paired_secret:
            print("ERROR: State file is for paired-secret mode, but --paired-secret flag not provided.", file=sys.stderr)
            print("Resume with: --resume --paired-secret", file=sys.stderr)
            sys.exit(1)
        if not state_paired_mode and args.paired_secret:
            print("ERROR: State file is for single-secret mode, but --paired-secret flag provided.", file=sys.stderr)
            print("Resume without --paired-secret flag, or use a different state file.", file=sys.stderr)
            sys.exit(1)

        # Get new key (optional in resume mode - only for verification)
        # In resume mode, the key was already used to modify files, so we don't strictly need it
        # But we can verify it matches if provided
        new_key = None
        if args.prompt_key:
            new_key = getpass.getpass("Enter new AWS key (input will be hidden): ")
        elif args.new_key:
            new_key = args.new_key
        else:
            new_key = os.environ.get('TRUFFLEHOG_NEW_AWS_KEY')
            # In resume mode, key is optional - only warn if provided and doesn't match

        # Verify key hash matches (only if we have a key - optional in resume mode)
        if new_key:
            new_key_hash = hashlib.sha256(new_key.encode()).hexdigest()
            if state.get('new_key_hash') != f'sha256:{new_key_hash}':
                print("WARNING: New key hash does not match state file. Continuing anyway...", file=sys.stderr)
        # Note: In resume mode, we don't require the key - files were already modified in initial run

        # Handle paired secret in resume mode
        new_paired_secret = None
        if state_paired_mode:
            if args.prompt_paired_secret:
                new_paired_secret = getpass.getpass("Enter new paired secret (input will be hidden): ")
            elif args.new_paired_secret:
                new_paired_secret = args.new_paired_secret
            else:
                secret_type = state.get('secret_type', 'aws')
                if secret_type == 'aws':
                    new_paired_secret = os.environ.get('TRUFFLEHOG_NEW_AWS_SECRET_KEY')

            # Verify paired secret hash if provided
            if new_paired_secret:
                new_paired_secret_hash = hashlib.sha256(new_paired_secret.encode()).hexdigest()
                if state.get('new_paired_secret_hash') != f'sha256:{new_paired_secret_hash}':
                    print("WARNING: New paired secret hash does not match state file. Continuing anyway...", file=sys.stderr)

        # Determine what operations to perform
        do_commit = args.mode == 'commit'
        do_push = args.push
        do_create_pr = args.create_pr

        # Process pending repositories based on operation
        if do_commit:
            # Resume commit mode: find repos that need committing
            pending_repos = [r for r in state['repositories'] if r['status'] in ('pending', 'completed') and not r.get('changes_committed', False)]
            if not args.quiet:
                print(f"Found {len(pending_repos)} repositories with pending changes", file=sys.stderr)
        elif do_push:
            # Resume push mode: find repos that need pushing
            pending_repos = [r for r in state['repositories'] if r.get('changes_committed', False) and not r.get('pushed', False)]
            if not args.quiet:
                print(f"Found {len(pending_repos)} repositories with committed changes to push", file=sys.stderr)
        elif do_create_pr:
            # Resume PR mode: find repos that need PRs
            pending_repos = [r for r in state['repositories'] if r.get('pushed', False) and not r.get('pr_created', False)]
            if not args.quiet:
                print(f"Found {len(pending_repos)} repositories with pushed branches to create PRs for", file=sys.stderr)
        else:
            # Default: commit mode
            pending_repos = [r for r in state['repositories'] if r['status'] in ('pending', 'completed') and not r.get('changes_committed', False)]
            if not args.quiet:
                print(f"Found {len(pending_repos)} repositories with pending changes", file=sys.stderr)

        # Apply limit
        if args.limit > 0:
            pending_repos = pending_repos[:args.limit]

        # Apply skip filters
        skip_repos = set((args.skip_repos or '').split(',')) if args.skip_repos else set()
        skip_pr_repos = set((args.skip_pr or '').split(',')) if args.skip_pr else set()

        work_dir = Path(state['work_dir'])
        # old_key is no longer stored in state file (replaced with old_key_hash for security)
        # Resume mode doesn't need old_key since it only commits existing changes

        for i, repo_status in enumerate(pending_repos, 1):
            org = repo_status.get('organization', 'unknown')
            repo_name = repo_status.get('repository_name', 'unknown')
            if not args.quiet:
                print(f"\n[{i}/{len(pending_repos)}] Processing {org}/{repo_name}...", file=sys.stderr)

            # Skip if in skip list
            if repo_name in skip_repos:
                if not args.quiet:
                    print(f"  Skipping {repo_name} (in --skip-repos)", file=sys.stderr)
                continue

            local_path = Path(repo_status['local_clone_path'])
            if not local_path.exists():
                repo_status['status'] = 'failed'
                repo_status['error'] = 'Local clone path does not exist'
                continue

            try:
                repo = Repo(str(local_path))
                branch_name = repo_status.get('branch_name')

                # Handle commit operation
                if do_commit:
                    if branch_name:
                        try:
                            repo.git.checkout(branch_name)
                        except GitCommandError:
                            repo_status['status'] = 'failed'
                            repo_status['error'] = 'Branch does not exist'
                            continue

                    # Check if there are uncommitted changes
                    if repo.is_dirty() or len(list(repo.index.diff('HEAD'))) > 0:
                        commit_message = args.commit_message or f"Rotate AWS key: {state['identifier']}"
                        repo.git.add('-A')
                        repo.git.commit('-m', commit_message)
                        repo_status['changes_committed'] = True
                        repo_status['commit_hash'] = repo.head.commit.hexsha
                        repo_status['status'] = 'completed'
                    else:
                        repo_status['status'] = 'completed'
                        if not args.quiet:
                            print(f"  No uncommitted changes found", file=sys.stderr)

                # Handle push operation
                if do_push and repo_status.get('changes_committed', False) and not repo_status.get('pushed', False):
                    if not branch_name:
                        repo_status['push_error'] = 'No branch name found'
                        repo_status['push_attempted'] = True
                        continue

                    try:
                        repo.git.checkout(branch_name)
                    except GitCommandError:
                        repo_status['push_error'] = 'Branch does not exist'
                        repo_status['push_attempted'] = True
                        continue

                    push_success, push_error = push_branch(
                        repo, branch_name, args.push_remote, args.force_push,
                        args.skip_if_exists, args.verbose
                    )
                    repo_status['pushed'] = push_success
                    repo_status['push_attempted'] = True
                    if push_success:
                        repo_status['push_timestamp'] = datetime.now().isoformat()
                        repo_status['push_error'] = None
                        if not args.quiet:
                            print(f"  ✓ Pushed branch {branch_name}", file=sys.stderr)
                    else:
                        repo_status['push_error'] = push_error
                        if not args.quiet:
                            print(f"  ✗ Push failed: {push_error}", file=sys.stderr)

                # Handle PR creation operation
                if do_create_pr and repo_status.get('pushed', False) and not repo_status.get('pr_created', False):
                    if repo_name in skip_pr_repos:
                        if not args.quiet:
                            print(f"  Skipping PR creation for {repo_name} (in --skip-pr)", file=sys.stderr)
                        continue

                    if not branch_name:
                        repo_status['pr_error'] = 'No branch name found'
                        repo_status['pr_attempted'] = True
                        continue

                    base_branch = args.pr_base_branch or repo_status.get('base_branch', 'main')
                    identifier = state['identifier']

                    # Generate PR title
                    if args.pr_title:
                        pr_title = args.pr_title.format(identifier=identifier, repo=repo_name, branch=branch_name)
                    else:
                        pr_title = f"Rotate AWS key: {identifier}"

                    # Generate PR body
                    if args.pr_body and Path(args.pr_body).exists():
                        with open(args.pr_body, 'r') as f:
                            pr_body = f.read().format(identifier=identifier, repo=repo_name, branch=branch_name)
                    else:
                        pr_body = f"""Rotate AWS key: {identifier}

This PR rotates the AWS key found in this repository.

**Branch:** {branch_name}
**Identifier:** {identifier}
**Files Modified:** {', '.join(repo_status.get('files_modified', []))}

Please review and merge when ready.
"""

                    # Parse labels, reviewers, assignees
                    labels = [l.strip() for l in (args.pr_labels or '').split(',') if l.strip()]
                    reviewers = [r.strip() for r in (args.pr_reviewers or '').split(',') if r.strip()]
                    assignees = [a.strip() for a in (args.pr_assignees or '').split(',') if a.strip()]

                    # Determine which method to use
                    # Prefer CLI if installed (even if not authenticated, will try and give better error)
                    use_cli = args.use_gh_cli or (not args.use_github_api and check_gh_cli_installed())

                    pr_success, pr_result = create_pull_request(
                        org, repo_name, branch_name, base_branch, pr_title, pr_body,
                        labels, reviewers, assignees, args.draft_pr,
                        use_cli, args.github_token, args.verbose
                    )

                    repo_status['pr_attempted'] = True
                    if pr_success and pr_result:
                        repo_status['pr_created'] = True
                        repo_status['pr_url'] = pr_result.get('url')
                        repo_status['pr_number'] = pr_result.get('number')
                        repo_status['pr_timestamp'] = datetime.now().isoformat()
                        repo_status['pr_error'] = None
                        if not args.quiet:
                            print(f"  ✓ Created PR: {pr_result.get('url')}", file=sys.stderr)
                    else:
                        repo_status['pr_error'] = pr_result if isinstance(pr_result, str) else 'Unknown error'
                        if not args.quiet:
                            print(f"  ✗ PR creation failed: {repo_status['pr_error']}", file=sys.stderr)

            except Exception as e:
                if do_commit:
                    repo_status['status'] = 'failed'
                    repo_status['error'] = str(e)
                elif do_push:
                    repo_status['push_error'] = str(e)
                    repo_status['push_attempted'] = True
                elif do_create_pr:
                    repo_status['pr_error'] = str(e)
                    repo_status['pr_attempted'] = True
                if args.verbose:
                    print(f"  Error: {e}", file=sys.stderr)

        # Update state file
        state['mode'] = args.mode
        save_state(state, state_file)

        if not args.quiet:
            if do_commit:
                completed = sum(1 for r in state['repositories'] if r.get('changes_committed', False))
                print(f"\nCompleted: {completed} repositories committed", file=sys.stderr)
                # Show next step if not already pushing
                if not do_push:
                    pushed_count = sum(1 for r in state['repositories'] if r.get('pushed', False))
                    if pushed_count == 0:
                        print("\nTo push commits, run:", file=sys.stderr)
                        print(f"  ./trufflehog/trufflehog-rotate-aws-key.py --resume -i {state['identifier']} --push", file=sys.stderr)
            if do_push:
                pushed = sum(1 for r in state['repositories'] if r.get('pushed', False))
                print(f"Pushed: {pushed} repositories", file=sys.stderr)
                # Show next step if not already creating PRs
                if not do_create_pr:
                    pr_count = sum(1 for r in state['repositories'] if r.get('pr_created', False))
                    if pr_count == 0 and pushed > 0:
                        print("\nTo create pull requests, run:", file=sys.stderr)
                        print(f"  ./trufflehog/trufflehog-rotate-aws-key.py --resume -i {state['identifier']} --create-pr", file=sys.stderr)
            if do_create_pr:
                prs_created = sum(1 for r in state['repositories'] if r.get('pr_created', False))
                print(f"PRs created: {prs_created} repositories", file=sys.stderr)
            print(f"State updated: {state_file}", file=sys.stderr)
            if log_file:
                print(f"Log file: {log_file}", file=sys.stderr)

        # Cleanup logging
        if tee_output:
            tee_output.__exit__(None, None, None)

        sys.exit(0)

    # Validate prerequisites BEFORE prompting for sensitive input (keys)
    # This prevents prompting for secrets when the script will fail due to missing files/invalid identifiers
    # BUG-1: Fixed validation order - validate report file and identifier before prompting for key

    # Parse report (required for initial run, not for resume with push/PR only)
    if not args.report and not args.resume:
        print("ERROR: Report file required for initial run. Use -r/--report", file=sys.stderr)
        sys.exit(1)

    if not args.report:
        # Resume mode with push/PR only - no report needed
        sys.exit(0)

    report_path = Path(args.report)
    if not report_path.exists():
        print(f"ERROR: Report file not found: {report_path}", file=sys.stderr)
        sys.exit(1)

    if not args.quiet:
        print(f"Parsing report: {report_path}", file=sys.stderr)

    identifiers = parse_report(report_path)

    if args.identifier not in identifiers:
        print(f"ERROR: Identifier not found in report: {args.identifier}", file=sys.stderr)
        print(f"Available identifiers: {', '.join(identifiers.keys())}", file=sys.stderr)
        sys.exit(1)

    # Now that prerequisites are validated, load credentials using priority order:
    # 1. CLI argument (-k / --new-key)
    # 2. Interactive prompt (-p / --prompt-key)
    # 3. Credential loader script (--credential-loader)
    # 4. Environment variable (TRUFFLEHOG_NEW_AWS_KEY)
    # 5. Automatic prompt (if none of above)
    
    # Determine credential loader script path
    loader_script = None
    if args.credential_loader:
        loader_script = Path(args.credential_loader)
    elif os.environ.get('TRUFFLEHOG_CREDENTIAL_LOADER'):
        loader_script = Path(os.environ.get('TRUFFLEHOG_CREDENTIAL_LOADER'))
    else:
        # Default: try file_loader.py if it exists
        script_dir = Path(__file__).parent
        default_loader = script_dir / 'credential-loaders' / 'file_loader.py'
        if default_loader.exists():
            loader_script = default_loader
    
    # Load credentials from loader script (if available)
    loader_credentials = None
    if loader_script:
        loader_credentials = load_credentials_from_script(str(loader_script), args.quiet)
    
    # Priority 1: CLI argument (-k / --new-key)
    if args.new_key:
        # CLI args are insecure (visible in shell history and process lists)
        # But allow for backward compatibility - warn user
        print("WARNING: Passing secrets via CLI arguments is insecure (visible in shell history and process lists).", file=sys.stderr)
        print("WARNING: Consider using -p (prompt) or credential loaders instead.", file=sys.stderr)
        new_key = args.new_key
    # Priority 2: Interactive prompt (-p / --prompt-key)
    elif args.prompt_key:
        new_key = getpass.getpass("Enter new AWS key (input will be hidden): ")
    # Priority 3: Credential loader (--credential-loader) (NEW)
    elif loader_credentials and loader_credentials.get('new_aws_key'):
        new_key = loader_credentials['new_aws_key']
        if not args.quiet:
            print("INFO: Loaded new AWS key from credential loader", file=sys.stderr)
    # Priority 4: Environment variable (TRUFFLEHOG_NEW_AWS_KEY)
    else:
        new_key = os.environ.get('TRUFFLEHOG_NEW_AWS_KEY')
        if not new_key and not args.resume:
            # Priority 5: Automatically prompt if no key provided (most secure default)
            new_key = getpass.getpass("Enter new AWS key (input will be hidden): ")

    if not new_key and not args.resume:
        print("ERROR: New key cannot be empty", file=sys.stderr)
        sys.exit(1)

    identifier_data = identifiers[args.identifier]

    # Detect secret type from identifier data
    secret_type = identifier_data.get('secret_type', 'aws')

    # Get old key
    if args.identifier.startswith('RAW_'):
        old_key = identifier_data['secret_value']
        if not old_key:
            print(f"ERROR: Could not extract secret value for RAW_ identifier", file=sys.stderr)
            sys.exit(1)
    elif args.identifier.startswith('TOKEN_'):
        if not args.lookup_table:
            print(f"ERROR: Lookup table required for TOKEN_ identifier. Use --lookup-table", file=sys.stderr)
            sys.exit(1)
        # Load lookup table and get secret
        with open(args.lookup_table, 'r') as f:
            lookup = json.load(f)
        if args.identifier not in lookup:
            print(f"ERROR: Identifier not found in lookup table: {args.identifier}", file=sys.stderr)
            sys.exit(1)
        old_key = lookup[args.identifier]
    else:
        print(f"ERROR: Unknown identifier format: {args.identifier}", file=sys.stderr)
        sys.exit(1)

    # Handle paired secret mode
    paired_secret_mode = args.paired_secret
    old_paired_secret = None
    new_paired_secret = None
    paired_secret_identifier = None
    secret_discovery_method = None

    if paired_secret_mode:
        # Get paired secret identifier (explicit mode)
        if args.paired_secret_identifier:
            paired_secret_identifier = args.paired_secret_identifier
            if paired_secret_identifier not in identifiers:
                print(f"ERROR: Paired secret identifier not found in report: {paired_secret_identifier}", file=sys.stderr)
                print(f"Available identifiers: {', '.join(identifiers.keys())}", file=sys.stderr)
                sys.exit(1)

            paired_identifier_data = identifiers[paired_secret_identifier]
            secret_discovery_method = 'explicit'

            # Get old paired secret
            if paired_secret_identifier.startswith('RAW_'):
                old_paired_secret = paired_identifier_data['secret_value']
                if not old_paired_secret:
                    print(f"ERROR: Could not extract secret value for paired RAW_ identifier", file=sys.stderr)
                    sys.exit(1)
            elif paired_secret_identifier.startswith('TOKEN_'):
                if not args.lookup_table:
                    print(f"ERROR: Lookup table required for paired TOKEN_ identifier. Use --lookup-table", file=sys.stderr)
                    sys.exit(1)
                if paired_secret_identifier not in lookup:
                    print(f"ERROR: Paired identifier not found in lookup table: {paired_secret_identifier}", file=sys.stderr)
                    sys.exit(1)
                old_paired_secret = lookup[paired_secret_identifier]
            else:
                print(f"ERROR: Unknown paired identifier format: {paired_secret_identifier}", file=sys.stderr)
                sys.exit(1)
        else:
            # Explicit mode: require old paired secret from credential loader, environment variable, or prompt
            # Automatic discovery is disabled due to fragility - see find_paired_secret_near_primary()
            if secret_type == 'aws':
                # Priority 1: Credential loader (NEW)
                if loader_credentials and loader_credentials.get('old_aws_secret_key'):
                    old_paired_secret = loader_credentials['old_aws_secret_key']
                    secret_discovery_method = 'explicit_loader'
                    if not args.quiet:
                        print("INFO: Using old paired secret from credential loader", file=sys.stderr)
                # Priority 2: Environment variable
                elif os.environ.get('TRUFFLEHOG_OLD_AWS_SECRET_KEY'):
                    old_paired_secret = os.environ.get('TRUFFLEHOG_OLD_AWS_SECRET_KEY')
                    secret_discovery_method = 'explicit_env'
                    if not args.quiet:
                        print("INFO: Using old paired secret from TRUFFLEHOG_OLD_AWS_SECRET_KEY environment variable", file=sys.stderr)
                else:
                    # Will prompt user during processing if not provided
                    secret_discovery_method = 'explicit_prompt'
            else:
                secret_discovery_method = 'explicit_prompt'
            paired_secret_identifier = None

        # Get new paired secret using priority order:
        # 1. Interactive prompt (--prompt-paired-secret)
        # 2. Credential loader script (--credential-loader) (NEW)
        # 3. Environment variable (TRUFFLEHOG_NEW_AWS_SECRET_KEY)
        # 4. Automatic prompt (if none of above)
        if args.prompt_paired_secret:
            new_paired_secret = getpass.getpass("Enter new paired secret (input will be hidden): ")
        # Priority 2: Credential loader (NEW)
        elif loader_credentials and loader_credentials.get('new_aws_secret_key'):
            new_paired_secret = loader_credentials['new_aws_secret_key']
            if not args.quiet:
                print("INFO: Loaded new paired secret from credential loader", file=sys.stderr)
        # Priority 3: Environment variable
        else:
            # Try environment variable (AWS-specific for now)
            # Note: Environment variables are still visible in process lists, but safer than CLI args
            if secret_type == 'aws':
                new_paired_secret = os.environ.get('TRUFFLEHOG_NEW_AWS_SECRET_KEY')
            if not new_paired_secret:
                # Priority 4: Automatically prompt if not provided (most secure default)
                new_paired_secret = getpass.getpass("Enter new paired secret (input will be hidden): ")

        if not new_paired_secret:
            print("ERROR: New paired secret cannot be empty", file=sys.stderr)
            sys.exit(1)

        # Note: old_paired_secret will be:
        # 1. From --paired-secret-identifier (explicit mode)
        # 2. From TRUFFLEHOG_OLD_AWS_SECRET_KEY environment variable (explicit mode via env)
        # 3. Discovered per-file during processing (automatic discovery)

    # Get paired secret occurrences if in paired secret mode
    paired_secret_occurrences_data = None
    if paired_secret_mode and paired_secret_identifier:
        if paired_secret_identifier in identifiers:
            paired_secret_occurrences_data = identifiers[paired_secret_identifier]['occurrences']
        else:
            print(f"ERROR: Paired secret identifier not found in report: {paired_secret_identifier}", file=sys.stderr)
            sys.exit(1)

    # Group occurrences by repository
    repos = defaultdict(list)
    for occ in identifier_data['occurrences']:
        repo_key = (occ['repository_url'], occ['repository_name'], occ['organization'])
        repos[repo_key].append(occ)

    # Group paired secret occurrences by repository if in paired secret mode
    paired_repos = defaultdict(list)
    if paired_secret_occurrences_data:
        for occ in paired_secret_occurrences_data:
            repo_key = (occ['repository_url'], occ['repository_name'], occ['organization'])
            paired_repos[repo_key].append(occ)

    # Apply filters
    skip_repos = set(args.skip_repos.split(',')) if args.skip_repos else set()
    only_repos = set(args.only_repos.split(',')) if args.only_repos else set()

    repo_list = []
    for (repo_url, repo_name, org), occs in repos.items():
        if repo_name in skip_repos:
            continue
        if only_repos and repo_name not in only_repos:
            continue

        # Get paired secret occurrences for this repository
        paired_occs = paired_repos.get((repo_url, repo_name, org), []) if paired_secret_mode else None

        repo_list.append({
            'repository_url': repo_url,
            'repository_name': repo_name,
            'organization': org,
            'identifier': args.identifier,
            'occurrences': occs,
            'paired_secret_occurrences': paired_occs
        })

    # Apply limit
    if args.limit > 0:
        repo_list = repo_list[:args.limit]

    # Early validation: Check repository existence if PRs will be created
    # This prevents processing files and pushing branches for non-existent repos
    # Do this BEFORE creating work directories and setting up logging for fast failure
    if args.create_pr:
        # Always validate when PRs will be created
        if not args.quiet:
            print("Validating repository existence on GitHub (required for PR creation)...", file=sys.stderr)
        
        # Check authentication status
        use_cli = args.use_gh_cli or (not args.use_github_api and check_gh_cli_installed())
        has_token = bool(args.github_token or os.environ.get('GITHUB_TOKEN'))
        
        if use_cli and check_gh_cli_installed():
            # Check if gh is authenticated
            try:
                auth_result = subprocess.run(
                    ['gh', 'auth', 'status'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if auth_result.returncode != 0 and not args.quiet:
                    print("WARNING: GitHub CLI may not be authenticated. Run 'gh auth login'", file=sys.stderr)
            except Exception:
                pass  # Ignore auth check failures
        
        if not use_cli and not has_token and not args.quiet:
            print("WARNING: No GitHub authentication found. Private repositories may fail validation.", file=sys.stderr)
            print("  Set GITHUB_TOKEN environment variable or use --github-token", file=sys.stderr)
        
        all_valid, invalid_repos = validate_repositories(
            repo_list, args.github_token, use_cli, args.verbose
        )
        
        if not all_valid:
            print("\nERROR: Some repositories could not be validated on GitHub:", file=sys.stderr)
            for error in invalid_repos:
                print(f"  ✗ {error}", file=sys.stderr)
            print("\nPossible causes:", file=sys.stderr)
            print("  1. Repository names in the report are incorrect", file=sys.stderr)
            print("  2. Repositories are private and authentication is required", file=sys.stderr)
            print("     - Run 'gh auth login' for GitHub CLI", file=sys.stderr)
            print("     - Or set GITHUB_TOKEN environment variable", file=sys.stderr)
            print("     - Or use --github-token flag", file=sys.stderr)
            print("  3. Repositories have been renamed or deleted", file=sys.stderr)
            print("\nYou can skip invalid repositories using --skip-repos <repo1,repo2,...>", file=sys.stderr)
            sys.exit(1)
        
        if not args.quiet:
            print(f"✓ All {len(repo_list)} repositories validated successfully", file=sys.stderr)

    # Process repositories
    work_dir = Path(args.work_dir)
    repos_dir = work_dir / 'repos'

    # Create working directories upfront
    work_dir.mkdir(parents=True, exist_ok=True)
    repos_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging for initial run
    log_file = work_dir / f"trufflehog-rotate-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    tee_output = TeeOutput(log_file, args.quiet)
    tee_output.__enter__()
    sys.stderr = tee_output

    if not args.quiet:
        print(f"Log file: {log_file}", file=sys.stderr)

    if not args.quiet:
        print("─" * 70, file=sys.stderr)
        print("Configuration:", file=sys.stderr)
        print(f"  Working directory: {work_dir}", file=sys.stderr)
        print(f"  Repositories will be cloned to: {repos_dir}", file=sys.stderr)
        print(f"  Backup directory: {backup_dir}", file=sys.stderr)
        print("─" * 70, file=sys.stderr)
        if paired_secret_mode:
            print(f"Processing paired secret rotation for identifier: {args.identifier}", file=sys.stderr)
            print(f"Paired secret identifier: {paired_secret_identifier}", file=sys.stderr)
            print(f"Old primary key: {old_key[:8]}... (hidden)", file=sys.stderr)
            print(f"New primary key: ******** (hidden)", file=sys.stderr)
            print(f"Old paired secret: {old_paired_secret[:8] if old_paired_secret else 'N/A'}... (hidden)", file=sys.stderr)
            print(f"New paired secret: ******** (hidden)", file=sys.stderr)
        else:
            print(f"Processing AWS key rotation for identifier: {args.identifier}", file=sys.stderr)
            print(f"Old key: {old_key[:8]}... (hidden)", file=sys.stderr)
            print(f"New key: ******** (hidden)", file=sys.stderr)
        print(f"Repositories to process: {len(repo_list)}", file=sys.stderr)
        print("─" * 70, file=sys.stderr)
    timestamp = datetime.now().isoformat()

    # Create a shared mutable container for old_paired_secret that persists across repositories
    # This allows us to prompt once and reuse the value for all repositories
    shared_old_paired_secret_ref = [old_paired_secret] if (paired_secret_mode and old_paired_secret) else []

    # Create a shared mutable container for "confirm all" flag that persists across repositories
    # This allows users to say "all" once and skip all future confirmations
    shared_confirm_all_ref = [False]

    repositories_status = []
    for i, repo_info in enumerate(repo_list, 1):
        if not args.quiet:
            print(f"\n[{i}/{len(repo_list)}] Processing {repo_info['organization']}/{repo_info['repository_name']}...", file=sys.stderr)

        # Add commit message to repo_info if provided
        if args.commit_message:
            repo_info['commit_message'] = args.commit_message

        # Use the shared mutable containers
        old_paired_secret_ref = shared_old_paired_secret_ref if paired_secret_mode else None
        confirm_all_ref = shared_confirm_all_ref if args.debug else None

        status = process_repository(
            repo_info, old_key, new_key, work_dir, backup_dir,
            args.branch_prefix, timestamp, args.mode, args.reuse_clones, args.verbose,
            args.push, args.force_push, args.push_remote, args.skip_if_exists,
            paired_secret_mode=paired_secret_mode,
            old_paired_secret=old_paired_secret,
            new_paired_secret=new_paired_secret,
            secret_type=secret_type,
            paired_secret_occurrences=repo_info.get('paired_secret_occurrences'),
            debug=args.debug,
            quiet=args.quiet,
            old_paired_secret_ref=old_paired_secret_ref,
            confirm_all_ref=confirm_all_ref
        )
        repositories_status.append(status)

        if not args.quiet:
            if status['status'] == 'completed':
                print(f"  ✓ Status: {status['status']}", file=sys.stderr)
                print(f"  ✓ Files modified: {len(status['files_modified'])}", file=sys.stderr)
                if status['changes_committed']:
                    print(f"  ✓ Changes committed", file=sys.stderr)
                if status.get('pushed'):
                    print(f"  ✓ Branch pushed", file=sys.stderr)
            else:
                print(f"  ✗ Status: {status['status']}", file=sys.stderr)
                if 'error' in status:
                    print(f"  ✗ Error: {status['error']}", file=sys.stderr)

    # Create PRs if requested (after all repositories are processed)
    if args.create_pr:
        skip_pr_repos = set((args.skip_pr or '').split(',')) if args.skip_pr else set()
        # Prefer CLI if installed (even if not authenticated, will try and give better error)
        use_cli = args.use_gh_cli or (not args.use_github_api and check_gh_cli_installed())

        for repo_status in repositories_status:
            if not repo_status.get('pushed', False) or repo_status.get('pr_created', False):
                continue

            repo_name = repo_status.get('repository_name')
            if repo_name in skip_pr_repos:
                continue

            org = repo_status.get('organization', 'unknown')
            branch_name = repo_status.get('branch_name')
            if not branch_name:
                repo_status['pr_error'] = 'No branch name found'
                repo_status['pr_attempted'] = True
                continue

            base_branch = args.pr_base_branch or repo_status.get('base_branch', 'main')

            # Generate PR title
            if args.pr_title:
                pr_title = args.pr_title.format(identifier=args.identifier, repo=repo_name, branch=branch_name)
            else:
                pr_title = f"Rotate AWS key: {args.identifier}"

            # Generate PR body
            if args.pr_body and Path(args.pr_body).exists():
                with open(args.pr_body, 'r') as f:
                    pr_body = f.read().format(identifier=args.identifier, repo=repo_name, branch=branch_name)
            else:
                pr_body = f"""Rotate AWS key: {args.identifier}

This PR rotates the AWS key found in this repository.

**Branch:** {branch_name}
**Identifier:** {args.identifier}
**Files Modified:** {', '.join(repo_status.get('files_modified', []))}

Please review and merge when ready.
"""

            # Parse labels, reviewers, assignees
            labels = [l.strip() for l in (args.pr_labels or '').split(',') if l.strip()]
            reviewers = [r.strip() for r in (args.pr_reviewers or '').split(',') if r.strip()]
            assignees = [a.strip() for a in (args.pr_assignees or '').split(',') if a.strip()]

            pr_success, pr_result = create_pull_request(
                org, repo_name, branch_name, base_branch, pr_title, pr_body,
                labels, reviewers, assignees, args.draft_pr,
                use_cli, args.github_token, args.verbose
            )

            repo_status['pr_attempted'] = True
            if pr_success and pr_result:
                repo_status['pr_created'] = True
                repo_status['pr_url'] = pr_result.get('url')
                repo_status['pr_number'] = pr_result.get('number')
                repo_status['pr_timestamp'] = datetime.now().isoformat()
                repo_status['pr_error'] = None
                if not args.quiet:
                    print(f"  ✓ Created PR for {org}/{repo_name}: {pr_result.get('url')}", file=sys.stderr)
            else:
                repo_status['pr_error'] = pr_result if isinstance(pr_result, str) else 'Unknown error'
                if not args.quiet:
                    print(f"  ✗ PR creation failed for {org}/{repo_name}: {repo_status['pr_error']}", file=sys.stderr)

    # Create state file
    new_key_hash = hashlib.sha256(new_key.encode()).hexdigest()
    old_key_hash = hashlib.sha256(old_key.encode()).hexdigest()
    state = {
        'identifier': args.identifier,
        'old_key_hash': f'sha256:{old_key_hash}',  # Store hash instead of plain text
        'new_key_hash': f'sha256:{new_key_hash}',
        'timestamp': timestamp,
        'mode': args.mode,
        'report_file': str(report_path),
        'work_dir': str(work_dir),
        'repositories': repositories_status,
        'summary': {
            'total_repositories': len(repo_list),
            'completed': sum(1 for r in repositories_status if r['status'] == 'completed'),
            'pending': sum(1 for r in repositories_status if r['status'] == 'pending'),
            'failed': sum(1 for r in repositories_status if r['status'] == 'failed'),
            'skipped': sum(1 for r in repositories_status if r['status'] == 'skipped')
        }
    }

    # Add paired secret information if in paired secret mode
    if paired_secret_mode:
        new_paired_secret_hash = hashlib.sha256(new_paired_secret.encode()).hexdigest()
        state['paired_secret_mode'] = True
        state['secret_type'] = secret_type
        state['secret_discovery_method'] = secret_discovery_method
        state['new_paired_secret_hash'] = f'sha256:{new_paired_secret_hash}'

        # Store old paired secret hash only if we have it (explicit mode)
        if old_paired_secret:
            old_paired_secret_hash = hashlib.sha256(old_paired_secret.encode()).hexdigest()
            state['old_paired_secret_hash'] = f'sha256:{old_paired_secret_hash}'

        # Store paired secret identifier only if explicit mode
        if paired_secret_identifier:
            state['paired_secret_identifier'] = paired_secret_identifier

    state_file = trufflehog_rotate_dir / f"{args.identifier}-{timestamp.replace(':', '-').replace(' ', '_')}.json"
    save_state(state, state_file)

    if not args.quiet:
        print("\n" + "─" * 70, file=sys.stderr)
        print("Summary:", file=sys.stderr)
        print(f"  Total repositories: {state['summary']['total_repositories']}", file=sys.stderr)
        print(f"  Completed: {state['summary']['completed']}", file=sys.stderr)
        print(f"  Failed: {state['summary']['failed']}", file=sys.stderr)
        print(f"  Skipped: {state['summary']['skipped']}", file=sys.stderr)
        print(f"\nState saved to: {state_file}", file=sys.stderr)
        print("\n" + "─" * 70, file=sys.stderr)
        print("Configuration:", file=sys.stderr)
        print(f"  Working directory: {work_dir}", file=sys.stderr)
        print(f"  Repositories will be cloned to: {repos_dir}", file=sys.stderr)
        print(f"  Backup directory: {backup_dir}", file=sys.stderr)
        print("─" * 70, file=sys.stderr)

        if args.mode == 'dry-run':
            print("\nTo commit changes, run:", file=sys.stderr)
            print(f"  ./trufflehog/trufflehog-rotate-aws-key.py --resume -i {args.identifier} --mode commit", file=sys.stderr)
        elif args.mode == 'commit':
            pushed_count = sum(1 for r in repositories_status if r.get('pushed', False))
            pr_count = sum(1 for r in repositories_status if r.get('pr_created', False))
            if not args.push and pushed_count == 0:
                print("\nTo push commits, run:", file=sys.stderr)
                print(f"  ./trufflehog/trufflehog-rotate-aws-key.py --resume -i {args.identifier} --push", file=sys.stderr)
            if not args.create_pr and pr_count == 0 and pushed_count > 0:
                print("\nTo create pull requests, run:", file=sys.stderr)
                print(f"  ./trufflehog/trufflehog-rotate-aws-key.py --resume -i {args.identifier} --create-pr", file=sys.stderr)

        if log_file:
            print(f"\nLog file: {log_file}", file=sys.stderr)

    # Cleanup logging
    if tee_output:
        tee_output.__exit__(None, None, None)


if __name__ == '__main__':
    main()
