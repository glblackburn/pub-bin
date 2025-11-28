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
    local height=$(tput lines 2>/dev/null || echo 24)
    # Subtract lines for header/footer space
    echo $((height - 4))
}
```

**Recommendation:** Fall back to default height (24 lines) if `tput` fails or terminal height cannot be detected. This ensures the script works in non-interactive environments, CI/CD pipelines, or when terminal detection is unavailable. The implementation uses `tput lines 2>/dev/null || echo 24` to gracefully handle failures.

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
   - [ ] `./run_analysis.sh` (default) pauses at terminal height
   - [ ] `./run_analysis.sh --no-page` disables paging (original behavior)
   - [ ] Terminal height detection works correctly

2. **Interactive Mode**
   - [ ] Pauses wait for Enter keypress
   - [ ] Output continues after Enter
   - [ ] Step completion pause still works

3. **Auto Mode**
   - [ ] `./run_analysis.sh --auto` uses timed pauses at terminal height (default)
   - [ ] `./run_analysis.sh --auto --no-page` disables paging in auto mode
   - [ ] `PAUSE_TIME` controls pause duration
   - [ ] Pauses occur at terminal height

4. **Color Mode**
   - [ ] `./run_analysis.sh --color` preserves colors with default paging
   - [ ] `./run_analysis.sh --color --no-page` disables paging but keeps colors
   - [ ] ANSI codes don't break line counting
   - [ ] Colored output pages correctly

5. **Different Terminal Sizes**
   - [ ] Small terminal (24 lines) works
   - [ ] Medium terminal (40 lines) works
   - [ ] Large terminal (80+ lines) works
   - [ ] Terminal resize during execution (if possible)

6. **Edge Cases**
   - [ ] Scripts with very long output
   - [ ] Scripts with minimal output
   - [ ] Error output (stderr) is also paged
   - [ ] Terminal height detection failure (fallback to 24 lines works correctly)
   - [ ] Non-interactive environments (CI/CD, scripts) work with fallback

7. **Backward Compatibility**
   - [ ] `--no-page` flag restores original continuous output behavior
   - [ ] Environment variable `PAGE_MODE=false` disables paging
   - [ ] Existing scripts/workflows can use `--no-page` to maintain old behavior
   - [ ] **Note**: Default behavior changes (paging enabled), but can be disabled

8. **Screen Recording**
   - [ ] All output is visible in recording
   - [ ] Pauses are appropriate for narration
   - [ ] No content is missed

---

## Implementation Checklist

### Phase 1: Core Functionality
- [ ] Add `PAGE_MODE=true` variable (default enabled)
- [ ] Add `--no-page` flag parsing (to disable paging)
- [ ] Implement `get_terminal_height()` function
- [ ] Implement `page_output()` function
- [ ] Modify `run_step()` to use paging by default
- [ ] Test basic paging functionality (default behavior)
- [ ] Test `--no-page` flag (backward compatibility)

### Phase 2: Integration
- [ ] Test with all step scripts
- [ ] Test with color mode
- [ ] Test in both interactive and auto modes
- [ ] Handle edge cases (ANSI codes, wrapped lines)

### Phase 3: Documentation
- [ ] Update `run_analysis.sh` help text (document default paging, `--no-page` flag)
- [ ] Update `README.md` with default paging behavior and `--no-page` flag
- [ ] Add usage examples for screen recording (default behavior)
- [ ] Document environment variable `PAGE_MODE` (defaults to `true`)
- [ ] Note the change in default behavior from previous versions

### Phase 4: Testing & Refinement
- [ ] Test with various terminal sizes
- [ ] Test screen recording workflow
- [ ] Gather feedback and refine pause timing
- [ ] Optimize line counting if needed

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

1. ✅ Paging works by default in both interactive and auto modes
2. ✅ Terminal height detection is accurate
3. ✅ Colors are preserved when paging
4. ✅ `--no-page` flag restores original continuous output behavior
5. ✅ Screen recording captures all output clearly (default behavior)
6. ✅ Documentation clearly explains default paging and `--no-page` option
7. ✅ Users can easily disable paging if needed

---

## Notes

- Consider starting with simpler implementation (fixed line count) and refining based on feedback
- May need to handle ANSI codes more carefully if line counting is inaccurate
- Terminal height detection should be robust with good fallback
