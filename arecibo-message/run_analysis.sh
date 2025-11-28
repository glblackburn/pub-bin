#!/bin/bash
#
# Wrapper script to run Arecibo Message analysis steps in order
# Pauses between each step for review
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Arecibo Message Analysis${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if arecibo-message.txt exists
if [ ! -f "arecibo-message.txt" ]; then
    echo -e "${YELLOW}Error: arecibo-message.txt not found!${NC}"
    exit 1
fi

# Function to pause between steps
pause() {
    echo ""
    echo -e "${YELLOW}Press Enter to continue to next step...${NC}"
    read -r
    echo ""
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
    
    python3 "$script_name"
    
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
pause

# Optional: Run complete analysis
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

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Analysis Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
