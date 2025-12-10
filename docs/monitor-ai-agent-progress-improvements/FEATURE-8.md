# FEATURE-8: Historical Logging

**Status:** Open  
**Priority:** Low  
**Severity:** Low  
**Reported:** 2025-12-09  
**Target:** TBD

**Description:**
Add optional historical logging to track metrics over time in a log file. This enables trend analysis, pattern identification, and historical review of AI agent activity. Logs are stored in CSV format for easy analysis and can be rotated to prevent unlimited growth.

**Current Behavior:**
- Only tracks current vs previous state
- No historical data is preserved
- Can't see trends over time
- No way to identify patterns in activity

**Expected Behavior:**
- Optional log file to track metrics over time
- CSV format for easy analysis
- Rotate logs to prevent unlimited growth
- Configurable log file location and rotation policy
- Timestamp each log entry

**Proposed Implementation:**

1. **Log File Location:**
   - Default: `~/.config/pub-bin/monitor-history.log`
   - Optional: Allow custom location via CLI flag
   - Create directory structure if it doesn't exist

2. **Log File Format (CSV):**
   ```csv
   timestamp,work_count,diff_lines,status_count,process_count,repo_name,branch_name,work_status,diff_status,status_status,process_status
   2025-12-09T14:00:00Z,6,97,2,234,pub-bin,main,new,new,new,new
   2025-12-09T14:01:00Z,7,98,3,235,pub-bin,main,increasing,increasing,increasing,increasing
   2025-12-09T14:02:00Z,7,98,3,235,pub-bin,main,stable,stable,stable,stable
   ```

3. **Logging Behavior:**
   - Log every monitoring cycle (every interval)
   - Optional: Log only on state changes (reduces log size)
   - Include all enabled metrics
   - Include status information (new, increasing, decreasing, stable)
   - Include repository and branch info (if enabled)

4. **Log Rotation:**
   - Option A: Size-based rotation (e.g., rotate at 10MB)
   - Option B: Time-based rotation (e.g., daily, weekly)
   - Option C: Entry-count-based rotation (e.g., rotate at 10,000 entries)
   - **Recommendation:** Size-based with optional time-based

5. **Rotation Strategy:**
   - Keep N rotated log files (e.g., keep 5 rotated files)
   - Rotated files: `monitor-history.log.1`, `monitor-history.log.2`, etc.
   - Oldest rotated file is deleted when limit reached
   - Compress old rotated files (optional enhancement)

**Proposed Code:**

**Log Entry Function:**
```bash
function log_metrics_to_file {
    local log_file="${HOME}/.config/pub-bin/monitor-history.log"
    local log_dir=$(dirname "${log_file}")
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Create directory if it doesn't exist
    mkdir -p "${log_dir}" 2>/dev/null || return 1
    
    # Check if log file exists, write header if new
    if [ ! -f "${log_file}" ] ; then
        echo "timestamp,work_count,diff_lines,status_count,process_count,repo_name,branch_name,work_status,diff_status,status_status,process_status" > "${log_file}"
    fi
    
    # Write log entry
    {
        echo "${timestamp},${work_count:-0},${diff_lines:-0},${status_count:-0},${process_count:-0},${repo_name:-},${branch_name:-},${work_status:-},${diff_status:-},${status_status:-},${process_status:-}"
    } >> "${log_file}" 2>/dev/null || return 1
    
    # Check log file size and rotate if needed
    rotate_log_if_needed "${log_file}"
}
```

**Log Rotation Function:**
```bash
function rotate_log_if_needed {
    local log_file=$1
    local max_size_mb=${LOG_MAX_SIZE_MB:-10}  # Default 10MB
    local max_size_bytes=$((max_size_mb * 1024 * 1024))
    local keep_rotated=${LOG_KEEP_ROTATED:-5}  # Keep 5 rotated files
    
    if [ ! -f "${log_file}" ] ; then
        return 0
    fi
    
    local file_size=$(stat -f%z "${log_file}" 2>/dev/null || stat -c%s "${log_file}" 2>/dev/null || echo "0")
    
    if [ "${file_size}" -gt "${max_size_bytes}" ] ; then
        # Rotate log files
        for i in $(seq $((keep_rotated - 1)) -1 1); do
            if [ -f "${log_file}.${i}" ] ; then
                mv "${log_file}.${i}" "${log_file}.$((i + 1))" 2>/dev/null
            fi
        done
        
        # Move current log to .1
        mv "${log_file}" "${log_file}.1" 2>/dev/null
        
        # Recreate log file with header
        echo "timestamp,work_count,diff_lines,status_count,process_count,repo_name,branch_name,work_status,diff_status,status_status,process_status" > "${log_file}"
    fi
}
```

**CLI Changes:**

- Add `-L` or `--log` flag: Enable historical logging
- Add `--log-file` option: Specify custom log file location
- Add `--log-max-size` option: Set maximum log file size before rotation (default: 10MB)
- Add `--log-keep` option: Set number of rotated log files to keep (default: 5)
- Add `--log-changes-only` option: Only log when metrics change (reduces log size)

**Example Usage:**

```bash
# Enable logging with defaults
./monitor-ai-agent-progress.sh -i 5 -L

# Enable logging with custom file and size
./monitor-ai-agent-progress.sh -i 5 -L --log-file /tmp/monitor.log --log-max-size 50

# Enable logging, only log changes
./monitor-ai-agent-progress.sh -i 5 -L --log-changes-only
```

**Integration with Other Features:**

- **FEATURE-7 (State Persistence):** Can use log file to reconstruct state
- **FEATURE-3 (Graceful Exit):** Can log final state on exit
- **FEATURE-9 (Summary Statistics):** Can analyze log file for statistics

**Files Affected:**
- `monitor-ai-agent-progress.sh`
  - Add `log_metrics_to_file` function
  - Add `rotate_log_if_needed` function
  - Add CLI flags (`-L`, `--log-file`, `--log-max-size`, `--log-keep`, `--log-changes-only`)
  - Integrate logging into main monitoring loop
  - Add log rotation logic

**Impact:**
- **Low Risk:** Opt-in feature, doesn't affect default behavior
- **User Experience:** Enables historical analysis
- **Performance:** Minimal (file append operation, rotation check)
- **Storage:** Log files will grow over time (mitigated by rotation)
- **Breaking Change:** None (additive feature)

**Benefits:**
- Track metrics over time
- Identify patterns in activity
- Historical review of agent activity
- Enable trend analysis
- Useful for debugging and optimization
- CSV format allows easy analysis with tools (Excel, Python, etc.)

**Potential Issues:**
- Log file growth (mitigated by rotation)
- Disk space usage
- File I/O performance with large logs
- Log file corruption
- File permissions issues
- Multiple script instances writing to same log (consider locking)

**Testing:**
- Test log file creation and directory creation
- Test CSV format correctness
- Test log rotation at size threshold
- Test log rotation with multiple rotated files
- Test log file permissions
- Test with missing log directory (should create)
- Test with read-only log directory (should handle gracefully)
- Test `--log-changes-only` option
- Test custom log file location
- Test log file analysis with CSV tools
- Test performance with large log files

**Estimated Complexity:**
- **Medium (2-3 hours)**
  - CSV formatting and writing
  - Log rotation logic
  - File size checking
  - Error handling
  - Testing various scenarios

**Analysis Tools:**

The CSV format enables easy analysis with various tools:

**Python Example:**
```python
import pandas as pd
df = pd.read_csv('~/.config/pub-bin/monitor-history.log')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.plot(x='timestamp', y='diff_lines')
```

**Command Line Example:**
```bash
# Count entries
wc -l ~/.config/pub-bin/monitor-history.log

# Show last 10 entries
tail -10 ~/.config/pub-bin/monitor-history.log

# Filter by status
grep "increasing" ~/.config/pub-bin/monitor-history.log
```

**Questions to Answer:**
1. **Should logging be opt-in or default?**
   - Recommendation: Opt-in with `-L` flag

2. **What rotation strategy?**
   - Options: Size-based, time-based, entry-count-based
   - Recommendation: Size-based with configurable threshold

3. **Should old logs be compressed?**
   - Recommendation: Optional enhancement, not required initially

4. **Should logging be conditional (only on changes)?**
   - Recommendation: Optional with `--log-changes-only` flag

5. **How many rotated files to keep?**
   - Recommendation: Configurable, default 5

**Additional Notes:**
- This is Phase 3 in the improvement plan
- Builds on FEATURE-7 (State Persistence)
- Enables FEATURE-9 (Summary Statistics) to analyze historical data
- CSV format chosen for compatibility and ease of analysis
- Consider adding log compression for old rotated files (future enhancement)
- Consider adding time-based rotation (daily/weekly) as alternative to size-based
