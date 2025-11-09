# AI Coding Standards

This document defines the standard AI coding rules that should be applied consistently across all projects.

## Core Standards

When AI agents are used to modify or create files in any repository:

### 1. Code Quality

- **No trailing spaces**: Do not leave trailing spaces on any line in any file. Trailing whitespace should be removed.
- **No whitespace-only lines**: Do not leave lines with only spaces or tabs. Empty lines are fine, but lines containing only whitespace are not.
- **Always end files with newline**: Every file must end with a single newline character. This prevents issues with text processing tools and ensures POSIX compliance.
- **Clean up backup files before commits**: Remove Emacs backup files (files ending with `~`) before creating any commits. This ensures backup files are not accidentally committed to the repository.
  - If `clean-emacs-files.sh` exists in the project, use it: `./clean-emacs-files.sh`
  - Otherwise, use direct commands:
    ```bash
    # Find backup files
    find . -name "*~"
    
    # Remove backup files (use with caution)
    find . -name "*~" -delete
    ```
- **Follow existing script patterns**: Use consistent error handling and logging. Follow the established script structure and naming conventions. Maintain compatibility with existing scripts.

### 2. Git Operations

**IMPORTANT: Git Policy for AI Assistants**
- AI assistants should NEVER automatically commit changes
- AI assistants should NEVER prompt for commits
- AI assistants should NEVER stage changes with `git add`
- AI assistants may only ask to check `git status` or `git diff`
- The user handles ALL git operations (add, commit, push, etc.)
- This applies to all AI coding assistants working on any project

### 3. File Creation

- **Always ask before creating new files**
  - Confirm file creation with the user before proceeding
  - Explain the purpose and location of any new files

### 4. Code Quality Verification

Before submitting changes, verify file formatting:

```bash
# Check for trailing whitespace
grep -n '[[:space:]]$' *.sh *.md

# Check file endings (should show no output if files end with newline)
for file in *.sh *.md; do
  if [[ -s "$file" && $(tail -c1 "$file" | wc -l) -eq 0 ]]; then
    echo "ERROR: $file does not end with newline"
  fi
done

# Check for backup files (should show no output if none exist)
find . -name "*~"
```

## Project-Specific Standards

Projects may have additional standards beyond these core rules. Refer to each project's README.md for project-specific AI coding standards.
