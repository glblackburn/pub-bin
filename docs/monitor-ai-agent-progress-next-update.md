# monitor-ai-agent-progress.sh - Next Update Plan

**Date:** December 8, 2025  
**Current Version:** Latest (after commit b95dcae - optional working dir path)

## Recently Completed ✅

1. ✅ Added `-w` flag to optionally show working directory path (hidden by default)
2. ✅ Removed unnecessary `sleep 2` delays (4 seconds per cycle)
3. ✅ Added startup validation for working directory existence
4. ✅ Improved error handling for missing directories

## Next Update Plan

### Priority: High - Improve Git Status Counting

**Goal:** Accurately count all untracked files, including all files within untracked directories.

**Why This Matters:**
- Current method uses `git ls-files --others` which may not count all files in untracked directories
- Untracked entries from `git status --porcelain` can be directories
- Need to use `find` to recursively count all files in untracked directories
- More accurate tracking of AI agent file creation activity

**Current Implementation (lines 220-230):**
```bash
# Count modified/staged files (M, A, D, R, C in first column)
modified_count=$(git status --porcelain 2>/dev/null | grep -E "^[MADRC]" | wc -l | tr -d ' ' || echo "0")

# Count untracked files
# git status --porcelain shows "??" for untracked, but these could be directories
# Use git ls-files --others --exclude-standard to get all untracked files
untracked_count=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ' || echo "0")

# Total status count is modified + untracked
status_count=$((modified_count + untracked_count))
```

**Issue:**
- `git ls-files --others` may not accurately count all files in untracked directories
- Especially problematic with nested untracked directories
- Edge cases with gitignore patterns

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

**Testing:**
- Test with single untracked file
- Test with untracked directory containing multiple files
- Test with nested untracked directories
- Test with mix of untracked files and directories
- Test with modified files (ensure still works)
- Performance test with many untracked files

### Priority: High - Add Process Count Monitoring

**Goal:** Add a fourth metric to monitor system process count.

**Why This Matters:**
- AI agents often spawn multiple processes
- Process count can indicate agent activity level
- Useful for detecting when agent is actively working vs idle
- Complements existing metrics (files, git changes)

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

**Implementation Code:**
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

**Testing:**
- Test on macOS
- Test on Linux
- Test with many processes (performance)
- Test with `ps` command unavailable
- Verify count accuracy

### Priority: High - Graceful Exit Handling

**Goal:** Add signal handling for clean shutdown and optional summary on exit.

**Why This Matters:**
- Currently, Ctrl+C just kills the script immediately
- No way to see final state or summary
- Can't save state before exit
- Interrupts might happen mid-cycle

**Proposed Implementation:**

1. **Add Signal Trapping**
   ```bash
   trap cleanup_on_exit SIGINT SIGTERM
   ```

2. **Create Cleanup Function**
   - Display final metrics summary
   - Optionally save state to file
   - Clean exit with status code

3. **Add Exit Summary Option**
   - Show min/max/average for session
   - Show total monitoring time
   - Show final status of all metrics

**Features to Add:**

- **Signal Handling:**
  - Trap SIGINT (Ctrl+C) and SIGTERM
  - Call cleanup function before exit
  - Prevent multiple interrupts from causing issues

- **Exit Summary:**
  - Display final metrics (work, diff, status, processes counts)
  - Show session duration
  - Show min/max values seen during session
  - Optional: Show trend (increasing/decreasing/stable)

- **State Saving (Optional):**
  - Save current state to file on exit
  - Allow resuming with `-r` flag (resume)
  - State file: `~/.config/pub-bin/monitor-state`

**CLI Changes:**

- Add `-S` or `--summary` flag: Show summary and exit (don't monitor)
- Add `-s` or `--save-state` flag: Save state on exit
- Add `-r` or `--resume` flag: Resume from saved state

**Example Usage:**

```bash
# Normal monitoring with graceful exit
./monitor-ai-agent-progress.sh -i 5
# Ctrl+C shows summary and exits cleanly

# Show summary and exit (no monitoring)
./monitor-ai-agent-progress.sh -S

# Save state on exit
./monitor-ai-agent-progress.sh -i 5 -s

# Resume from saved state
./monitor-ai-agent-progress.sh -i 5 -r
```

**Implementation Details:**

1. **State Tracking Variables:**
   - `session_start_time` - Track when monitoring started
   - `min_work_count`, `max_work_count` - Track min/max values
   - `min_diff_lines`, `max_diff_lines`
   - `min_status_count`, `max_status_count`
   - `min_process_count`, `max_process_count` - Track process count min/max
   - `total_cycles` - Count monitoring cycles

2. **Cleanup Function:**
   ```bash
   function cleanup_on_exit {
       local exit_code=$?
       echo ""
       echo "=== Monitoring Session Summary ==="
       echo "Duration: $(calculate_duration)"
       echo "Cycles: ${total_cycles}"
       echo "Final state:"
       echo "  work:      ${work_count}"
       echo "  diff:      ${diff_lines}"
       echo "  status:    ${status_count}"
       echo "  processes: ${process_count}"
       echo "Min/Max values:"
       echo "  work:      ${min_work_count} / ${max_work_count}"
       echo "  diff:      ${min_diff_lines} / ${max_diff_lines}"
       echo "  status:    ${min_status_count} / ${max_status_count}"
       echo "  processes: ${min_process_count} / ${max_process_count}"
       
       if [ "${SAVE_STATE}" = true ] ; then
           save_state_to_file
       fi
       
       exit ${exit_code}
   }
   ```

3. **State File Format:**
   ```json
   {
     "prev_work_count": "6",
     "prev_diff_count": "97",
     "prev_status_count": "2",
     "prev_process_count": "234",
     "last_update": "2025-12-08T18:20:00Z"
   }
   ```

**Benefits:**
- Better user experience with graceful shutdown
- Ability to see session summary
- Optional state persistence for resuming
- Professional script behavior

**Testing:**
- Test Ctrl+C handling
- Test SIGTERM handling
- Test summary display
- Test state saving/loading
- Test resume functionality
- Test with various interrupt scenarios

## Alternative: Simpler First Step

If the full implementation is too complex, start with:

1. **Basic Signal Handling:**
   - Trap SIGINT
   - Display simple "Exiting..." message
   - Clean exit

2. **Simple Summary:**
   - Show final metrics on exit
   - No min/max tracking initially
   - No state persistence initially

This provides immediate value while keeping complexity low.

## Questions to Answer

1. **Should summary be always shown on exit, or only with flag?**
   - Recommendation: Always show on signal interrupt, optional with `-S` flag

2. **Should state persistence be opt-in or default?**
   - Recommendation: Opt-in with `-s` flag

3. **What format for state file?**
   - Options: JSON, simple key=value, or structured text
   - Recommendation: Simple key=value for bash compatibility

4. **Should resume automatically detect state file?**
   - Recommendation: Explicit `-r` flag to resume, don't auto-detect

## Related Improvements

This update sets the foundation for:
- State persistence (Phase 2)
- Historical logging (Phase 3)
- Summary statistics (Phase 3)

## Estimated Complexity

- **Git status improvement:** Low (1-2 hours)
  - Straightforward logic change
  - Need to handle edge cases (special characters, etc.)
- **Process count monitoring:** Low-Medium (1-2 hours)
  - Simple to add, but need to handle cross-platform differences
  - Performance considerations for systems with many processes
- **Basic signal handling:** Low (1-2 hours)
- **Exit summary:** Medium (2-3 hours)
- **State persistence:** Medium-High (3-4 hours)
- **Full implementation:** High (4-6 hours)

**Recommendation:** 
1. Start with git status improvement (quick fix, improves accuracy)
2. Add process count monitoring (straightforward addition, immediate value)
3. Then add basic signal handling and simple summary
4. Finally add state persistence in a follow-up update

**Implementation Order:**
1. Improve git status counting (quick win, improves accuracy)
2. Add process count metric (quick win, immediate value)
3. Add graceful exit handling (improves UX)
4. Add state persistence (advanced feature)
