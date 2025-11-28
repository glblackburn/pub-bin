#!/usr/bin/env python3
"""
Step 2: Visualize the binary data as a bitmap
Try different orientations to see which makes visual sense.
"""

from get_dimensions import get_dimensions

# Get dimensions using helper function
data = open('arecibo-message.txt').read().strip()
rows, cols = get_dimensions(len(data))

print("=" * 70)
print("STEP 2: VISUALIZATION - Testing Different Orientations")
print("=" * 70)
print(f"\nUsing dimensions: {rows} rows × {cols} columns")
print(f"\nVisualizing as {rows}×{cols} bitmap (1=█, 0=space):")
print("-" * 70)

for i in range(0, len(data), cols):
    row = data[i:i+cols]
    visual = ''.join('█' if bit == '1' else ' ' for bit in row)
    print(f"{i//cols:2d}: {visual}")

print("\n" + "-" * 70)
print(f"\nNow trying {cols}×{rows} orientation:")
print("-" * 70)

# Try transposed
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
print("=" * 70)
