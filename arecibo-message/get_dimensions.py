#!/usr/bin/env python3
"""
Helper function to determine grid dimensions from binary data length.
Returns (rows, cols) tuple.
"""

def get_dimensions(data_length):
    """Determine grid dimensions from data length by factorization."""
    n = data_length
    
    # Factor analysis
    factors = []
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            factors.append((i, n // i))
            if i != n // i:
                factors.append((n // i, i))
    factors.sort()
    
    # Find reasonable aspect ratios (excluding 1×N and N×1)
    reasonable = []
    for r, c in factors:
        if r == 1 or c == 1:
            continue
        ratio = r/c if r <= c else c/r
        if 1/4 <= ratio <= 4:  # Inclusive range
            reasonable.append((r, c))
    
    if reasonable:
        # Prefer taller format (more rows) for bitmap images
        return max(reasonable, key=lambda x: x[0])
    else:
        # Fallback: closest to square, excluding 1×N
        non_trivial = [(r, c) for r, c in factors if r > 1 and c > 1]
        if non_trivial:
            return min(non_trivial, key=lambda x: abs(x[0]/x[1] - 1))
        else:
            return factors[1] if len(factors) > 1 else factors[0]

if __name__ == "__main__":
    # Test with arecibo message
    data = open('arecibo-message.txt').read().strip()
    rows, cols = get_dimensions(len(data))
    print(f"Determined dimensions: {rows} rows × {cols} columns")
