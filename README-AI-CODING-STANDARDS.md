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

## General Principles

1. **Readability First**
   - Clear, descriptive variable and function names
   - Comments explain why, not what
   - Consistent formatting and indentation

2. **Error Handling**
   - Check for command failures
   - Validate inputs
   - Provide meaningful error messages
   - Handle edge cases

3. **DRY (Don't Repeat Yourself)**
   - Extract common logic into functions
   - Avoid code duplication
   - Reusable components

4. **Defensive Programming**
   - Validate inputs before use
   - Check for null/empty values
   - Handle edge cases (low resources, missing files, etc.)
   - Use safe defaults

## Bash-Specific Standards

1. **Function Organization**
   - Functions before main logic
   - Clear function names (verb-noun pattern)
   - Local variables in functions
   - Return codes for success/failure

2. **Variable Usage**
   - Use `local` for function variables
   - Quote variables to prevent word splitting
   - Use `${variable}` for clarity
   - Uppercase for constants, lowercase for variables

3. **Error Handling**
   - Check exit codes: `command || handle_error`
   - Use `set -e` for fail-fast behavior (when appropriate)
   - Validate inputs before processing
   - Return meaningful exit codes
   - Use `set -euET -o pipefail` for error handling
   - Use the `|| ret=$?` pattern for error handling

4. **Code Structure**
   - Clear sections with comments
   - Logical flow: setup → validation → processing → cleanup
   - Consistent indentation (spaces or tabs, consistent)

5. **Best Practices**
   - Use `[[ ]]` for conditionals (bash-specific)
   - Use `$(command)` instead of backticks
   - Quote strings to prevent globbing
   - Use `readonly` for constants when possible

6. **Script Patterns**
   - Follow patterns from `shell-template.sh` in the pub-bin repository
   - Use `set -euET -o pipefail` for error handling
   - Use consistent verbose/quiet output control patterns
   - Use proper directory management (pushd/popd in functions)
   - Use the `|| ret=$?` pattern for error handling

## Common Patterns

### Function Pattern
```bash
function function-name {
    local param1=${1}
    local param2=${2}

    # Validation
    if [ -z "$param1" ]; then
        echo "ERROR: param1 required" >&2
        return 1
    fi

    # Processing
    # ...

    # Return result
    echo "$result"
}
```

### Error Handling Pattern
```bash
if ! command; then
    echo "ERROR: command failed" >&2
    return 1
fi
```

### Validation Pattern
```bash
if [ -z "$variable" ] || [ "$variable" = "null" ]; then
    # handle error
fi
```

## Project-Specific Standards

Projects may have additional standards beyond these core rules. Refer to each project's README.md for project-specific AI coding standards.
