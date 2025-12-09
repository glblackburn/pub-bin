# monitor-ai-agent-progress.sh - Next Update Plan

**Date:** December 8, 2025  
**Current Version:** Latest (after commit b95dcae - optional working dir path)

## Recently Completed ✅

1. ✅ Added `-w` flag to optionally show working directory path (hidden by default)
2. ✅ Removed unnecessary `sleep 2` delays (4 seconds per cycle)
3. ✅ Added startup validation for working directory existence
4. ✅ Improved error handling for missing directories

## Next Update Plan

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
  - Display final metrics (work, diff, status counts)
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
       echo "  work:   ${work_count}"
       echo "  diff:   ${diff_lines}"
       echo "  status: ${status_count}"
       echo "Min/Max values:"
       echo "  work:   ${min_work_count} / ${max_work_count}"
       echo "  diff:   ${min_diff_lines} / ${max_diff_lines}"
       echo "  status: ${min_status_count} / ${max_status_count}"
       
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

- **Basic signal handling:** Low (1-2 hours)
- **Exit summary:** Medium (2-3 hours)
- **State persistence:** Medium-High (3-4 hours)
- **Full implementation:** High (4-6 hours)

**Recommendation:** Start with basic signal handling and simple summary, then add state persistence in a follow-up update.
