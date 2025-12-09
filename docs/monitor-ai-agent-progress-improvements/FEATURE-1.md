# FEATURE-1: Improve Git Status Counting

**Status:** Open  
**Priority:** High  
**Severity:** Medium  
**Reported:** 2025-12-08  
**Target:** TBD

**Description:**
The current git status counting method uses `git ls-files --others` which may not accurately count all files in untracked directories. This enhancement will improve accuracy by using `find` to recursively count all files within untracked directories, ensuring all untracked files are properly tracked.

**Current Implementation (lines 217-219):**
```bash
work_count=$(find -L "${work_dir_resolved}" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
diff_lines=$(git diff 2>/dev/null | wc -l | tr -d ' ' || echo "0")
status_count=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ' || echo "0")
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

**Proposed Implementation:**

1. **Get untracked entries from git status:**
   ```bash
   git status --porcelain | grep "^??"
   ```

2. **For each untracked entry:**
   - Check if it's a directory or file
   - If directory: Use `find` to count all files recursively
   - If file: Count as 1
   - Sum all counts

3. **Keep modified count separate:**
   - Continue using current method (already accurate)
   - Display modified and untracked separately (optional enhancement)

**Proposed Code:**

```bash
# Count modified/staged files (M, A, D, R, C in first column)
modified_count=$(git status --porcelain 2>/dev/null | grep -E "^[MADRC]" | wc -l | tr -d ' ' || echo "0")

# Count untracked files accurately using find
untracked_count=0
untracked_items=$(git status --porcelain 2>/dev/null | grep "^??" | awk '{print $2}' || true)

if [ -n "${untracked_items}" ] ; then
    while IFS= read -r item; do
        if [ -n "${item}" ] ; then
            if [ -d "${item}" ] ; then
                # Directory - count all files recursively
                count=$(find "${item}" -type f 2>/dev/null | wc -l | tr -d ' ' || echo "0")
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
- `monitor-ai-agent-progress.sh` - Lines 217-219 (git status counting logic)

**Impact:**
- **Medium:** Improves accuracy of git status tracking
- Better visibility into AI agent file creation activity
- More reliable metrics for monitoring

**Testing Plan:**
1. Test with single untracked file
2. Test with untracked directory containing multiple files
3. Test with nested untracked directories
4. Test with mix of untracked files and directories
5. Test with modified files (ensure still works)
6. Performance test with many untracked files

**Benefits:**
- ✅ Accurate count of all untracked files
- ✅ Handles untracked directories correctly
- ✅ Works with nested directory structures
- ✅ More reliable than `git status --porcelain | wc -l` for directories

**Potential Issues:**
- **Performance:** `find` on large untracked directories might be slow
- **Edge cases:** Need to handle special characters in filenames
- **Git repo check:** Need to ensure we're in a git repo before running git commands

**Implementation Notes:**
- Use `2>/dev/null` to suppress errors
- Handle empty results gracefully
- Ensure `find` doesn't follow symlinks outside repo (use `-L` carefully)
- Consider excluding `.git` directory from find if needed

**Estimated Complexity:**
- **Low (1-2 hours)**
  - Straightforward logic change
  - Need to handle edge cases (special characters, etc.)

**Additional Notes:**
- This is the first priority in the improvement plan
- Quick win that improves accuracy without changing output format
- Can be enhanced later with separate display options
