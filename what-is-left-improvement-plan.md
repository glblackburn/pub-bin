# what-is-left.sh → what-is-left.py Improvement Plan

## Current State Analysis

### What the Script Currently Does

The bash script compares files between two directories:
- **Current directory** (`pub-bin`): The public repository
- **Old directory** (`../bin`): The old private repository

**Current Output:**
1. Lists ALL files in `pub-bin` (excluding `.git`)
2. Lists ALL files in `../bin` (excluding `.git`)
3. Shows a raw `diff` output indicating:
   - Files in old repo but not in pub-bin (prefixed with `<`)
   - Files in pub-bin but not in old repo (prefixed with `>`)

### Problems with Current Implementation

1. **Too Much Noise**
   - Includes cache files (`__pycache__`, `.pyc`, `.pyo`)
   - Includes system files (`.DS_Store`)
   - Includes images (`.png`, `.jpg`, `.gif`, `.mov`, etc.)
   - Includes documentation (`.md`, `.txt`)
   - Includes build artifacts and temporary files
   - Makes it hard to see what actually needs to be migrated

2. **Raw Output Format**
   - Uses basic `diff` output which is not user-friendly
   - No summary statistics
   - No categorization
   - No clear indication of what's important vs. what's not
   - No color coding

3. **No Context**
   - Doesn't show file types (scripts vs. configs vs. other)
   - Doesn't show what exists in both places (needs fixing)
   - Doesn't show what has moved (using git history)
   - Doesn't distinguish between essential and non-essential files

4. **Missing Features**
   - No way to detect files that exist in both places (duplicates that need fixing)
   - No git history analysis to detect moved files
   - No color coding for different file states
   - No summary statistics

## Goals for Improvement

### Primary Goals

1. **Easy Comparison Output**
   - **RED**: Files that exist in both places (need to be fixed/removed from old repo)
   - **YELLOW/ORANGE**: Files still in old bin folder (need to be migrated)
   - **GREEN**: Files that have moved from bin to pub (detected via git history)
   - **BLUE/CYAN**: New files in pub-bin (not in old repo)

2. **Better Output Format**
   - Rich color-coded output using Python color libraries
   - Summary statistics at the top
   - Clear visual separation between sections
   - Easy to scan and understand at a glance

3. **Git History Analysis**
   - Detect files that have moved from `../bin` to `pub-bin` using git history
   - Show when files were moved
   - Help identify migration progress

### Secondary Goals

1. **Flexibility**
   - Option to show/hide new files
   - Option to include/exclude specific file types
   - Option for verbose mode (show all files)
   - Option for quiet mode (summary only)

2. **Maintainability**
   - Clear Python code structure
   - Well-documented
   - Easy to extend with new features

## Proposed Solution: Python Implementation

### Technology Stack

- **Language**: Python 3.8+
- **Color Library**: `rich` (recommended) or `colorama` + `termcolor`
  - `rich` provides tables, panels, progress bars, and beautiful formatting
  - Alternative: `colorama` for cross-platform color support
- **Git Integration**: `GitPython` library or subprocess calls to `git`
- **File Operations**: `pathlib` for modern path handling

### File States and Color Coding

1. **🔴 RED - Files in Both Places (Need Fixing)**
   - Files that exist in both `../bin` and `pub-bin`
   - These are duplicates that need to be removed from old repo or consolidated
   - **Action**: Review and remove from old repo

2. **🟡 YELLOW - Files to Migrate (In Old Bin Only)**
   - Files that exist in `../bin` but not in `pub-bin`
   - These need to be migrated
   - **Action**: Migrate to pub-bin

3. **🟢 GREEN - Successfully Migrated (Moved Files)**
   - Files that were in `../bin` and are now in `pub-bin`
   - Detected via git history analysis
   - **Action**: None (already done)

4. **🔵 BLUE - New Files (In Pub-Bin Only)**
   - Files that exist in `pub-bin` but not in `../bin`
   - These are new additions
   - **Action**: None (already in place)

### File Filtering Strategy

**Exclude by Default:**
- Cache files: `__pycache__`, `.pyc`, `.pyo`, `.cache`, `.pytest_cache`, etc.
- System files: `.DS_Store`, `Thumbs.db`, `.swp`, `.swo`, `.tmp`
- Images/media: `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.mov`, `.mp4`, etc.
- Documentation: `.md`, `.txt` (unless they're README files in root)
- Build artifacts: `.o`, `.so`, `.dylib`, `.a`, `.class`, `.jar`, etc.
- Config files: `.json`, `.yaml`, `.yml`, `.toml`, `.ini`, `.cfg`, `.conf` (unless in config dirs)
- Temporary/backup: `.orig`, `.bak`, `.backup`, `.old`, `.test`
- IDE files: `.idea/`, `.vscode/`, `.swiftpm/`
- Package managers: `node_modules/`, `venv/`, `.venv/`, `.tox/`
- Git-related: `.gitignore`, `.gitkeep` (already excluding `.git/`)

**Include by Default:**
- Scripts: `.sh`, `.bash`, `.zsh`, `.fish`, `.py`, `.pl`, `.rb`, etc.
- Executables: Files without extensions that are likely executables
- Makefiles: `Makefile`, `makefile`, `GNUmakefile`
- Important configs: Files in specific config directories

### Output Format Design

Using `rich` library for beautiful output:

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    Migration Status Summary                                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Files in old repository (../bin):    118
Files in current repository (pub-bin): 39
Files in both (need fixing):           12  🔴
Files to migrate (old bin only):       79  🟡
Files successfully migrated:          27  🟢
New files in pub-bin:                  12  🔵

Progress: 23% migrated (27 of 106 files)

╔═══════════════════════════════════════════════════════════════════════════════╗
║  🔴 Files in Both Places (Need Fixing) - 12 files                           ║
╚═══════════════════════════════════════════════════════════════════════════════╝

  ./load-ssh-key.sh
  ./clean-screenshots.sh
  ./monitor-ai-agent-progress.sh
  ...

╔═══════════════════════════════════════════════════════════════════════════════╗
║  🟡 Files to Migrate (Old Bin Only) - 79 files                              ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Scripts (65):
  ./arrays.sh
  ./backup-wrapper.sh
  ./backup.sh
  ...

Executables (3):
  ./some-binary
  ...

╔═══════════════════════════════════════════════════════════════════════════════╗
║  🟢 Successfully Migrated (Moved Files) - 27 files                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝

  ./load-ssh-key.sh (moved 2025-11-05)
  ./clean-screenshots.sh (moved 2025-11-11)
  ...

╔═══════════════════════════════════════════════════════════════════════════════╗
║  🔵 New Files in Pub-Bin - 12 files                                         ║
╚═══════════════════════════════════════════════════════════════════════════════╝

  ./what-is-left.py (new)
  ./shell-template.sh (new)
  ...
```

### Implementation Approach

#### Phase 1: Basic Python Structure and File Discovery
- Create Python script with proper structure
- Implement file discovery for both directories
- Implement file filtering
- Basic output (no colors yet)
- Test with current repositories

#### Phase 2: Git History Analysis
- Integrate GitPython or subprocess git calls
- Detect moved files by analyzing git history
- Match files between old and new locations
- Store move dates and paths

#### Phase 3: File State Detection
- Compare files between directories
- Identify files in both places
- Identify files only in old bin
- Identify files only in pub-bin
- Cross-reference with git history to detect moves

#### Phase 4: Rich Color Output
- Install and configure `rich` library
- Create color-coded sections for each file state
- Format summary statistics
- Add progress indicators
- Add emoji/icons for visual clarity

#### Phase 5: Enhanced Features
- Add CLI options (`--verbose`, `--quiet`, `--no-new`)
- Add filtering options
- Add table view option
- Add export to file option

### Code Structure

```python
#!/usr/bin/env python3
"""
what-is-left.py - Compare files between old bin and pub-bin repositories
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

# Configuration
EXCLUDE_PATTERNS = [
    r'__pycache__',
    r'\.pyc$',
    r'\.pyo$',
    r'\.DS_Store$',
    # ... more patterns
]

class FileComparator:
    """Main class for comparing files between directories"""
    
    def __init__(self, old_bin_path: Path, pub_bin_path: Path):
        self.old_bin_path = old_bin_path
        self.pub_bin_path = pub_bin_path
        self.console = Console() if RICH_AVAILABLE else None
        
    def should_exclude(self, file_path: Path) -> bool:
        """Check if file should be excluded from comparison"""
        # Implementation
        
    def discover_files(self, directory: Path) -> Set[Path]:
        """Discover all files in directory, excluding filtered ones"""
        # Implementation
        
    def analyze_git_history(self) -> Dict[Path, Tuple[Path, datetime]]:
        """Analyze git history to find moved files"""
        # Implementation
        
    def compare_files(self) -> Dict[str, List[Path]]:
        """Compare files and categorize by state"""
        # Implementation
        
    def print_summary(self, results: Dict[str, List[Path]]):
        """Print color-coded summary using rich"""
        # Implementation

def main():
    parser = argparse.ArgumentParser(description='Compare files between old bin and pub-bin')
    parser.add_argument('--verbose', action='store_true', help='Show all files')
    parser.add_argument('--quiet', action='store_true', help='Summary only')
    parser.add_argument('--no-new', action='store_true', help='Hide new files')
    args = parser.parse_args()
    
    old_bin = Path('../bin')
    pub_bin = Path('.')
    
    comparator = FileComparator(old_bin, pub_bin)
    results = comparator.compare_files()
    comparator.print_summary(results)

if __name__ == '__main__':
    main()
```

### Git History Analysis Strategy

To detect moved files:

1. **Check git log for renames:**
   ```bash
   git log --follow --name-status --format="%H|%ai|%s" --diff-filter=R
   ```

2. **Check for files that existed in old location:**
   - Look for commits that mention files from `../bin`
   - Track when they appeared in `pub-bin`

3. **Match by content hash (if available):**
   - Compare file contents between old and new locations
   - If identical, likely a move

4. **Match by filename:**
   - Simple filename matching (less reliable but faster)
   - Works for files that kept same name

### Libraries and Dependencies

#### Standard Library (Built-in, No Installation Required)

These are part of Python's standard library:

- **`pathlib`** - Modern path handling and file system operations
- **`argparse`** - Command-line argument parsing
- **`subprocess`** - Running git commands (alternative to GitPython)
- **`re`** - Regular expressions for pattern matching in file filtering
- **`typing`** - Type hints for better code documentation and IDE support
- **`collections`** - `defaultdict` for categorizing files
- **`datetime`** - Date/time handling for git history timestamps
- **`os`** - Operating system interface (if needed for path operations)
- **`sys`** - System-specific parameters and functions

#### Third-Party Libraries (Required)

These must be installed via pip:

- **`rich`** (v13.0.0+)
  - **Purpose**: Beautiful terminal output with colors, tables, panels, and formatting
  - **Features Used**:
    - `Console` - Colored terminal output
    - `Table` - Formatted tables for file listings
    - `Panel` - Bordered sections for different file states
    - `Text` - Colored text formatting
    - Progress bars and status indicators
  - **Installation**: `pip install rich`
  - **Why**: Provides the best cross-platform color support and beautiful formatting

#### Third-Party Libraries (Optional)

These enhance functionality but have fallbacks:

- **`GitPython`** (v3.1.0+)
  - **Purpose**: Pythonic interface to Git repositories
  - **Features Used**:
    - `Repo` - Access git repository information
    - `Commit` - Analyze commit history
    - `Diff` - Compare file changes
  - **Installation**: `pip install GitPython`
  - **Fallback**: If not available, use `subprocess` to call `git` commands directly
  - **Why**: More reliable git history analysis, but `subprocess` works fine for basic needs

- **`colorama`** (v0.4.0+)
  - **Purpose**: Cross-platform colored terminal text
  - **Installation**: `pip install colorama`
  - **Fallback**: Only needed if `rich` is not available (not recommended)
  - **Why**: `rich` includes colorama functionality, so this is only a last resort

#### Installation Instructions

**Minimal Installation (Required Only):**
```bash
pip install rich
```

**Full Installation (With Optional Features):**
```bash
pip install rich GitPython
```

**For Development (With Type Checking):**
```bash
pip install rich GitPython mypy
```

#### Version Requirements

- **Python**: 3.8 or higher (for `pathlib`, type hints, and f-strings)
- **rich**: 13.0.0 or higher (for latest features and bug fixes)
- **GitPython**: 3.1.0 or higher (if using optional git integration)

#### Library Usage Summary

| Library | Purpose | Required? | Used For |
|---------|--------|----------|----------|
| `pathlib` | File paths | ✅ Built-in | Finding and comparing files |
| `argparse` | CLI parsing | ✅ Built-in | Command-line options |
| `subprocess` | External commands | ✅ Built-in | Git commands (if GitPython not used) |
| `re` | Pattern matching | ✅ Built-in | File filtering patterns |
| `typing` | Type hints | ✅ Built-in | Code documentation |
| `collections` | Data structures | ✅ Built-in | Categorizing files |
| `datetime` | Date/time | ✅ Built-in | Git history timestamps |
| `rich` | Terminal output | ✅ Required | Color-coded output, tables, panels |
| `GitPython` | Git integration | ⚠️ Optional | Better git history analysis |
| `colorama` | Colors (fallback) | ⚠️ Optional | Only if rich unavailable |

### CLI Options

```bash
what-is-left.py [OPTIONS]

Options:
  --verbose          Show all files, including excluded ones
  --quiet            Show summary statistics only
  --no-new           Hide new files in pub-bin section
  --no-moved         Hide successfully migrated files
  --export FILE      Export results to JSON/CSV file
  --format {table,list,json}  Output format (default: table)
```

## Questions to Resolve

1. **Git History Analysis**
   - Should we analyze git history in `pub-bin` only, or both repos?
   - How far back should we look in git history?
   - What if a file was moved multiple times?

2. **Files in Both Places**
   - Should we compare file contents to see if they're identical?
   - Should we show a diff or just flag them?
   - What's the recommended action (remove from old, keep both, etc.)?

3. **File Filtering**
   - Should we exclude ALL `.md` files, or keep README files?
   - Should we exclude documentation in subdirectories but keep root-level docs?
   - Are there config files that are important to track?

4. **Output Format**
   - Should we group by directory structure within each category?
   - Should we show file sizes or modification dates?
   - Should we provide actionable commands (e.g., "cp ../bin/file.sh ./file.sh")?

## Testing Plan

1. **Test with current repositories**
   - Run on actual `pub-bin` and `../bin`
   - Verify filtering works correctly
   - Check that important files aren't excluded
   - Verify git history analysis finds moved files

2. **Test file state detection**
   - Create test files in both directories
   - Verify they show up in "files in both" section
   - Create test files only in old bin
   - Verify they show up in "to migrate" section

3. **Test git history analysis**
   - Create a test file in old bin
   - Move it to pub-bin and commit
   - Verify it shows up in "moved" section

4. **Test edge cases**
   - Empty directories
   - Directories with only excluded files
   - Files that were moved then deleted
   - Files that were moved then modified

5. **Test output formatting**
   - Verify colors work in different terminals
   - Test with `--quiet` flag
   - Test with `--no-new` flag
   - Test with `--verbose` flag

## Success Criteria

The improved Python script should:
- ✅ Make it immediately clear what needs attention (RED = fix, YELLOW = migrate)
- ✅ Show what's already been done (GREEN = moved files)
- ✅ Filter out noise (cache, images, docs, etc.) automatically
- ✅ Use git history to detect moved files
- ✅ Provide beautiful, color-coded output using `rich` library
- ✅ Be easy to read and understand at a glance
- ✅ Show summary statistics at the top
- ✅ Be flexible enough to show more detail when needed

## Next Steps

1. ✅ Review this plan and get approval
2. Set up Python environment and install dependencies
3. Implement Phase 1 (basic structure and file discovery)
4. Test and refine
5. Implement Phase 2 (git history analysis)
6. Test and refine
7. Implement Phase 3 (file state detection)
8. Test and refine
9. Implement Phase 4 (rich color output)
10. Test and refine
11. Implement Phase 5 (enhanced features)
12. Final testing and documentation
13. Replace bash script with Python version
