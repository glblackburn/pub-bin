# Arecibo Message

## Overview

This directory contains the binary representation of the **Arecibo Message**, a famous interstellar radio message that was broadcast into space on November 16, 1974, from the Arecibo radio telescope in Puerto Rico.

## Files

- `arecibo-message.txt` - Single-line binary string containing 1,679 binary digits (0s and 1s)

## Content Analysis

The binary string contains 1,679 characters, which represents the Arecibo Message encoded as a bitmap image. When properly decoded and arranged in a grid (typically 73 rows × 23 columns), the message encodes:

- **Numbers 1-10** (decimal representation)
- **Atomic numbers** of the elements hydrogen, carbon, nitrogen, oxygen, and phosphorus (the building blocks of DNA)
- **DNA structure** (double helix)
- **Human figure** (representing humanity)
- **Solar system** (showing Earth's position)
- **Arecibo telescope** (the instrument that sent the message)

## Structure

- `arecibo-message.txt`: Single continuous line containing 1,679 binary digits
- The message is designed to be arranged in a grid of 73 rows × 23 columns (1,679 = 73 × 23)

## Historical Context

The Arecibo Message was created by Frank Drake and Carl Sagan, along with other scientists, to demonstrate the capabilities of the Arecibo radio telescope. It was transmitted toward the globular star cluster M13, approximately 25,000 light-years away.

The message serves as:
- A demonstration of human technological achievement
- A symbolic attempt at interstellar communication
- A time capsule representing humanity and our understanding of science

## Git Status

This directory is part of the `pub-bin` repository. The files are currently untracked and have not been committed to version control.

## Usage

The binary data in `arecibo-message.txt` can be:
- Decoded and visualized as a bitmap image
- Processed by scripts to extract the encoded information
- Used for educational purposes to understand binary encoding and interstellar communication

## Decoding Analysis

### Analysis Scripts

This directory contains Python scripts that decode the message from **first principles** - without using any historical knowledge:

- **`decode_analysis.py`** - Complete analysis script (run this for full analysis)
- **`step1_analyze_structure.py`** - Determines grid dimensions from data factorization
- **`step2_visualize_patterns.py`** - Visualizes binary data as bitmap
- **`step3_identify_sections.py`** - Identifies distinct sections by bit density
- **`step4_find_human_figure.py`** - Recognizes anthropomorphic patterns
- **`step5_decode_numbers.py`** - Attempts to decode numbers 1-10
- **`step6_decode_atomic_numbers.py`** - Attempts to decode atomic elements
- **`get_dimensions.py`** - Helper function to determine grid dimensions

### Documentation

- **[DECODING_ANALYSIS.md](DECODING_ANALYSIS.md)** - Detailed findings from raw binary analysis
- **[ANALYSIS_PROCESS.md](ANALYSIS_PROCESS.md)** - Step-by-step explanation of the analysis methodology
- **[COMBINE_ANALYSIS.md](COMBINE_ANALYSIS.md)** - Analysis of combining wrapper scripts into a unified design

### Running the Analysis

**Easy way - Use the wrapper script:**

```bash
# Interactive mode (default - pauses and waits for Enter between steps)
./run_analysis.sh

# Auto mode (auto-advances with timed pauses)
./run_analysis.sh --auto

# Auto mode with custom pause time (e.g., 5 seconds)
./run_analysis.sh --auto --pause-time 5

# Enable colored terminal output
./run_analysis.sh --color

# Auto mode with colored output
./run_analysis.sh --auto --color

# Short form
./run_analysis.sh -a -t 5 -c

# Always run complete analysis (skip prompt)
./run_analysis.sh --complete

# Skip complete analysis prompt and don't run it
./run_analysis.sh --auto --no-complete

# Auto mode with complete analysis
./run_analysis.sh --auto --complete

# Show help
./run_analysis.sh --help
```

**Backward Compatibility:** The `run_analysis_auto.sh` script is still available for backward compatibility but now simply calls `run_analysis.sh --auto`. For new usage, prefer the unified `run_analysis.sh` script with flags.

**Historical Note:** Previously, there were two separate wrapper scripts (`run_analysis.sh` and `run_analysis_auto.sh`) with ~95% code duplication. These have been unified into a single script with command-line flag support. See [COMBINE_ANALYSIS.md](COMBINE_ANALYSIS.md) for the detailed design analysis that led to this change.

**Manual way - Run scripts directly:**

```bash
# Run complete analysis
python3 decode_analysis.py

# Generate color PNG visualization (requires Pillow)
python3 decode_analysis.py --color
python3 decode_analysis.py --color --output my-image.png

# Or run individual steps
python3 step1_analyze_structure.py
python3 step2_visualize_patterns.py --color  # Generate color visualization
python3 step3_identify_sections.py
python3 step4_find_human_figure.py
python3 step5_decode_numbers.py
python3 step6_decode_atomic_numbers.py
```

**Color Visualization:**
The visualization scripts (`step2_visualize_patterns.py` and `decode_analysis.py`) support colored terminal output using ANSI color codes, similar to the [Wikipedia visualization](https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Arecibo_message.svg/250px-Arecibo_message.svg.png). Use the `--color` or `-c` flag to enable colored output. Different sections are color-coded:
- Cyan: Numbers (rows 0-9)
- Green: Atomic numbers (rows 10-12, 15-22)
- Yellow: DNA structure (rows 13-14, 23-24)
- Red: Human figure (rows 40-54)
- Blue: Bottom section (rows 55-72)

**Note:** Color output uses ANSI terminal codes and works in most modern terminals. No additional libraries required.

**Key Point**: All scripts determine the 73×23 grid dimensions from data factorization (1,679 = 73 × 23), not from assumptions. The analysis is performed purely from the binary data itself.

## References

- [Arecibo Message on Wikipedia](https://en.wikipedia.org/wiki/Arecibo_message)
- [YouTube Video](https://www.youtube.com/watch?v=CrUyjYZsIvY)

**Note:** The Arecibo Observatory website (naic.edu) is no longer actively maintained following the telescope's collapse in 2020, and its SSL certificate has expired. The Wikipedia article provides comprehensive information about the observatory and its history.
