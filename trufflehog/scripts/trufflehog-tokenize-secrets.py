#!/usr/bin/env python3
"""
Trufflehog Secret Tokenization Script

Replaces secret values in trufflehog output files with reversible tokens.
Same secret values map to the same tokens across all files.
Generates a lookup table for later restoration.
"""

import argparse
import hashlib
import json
import os
import re
import secrets
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


def generate_token(secret: str, existing_tokens: Dict[str, str], hash_length: int = 8, suffix_length: int = 8) -> str:
    """
    Generate a token for a secret value.
    Same secret always generates the same token.
    
    Format: TOKEN_<hash_prefix>_<random_suffix>
    """
    # Calculate SHA256 hash for deterministic prefix
    hash_obj = hashlib.sha256(secret.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    hash_prefix = hash_hex[:hash_length]
    
    # Check if we already have a token for this secret
    if secret in existing_tokens:
        return existing_tokens[secret]
    
    # Generate random suffix for uniqueness and security
    # suffix_length is in hex characters, so divide by 2 for bytes
    suffix_bytes = (suffix_length + 1) // 2
    random_suffix = secrets.token_hex(suffix_bytes)[:suffix_length]
    
    token = f"TOKEN_{hash_prefix}_{random_suffix}"
    
    # Handle extremely unlikely collision
    if token in existing_tokens.values():
        # Regenerate suffix if collision (should never happen, but be safe)
        while token in existing_tokens.values():
            random_suffix = secrets.token_hex(suffix_bytes)[:suffix_length]
            token = f"TOKEN_{hash_prefix}_{random_suffix}"
    
    return token


def extract_secrets(file_path: Path) -> List[str]:
    """
    Extract all "Raw result:" values from a file.
    Returns list of unique secret values found.
    """
    secrets_found = []
    raw_result_pattern = re.compile(r'^Raw result:\s*(.+)$', re.MULTILINE)
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            matches = raw_result_pattern.findall(content)
            secrets_found = [match.strip() for match in matches if match.strip()]
    except Exception as e:
        print(f"ERROR: Failed to read {file_path}: {e}", file=sys.stderr)
        return []
    
    return secrets_found


def tokenize_file(input_path: Path, output_path: Path, token_map: Dict[str, str]) -> bool:
    """
    Replace secrets with tokens in a file.
    Returns True if successful, False otherwise.
    """
    try:
        with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Replace each secret with its token
        # Match "Raw result: <secret>" (with optional whitespace) and replace with "Raw result: <token>"
        for secret, token in token_map.items():
            # Escape the secret for regex, but allow for optional whitespace
            escaped_secret = re.escape(secret)
            # Match "Raw result:" followed by optional whitespace, then the secret
            # The secret might be at end of line or followed by whitespace/newline
            pattern = rf'Raw result:\s+{escaped_secret}(?=\s|$)'
            replacement = f"Raw result: {token}"
            content = re.sub(pattern, replacement, content)
        
        # Write tokenized content
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"ERROR: Failed to tokenize {input_path}: {e}", file=sys.stderr)
        return False


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


def save_lookup_table(lookup_table: dict, output_path: Path, verbose: bool = False) -> bool:
    """
    Save lookup table to JSON file with secure permissions.
    """
    try:
        # Create parent directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(lookup_table, f, indent=2, ensure_ascii=False)
        
        # Set restrictive permissions (600 = owner read/write only)
        os.chmod(output_path, 0o600)
        
        if verbose:
            print(f"✓ Saved lookup table to {output_path}")
        
        return True
    except Exception as e:
        print(f"ERROR: Failed to save lookup table to {output_path}: {e}", file=sys.stderr)
        return False


def set_secure_permissions(file_path: Path) -> None:
    """Set restrictive file permissions."""
    try:
        os.chmod(file_path, 0o600)
    except Exception as e:
        print(f"WARNING: Could not set permissions on {file_path}: {e}", file=sys.stderr)


def display_warning_banner(lookup_table_path: Path, file_count: int) -> None:
    """Display HUGE WARNING BANNER for in-place tokenization."""
    banner = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    ⚠️  WARNING: IN-PLACE TOKENIZATION  ⚠️                  ║
║                                                                              ║
║  This operation will OVERWRITE your original files with tokenized versions. ║
║                                                                              ║
║  • Original files will be PERMANENTLY MODIFIED                               ║
║  • You MUST have the lookup table to restore original secrets               ║
║  • If you lose the lookup table, secrets CANNOT be recovered                ║
║  • This action CANNOT be undone without the lookup table                    ║
║                                                                              ║
║  Lookup table will be saved to: {lookup_table_path}                         ║
║  Files to be modified: {file_count} files                                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner, file=sys.stderr)


def confirm_in_place() -> bool:
    """Require explicit confirmation for in-place tokenization."""
    response = input("Type 'YES' to confirm in-place tokenization (this cannot be undone): ")
    return response == "YES"


def main():
    parser = argparse.ArgumentParser(
        description='Tokenize secrets in trufflehog output files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (creates timestamped output directory)
  %(prog)s -d ./scan_results

  # Custom output and lookup table
  %(prog)s -d ./scan_results -o ./tokenized_results -l ./secrets_lookup.json

  # Dry run to see what would happen
  %(prog)s -d ./scan_results -n -v

  # In-place tokenization (with confirmation prompt)
  %(prog)s -d ./scan_results --in-place
        """
    )
    
    parser.add_argument('-d', '--directory', required=True,
                        help='Target directory containing files to tokenize')
    parser.add_argument('-o', '--output',
                        help='Output directory for tokenized files (default: <input_dir>_tokenized_<timestamp>)')
    parser.add_argument('-l', '--lookup-table',
                        help='Path to lookup table file (default: secrets_lookup_<timestamp>.json in output directory)')
    parser.add_argument('-p', '--pattern', default='trufflehog-*.txt',
                        help='File pattern to match (default: trufflehog-*.txt)')
    parser.add_argument('--hash-length', type=int, default=8,
                        help='Length of hash prefix in token (default: 8)')
    parser.add_argument('--suffix-length', type=int, default=8,
                        help='Length of random suffix in token (default: 8 hex chars)')
    parser.add_argument('--in-place', action='store_true',
                        help='Overwrite original files (REQUIRES EXPLICIT CONFIRMATION)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Quiet mode')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='Show what would be done without making changes')
    
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
    
    # Generate timestamp for unique naming
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Determine output directory
    if args.in_place:
        output_dir = input_dir
    elif args.output:
        output_dir = Path(args.output).resolve()
    else:
        output_dir = Path(f"{input_dir}_tokenized_{timestamp}")
    
    # Determine lookup table path
    if args.lookup_table:
        lookup_table_path = Path(args.lookup_table).resolve()
    else:
        lookup_table_path = output_dir / f"secrets_lookup_{timestamp}.json"
    
    # Check if lookup table already exists
    if lookup_table_path.exists():
        print(f"ERROR: Lookup table already exists: {lookup_table_path}", file=sys.stderr)
        print("Please use a different filename or remove the existing file.", file=sys.stderr)
        sys.exit(1)
    
    # Find files to process
    files = scan_files(input_dir, args.pattern)
    
    if not files:
        if not args.quiet:
            print(f"No files found matching pattern '{args.pattern}' in {input_dir}", file=sys.stderr)
        sys.exit(0)
    
    if not args.quiet:
        print(f"Found {len(files)} file(s) to process", file=sys.stderr)
    
    # Handle in-place tokenization
    if args.in_place:
        display_warning_banner(lookup_table_path, len(files))
        if not args.dry_run:
            if not confirm_in_place():
                print("Operation cancelled.", file=sys.stderr)
                sys.exit(0)
        else:
            if not args.quiet:
                print("DRY RUN: Would require confirmation in real run", file=sys.stderr)
    
    if args.dry_run:
        if not args.quiet:
            print(f"DRY RUN: Would process {len(files)} file(s)", file=sys.stderr)
            print(f"DRY RUN: Output directory: {output_dir}", file=sys.stderr)
            print(f"DRY RUN: Lookup table: {lookup_table_path}", file=sys.stderr)
        sys.exit(0)
    
    # Phase 1: Extract all secrets from all files
    if not args.quiet:
        print("Phase 1: Extracting secrets from files...", file=sys.stderr)
    
    all_secrets = set()
    file_secrets_map = {}
    
    for file_path in files:
        secrets_found = extract_secrets(file_path)
        file_secrets_map[file_path] = secrets_found
        all_secrets.update(secrets_found)
        
        if args.verbose:
            print(f"  {file_path.name}: {len(secrets_found)} secret(s) found", file=sys.stderr)
    
    if not args.quiet:
        print(f"Found {len(all_secrets)} unique secret(s) across all files", file=sys.stderr)
    
    # Phase 2: Generate tokens for all secrets
    if not args.quiet:
        print("Phase 2: Generating tokens...", file=sys.stderr)
    
    secret_to_token = {}
    token_to_secret = {}
    
    for secret in sorted(all_secrets):
        token = generate_token(secret, secret_to_token, args.hash_length, args.suffix_length)
        secret_to_token[secret] = token
        token_to_secret[token] = secret
    
    # Phase 3: Build lookup table structure
    if not args.quiet:
        print("Phase 3: Building lookup table...", file=sys.stderr)
    
    lookup_table = {
        "metadata": {
            "version": "1.0",
            "created": datetime.now().isoformat() + "Z",
            "source_directory": str(input_dir),
            "file_count": len(files),
            "unique_secrets": len(all_secrets),
            "tool": "trufflehog-tokenize-secrets"
        },
        "tokens": {}
    }
    
    # Build token entries with file tracking
    for secret, token in secret_to_token.items():
        occurrence_count = 0
        files_with_secret = []
        
        for file_path, secrets_list in file_secrets_map.items():
            count = secrets_list.count(secret)
            if count > 0:
                occurrence_count += count
                files_with_secret.append(file_path.name)
        
        lookup_table["tokens"][token] = {
            "secret": secret,
            "first_seen": datetime.now().isoformat() + "Z",
            "occurrence_count": occurrence_count,
            "files": sorted(set(files_with_secret))
        }
    
    # Phase 4: Tokenize files
    if not args.quiet:
        print("Phase 4: Tokenizing files...", file=sys.stderr)
    
    success_count = 0
    for file_path in files:
        if args.in_place:
            output_path = file_path
        else:
            output_path = output_dir / file_path.name
        
        if tokenize_file(file_path, output_path, secret_to_token):
            success_count += 1
            if args.verbose:
                print(f"  ✓ {output_path}", file=sys.stderr)
        else:
            print(f"  ✗ Failed: {file_path}", file=sys.stderr)
    
    # Phase 5: Save lookup table
    if not args.quiet:
        print("Phase 5: Saving lookup table...", file=sys.stderr)
    
    if save_lookup_table(lookup_table, lookup_table_path, args.verbose):
        if not args.quiet:
            print(f"✓ Tokenization complete!", file=sys.stderr)
            print(f"  Processed: {success_count}/{len(files)} file(s)", file=sys.stderr)
            print(f"  Lookup table: {lookup_table_path}", file=sys.stderr)
            if not args.in_place:
                print(f"  Output directory: {output_dir}", file=sys.stderr)
    else:
        print("ERROR: Failed to save lookup table", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
