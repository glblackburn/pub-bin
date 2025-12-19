# AI Coding Standards

This document defines the standard AI coding rules that should be applied consistently across all projects.

**IMPORTANT:** These rules are automatically loaded in Cursor via `.cursorrules` file at the repository root. The `.cursorrules` file contains the most critical rules that must be followed in every session. This document provides complete details and context.

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
- AI assistants should NEVER stage changes with `git add` (except as noted below)
- AI assistants may only ask to check `git status` or `git diff`
- The user handles ALL git operations (add, commit, push, etc.)

**MANDATORY: Commit Workflow (Two-Step Process)**

AI assistants MUST follow this exact workflow to commit changes. This is a REQUIRED PROCESS, not optional.

**Understanding "Commit" Requests:**
- When user says "commit" or "commit [file]", they are REQUESTING to see what will be committed, NOT giving permission to commit
- Interpret "commit" as: "show me what will be committed" - NOT as "go ahead and commit"
- Permission to commit comes in a SEPARATE message AFTER you show the commit information
- "Commit" has two meanings:
  - **Request:** "Show me what will be committed" (what user means when they say "commit")
  - **Confirmation:** "Go ahead and commit" (what user means when they say "yes", "go ahead", "proceed", etc.)

**What Does NOT Count as Confirmation:**
- User saying "commit" (this is the request, not confirmation)
- User saying "commit [file]" (this is the request, not confirmation)
- User saying "ok" without seeing the full summary first

**What DOES Count as Confirmation:**
- "yes, commit with that message"
- "go ahead and commit"
- "proceed"
- "commit with that message"
- Similar explicit confirmation AFTER seeing the commit summary

**Step-by-Step Commit Workflow:**

Before committing, you MUST complete ALL of these steps:

1. **[ ] Show Commit Information in Response:**
   - Display the exact commit message that will be used
   - Display the complete list of ALL files that will be committed (no exceptions)
   - Display a summary of changes for EACH file (via `git diff --stat` or `git diff` for each file)
   - Format clearly with headers: "Commit message:", "Files:", "Changes:"

2. **[ ] END YOUR RESPONSE (CRITICAL):**
   - **You MUST NEVER commit in the same response where you show the commit message**
   - **The commit message display and the commit execution MUST be in separate responses**
   - After showing commit info, END your response with: "Should I proceed with this commit?" or similar
   - **STOP - DO NOT PROCEED - WAIT FOR USER'S NEXT MESSAGE**

3. **[ ] Wait for User's Next Message:**
   - Do not commit until you receive a SEPARATE message from the user
   - The user's confirmation must come AFTER they see your commit summary
   - The confirmation must be in a DIFFERENT message than the original "commit" request

4. **[ ] Verify Confirmation:**
   - User's message must explicitly confirm (not just "commit" again)
   - Confirmation must acknowledge the commit message or changes
   - Examples: "yes", "go ahead", "proceed", "commit with that message"

5. **[ ] Execute Commit in NEW Response:**
   - Only after receiving explicit confirmation in a separate message
   - Use the exact commit message you showed in step 1
   - Only commit the files that were explicitly listed in step 1
   - Do not add any files that were not in the review summary
   - Verify the commit succeeded and show the commit hash

**CRITICAL RULES:**

- **NEVER commit in the same response as showing commit information**
- **ALWAYS end your response after showing commit info, then wait for user confirmation**
- **The commit must happen in a SEPARATE response after user confirms**
- **If you show commit info, you MUST end your response and wait for user confirmation**

**Multi-File Commits:**
- If multiple files are modified, ALL files must be included in the review summary
- Each file must have its changes shown (diff or stat)
- User must confirm they've reviewed ALL files before committing
- Never assume files can be committed together without explicit review of each
- The confirmation must acknowledge that ALL files have been reviewed

**Example Workflow:**

```
User: "commit Makefile change"

AI Response 1 (SHOW INFO, THEN STOP):
"I'll prepare the commit. Here's what will be committed:

**Commit message:**
Fix Makefile: Quote GitPython package specification

**Files:**
- Makefile

**Changes:**
Makefile | 2 +-
1 file changed, 1 insertion(+), 1 deletion(-)

Should I proceed with this commit?"

[END RESPONSE - DO NOT COMMIT YET]

User: "yes"

AI Response 2 (NOW COMMIT):
[Executes git commit]
Commit successful. Commit hash: abc1234
```

**Default Behavior:**
- When user requests "commit" without the above review process, follow the workflow above
- This workflow applies to all AI coding assistants working on any project

### 3. File Creation

- **Files in Source Control Tree:**
  - AI assistants may create files freely within the repository source tree
  - Files must NOT be automatically committed (see Git Operations policy)
  - No need to ask permission for files in the repository directory structure
  - **IMPORTANT:** Distinguish between:
    - **Code/implementation files** (scripts, configs, etc.) - Create freely when needed for the task
    - **Documentation/review files** (review docs, analysis reports, etc.) - Only create when explicitly requested
    - **Conversational output** (reviews, analysis, findings) - Provide in conversation, don't create files unless asked

- **When to Create Documentation Files:**
  - ✅ User explicitly requests: "create a review document", "write an analysis file", "generate a report"
  - ✅ File creation is clearly necessary for the task (e.g., "generate a report file")
  - ✅ **AI Coding Standards Compliance Reviews:** When user asks to review a session for violations of AI coding standards, create a detailed review file:
    - File should be named: `AI_STANDARDS_SESSION_REVIEW_YYYY-MM-DD.md`
    - File should be saved in: `docs/ai-standards/`
    - File should document all commits made, standards checked, violations found, and compliance status
    - Any violations found must also be documented in `docs/ai-standards/AI_STANDARDS_VIOLATIONS_LOG.md`
    - This is an exception to the general rule - standards compliance reviews require documentation files
  - ❌ User says "review X" (general reviews) - Provide review in conversation, don't create a file
  - ❌ User says "analyze Y" - Provide analysis in conversation, don't create a file
  - ❌ Creating file "just in case" or "for future reference" without being asked
  - **When in doubt:** Ask: "Should I create a review document file, or just provide the review here?"

- **Files Outside Source Control Tree:**
  - AI assistants should NEVER create files outside the repository unless:
    - They are temporary working files
    - They are created in a specific directory under `/tmp/` (e.g., `/tmp/<project-name>/`)
    - They are clearly temporary and will be cleaned up
  - Always ask before creating files outside the repository
  - Explain the purpose and location of any files created outside the repository

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

### 5. Security and Sensitive Data

**CRITICAL: Never Commit Sensitive Data - ENFORCED BY GIT HOOKS**

This rule is **MANDATORY** and is enforced by git hooks. Violations will block commits.

**Policy:**
- AI assistants must NEVER commit files containing sensitive data, including:
  - API keys, access tokens, passwords
  - AWS access keys (AKIA pattern)
  - GitHub tokens (ghp_/gh[oprsu]_ pattern)
  - Private keys, SSH keys, certificates
  - Database credentials, connection strings
  - Any credentials, secrets, or authentication tokens

**NO EXCEPTIONS:**
- **ALL file types are checked** (including `.md`, `.txt`, `.py`, `.sh`, `.json`, `.yaml`, etc.)
- **ALL locations are checked** (including `docs/`, `test/`, `examples/`, root directory, etc.)
- **ALL commits are checked** (including commit messages)
- Only binary files (detected by git attributes) are skipped because they cannot be checked as text

**Enforcement:**
- Git hooks automatically scan ALL staged files before every commit
- Git hooks scan commit messages for sensitive data patterns
- Commits containing sensitive data will be **BLOCKED** by the pre-commit hook
- This is why the git hooks system was developed - to enforce this critical security rule

**If Sensitive Data is Found:**
1. **DO NOT COMMIT** - The hook will block it automatically
2. Alert the user immediately about the sensitive data
3. Suggest alternatives:
   - Use environment variables
   - Use secret managers (AWS Secrets Manager, HashiCorp Vault, etc.)
   - Use configuration files that are in `.gitignore`
   - Use placeholder/example values for testing (clearly marked as examples)

**For Testing/Examples:**
- Use clearly invalid/example patterns:
  - `AKIAEXAMPLE12345678` (invalid format)
  - `ghp_EXAMPLE_TOKEN_123456789012345678901234567890` (invalid format)
- Mark examples clearly in comments: `# EXAMPLE: Not a real key`
- Never use real credentials, even in test files

**Git Hooks Configuration:**
- See `git/README.md` for hook installation and configuration
- Hooks are installed via: `cd git/ && make install-hooks`
- Test hooks via: `cd git/ && make test`
- Hooks cannot be bypassed without explicit `--no-verify` flag (not recommended)

**Related Documentation:**
- `git/README.md` - Git hooks documentation and setup
- `docs/ai-standards/AI_STANDARDS_VIOLATIONS_LOG.md` - Security violations and lessons learned
- `git/docs/` - Additional git hooks documentation

**This rule takes precedence over all other rules.** Security is non-negotiable.

### 6. AI Coding Standards Compliance Reviews

**IMPORTANT: Session Review Documentation**

When asked to review a session for violations of AI coding standards:

1. **Create Detailed Review File:**
   - File name: `AI_STANDARDS_SESSION_REVIEW_YYYY-MM-DD.md`
   - File location: `docs/ai-standards/`
   - Document all commits made during the session
   - Review each commit against the exception protocol requirements
   - Check file creation, code quality, security, and other standards
   - Provide summary of violations found (if any) and compliance status

2. **Document Violations:**
   - Any violations found must be documented in `docs/ai-standards/AI_STANDARDS_VIOLATIONS_LOG.md`
   - Include root cause analysis, corrective action, and prevention measures
   - Follow the format established in the violations log

3. **Review Scope:**
   - Check all git operations (commits, staging, etc.)
   - Verify file creation followed standards
   - Check code quality (trailing whitespace, newlines, etc.)
   - Verify no sensitive data was committed
   - Check documentation accuracy (if applicable)

**This is a required exception:** When reviewing for standards compliance, a documentation file must be created (unlike general "review X" requests which are conversational).

### 7. Documentation Verification

**IMPORTANT: README Accuracy Check**
- Before committing changes to scripts, verify that README.md accurately reflects the current script implementation
- Check that all script options, features, and behavior described in README.md match the actual script
- Update README.md if script changes affect:
  - CLI options or parameters
  - Script behavior or functionality
  - Output format or examples
  - Configuration requirements
  - Dependencies or requirements
- When in doubt, ask: "Is the README in sync with the code changes?"

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

## Security Enforcement

**The Security and Sensitive Data rule (Section 5) is enforced by git hooks.**

Git hooks automatically:
- Scan all staged files before every commit
- Scan commit messages for sensitive data patterns
- Block commits that contain sensitive data
- Cannot be bypassed without explicit `--no-verify` flag

**This enforcement is why the git hooks system was developed.**

If you encounter issues with hooks:
- Verify hooks are installed: `ls -la .git/hooks/pre-commit`
- Reinstall hooks: `cd git/ && make install-hooks`
- Test hooks: `cd git/ && make test`
- See `git/README.md` for troubleshooting

## Project-Specific Standards

Projects may have additional standards beyond these core rules. Refer to each project's README.md for project-specific AI coding standards.

## Related Documentation

- `docs/ai-standards/AI_STANDARDS_VIOLATIONS_LOG.md` - Historical violations and lessons learned
- `docs/ai-standards/AI_RULES_REVIEW.md` - Standards review and recommendations
- `docs/ai-standards/AI_STANDARDS_SESSION_REVIEW_*.md` - Session-specific compliance reviews
