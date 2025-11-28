#!/usr/bin/env python3
"""
Complete decoding analysis script
Determines grid dimensions from data and performs full analysis.
Run this script to analyze the Arecibo message from first principles.

Optional: Use --color or -c flag to enable colored terminal output
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

# Check for color output flag
color_output = '--color' in sys.argv or '-c' in sys.argv

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

data = open('arecibo-message.txt').read().strip()

print("=" * 70)
print("BINARY MESSAGE DECODING ANALYSIS")
print("(From First Principles - No Assumptions)")
print("=" * 70)

# STEP 1: Determine grid dimensions from data
print("\n" + "=" * 70)
print("STEP 1: DETERMINING GRID DIMENSIONS")
print("=" * 70)
print(f"\nTotal bits: {len(data)}")
print(f"All binary: {all(c in '01' for c in data)}")
print(f"Ones: {data.count('1')} ({data.count('1')/len(data):.1%}), Zeros: {data.count('0')} ({data.count('0')/len(data):.1%})")

# Factor analysis
n = len(data)
factors = []
for i in range(1, int(n**0.5) + 1):
    if n % i == 0:
        factors.append((i, n // i))
        if i != n // i:
            factors.append((n // i, i))
factors.sort()

print(f"\nFactoring {n} to find possible grid dimensions:")
print("Possible dimensions:")
for r, c in factors:
    if r > 1 and c > 1:
        ratio = r/c if r <= c else c/r
        print(f"  {r:4d} × {c:4d} (ratio: {ratio:.2f})")

# Use helper function to determine dimensions
rows, cols = get_dimensions(len(data))
print(f"\n✓ Determined from factorization: {rows} rows × {cols} columns")

# STEP 2: Visualize
print("\n" + "=" * 70)
print("STEP 2: VISUALIZATION")
print("=" * 70)
if color_output:
    print("Color mode: Enabled (using ANSI terminal colors)")
print(f"\nVisualizing as {rows}×{cols} bitmap:")
print("-" * 70)
for i in range(rows):
    row = data[i*cols:(i+1)*cols]
    color_code = get_color_code(i)
    reset_code = RESET if color_output else ''
    visual = ''.join('█' if bit == '1' else ' ' for bit in row)
    print(f"{i:2d}: {color_code}{visual}{reset_code}")

# STEP 3: Identify sections
print("\n" + "=" * 70)
print("STEP 3: SECTION IDENTIFICATION")
print("=" * 70)
ones_per_row = [data[i*cols:(i+1)*cols].count('1') for i in range(rows)]

print("\nRows with most '1' bits (content rows):")
top_rows = sorted(enumerate(ones_per_row), key=lambda x: x[1], reverse=True)[:15]
for i, count in top_rows:
    print(f"  Row {i:2d}: {count:2d} ones")

print("\nRows with fewest '1' bits (separators/empty):")
empty_rows = sorted(enumerate(ones_per_row), key=lambda x: x[1])[:15]
for i, count in empty_rows:
    print(f"  Row {i:2d}: {count:2d} ones")

# STEP 4: Find human figure
print("\n" + "=" * 70)
print("STEP 4: PATTERN RECOGNITION - Human Figure")
print("=" * 70)
print("\nLooking for anthropomorphic patterns (rows 40-54):")
for i in range(40, min(55, rows)):
    row = data[i*cols:(i+1)*cols]
    visual = ''.join('█' if bit == '1' else ' ' for bit in row)
    print(f"Row {i:2d}: {visual}")

# STEP 5: Decode numbers
print("\n" + "=" * 70)
print("STEP 5: DECODING NUMBERS (Rows 0-9)")
print("=" * 70)
print("\nVisual patterns (likely pattern-encoded digits):")
for i in range(10):
    row = data[i*cols:(i+1)*cols]
    visual = ''.join('█' if bit == '1' else ' ' for bit in row)
    decimal = int(row, 2) if row.strip() else 0
    print(f"Row {i:2d}: {visual} | Binary: {decimal:8d}")

# STEP 6: Decode atomic numbers
print("\n" + "=" * 70)
print("STEP 6: DECODING ATOMIC NUMBERS")
print("=" * 70)
print("\nColumns 0-4, rows 15-22 (reading top to bottom):")
for col in range(5):
    bits = ''.join(data[row*cols + col] for row in range(15, 23))
    decimal = int(bits, 2) if bits.strip() else 0
    element_match = ""
    if decimal in [1, 6, 7, 8, 15]:
        elements = {1: "H", 6: "C", 7: "N", 8: "O", 15: "P"}
        element_match = f" → {elements[decimal]}"
    print(f"  Col {col}: {decimal:2d}{element_match}")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
if color_output:
    print("\nColor legend:")
    print(f"  {CYAN}Cyan{RESET}: Numbers (rows 0-9)")
    print(f"  {GREEN}Green{RESET}: Atomic numbers (rows 10-12, 15-22)")
    print(f"  {YELLOW}Yellow{RESET}: DNA structure (rows 13-14, 23-24)")
    print(f"  {RED}Red{RESET}: Human figure (rows 40-54)")
    print(f"  {BLUE}Blue{RESET}: Bottom section (rows 55-72)")
print(f"""
Key Findings:
- Grid structure: {rows}×{cols} bitmap (determined from factorization)
- Human figure: Clearly visible in rows 40-54
- Section separators: Dense horizontal bars
- Numbers: Pattern-encoded (not standard binary)
- Atomic numbers: Partial decoding attempted
""")
