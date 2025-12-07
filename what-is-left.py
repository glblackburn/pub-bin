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
import json
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

TRACKING_FILE_NAME = '.migration-tracking.json'

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
        self.tracking_file = self.old_bin_path / TRACKING_FILE_NAME
        
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
    
    def load_tracking_file(self) -> Dict[str, Dict[str, str]]:
        """Load migration tracking file from old bin directory"""
        if not self.tracking_file.exists():
            return {}
        
        try:
            with open(self.tracking_file, 'r') as f:
                data = json.load(f)
                return data.get('migrations', {})
        except (json.JSONDecodeError, IOError) as e:
            if self.verbose:
                print(f"Error loading tracking file: {e}", file=sys.stderr)
            return {}
    
    def save_tracking_file(self, migrations: Dict[str, Dict[str, str]]):
        """Save migration tracking file to old bin directory"""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'migrations': migrations
            }
            with open(self.tracking_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            if self.verbose:
                print(f"Error saving tracking file: {e}", file=sys.stderr)
    
    def get_last_migration_date(self, tracking_data: Dict[str, Dict[str, str]]) -> Optional[datetime]:
        """Get the most recent migration date from tracking file"""
        if not tracking_data:
            return None
        
        dates = []
        for migration in tracking_data.values():
            if 'date' in migration:
                try:
                    dates.append(datetime.fromisoformat(migration['date']))
                except (ValueError, TypeError):
                    continue
        
        return max(dates) if dates else None
    
    def analyze_git_history_pub_bin(self, since_date: Optional[datetime] = None) -> Dict[Path, Tuple[Path, datetime]]:
        """Analyze git history in pub-bin repository"""
        moved_files = {}
        
        if not self.pub_bin_path.joinpath('.git').exists():
            return moved_files
        
        try:
            # Build git log command with date filter if provided
            cmd = ['git', 'log', '--name-status', '--format=%H|%ai|%s', '--diff-filter=R']
            if since_date:
                cmd.extend(['--since', since_date.isoformat()])
            
            result = subprocess.run(
                cmd,
                cwd=str(self.pub_bin_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                current_date = None
                for line in result.stdout.split('\n'):
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            try:
                                current_date = datetime.fromisoformat(parts[1].replace(' ', 'T', 1))
                            except ValueError:
                                continue
                    elif line.startswith('R'):
                        # Rename detected: R100 old_path new_path
                        parts = line.split('\t')
                        if len(parts) >= 3 and current_date:
                            old_path = Path(parts[1])
                            new_path = Path(parts[2])
                            moved_files[new_path] = (old_path, current_date)
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            if self.verbose:
                print(f"Error analyzing pub-bin git history: {e}", file=sys.stderr)
        
        return moved_files
    
    def analyze_git_history_old_bin(self, since_date: Optional[datetime] = None) -> Dict[str, datetime]:
        """Analyze git history in old bin repository to find when files were added/modified"""
        file_dates = {}
        
        if not self.old_bin_path.joinpath('.git').exists():
            return file_dates
        
        try:
            # Get file modification dates from git log
            # Use --all to get all branches, --reverse to get chronological order
            cmd = ['git', 'log', '--all', '--format=%ai|%H', '--name-only', '--reverse', '--diff-filter=A']
            if since_date:
                cmd.extend(['--since', since_date.isoformat()])
            
            result = subprocess.run(
                cmd,
                cwd=str(self.old_bin_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                current_date = None
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    # Check if it's a date line (format: YYYY-MM-DD HH:MM:SS +TZ|hash)
                    if '|' in line:
                        try:
                            date_part = line.split('|')[0]
                            current_date = datetime.fromisoformat(date_part.replace(' ', 'T', 1))
                        except (ValueError, IndexError):
                            continue
                    else:
                        # It's a filename
                        if current_date and line and not line.startswith('commit'):
                            # Only record the first (earliest) date for each file
                            if line not in file_dates:
                                file_dates[line] = current_date
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            if self.verbose:
                print(f"Error analyzing old-bin git history: {e}", file=sys.stderr)
        
        return file_dates
    
    def find_name_based_matches(self, old_files: Set[Path], pub_files: Set[Path], 
                                old_bin_file_dates: Dict[str, datetime],
                                pub_bin_file_dates: Dict[Path, datetime]) -> Dict[Path, Tuple[Path, datetime]]:
        """Use name-based heuristic to find migrated files"""
        matches = {}
        
        # Create filename to path mapping for old files
        # Handle multiple files with same name by using relative path
        old_file_map = {}
        for old_path in old_files:
            filename = old_path.name
            # Use relative path as key to handle same-named files in different dirs
            rel_path_str = str(old_path).replace('\\', '/')
            if filename not in old_file_map:
                old_file_map[filename] = []
            old_file_map[filename].append((old_path, rel_path_str))
        
        # Check each pub file against old files by name
        for pub_path in pub_files:
            filename = pub_path.name
            pub_rel_path_str = str(pub_path).replace('\\', '/')
            
            if filename in old_file_map:
                # Found files with the same name - try to match by relative path first
                best_match = None
                best_match_path = None
                
                for old_path, old_rel_path_str in old_file_map[filename]:
                    # Prefer exact path match
                    if pub_rel_path_str == old_rel_path_str:
                        best_match = old_path
                        best_match_path = old_rel_path_str
                        break
                    # Otherwise use first match
                    elif best_match is None:
                        best_match = old_path
                        best_match_path = old_rel_path_str
                
                if best_match:
                    # Try to determine migration date
                    migration_date = None
                    
                    # Check pub-bin git history for when this file appeared
                    if pub_path in pub_bin_file_dates:
                        migration_date = pub_bin_file_dates[pub_path]
                    else:
                        # Use old bin file date as fallback
                        if best_match_path in old_bin_file_dates:
                            migration_date = old_bin_file_dates[best_match_path]
                        else:
                            # Use current date as last resort
                            migration_date = datetime.now()
                    
                    matches[pub_path] = (best_match, migration_date)
        
        return matches
    
    def analyze_git_history(self) -> Dict[Path, Tuple[Path, datetime]]:
        """Analyze git history from both repositories to find moved files"""
        # Load existing tracking data
        tracking_data = self.load_tracking_file()
        last_migration_date = self.get_last_migration_date(tracking_data)
        
        if self.verbose and last_migration_date:
            print(f"Last migration date in tracking file: {last_migration_date.isoformat()}", file=sys.stderr)
        
        moved_files = {}
        
        # Analyze pub-bin git history (for explicit renames)
        pub_bin_moves = self.analyze_git_history_pub_bin(since_date=last_migration_date)
        moved_files.update(pub_bin_moves)
        
        # Get file dates from both repositories for name-based matching
        old_bin_file_dates = {}
        pub_bin_file_dates = {}
        
        if self.old_bin_path.joinpath('.git').exists():
            old_bin_file_dates = self.analyze_git_history_old_bin(since_date=last_migration_date)
        
        if self.pub_bin_path.joinpath('.git').exists():
            # Get file addition dates from pub-bin
            try:
                result = subprocess.run(
                    ['git', 'log', '--format=%ai', '--name-only', '--reverse', '--diff-filter=A'],
                    cwd=str(self.pub_bin_path),
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    current_date = None
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            current_date = datetime.fromisoformat(line.replace(' ', 'T', 1))
                        except ValueError:
                            if current_date and line:
                                pub_bin_file_dates[Path(line)] = current_date
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass
        
        # Use name-based heuristic for files not found via git renames
        # This will be called after we have the file lists
        self.old_bin_file_dates = old_bin_file_dates
        self.pub_bin_file_dates = pub_bin_file_dates
        
        self.moved_files = moved_files
        return moved_files
    
    def normalize_filename(self, filename: str) -> str:
        """Normalize filename for matching (convert underscores to hyphens, lowercase)"""
        return filename.lower().replace('_', '-')
    
    def retro_calculate_migrations(self) -> Dict[str, Dict[str, str]]:
        """Retroactively calculate all migrations from git history of both repos
        
        Always searches full git history (no date filtering).
        Use --force-recalculate to clear existing tracking file first.
        """
        if self.verbose:
            print("Retroactively calculating migrations from full git history...", file=sys.stderr)
        
        migrations = {}
        
        # Get all files that ever existed in pub-bin git history
        pub_bin_all_files = {}
        if self.pub_bin_path.joinpath('.git').exists():
            try:
                result = subprocess.run(
                    ['git', 'log', '--all', '--full-history', '--format=%ai|%H', '--name-only', '--reverse', '--diff-filter=A'],
                    cwd=str(self.pub_bin_path),
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode == 0:
                    current_date = None
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        if '|' in line:
                            try:
                                date_part = line.split('|')[0]
                                current_date = datetime.fromisoformat(date_part.replace(' ', 'T', 1))
                            except (ValueError, IndexError):
                                continue
                        else:
                            # It's a filename - filter out non-script files
                            if current_date and line and not self.should_exclude(Path(line)):
                                file_path = Path(line)
                                # Only record the first (earliest) date for each file
                                if file_path not in pub_bin_all_files:
                                    pub_bin_all_files[file_path] = current_date
            except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
                if self.verbose:
                    print(f"Error getting pub-bin file dates: {e}", file=sys.stderr)
        
        # Get all files that ever existed in old bin git history
        old_bin_all_files = {}
        old_bin_by_normalized = {}  # Index by normalized name for matching
        if self.old_bin_path.joinpath('.git').exists():
            try:
                result = subprocess.run(
                    ['git', 'log', '--all', '--full-history', '--format=%ai|%H', '--name-only', '--reverse', '--diff-filter=A'],
                    cwd=str(self.old_bin_path),
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode == 0:
                    current_date = None
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        if '|' in line:
                            try:
                                date_part = line.split('|')[0]
                                current_date = datetime.fromisoformat(date_part.replace(' ', 'T', 1))
                            except (ValueError, IndexError):
                                continue
                        else:
                            # It's a filename - filter out non-script files
                            if current_date and line and not self.should_exclude(Path(line)):
                                # Store by filename for matching
                                file_path = Path(line)
                                filename = file_path.name
                                normalized = self.normalize_filename(filename)
                                
                                # Store earliest date for each filename (exact match)
                                if filename not in old_bin_all_files:
                                    old_bin_all_files[filename] = {
                                        'path': str(file_path).replace('\\', '/'),
                                        'date': current_date
                                    }
                                
                                # Store earliest date for normalized name (for underscore/hyphen matching)
                                if normalized not in old_bin_by_normalized:
                                    old_bin_by_normalized[normalized] = {
                                        'path': str(file_path).replace('\\', '/'),
                                        'date': current_date,
                                        'original_name': filename
                                    }
            except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
                if self.verbose:
                    print(f"Error getting old-bin file dates: {e}", file=sys.stderr)
        
        # Match files by filename (exact and normalized)
        for pub_path, pub_date in pub_bin_all_files.items():
            filename = pub_path.name
            normalized = self.normalize_filename(filename)
            matched = False
            
            # Try exact match first
            if filename in old_bin_all_files:
                old_info = old_bin_all_files[filename]
                old_date = old_info['date']
                old_path = old_info['path']
                
                # If file was added to pub-bin after it existed in old bin, it's a migration
                if pub_date > old_date:
                    pub_path_str = str(pub_path).replace('\\', '/')
                    migrations[pub_path_str] = {
                        'old_path': old_path,
                        'new_path': pub_path_str,
                        'date': pub_date.isoformat(),
                        'old_date': old_date.isoformat(),
                        'detected_date': datetime.now().isoformat(),
                        'method': 'retro_calculation'
                    }
                    matched = True
            
            # Try normalized match (for underscore/hyphen differences)
            if not matched and normalized in old_bin_by_normalized:
                old_info = old_bin_by_normalized[normalized]
                old_date = old_info['date']
                old_path = old_info['path']
                
                # If file was added to pub-bin after it existed in old bin, it's a migration
                if pub_date > old_date:
                    pub_path_str = str(pub_path).replace('\\', '/')
                    migrations[pub_path_str] = {
                        'old_path': old_path,
                        'new_path': pub_path_str,
                        'date': pub_date.isoformat(),
                        'old_date': old_date.isoformat(),
                        'detected_date': datetime.now().isoformat(),
                        'method': 'retro_calculation_normalized'
                    }
        
        if self.verbose:
            print(f"Found {len(migrations)} potential migrations from git history", file=sys.stderr)
        
        return migrations
    
    def compare_files(self) -> Dict[str, List[Tuple[Path, Optional[str]]]]:
        """Compare files and categorize by state"""
        # Discover files
        old_files = self.discover_files(self.old_bin_path)
        pub_files = self.discover_files(self.pub_bin_path)
        
        # Load tracking data first (includes retro-calculated migrations)
        tracking_data = self.load_tracking_file()
        
        # Build moved_files from tracking data
        moved_files = {}
        for new_path_str, migration_info in tracking_data.items():
            new_path = Path(new_path_str)
            if 'date' in migration_info:
                try:
                    move_date = datetime.fromisoformat(migration_info['date'])
                    old_path = Path(migration_info.get('old_path', ''))
                    moved_files[new_path] = (old_path, move_date)
                except (ValueError, KeyError):
                    continue
        
        # Analyze git history for additional moved files (not in tracking)
        git_moved_files = self.analyze_git_history()
        
        # Merge git history matches (only if not already tracked)
        for pub_path, (old_path, move_date) in git_moved_files.items():
            pub_path_str = str(pub_path).replace('\\', '/')
            if pub_path_str not in tracking_data:
                moved_files[pub_path] = (old_path, move_date)
        
        # Apply name-based heuristic for files not found via git renames or tracking
        name_based_matches = self.find_name_based_matches(
            old_files, pub_files,
            getattr(self, 'old_bin_file_dates', {}),
            getattr(self, 'pub_bin_file_dates', {})
        )
        
        # Merge name-based matches (only if not already in moved_files or tracking)
        for pub_path, (old_path, move_date) in name_based_matches.items():
            pub_path_str = str(pub_path).replace('\\', '/')
            if pub_path not in moved_files and pub_path_str not in tracking_data:
                moved_files[pub_path] = (old_path, move_date)
        
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
            # Check if this file was moved (by git rename or name match)
            if file_path in moved_files:
                old_path, move_date = moved_files[file_path]
                results['moved'].append((file_path, move_date.strftime('%Y-%m-%d')))
            else:
                results['to_migrate'].append((file_path, None))
        
        # Find new files (only in pub-bin)
        new_migrations = {}
        for file_path in pub_files - old_files:
            # Check if this was a moved file (by git rename or name match)
            file_str = str(file_path).replace('\\', '/')
            if file_path in moved_files:
                old_path, move_date = moved_files[file_path]
                date_str = move_date.strftime('%Y-%m-%d')
                results['moved'].append((file_path, date_str))
                
                # Record new migration for tracking file (if not already tracked)
                if file_str not in tracking_data:
                    new_migrations[file_str] = {
                        'old_path': str(old_path).replace('\\', '/'),
                        'new_path': file_str,
                        'date': move_date.isoformat(),
                        'detected_date': datetime.now().isoformat()
                    }
            else:
                results['new'].append((file_path, None))
        
        # Update tracking file with new migrations
        if new_migrations:
            tracking_data.update(new_migrations)
            self.save_tracking_file(tracking_data)
            if self.verbose:
                print(f"Updated tracking file with {len(new_migrations)} new migrations", file=sys.stderr)
        
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
    parser.add_argument('--retro-calculate', action='store_true',
                       help='Retroactively calculate all migrations from git history and update tracking file')
    parser.add_argument('--force-recalculate', action='store_true',
                       help='Force full recalculation from scratch, ignoring existing tracking file')
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
    
    # Force recalculation from scratch if requested
    if args.force_recalculate:
        if comparator.tracking_file.exists():
            # Backup existing tracking file
            backup_file = comparator.tracking_file.with_suffix('.json.backup')
            import shutil
            shutil.copy2(comparator.tracking_file, backup_file)
            if not args.quiet:
                print(f"Backed up existing tracking file to: {backup_file}", file=sys.stderr)
            
            # Clear tracking file before recalculation
            comparator.tracking_file.unlink()
            if args.verbose:
                print("Cleared existing tracking file for full recalculation", file=sys.stderr)
        
        # Recalculate from full history (no existing tracking file to limit search)
        migrations = comparator.retro_calculate_migrations()
        comparator.save_tracking_file(migrations)
        if not args.quiet:
            print(f"\nForce recalculated {len(migrations)} migrations from full git history")
            print(f"Tracking file updated: {comparator.tracking_file}")
    
    # Retroactively calculate migrations if requested (incremental - adds new ones)
    elif args.retro_calculate:
        # Get existing migrations
        existing = comparator.load_tracking_file()
        existing_count = len(existing)
        
        # Recalculate from full history
        migrations = comparator.retro_calculate_migrations()
        
        # Merge with existing (new ones will overwrite if same key, but that's fine)
        existing.update(migrations)
        comparator.save_tracking_file(existing)
        
        new_count = len(existing) - existing_count
        if not args.quiet:
            if new_count > 0:
                print(f"\nRetroactively calculated {new_count} new migrations from git history")
            else:
                print(f"\nNo new migrations found (all {len(existing)} already tracked)")
            print(f"Total migrations in tracking file: {len(existing)}")
            print(f"Tracking file updated: {comparator.tracking_file}")
    
    results = comparator.compare_files()
    comparator.print_summary(results, show_new=not args.no_new, quiet=args.quiet)

if __name__ == '__main__':
    main()
