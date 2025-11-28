#!/usr/bin/env python3
"""
Step 1: Analyze the raw binary data structure
Determine grid dimensions from the data itself, not assumptions.
"""

data = open('arecibo-message.txt').read().strip()

print("=" * 70)
print("STEP 1: RAW DATA STRUCTURE ANALYSIS")
print("=" * 70)
print(f"\nTotal characters: {len(data)}")
print(f"All binary (0s and 1s): {all(c in '01' for c in data)}")
print(f"Zeros: {data.count('0')}, Ones: {data.count('1')}")
print(f"Ratio: {data.count('1')/len(data):.2%} ones, {data.count('0')/len(data):.2%} zeros")

# Factor analysis to find possible grid dimensions
n = len(data)
print(f"\nFactoring {n} to find possible grid dimensions:")
print("-" * 70)

factors = []
for i in range(1, int(n**0.5) + 1):
    if n % i == 0:
        factors.append((i, n // i))
        if i != n // i:
            factors.append((n // i, i))

factors.sort()

print("\nPossible rectangular grid dimensions (rows × cols):")
for r, c in factors:
    print(f"  {r:4d} × {c:4d} = {r*c}")

# Look for reasonable aspect ratios (not too wide or tall)
print("\nReasonable aspect ratios (between 1:4 and 4:1):")
reasonable = []
for r, c in factors:
    if r == 1 or c == 1:  # Skip 1×N and N×1
        continue
    ratio = r/c if r <= c else c/r
    if 1/4 <= ratio <= 4:  # More inclusive to catch 23×73 (ratio ~0.315)
        reasonable.append((r, c))
        print(f"  {r:4d} × {c:4d} (ratio: {ratio:.2f})")

# The most likely candidates are those with reasonable aspect ratios
# For 1679, we have 23×73 and 73×23 - both are reasonable
# We'll prefer taller format (more rows) for bitmap images
if reasonable:
    print(f"\nMost likely dimensions: {reasonable}")
    # Use the one with more rows (taller format) for better visualization
    rows, cols = max(reasonable, key=lambda x: x[0])
    print(f"Using taller format: {rows} rows × {cols} columns")
else:
    # Fallback: use the pair closest to square, excluding 1×N
    non_trivial = [(r, c) for r, c in factors if r > 1 and c > 1]
    if non_trivial:
        rows, cols = min(non_trivial, key=lambda x: abs(x[0]/x[1] - 1))
        print(f"\nUsing closest to square: {rows} rows × {cols} columns")
    else:
        rows, cols = factors[1]  # Skip 1×N, use second
        print(f"\nUsing: {rows} rows × {cols} columns")

print("\n" + "=" * 70)
print("CONCLUSION: Grid dimensions determined from data factorization")
print(f"  Rows: {rows}, Columns: {cols}")
print("=" * 70)
