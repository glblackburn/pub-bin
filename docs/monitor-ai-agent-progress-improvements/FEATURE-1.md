# FEATURE-1: Improve Git Status Counting

**Status:** Completed
**Priority:** High
**Severity:** Medium
**Reported:** 2025-12-08
**Completed:** 2025-12-09
**Commit:** 1012459

**Description:**
The current git status counting method uses `git ls-files --others` which may not accurately count all files in untracked directories. This enhancement will improve accuracy by using `find` to recursively count all files within untracked directories, ensuring all untracked files are properly tracked.

**Previous Implementation (before FEATURE-1):**
```bash
work_count=$(find -L "${work_dir_resolved}" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
diff_lines=$(git diff 2>/dev/null | wc -l | tr -d ' ' || echo "0")
status_count=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ' || echo "0")
```

**Current Implementation (lines 220-248):**
```bash
# Count git status accurately (FEATURE-1)
# Count modified/staged files (M, A, D, R, C in first column for staged, or space+M/D in second column for unstaged)
# Format: "XY filename" where X=staged, Y=unstaged
# Matches: M, A, D, R, C in first column OR M, D in second column (unstaged changes)
modified_count=$(git status --porcelain 2>/dev/null | grep -E "^[MADRC].|^.[MD]" | wc -l | tr -d '[:space:]' || echo "0")

# Count untracked files accurately using find
untracked_count=0
# Get untracked items, handling paths with spaces properly
# git status --porcelain format: "?? path" or "?? "path with spaces""
untracked_items=$(git status --porcelain 2>/dev/null | grep "^??" | sed 's/^?? //' || true)

if [ -n "${untracked_items}" ] ; then
    while IFS= read -r item; do
        if [ -n "${item}" ] ; then
            # Remove quotes if present (git quotes paths with spaces)
            item=$(echo "${item}" | sed 's/^"//;s/"$//')
            if [ -d "${item}" ] ; then
                # Directory - count all files recursively
                count=$(find "${item}" -type f 2>/dev/null | wc -l | tr -d '[:space:]' || echo "0")
                untracked_count=$((untracked_count + count))
            else
                # File - count as 1
                untracked_count=$((untracked_count + 1))
            fi
        fi
    done <<< "${untracked_items}"
fi

# Total status count is modified + untracked
status_count=$((modified_count + untracked_count))
```

**Issue:**
- `git status --porcelain | wc -l` counts lines, not files
- If an untracked entry is a directory, it only counts as 1 line
- Files within untracked directories are not counted
- Especially problematic with nested untracked directories
- Edge cases with gitignore patterns

**Expected Behavior:**
- All untracked files should be accurately counted
- Untracked directories should have all their files counted recursively
- Nested directory structures should be fully enumerated
- Modified files should continue to be counted correctly
- Combined count (modified + untracked) should be accurate

**Implementation Details:**

The implementation includes the following improvements over the original:

1. **Accurate Modified File Counting:**
   - Uses `grep -E "^[MADRC].|^.[MD]"` to match both staged and unstaged modifications
   - Catches files with `M`, `A`, `D`, `R`, `C` in first column (staged) or `M`, `D` in second column (unstaged)
   - Fixes issue where unstaged modifications (format: ` M`) were not being counted

2. **Accurate Untracked File Counting:**
   - Extracts untracked items using `sed 's/^?? //'` instead of `awk` for better path handling
   - Handles paths with spaces by removing quotes if present
   - Recursively counts all files in untracked directories using `find -type f`
   - Counts individual untracked files as 1

3. **Whitespace Handling:**
   - Uses `tr -d '[:space:]'` instead of `tr -d ' '` to remove all whitespace (including newlines)
   - Prevents arithmetic syntax errors from newlines in `wc -l` output
   - Applied consistently to all count variables (`work_count`, `diff_lines`, `modified_count`, `count`)

4. **Error Handling:**
   - All git commands use `2>/dev/null` to suppress errors when not in a git repo
   - Fallback values (`|| echo "0"`) ensure script continues even if commands fail
   - Empty results handled gracefully with `[ -n "${untracked_items}" ]` check

**Display Options:**

**Option 1: Keep combined display (recommended for now)**
```
status:      5 (   new    )
```
- Shows total of modified + untracked
- No change to output format
- Minimal disruption

**Option 2: Show separate counts (future enhancement)**
```
modified:    2 (   new    )
untracked:   3 (   new    )
```
- Shows modified and untracked separately
- More detailed information
- Requires two output lines

**Option 3: Combined with breakdown in verbose mode**
```
status:      5 (   new    ) (2 modified, 3 untracked)
```
- Shows total in normal mode
- Shows breakdown in verbose mode or with flag

**Recommendation:** Start with Option 1 (keep combined, improve accuracy), then add Option 3 as enhancement.

**Environment:**
- Script: `monitor-ai-agent-progress.sh`
- Git Version: Any modern version
- OS: macOS, Linux (any Unix-like system)
- Shell: Bash

**Files Affected:**
- `monitor-ai-agent-progress.sh` - Lines 217-248 (git status counting logic)
  - Lines 217-218: Updated whitespace handling for `work_count` and `diff_lines`
  - Lines 220-248: New accurate git status counting implementation

**Impact:**
- **Medium:** Improves accuracy of git status tracking
- Better visibility into AI agent file creation activity
- More reliable metrics for monitoring

**Testing Plan:**
1. ✅ Test with single untracked file
2. ✅ Test with untracked directory containing multiple files
3. ✅ Test with nested untracked directories
4. ✅ Test with mix of untracked files and directories
5. ✅ Test with modified files (both staged and unstaged)
6. ✅ Test with paths containing spaces
7. ✅ Performance test with many untracked files
8. ✅ Test arithmetic operations (fixed whitespace handling issue)

**Benefits:**
- ✅ Accurate count of all untracked files
- ✅ Handles untracked directories correctly
- ✅ Works with nested directory structures
- ✅ More reliable than `git status --porcelain | wc -l` for directories

**Issues Resolved:**
- ✅ **Arithmetic syntax error:** Fixed by using `tr -d '[:space:]'` instead of `tr -d ' '` to remove newlines
- ✅ **Unstaged modifications not counted:** Fixed by using pattern `^[MADRC].|^.[MD]` to match both staged and unstaged
- ✅ **Paths with spaces:** Handled by removing quotes with `sed 's/^"//;s/"$//'`
- ✅ **Whitespace in wc output:** Fixed by using `tr -d '[:space:]'` consistently

**Implementation Notes:**
- Uses `2>/dev/null` to suppress errors when not in a git repo
- Handles empty results gracefully with conditional checks
- `find` uses `-type f` to only count files, not directories
- All count variables use consistent whitespace removal pattern

**Actual Complexity:**
- **Low (1-2 hours)** - As estimated
  - Straightforward logic change
  - Required handling edge cases (special characters, whitespace, unstaged modifications)
  - Fixed arithmetic syntax error discovered during testing

**Additional Notes:**
- ✅ This was the first priority in the improvement plan and has been completed
- ✅ Quick win that improves accuracy without changing output format
- ✅ Can be enhanced later with separate display options (Option 3 from Display Options)
- ✅ All edge cases identified in testing have been resolved
