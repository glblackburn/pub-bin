# FEATURE-4: Audio Changes Only Mode

**Status:** Completed
**Priority:** Medium
**Severity:** Low
**Reported:** 2025-12-09
**Completed:** 2025-12-09

**Description:**
Add a flag to only run the `say` command (audio feedback) when metrics are increasing or decreasing, reducing audio noise when all metrics are stable.

**Current Behavior:**
- Audio feedback occurs every cycle (every interval seconds)
- Audio announces even when all metrics are stable
- Can be noisy during periods of inactivity

**Expected Behavior:**
- With `-c` flag: Audio only announces when at least one metric is increasing or decreasing
- Without `-c` flag: Audio announces every cycle (existing behavior)
- Reduces audio noise during stable periods

**Current Implementation (lines 16, 49, 153, 170, 208, 150-171, 341-352):**

1. **CLI Parameter (line 16):**
   ```bash
   AUDIO_CHANGES_ONLY=false
   ```

2. **CLI Option (lines 49, 153, 170):**
   - Added `-c` flag to getopts string
   - Added `-c` case handler
   - Updated usage function to document option

3. **Status Change Detection Function (lines 150-171):**
   ```bash
   function has-status-changes {
       local work_status=$1
       local diff_status=$2
       local status_status=$3
       local process_status=$4

       # Check if any status is "increasing" or "decreasing"
       if [ "${work_status}" = "increasing" ] || [ "${work_status}" = "decreasing" ] ; then
           return 0
       fi
       if [ "${diff_status}" = "increasing" ] || [ "${diff_status}" = "decreasing" ] ; then
           return 0
       fi
       if [ "${status_status}" = "increasing" ] || [ "${status_status}" = "decreasing" ] ; then
           return 0
       fi
       if [ -n "${process_status}" ] && ( [ "${process_status}" = "increasing" ] || [ "${process_status}" = "decreasing" ] ) ; then
           return 0
       fi

       # No changes detected
       return 1
   }
   ```

4. **Audio Logic (lines 341-352):**
   ```bash
   if [ "${QUIET}" != true ] ; then
       # Check if we should announce based on changes-only flag
       should_announce=true
       if [ "${AUDIO_CHANGES_ONLY}" = true ] ; then
           if ! has-status-changes "${work_status}" "${diff_status}" "${status_status}" "${process_status}" ; then
               should_announce=false
           fi
       fi

       if [ "${should_announce}" = true ] ; then
           echo "${combined_message}" | say || true
       fi
   fi
   ```

**Usage:**
```bash
# Normal mode - audio every cycle
./monitor-ai-agent-progress.sh -i 5

# Audio only when metrics change
./monitor-ai-agent-progress.sh -i 5 -c

# Quiet mode overrides changes-only flag
./monitor-ai-agent-progress.sh -i 5 -c -q  # No audio
```

**Behavior:**
- **Default (no `-c`):** Audio announces every cycle regardless of status
- **With `-c` flag:** Audio only announces when at least one metric is "increasing" or "decreasing"
- **With `-q` flag:** No audio (overrides `-c` flag)
- Status values checked: "increasing", "decreasing" (excludes "new", "stable")

**Files Affected:**
- `monitor-ai-agent-progress.sh` - Lines 16, 49, 153, 170, 208, 150-171, 341-352
  - Line 16: Added `AUDIO_CHANGES_ONLY=false` CLI parameter
  - Line 49: Added `-c` option description in help
  - Line 153: Added `-c` to getopts string
  - Line 170: Added `-c` case handler
  - Line 208: Added to verbose startup output
  - Lines 150-171: Added `has-status-changes` function
  - Lines 341-352: Modified audio announcement logic

**Impact:**
- **Low-Medium:** Improves user experience by reducing audio noise
- Useful for long-running monitoring sessions
- Reduces interruptions during stable periods

**Benefits:**
- Reduces audio noise during stable periods
- Still announces when activity is detected
- Optional feature (opt-in with `-c` flag)
- Maintains backward compatibility (default behavior unchanged)

**Testing:**
- ✅ Test with `-c` flag when metrics are stable (no audio)
- ✅ Test with `-c` flag when metrics are changing (audio plays)
- ✅ Test without `-c` flag (audio every cycle)
- ✅ Test with `-q` flag (no audio, overrides `-c`)
- ✅ Test with process monitoring enabled/disabled

**Estimated Complexity:**
- **Low (30 minutes)**
  - Straightforward logic addition
  - Simple status checking function
  - Minimal code changes

**Implementation Notes:**
- Uses existing status values ("increasing", "decreasing", "stable", "new")
- Checks all four metrics (work, diff, status, processes)
- Handles case where process monitoring is disabled (empty process_status)
- Maintains backward compatibility (default behavior unchanged)

**Additional Notes:**
- This feature addresses the "No Rate Limiting for Audio" issue mentioned in the improvement plan
- Provides a simple solution without complex rate limiting logic
- Can be combined with other flags (`-p`, `-r`, `-w`, etc.)
