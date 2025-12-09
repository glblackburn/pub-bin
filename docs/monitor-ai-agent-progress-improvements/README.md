# monitor-ai-agent-progress.sh Improvements

**Date:** December 8, 2025  
**Current Version:** Latest (after commit b95dcae - optional working dir path)

This section tracks planned improvements and enhancements for the `monitor-ai-agent-progress.sh` script. Individual feature plans are tracked in separate documents following the defect tracking pattern.

| ID | Status | Priority | Severity | Title | Description |
|----|--------|----------|----------|-------|-------------|
| [FEATURE-1](FEATURE-1.md) | Completed | High | Medium | Improve Git Status Counting | Accurately count all untracked files, including all files within untracked directories using `find` |
| [FEATURE-2](FEATURE-2.md) | Open | High | Low | Add Process Count Monitoring | Add a fourth metric to monitor system process count for better visibility into AI agent activity |
| [FEATURE-3](FEATURE-3.md) | Open | High | Low | Graceful Exit Handling | Add signal handling for clean shutdown and optional summary on exit |

## Recently Completed ✅

1. ✅ **FEATURE-1: Improve Git Status Counting** - Accurately count all untracked files, including all files within untracked directories using `find`
2. ✅ Added `-w` flag to optionally show working directory path (hidden by default)
3. ✅ Removed unnecessary `sleep 2` delays (4 seconds per cycle)
4. ✅ Added startup validation for working directory existence
5. ✅ Improved error handling for missing directories

## Implementation Order

The following features are planned in priority order:

1. **[FEATURE-1: Improve Git Status Counting](FEATURE-1.md)** - Priority: High
   - Accurately count all untracked files, including all files within untracked directories
   - Estimated: Low (1-2 hours)
   - Quick win that improves accuracy

2. **[FEATURE-2: Add Process Count Monitoring](FEATURE-2.md)** - Priority: High
   - Add a fourth metric to monitor system process count
   - Estimated: Low-Medium (1-2 hours)
   - Straightforward addition with immediate value

3. **[FEATURE-3: Graceful Exit Handling](FEATURE-3.md)** - Priority: High
   - Add signal handling for clean shutdown and optional summary on exit
   - Estimated: Medium-High (4-6 hours for full implementation)
   - Can be implemented incrementally (basic signal handling first)

## Summary

See individual feature documents for detailed specifications, implementation details, testing plans, and code examples.

## Related Improvements

This update sets the foundation for:
- State persistence (Phase 2)
- Historical logging (Phase 3)
- Summary statistics (Phase 3)

## Estimated Complexity

- **FEATURE-1 (Git status improvement):** Low (1-2 hours)
  - Straightforward logic change
  - Need to handle edge cases (special characters, etc.)
- **FEATURE-2 (Process count monitoring):** Low-Medium (1-2 hours)
  - Simple to add, but need to handle cross-platform differences
  - Performance considerations for systems with many processes
- **FEATURE-3 (Graceful exit handling):**
  - Basic signal handling: Low (1-2 hours)
  - Exit summary: Medium (2-3 hours)
  - State persistence: Medium-High (3-4 hours)
  - Full implementation: High (4-6 hours)

**Implementation Recommendation:** 
1. Start with FEATURE-1 (quick fix, improves accuracy)
2. Add FEATURE-2 (straightforward addition, immediate value)
3. Then add basic signal handling and simple summary (FEATURE-3)
4. Finally add state persistence in a follow-up update

## Legend

- **Status:** Open, In Progress, Completed, Closed
- **Priority:** Low, Medium, High, Critical
- **Severity:** Low, Medium, High, Critical
