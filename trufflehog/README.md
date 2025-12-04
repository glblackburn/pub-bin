# Trufflehog Scripts

## trufflehog-local-git-repos.sh

A utility script to recursively find and scan git repositories for secrets using Trufflehog.

**What it does:**
- Recursively searches for `.git` directories in the target directory
- Runs `trufflehog` on each identified repository
- Captures scan results to separate timestamped log files for each repository
- Uses `trufflehog git file://...` URI format for scanning
- Filters results to show only `verified` and `unknown` secrets

**Usage:**
```bash
./trufflehog-local-git-repos.sh [-hqv] -d <directory> [-o <output_directory>]
```

**Options:**
- `-h` : Display help message
- `-d <directory>` : Target directory to scan (Required)
- `-o <directory>` : Output directory for reports (Default: target directory)
- `-q` : Quiet mode (output as little as possible)
- `-v` : Verbose output

**Details:**
- The script identifies repositories by looking for `.git` directories.
- It executes `trufflehog git file://<repo_path> --results=verified,unknown`.
- Output files are saved in the target directory with the naming convention: `trufflehog-<repo_name>-<timestamp>.txt`.
- Follows shell-template.sh patterns: proper error handling, CLI options, functions, and structure.

**Examples:**
```bash
# Scan all repos in ~/projects
./trufflehog-local-git-repos.sh -d ~/projects

# Verbose mode
./trufflehog-local-git-repos.sh -v -d ~/projects
```

**Dependencies:**
- `trufflehog` - Required for scanning (must be in PATH)
- `git` - Required for repository operations

**Installation:**

The script requires `trufflehog` to be installed. You can install it using the provided Makefile:

```bash
# Check if trufflehog is installed
make check

# Install trufflehog automatically (detects OS and architecture)
make install

# Or install to a custom directory
INSTALL_DIR=~/bin make install
```

The Makefile will:
- Detect your OS (Linux, macOS, Windows) and architecture (amd64, arm64)
- Download the latest trufflehog release from GitHub
- Install it to `~/bin` (or `/usr/local/bin` if `~/bin` doesn't exist)
- Ensure it's executable and in your PATH

If trufflehog is not installed, the script will display a clear error message with installation instructions.

---
Created using Google Antigravity.
