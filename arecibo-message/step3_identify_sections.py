#!/usr/bin/env python3
"""
Step 3: Identify distinct sections by analyzing bit density
Look for natural breaks and patterns.
"""

from get_dimensions import get_dimensions

# Get dimensions using helper function
data = open('arecibo-message.txt').read().strip()
rows, cols = get_dimensions(len(data))

print("=" * 70)
print("STEP 3: SECTION IDENTIFICATION")
print("=" * 70)
print(f"\nAnalyzing bit density per row to find sections...")

# Count ones per row
ones_per_row = []
for i in range(rows):
    row = data[i*cols:(i+1)*cols]
    ones_per_row.append(row.count('1'))

# Find rows with significant content
print("\nRows with most '1' bits (likely content rows):")
top_rows = sorted(enumerate(ones_per_row), key=lambda x: x[1], reverse=True)[:20]
for i, count in top_rows:
    print(f"  Row {i:2d}: {count:2d} ones")

# Find rows with few or no ones (likely separators)
print("\nRows with fewest '1' bits (likely separators/empty):")
empty_rows = sorted(enumerate(ones_per_row), key=lambda x: x[1])[:20]
for i, count in empty_rows:
    print(f"  Row {i:2d}: {count:2d} ones")

# Look for patterns in density changes
print("\n" + "-" * 70)
print("Bit density analysis (looking for natural breaks):")
print("-" * 70)

# Group rows by density
dense_threshold = max(ones_per_row) * 0.7
sparse_threshold = max(ones_per_row) * 0.1

dense_sections = []
sparse_sections = []
current_section_start = 0
current_type = None

for i, count in enumerate(ones_per_row):
    if count >= dense_threshold:
        section_type = 'dense'
    elif count <= sparse_threshold:
        section_type = 'sparse'
    else:
        section_type = 'medium'
    
    if current_type != section_type:
        if current_type:
            if current_type == 'dense':
                dense_sections.append((current_section_start, i-1))
            elif current_type == 'sparse':
                sparse_sections.append((current_section_start, i-1))
        current_section_start = i
        current_type = section_type

# Add final section
if current_type == 'dense':
    dense_sections.append((current_section_start, rows-1))
elif current_type == 'sparse':
    sparse_sections.append((current_section_start, rows-1))

print("\nDense content sections (rows with many ones):")
for start, end in dense_sections:
    print(f"  Rows {start:2d}-{end:2d}")

print("\nSparse/separator sections (rows with few ones):")
for start, end in sparse_sections:
    print(f"  Rows {start:2d}-{end:2d}")

print("\n" + "=" * 70)
print("HYPOTHESIS: Sections identified based on bit density")
print("=" * 70)
