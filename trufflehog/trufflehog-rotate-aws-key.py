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
from typing import Dict, List, Optional, Tuple

try:
    from git import Repo, GitCommandError
except ImportError:
    print("ERROR: GitPython is required.", file=sys.stderr)
    print("Install with: make install-deps", file=sys.stderr)
    print("Or manually: pip install GitPython", file=sys.stderr)
    sys.exit(1)


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
        occurrences = []
        location_pattern = r'(\d+)\. \*\*Repository:\*\* (\S+)\s+.*?\*\*File:\*\* \[([^\]]+)\]\((https://github\.com/[^\)]+)\)\s+\*\*Detector:\*\* (\S+)'

        for loc_match in re.finditer(location_pattern, section_content, re.DOTALL):
            repo_name = loc_match.group(2)
            file_display = loc_match.group(3)
            file_url = loc_match.group(4)
            detector = loc_match.group(5)

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
            identifiers[identifier] = {
                'identifier': identifier,
                'secret_value': secret_value,
                'detector_type': 'AWS',  # Default, could extract from first occurrence
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


def replace_key_in_file(file_path: Path, old_key: str, new_key: str, line_number: int, backup_path: Optional[Path] = None) -> bool:
    """
    Replace AWS key in file.
    Returns: True if replacement was made, False otherwise
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

        # Common AWS key patterns
        patterns = [
            (r'(AWS_ACCESS_KEY_ID\s*[=:]\s*["\']?)' + re.escape(old_key) + r'(["\']?)', r'\1' + new_key + r'\2'),
            (r'("accessKeyId"\s*:\s*["\']?)' + re.escape(old_key) + r'(["\']?)', r'\1' + new_key + r'\2'),
            (r'("access_key"\s*:\s*["\']?)' + re.escape(old_key) + r'(["\']?)', r'\1' + new_key + r'\2'),
            (r'(access_key\s*[=:]\s*["\']?)' + re.escape(old_key) + r'(["\']?)', r'\1' + new_key + r'\2'),
            (re.escape(old_key), new_key)  # Fallback: exact match
        ]

        modified = False
        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                modified = True
                content = new_content
                break

        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False
    except Exception as e:
        print(f"ERROR: Failed to replace key in {file_path}: {e}", file=sys.stderr)
        return False


def process_repository(repo_info: Dict, old_key: str, new_key: str, work_dir: Path,
                      backup_dir: Path, branch_prefix: str, timestamp: str,
                      mode: str, reuse_clones: bool = False, verbose: bool = False) -> Dict:
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
        'backup_files': []
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

        # Find all occurrences for this repository
        for occ in repo_info.get('occurrences', []):
            if occ['repository_name'] == repo_name:
                file_path = local_path / occ['file_path']
                if file_path.exists():
                    backup_path = backup_dir / f"{org}-{repo_name}-{occ['file_path'].replace('/', '-')}"
                    if replace_key_in_file(file_path, old_key, new_key, occ['line_number'], backup_path):
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
            commit_message = repo_info.get('commit_message', f"Rotate AWS key: {identifier}")
            repo.git.commit('-m', commit_message)
            status['changes_committed'] = True
            status['commit_hash'] = repo.head.commit.hexsha

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


def main():
    parser = argparse.ArgumentParser(
        description='Rotate AWS keys found in trufflehog analysis reports',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('-r', '--report', required=True, help='Path to trufflehog-analyze-results.py markdown report')
    parser.add_argument('-i', '--identifier', required=True, help='Identifier to rotate (TOKEN_* or RAW_*)')
    parser.add_argument('-k', '--new-key', help='New AWS key value (or use -p for prompt)')
    parser.add_argument('-l', '--limit', type=int, default=0, help='Limit number of repositories to process (Default: 0 = all)')
    parser.add_argument('-p', '--prompt-key', action='store_true', help='Prompt for new key interactively (masked input)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode. Output as little as possible.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output (may contain sensitive data)')

    parser.add_argument('--lookup-table', help='Path to secrets lookup table (required for TOKEN_ identifiers)')
    parser.add_argument('--mode', choices=['dry-run', 'commit'], default='dry-run', help='Operation mode (Default: dry-run)')
    parser.add_argument('--resume', action='store_true', help='Resume a previous rotation operation')
    parser.add_argument('--state-file', help='Path to state file for resume functionality')
    parser.add_argument('--branch-prefix', default='rotate-aws-key', help='Prefix for branch names (Default: rotate-aws-key)')
    parser.add_argument('--commit-message', help='Custom commit message')
    parser.add_argument('--skip-repos', help='Comma-separated list of repository names to skip')
    parser.add_argument('--only-repos', help='Comma-separated list of repository names to process')
    parser.add_argument('--work-dir', default='/tmp/trufflehog-rotate', help='Working directory for cloning repositories')
    parser.add_argument('--reuse-clones', action='store_true', help='Reuse existing clones if found')
    parser.add_argument('--backup-dir', help='Directory to store backup copies of modified files')

    args = parser.parse_args()

    # Setup secure directories
    secure_dir, trufflehog_rotate_dir, default_backup_dir = setup_secure_directories()
    backup_dir = Path(args.backup_dir) if args.backup_dir else default_backup_dir

    # Get new key
    if args.prompt_key:
        new_key = getpass.getpass("Enter new AWS key (input will be hidden): ")
    elif args.new_key:
        new_key = args.new_key
    else:
        new_key = os.environ.get('TRUFFLEHOG_NEW_AWS_KEY')
        if not new_key:
            print("ERROR: New key required. Use -k, -p, or set TRUFFLEHOG_NEW_AWS_KEY", file=sys.stderr)
            sys.exit(1)

    if not new_key:
        print("ERROR: New key cannot be empty", file=sys.stderr)
        sys.exit(1)

    # Resume mode
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

        if not args.quiet:
            print(f"Resuming from state file: {state_file}", file=sys.stderr)

        state = load_state(state_file)

        # Get new key (should be same as before, but verify hash)
        if args.prompt_key:
            new_key = getpass.getpass("Enter new AWS key (input will be hidden): ")
        elif args.new_key:
            new_key = args.new_key
        else:
            new_key = os.environ.get('TRUFFLEHOG_NEW_AWS_KEY')
            if not new_key:
                print("ERROR: New key required for resume. Use -k, -p, or set TRUFFLEHOG_NEW_AWS_KEY", file=sys.stderr)
                sys.exit(1)

        # Verify key hash matches
        new_key_hash = hashlib.sha256(new_key.encode()).hexdigest()
        if state.get('new_key_hash') != f'sha256:{new_key_hash}':
            print("WARNING: New key hash does not match state file. Continuing anyway...", file=sys.stderr)

        # Process pending repositories
        pending_repos = [r for r in state['repositories'] if r['status'] in ('pending', 'completed') and not r.get('changes_committed', False)]

        # Apply limit
        if args.limit > 0:
            pending_repos = pending_repos[:args.limit]

        if not args.quiet:
            print(f"Found {len(pending_repos)} repositories with pending changes", file=sys.stderr)

        work_dir = Path(state['work_dir'])
        # old_key is no longer stored in state file (replaced with old_key_hash for security)
        # Resume mode doesn't need old_key since it only commits existing changes

        for i, repo_status in enumerate(pending_repos, 1):
            org = repo_status.get('organization', 'unknown')
            repo_name = repo_status.get('repository_name', 'unknown')
            if not args.quiet:
                print(f"\n[{i}/{len(pending_repos)}] Processing {org}/{repo_name}...", file=sys.stderr)

            local_path = Path(repo_status['local_clone_path'])
            if not local_path.exists():
                repo_status['status'] = 'failed'
                repo_status['error'] = 'Local clone path does not exist'
                continue

            try:
                repo = Repo(str(local_path))

                # Check if branch exists
                branch_name = repo_status.get('branch_name')
                if branch_name:
                    try:
                        repo.git.checkout(branch_name)
                    except GitCommandError:
                        repo_status['status'] = 'failed'
                        repo_status['error'] = 'Branch does not exist'
                        continue

                # Check if there are uncommitted changes
                if repo.is_dirty() or len(list(repo.index.diff('HEAD'))) > 0:
                    # Commit if in commit mode
                    if args.mode == 'commit':
                        commit_message = args.commit_message or f"Rotate AWS key: {state['identifier']}"
                        repo.git.add('-A')
                        repo.git.commit('-m', commit_message)
                        repo_status['changes_committed'] = True
                        repo_status['commit_hash'] = repo.head.commit.hexsha
                        repo_status['status'] = 'completed'
                    else:
                        repo_status['status'] = 'pending'
                else:
                    repo_status['status'] = 'completed'
                    if not args.quiet:
                        print(f"  No uncommitted changes found", file=sys.stderr)

            except Exception as e:
                repo_status['status'] = 'failed'
                repo_status['error'] = str(e)
                if args.verbose:
                    print(f"  Error: {e}", file=sys.stderr)

        # Update state file
        state['mode'] = args.mode
        save_state(state, state_file)

        if not args.quiet:
            completed = sum(1 for r in state['repositories'] if r.get('changes_committed', False))
            print(f"\nCompleted: {completed} repositories committed", file=sys.stderr)
            print(f"State updated: {state_file}", file=sys.stderr)

        sys.exit(0)

    # Parse report
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

    identifier_data = identifiers[args.identifier]

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

    # Group occurrences by repository
    repos = defaultdict(list)
    for occ in identifier_data['occurrences']:
        repo_key = (occ['repository_url'], occ['repository_name'], occ['organization'])
        repos[repo_key].append(occ)

    # Apply filters
    skip_repos = set(args.skip_repos.split(',')) if args.skip_repos else set()
    only_repos = set(args.only_repos.split(',')) if args.only_repos else set()

    repo_list = []
    for (repo_url, repo_name, org), occs in repos.items():
        if repo_name in skip_repos:
            continue
        if only_repos and repo_name not in only_repos:
            continue

        repo_list.append({
            'repository_url': repo_url,
            'repository_name': repo_name,
            'organization': org,
            'identifier': args.identifier,
            'occurrences': occs
        })

    # Apply limit
    if args.limit > 0:
        repo_list = repo_list[:args.limit]

    if not args.quiet:
        print(f"Processing AWS key rotation for identifier: {args.identifier}", file=sys.stderr)
        print(f"Old key: {old_key[:8]}... (hidden)", file=sys.stderr)
        print(f"New key: ******** (hidden)", file=sys.stderr)
        print(f"Repositories to process: {len(repo_list)}", file=sys.stderr)
        print("─" * 70, file=sys.stderr)

    # Process repositories
    work_dir = Path(args.work_dir)
    timestamp = datetime.now().isoformat()

    repositories_status = []
    for i, repo_info in enumerate(repo_list, 1):
        if not args.quiet:
            print(f"\n[{i}/{len(repo_list)}] Processing {repo_info['organization']}/{repo_info['repository_name']}...", file=sys.stderr)

        # Add commit message to repo_info if provided
        if args.commit_message:
            repo_info['commit_message'] = args.commit_message

        status = process_repository(
            repo_info, old_key, new_key, work_dir, backup_dir,
            args.branch_prefix, timestamp, args.mode, args.reuse_clones, args.verbose
        )
        repositories_status.append(status)

        if not args.quiet:
            if status['status'] == 'completed':
                print(f"  ✓ Status: {status['status']}", file=sys.stderr)
                print(f"  ✓ Files modified: {len(status['files_modified'])}", file=sys.stderr)
                if status['changes_committed']:
                    print(f"  ✓ Changes committed", file=sys.stderr)
            else:
                print(f"  ✗ Status: {status['status']}", file=sys.stderr)
                if 'error' in status:
                    print(f"  ✗ Error: {status['error']}", file=sys.stderr)

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

        if args.mode == 'dry-run':
            print("\nTo commit changes, run:", file=sys.stderr)
            print(f"  ./trufflehog-rotate-aws-key.py --resume --mode commit", file=sys.stderr)


if __name__ == '__main__':
    main()
