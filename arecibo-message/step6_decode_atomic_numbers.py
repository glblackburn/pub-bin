#!/usr/bin/env python3
"""
Step 6: Attempt to decode atomic numbers
Try different reading directions and column selections.
"""

from get_dimensions import get_dimensions

# Get dimensions using helper function
data = open('arecibo-message.txt').read().strip()
rows, cols = get_dimensions(len(data))

print("=" * 70)
print("STEP 6: DECODING ATOMIC NUMBERS")
print("=" * 70)
print("\nLooking for atomic numbers in sections between dense bars...")
print("Common DNA elements: H=1, C=6, N=7, O=8, P=15")

# Identify sections between bars (rows 10-12, 15-22)
print("\n" + "-" * 70)
print("Method 1: Read columns vertically (top to bottom)")
print("-" * 70)
print("Columns 0-4, rows 10-12:")
for col in range(5):
    bits = ''.join(data[row*cols + col] for row in range(10, 13))
    decimal = int(bits, 2) if bits.strip() else 0
    visual = ' '.join(data[row*cols + col] for row in range(10, 13))
    element_match = ""
    if decimal in [1, 6, 7, 8, 15]:
        elements = {1: "H", 6: "C", 7: "N", 8: "O", 15: "P"}
        element_match = f" ✓ {elements[decimal]}"
    print(f"  Col {col}: {visual} = {decimal:2d}{element_match}")

print("\nColumns 0-4, rows 15-22:")
for col in range(5):
    bits = ''.join(data[row*cols + col] for row in range(15, 23))
    decimal = int(bits, 2) if bits.strip() else 0
    visual = ' '.join(data[row*cols + col] for row in range(15, 23))
    element_match = ""
    if decimal in [1, 6, 7, 8, 15]:
        elements = {1: "H", 6: "C", 7: "N", 8: "O", 15: "P"}
        element_match = f" ✓ {elements[decimal]}"
    print(f"  Col {col}: {visual} = {decimal:2d}{element_match}")

print("\n" + "-" * 70)
print("Method 2: Read columns vertically (bottom to top)")
print("-" * 70)
print("Columns 0-4, rows 15-22 (reversed):")
for col in range(5):
    bits = ''.join(data[row*cols + col] for row in range(22, 14, -1))
    decimal = int(bits, 2) if bits.strip() else 0
    element_match = ""
    if decimal in [1, 6, 7, 8, 15]:
        elements = {1: "H", 6: "C", 7: "N", 8: "O", 15: "P"}
        element_match = f" ✓ {elements[decimal]}"
    print(f"  Col {col}: Binary {bits} = {decimal:2d}{element_match}")

print("\n" + "-" * 70)
print("Method 3: Read horizontally in groups")
print("-" * 70)
print("Rows 11-12, trying different bit group sizes:")
for i in [11, 12]:
    row = data[i*cols:(i+1)*cols]
    visual = ''.join('█' if bit == '1' else ' ' for bit in row)
    print(f"\nRow {i}: {visual}")
    for group_size in [4, 5, 6]:
        groups = [row[j:j+group_size] for j in range(0, len(row), group_size)]
        decimals = [int(g, 2) for g in groups if g.strip()]
        matches = [d for d in decimals if d in [1, 6, 7, 8, 15]]
        match_str = f" ✓ Matches: {matches}" if matches else ""
        print(f"  {group_size}-bit groups: {decimals}{match_str}")

print("\n" + "=" * 70)
print("CONCLUSION: Need to determine correct encoding method")
print("Try different columns, reading directions, and bit groupings")
print("=" * 70)
