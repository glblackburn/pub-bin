# Analysis: Combining run_analysis.sh and run_analysis_auto.sh

## Current State

Two separate scripts with ~95% code duplication:

### Differences Found:

1. **Pause mechanism:**
   - `run_analysis.sh`: Uses `read -r` (waits for user input)
   - `run_analysis_auto.sh`: Uses `sleep $PAUSE_TIME` (timed pause)

2. **Header message:**
   - `run_analysis.sh`: "Arecibo Message Analysis"
   - `run_analysis_auto.sh`: "Arecibo Message Analysis (Auto Mode)" + pause time display

3. **Complete analysis prompt:**
   - `run_analysis.sh`: Includes optional prompt to run complete analysis
   - `run_analysis_auto.sh`: No prompt, just finishes

4. **Final pause:**
   - `run_analysis.sh`: Pauses after step 6
   - `run_analysis_auto.sh`: No pause after step 6

5. **Environment variable:**
   - `run_analysis_auto.sh`: Uses `PAUSE_TIME` env var (default: 3 seconds)
   - `run_analysis.sh`: No env var support

## Recommended Changes

### Option 1: Single Script with Command-Line Flag (Recommended)

**Script name:** `run_analysis.sh`

**Changes:**
1. Add `--auto` or `-a` flag for auto mode
2. Add `--pause-time` or `-t` flag to set pause duration (default: 3)
3. Detect mode based on flag or environment variable
4. Keep interactive mode as default (backward compatible)
5. Add `--no-complete` flag to skip complete analysis prompt

**Usage:**
```bash
# Interactive mode (default)
./run_analysis.sh

# Auto mode with default 3-second pauses
./run_analysis.sh --auto

# Auto mode with custom pause time
./run_analysis.sh --auto --pause-time 5

# Short form
./run_analysis.sh -a -t 5

# Skip complete analysis prompt
./run_analysis.sh --auto --no-complete
```

**Benefits:**
- Single script to maintain
- Backward compatible (default behavior unchanged)
- Flexible configuration
- Clear command-line interface

### Option 2: Single Script with Environment Variable

**Script name:** `run_analysis.sh`

**Changes:**
1. Check `AUTO_MODE` environment variable
2. If `AUTO_MODE=1` or `AUTO_MODE=true`, use auto mode
3. Use `PAUSE_TIME` env var for pause duration (default: 3)
4. Keep interactive as default

**Usage:**
```bash
# Interactive mode (default)
./run_analysis.sh

# Auto mode
AUTO_MODE=1 ./run_analysis.sh

# Auto mode with custom pause
AUTO_MODE=1 PAUSE_TIME=5 ./run_analysis.sh
```

**Benefits:**
- Simple implementation
- Environment-based configuration
- Less code changes needed

**Drawbacks:**
- Less discoverable than flags
- Requires environment variable documentation

### Option 3: Single Script with Both Methods

**Script name:** `run_analysis.sh`

**Changes:**
1. Support both command-line flags AND environment variables
2. Command-line flags take precedence over env vars
3. Default to interactive mode if neither specified

**Usage:**
```bash
# All of these work:
./run_analysis.sh
./run_analysis.sh --auto
AUTO_MODE=1 ./run_analysis.sh
AUTO_MODE=1 ./run_analysis.sh --auto  # flag overrides env var
```

**Benefits:**
- Maximum flexibility
- Supports both CLI and env var users
- Most user-friendly

## Recommended Implementation (Option 1)

### Code Structure:

```bash
#!/bin/bash
# Parse command-line arguments
AUTO_MODE=false
PAUSE_TIME=3
RUN_COMPLETE=true

while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--auto)
            AUTO_MODE=true
            shift
            ;;
        -t|--pause-time)
            PAUSE_TIME="$2"
            shift 2
            ;;
        --no-complete)
            RUN_COMPLETE=false
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to pause based on mode
pause() {
    if [ "$AUTO_MODE" = true ]; then
        echo ""
        echo -e "${YELLOW}Waiting ${PAUSE_TIME} seconds before next step...${NC}"
        sleep "$PAUSE_TIME"
        echo ""
    else
        echo ""
        echo -e "${YELLOW}Press Enter to continue to next step...${NC}"
        read -r
        echo ""
    fi
}

# Update header based on mode
if [ "$AUTO_MODE" = true ]; then
    echo -e "${BLUE}Arecibo Message Analysis (Auto Mode)${NC}"
    echo -e "${YELLOW}Pause time: ${PAUSE_TIME} seconds${NC}"
else
    echo -e "${BLUE}Arecibo Message Analysis${NC}"
fi
```

### Additional Features to Add:

1. **Help message:** `--help` or `-h` flag
2. **Version info:** `--version` flag
3. **Skip steps:** `--skip-step N` to skip specific steps
4. **Verbose mode:** `--verbose` for more output
5. **Dry run:** `--dry-run` to show what would be executed

## Migration Path

1. Create new unified `run_analysis.sh` with flag support
2. Keep `run_analysis_auto.sh` as a symlink or wrapper:
   ```bash
   #!/bin/bash
   exec "$(dirname "$0")/run_analysis.sh" --auto "$@"
   ```
3. Update README.md with new usage
4. Deprecate old script after transition period

## Summary

**Recommended:** Option 1 (Command-line flags)
- Single script to maintain
- Backward compatible
- Clear and discoverable interface
- Easy to extend with additional features

**Key Changes:**
- Add `--auto` flag for auto mode
- Add `--pause-time` flag for custom pause duration
- Add `--no-complete` flag to skip complete analysis prompt
- Add `--help` flag for usage information
- Keep interactive mode as default
