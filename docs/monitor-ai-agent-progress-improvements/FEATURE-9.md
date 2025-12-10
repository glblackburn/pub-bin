# FEATURE-9: Summary Statistics

**Status:** Open  
**Priority:** Low  
**Severity:** Low  
**Reported:** 2025-12-09  
**Target:** TBD

**Description:**
Add summary statistics to show min/max/average values over the monitoring session. This provides insights into the range of activity, peak values, and overall trends during the monitoring period. Statistics can be displayed on exit or with a special option.

**Current Behavior:**
- Only shows current values
- No summary of session activity
- Can't see min/max values reached
- No way to understand overall activity range

**Expected Behavior:**
- Show min/max/average values for all metrics
- Display statistics on exit (with FEATURE-3) or with special option
- Track statistics during monitoring session
- Optionally show statistics from historical log (FEATURE-8)

**Proposed Implementation:**

1. **Statistics to Track:**
   - Min/max/average for each metric:
     - Work count
     - Diff lines
     - Status count
     - Process count (if enabled)
   - Total number of monitoring cycles
   - Session duration
   - Number of status changes (increasing/decreasing events)

2. **Display Options:**
   - Option A: Display on exit (integrated with FEATURE-3)
   - Option B: Display with `-S` or `--summary` flag (show and exit)
   - Option C: Display periodically during monitoring (optional)
   - **Recommendation:** Options A and B

3. **Statistics Calculation:**
   - Track min/max during monitoring loop
   - Calculate average: sum of all values / number of cycles
   - Count status changes during session
   - Calculate session duration

4. **Historical Statistics (Optional):**
   - If FEATURE-8 (Historical Logging) is enabled, can analyze log file
   - Show statistics for entire log history
   - Compare current session to historical averages

**Proposed Code:**

**Statistics Tracking Variables:**
```bash
# Add to state tracking section
min_work_count=""
max_work_count=""
total_work_count=0
work_count_samples=0

min_diff_lines=""
max_diff_lines=""
total_diff_lines=0
diff_lines_samples=0

min_status_count=""
max_status_count=""
total_status_count=0
status_count_samples=0

min_process_count=""
max_process_count=""
total_process_count=0
process_count_samples=0

total_cycles=0
session_start_time=$(date +%s)
status_changes=0
```

**Statistics Update Function:**
```bash
function update_statistics {
    # Update work count statistics
    if [ "${SHOW_WORK_METRIC}" = true ] ; then
        if [ -z "${min_work_count}" ] || [ "${work_count}" -lt "${min_work_count}" ] ; then
            min_work_count="${work_count}"
        fi
        if [ -z "${max_work_count}" ] || [ "${work_count}" -gt "${max_work_count}" ] ; then
            max_work_count="${work_count}"
        fi
        total_work_count=$((total_work_count + work_count))
        work_count_samples=$((work_count_samples + 1))
    fi
    
    # Update diff lines statistics
    if [ -z "${min_diff_lines}" ] || [ "${diff_lines}" -lt "${min_diff_lines}" ] ; then
        min_diff_lines="${diff_lines}"
    fi
    if [ -z "${max_diff_lines}" ] || [ "${diff_lines}" -gt "${max_diff_lines}" ] ; then
        max_diff_lines="${diff_lines}"
    fi
    total_diff_lines=$((total_diff_lines + diff_lines))
    diff_lines_samples=$((diff_lines_samples + 1))
    
    # Update status count statistics
    if [ -z "${min_status_count}" ] || [ "${status_count}" -lt "${min_status_count}" ] ; then
        min_status_count="${status_count}"
    fi
    if [ -z "${max_status_count}" ] || [ "${status_count}" -gt "${max_status_count}" ] ; then
        max_status_count="${status_count}"
    fi
    total_status_count=$((total_status_count + status_count))
    status_count_samples=$((status_count_samples + 1))
    
    # Update process count statistics (if enabled)
    if [ "${SHOW_PROCESSES}" = true ] ; then
        if [ -z "${min_process_count}" ] || [ "${process_count}" -lt "${min_process_count}" ] ; then
            min_process_count="${process_count}"
        fi
        if [ -z "${max_process_count}" ] || [ "${process_count}" -gt "${max_process_count}" ] ; then
            max_process_count="${process_count}"
        fi
        total_process_count=$((total_process_count + process_count))
        process_count_samples=$((process_count_samples + 1))
    fi
    
    # Count status changes
    if [ "${work_status}" = "increasing" ] || [ "${work_status}" = "decreasing" ] ; then
        status_changes=$((status_changes + 1))
    fi
    if [ "${diff_status}" = "increasing" ] || [ "${diff_status}" = "decreasing" ] ; then
        status_changes=$((status_changes + 1))
    fi
    if [ "${status_status}" = "increasing" ] || [ "${status_status}" = "decreasing" ] ; then
        status_changes=$((status_changes + 1))
    fi
    if [ "${SHOW_PROCESSES}" = true ] && ([ "${process_status}" = "increasing" ] || [ "${process_status}" = "decreasing" ]) ; then
        status_changes=$((status_changes + 1))
    fi
    
    total_cycles=$((total_cycles + 1))
}
```

**Statistics Display Function:**
```bash
function display_statistics {
    local session_end_time=$(date +%s)
    local session_duration=$((session_end_time - session_start_time))
    local hours=$((session_duration / 3600))
    local minutes=$(((session_duration % 3600) / 60))
    local seconds=$((session_duration % 60))
    
    echo ""
    echo "=== Monitoring Session Summary ==="
    echo "Duration: ${hours}h ${minutes}m ${seconds}s"
    echo "Cycles: ${total_cycles}"
    echo "Status Changes: ${status_changes}"
    echo ""
    echo "Statistics:"
    
    # Work count statistics
    if [ "${SHOW_WORK_METRIC}" = true ] && [ "${work_count_samples}" -gt 0 ] ; then
        local avg_work=$((total_work_count / work_count_samples))
        echo "  Work Count:"
        echo "    Min: ${min_work_count}"
        echo "    Max: ${max_work_count}"
        echo "    Avg: ${avg_work}"
    fi
    
    # Diff lines statistics
    if [ "${diff_lines_samples}" -gt 0 ] ; then
        local avg_diff=$((total_diff_lines / diff_lines_samples))
        echo "  Diff Lines:"
        echo "    Min: ${min_diff_lines}"
        echo "    Max: ${max_diff_lines}"
        echo "    Avg: ${avg_diff}"
    fi
    
    # Status count statistics
    if [ "${status_count_samples}" -gt 0 ] ; then
        local avg_status=$((total_status_count / status_count_samples))
        echo "  Status Count:"
        echo "    Min: ${min_status_count}"
        echo "    Max: ${max_status_count}"
        echo "    Avg: ${avg_status}"
    fi
    
    # Process count statistics
    if [ "${SHOW_PROCESSES}" = true ] && [ "${process_count_samples}" -gt 0 ] ; then
        local avg_process=$((total_process_count / process_count_samples))
        echo "  Process Count:"
        echo "    Min: ${min_process_count}"
        echo "    Max: ${max_process_count}"
        echo "    Avg: ${avg_process}"
    fi
    
    echo ""
    echo "Final State:"
    if [ "${SHOW_WORK_METRIC}" = true ] ; then
        echo "  work:      ${work_count}"
    fi
    echo "  diff:      ${diff_lines}"
    echo "  status:    ${status_count}"
    if [ "${SHOW_PROCESSES}" = true ] ; then
        echo "  processes: ${process_count}"
    fi
}
```

**CLI Changes:**

- Add `-S` or `--summary` flag: Show summary statistics and exit (don't monitor)
- Statistics automatically displayed on exit (with FEATURE-3)
- No additional flags needed for exit summary (integrated with graceful exit)

**Example Usage:**

```bash
# Normal monitoring - statistics shown on exit (Ctrl+C)
./monitor-ai-agent-progress.sh -i 5
# ... monitoring ...
# Ctrl+C shows statistics and exits

# Show summary and exit immediately (no monitoring)
./monitor-ai-agent-progress.sh -S

# Show summary from historical log (if FEATURE-8 enabled)
./monitor-ai-agent-progress.sh -S --log-file ~/.config/pub-bin/monitor-history.log
```

**Example Output:**

```
=== Monitoring Session Summary ===
Duration: 2h 15m 30s
Cycles: 162
Status Changes: 45

Statistics:
  Work Count:
    Min: 6
    Max: 127
    Avg: 42
  Diff Lines:
    Min: 0
    Max: 275
    Avg: 97
  Status Count:
    Min: 0
    Max: 15
    Avg: 3
  Process Count:
    Min: 234
    Max: 287
    Avg: 256

Final State:
  work:      42
  diff:      97
  status:    3
  processes: 256
```

**Integration with Other Features:**

- **FEATURE-3 (Graceful Exit):** Statistics displayed in cleanup function
- **FEATURE-8 (Historical Logging):** Can analyze log file for historical statistics
- **FEATURE-7 (State Persistence):** Can save statistics to state file

**Files Affected:**
- `monitor-ai-agent-progress.sh`
  - Add statistics tracking variables
  - Add `update_statistics` function
  - Add `display_statistics` function
  - Integrate statistics tracking into main loop
  - Integrate statistics display into FEATURE-3 cleanup function
  - Add `-S` flag handling

**Impact:**
- **Low Risk:** Additive feature, doesn't affect core functionality
- **User Experience:** Provides valuable insights into monitoring session
- **Performance:** Minimal (simple arithmetic operations)
- **Breaking Change:** None (additive feature)

**Benefits:**
- Understand activity range during session
- Identify peak values
- See overall trends
- Useful for performance analysis
- Helps with debugging and optimization
- Provides context for monitoring results

**Potential Issues:**
- Integer division for averages (may lose precision)
- Memory usage for tracking (minimal, but consider for very long sessions)
- Statistics calculation overhead (minimal)

**Testing:**
- Test statistics tracking during monitoring
- Test min/max calculation
- Test average calculation
- Test statistics display on exit
- Test `-S` flag (show and exit)
- Test with different metric combinations (work, processes enabled/disabled)
- Test with very long monitoring sessions
- Test with zero cycles (edge case)
- Test integration with FEATURE-3 (graceful exit)
- Test integration with FEATURE-8 (historical log analysis)

**Estimated Complexity:**
- **Low-Medium (2-3 hours)**
  - Statistics tracking logic
  - Display formatting
  - Integration with exit handling
  - Testing various scenarios

**Future Enhancements:**
- Calculate standard deviation
- Show percentiles (25th, 50th, 75th, 95th)
- Show trend analysis (increasing/decreasing trends)
- Compare current session to historical averages
- Export statistics to file (JSON, CSV)
- Show statistics for specific time ranges

**Questions to Answer:**
1. **Should statistics be always calculated or opt-in?**
   - Recommendation: Always calculated (minimal overhead), opt-in display

2. **Should statistics include standard deviation?**
   - Recommendation: Future enhancement, not required initially

3. **Should statistics be saved to file?**
   - Recommendation: Optional enhancement, can use FEATURE-8 log file

4. **How to handle integer division precision?**
   - Recommendation: Use integer division (bash limitation), document precision

**Additional Notes:**
- This is Phase 3 in the improvement plan
- Works well with FEATURE-3 (Graceful Exit) for exit summary
- Can leverage FEATURE-8 (Historical Logging) for historical analysis
- Statistics tracking has minimal performance impact
- Can be enhanced with more sophisticated analysis later
