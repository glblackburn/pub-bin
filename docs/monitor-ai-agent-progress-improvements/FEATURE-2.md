# FEATURE-2: Add Process Count Monitoring

**Status:** Completed
**Priority:** High
**Severity:** Low
**Reported:** 2025-12-08
**Completed:** 2025-12-09

**Description:**
Add a fourth metric to monitor system process count. AI agents often spawn multiple processes, and tracking process count can provide better visibility into agent activity level, helping to detect when an agent is actively working versus idle.

**Expected Behavior:**
- Process count should be displayed as a fourth metric
- Process count should track changes (new, increasing, decreasing, stable)
- Process count should be included in audio announcements
- Process count should follow the same format as other metrics

**Current Implementation (lines 15, 23, 34, 40, 134-140, 140, 163, 200, 261-281, 303-309):**

1. **CLI Parameter (line 15):**
   ```bash
   SHOW_PROCESSES=false
   ```

2. **Process Count Function (lines 134-140):**
   ```bash
   function format-process-output {
       local process_count=$1
       local status=$2
       local status_centered=$(center-text "${status}" 10)

       printf "%-10s %6s (%s)\n" "processes:" "${process_count}" "${status_centered}"
   }
   ```

3. **Process Count Retrieval (lines 261-281):**
   ```bash
   # Get process count (FEATURE-2) - only if enabled
   process_count=0
   process_status=""
   if [ "${SHOW_PROCESSES}" = true ] ; then
       # Cross-platform process counting
       if command -v ps >/dev/null 2>&1 ; then
           # Try ps -e first (more portable, shows all processes)
           process_count=$(ps -e 2>/dev/null | wc -l | tr -d '[:space:]' || echo "0")
           # Subtract header line if count > 0
           if [ "${process_count}" -gt 0 ] ; then
               process_count=$((process_count - 1))
           fi
       fi
       process_status=$(get-status "${process_count}" "${prev_process_count}")
   fi
   ```

4. **Conditional Output (lines 303-309):**
   ```bash
   # Add process output only if enabled
   if [ "${SHOW_PROCESSES}" = true ] ; then
       process_output=$(format-process-output "${process_count}" "${process_status}")
       combined_message="${combined_message}
   ${process_output}"
       prev_process_count="${process_count}"
   fi
   ```

5. **CLI Integration:**
   - Added `-p` flag to getopts (line 140)
   - Added `-p` case handler (line 163)
   - Updated usage function to document `-p` option (lines 34, 40)
   - Added to verbose startup output (line 200)

**Output Format:**
```
work:        6 (   new    )
diff:       97 (   new    )
status:      2 (   new    )
processes: 234 (   new    )
```

**Platform Considerations:**
- **macOS/Linux:** `ps aux | wc -l` or `ps -e | wc -l`
- **Cross-platform:** May need OS detection
- **Performance:** `ps` can be slow on systems with many processes
- **Alternative:** Use `/proc` on Linux (faster but Linux-only)

**CLI Changes:**
- Added `-p` flag to show process count (off by default)
- Process count only displayed when `-p` flag is used
- Default behavior: process count hidden (reduces output noise)
- Use `-p` flag when process monitoring is needed

**Audio Announcement:**
- Include process count in combined audio message
- Format: "work X, diff Y, status Z, processes W"

**State Tracking:**
- Add `prev_process_count` variable
- Track min/max process count during session
- Include in exit summary

**Example Output (with `-p` flag):**
```
Mon Dec  8 18:20:00 EST 2025
work:        6 (   new    )
diff:       97 (   new    )
status:      2 (   new    )
processes: 234 (   new    )
```

**Example Output (without `-p` flag, default):**
```
Mon Dec  8 18:20:00 EST 2025
work:        6 (   new    )
diff:       97 (   new    )
status:      2 (   new    )
```

**Environment:**
- Script: `monitor-ai-agent-progress.sh`
- OS: macOS, Linux (any Unix-like system)
- Shell: Bash
- Dependencies: `ps` command (standard on Unix systems)

**Files Affected:**
- `monitor-ai-agent-progress.sh` - Lines 15, 23, 34, 40, 140, 163, 200, 261-280, 290-300
  - Line 15: Added `SHOW_PROCESSES=false` CLI parameter
  - Line 23: Added `prev_process_count` state variable
  - Line 34: Updated usage to include `-p` option
  - Line 40: Added `-p` option description in help
  - Line 140: Added `-p` to getopts
  - Line 163: Added `-p` case handler
  - Line 200: Added to verbose startup output
  - Lines 134-140: Added `format-process-output` function
  - Lines 261-280: Conditional process count retrieval logic
  - Lines 290-300: Conditional process output inclusion

**Impact:**
- **Low:** Adds new metric for better visibility
- Helps identify when agent is spawning processes
- Complements file and git metrics
- Useful for debugging agent behavior

**Benefits:**
- Better visibility into system activity
- Helps identify when agent is spawning processes
- Complements file and git metrics
- Useful for debugging agent behavior

**Potential Issues:**
- `ps` command performance on systems with many processes
- Different `ps` syntax across platforms
- Process count can be noisy (many system processes)
- May need filtering (e.g., exclude system processes)

**Testing:**
- ✅ Test on macOS (verified)
- ⏳ Test on Linux (pending)
- ✅ Test with many processes (performance acceptable)
- ✅ Test with `ps` command unavailable (gracefully handles with fallback to 0)
- ✅ Verify count accuracy (subtracts header line correctly)
- ✅ Verify status tracking (new, increasing, decreasing, stable)
- ✅ Verify audio announcement includes process count

**Actual Complexity:**
- **Low (1 hour)** - Simpler than estimated
  - Straightforward addition following existing patterns
  - Cross-platform handling with `ps -e` works well
  - Performance acceptable even with many processes
  - No CLI changes needed (always shown like other metrics)

**Implementation Notes:**
- Uses `ps -e` for cross-platform compatibility (works on macOS and Linux)
- Uses `tr -d '[:space:]'` for consistent whitespace handling (matches FEATURE-1 pattern)
- Gracefully handles missing `ps` command (returns 0)
- Follows existing code patterns for consistency
- No performance issues observed with typical process counts

**Additional Notes:**
- ✅ This was the second priority in the improvement plan and has been completed
- ✅ Straightforward addition that provides immediate value
- ⏳ Can be enhanced later with filtering options (e.g., exclude system processes)
