# FEATURE-5: Refactor Work Metric Display and Add Working Directory Path Flag

**Status:** Completed
**Priority:** Medium
**Severity:** Low
**Reported:** 2025-12-09
**Completed:** 2025-12-09

**Description:**
Refactor the `-w` flag to work like the `-p` flag (show/hide the entire work metric), and add a new flag to control display of the working directory path separately. This provides better control over what information is displayed.

**Previous Behavior:**
- `-w` flag showed/hid the working directory path in the work metric output
- Work metric was always displayed
- Working directory path was hidden by default (only shown with `-w` flag)

**Current Behavior:**
- `-w` flag shows/hides the entire work metric (like `-p` does for processes)
- Work metric is off by default (hidden)
- `-W` flag shows the working directory path in work metric output
- Working directory path display is independent of work metric visibility
- Path display only relevant when work metric is visible

**Current Implementation (lines 14-15, 48, 99-110, 153, 170, 208, 269-273, 328-332, 341-344, 350-355):**

1. **CLI Parameters (lines 14-15):**
   ```bash
   SHOW_WORK_METRIC=false
   SHOW_WORK_PATH=false
   ```

2. **Refactored `-w` Flag:**
   - Renamed `SHOW_WORKING_DIR` to `SHOW_WORK_METRIC`
   - `-w` flag controls whether work metric is displayed at all
   - Work metric hidden by default (like process metric with `-p`)

3. **New `-W` Flag for Path Display:**
   - Added `-W` flag to getopts (line 153)
   - Added `-W` case handler (line 170)
   - Controls display of working directory path in work metric output
   - Independent of work metric visibility
   - Path display off by default

4. **Optimized Work Count Calculation (lines 269-273):**
   - Work count only calculated when `SHOW_WORK_METRIC=true`
   - Avoids unnecessary `find` operations when work metric is hidden
   - Performance improvement when work metric is disabled

5. **Conditional Work Status Calculation (lines 328-332):**
   - Work status only calculated when work metric is enabled
   - Avoids unnecessary status calculations

6. **Conditional Work Output (lines 350-355):**
   - Work output only included in combined message when enabled
   - Work metric appears first in output (like process metric appears last)

3. **Output Behavior:**
   ```
   # Default (work metric hidden, no path)
   diff:      275 (   new    )
   status:      3 (   new    )

   # With -w (work metric shown, no path)
   work:       45 (   new    )
   diff:      275 (   new    )
   status:      3 (   new    )

   # With -w -W (work metric shown, with path)
   work:       45 (   new    ) (/tmp)
   diff:      275 (   new    )
   status:      3 (   new    )
   ```

**CLI Changes:**
- `-w` flag: Show/hide work metric (off by default, like `-p`)
- New flag (e.g., `-W` or `-P`): Show working directory path in work metric output
- Path display only relevant when work metric is visible

**Alternative Flag Names:**
- `-W` for working directory path (uppercase to match `-w` for work metric)
- `-P` for path (but might conflict with process `-p`)
- `--show-work-path` for long form
- Recommendation: Use `-W` for consistency with `-w`/`-p` pattern

**Implementation Details:**
- Rename `SHOW_WORKING_DIR` to `SHOW_WORK_METRIC`
- Add new `SHOW_WORK_PATH` variable
- Update `format-work-output` function to handle both flags
- Update usage function
- Update getopts and case handlers
- Update verbose startup output

**Files Affected:**
- `monitor-ai-agent-progress.sh` - Lines 14-15, 48, 99-110, 153, 170, 208, 269-273, 328-332, 341-344, 350-355
  - Lines 14-15: Renamed `SHOW_WORKING_DIR` to `SHOW_WORK_METRIC`, added `SHOW_WORK_PATH`
  - Line 48: Updated `-w` description, added `-W` flag description
  - Lines 99-110: Updated `format-work-output` function to use `SHOW_WORK_PATH`
  - Line 153: Added `-W` to getopts string
  - Line 170: Added `-W` case handler
  - Line 208: Updated verbose output
  - Lines 269-273: Optimized work count calculation (only when enabled)
  - Lines 328-332: Conditional work status calculation
  - Lines 341-344: Conditional prev_work_count update
  - Lines 350-355: Conditional work output inclusion

**Impact:**
- **Low-Medium:** Changes default behavior (work metric hidden by default)
- Better consistency with `-p` flag behavior
- More granular control over output
- Breaking change for users who expect work metric by default

**Benefits:**
- Consistent behavior between `-w` and `-p` flags
- More control over output display
- Cleaner default output (fewer metrics)
- Separates metric visibility from path display

**Issues Resolved:**
- ✅ **Breaking Change:** Work metric now hidden by default (consistent with `-p` flag behavior)
- ✅ **Flag Naming:** Used `-W` for path display (uppercase, matches `-w` pattern)
- ✅ **Performance:** Work count calculation optimized (only runs when metric enabled)
- ✅ **Consistency:** Work metric behavior now matches process metric behavior

**Testing:**
- ✅ Test work metric display with/without `-w` flag
- ✅ Test path display with/without `-W` flag
- ✅ Test combination of flags (`-w -W`)
- ✅ Test default behavior (work metric hidden)
- ✅ Verify work count calculation only runs when enabled
- ✅ Verify work status calculation only runs when enabled
- ✅ Test with audio changes-only flag (`-c`)

**Actual Complexity:**
- **Low (1 hour)** - As estimated
  - Straightforward refactoring
  - Similar to `-p` flag implementation
  - Performance optimization by skipping work count when disabled

**Questions to Answer:**
1. **Should work metric be hidden by default?**
   - Recommendation: Yes, for consistency with `-p` flag
   - But this is a breaking change

2. **What flag name for path display?**
   - Options: `-W`, `-P`, `--show-work-path`
   - Recommendation: `-W` (uppercase, matches `-w` pattern)

3. **Should path display require work metric to be visible?**
   - Recommendation: Yes, path only makes sense when work metric is shown
   - Could show warning if path flag used without `-w`

**Implementation Notes:**
- Work metric now follows same pattern as process metric (`-p` flag)
- Path display is independent of metric visibility
- Performance optimized: work count and status only calculated when needed
- Audio changes-only flag (`-c`) correctly handles work metric visibility
- Breaking change: users who relied on work metric by default need to add `-w` flag

**Additional Notes:**
- ✅ This refactoring improves consistency with the `-p` flag pattern
- ✅ Separates concerns: metric visibility vs. path display
- ✅ Performance improvement: avoids unnecessary `find` operations when work metric disabled
- ✅ Breaking change documented and implemented for consistency
