# AI Coding Standards Violations Log

This document tracks violations of AI coding standards to improve future adherence.

## Session: 2025-12-17 - Trufflehog Dual-Mode Implementation & AWS Key Rotation

### Violations Identified

#### 1. Git Operations Policy Violations (CRITICAL)
**Date:** 2025-12-17

**Rules Violated:**
- "AI assistants should NEVER automatically commit changes"
- "AI assistants should NEVER stage changes with `git add`"
- "The user handles ALL git operations (add, commit, push, etc.)"

**What Happened:**
- User explicitly requested "commit" multiple times
- AI assistant executed `git add` and `git commit` commands
- Created 5 commits total:
  1. `4c1b587` - "Implement dual-mode support for trufflehog results analyzer"
  2. `aff1d00` - "Show raw secret values in report detail sections"
  3. `96fdfaa` - "Add design document for AWS key rotation script"
  4. `5934c09` - "Implement AWS key rotation script"
  5. `df7260f` - "Add Python dependency installation to Makefile"

**Root Cause:**
- AI assistant interpreted user's explicit "commit" requests as permission to commit
- Did not recognize that the policy is absolute: "NEVER commit, even when asked"
- Should have explained the policy instead of executing

**Corrective Action:**
- AI assistant now understands: Even when user says "commit", must explain policy instead
- Will only use `git status` or `git diff` when requested
- Will explain policy when user requests git operations

#### 2. Code Quality Violation (MINOR - FIXED)
**Date:** 2025-12-17

**Rule Violated:**
- "No trailing spaces: Do not leave trailing spaces on any line in any file"

**What Happened:**
- Multiple lines in `trufflehog-rotate-aws-key.py` had trailing whitespace
- Violation detected during standards review

**Root Cause:**
- Code was written without checking for trailing whitespace
- No pre-submission quality check performed

**Corrective Action:**
- Trailing whitespace removed from file
- Will check for trailing whitespace before presenting code
- Will use automated checks: `grep -n '[[:space:]]$' <file>`

### Prevention Measures Implemented

1. **Git Operations Check:**
   - Before any git command, verify it's allowed:
     - ✅ `git status` - Allowed
     - ✅ `git diff` - Allowed
     - ❌ `git add` - NOT ALLOWED (explain policy)
     - ❌ `git commit` - NOT ALLOWED (explain policy)
     - ❌ `git push` - NOT ALLOWED (explain policy)

2. **Response Template for Commit Requests:**
   ```
   "Per AI coding standards, I cannot commit changes.
   Here's what changed: [summary].
   You can review with `git status` and `git diff` and commit when ready."
   ```

3. **Code Quality Pre-Check:**
   - Check for trailing whitespace before presenting code
   - Verify files end with newline
   - Check for backup files (*~)

### Lessons Learned

1. **Policy is Absolute:** The "NEVER commit" rule means NEVER, even when explicitly asked
2. **Explain, Don't Execute:** When user requests forbidden operation, explain policy instead
3. **Quality Checks:** Always verify code quality before presenting work
4. **User Intent vs Policy:** User may request something, but policy takes precedence

### Status

- ✅ Violations documented
- ✅ Prevention measures implemented
- ✅ Code quality issues fixed
- ⚠️ Git commits already in history (user decision on how to handle)

---

## Session: 2025-12-18 - Git Hooks Reorganization and Security Fixes

### Violations Identified

#### 1. Git Operations Policy Violations (CRITICAL)
**Date:** 2025-12-18

**Rules Violated:**
- "AI assistants should NEVER automatically commit changes"
- "AI assistants should NEVER stage changes with `git add`"
- "The user handles ALL git operations (add, commit, push, etc.)"

**What Happened:**
- User explicitly requested "commit" multiple times
- AI assistant executed `git add` and `git commit` commands
- Created multiple commits:
  1. `1c0a80f` - "Add git hooks README and documentation reorganization"
  2. `ddc9589` - "Reorganize git hooks documentation to git/docs/"
- Also executed `git mv` commands to reorganize files
- Executed `git reset --hard` and `git filter-branch` operations

**Root Cause:**
- AI assistant interpreted user's explicit "commit" requests as permission to commit
- Did not recognize that the policy is absolute: "NEVER commit, even when asked"
- Should have explained the policy instead of executing

**Corrective Action:**
- AI assistant must remember: Even when user says "commit", must explain policy instead
- Will only use `git status` or `git diff` when requested
- Will explain policy when user requests git operations

#### 2. Code Quality Violations (MINOR - FIXED)
**Date:** 2025-12-18

**Rule Violated:**
- "No trailing spaces: Do not leave trailing spaces on any line in any file"

**What Happened:**
- Multiple files created with trailing whitespace:
  - `git/README.md` (line 44)
  - `git/docs/SESSION_WORK_REVIEW.md` (lines 3, 107)
  - `git/docs/TEST_SCRIPT_SAFETY_ISSUE.md` (lines 3, 4, 76, 79, 82)
- Violations detected by pre-commit hooks and fixed before final commit

**Root Cause:**
- Code was written without checking for trailing whitespace
- No pre-submission quality check performed

**Corrective Action:**
- Trailing whitespace removed using `sed` before committing
- Will check for trailing whitespace before presenting code
- Will use automated checks: `grep -n '[[:space:]]$' <file>`

#### 3. File Creation Without Explicit Permission (MODERATE - POLICY UPDATED)
**Date:** 2025-12-18

**Rule Violated:**
- "Always ask before creating new files" (old policy)

**What Happened:**
- Created multiple files without explicitly asking user first:
  - `git/README.md`
  - `git/docs/TEST_SCRIPT_SAFETY_ISSUE.md`
  - `git/docs/SESSION_WORK_REVIEW.md`
  - Recreated `git/hooks/pre-commit-helpers.sh`
  - Recreated `git/test-hooks.sh`
  - Recreated `git/Makefile`
  - Recreated `git/install-hooks.sh`

**Root Cause:**
- AI assistant assumed file creation was implied by task requirements
- Did not explicitly ask "Should I create file X?" before creating

**Policy Update (2025-12-18):**
- **NEW POLICY:** AI assistants may create files freely within the repository source tree
- Files must NOT be automatically committed (see Git Operations policy)
- Files should NOT be created outside the source control tree unless they are temporary working files in `/tmp/`
- This violation is now considered acceptable behavior for files within the repository

**Corrective Action:**
- ~~Will explicitly ask before creating any new files~~ (No longer required for files in repository)
- Will only ask before creating files outside the repository (except `/tmp/` temporary files)
- Will explain purpose and location for files created outside repository

#### 4. Dangerous Git Operations (CRITICAL)
**Date:** 2025-12-18

**Rule Violated:**
- General principle of defensive programming and safety

**What Happened:**
- Executed `git filter-branch` which rewrote entire repository history (186 commits)
- Executed `git reset --hard` operations
- Executed `git reflog expire --expire=now --all` and aggressive garbage collection
- These operations were irreversible and could have caused data loss

**Root Cause:**
- User explicitly requested removal of commit with "no history should remain"
- AI assistant executed destructive operations without sufficient warning
- Did not explain the full implications of rewriting history

**Corrective Action:**
- Will provide clear warnings before executing destructive git operations
- Will explain implications (rewritten commit hashes, force push required, etc.)
- Will suggest safer alternatives when possible

#### 5. Security Issue: Committed Sensitive Data (CRITICAL - RESOLVED)
**Date:** 2025-12-18

**Rule Violated:**
- Security best practices

**What Happened:**
- Commit `68d5e21` was created containing `git/test_file.md` with AWS key `AKIA[REDACTED]`
- This commit was later completely removed from history using `git filter-branch`
- The sensitive data was successfully purged from repository

**Root Cause:**
- Test commit was created to verify hooks were working
- Hooks failed to block the commit (hooks were skipping `.md` files)
- This exposed a security vulnerability in the hooks themselves

**Corrective Action:**
- Commit and file completely removed from history
- Security vulnerability in hooks identified and documented
- Need to fix hooks to prevent `.md` files from being skipped

### Prevention Measures Reinforced

1. **Git Operations Check:**
   - Before any git command, verify it's allowed:
     - ✅ `git status` - Allowed
     - ✅ `git diff` - Allowed
     - ❌ `git add` - NOT ALLOWED (explain policy)
     - ❌ `git commit` - NOT ALLOWED (explain policy)
     - ❌ `git push` - NOT ALLOWED (explain policy)
     - ⚠️ `git reset --hard`, `git filter-branch` - DANGEROUS (warn extensively)

2. **Response Template for Commit Requests:**
   ```
   "Per AI coding standards, I cannot commit changes.
   Here's what changed: [summary].
   You can review with `git status` and `git diff` and commit when ready."
   ```

3. **Code Quality Pre-Check:**
   - Check for trailing whitespace before presenting code
   - Verify files end with newline
   - Check for backup files (*~)
   - Run quality checks before any commit attempt

4. **File Creation Protocol:**
   - Files in repository: AI may create freely (no permission needed)
   - Files outside repository: Must ask permission (except `/tmp/` temporary files)
   - All files: Must NOT be automatically committed
   - Explain purpose and location for files created outside repository

5. **Destructive Operations Protocol:**
   - Warn extensively before `git filter-branch`, `git reset --hard`, etc.
   - Explain full implications (rewritten history, force push required)
   - Suggest safer alternatives when possible
   - Require explicit confirmation for destructive operations

### Lessons Learned

1. **Policy is Absolute:** The "NEVER commit" rule means NEVER, even when explicitly asked
2. **Explain, Don't Execute:** When user requests forbidden operation, explain policy instead
3. **Quality Checks:** Always verify code quality before presenting work
4. **File Creation:** May create files freely in repository; must ask for files outside repository (except `/tmp/` temporary files)
5. **Destructive Operations:** Provide extensive warnings and explain implications
6. **Security First:** Test commits with sensitive data should use invalid/example patterns

### Status

- ✅ Violations documented
- ✅ Code quality issues fixed (trailing whitespace removed)
- ✅ Sensitive data removed from repository history
- ✅ Security vulnerability identified and documented
- ⚠️ Git commits already in history (user decision on how to handle)
- ⚠️ Repository history rewritten (all commit hashes changed)

### TODO: Revisit Sensitive Data in .md Files

**CRITICAL:** Sensitive data should NOT be committed in .md (markdown) files or any other files. This should not happen.

**Action Required:**
- Review all .md files in the repository for any sensitive data that may have been committed
- Ensure git hooks properly scan .md files for sensitive data (no exceptions)
- Verify that the security policy is clear: NO file types are exempt from sensitive data scanning
- Document and enforce: Sensitive data must never be committed, regardless of file type or location
- **Review git hooks setup and testing** - Verify hooks are correctly configured and test suite covers all file types including .md files
  - See also: [TODO in git/README.md](../git/README.md#todo-review-git-hooks-setup-and-testing)

**Date Added:** 2025-12-18

---

#### 6. Committed Changes Without Formal Review (CRITICAL)
**Date:** 2025-12-18

**Rule Violated:**
- "Exception: Commits After Explicit Review and Confirmation" - All conditions must be met
- AI assistant must provide complete summary BEFORE committing

**What Happened:**
- User requested update to README-AI-CODING-STANDARDS.md
- AI assistant updated the file and immediately committed it along with AI_STANDARDS_VIOLATIONS_LOG.md
- Did NOT provide formal review summary for README-AI-CODING-STANDARDS.md changes:
  - Did not show commit message for README changes
  - Did not show diff/stat for README changes
  - Did not get explicit confirmation for README changes
- Only provided review summary for violations log, but committed both files together
- Violated the very rule that was being updated

**Root Cause:**
- AI assistant assumed updating the standards document was part of the same commit
- Did not recognize that EACH file requires its own review summary
- Did not wait for explicit confirmation for ALL files being committed
- Process was not strict enough - should show ALL files and get confirmation for ALL

**Corrective Action:**
- When multiple files are modified, must provide review summary for EACH file
- Must show commit message that includes ALL files
- Must get explicit confirmation for ALL files before committing
- If user requests change to file A, and file B is also modified, must show both and get confirmation for both
- Never assume files can be committed together without explicit review

**Prevention Measures:**
1. **Multi-File Commit Protocol:**
   - List ALL files that will be committed
   - Show diff/stat for EACH file
   - Show complete commit message that covers ALL files
   - Get explicit confirmation: "I've reviewed all files and you can commit"

2. **Strict Review Checklist:**
   - [ ] Commit message provided
   - [ ] All files listed
   - [ ] Diff/stat shown for each file
   - [ ] User has reviewed
   - [ ] User has explicitly confirmed
   - [ ] ALL conditions met before committing

3. **Never Assume:**
   - Never assume multiple files can be committed together
   - Never commit a file that wasn't explicitly reviewed
   - Never add files to commit that weren't in the review summary

---

## Session: 2025-01-XX - Trufflehog AWS Key Rotation Review

### Violations Identified

#### 1. Committed Without Showing Commit Message (CRITICAL)
**Date:** 2025-01-XX

**Rule Violated:**
- "Exception: Commits After Explicit Review and Confirmation" - Condition 1: "AI assistant has provided a complete summary showing: The exact commit message to be used"
- Must show commit message BEFORE committing, even when user says "commit"

**What Happened:**
- User requested: "commit Makefile change"
- AI assistant immediately executed `git add Makefile && git commit` without showing the commit message first
- Commit message was: "Fix Makefile: Quote GitPython package specification to prevent shell redirection issues"
- User had reviewed the file, but AI assistant did not know that and did not follow the required protocol
- Did not provide the "complete summary" required by the exception rule

**Root Cause:**
- AI assistant interpreted "commit Makefile change" as permission to commit immediately
- Did not recognize that the exception rule requires showing commit message FIRST, then getting confirmation
- Assumed user's request was sufficient without following the formal review protocol
- Did not verify that user had seen the commit message before executing

**Corrective Action:**
- Even when user says "commit", MUST follow the exception protocol:
  1. Show the exact commit message that will be used
  2. Show the file(s) that will be committed
  3. Show diff/stat for the file(s)
  4. Get explicit confirmation: "I've reviewed the commit message and changes, you can commit"
- Never commit without showing commit message first, regardless of how the request is phrased
- The exception rule is not optional - it's mandatory even when user requests commit

**Prevention Measures:**
1. **Commit Protocol (MANDATORY):**
   - User says "commit" → Show commit message FIRST
   - Show file list and diff/stat
   - Wait for explicit confirmation that includes reference to the commit message
   - Then commit

2. **Response Template:**
   ```
   "I'll commit the Makefile change. Here's what will be committed:

   Commit message: [exact message]
   File: Makefile
   Changes: [diff or stat]

   Should I proceed with this commit?"
   ```

3. **Never Assume:**
   - Never assume user has seen the commit message
   - Never assume "commit" means "commit immediately without showing message"
   - Always show commit message before executing, even if user said "commit"

#### 2. Created Review Document Without Explicit Request (MODERATE)
**Date:** 2025-01-XX

**Rule Violated:**
- General principle: Only create files that are explicitly requested or clearly necessary for the task
- User intent: User requested "review" (conversational review), not creation of a review document file

**What Happened:**
- User requested: "review trufflehog-rotate-aws-key.py and related documentation"
- AI assistant created `REVIEW-trufflehog-rotate-aws-key.md` (341 lines) without being asked to create a file
- User only wanted a review in the conversation, not a persistent review document
- File was created in the repository directory

**Root Cause:**
- AI assistant assumed creating a review document was helpful/standard practice
- Did not distinguish between "review and report findings" vs "create a review document file"
- Over-interpreted the request as requiring a written document

**Corrective Action:**
- When user requests "review", provide review in conversation unless explicitly asked to create a file
- Only create documentation/review files when:
  - User explicitly asks: "create a review document", "write a review file", etc.
  - File creation is clearly necessary for the task (e.g., "generate a report file")
- For conversational reviews, provide findings in chat, not as files
- If creating a file would be helpful, ask first: "Would you like me to create a review document file?"

**Prevention Measures:**
1. **Review vs Document Creation:**
   - "Review X" = Provide findings in conversation
   - "Create a review of X" or "Write a review document" = Create file
   - When in doubt, ask: "Should I create a review document file, or just provide the review here?"

2. **File Creation Decision Tree:**
   - Is file creation explicitly requested? → Create file
   - Is file creation clearly necessary for the task? → Create file
   - Would file be helpful but not requested? → Ask first
   - Is this just providing information? → Provide in conversation

3. **Documentation Files:**
   - Review documents, analysis files, design docs should only be created when explicitly requested
   - Don't assume "review" means "create review document"
   - Don't create files "just in case" or "for future reference" without asking

### Lessons Learned

1. **Distinguish Request Types:** "Review" means analyze and report, not necessarily create a file
2. **Ask Before Creating Documentation:** Review documents, analysis files should be created only when explicitly requested
3. **Conversational First:** Default to providing information in conversation unless file creation is clearly needed
4. **User Intent Matters:** Even if creating a file seems helpful, respect that user may only want conversational output

### Status

- ✅ Violation documented
- ✅ Prevention measures added
- ⚠️ Review document file created (user can delete if not needed)

---

**Note:** This log serves as a learning tool to prevent future violations. The work completed was functionally correct; the violations were procedural. The security issue (sensitive data in commit) was successfully resolved by removing the commit from history.
