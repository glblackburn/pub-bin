#!/bin/bash
#
# Wrapper script to run Arecibo Message analysis steps in order
# Supports both interactive and auto modes via command-line flags
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default settings
AUTO_MODE=false
PAUSE_TIME=3
RUN_COMPLETE=prompt  # prompt, true, false
COLOR_MODE=false
PAGE_MODE=true  # paging enabled by default
DEBUG_MODE=false  # debug output for troubleshooting

# Function to show help
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Run Arecibo Message analysis steps in sequence.

OPTIONS:
    -a, --auto              Auto mode: advance automatically with timed pauses
    -t, --pause-time SEC    Set pause time in seconds for auto mode (default: 3)
    -c, --color             Enable colored terminal output for visualizations
    --no-page               Disable paged output (use original continuous output)
    --debug                  Enable debug output (shows line counting details)
    --complete              Always run complete analysis (skip prompt)
    --no-complete           Skip the prompt and don't run complete analysis
    -h, --help              Show this help message

NOTE: Paged output (pauses at terminal height) is enabled by default for better
screen recording and user experience. Use --no-page to disable.

EXAMPLES:
    # Interactive mode (default - pauses and waits for Enter)
    $0

    # Auto mode with default 3-second pauses
    $0 --auto

    # Auto mode with custom pause time
    $0 --auto --pause-time 5

    # Enable colored output
    $0 --color

    # Auto mode with colored output
    $0 --auto --color

    # Disable paging (use original continuous output)
    $0 --no-page

    # Short form
    $0 -a -t 5 -c

    # Always run complete analysis (skip prompt)
    $0 --complete

    # Skip complete analysis prompt and don't run it
    $0 --auto --no-complete

    # Auto mode with complete analysis
    $0 --auto --complete

ENVIRONMENT VARIABLES:
    AUTO_MODE               If set to "1" or "true", enables auto mode
    PAUSE_TIME              Pause time in seconds for auto mode (default: 3)
    COLOR_MODE              If set to "1" or "true", enables colored output
    PAGE_MODE               If set to "0" or "false", disables paged output (default: true)
    RUN_COMPLETE            If set to "1" or "true", always run complete analysis
                            If set to "0" or "false", skip complete analysis

EOF
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--auto)
            AUTO_MODE=true
            shift
            ;;
        -t|--pause-time)
            PAUSE_TIME="$2"
            if ! [[ "$PAUSE_TIME" =~ ^[0-9]+$ ]]; then
                echo -e "${YELLOW}Error: Pause time must be a positive integer${NC}"
                exit 1
            fi
            shift 2
            ;;
        -c|--color)
            COLOR_MODE=true
            shift
            ;;
        --complete)
            RUN_COMPLETE=true
            shift
            ;;
        --no-complete)
            RUN_COMPLETE=false
            shift
            ;;
        --no-page)
            PAGE_MODE=false
            shift
            ;;
        --debug)
            DEBUG_MODE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${YELLOW}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check environment variables (command-line flags take precedence)
if [ -z "$AUTO_MODE" ] || [ "$AUTO_MODE" != "true" ]; then
    if [ "${AUTO_MODE:-}" = "1" ] || [ "${AUTO_MODE:-}" = "true" ]; then
        AUTO_MODE=true
    fi
fi

if [ -n "${PAUSE_TIME:-}" ] && [[ "$PAUSE_TIME" =~ ^[0-9]+$ ]]; then
    PAUSE_TIME="${PAUSE_TIME}"
fi

if [ "$COLOR_MODE" != "true" ]; then
    if [ "${COLOR_MODE:-}" = "1" ] || [ "${COLOR_MODE:-}" = "true" ]; then
        COLOR_MODE=true
    fi
fi

# Check environment variable for PAGE_MODE if not set by flags
if [ "$PAGE_MODE" != false ]; then
    if [ "${PAGE_MODE:-}" = "0" ] || [ "${PAGE_MODE:-}" = "false" ]; then
        PAGE_MODE=false
    fi
fi

# Check environment variable for RUN_COMPLETE if not set by flags
if [ "$RUN_COMPLETE" = "prompt" ]; then
    if [ "${RUN_COMPLETE:-}" = "1" ] || [ "${RUN_COMPLETE:-}" = "true" ]; then
        RUN_COMPLETE=true
    elif [ "${RUN_COMPLETE:-}" = "0" ] || [ "${RUN_COMPLETE:-}" = "false" ]; then
        RUN_COMPLETE=false
    fi
fi

# Build color flag for Python scripts
COLOR_FLAG=""
if [ "$COLOR_MODE" = true ]; then
    COLOR_FLAG="--color"
fi

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Function to get terminal height with fallback
get_terminal_height() {
    local height=24  # default fallback
    local method=""
    
    # Method 1: Try environment variable first (most reliable, set by terminal)
    if [ -n "${LINES:-}" ] && [[ "${LINES}" =~ ^[0-9]+$ ]] && [ "${LINES}" -gt 0 ]; then
        height="${LINES}"
        method="LINES env var"
    # Method 2: Try stty size (most reliable when stdin may be redirected)
    elif [ -c /dev/tty ]; then
        local stty_size=$(stty size < /dev/tty 2>/dev/null | awk '{print $1}')
        if [ -n "$stty_size" ] && [[ "$stty_size" =~ ^[0-9]+$ ]] && [ "$stty_size" -gt 0 ]; then
            height="$stty_size"
            method="stty size < /dev/tty"
        else
            # Fallback: try tput with /dev/tty
            height=$(tput lines < /dev/tty 2>/dev/null || echo 24)
            method="tput lines < /dev/tty (fallback)"
        fi
    # Method 3: Try regular tput (works when stdin is terminal)
    elif [ -t 0 ]; then
        height=$(tput lines 2>/dev/null || echo 24)
        method="tput lines (stdin is terminal)"
    # Method 4: Last resort - try tput anyway
    else
        height=$(tput lines 2>/dev/null || echo 24)
        method="tput lines (last resort)"
    fi
    
    # Debug output (only show if called from run_step, not from initial check)
    if [ "$DEBUG_MODE" = true ] && [ "${CALLED_FROM_RUN_STEP:-false}" = "true" ]; then
        echo "[DEBUG] Terminal height detection:" >&2
        echo "[DEBUG]   Method used: $method" >&2
        echo "[DEBUG]   Raw terminal height: $height" >&2
    fi
    
    # Calculate available lines for Python output:
    # Terminal height - header lines (~9 lines: main header + STEP header) - prompt (~1 line)
    # For larger terminals, use proportionally less overhead to maximize screen usage
    local page_size
    if [ $height -gt 50 ]; then
        # Very large terminal (60+): minimal overhead, maximize content
        # Subtract only header (~9) + prompt (~1) = 10 lines overhead
        page_size=$((height - 10))
    elif [ $height -gt 30 ]; then
        # Medium terminal: moderate overhead
        page_size=$((height - 9))
    else
        # Small terminal: more conservative to avoid overflow
        page_size=$((height - 8))
    fi
    
    # Debug output (only show if called from run_step)
    if [ "$DEBUG_MODE" = true ] && [ "${CALLED_FROM_RUN_STEP:-false}" = "true" ]; then
        echo "[DEBUG]   Calculated page size: $page_size lines" >&2
    fi
    
    echo $page_size
}

# Function to page output by counting lines and pausing at terminal height
page_output() {
    local max_lines=$1
    local line_count=0
    local IFS=''
    
    # Debug output (minimal - only show pause events)
    # Removed initial call message to reduce verbosity
    
    # Open terminal for reading (file descriptor 3)
    exec 3< /dev/tty
    
    while IFS= read -r line; do
        echo "$line"
        ((line_count++))
        
        # Debug output every 20 lines (reduced verbosity for cleaner output)
        if [ "$DEBUG_MODE" = true ] && [ $((line_count % 20)) -eq 0 ] && [ $line_count -gt 0 ]; then
            echo "[DEBUG] Line count: $line_count / $max_lines" >&2
        fi
        
        if [ $line_count -ge $max_lines ]; then
            if [ "$DEBUG_MODE" = true ]; then
                echo "[DEBUG] PAUSING at line $line_count (max_lines=$max_lines)" >&2
            fi
            
            if [ "$AUTO_MODE" = true ]; then
                sleep "$PAUSE_TIME"
            else
                echo ""
                echo -e "${YELLOW}Press Enter to continue...${NC}"
                # Read from terminal (fd 3), not from stdin (which is the pipe)
                read -r <&3
            fi
            line_count=0
            
            if [ "$DEBUG_MODE" = true ]; then
                echo "[DEBUG] Resuming, line_count reset to 0" >&2
            fi
        fi
    done
    
    # Close file descriptor
    exec 3<&-
    
    # Removed final debug message to reduce verbosity
}

# Display header
echo -e "${BLUE}========================================${NC}"
if [ "$AUTO_MODE" = true ]; then
    echo -e "${BLUE}Arecibo Message Analysis (Auto Mode)${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${YELLOW}Pause time: ${PAUSE_TIME} seconds${NC}"
else
    echo -e "${BLUE}Arecibo Message Analysis${NC}"
    echo -e "${BLUE}========================================${NC}"
fi
if [ "$COLOR_MODE" = true ]; then
    echo -e "${YELLOW}Color mode: Enabled${NC}"
fi
if [ "$PAGE_MODE" = true ]; then
    echo -e "${YELLOW}Paged output: Enabled (pauses at terminal height)${NC}"
fi
if [ "$DEBUG_MODE" = true ]; then
    echo -e "${YELLOW}Debug mode: Enabled${NC}"
    echo "[DEBUG] Script start - checking terminal detection..." >&2
    test_height=$(get_terminal_height)
    echo "[DEBUG] Initial terminal height check: $test_height lines" >&2
fi
echo ""

# Check if arecibo-message.txt exists
if [ ! -f "arecibo-message.txt" ]; then
    echo -e "${YELLOW}Error: arecibo-message.txt not found!${NC}"
    exit 1
fi

# Function to pause between steps
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

# Function to run a step script
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
        CALLED_FROM_RUN_STEP=true
        local terminal_height=$(get_terminal_height)
        unset CALLED_FROM_RUN_STEP
        
        if [ "$DEBUG_MODE" = true ]; then
            echo "[DEBUG] run_step() - script: $script_name, page size: $terminal_height lines" >&2
        fi
        
        # Use -u flag for unbuffered output to ensure paging works correctly
        if [ "$COLOR_MODE" = true ] && ([[ "$script_name" == *"step2"* ]] || [[ "$script_name" == *"step4"* ]] || [[ "$script_name" == *"decode_analysis"* ]]); then
            python3 -u "$script_name" $COLOR_FLAG 2>&1 | page_output "$terminal_height"
        else
            python3 -u "$script_name" 2>&1 | page_output "$terminal_height"
        fi
    else
        # Original behavior (no paging) - only when --no-page is used
        if [ "$COLOR_MODE" = true ] && ([[ "$script_name" == *"step2"* ]] || [[ "$script_name" == *"step4"* ]] || [[ "$script_name" == *"decode_analysis"* ]]); then
            python3 "$script_name" $COLOR_FLAG
        else
            python3 "$script_name"
        fi
    fi
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ Step $step_num completed successfully${NC}"
    else
        echo ""
        echo -e "${YELLOW}⚠ Step $step_num completed with warnings${NC}"
    fi
}

# Run all steps in order
run_step 1 "step1_analyze_structure.py" "Analyze Structure - Determine Grid Dimensions"
pause

run_step 2 "step2_visualize_patterns.py" "Visualize Patterns - Display Bitmap"
pause

run_step 3 "step3_identify_sections.py" "Identify Sections - Bit Density Analysis"
pause

run_step 4 "step4_find_human_figure.py" "Find Human Figure - Pattern Recognition"
pause

run_step 5 "step5_decode_numbers.py" "Decode Numbers - Attempt Number Decoding"
pause

run_step 6 "step6_decode_atomic_numbers.py" "Decode Atomic Numbers - Attempt Element Decoding"

# Optional: Run complete analysis
if [ "$RUN_COMPLETE" = true ]; then
    # Always run complete analysis
    pause
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Complete Analysis${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    run_step "Complete" "decode_analysis.py" "Complete Analysis - All Steps Combined"
elif [ "$RUN_COMPLETE" = "prompt" ] && [ "$AUTO_MODE" != true ]; then
    # Prompt user in interactive mode
    pause
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Complete Analysis${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Run complete analysis script? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo ""
        run_step "Complete" "decode_analysis.py" "Complete Analysis - All Steps Combined"
    fi
fi
# If RUN_COMPLETE=false, skip complete analysis entirely

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Analysis Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
