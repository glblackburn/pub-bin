# Design: Paged Output for Screen Recording

## Problem Statement

The current `run_analysis.sh` script outputs all content from each step at once, which causes:
- Content scrolling past the terminal height too quickly
- Users missing important output during screen recording
- Difficulty following the analysis flow visually

## Requirements

1. **Pause at terminal height**: Automatically pause when output reaches terminal height
2. **Pause after each step**: Continue existing behavior of pausing between steps
3. **Screen recording friendly**: Make it easy to capture all output without missing content
4. **Backward compatible**: Existing functionality should still work
5. **Configurable**: Allow users to enable/disable paged output

## Design Approach

### Option 1: Terminal Height Detection with Line Counting

**How it works:**
- Detect terminal height using `tput lines`
- Buffer script output and count lines
- When output reaches terminal height, pause for user input
- Continue displaying remaining output in chunks
- After step completes, pause again (existing behavior)

**Pros:**
- Precise control over when to pause
- Works with any terminal size
- Can be made configurable
- Doesn't require external tools

**Cons:**
- More complex implementation
- Need to handle ANSI color codes correctly when counting lines

### Option 2: Use `less` Pager

**How it works:**
- Pipe each step's output through `less -R` (preserve colors)
- User presses space to continue
- After step completes, pause again

**Pros:**
- Simple implementation
- Standard Unix tool
- Handles colors with `-R` flag
- Familiar interface

**Cons:**
- Less control over exact pause points
- Requires user interaction (not ideal for auto mode)
- May not work well with auto mode

### Option 3: Hybrid Approach (Best for Screen Recording)

**How it works:**
- In interactive mode: Use terminal height detection with automatic pauses
- In auto mode: Use timed pauses at terminal height
- **Default: Terminal height detection enabled** (paged output is default)
- Add `--no-page` flag to disable paged output (for backward compatibility)

**Pros:**
- Best of both worlds
- Screen recording friendly by default
- Better user experience (no content scrolling past)
- Still configurable for users who want continuous output

**Cons:**
- More complex implementation
- Need to handle both modes
- Changes default behavior (may affect existing workflows)

## Selected Solution: Option 3 (Hybrid Approach) - **Default Enabled**

**Status:** ✅ **SELECTED AND APPROVED**

This approach has been selected as the implementation approach. Terminal height detection is enabled by default, with `--no-page` flag available for backward compatibility.

### Implementation Details

#### 1. Terminal Height Detection
```bash
get_terminal_height() {
    # Method 1: Check $LINES environment variable
    # Method 2: Use stty size < /dev/tty (most reliable)
    # Method 3: Try tput lines (if stdin is terminal)
    # Method 4: Fallback to tput lines
    # Returns page size (terminal height - overhead)
}
```

**Implementation:** Uses `stty size < /dev/tty` as the primary detection method (after `$LINES` check) because it works reliably even when stdin is redirected. Falls back to `tput lines` if `stty` is unavailable.

**Recommendation:** Fall back to default height (24 lines) if all detection methods fail. This ensures the script works in non-interactive environments or when terminal detection is unavailable.

#### 2. Paged Output Function
```bash
page_output() {
    local max_lines=$1
    local line_count=0
    local IFS=''
    
    # Open file descriptor 3 to /dev/tty for interactive read
    exec 3< /dev/tty
    
    while IFS= read -r line; do
        echo "$line"
        ((line_count++))
        
        if [ $line_count -ge $max_lines ]; then
            if [ "$AUTO_MODE" = true ]; then
                sleep "$PAUSE_TIME"
            else
                echo ""
                echo -e "${YELLOW}Press Enter to continue...${NC}"
                read -r <&3  # Read from terminal, not stdin
            fi
            line_count=0
        fi
    done
}
```

#### 3. Modified run_step Function
```bash
run_step() {
    local step_num=$1
    local script_name=$2
    local description=$3
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}STEP $step_num: $description${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    if [ ! -f "$script_name" ]; then
        echo -e "${YELLOW}Warning: $script_name not found, skipping...${NC}"
        return
    fi
    
    # Run script with paged output (default behavior)
    if [ "$PAGE_MODE" != false ]; then
        local terminal_height=$(get_terminal_height)
        if [ "$COLOR_MODE" = true ] && ([[ "$script_name" == *"step2"* ]] || [[ "$script_name" == *"step4"* ]] || [[ "$script_name" == *"decode_analysis"* ]]); then
            python3 "$script_name" $COLOR_FLAG 2>&1 | page_output "$terminal_height"
        else
            python3 "$script_name" 2>&1 | page_output "$terminal_height"
        fi
    else
        # Original behavior (no paging) - for backward compatibility
        if [ "$COLOR_MODE" = true ] && ([[ "$script_name" == *"step2"* ]] || [[ "$script_name" == *"step4"* ]] || [[ "$script_name" == *"decode_analysis"* ]]); then
            python3 "$script_name" $COLOR_FLAG
        else
            python3 "$script_name"
        fi
    fi
    
    # ... rest of function
}
```

### Command-Line Interface

**Default behavior:** Terminal height detection is **enabled by default**

Add new flag:
- `--no-page`: Disable paged output (use original continuous output behavior)

**Usage Examples:**
```bash
# Default: Interactive mode with paged output (best for screen recording)
./run_analysis.sh

# Auto mode with paged output (default) and timed pauses
./run_analysis.sh --auto --pause-time 2

# Paged output with colors (default paging)
./run_analysis.sh --color

# Disable paging (use original continuous output)
./run_analysis.sh --no-page

# Disable paging in auto mode
./run_analysis.sh --auto --no-page
```

### Environment Variable

Add `PAGE_MODE` environment variable:
- **Default:** `true` (paged output enabled)
- `PAGE_MODE=0` or `PAGE_MODE=false`: Disable paged output
- `PAGE_MODE=1` or `PAGE_MODE=true`: Enable paged output (default)

## Edge Cases to Handle

1. **ANSI Color Codes**: Don't count color codes as lines
   - Solution: Strip ANSI codes when counting, but preserve in output
   - Use `sed` or similar to count actual display lines

2. **Very Long Lines**: Lines that wrap should count as multiple lines
   - Solution: Use `tput cols` to detect width, calculate wraps

3. **Terminal Size Changes**: Terminal resized during execution
   - Solution: Re-detect height before each step (simpler) or on each pause (more complex)

4. **Auto Mode**: How to handle pauses in auto mode
   - Solution: Use `PAUSE_TIME` for pauses at terminal height in auto mode

5. **Error Output**: stderr should also be paged
   - Solution: Redirect stderr to stdout (`2>&1`) before paging

## Testing Considerations

1. Test with different terminal sizes (small, medium, large)
2. Test with colored output enabled
3. Test in both interactive and auto modes
4. Test with scripts that produce varying amounts of output
5. Test screen recording to ensure all content is visible

## Implementation Steps

1. ✅ Create design document (this file)
2. ✅ Set `PAGE_MODE=true` as default
3. ✅ Add `--no-page` flag parsing (to disable paging)
4. ✅ Add `get_terminal_height()` function (uses `stty size < /dev/tty`)
5. ✅ Add `page_output()` function (handles ANSI codes, uses file descriptor 3 for terminal read)
6. ✅ Modify `run_step()` to use paged output by default
7. ✅ Update help text (document default behavior and `--no-page` flag)
8. ✅ Test with various terminal sizes (24-line and 60-line tested)
9. ✅ Update README.md with new default behavior and `--no-page` flag documentation
10. ✅ Add `--debug` flag for troubleshooting
11. ✅ Fix terminal detection issues (changed from `tput` to `stty`)
12. ✅ Reduce debug output verbosity

**Status:** ✅ **IMPLEMENTATION COMPLETE**

## Alternative: Simpler First Implementation

For initial implementation, we could:
- Use `less -R` in interactive mode (though paging is now default)
- In auto mode, use timed pauses at fixed intervals (every N lines)
- Simpler but less precise

**Note:** This alternative approach is not selected since terminal height detection (Option 3) is now the default. The selected approach (Option 3) provides better user experience and screen recording support.

This could be refined later based on user feedback.

## Questions to Resolve

1. **Default behavior**: Should paging be enabled by default, or opt-in?
   - **✅ RESOLVED**: **Default enabled** - Terminal height detection is the default mode
   - **Rationale**: Better user experience, screen recording friendly, prevents content scrolling past

2. **Auto mode paging**: Should auto mode pause at terminal height, or just between steps?
   - **Recommendation**: Pause at terminal height in auto mode too, using `PAUSE_TIME`

3. **Line counting**: How to handle ANSI codes and wrapped lines?
   - **Recommendation**: Strip ANSI codes for counting, detect wraps using terminal width

4. **Terminal detection failure**: What if `tput` fails?
   - **Recommendation**: Fall back to default height (24 lines)
   - **Implementation**: Use `tput lines 2>/dev/null || echo 24` to gracefully handle failures
   - **Rationale**: Ensures script works in non-interactive environments, CI/CD pipelines, or when terminal detection is unavailable

5. **Backward compatibility**: How to handle users who want original behavior?
   - **✅ RESOLVED**: Add `--no-page` flag to disable paging for backward compatibility

---

## Implementation Status

**Status:** ✅ **IMPLEMENTATION COMPLETE AND WORKING**

The paged output feature has been successfully implemented and tested. Key achievements:

- ✅ Terminal height detection works correctly using `stty size < /dev/tty` (detects 60-line terminal accurately)
- ✅ Paging pauses at terminal height as designed (~50 lines for 60-line terminal)
- ✅ Interactive pauses work correctly using file descriptor 3 (`read -r <&3`)
- ✅ All test cases passed (interactive mode, auto mode, color mode, various terminal sizes)
- ✅ Screen recording workflow verified - all output visible, appropriate pauses
- ✅ Debug mode (`--debug` flag) available for troubleshooting
- ✅ Backward compatibility maintained with `--no-page` flag

The feature is ready for production use and provides optimal screen recording experience.
