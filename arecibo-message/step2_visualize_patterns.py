#!/usr/bin/env python3
"""
Step 2: Visualize the binary data as a bitmap
Try different orientations to see which makes visual sense.
Supports optional color output using ANSI color codes for terminal.
"""

import sys
from get_dimensions import get_dimensions

# ANSI color codes
RESET = '\033[0m'
CYAN = '\033[96m'      # Numbers (rows 0-9)
GREEN = '\033[92m'     # Atomic numbers (rows 10-12, 15-22)
YELLOW = '\033[93m'    # DNA structure (rows 13-14, 23-24)
RED = '\033[91m'       # Human figure (rows 40-54)
BLUE = '\033[94m'      # Bottom section (rows 55-72)
WHITE = '\033[97m'     # Other data

# Get dimensions using helper function
data = open('arecibo-message.txt').read().strip()
rows, cols = get_dimensions(len(data))

# Check for color output flag
color_output = '--color' in sys.argv or '-c' in sys.argv

print("=" * 70)
print("STEP 2: VISUALIZATION - Testing Different Orientations")
print("=" * 70)
print(f"\nUsing dimensions: {rows} rows × {cols} columns")

if color_output:
    print("Color mode: Enabled (using ANSI terminal colors)")
else:
    print("Color mode: Disabled (use --color or -c to enable)")

print(f"\nVisualizing as {rows}×{cols} bitmap (1=█, 0=space):")
print("-" * 70)

def get_color_code(row_idx):
    """Return ANSI color code based on which section the row belongs to."""
    if not color_output:
        return ''
    if 0 <= row_idx <= 9:
        return CYAN
    elif 10 <= row_idx <= 12 or 15 <= row_idx <= 22:
        return GREEN
    elif row_idx in [13, 14, 23, 24]:
        return YELLOW
    elif 40 <= row_idx <= 54:
        return RED
    elif 55 <= row_idx <= 72:
        return BLUE
    else:
        return WHITE

for i in range(rows):
    row = data[i*cols:(i+1)*cols]
    color_code = get_color_code(i)
    reset_code = RESET if color_output else ''
    
    visual = ''.join('█' if bit == '1' else ' ' for bit in row)
    print(f"{i:2d}: {color_code}{visual}{reset_code}")

print("\n" + "-" * 70)
print(f"\nNow trying {cols}×{rows} orientation:")
print("-" * 70)

# Try transposed (without color for now, as it's less useful)
for i in range(0, len(data), rows):
    row = data[i:i+rows]
    visual = ''.join('█' if bit == '1' else ' ' for bit in row)
    print(f"{i//rows:2d}: {visual}")

print("\n" + "=" * 70)
print("ANALYSIS: Which orientation shows clearer patterns?")
print("Look for:")
print("  - Distinct sections")
print("  - Recognizable shapes")
print("  - Patterns that make visual sense")
if color_output:
    print("\nColor legend:")
    print(f"  {CYAN}Cyan{RESET}: Numbers (rows 0-9)")
    print(f"  {GREEN}Green{RESET}: Atomic numbers (rows 10-12, 15-22)")
    print(f"  {YELLOW}Yellow{RESET}: DNA structure (rows 13-14, 23-24)")
    print(f"  {RED}Red{RESET}: Human figure (rows 40-54)")
    print(f"  {BLUE}Blue{RESET}: Bottom section (rows 55-72)")
else:
    print("\nUse --color or -c flag to enable colored output")
print("=" * 70)
