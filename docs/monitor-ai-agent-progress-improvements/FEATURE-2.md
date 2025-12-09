# FEATURE-2: Add Process Count Monitoring

**Status:** Open
**Priority:** High
**Severity:** Low
**Reported:** 2025-12-08
**Target:** TBD

**Description:**
Add a fourth metric to monitor system process count. AI agents often spawn multiple processes, and tracking process count can provide better visibility into agent activity level, helping to detect when an agent is actively working versus idle.

**Expected Behavior:**
- Process count should be displayed as a fourth metric
- Process count should track changes (new, increasing, decreasing, stable)
- Process count should be included in audio announcements
- Process count should follow the same format as other metrics

**Proposed Implementation:**

1. **Add Process Count Metric**
   - Use `ps` command to count running processes
   - Track process count changes (new, increasing, decreasing, stable)
   - Display in same format as other metrics

2. **Output Format:**
   ```
   work:        6 (   new    )
   diff:       97 (   new    )
   status:      2 (   new    )
   processes: 234 (   new    )
   ```

3. **Implementation Details:**
   - Use `ps aux | wc -l` or `ps -e | wc -l` (OS-dependent)
   - Subtract 1 for header line
   - Track previous count for status calculation
   - Include in audio announcement

**Proposed Code:**

```bash
# Get process count (cross-platform)
if command -v ps >/dev/null 2>&1 ; then
    # Try ps -e first (more portable)
    process_count=$(ps -e 2>/dev/null | wc -l | tr -d ' ' || echo "0")
    # Subtract header line
    if [ "${process_count}" -gt 0 ] ; then
        process_count=$((process_count - 1))
    fi
else
    process_count=0
fi
```

**Platform Considerations:**
- **macOS/Linux:** `ps aux | wc -l` or `ps -e | wc -l`
- **Cross-platform:** May need OS detection
- **Performance:** `ps` can be slow on systems with many processes
- **Alternative:** Use `/proc` on Linux (faster but Linux-only)

**CLI Changes:**
- No new flags needed initially
- Process count always shown (like work/diff/status)
- Optional: Add `-p` flag to hide process count if desired

**Audio Announcement:**
- Include process count in combined audio message
- Format: "work X, diff Y, status Z, processes W"

**State Tracking:**
- Add `prev_process_count` variable
- Track min/max process count during session
- Include in exit summary

**Example Output:**
```
Mon Dec  8 18:20:00 EST 2025
work:        6 (   new    )
diff:       97 (   new    )
status:      2 (   new    )
processes: 234 (   new    )
```

**Environment:**
- Script: `monitor-ai-agent-progress.sh`
- OS: macOS, Linux (any Unix-like system)
- Shell: Bash
- Dependencies: `ps` command (standard on Unix systems)

**Files Affected:**
- `monitor-ai-agent-progress.sh` - Add process count logic and display

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
- Test on macOS
- Test on Linux
- Test with many processes (performance)
- Test with `ps` command unavailable
- Verify count accuracy

**Estimated Complexity:**
- **Low-Medium (1-2 hours)**
  - Simple to add, but need to handle cross-platform differences
  - Performance considerations for systems with many processes

**Additional Notes:**
- This is the second priority in the improvement plan
- Straightforward addition that provides immediate value
- Can be enhanced later with filtering options
