#!/usr/bin/env python3
"""
Step 5: Attempt to decode numbers
Try different encoding methods to decode the first 10 rows.
"""

from get_dimensions import get_dimensions

# Get dimensions using helper function
data = open('arecibo-message.txt').read().strip()
rows, cols = get_dimensions(len(data))

print("=" * 70)
print("STEP 5: DECODING NUMBERS (Rows 0-9)")
print("=" * 70)
print("\nAttempting different decoding methods...")

print("\n" + "-" * 70)
print("Method 1: Read each row as binary number")
print("-" * 70)
for i in range(10):
    row = data[i*cols:(i+1)*cols]
    decimal = int(row, 2) if row.strip() else 0
    visual = ''.join('█' if bit == '1' else ' ' for bit in row)
    print(f"Row {i:2d}: {visual} | Decimal: {decimal:8d}")

print("\n" + "-" * 70)
print("Method 2: Read rightmost columns as binary")
print("-" * 70)
for i in range(10):
    row = data[i*cols:(i+1)*cols]
    # Try last 5, 6, 7, 8, 9 bits
    for width in [5, 6, 7, 8, 9]:
        if len(row) >= width:
            right_part = row[-width:]
            decimal = int(right_part, 2) if right_part.strip() else 0
            if i == 0:  # Show format on first row
                print(f"  Trying last {width} bits:")
            visual = ''.join('█' if bit == '1' else ' ' for bit in right_part)
            if decimal > 0 and decimal <= 10:
                print(f"Row {i:2d}: {visual} | Decimal: {decimal} ✓")
            elif i < 3:  # Show first few for debugging
                print(f"Row {i:2d}: {visual} | Decimal: {decimal}")

print("\n" + "-" * 70)
print("Method 3: Read leftmost columns as binary")
print("-" * 70)
for i in range(10):
    row = data[i*cols:(i+1)*cols]
    # Try first 5, 6, 7, 8, 9 bits
    for width in [5, 6, 7, 8, 9]:
        if len(row) >= width:
            left_part = row[:width]
            decimal = int(left_part, 2) if left_part.strip() else 0
            if i == 0:
                print(f"  Trying first {width} bits:")
            visual = ''.join('█' if bit == '1' else ' ' for bit in left_part)
            if decimal > 0 and decimal <= 10:
                print(f"Row {i:2d}: {visual} | Decimal: {decimal} ✓")
            elif i < 3:
                print(f"Row {i:2d}: {visual} | Decimal: {decimal}")

print("\n" + "-" * 70)
print("Method 4: Pattern recognition (visual digit encoding)")
print("-" * 70)
print("These appear to be visual representations, not binary numbers.")
print("Each row likely represents a digit 1-10 as a pattern:")
for i in range(10):
    row = data[i*cols:(i+1)*cols]
    visual = ''.join('█' if bit == '1' else ' ' for bit in row)
    print(f"Row {i:2d}: {visual}")

print("\n" + "=" * 70)
print("CONCLUSION: Numbers appear to be pattern-encoded, not binary")
print("Requires visual pattern matching to decode")
print("=" * 70)
