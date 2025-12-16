#!/usr/bin/env python3
"""
Trufflehog Tokenized Results Analyzer

Processes tokenized trufflehog output files to generate a summary report.
Counts unique tokens, identifies where each token appears, and generates GitHub URLs.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import quote


def extract_repository_name(repo_path: str) -> str:
    """
    Extract repository name from file:// URI path.
    Input: file:///path/to/repos/repo-name
    Output: repo-name (last component)
    """
    # Remove file:// prefix if present
    if repo_path.startswith('file://'):
        repo_path = repo_path[7:]
    
    # Get last component
    return Path(repo_path).name


def parse_tokenized_file(file_path: Path) -> List[Dict]:
    """
    Parse a single tokenized file and extract token occurrences.
    Returns list of token occurrences with context.
    """
    occurrences = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Split into result blocks (each starts with "✅ Found verified result")
        # Pattern to match result blocks
        result_blocks = re.split(r'✅ Found verified result', content)
        
        for block in result_blocks[1:]:  # Skip first empty split
            occurrence = {}
            
            # Extract Detector Type
            detector_match = re.search(r'^Detector Type:\s*(.+)$', block, re.MULTILINE)
            if detector_match:
                occurrence['detector_type'] = detector_match.group(1).strip()
            else:
                occurrence['detector_type'] = None
            
            # Extract Raw result (token)
            token_match = re.search(r'^Raw result:\s*(TOKEN_\S+)$', block, re.MULTILINE)
            if not token_match:
                continue  # Skip if no token found
            occurrence['token'] = token_match.group(1).strip()
            
            # Extract File
            file_match = re.search(r'^File:\s*(.+)$', block, re.MULTILINE)
            if file_match:
                occurrence['file_path'] = file_match.group(1).strip()
            else:
                occurrence['file_path'] = None
            
            # Extract Line
            line_match = re.search(r'^Line:\s*(\d+)$', block, re.MULTILINE)
            if line_match:
                occurrence['line_number'] = int(line_match.group(1))
            else:
                occurrence['line_number'] = None
            
            # Extract Repository (prefer file:// format, but handle both)
            repo_match = re.search(r'^Repository:\s*(.+)$', block, re.MULTILINE)
            if repo_match:
                repo_path = repo_match.group(1).strip()
                # If it doesn't start with file://, add it for consistency
                if not repo_path.startswith('file://'):
                    repo_path = f'file://{repo_path}'
                occurrence['repository_path'] = repo_path
                occurrence['repository_name'] = extract_repository_name(repo_path)
            else:
                occurrence['repository_path'] = None
                occurrence['repository_name'] = None
            
            # Only add if we have essential fields
            if occurrence.get('token') and occurrence.get('repository_name'):
                occurrences.append(occurrence)
    
    except Exception as e:
        print(f"ERROR: Failed to parse {file_path}: {e}", file=sys.stderr)
        return []
    
    return occurrences


def get_repo_config(repo_name: str, repo_map: Dict, default_org: str, default_branch: str) -> Tuple[str, str]:
    """
    Get org and branch for a repository.
    Check repo-map first, fall back to defaults.
    """
    if repo_name in repo_map:
        org = repo_map[repo_name].get('org', default_org)
        branch = repo_map[repo_name].get('branch', default_branch)
    else:
        org = default_org
        branch = default_branch
    
    return org, branch


def detect_branch(repo_path: str, default_branch: str, branch_cache: Dict[str, str]) -> str:
    """
    Detect current git branch from local repo if path exists.
    Cache results to avoid repeated git commands.
    """
    # Remove file:// prefix if present
    if repo_path.startswith('file://'):
        repo_path = repo_path[7:]
    
    # Check cache first
    if repo_path in branch_cache:
        return branch_cache[repo_path]
    
    # Try to detect branch if path exists
    if os.path.exists(repo_path) and os.path.isdir(repo_path):
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                branch = result.stdout.strip()
                branch_cache[repo_path] = branch
                return branch
        except Exception:
            pass  # Fall through to default
    
    # Use default
    branch_cache[repo_path] = default_branch
    return default_branch


def build_github_file_url(base_url: str, org: str, repo_name: str, branch: str, 
                         file_path: str, line_number: Optional[int] = None) -> str:
    """
    Build complete GitHub URL for a file.
    Format: {base_url}{org}/{repo_name}/blob/{branch}/{file_path}#L{line}
    """
    # Ensure base_url ends with /
    if not base_url.endswith('/'):
        base_url += '/'
    
    # URL encode file path components
    path_parts = file_path.split('/')
    encoded_parts = [quote(part, safe='') for part in path_parts]
    encoded_path = '/'.join(encoded_parts)
    
    url = f"{base_url}{org}/{repo_name}/blob/{branch}/{encoded_path}"
    
    if line_number:
        url += f"#L{line_number}"
    
    return url


def build_token_index(occurrences: List[Dict]) -> Dict:
    """
    Build token → locations mapping.
    """
    token_index = defaultdict(lambda: {
        'occurrences': [],
        'detector_types': set(),
        'repositories': set(),
        'files': set()
    })
    
    for occ in occurrences:
        token = occ['token']
        token_index[token]['occurrences'].append(occ)
        if occ.get('detector_type'):
            token_index[token]['detector_types'].add(occ['detector_type'])
        if occ.get('repository_name'):
            token_index[token]['repositories'].add(occ['repository_name'])
        if occ.get('file_path'):
            token_index[token]['files'].add(occ['file_path'])
    
    return token_index


def calculate_token_counts(token_index: Dict, repo_map: Dict, default_org: str, 
                           default_branch: str, base_url: str, branch_cache: Dict) -> Dict:
    """
    Calculate occurrence, repository, file counts, and detector types per token.
    Also validates detector types and builds URLs.
    """
    result = {}
    
    for token, data in token_index.items():
        # Validate detector type (should be only one)
        detector_types = list(data['detector_types'])
        if len(detector_types) > 1:
            detector_type = detector_types[0]  # Use first, but flag error
            detector_type_error = True
        elif len(detector_types) == 1:
            detector_type = detector_types[0]
            detector_type_error = False
        else:
            detector_type = "Unknown"
            detector_type_error = False
        
        # Build occurrences with URLs
        occurrences_with_urls = []
        for occ in data['occurrences']:
            if occ.get('repository_path') and occ.get('file_path'):
                repo_name = occ['repository_name']
                org, branch = get_repo_config(repo_name, repo_map, default_org, default_branch)
                
                # Detect branch if needed
                if branch == default_branch:
                    branch = detect_branch(occ['repository_path'], default_branch, branch_cache)
                
                file_url = build_github_file_url(
                    base_url, org, repo_name, branch,
                    occ['file_path'], occ.get('line_number')
                )
                occ['file_url'] = file_url
                occ['org'] = org
                occ['branch'] = branch
            else:
                occ['file_url'] = None
                occ['org'] = None
                occ['branch'] = None
            
            occurrences_with_urls.append(occ)
        
        result[token] = {
            'occurrences': occurrences_with_urls,
            'occurrence_count': len(occurrences_with_urls),
            'repository_count': len(data['repositories']),
            'file_count': len(data['files']),
            'detector_type': detector_type,
            'detector_type_error': detector_type_error,
            'repositories': sorted(data['repositories']),
            'files': sorted(data['files'])
        }
    
    return result


def create_token_anchor_id(token: str) -> str:
    """
    Generate anchor ID from token.
    Converts TOKEN_abc123_def456 → token-abc123-def456
    """
    # Remove TOKEN_ prefix and convert to lowercase
    anchor = token.replace('TOKEN_', '').lower()
    # Replace underscores with hyphens
    anchor = anchor.replace('_', '-')
    return f"token-{anchor}"


def format_tokens_summary_table(token_data: Dict) -> str:
    """
    Format clean tokens summary table with clickable links.
    """
    lines = [
        "## Tokens Summary",
        "",
        "A clean summary table with clickable links to detailed token sections below.",
        "",
        "| Token | Occurrences | Repositories | Files | Detector Type |",
        "|-------|-------------|--------------|-------|---------------|"
    ]
    
    # Sort by occurrence count (descending)
    sorted_tokens = sorted(
        token_data.items(),
        key=lambda x: x[1]['occurrence_count'],
        reverse=True
    )
    
    for token, data in sorted_tokens:
        anchor_id = create_token_anchor_id(token)
        detector_type = data['detector_type']
        if data['detector_type_error']:
            detector_type += " ⚠️ ERROR: Multiple types"
        
        lines.append(
            f"| [{token}](#{anchor_id}) | {data['occurrence_count']} | "
            f"{data['repository_count']} | {data['file_count']} | {detector_type} |"
        )
    
    lines.append("")
    lines.append("*Click token names to jump to detailed information. Sorted by occurrence count (descending).*")
    if any(data['detector_type_error'] for data in token_data.values()):
        lines.append("*⚠️ Some tokens have multiple detector types - this is an error condition.*")
    
    return '\n'.join(lines)


def format_token_section(token: str, data: Dict) -> str:
    """
    Format token details section with anchor ID.
    """
    anchor_id = create_token_anchor_id(token)
    lines = [
        f"### <a id=\"{anchor_id}\"></a>{token}",
        f"**Occurrences:** {data['occurrence_count']} (total times this token appears)",
        f"**Repositories:** {data['repository_count']} (number of unique repositories containing this token)",
        f"**Files:** {data['file_count']} (number of unique files containing this token)",
        f"**Detector Type:** {data['detector_type']}"
    ]
    
    if data['detector_type_error']:
        lines.append("⚠️ **ERROR:** This token appears with multiple detector types!")
    
    lines.append("")
    lines.append("**Locations:**")
    
    # Group by repository
    repo_groups = defaultdict(list)
    for occ in data['occurrences']:
        repo_name = occ.get('repository_name', 'Unknown')
        repo_groups[repo_name].append(occ)
    
    repo_num = 1
    for repo_name, occs in sorted(repo_groups.items()):
        lines.append(f"{repo_num}. **Repository:** {repo_name}")
        
        # Group by detector type within this repo
        for occ in occs:
            file_path = occ.get('file_path', 'Unknown')
            line_num = occ.get('line_number')
            file_url = occ.get('file_url')
            detector = occ.get('detector_type', 'Unknown')
            
            if line_num:
                file_display = f"{file_path}:{line_num}"
            else:
                file_display = file_path
            
            if file_url:
                lines.append(f"   - **File:** [{file_display}]({file_url})")
            else:
                lines.append(f"   - **File:** {file_display} (URL not available)")
            lines.append(f"   - **Detector:** {detector}")
        
        repo_num += 1
    
    return '\n'.join(lines)


def format_repository_summary_table(repo_data: Dict, base_url: str, org_map: Dict, default_org: str) -> str:
    """
    Format repository summary table with clickable links.
    """
    lines = [
        "## Repositories Summary",
        "",
        "| Repository | Tokens | Files | Occurrences |",
        "|------------|--------|-------|-------------|"
    ]
    
    # Sort by occurrences (descending)
    sorted_repos = sorted(
        repo_data.items(),
        key=lambda x: x[1]['occurrences'],
        reverse=True
    )
    
    for repo_name, data in sorted_repos:
        # Get org for this repo
        org, _ = get_repo_config(repo_name, org_map, default_org, 'main')
        repo_url = f"{base_url.rstrip('/')}/{org}/{repo_name}"
        
        lines.append(
            f"| [{repo_name}]({repo_url}) | {data['tokens']} | "
            f"{data['files']} | {data['occurrences']} |"
        )
    
    return '\n'.join(lines)


def build_repository_summary(token_data: Dict) -> Dict:
    """
    Build repository summary data.
    """
    repo_summary = defaultdict(lambda: {
        'tokens': set(),
        'files': set(),
        'occurrences': 0
    })
    
    for token, data in token_data.items():
        for occ in data['occurrences']:
            repo_name = occ.get('repository_name')
            if repo_name:
                repo_summary[repo_name]['tokens'].add(token)
                if occ.get('file_path'):
                    repo_summary[repo_name]['files'].add(occ['file_path'])
                repo_summary[repo_name]['occurrences'] += 1
    
    # Convert sets to counts
    result = {}
    for repo_name, data in repo_summary.items():
        result[repo_name] = {
            'tokens': len(data['tokens']),
            'files': len(data['files']),
            'occurrences': data['occurrences']
        }
    
    return result


def generate_markdown_report(token_data: Dict, repo_summary: Dict, source_dir: Path,
                           base_url: str, org_map: Dict, default_org: str,
                           output_path: Path) -> None:
    """
    Generate markdown report file.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    total_files = sum(1 for _ in source_dir.glob('trufflehog-*.txt'))
    unique_tokens = len(token_data)
    total_occurrences = sum(data['occurrence_count'] for data in token_data.values())
    total_repos = len(repo_summary)
    
    lines = [
        "# Trufflehog Tokenized Results Analysis",
        "",
        f"**Generated:** {timestamp}",
        f"**Source Directory:** {source_dir}",
        f"**Files Processed:** {total_files}",
        f"**Unique Tokens:** {unique_tokens}",
        f"**Total Occurrences:** {total_occurrences}",
        "",
        "---",
        "",
        "## Summary Statistics",
        "",
        f"- **Total Files Scanned:** {total_files}",
        f"- **Total Repositories:** {total_repos}",
        f"- **Unique Tokens Found:** {unique_tokens}",
        f"- **Total Token Occurrences:** {total_occurrences}",
    ]
    
    if unique_tokens > 0:
        avg_occurrences = total_occurrences / unique_tokens
        lines.append(f"- **Average Occurrences per Token:** {avg_occurrences:.2f}")
    
    lines.extend([
        "",
        "---",
        "",
        format_tokens_summary_table(token_data),
        "",
        "---",
        "",
        "## Token Details",
        ""
    ])
    
    # Sort tokens by occurrence count for details
    sorted_tokens = sorted(
        token_data.items(),
        key=lambda x: x[1]['occurrence_count'],
        reverse=True
    )
    
    for token, data in sorted_tokens:
        lines.append(format_token_section(token, data))
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # Add repository summary
    lines.append(format_repository_summary_table(repo_summary, base_url, org_map, default_org))
    lines.append("")
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def open_in_browser(file_path: Path) -> None:
    """
    Open markdown file in default browser.
    """
    try:
        if sys.platform == 'darwin':  # macOS
            subprocess.run(['open', str(file_path)], check=False)
        elif sys.platform == 'linux':
            subprocess.run(['xdg-open', str(file_path)], check=False)
        elif sys.platform == 'win32':
            os.startfile(str(file_path))
    except Exception as e:
        print(f"WARNING: Could not open browser: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze tokenized trufflehog output files and generate markdown report',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-d', '--directory', required=True,
                        help='Directory containing tokenized files')
    parser.add_argument('-o', '--output',
                        help='Output markdown file path (default: /tmp/tokenized_analysis_<timestamp>.md)')
    parser.add_argument('-p', '--pattern', default='trufflehog-*.txt',
                        help='File pattern to match (default: trufflehog-*.txt)')
    parser.add_argument('--org', required=True,
                        help='GitHub organization/user name')
    parser.add_argument('--branch', default='main',
                        help='Default git branch to use in URLs (default: main)')
    parser.add_argument('--repo-map',
                        help='JSON file for repo-specific org/branch overrides')
    parser.add_argument('--github-base', default='https://github.com/',
                        help='Base GitHub URL (default: https://github.com/)')
    parser.add_argument('--no-browser', action='store_true',
                        help='Do not open report in browser')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Quiet mode')
    
    args = parser.parse_args()
    
    # Convert to Path objects
    input_dir = Path(args.directory).resolve()
    
    # Validate input directory
    if not input_dir.exists():
        print(f"ERROR: Directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)
    
    if not input_dir.is_dir():
        print(f"ERROR: Not a directory: {input_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Determine output file
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = Path(f"/tmp/tokenized_analysis_{timestamp}.md")
    
    # Load repo map if provided
    repo_map = {}
    if args.repo_map:
        repo_map_path = Path(args.repo_map)
        if not repo_map_path.exists():
            print(f"ERROR: Repo map file not found: {repo_map_path}", file=sys.stderr)
            sys.exit(1)
        try:
            with open(repo_map_path, 'r') as f:
                repo_map = json.load(f)
        except Exception as e:
            print(f"ERROR: Failed to load repo map: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Find files to process
    files = sorted(input_dir.glob(args.pattern))
    
    if not files:
        if not args.quiet:
            print(f"No files found matching pattern '{args.pattern}' in {input_dir}", file=sys.stderr)
        sys.exit(0)
    
    if not args.quiet:
        print(f"Found {len(files)} file(s) to process", file=sys.stderr)
    
    # Parse all files
    all_occurrences = []
    for file_path in files:
        if args.verbose:
            print(f"Processing {file_path.name}...", file=sys.stderr)
        occurrences = parse_tokenized_file(file_path)
        all_occurrences.extend(occurrences)
        if args.verbose:
            print(f"  Found {len(occurrences)} token occurrence(s)", file=sys.stderr)
    
    if not args.quiet:
        print(f"Total occurrences found: {len(all_occurrences)}", file=sys.stderr)
    
    # Build token index
    token_index = build_token_index(all_occurrences)
    
    # Calculate counts and build URLs
    branch_cache = {}
    token_data = calculate_token_counts(
        token_index, repo_map, args.org, args.branch,
        args.github_base, branch_cache
    )
    
    # Check for detector type errors
    errors = [token for token, data in token_data.items() if data['detector_type_error']]
    if errors and not args.quiet:
        print(f"WARNING: {len(errors)} token(s) have multiple detector types (error condition)", file=sys.stderr)
    
    # Build repository summary
    repo_summary = build_repository_summary(token_data)
    
    # Generate markdown report
    if not args.quiet:
        print(f"Generating markdown report...", file=sys.stderr)
    
    generate_markdown_report(
        token_data, repo_summary, input_dir,
        args.github_base, repo_map, args.org,
        output_path
    )
    
    if not args.quiet:
        print(f"✓ Report saved to: {output_path}", file=sys.stderr)
    
    # Open in browser
    if not args.no_browser:
        if not args.quiet:
            print(f"Opening report in browser...", file=sys.stderr)
        open_in_browser(output_path)


if __name__ == '__main__':
    main()
