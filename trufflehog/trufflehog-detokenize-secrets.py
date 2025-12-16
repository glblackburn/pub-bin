#!/usr/bin/env python3
"""
Trufflehog Secret Detokenization Script

Restores original secret values from tokenized trufflehog output files
using a lookup table.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


def load_lookup_table(lookup_table_path: Path) -> Dict[str, str]:
    """
    Load and validate lookup table from JSON file.
    Returns dictionary mapping tokens to secrets.
    """
    try:
        with open(lookup_table_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate structure
        if 'tokens' not in data:
            raise ValueError("Lookup table missing 'tokens' key")
        
        # Build token -> secret mapping
        token_map = {}
        for token, token_data in data['tokens'].items():
            if 'secret' not in token_data:
                raise ValueError(f"Token entry missing 'secret' key: {token}")
            token_map[token] = token_data['secret']
        
        return token_map
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in lookup table: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to load lookup table: {e}", file=sys.stderr)
        sys.exit(1)


def find_tokens_in_file(file_path: Path) -> Set[str]:
    """
    Find all tokens in a file.
    Returns set of token strings found.
    """
    tokens = set()
    # Pattern to match TOKEN_<hash>_<suffix>
    token_pattern = re.compile(r'TOKEN_[a-f0-9]{8}_[a-f0-9]{8}')
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            matches = token_pattern.findall(content)
            tokens.update(matches)
    except Exception as e:
        print(f"ERROR: Failed to read {file_path}: {e}", file=sys.stderr)
    
    return tokens


def detokenize_file(input_path: Path, output_path: Path, token_map: Dict[str, str]) -> Tuple[bool, Set[str]]:
    """
    Replace tokens with original secrets in a file.
    Returns (success, missing_tokens).
    """
    missing_tokens = set()
    
    try:
        with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Find all tokens in the file
        tokens_in_file = find_tokens_in_file(input_path)
        
        # Check for missing tokens
        for token in tokens_in_file:
            if token not in token_map:
                missing_tokens.add(token)
        
        # Replace each token with its secret
        for token, secret in token_map.items():
            # Match "Raw result: <token>" (with optional whitespace) and replace with "Raw result: <secret>"
            escaped_token = re.escape(token)
            pattern = rf'Raw result:\s+{escaped_token}(?=\s|$)'
            replacement = f"Raw result: {secret}"
            content = re.sub(pattern, replacement, content)
        
        # Write detokenized content
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True, missing_tokens
    except Exception as e:
        print(f"ERROR: Failed to detokenize {input_path}: {e}", file=sys.stderr)
        return False, missing_tokens


def scan_files(directory: Path, pattern: str) -> List[Path]:
    """
    Find all files matching the pattern in the directory (non-recursive).
    """
    files = []
    try:
        # Non-recursive search
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                files.append(file_path)
    except Exception as e:
        print(f"ERROR: Failed to scan directory {directory}: {e}", file=sys.stderr)
    
    return sorted(files)


def find_lookup_table(directory: Path, verbose: bool = False) -> Path:
    """
    Find lookup table file in the directory.
    Looks for files matching 'secrets_lookup_*.json' pattern.
    Returns the most recent one if multiple found.
    """
    lookup_files = []
    pattern = 'secrets_lookup_*.json'
    
    try:
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                lookup_files.append(file_path)
    except Exception as e:
        print(f"ERROR: Failed to search for lookup table in {directory}: {e}", file=sys.stderr)
        raise
    
    if not lookup_files:
        print(f"ERROR: No lookup table found in {directory}", file=sys.stderr)
        print(f"  Expected pattern: {pattern}", file=sys.stderr)
        print(f"  Use -l to specify a lookup table path", file=sys.stderr)
        sys.exit(1)
    
    if len(lookup_files) > 1:
        if verbose:
            print(f"WARNING: Found {len(lookup_files)} lookup table(s), using most recent:", file=sys.stderr)
            for f in sorted(lookup_files, key=lambda p: p.stat().st_mtime, reverse=True):
                print(f"  {f.name}", file=sys.stderr)
        # Use most recent (by modification time)
        lookup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    return lookup_files[0]


def main():
    parser = argparse.ArgumentParser(
        description='Restore original secrets from tokenized trufflehog output files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Restore secrets (auto-detects lookup table in directory)
  %(prog)s -d ./tokenized_results -o ./restored_results

  # Specify lookup table explicitly
  %(prog)s -d ./tokenized_results -l ./secrets_lookup.json -o ./restored_results

  # Dry run to see what would happen
  %(prog)s -d ./tokenized_results -n -v
        """
    )
    
    parser.add_argument('-d', '--directory', required=True,
                        help='Directory containing tokenized files')
    parser.add_argument('-l', '--lookup-table',
                        help='Path to lookup table JSON file (default: auto-detect in -d directory)')
    parser.add_argument('-o', '--output',
                        help='Output directory for detokenized files (default: <input_dir>_restored_<timestamp>)')
    parser.add_argument('-p', '--pattern', default='trufflehog-*.txt',
                        help='File pattern to match (default: trufflehog-*.txt)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Quiet mode')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='Show what would be done without making changes')
    parser.add_argument('--continue-on-missing', action='store_true',
                        help='Continue processing even if some tokens are missing from lookup table')
    
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
    
    # Determine lookup table path
    if args.lookup_table:
        lookup_table_path = Path(args.lookup_table).resolve()
        # Validate explicitly provided lookup table
        if not lookup_table_path.exists():
            print(f"ERROR: Lookup table not found: {lookup_table_path}", file=sys.stderr)
            sys.exit(1)
    else:
        # Auto-detect lookup table in input directory
        if not args.quiet:
            print(f"Auto-detecting lookup table in {input_dir}...", file=sys.stderr)
        lookup_table_path = find_lookup_table(input_dir, args.verbose)
        if not args.quiet:
            print(f"Using lookup table: {lookup_table_path.name}", file=sys.stderr)
    
    # Determine output directory
    if args.output:
        output_dir = Path(args.output).resolve()
    else:
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path(f"{input_dir}_restored_{timestamp}")
    
    # Load lookup table
    if not args.quiet:
        print(f"Loading lookup table from {lookup_table_path}...", file=sys.stderr)
    
    token_map = load_lookup_table(lookup_table_path)
    
    if not args.quiet:
        print(f"Loaded {len(token_map)} token(s) from lookup table", file=sys.stderr)
    
    # Find files to process
    files = scan_files(input_dir, args.pattern)
    
    if not files:
        if not args.quiet:
            print(f"No files found matching pattern '{args.pattern}' in {input_dir}", file=sys.stderr)
        sys.exit(0)
    
    if not args.quiet:
        print(f"Found {len(files)} file(s) to process", file=sys.stderr)
    
    if args.dry_run:
        if not args.quiet:
            print(f"DRY RUN: Would process {len(files)} file(s)", file=sys.stderr)
            print(f"DRY RUN: Output directory: {output_dir}", file=sys.stderr)
        sys.exit(0)
    
    # Process files
    if not args.quiet:
        print("Processing files...", file=sys.stderr)
    
    success_count = 0
    all_missing_tokens = set()
    
    for file_path in files:
        output_path = output_dir / file_path.name
        
        success, missing_tokens = detokenize_file(file_path, output_path, token_map)
        
        if success:
            success_count += 1
            all_missing_tokens.update(missing_tokens)
            
            if missing_tokens:
                print(f"  ⚠ {file_path.name}: {len(missing_tokens)} missing token(s)", file=sys.stderr)
                if args.verbose:
                    for token in sorted(missing_tokens):
                        print(f"    Missing: {token}", file=sys.stderr)
            else:
                if args.verbose:
                    print(f"  ✓ {output_path}", file=sys.stderr)
        else:
            print(f"  ✗ Failed: {file_path}", file=sys.stderr)
    
    # Report results
    if not args.quiet:
        print(f"\nDetokenization complete!", file=sys.stderr)
        print(f"  Processed: {success_count}/{len(files)} file(s)", file=sys.stderr)
        print(f"  Output directory: {output_dir}", file=sys.stderr)
    
    # Handle missing tokens
    if all_missing_tokens:
        print(f"\nWARNING: Found {len(all_missing_tokens)} missing token(s) in files", file=sys.stderr)
        if args.verbose:
            print("Missing tokens:", file=sys.stderr)
            for token in sorted(all_missing_tokens):
                print(f"  {token}", file=sys.stderr)
        
        if not args.continue_on_missing:
            print("\nERROR: Some tokens were not found in lookup table.", file=sys.stderr)
            print("Use --continue-on-missing to proceed anyway, or update the lookup table.", file=sys.stderr)
            sys.exit(1)
        else:
            if not args.quiet:
                print("Continuing despite missing tokens (--continue-on-missing)", file=sys.stderr)


if __name__ == '__main__':
    main()
