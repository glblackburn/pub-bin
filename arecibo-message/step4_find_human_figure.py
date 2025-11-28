#!/usr/bin/env python3
"""
Step 4: Look for recognizable shapes - human figure
Search for anthropomorphic patterns.
"""

from get_dimensions import get_dimensions

# Get dimensions using helper function
data = open('arecibo-message.txt').read().strip()
rows, cols = get_dimensions(len(data))

print("=" * 70)
print("STEP 4: PATTERN RECOGNITION - Looking for Human Figure")
print("=" * 70)
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
    
    # Flag interesting rows
    marker = ""
    if ones_count > 5 and symmetry_score > 2:
        marker = " <-- potential human figure part"
    
    print(f"Row {i:2d}: {visual} | ones:{ones_count:2d} sym:{symmetry_score}{marker}")

print("\n" + "=" * 70)
print("ANALYSIS: Manually identify rows that form human figure")
print("Look for:")
print("  - Head: small, centered, rows ~40-47")
print("  - Torso: wider, rows ~48-52")
print("  - Arms: horizontal extensions, rows ~40-43")
print("  - Legs: vertical, possibly split, rows ~53-54")
print("=" * 70)
