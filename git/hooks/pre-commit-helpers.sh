#!/bin/bash
# Pre-commit helper functions
# Used by pre-commit and pre-commit-msg hooks

# Check code quality (trailing whitespace, file endings)
check_code_quality() {
    local errors=0
    local files
    local file
    local staged_content
    local working_content

    # Get staged files
    files=$(git diff --cached --name-only --diff-filter=ACM)

    if [ -z "$files" ]; then
        return 0
    fi

    echo "Checking code quality..." >&2

    # Check for trailing whitespace and file endings
    while IFS= read -r file; do
        if [ ! -f "$file" ]; then
            continue
        fi

        # Skip binary files
        if git check-attr --all "$file" 2>/dev/null | grep -q "binary: set"; then
            continue
        fi

        # Check STAGED content (what will be committed)
        # Write staged content directly to temp file to preserve newlines
        local temp_staged=$(mktemp)
        if git show :"$file" > "$temp_staged" 2>/dev/null && [ -s "$temp_staged" ]; then
            # Check trailing whitespace in staged content
            if grep -n '[[:space:]]$' "$temp_staged" >/dev/null 2>&1; then
                echo "ERROR: $file (STAGED) contains trailing whitespace" >&2
                grep -n '[[:space:]]$' "$temp_staged" | head -5 | sed 's/^/  /' >&2
                errors=1
            fi

            # Check file ending in staged content (must end with newline)
            if [ "$(tail -c1 "$temp_staged" | od -An -tx1 | tr -d ' \n')" != "0a" ]; then
                echo "ERROR: $file (STAGED) does not end with newline" >&2
                errors=1
            fi
        fi
        rm -f "$temp_staged"

        # Check WORKING DIRECTORY content (what's on disk)
        if [ -f "$file" ]; then
            # Check trailing whitespace in working directory
            if grep -n '[[:space:]]$' "$file" >/dev/null 2>&1; then
                echo "ERROR: $file (WORKING DIRECTORY) contains trailing whitespace" >&2
                grep -n '[[:space:]]$' "$file" | head -5 | sed 's/^/  /' >&2
                errors=1
            fi

            # Check file ending in working directory (must end with newline)
            if [ -s "$file" ] && [ "$(tail -c1 "$file" | wc -l)" -eq 0 ]; then
                echo "ERROR: $file (WORKING DIRECTORY) does not end with newline" >&2
                errors=1
            fi
        fi
    done <<< "$files"

    return $errors
}

# Check for sensitive data in staged files
check_sensitive_data_files() {
    local errors=0
    local files
    local project_root
    local file

    project_root="$(git rev-parse --show-toplevel)"
    files=$(git diff --cached --name-only --diff-filter=ACM)

    if [ -z "$files" ]; then
        return 0
    fi

    echo "Scanning for sensitive data..." >&2

    # Check for sensitive patterns directly
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            # Skip binary files
            if git check-attr --all "$file" 2>/dev/null | grep -q "binary: set"; then
                continue
            fi

            # Skip documentation files (they contain example patterns)
            if [[ "$file" == *.md ]]; then
                continue
            fi

            # Skip test files in test_hooks directory (they contain intentional test patterns)
            # But don't skip temporary test files created by test script (test_hook_*)
            if [[ "$file" == */test_hooks/* ]]; then
                filename=$(basename "$file")
                if [[ ! "$filename" =~ ^test_hook_ ]]; then
                    continue
                fi
            fi
            if [[ "$file" == *test-hooks.sh ]] || [[ "$file" == *verify-hooks.sh ]]; then
                continue
            fi

            # Check for AWS keys (AKIA followed by 16 alphanumeric chars)
            if grep -qE '\bAKIA[0-9A-Z]{16}\b' "$file" 2>/dev/null; then
                echo "ERROR: $file contains sensitive data!" >&2
                grep -nE '\bAKIA[0-9A-Z]{16}\b' "$file" | head -3 | sed 's/^/  /' >&2
                errors=1
            fi

            # Check for GitHub tokens (ghp_ or gh[oprsu]_ followed by 36 chars)
            if grep -qE '\bgh[oprsu]_[0-9a-zA-Z]{36}\b' "$file" 2>/dev/null; then
                echo "ERROR: $file contains GitHub token!" >&2
                grep -nE '\bgh[oprsu]_[0-9a-zA-Z]{36}\b' "$file" | head -3 | sed 's/^/  /' >&2
                errors=1
            fi

            # Check for API keys (api_key, secret_key, etc. with values 20+ chars)
            if grep -qiE '(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*[:=]\s*["'\'']?[A-Za-z0-9_-]{20,}' "$file" 2>/dev/null; then
                echo "ERROR: $file contains potential API key or token!" >&2
                grep -niE '(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*[:=]\s*["'\'']?[A-Za-z0-9_-]{20,}' "$file" | head -3 | sed 's/^/  /' >&2
                errors=1
            fi

            # Check for passwords (password, passwd, pwd with values 8+ chars)
            if grep -qiE '(password|passwd|pwd)\s*[:=]\s*["'\'']?[^\s"'\''`]{8,}' "$file" 2>/dev/null; then
                echo "ERROR: $file contains potential password!" >&2
                grep -niE '(password|passwd|pwd)\s*[:=]\s*["'\'']?[^\s"'\''`]{8,}' "$file" | head -3 | sed 's/^/  /' >&2
                errors=1
            fi
        fi
    done <<< "$files"

    return $errors
}

# Check commit message for sensitive data
check_commit_message() {
    local commit_msg_file="$1"
    local errors=0

    if [ ! -f "$commit_msg_file" ]; then
        return 1
    fi

    echo "Checking commit message for sensitive data..." >&2

    # Check for AWS keys (AKIA followed by 16 alphanumeric chars)
    if grep -qE '\bAKIA[0-9A-Z]{16}\b' "$commit_msg_file" 2>/dev/null; then
        echo "ERROR: Commit message contains sensitive data!" >&2
        errors=1
    fi

    # Check for GitHub tokens (ghp_ or gh[oprsu]_ followed by 36 chars)
    if grep -qE '\bgh[oprsu]_[0-9a-zA-Z]{36}\b' "$commit_msg_file" 2>/dev/null; then
        echo "ERROR: Commit message contains GitHub token!" >&2
        errors=1
    fi

    # Check for API keys (api_key, secret_key, etc. with values 20+ chars)
    if grep -qiE '(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*[:=]\s*["'\'']?[A-Za-z0-9_-]{20,}' "$commit_msg_file" 2>/dev/null; then
        echo "ERROR: Commit message contains potential API key or token!" >&2
        errors=1
    fi

    # Check for passwords (password, passwd, pwd with values 8+ chars)
    if grep -qiE '(password|passwd|pwd)\s*[:=]\s*["'\'']?[^\s"'\''`]{8,}' "$commit_msg_file" 2>/dev/null; then
        echo "ERROR: Commit message contains potential password!" >&2
        errors=1
    fi

    if [ $errors -ne 0 ]; then
        return 1
    fi

    return 0
}

# Check for backup files
check_backup_files() {
    local errors=0
    local backup_files

    backup_files=$(git ls-files | grep -E '~$|\.bak$|\.backup$' || true)

    if [ -n "$backup_files" ]; then
        echo "WARNING: Backup files found in repository:" >&2
        echo "$backup_files" | sed 's/^/  /' >&2
        echo "Consider removing these files:" >&2
        echo "  find . -name '*~' -delete" >&2
        # Don't fail, just warn
    fi

    return 0
}


