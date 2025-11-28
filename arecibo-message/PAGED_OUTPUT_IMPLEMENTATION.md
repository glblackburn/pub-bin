# Paged Output Implementation Plan

## Overview

This document tracks the implementation of paged output functionality for `run_analysis.sh` to improve screen recording and user experience by pausing output at terminal height.

**Selected Approach:** Option 3 (Hybrid Approach) - Terminal height detection enabled by default. See [PAGED_OUTPUT_DESIGN.md](PAGED_OUTPUT_DESIGN.md) for complete design specification and rationale.

## Scripts That Need Changes

### 1. `run_analysis.sh` (Primary Changes)

**File:** `run_analysis.sh`

**Changes Required:**

#### A. Add New Command-Line Flag
- Add `--no-page` flag parsing (to disable paging)
- Add `PAGE_MODE` variable (**default: `true`** - paging enabled by default)
- Support `PAGE_MODE` environment variable (defaults to `true`)

#### B. Add New Functions
- `get_terminal_height()` - Detect terminal height with fallback
- `page_output()` - Pipe output through line counter and pause at terminal height
- `strip_ansi_codes()` - Helper to count lines without ANSI codes (if needed)

#### C. Modify Existing Functions
- `run_step()` - **Change default behavior** to pipe output through `page_output()` (paging enabled by default)
- `show_help()` - Add documentation for `--no-page` flag and explain default paging behavior

#### D. Update Default Settings
- Add `PAGE_MODE=true` to default settings section (**paging enabled by default**)

**Lines to Modify:**
- ~16-19: Default settings (add `PAGE_MODE=true` - **paging enabled by default**)
- ~22-72: Help function (add `--no-page` documentation, explain default paging)
- ~75-111: Argument parsing (add `--no-page` case to disable paging)
- ~170-183: `pause()` function (may need minor updates)
- ~186-215: `run_step()` function (**major changes** - paging is now default, add conditional for `--no-page`)
- ~113-137: Environment variable checks (add `PAGE_MODE` check, default to `true`)

**Estimated Lines Changed:** ~50-80 lines

---

### 2. Python Scripts (No Changes Required)

**Files:** 
- `step1_analyze_structure.py`
- `step2_visualize_patterns.py`
- `step3_identify_sections.py`
- `step4_find_human_figure.py`
- `step5_decode_numbers.py`
- `step6_decode_atomic_numbers.py`
- `decode_analysis.py`
- `get_dimensions.py`

**Status:** ✅ **NO CHANGES NEEDED**

**Reason:** The paging logic will be implemented entirely in the bash wrapper script. Python scripts will continue to output normally, and the bash script will handle paging by piping their output.

---

### 3. `run_analysis_auto.sh` (No Changes Required)

**File:** `run_analysis_auto.sh`

**Status:** ✅ **NO CHANGES NEEDED**

**Reason:** This is a thin wrapper that calls `run_analysis.sh --auto`. Since paging is now the default behavior, it will automatically work. Users can pass `--no-page` through if needed.

---

### 4. Documentation Files (Updates Needed)

#### A. `README.md`

**Changes Required:**
- **Document default paging behavior** (terminal height detection enabled by default)
- Add `--no-page` flag to usage examples (to disable paging)
- Document paged output feature as default behavior
- Add screen recording use case (now the default)
- Update help text examples to show default paging
- Note: This is a change from previous versions

**Sections to Update:**
- "Running the Analysis" section (~lines 113-169)
- Usage examples (show default paging, `--no-page` option)
- Command-line options list (add `--no-page`)

#### B. `PAGED_OUTPUT_DESIGN.md` (Already Created)

**Status:** ✅ **COMPLETE**

**Purpose:** Design document explaining the approach and rationale.

---

## Implementation Details

### Function Signatures

```bash
# Get terminal height, with fallback
get_terminal_height() {
    # Method 1: Try $LINES env var
    # Method 2: Try stty size < /dev/tty (most reliable)
    # Method 3: Try tput lines (if stdin is terminal)
    # Method 4: Fallback to tput lines
    # Returns page size (terminal height - overhead)
}
```

**Implementation Note:** Uses `stty size < /dev/tty` as primary method (after `$LINES` check) because it works reliably even when stdin is redirected. Falls back to `tput lines` if `stty` is unavailable. Recommendation: Fall back to default height (24 lines) if all detection methods fail. This ensures the script works in non-interactive environments, CI/CD pipelines, or when terminal detection is unavailable.

```bash
# Page output by counting lines and pausing at terminal height
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

### Modified run_step() Function

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
        # Original behavior (no paging) - only when --no-page is used
        if [ "$COLOR_MODE" = true ] && ([[ "$script_name" == *"step2"* ]] || [[ "$script_name" == *"step4"* ]] || [[ "$script_name" == *"decode_analysis"* ]]); then
            python3 "$script_name" $COLOR_FLAG
        else
            python3 "$script_name"
        fi
    fi
    
    # ... rest of function (error handling, success message)
}
```

---

## Testing Plan

### Test Cases

1. **Basic Functionality**
   - [x] `./run_analysis.sh` (default) pauses at terminal height - ✅ **PASSED**
   - [x] `./run_analysis.sh --no-page` disables paging (original behavior) - ✅ **PASSED**
   - [x] Terminal height detection works correctly - ✅ **PASSED** (detects 60-line terminal correctly)

2. **Interactive Mode**
   - [x] Pauses wait for Enter keypress - ✅ **PASSED** (uses file descriptor 3)
   - [x] Output continues after Enter - ✅ **PASSED**
   - [x] Step completion pause still works - ✅ **PASSED**

3. **Auto Mode**
   - [x] `./run_analysis.sh --auto` uses timed pauses at terminal height (default) - ✅ **PASSED**
   - [x] `./run_analysis.sh --auto --no-page` disables paging in auto mode - ✅ **PASSED**
   - [x] `PAUSE_TIME` controls pause duration - ✅ **PASSED**
   - [x] Pauses occur at terminal height - ✅ **PASSED**

4. **Color Mode**
   - [x] `./run_analysis.sh --color` preserves colors with default paging - ✅ **PASSED**
   - [x] `./run_analysis.sh --color --no-page` disables paging but keeps colors - ✅ **PASSED**
   - [x] ANSI codes don't break line counting - ✅ **PASSED**
   - [x] Colored output pages correctly - ✅ **PASSED**

5. **Different Terminal Sizes**
   - [x] Small terminal (24 lines) works - ✅ **TESTED** (fallback works)
   - [x] Medium terminal (40 lines) works - ✅ **VERIFIED** (calculation correct)
   - [x] Large terminal (60+ lines) works - ✅ **TESTED** (60-line terminal working)
   - [ ] Terminal resize during execution** - Not applicable (detection happens per step)

6. **Edge Cases**
   - [x] Scripts with very long output - ✅ **PASSED** (step2 with 120 lines works)
   - [x] Scripts with minimal output - ✅ **PASSED** (step1 with 29 lines works)
   - [x] Error output (stderr) is also paged - ✅ **PASSED** (uses `2>&1`)
   - [x] Terminal height detection failure (fallback to 24 lines works correctly) - ✅ **PASSED**
   - [x] Non-interactive environments (CI/CD, scripts) work with fallback - ✅ **VERIFIED**

7. **Backward Compatibility**
   - [x] `--no-page` flag restores original continuous output behavior - ✅ **PASSED**
   - [x] Environment variable `PAGE_MODE=false` disables paging - ✅ **PASSED**
   - [x] Existing scripts/workflows can use `--no-page` to maintain old behavior - ✅ **PASSED**
   - ✅ **Note**: Default behavior changes (paging enabled), but can be disabled

8. **Screen Recording**
   - [x] All output is visible in recording - ✅ **PASSED**
   - [x] Pauses are appropriate for narration - ✅ **PASSED**
   - [x] No content is missed - ✅ **PASSED**

---

## Implementation Checklist

### Phase 1: Core Functionality
- [x] Add `PAGE_MODE=true` variable (default enabled)
- [x] Add `--no-page` flag parsing (to disable paging)
- [x] Implement `get_terminal_height()` function (uses `stty size < /dev/tty`)
- [x] Implement `page_output()` function (with file descriptor 3 for terminal read)
- [x] Modify `run_step()` to use paging by default
- [x] Test basic paging functionality (default behavior) - ✅ Working
- [x] Test `--no-page` flag (backward compatibility) - ✅ Working

### Phase 2: Integration
- [x] Test with all step scripts - ✅ Working
- [x] Test with color mode - ✅ Working
- [x] Test in both interactive and auto modes - ✅ Working
- [x] Handle edge cases (ANSI codes, wrapped lines) - ✅ Handled

### Phase 3: Documentation
- [x] Update `run_analysis.sh` help text (document default paging, `--no-page` flag) - ✅ Complete
- [x] Update `README.md` with default paging behavior and `--no-page` flag - ✅ Complete
- [x] Add usage examples for screen recording (default behavior) - ✅ Complete
- [x] Document environment variable `PAGE_MODE` (defaults to `true`) - ✅ Complete
- [x] Note the change in default behavior from previous versions - ✅ Complete

### Phase 4: Testing & Refinement
- [x] Test with various terminal sizes - ✅ Tested with 24-line and 60-line terminals
- [x] Test screen recording workflow - ✅ Working correctly
- [x] Gather feedback and refine pause timing - ✅ Complete
- [x] Optimize line counting if needed - ✅ Optimized (uses unbuffered Python output)

---

## Risk Assessment

### Low Risk
- ✅ Python scripts unchanged (no risk of breaking analysis)
- ✅ `--no-page` flag provides backward compatibility option
- ⚠️ **Default behavior change** - users expecting continuous output will see paging by default
- ⚠️ Existing scripts/workflows may need `--no-page` flag added

### Medium Risk
- ⚠️ ANSI code handling (may need refinement)
- ⚠️ Line counting accuracy (wrapped lines)
- ⚠️ Terminal detection edge cases

### Mitigation
- **Fallback to default height (24 lines)** if `tput` fails - ensures script works in all environments
- Test thoroughly with colored output
- Test terminal height detection failure scenarios
- Consider simpler initial implementation, refine based on feedback

---

## Dependencies

### Required Tools
- `tput` - Standard POSIX tool (should be available)
- `bash` - Already required (script is bash)

### No New Dependencies
- ✅ No external tools required
- ✅ No Python package changes
- ✅ Pure bash implementation

---

## Timeline Estimate

- **Design:** ✅ Complete
- **Implementation:** 2-4 hours
- **Testing:** 1-2 hours
- **Documentation:** 1 hour
- **Total:** ~4-7 hours

---

## Success Criteria

1. ✅ Paging works by default in both interactive and auto modes - **ACHIEVED**
2. ✅ Terminal height detection is accurate - **ACHIEVED** (uses `stty size < /dev/tty`)
3. ✅ Colors are preserved when paging - **ACHIEVED**
4. ✅ `--no-page` flag restores original continuous output behavior - **ACHIEVED**
5. ✅ Screen recording captures all output clearly (default behavior) - **ACHIEVED**
6. ✅ Documentation clearly explains default paging and `--no-page` option - **ACHIEVED**
7. ✅ Users can easily disable paging if needed - **ACHIEVED**

**Implementation Status:** ✅ **COMPLETE AND WORKING**

All success criteria have been met. The paged output feature is fully functional and tested with 24-line and 60-line terminals. Terminal height detection works correctly using `stty size < /dev/tty`, and paging pauses at the appropriate terminal height for optimal screen recording.

---

## Notes

- Consider starting with simpler implementation (fixed line count) and refining based on feedback
- May need to handle ANSI codes more carefully if line counting is inaccurate
- Terminal height detection should be robust with good fallback
