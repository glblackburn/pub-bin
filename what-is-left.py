#!/usr/bin/env python3
"""
what-is-left.py - Compare files between old bin and pub-bin repositories

Shows a color-coded comparison of files:
- RED: Files in both places (need fixing)
- YELLOW: Files to migrate (old bin only)
- GREEN: Successfully migrated (moved files)
- BLUE: New files in pub-bin
"""

# Standard library imports
import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime
from collections import defaultdict

# Third-party imports
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: rich library not available. Install with: pip install rich", file=sys.stderr)

# Optional third-party imports
try:
    import git
    from git import Repo
    GITPYTHON_AVAILABLE = True
except ImportError:
    GITPYTHON_AVAILABLE = False
    # Will use subprocess to call git commands instead

################################################################################
# Configuration
################################################################################

EXCLUDE_PATTERNS = [
    r'__pycache__',
    r'\.pyc$',
    r'\.pyo$',
    r'\.DS_Store$',
    r'\.git',
    r'\.swp$',
    r'\.swo$',
    r'\.tmp$',
    r'\.log$',
    r'\.cache',
    r'\.pytest_cache',
    r'\.mypy_cache',
    r'\.coverage',
    r'\.tox',
    r'\.venv',
    r'venv/',
    r'node_modules/',
    r'\.idea/',
    r'\.vscode/',
    r'Thumbs\.db',
    r'\.png$',
    r'\.jpg$',
    r'\.jpeg$',
    r'\.gif$',
    r'\.svg$',
    r'\.mov$',
    r'\.mp4$',
    r'\.webm$',
    r'\.ico$',
    r'\.pdf$',
    r'\.zip$',
    r'\.tar\.gz$',
    r'\.tar$',
    r'\.gz$',
    r'\.bz2$',
    r'\.xz$',
    r'\.md$',  # Exclude markdown files (documentation)
    r'\.txt$',  # Exclude text files (documentation)
    r'\.json$',  # Exclude JSON config files
    r'\.yaml$',
    r'\.yml$',
    r'\.toml$',
    r'\.ini$',
    r'\.cfg$',
    r'\.conf$',
    r'LICENSE',
    r'CHANGELOG',
    r'CONTRIBUTING',
    r'AUTHORS',
    r'\.editorconfig',
    r'\.github/',
    r'\.gitlab-ci\.yml',
    r'\.travis\.yml',
    r'\.circleci/',
    r'\.env\.example',
    r'\.env\.template',
    r'\.sample',
    r'\.example',
    r'\.template',
    r'\.orig$',
    r'\.bak$',
    r'\.backup$',
    r'\.old$',
    r'\.test$',
    r'\.spec$',
    r'images/',
    r'LinkedIn-posts/',
]

################################################################################
# FileComparator Class
################################################################################

class FileComparator:
    """Main class for comparing files between directories"""
    
    def __init__(self, old_bin_path: Path, pub_bin_path: Path, verbose: bool = False):
        self.old_bin_path = Path(old_bin_path).resolve()
        self.pub_bin_path = Path(pub_bin_path).resolve()
        self.verbose = verbose
        self.console = Console() if RICH_AVAILABLE else None
        self.moved_files: Dict[Path, Tuple[Path, datetime]] = {}
        
    def should_exclude(self, file_path: Path) -> bool:
        """Check if file should be excluded from comparison"""
        file_str = str(file_path)
        
        # Check against exclude patterns
        for pattern in EXCLUDE_PATTERNS:
            if re.search(pattern, file_str):
                return True
        
        return False
    
    def discover_files(self, directory: Path) -> Set[Path]:
        """Discover all files in directory, excluding filtered ones"""
        files = set()
        
        if not directory.exists():
            return files
        
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    # Get relative path from directory
                    try:
                        rel_path = file_path.relative_to(directory)
                        if not self.should_exclude(rel_path):
                            files.add(rel_path)
                    except ValueError:
                        # File is outside directory, skip
                        continue
        except PermissionError:
            if self.verbose:
                print(f"Permission denied accessing {directory}", file=sys.stderr)
        
        return files
    
    def analyze_git_history(self) -> Dict[Path, Tuple[Path, datetime]]:
        """Analyze git history to find moved files"""
        moved_files = {}
        
        if not self.pub_bin_path.joinpath('.git').exists():
            return moved_files
        
        try:
            if GITPYTHON_AVAILABLE:
                repo = Repo(str(self.pub_bin_path))
                # Look for renames in git history
                for commit in repo.iter_commits():
                    for item in commit.stats.files:
                        # Check if this looks like a move from old bin
                        if '../bin' in item or 'bin/' in item:
                            # Try to find the actual rename
                            for diff in commit.diff(commit.parents[0] if commit.parents else None):
                                if diff.renamed:
                                    old_path = Path(diff.rename_from)
                                    new_path = Path(diff.rename_to)
                                    moved_files[new_path] = (old_path, commit.committed_datetime)
            else:
                # Use subprocess to call git
                try:
                    result = subprocess.run(
                        ['git', 'log', '--follow', '--name-status', '--format=%H|%ai|%s', '--diff-filter=R'],
                        cwd=str(self.pub_bin_path),
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        # Parse git log output
                        current_commit = None
                        current_date = None
                        for line in result.stdout.split('\n'):
                            if '|' in line:
                                parts = line.split('|')
                                if len(parts) >= 3:
                                    current_commit = parts[0]
                                    current_date = datetime.fromisoformat(parts[1].replace(' ', 'T', 1))
                            elif line.startswith('R'):
                                # Rename detected: R100 old_path new_path
                                parts = line.split('\t')
                                if len(parts) >= 3:
                                    old_path = Path(parts[1])
                                    new_path = Path(parts[2])
                                    if current_date:
                                        moved_files[new_path] = (old_path, current_date)
                except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                    pass
        except Exception as e:
            if self.verbose:
                print(f"Error analyzing git history: {e}", file=sys.stderr)
        
        self.moved_files = moved_files
        return moved_files
    
    def compare_files(self) -> Dict[str, List[Tuple[Path, Optional[str]]]]:
        """Compare files and categorize by state"""
        # Discover files
        old_files = self.discover_files(self.old_bin_path)
        pub_files = self.discover_files(self.pub_bin_path)
        
        # Analyze git history for moved files
        moved_files = self.analyze_git_history()
        
        # Categorize files
        results = {
            'in_both': [],      # RED - Files in both places
            'to_migrate': [],   # YELLOW - Files only in old bin
            'moved': [],        # GREEN - Files that were moved
            'new': []           # BLUE - Files only in pub-bin
        }
        
        # Find files in both places
        for file_path in old_files & pub_files:
            results['in_both'].append((file_path, None))
        
        # Find files to migrate (only in old bin)
        for file_path in old_files - pub_files:
            # Check if this file was moved
            if file_path in moved_files:
                old_path, move_date = moved_files[file_path]
                results['moved'].append((file_path, move_date.strftime('%Y-%m-%d')))
            else:
                results['to_migrate'].append((file_path, None))
        
        # Find new files (only in pub-bin)
        for file_path in pub_files - old_files:
            # Check if this was a moved file
            if file_path in moved_files:
                old_path, move_date = moved_files[file_path]
                results['moved'].append((file_path, move_date.strftime('%Y-%m-%d')))
            else:
                results['new'].append((file_path, None))
        
        return results
    
    def get_file_type(self, file_path: Path) -> str:
        """Get file type category"""
        name = file_path.name
        
        # Scripts
        if re.search(r'\.(sh|bash|zsh|fish|py|pl|rb|php|js|ts|go|rs|java|scala|kt|swift|m|mm|c|cc|cpp|cxx|h|hpp|hxx)$', name, re.IGNORECASE):
            return 'script'
        # Makefiles
        elif name.lower() in ('makefile', 'gnumakefile') or file_path.name == 'Makefile':
            return 'makefile'
        # Executables (no extension, likely executable)
        elif not file_path.suffix and name[0].isupper():
            return 'executable'
        # Config files
        elif re.search(r'\.(env|config)$', name, re.IGNORECASE) or name.startswith('.'):
            return 'config'
        else:
            return 'other'
    
    def categorize_files(self, files: List[Tuple[Path, Optional[str]]]) -> Dict[str, List[Tuple[Path, Optional[str]]]]:
        """Categorize files by type"""
        categories = defaultdict(list)
        for file_path, extra_info in files:
            file_type = self.get_file_type(file_path)
            categories[file_type].append((file_path, extra_info))
        return dict(categories)
    
    def print_summary(self, results: Dict[str, List[Tuple[Path, Optional[str]]]], 
                     show_new: bool = True, quiet: bool = False):
        """Print color-coded summary using rich"""
        if not self.console:
            # Fallback to plain text
            self._print_plain_summary(results, show_new, quiet)
            return
        
        # Calculate statistics
        total_old = len(results['to_migrate']) + len(results['in_both']) + len([f for f, _ in results['moved'] if f not in results['in_both']])
        total_pub = len(results['new']) + len(results['in_both']) + len(results['moved'])
        in_both_count = len(results['in_both'])
        to_migrate_count = len(results['to_migrate'])
        moved_count = len(results['moved'])
        new_count = len(results['new'])
        
        # Calculate progress (moved files / total files that needed migration)
        total_needed = to_migrate_count + moved_count + in_both_count
        if total_needed > 0:
            progress_pct = int((moved_count / total_needed) * 100)
        else:
            progress_pct = 100
        
        if not quiet:
            # Print summary panel
            summary_text = f"""
Files in old repository (../bin):     {total_old}
Files in current repository (pub-bin): {total_pub}
Files in both (need fixing):          {in_both_count} 🔴
Files to migrate (old bin only):       {to_migrate_count} 🟡
Files successfully migrated:          {moved_count} 🟢
New files in pub-bin:                  {new_count} 🔵

Progress: {progress_pct}% migrated ({moved_count} of {total_needed} files)
"""
            self.console.print(Panel(summary_text.strip(), title="Migration Status Summary", border_style="cyan"))
        
        # Print files in both places (RED)
        if results['in_both']:
            self.console.print()
            files_text = "\n".join([f"  {str(f[0])}" for f in results['in_both']])
            self.console.print(Panel(files_text, title=f"🔴 Files in Both Places (Need Fixing) - {len(results['in_both'])} files", border_style="red"))
        
        # Print files to migrate (YELLOW)
        if results['to_migrate']:
            self.console.print()
            categorized = self.categorize_files(results['to_migrate'])
            
            files_text_parts = []
            for category in ['script', 'executable', 'makefile', 'config', 'other']:
                if category in categorized:
                    files = categorized[category]
                    files_text_parts.append(f"\n{category.capitalize()}s ({len(files)}):")
                    for file_path, _ in sorted(files):
                        files_text_parts.append(f"  {file_path}")
            
            files_text = "\n".join(files_text_parts)
            self.console.print(Panel(files_text, title=f"🟡 Files to Migrate (Old Bin Only) - {len(results['to_migrate'])} files", border_style="yellow"))
        
        # Print moved files (GREEN)
        if results['moved']:
            self.console.print()
            files_text = "\n".join([f"  {str(f[0])} (moved {f[1]})" if f[1] else f"  {str(f[0])} (moved)" for f in sorted(results['moved'])])
            self.console.print(Panel(files_text, title=f"🟢 Successfully Migrated (Moved Files) - {len(results['moved'])} files", border_style="green"))
        
        # Print new files (BLUE)
        if show_new and results['new']:
            self.console.print()
            files_text = "\n".join([f"  {str(f[0])}" for f in sorted(results['new'])])
            self.console.print(Panel(files_text, title=f"🔵 New Files in Pub-Bin - {len(results['new'])} files", border_style="blue"))
        
        self.console.print()
    
    def _print_plain_summary(self, results: Dict[str, List[Tuple[Path, Optional[str]]]], 
                             show_new: bool = True, quiet: bool = False):
        """Fallback plain text output when rich is not available"""
        total_old = len(results['to_migrate']) + len(results['in_both']) + len(results['moved'])
        total_pub = len(results['new']) + len(results['in_both']) + len(results['moved'])
        
        print("=" * 80)
        print("Migration Status Summary")
        print("=" * 80)
        print(f"Files in old repository (../bin):     {total_old}")
        print(f"Files in current repository (pub-bin): {total_pub}")
        print(f"Files in both (need fixing):          {len(results['in_both'])}")
        print(f"Files to migrate (old bin only):     {len(results['to_migrate'])}")
        print(f"Files successfully migrated:         {len(results['moved'])}")
        print(f"New files in pub-bin:                {len(results['new'])}")
        print()
        
        if results['in_both']:
            print("=" * 80)
            print(f"Files in Both Places (Need Fixing) - {len(results['in_both'])} files")
            print("=" * 80)
            for file_path, _ in results['in_both']:
                print(f"  {file_path}")
            print()
        
        if results['to_migrate']:
            print("=" * 80)
            print(f"Files to Migrate (Old Bin Only) - {len(results['to_migrate'])} files")
            print("=" * 80)
            categorized = self.categorize_files(results['to_migrate'])
            for category in ['script', 'executable', 'makefile', 'config', 'other']:
                if category in categorized:
                    print(f"\n{category.capitalize()}s ({len(categorized[category])}):")
                    for file_path, _ in sorted(categorized[category]):
                        print(f"  {file_path}")
            print()
        
        if results['moved']:
            print("=" * 80)
            print(f"Successfully Migrated (Moved Files) - {len(results['moved'])} files")
            print("=" * 80)
            for file_path, date_str in sorted(results['moved']):
                if date_str:
                    print(f"  {file_path} (moved {date_str})")
                else:
                    print(f"  {file_path} (moved)")
            print()
        
        if show_new and results['new']:
            print("=" * 80)
            print(f"New Files in Pub-Bin - {len(results['new'])} files")
            print("=" * 80)
            for file_path, _ in sorted(results['new']):
                print(f"  {file_path}")
            print()

################################################################################
# Main Function
################################################################################

def main():
    parser = argparse.ArgumentParser(
        description='Compare files between old bin and pub-bin repositories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Color coding:
  🔴 RED   - Files in both places (need fixing)
  🟡 YELLOW - Files to migrate (old bin only)
  🟢 GREEN  - Successfully migrated (moved files)
  🔵 BLUE   - New files in pub-bin
        """
    )
    parser.add_argument('--verbose', action='store_true', 
                       help='Show verbose output including errors')
    parser.add_argument('--quiet', action='store_true', 
                       help='Show summary statistics only')
    parser.add_argument('--no-new', action='store_true', 
                       help='Hide new files in pub-bin section')
    parser.add_argument('--old-bin', type=str, default='../bin',
                       help='Path to old bin directory (default: ../bin)')
    parser.add_argument('--pub-bin', type=str, default='.',
                       help='Path to pub-bin directory (default: .)')
    
    args = parser.parse_args()
    
    # Validate paths
    old_bin = Path(args.old_bin).resolve()
    pub_bin = Path(args.pub_bin).resolve()
    
    if not old_bin.exists():
        print(f"Error: Old bin directory not found: {old_bin}", file=sys.stderr)
        sys.exit(1)
    
    if not pub_bin.exists():
        print(f"Error: Pub-bin directory not found: {pub_bin}", file=sys.stderr)
        sys.exit(1)
    
    # Create comparator and run
    comparator = FileComparator(old_bin, pub_bin, verbose=args.verbose)
    results = comparator.compare_files()
    comparator.print_summary(results, show_new=not args.no_new, quiet=args.quiet)

if __name__ == '__main__':
    main()
