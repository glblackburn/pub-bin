# FEATURE-6: Show Git Repository Name and Branch Information

**Status:** Completed
**Priority:** Medium
**Severity:** Low
**Reported:** 2025-12-09
**Completed:** 2025-12-09

**Description:**
Add display of git repository name and current branch information to the output. This provides better context about which repository is being monitored, especially when working with multiple repositories or when the script is run from different locations.

**Implementation:**
- ✅ Repository name and branch detection when `-r` flag is used (lines 262-282)
- ✅ Displays as separate line after timestamp when `-r` flag is used (Example 2 format)
- ✅ Format: `repo: pub-bin  branch: main` displayed as separate line
- ✅ Gracefully handles non-git directories (shows "repo: unknown  branch: unknown")
- ✅ Handles detached HEAD state (shows short commit hash instead of branch name)
- ✅ Repository/branch line is piped to `say` command separately (independent of metrics audio)
- ✅ Audio behavior: Always piped to `say` unless `-c` flag is used (then only when repo/branch changes)
- ✅ Bug fix: Line 400 typo fixed (`repo_name_changed` → `repo_info_changed`)

**Current Behavior:**
- Repository name and branch are detected when `-r` flag is used
- Repository/branch info is displayed as a separate line after timestamp: `repo: pub-bin  branch: main`
- Repository/branch line is piped to `say` command separately (independent of metrics audio)
- Audio behavior: Always piped to `say` when `-r` is used, unless `-c` flag is used (then only when repo/branch changes)
- Gracefully handles non-git directories (shows "repo: unknown  branch: unknown")
- Handles detached HEAD state (shows short commit hash instead of branch name)

**Implementation Details:**
- `-r` flag enables repository/branch detection and display
- Shows as separate line after timestamp (Example 2 format)
- Format: `repo: pub-bin  branch: main`
- Uses `git rev-parse --show-toplevel` and `git rev-parse --abbrev-ref HEAD`
- Handles detached HEAD state (shows short commit hash via `git rev-parse --short HEAD`)
- Handles errors gracefully (shows "unknown" if not in git repo)
- Repository/branch line is piped to `say` command separately (lines 405-413)
- Audio is independent of metrics audio announcement
- Audio respects `-c` flag: only piped to `say` if repo/branch changed when `-c` is used
- Without `-c`: repo/branch line always piped to `say` when `-r` is used

**Proposed Implementation:**

1. **Add Git Repository and Branch Detection:**
   - Use `git rev-parse --show-toplevel` to get repository root
   - Use `git rev-parse --abbrev-ref HEAD` to get current branch name
   - Handle cases where not in a git repository gracefully
   - Cache repository info to avoid repeated git commands

2. **Display Options:**
   - Option A: Show in timestamp line (e.g., "Tue Dec 9 13:56:06 EST 2025 [repo-name:main]")
   - Option B: Show as separate line after timestamp
   - Option C: Show in each metric line (like current `-r` flag behavior)
   - Option D: Add new flag to control display location/format

3. **CLI Flag Consideration:**
   - Could extend `-r` flag to include branch info
   - Could add new flag (e.g., `-b` for branch, `-g` for git info)
   - Could make it default behavior (always show)
   - Default recommendation: Always show (no flag needed), or extend `-r` flag

**Output Examples:**

**Example 1: Show in timestamp line**
```
Tue Dec 9 13:56:06 EST 2025 [pub-bin:main]
diff:      275 (   new    )
status:      3 (   new    )
```

**Example 2: Show as separate line (IMPLEMENTED)**
```
Tue Dec 9 13:56:06 EST 2025
repo: pub-bin  branch: main
diff:      275 (   new    )
status:      3 (   new    )
```
*Note: The repo/branch line is also piped to `say` command separately (unless `-c` flag is used and repo/branch hasn't changed)*

**Example 3: Show in each metric (extend -r flag)**
```
Tue Dec 9 13:56:06 EST 2025
diff:      275 (   new    ) (pub-bin:main)
status:      3 (   new    ) (pub-bin:main)
```

**CLI Changes:**
- ✅ **Implemented:** `-r` flag shows repository and branch as separate line (Example 2 format)
- ✅ Repository/branch line is piped to `say` command separately (independent of metrics audio)
- ✅ Audio behavior: Always piped to `say` when `-r` is used, unless `-c` flag is used (then only when repo/branch changes)
- ✅ Format: `repo: pub-bin  branch: main` displayed as separate line after timestamp
- ✅ Usage message updated: "Show repository name and branch as separate line (also in audio unless -c used)"

**Implementation Details:**

1. **Git Commands:**
   ```bash
   # Get repository root
   repo_root=$(git rev-parse --show-toplevel 2>/dev/null)
   repo_name=$(basename "${repo_root}" 2>/dev/null || echo "unknown")

   # Get current branch
   branch_name=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
   ```

2. **Error Handling:**
   - Handle case where not in git repository
   - Handle case where git commands fail
   - Show "unknown" or "not-a-repo" as fallback
   - Don't break script if git is not available

3. **Performance:**
   - Consider caching repository info (only changes when branch changes)
   - Git commands are relatively fast, but avoid unnecessary calls
   - Could check once per iteration or cache until branch changes

**Files Affected:**
- `monitor-ai-agent-progress.sh`
  - ✅ Repository/branch detection when `-r` flag is used (lines 262-282)
  - ✅ Separate line display after timestamp (Example 2 format, line 276)
  - ✅ Repository/branch line piped to `say` separately (lines 405-413)
  - ✅ Audio is independent of metrics audio announcement
  - ✅ Audio respects `-c` flag (only piped to `say` if changed when `-c` is used)
  - ✅ Usage message updated (line 48)
  - ✅ Bug fix: Fixed typo `repo_name_changed` → `repo_info_changed` (line 400)

**Impact:**
- **Low Risk:** Display-only change, doesn't affect core functionality
- **User Experience:** Improves context awareness
- **Performance:** Minimal impact (2 git commands per iteration)
- **Breaking Change:** None (additive feature)

**Benefits:**
- Better context when monitoring multiple repositories
- Clear indication of which branch is being monitored
- Helps with debugging and understanding script output
- Useful for automated monitoring scenarios

**Potential Issues:**
- Git commands may fail in non-git directories
- Branch name detection may fail in detached HEAD state
- Performance impact of additional git commands (minimal)
- Display format needs to be clear and not cluttered

**Testing:**
- ✅ Test in git repository (various branches) - Verified
- ✅ Test in non-git directory - Verified (shows "repo: unknown  branch: unknown")
- ✅ Test in detached HEAD state - Verified (shows short commit hash)
- ✅ Test with `-r` flag - Verified (shows separate line)
- ✅ Test with `-r -c` flag - Verified (audio only when changed)
- ✅ Test without `-r` flag - Verified (no repo/branch line)
- ✅ Test audio behavior - Verified (piped to `say` separately)
- ⏳ Test performance with frequent updates - Pending
- ⏳ Test error handling when git is not available - Pending

**Estimated Complexity:**
- **Low (1-2 hours)**
  - Straightforward git command integration
  - Display formatting is simple
  - Error handling is standard
  - Performance optimization (caching) is optional

**Questions Answered:**
1. ✅ **Where should the repository/branch info be displayed?** - Separate line after timestamp (Example 2 format)
2. ✅ **Should this be always-on or controlled by a flag?** - Controlled by `-r` flag
3. ✅ **Should this extend the `-r` flag or be independent?** - Extends `-r` flag
4. ✅ **How to handle detached HEAD state?** - Shows short commit hash via `git rev-parse --short HEAD`
5. ✅ **Should repository info be cached or recalculated each iteration?** - Recalculated each iteration (minimal performance impact)
6. ✅ **Audio behavior?** - Piped to `say` separately, respects `-c` flag

**Additional Notes:**
- This feature improves observability and context awareness
- Consider consistency with existing `-r` flag behavior
- May want to show commit hash or short commit hash as additional info
- Could be combined with future features like "show last commit message" or "show commit status"
