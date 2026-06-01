# File Tools

Filesystem hygiene scripts — sanitize filenames and similar per-file
mutations.

All scripts in this directory run under `set -euET -o pipefail` (the
pub-bin strict-mode standard — see `README-AI-CODING-STANDARDS.md`).
Disabling strict mode is not allowed.

## Scripts

- `fix-spaces-in-filename.sh <file>` - Sanitize a single filename
  - Replaces any character that is not a letter, digit, dot, slash, or hyphen with `_`
  - Renames the file with `mv` only if the new name differs
  - Errors out (exit 1) on blank input or non-file paths
- `fix-spaces-in-filenames.sh [<directory>]` - Sanitize many filenames
  - With a directory argument: `find <dir> -type f | grep " "` and rename each
  - With no argument: reads filenames from stdin (one per line)
  - Calls `fix-spaces-in-filename.sh` for each file

## Usage

### fix-spaces-in-filename.sh
Rename a single file with spaces (or other non-safe chars) in its name:
```bash
./file-tools/fix-spaces-in-filename.sh "my file name.txt"
```

### fix-spaces-in-filenames.sh
Process every file in a directory tree:
```bash
./file-tools/fix-spaces-in-filenames.sh <directory>
```

Or pipe in a custom filename list:
```bash
find . -type f | grep " " | ./file-tools/fix-spaces-in-filenames.sh
```

```bash
find . -type f -name "*.txt" | grep " " | ./file-tools/fix-spaces-in-filenames.sh
```
