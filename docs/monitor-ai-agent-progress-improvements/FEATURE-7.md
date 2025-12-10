# FEATURE-7: State Persistence

**Status:** Open  
**Priority:** Medium  
**Severity:** Low  
**Reported:** 2025-12-09  
**Target:** TBD

**Description:**
Add optional state persistence to save previous metric values to a file, allowing the script to resume monitoring with historical context. This enables tracking changes across script restarts and provides continuity when the script is stopped and restarted.

**Current Behavior:**
- Previous state is lost when script exits
- On restart, all metrics show "new" status
- Can't resume monitoring with historical context
- No way to track changes across script restarts

**Expected Behavior:**
- Optional state file to save previous values
- Resume monitoring with historical context
- State persists across script restarts
- Graceful handling when state file is missing or corrupted
- Configurable state file location

**Proposed Implementation:**

1. **State File Location:**
   - Default: `~/.config/pub-bin/monitor-state`
   - Optional: Allow custom location via CLI flag or config
   - Create directory structure if it doesn't exist

2. **State File Format:**
   - Option A: Simple key=value format (bash-friendly)
   - Option B: JSON format (more structured, requires `jq` or similar)
   - **Recommendation:** Simple key=value for bash compatibility

3. **State Data to Persist:**
   - `prev_work_count` (if work metric enabled)
   - `prev_diff_count`
   - `prev_status_count`
   - `prev_process_count` (if process metric enabled)
   - `prev_repo_name` (if repo name tracking enabled)
   - `prev_branch_name` (if branch tracking enabled)
   - `last_update` timestamp

4. **Save Behavior:**
   - Save on script exit (normal or signal interrupt)
   - Optional: Save periodically during monitoring
   - Save on state changes (optional enhancement)

5. **Load Behavior:**
   - Load state file on script startup
   - Use loaded values as previous values for first iteration
   - Graceful fallback if state file missing or invalid
   - Validate state file format before loading

**Proposed Code:**

**State File Format (key=value):**
```bash
# State file: ~/.config/pub-bin/monitor-state
prev_work_count=6
prev_diff_count=97
prev_status_count=2
prev_process_count=234
prev_repo_name=pub-bin
prev_branch_name=main
last_update=2025-12-09T14:00:00Z
```

**Save State Function:**
```bash
function save_state_to_file {
    local state_file="${HOME}/.config/pub-bin/monitor-state"
    local state_dir=$(dirname "${state_file}")
    
    # Create directory if it doesn't exist
    mkdir -p "${state_dir}" 2>/dev/null || return 1
    
    # Save state to file
    {
        echo "# monitor-ai-agent-progress.sh state file"
        echo "# Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
        echo "prev_work_count=${prev_work_count:-0}"
        echo "prev_diff_count=${prev_diff_count:-0}"
        echo "prev_status_count=${prev_status_count:-0}"
        echo "prev_process_count=${prev_process_count:-0}"
        echo "prev_repo_name=${prev_repo_name:-}"
        echo "prev_branch_name=${prev_branch_name:-}"
        echo "last_update=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    } > "${state_file}" 2>/dev/null || return 1
}
```

**Load State Function:**
```bash
function load_state_from_file {
    local state_file="${HOME}/.config/pub-bin/monitor-state"
    
    if [ ! -f "${state_file}" ] ; then
        return 0  # No state file, start fresh
    fi
    
    # Load state from file (source it)
    # Use safe sourcing to avoid code injection
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "${key}" =~ ^#.*$ ]] && continue
        [[ -z "${key}" ]] && continue
        
        # Validate key names (whitelist approach)
        case "${key}" in
            prev_work_count|prev_diff_count|prev_status_count|prev_process_count|prev_repo_name|prev_branch_name|last_update)
                eval "${key}=\"${value}\""
                ;;
        esac
    done < "${state_file}"
}
```

**CLI Changes:**

- Add `-s` or `--save-state` flag: Save state on exit
- Add `-l` or `--load-state` flag: Load state on startup (default behavior)
- Add `-S` or `--state-file` option: Specify custom state file location
- Default: Auto-save on exit, auto-load on startup (opt-in with `-s` flag)

**Example Usage:**

```bash
# Normal monitoring with state persistence (opt-in)
./monitor-ai-agent-progress.sh -i 5 -s

# Load state from custom location
./monitor-ai-agent-progress.sh -i 5 -s -S /tmp/my-state-file

# Disable state persistence
./monitor-ai-agent-progress.sh -i 5  # No -s flag, no state saved/loaded
```

**Integration with FEATURE-3:**

This feature works well with FEATURE-3 (Graceful Exit Handling):
- State is saved in the cleanup function on exit
- State is loaded at script startup
- Exit summary can show when state was last saved

**Files Affected:**
- `monitor-ai-agent-progress.sh`
  - Add `save_state_to_file` function
  - Add `load_state_from_file` function
  - Add CLI flags (`-s`, `-S`)
  - Integrate with startup and exit logic
  - Integrate with FEATURE-3 cleanup function

**Impact:**
- **Low Risk:** Opt-in feature, doesn't affect default behavior
- **User Experience:** Provides continuity across restarts
- **Performance:** Minimal (file I/O on startup/exit only)
- **Breaking Change:** None (additive feature)

**Benefits:**
- Resume monitoring with historical context
- Track changes across script restarts
- Better continuity for long-running monitoring
- Useful for automated monitoring scenarios
- Enables better trend analysis

**Potential Issues:**
- State file corruption or invalid format
- File permissions issues
- State file location not writable
- Race conditions if multiple instances run simultaneously
- Security concerns with sourcing state file (mitigated with whitelist)

**Testing:**
- Test state file creation and directory creation
- Test state file loading on startup
- Test state file saving on exit
- Test with missing state file (graceful fallback)
- Test with corrupted state file (graceful fallback)
- Test with invalid state file format
- Test with file permission issues
- Test with custom state file location
- Test integration with FEATURE-3 (graceful exit)
- Test multiple script instances (file locking consideration)

**Estimated Complexity:**
- **Medium-High (3-4 hours)**
  - File I/O operations
  - State file format design and parsing
  - Error handling for various edge cases
  - Security considerations (safe file sourcing)
  - Integration with exit handling
  - Testing various failure scenarios

**Security Considerations:**
- Use whitelist approach when loading state file
- Validate all values before using them
- Don't source state file directly (parse line by line)
- Handle special characters in values safely
- Consider file locking for multi-instance scenarios

**Questions to Answer:**
1. **Should state persistence be opt-in or default?**
   - Recommendation: Opt-in with `-s` flag

2. **What format for state file?**
   - Options: JSON, simple key=value, or structured text
   - Recommendation: Simple key=value for bash compatibility

3. **When should state be saved?**
   - Options: On exit only, periodically, on state changes
   - Recommendation: On exit (with FEATURE-3), optionally periodically

4. **Should state file be locked?**
   - Recommendation: Consider file locking if multiple instances might run

5. **How to handle state file corruption?**
   - Recommendation: Validate format, fallback to fresh start if invalid

**Additional Notes:**
- This is Phase 2 in the improvement plan
- Sets foundation for historical logging (FEATURE-8)
- Works well with FEATURE-3 (graceful exit handling)
- Can be enhanced later with periodic saves or state change triggers
- Consider adding state file rotation or cleanup for old state files
