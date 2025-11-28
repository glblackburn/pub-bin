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

### Option 1: Terminal Height Detection with Line Counting (Recommended)

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

## Recommended Solution: Option 3 (Hybrid Approach) - **UPDATED: Default Enabled**

### Implementation Details

#### 1. Terminal Height Detection
```bash
get_terminal_height() {
    local height=$(tput lines 2>/dev/null || echo 24)
    # Subtract a few lines for header/footer space
    echo $((height - 4))
}
```

**Recommendation:** Fall back to default height (24 lines) if `tput` fails or terminal height cannot be detected. This ensures the script works in non-interactive environments or when terminal detection is unavailable.

#### 2. Paged Output Function
```bash
page_output() {
    local max_lines=$1
    local line_count=0
    local IFS=''
    
    while IFS= read -r line; do
        echo "$line"
        ((line_count++))
        
        if [ $line_count -ge $max_lines ]; then
            if [ "$AUTO_MODE" = true ]; then
                sleep "$PAUSE_TIME"
            else
                echo ""
                echo -e "${YELLOW}Press Enter to continue...${NC}"
                read -r
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
2. ✅ **UPDATED**: Set `PAGE_MODE=true` as default
3. Add `--no-page` flag parsing (to disable paging)
4. Add `get_terminal_height()` function
5. Add `page_output()` function (handle ANSI codes)
6. Modify `run_step()` to use paged output by default
7. Update help text (document default behavior and `--no-page` flag)
8. Test with various terminal sizes
9. Update README.md with new default behavior and `--no-page` flag documentation

## Alternative: Simpler First Implementation

For initial implementation, we could:
- Use `less -R` in interactive mode (though paging is now default)
- In auto mode, use timed pauses at fixed intervals (every N lines)
- Simpler but less precise

**Note:** This alternative approach is not recommended since terminal height detection is now the default. The recommended approach provides better user experience and screen recording support.

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
