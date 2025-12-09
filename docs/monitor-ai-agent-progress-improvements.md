# monitor-ai-agent-progress.sh - Improvement Plan

**Date:** December 7, 2025  
**Current Version:** Latest (as of commit 2e103ba)

## Current State Analysis

### What the Script Does
- Monitors AI agent activity by tracking:
  - Working directory file count (`/tmp` by default)
  - Git diff line count
  - Git status file count
- Provides audio feedback using `say` command
- Tracks status changes (new, increasing, decreasing, stable)
- Displays formatted, column-aligned output
- Runs in infinite loop with configurable interval

### Current Features
- ✅ CLI options: `-h`, `-q`, `-v`, `-i <interval>`, `-t <working_dir>`, `-r`
- ✅ Status tracking for all three metrics
- ✅ Audio feedback (can be disabled with `-q`)
- ✅ Timestamp display (always shown)
- ✅ Repository name display (optional with `-r`)
- ✅ Verbose mode for startup configuration
- ✅ Follows shell-template.sh patterns

## Issues Identified

### 1. ✅ **Unnecessary Sleep Delays** - FIXED
**Problem:** There were `sleep 2` commands between output formatting calls adding 4 seconds of delay per cycle.

**Status:** ✅ Fixed - Removed sleep delays in commit

### 2. ✅ **Working Directory Path Always Displayed** - FIXED
**Problem:** The working directory path was always shown in output, cluttering the display.

**Status:** ✅ Fixed - Added `-w` flag to optionally show path, hidden by default

### 3. ✅ **No Working Directory Validation** - FIXED
**Problem:** Script didn't validate that working directory exists at startup.

**Status:** ✅ Fixed - Added startup validation with clear error message

### 4. **No Graceful Exit Mechanism**
**Problem:** Script runs in infinite loop with no way to gracefully exit (except Ctrl+C).

**Impact:**
- Can't clean up or save state on exit
- No signal handling for clean shutdown
- Ctrl+C might interrupt operations mid-cycle

**Recommendation:** Add signal handling (SIGINT, SIGTERM) for graceful exit.

### 3. **No State Persistence**
**Problem:** Previous state is lost when script exits.

**Impact:**
- On restart, all metrics show "new" status
- Can't resume monitoring with historical context
- No way to track changes across script restarts

**Recommendation:** Optional state file to persist previous values.

### 4. **Limited Error Handling**
**Problem:** Some operations don't handle errors gracefully:
- `git rev-parse --show-toplevel` might fail if not in git repo
- `find` might fail if directory doesn't exist
- `say` command might not be available on all systems

**Impact:**
- Script might fail silently or with unclear errors
- Not all edge cases are handled

**Recommendation:** Improve error handling and provide fallbacks.

### 7. **No Rate Limiting for Audio**
**Problem:** Audio feedback happens every interval, which could be frequent.

**Impact:**
- Could be annoying if interval is short
- No way to throttle audio announcements

**Recommendation:** Add option to limit audio frequency or only announce on status changes.

### 8. **No Historical Tracking**
**Problem:** Only tracks current vs previous state, no history.

**Impact:**
- Can't see trends over time
- No way to identify patterns in activity

**Recommendation:** Optional logging to track metrics over time.

### 7. ✅ **Working Directory Validation** - FIXED
**Problem:** Script didn't validate that working directory exists or is accessible.

**Status:** ✅ Fixed - Added startup validation with clear error message

### 9. **No Configuration File Support**
**Problem:** All configuration is via CLI options only.

**Impact:**
- Have to remember and type options each time
- Can't set defaults for personal preferences

**Recommendation:** Support config file (similar to `config/config.sh` pattern).


## Proposed Improvements

### High Priority

1. ✅ **Remove unnecessary sleep delays** - COMPLETED
   - Removed `sleep 2` commands
   - Immediate improvement in responsiveness

2. ✅ **Make working directory path display optional** - COMPLETED
   - Added `-w` flag to show/hide path
   - Path hidden by default for cleaner output

3. ✅ **Add working directory validation** - COMPLETED
   - Validates directory exists at startup
   - Clear error message on invalid directory

4. **Add graceful exit handling**
   - Trap SIGINT and SIGTERM
   - Display final summary on exit
   - Clean shutdown

5. **Improve error handling**
   - Better git operation error messages
   - Enhanced fallback for `say` command
   - More informative error reporting

### Medium Priority

4. **Add state persistence**
   - Optional state file to save previous values
   - Resume monitoring with historical context
   - Use `~/.config/pub-bin/monitor-state` or similar

5. **Add working directory validation**
   - Check directory exists at startup
   - Validate permissions
   - Clear error messages

6. **Improve audio feedback options**
   - Option to only announce on status changes
   - Minimum time between audio announcements
   - Different audio for different metric types

### Lower Priority

7. **Add configuration file support**
   - Use `config/config.sh` pattern
   - Store default interval, working directory, etc.
   - Interactive setup if config missing

8. **Add historical logging**
   - Optional log file to track metrics over time
   - CSV format for easy analysis
   - Rotate logs to prevent growth

9. **Add summary statistics**
   - Show min/max/average over monitoring session
   - Display on exit or with special option

10. **Add multiple working directory support**
    - Monitor multiple directories
    - Aggregate or separate reporting

## Implementation Plan

### Phase 1: Quick Fixes (Immediate) - ✅ COMPLETED
1. ✅ Remove `sleep 2` delays
2. ✅ Make working directory path optional (hide by default, show with flag)
3. ✅ Add working directory validation at startup
4. ⏳ Add basic signal handling (NEXT)
5. ⏳ Improve error messages (NEXT)

### Phase 2: Enhancements (Short-term)
4. Add working directory validation
5. Improve error handling throughout
6. Add state persistence option

### Phase 3: Advanced Features (Long-term)
7. Configuration file support
8. Historical logging
9. Summary statistics

## Testing Considerations

- Test in non-git directory
- Test with invalid working directory
- Test signal handling (Ctrl+C)
- Test with `say` command unavailable
- Test state persistence across restarts
- Test with various interval values
- Test quiet and verbose modes

## Questions to Consider

1. **Should state persistence be default or opt-in?**
   - Recommendation: Opt-in with `-s` flag or config option

2. **Should audio be more configurable?**
   - Recommendation: Add `-a` flag for audio options (always, changes-only, off)

3. **Should we add a summary mode?**
   - Recommendation: Add `-S` flag to show summary and exit

4. **Should we support multiple metrics in one output?**
   - Current: All three metrics together
   - Alternative: Option to select which metrics to monitor

5. **Should we add a dry-run mode?**
   - Recommendation: Add `-n` flag to show what would be monitored without running

## Related Files

- `shell-template.sh` - Pattern to follow for CLI options and structure
- `config/config.sh` - Pattern for configuration management
- `README.md` - Documentation that needs updating if changes are made

## Notes

- Script was featured in LinkedIn post on November 10, 2025
- Recent commits show active development (5 commits since November 1)
- Follows shell-template.sh patterns (good foundation)
- Current implementation is functional but has room for improvement
