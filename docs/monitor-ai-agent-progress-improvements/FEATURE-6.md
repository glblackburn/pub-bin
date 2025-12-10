# FEATURE-6: Show Git Repository Name and Branch Information

**Status:** Completed
**Priority:** Medium
**Severity:** Low
**Reported:** 2025-12-09
**Completed:** 2025-12-09

**Description:**
Add display of git repository name and current branch information to the output. This provides better context about which repository is being monitored, especially when working with multiple repositories or when the script is run from different locations.

**Implementation:**
- ✅ Repository name and branch detection in `show-timestamp` function (lines 140-149)
- ✅ Always displays in timestamp line when in a git repository
- ✅ Format: `Tue Dec 9 16:45:00 EST 2025 [pub-bin:main]`
- ✅ Gracefully handles non-git directories (no repo info shown)
- ✅ Repository info is tracked for audio announcements (lines 264-270, 400-406)
- ✅ Bug fix: Line 391 typo fixed (`repo_name_changed` → `repo_info_changed`)

**Current Behavior:**
- Repository name and branch are always detected when in a git repository
- Repository/branch info is displayed in the timestamp line: `[repo-name:branch]`
- Repository info is also included in audio announcements when `-r` flag is used
- Gracefully handles non-git directories (no repo info shown in timestamp)

**Implementation Details:**
- Modified `show-timestamp` function to detect and display repo/branch info
- Always shows when in a git repository (no flag needed)
- Format: `Tue Dec 9 16:45:00 EST 2025 [pub-bin:main]`
- Uses `git rev-parse --show-toplevel` and `git rev-parse --abbrev-ref HEAD`
- Handles errors gracefully (shows nothing if not in git repo)

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

**Example 2: Show as separate line**
```
Tue Dec 9 13:56:06 EST 2025
repo: pub-bin  branch: main
diff:      275 (   new    )
status:      3 (   new    )
```

**Example 3: Show in each metric (extend -r flag)**
```
Tue Dec 9 13:56:06 EST 2025
diff:      275 (   new    ) (pub-bin:main)
status:      3 (   new    ) (pub-bin:main)
```

**CLI Changes:**
- Option 1: No new flag - always show repository and branch
- Option 2: Extend `-r` flag to include branch information
- Option 3: Add new flag (e.g., `-b` or `-g`) to control git info display
- **Recommendation:** Option 1 (always show) or Option 2 (extend `-r`)

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
  - ✅ Modified `show-timestamp` function (lines 140-149) to include repo/branch info
  - ✅ Git repository and branch detection in timestamp function
  - ✅ Repository info tracking for audio (lines 264-270, 400-406)
  - ✅ Bug fix: Fixed typo `repo_name_changed` → `repo_info_changed` (line 391)

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
- Test in git repository (various branches)
- Test in non-git directory
- Test in detached HEAD state
- Test with `-r` flag (if extending it)
- Test performance with frequent updates
- Test error handling when git is not available

**Estimated Complexity:**
- **Low (1-2 hours)**
  - Straightforward git command integration
  - Display formatting is simple
  - Error handling is standard
  - Performance optimization (caching) is optional

**Questions to Answer:**
1. Where should the repository/branch info be displayed? (timestamp line, separate line, in metrics)
2. Should this be always-on or controlled by a flag?
3. Should this extend the `-r` flag or be independent?
4. How to handle detached HEAD state? (show commit hash? show "detached"?)
5. Should repository info be cached or recalculated each iteration?

**Additional Notes:**
- This feature improves observability and context awareness
- Consider consistency with existing `-r` flag behavior
- May want to show commit hash or short commit hash as additional info
- Could be combined with future features like "show last commit message" or "show commit status"
