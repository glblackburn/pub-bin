#!/usr/bin/env python3
"""
Step 4: Look for recognizable shapes - human figure
Search for anthropomorphic patterns.
Supports optional color output using ANSI color codes for terminal.
"""

import sys
from get_dimensions import get_dimensions

# ANSI color codes
RESET = '\033[0m'
RED = '\033[91m'       # Human figure (rows 40-54)
CYAN = '\033[96m'      # Other sections for contrast

# Get dimensions using helper function
data = open('arecibo-message.txt').read().strip()
rows, cols = get_dimensions(len(data))

# Check for color output flag
color_output = '--color' in sys.argv or '-c' in sys.argv

print("=" * 70)
print("STEP 4: PATTERN RECOGNITION - Looking for Human Figure")
print("=" * 70)
if color_output:
    print("Color mode: Enabled (human figure highlighted in red)")
print(f"\nSearching for anthropomorphic patterns...")
print("Looking for:")
print("  - Vertical symmetry")
print("  - Head-like structure (smaller, centered)")
print("  - Torso (wider)")
print("  - Arms extending horizontally")
print("  - Legs (vertical, possibly split)")

# Visualize all rows to look for patterns
print("\n" + "-" * 70)
print("Full visualization (looking for human-like shape):")
print("-" * 70)

for i in range(rows):
    row = data[i*cols:(i+1)*cols]
    visual = ''.join('█' if bit == '1' else ' ' for bit in row)
    ones_count = row.count('1')
    
    # Look for patterns that might indicate human figure
    # - Symmetry around center
    center = cols // 2
    left_half = row[:center]
    right_half = row[center:]
    symmetry_score = sum(1 for j in range(min(len(left_half), len(right_half))) 
                       if left_half[-(j+1)] == right_half[j])
    
    # Color code: red for human figure section (rows 40-54), normal for others
    if color_output and 40 <= i <= 54:
        color_code = RED
        reset_code = RESET
    else:
        color_code = ''
        reset_code = ''
    
    # Flag interesting rows
    marker = ""
    if ones_count > 5 and symmetry_score > 2:
        marker = " <-- potential human figure part"
    
    print(f"Row {i:2d}: {color_code}{visual}{reset_code} | ones:{ones_count:2d} sym:{symmetry_score}{marker}")

print("\n" + "=" * 70)
print("ANALYSIS: Manually identify rows that form human figure")
print("Look for:")
print("  - Head: small, centered, rows ~40-47")
print("  - Torso: wider, rows ~48-52")
print("  - Arms: horizontal extensions, rows ~40-43")
print("  - Legs: vertical, possibly split, rows ~53-54")
if color_output:
    print(f"\n{RED}Red highlighted section{RESET}: Human figure (rows 40-54)")
    print("Use --color or -c flag to enable colored output")
print("=" * 70)
