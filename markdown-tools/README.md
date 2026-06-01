# Markdown Tools

Generate Markdown listings of files and images from a directory tree.

All scripts in this directory run under `set -euET -o pipefail` (the
pub-bin strict-mode standard — see `README-AI-CODING-STANDARDS.md`).
Disabling strict mode is not allowed.

## Scripts

- `generate-md-file-and-screenshot-lists.sh [-hvY] [-d <directory>]` - Generate clickable file + image lists for a directory
  - Renames any files containing spaces in their name first (via `fix-spaces-in-filenames.sh`); the `-Y` flag bypasses the confirmation prompt for that rename step
  - Emits a `## Files` section (one bullet link per file via `convert-to-md-file-link-list.sh`)
  - Emits a `## Screenshots` section (one clickable image per `*.png`/`*.jpg` via `convert-to-md-clickable-image-list.sh`)
  - Options: `-d <directory>` to set the input dir (default `.`), `-Y` to skip prompt, `-v` for verbose, `-h` for help
- `convert-to-md-file-link-list.sh [-h]` - Convert stdin filename list → markdown bullet links
  - Reads filenames from stdin (one per line)
  - Emits `* [<file>](<file>)` per line
- `convert-to-md-clickable-image-list.sh [-h]` - Convert stdin image-path list → clickable markdown images
  - Reads filenames from stdin (one per line)
  - Emits `[![<file>](<file>)](<file>)` per line (clicking the rendered thumbnail opens the original)

## Usage

### generate-md-file-and-screenshot-lists.sh
Generate file and screenshot lists for a directory:
```bash
./markdown-tools/generate-md-file-and-screenshot-lists.sh -Y -d ./screenshots
```

### convert-to-md-file-link-list.sh
Pipe a filename list and get markdown links:
```bash
ls -1 export* | ./markdown-tools/convert-to-md-file-link-list.sh
```

### convert-to-md-clickable-image-list.sh
Pipe a list of image paths and get clickable markdown images:
```bash
find screenshots -type f | ./markdown-tools/convert-to-md-clickable-image-list.sh
```
