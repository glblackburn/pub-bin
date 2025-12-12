# Analyze TCPDump Tool - Planning Document

**Related Documents:**
- **[Data Analysis](analyze-tcpdump-data-analysis.md)** - Real tcpdump file examination and parsing requirements
- This document provides the complete planning and implementation guide for `analyze-tcpdump.py`

## Tool Overview

**Tool Name:** `analyze-tcpdump.py`  
**Location:** `network-tools/capture/analyze-tcpdump.py`  
**Category:** `network-tools/capture/` (analysis tool for capture data)  
**Purpose:** Analyze tcpdump output files to extract IP addresses, monitor network connections, and generate connection statistics.  
**Language:** Python 3

### File Location Details

The tool will be located in the same directory as `record-tcpdump.sh`, which generates the tcpdump output files that this tool analyzes:

```
network-tools/
├── capture/
│   ├── .gitignore
│   ├── record-tcpdump.sh          # Creates tcpdump output
│   └── analyze-tcpdump.py         # Analyzes tcpdump output (NEW)
├── diagnostics/
│   ├── record-netstat.sh
│   └── sort-netstat-tcp.sh        # Analysis tool co-located (similar pattern)
├── intelligence/
├── scanning/
└── README.md
```

**Rationale:**
- **Co-location with related tool:** `record-tcpdump.sh` creates the data, `analyze-tcpdump.py` analyzes it
- **Follows existing pattern:** Similar to `sort-netstat-tcp.sh` being in `diagnostics/` with `record-netstat.sh`
- **Category alignment:** The `capture/` category is for "Deep packet inspection and traffic capture" - analysis fits here
- **Logical grouping:** Keeps all capture-related tools together

### Usage Path

Users can run the tool from the repository root:
```bash
./network-tools/capture/analyze-tcpdump.py [options] [tcpdump_file...]
# or
python3 network-tools/capture/analyze-tcpdump.py [options] [tcpdump_file...]
```

Or from within the capture directory:
```bash
cd network-tools/capture/
./analyze-tcpdump.py [options] [tcpdump_file...]
```

## Requirements

### Functional Requirements
- [x] Parse tcpdump output files from `record-tcpdump.sh`
- [x] Extract source and destination IP addresses
- [x] Extract port numbers (source and destination)
- [x] Identify protocols (TCP, UDP, ICMP, etc.)
- [x] Count connections per IP address
- [x] Generate statistics (top IPs, connection counts, port usage)
- [x] Filter by protocol, IP address, or port
- [x] Support multiple input files
- [x] Generate summary reports

### Non-Functional Requirements
- [x] Performance: Handle large tcpdump files efficiently
- [x] Compatibility: Works on macOS and Linux (tcpdump output format)
- [x] Security: No special privileges required (reads files only)

## Features

### Core Features
1. **IP Address Extraction:** Extract all unique source and destination IP addresses
2. **Connection Analysis:** Count connections per IP pair
3. **Protocol Detection:** Identify and filter by protocol (TCP, UDP, ICMP, etc.)
4. **Port Analysis:** Extract and analyze port usage
5. **Statistics Generation:** Generate summary statistics
6. **Top IPs Report:** List most frequently accessed IPs
7. **Connection Timeline:** Optional timestamp-based analysis

### Optional Features
- [ ] Filter by local IP addresses (exclude internal network)
- [ ] Group by port ranges (well-known ports, etc.)
- [ ] Export to CSV format
- [ ] Compare multiple tcpdump files
- [ ] Identify new IPs between captures
- [ ] Integration with GreyNoise API for threat intelligence
- [ ] DNS reverse lookup for IPs (optional, requires network)

## CLI Interface

### Command Syntax
```bash
# From repository root
./network-tools/capture/analyze-tcpdump.py [options] [tcpdump_file...]

# Or using python3 directly
python3 network-tools/capture/analyze-tcpdump.py [options] [tcpdump_file...]

# Or from within the capture directory
cd network-tools/capture/
./analyze-tcpdump.py [options] [tcpdump_file...]
```

### Options
- `-h` : Display help message
- `-q` : Quiet mode (output as little as possible)
- `-v` : Verbose output (show detailed processing information)
- `-f <file>` : Input tcpdump file (alternative to positional argument)
- `-o <format>` : Output format: `summary`, `ips`, `connections`, `ports`, `all` (Default: `all`)
- `-p <protocol>` : Filter by protocol: `tcp`, `udp`, `icmp`, `all` (Default: `all`)
- `-i <ip>` : Filter by IP address (show connections involving this IP)
- `-P <port>` : Filter by port number
- `-t <count>` : Show top N IPs/connections (Default: 10)
- `-l` : Exclude local/private IP addresses (10.x, 172.16-31.x, 192.168.x)
- `-c` : Output as CSV format
- `-d <dir>` : Directory containing tcpdump files (auto-finds latest if no file specified)

### Arguments
- `[tcpdump_file...]` : One or more tcpdump output files (optional if `-d` specified)

### Examples
```bash
# Analyze latest tcpdump file in log/ directory (from repo root)
./network-tools/capture/analyze-tcpdump.py

# Analyze specific file (relative to capture directory)
./network-tools/capture/analyze-tcpdump.py log/record-tcpdump_2025-12-07_120000.txt

# Show top 20 IPs only
./network-tools/capture/analyze-tcpdump.py -o ips -t 20

# Filter TCP only, exclude local IPs
./network-tools/capture/analyze-tcpdump.py -p tcp -l

# Filter by specific IP address
./network-tools/capture/analyze-tcpdump.py -i 8.8.8.8

# Output as CSV
./network-tools/capture/analyze-tcpdump.py -c -o connections

# Analyze multiple files
./network-tools/capture/analyze-tcpdump.py log/record-tcpdump_*.txt

# Verbose mode with protocol filter
./network-tools/capture/analyze-tcpdump.py -v -p udp

# From within capture directory
cd network-tools/capture/
./analyze-tcpdump.py log/record-tcpdump_2025-12-07_120000.txt
```

## Output Format

### Standard Output Formats

#### Summary Format (default `-o summary`)
```
TCPDump Analysis Summary
========================
File: log/record-tcpdump_2025-12-07_120000.txt
Total Packets: 1,234
Unique Source IPs: 45
Unique Destination IPs: 78
Protocols: TCP (850), UDP (300), ICMP (84)
Top 10 Source IPs:
  192.168.X.X      450 packets
  10.0.0.5         320 packets
  ...
Top 10 Destination IPs:
  8.8.8.8          200 packets
  1.1.1.1         150 packets
  ...
```

#### IPs Format (`-o ips`)
```
Unique IP Addresses
===================
Source IPs (45):
  192.168.X.X
  10.0.0.5
  ...

Destination IPs (78):
  8.8.8.8
  1.1.1.1
  ...
```

#### Connections Format (`-o connections`)
```
Connection Pairs (Source -> Destination)
=========================================
192.168.X.X:54321 -> 8.8.8.8:53 (UDP) - 200 packets
10.0.0.5:443 -> 1.1.1.1:443 (TCP) - 150 packets
...
```

#### Ports Format (`-o ports`)
```
Port Usage Analysis
==================
Source Ports:
  53 (DNS)      - 450 packets
  443 (HTTPS)   - 320 packets
  ...

Destination Ports:
  443 (HTTPS)   - 850 packets
  53 (DNS)      - 300 packets
  ...
```

#### CSV Format (`-c`)
```csv
type,ip,port,protocol,count
source,192.168.X.X,54321,udp,200
destination,8.8.8.8,53,udp,200
...
```

### Error Output
- File not found errors
- Invalid file format errors
- Parsing errors with line numbers

### File Output (optional)
- **Output file pattern:** `analyze-tcpdump_YYYY-MM-DD_HHMMSS.txt` (if `-o` writes to file)
- **Location:** Current directory or configurable
- **Format:** Same as stdout format

## TCPDump Output Format Understanding

> **See also:** [analyze-tcpdump-data-analysis.md](analyze-tcpdump-data-analysis.md) for detailed analysis of real tcpdump output data, parsing examples, and Python implementation patterns.

### Actual tcpdump Output Format (from real data)

**File analyzed:** `record-tcpdump_2025-12-09_215604.txt` (250,513 lines)

**Line Format:**
```
HH:MM:SS.microseconds IP source_ip.source_port > dest_ip.dest_port: protocol_info
```

### Real Examples from Actual Data

**UDP packets (most common - 159,407 in sample):**
```
21:56:11.886998 IP 203.0.113.10.46102 > 192.168.X.X.59922: UDP, length 28
21:56:11.887164 IP 192.168.X.X.59922 > 203.0.113.10.46102: UDP, length 37
```

**QUIC packets (17,827 in sample):**
```
21:56:16.643287 IP 192.168.X.X.59524 > 203.0.113.11.443: quic, protected
23:06:20.794967 IP 192.168.X.X.54275 > 203.0.113.12.443: quic, initial, dcid <example_id>, token ..., length 1161
```

**ICMP packets (1,985 in sample - NO PORTS):**
```
21:56:12.338504 IP 192.168.X.254 > 192.168.X.X: ICMP time exceeded in-transit, length 40
23:06:21.395971 IP 203.0.113.13 > 192.168.X.X: ICMP host 203.0.113.13 unreachable, length 64
```

**DNS queries (embedded in UDP):**
```
23:06:20.782221 IP 192.168.X.X.12863 > 192.168.X.1.53: 52898+ Type65? example.com. (37)
23:06:20.782360 IP 192.168.X.X.42299 > 192.168.X.1.53: 5267+ A? example.com. (37)
```

**Multicast/Broadcast:**
```
21:56:14.655689 IP 172.X.X.10.57621 > 172.X.255.255.57621: UDP, length 44
21:56:14.718036 IP 172.X.X.10.5353 > 224.0.0.251.5353: 0 PTR (QM)? _example_service._tcp.local. (41)
```

### Parsing Strategy

> **Detailed parsing examples:** See [analyze-tcpdump-data-analysis.md](analyze-tcpdump-data-analysis.md#recommended-parsing-approach-python) for complete Python code examples.

1. **Line Pattern Matching:**
   - **Standard IP packets:** `IP src.ip.src_port > dst.ip.dst_port: protocol, ...`
   - **ICMP packets:** `IP src.ip > dst.ip: ICMP message_type, ...` (NO PORTS)
   - **QUIC packets:** `IP src.ip.src_port > dst.ip.dst_port: quic, [flags], ...`
   - **DNS queries:** Embedded in UDP packets, contains query text

2. **IP Address Extraction:**
   - **Source IP:** Field 3 (format: `ip.port` or just `ip` for ICMP)
   - **Destination IP:** Field 5 (format: `ip.port` or just `ip` for ICMP)
   - **Extract IP:** Remove port portion (everything before last `.` before `:` or `>`)
   - **Handle ICMP:** No port numbers, format is `ip > ip`

3. **Port Extraction:**
   - **Format:** `ip.port` (extract port number after last dot)
   - **ICMP:** No ports (return empty/0)
   - **Multicast/Broadcast:** May have ports (e.g., `224.0.0.251.5353`)

4. **Protocol Detection:**
   - **UDP:** Contains "UDP" (case-sensitive in tcpdump output)
   - **QUIC:** Contains "quic" (lowercase)
   - **ICMP:** Contains "ICMP" (case-sensitive)
   - **TCP:** Contains "Flags" or "tcp" (not present in sample, but should handle)
   - **DNS:** Embedded in UDP, contains query patterns (optional enhancement)

5. **Packet Length:**
   - Available in format: `length X` or `length X, ...`
   - Can extract for statistics

### Key Observations from Real Data

- **File size:** 250,513 lines - requires streaming processing
- **Protocol distribution:** UDP (63.7%), QUIC (7.1%), ICMP (0.8%)
- **Top IPs:** Local IP (192.168.X.X) most common, followed by external IPs
- **Multicast:** mDNS traffic (224.0.0.251) present
- **Broadcast:** Network broadcast addresses (172.X.255.255, etc.)
- **No TCP:** Sample contains no TCP packets (but tool should handle it)

## Configuration

### Config Variables
- None required (reads files only, no API keys needed)

### Interactive Setup
- Not needed (no configuration required)

## Dependencies

### Python Version
- **Python 3.8+** required (for type hints, f-strings, pathlib, etc.)

### Standard Library Modules (No Installation Required)
- `argparse` : CLI argument parsing
- `re` : Regular expressions for parsing tcpdump lines
- `collections` : `defaultdict`, `Counter` for counting
- `ipaddress` : IP address validation and private IP detection
- `pathlib` : File path handling
- `sys` : Exit codes, stderr output
- `csv` : CSV output formatting

### Optional Third-Party Libraries
- `rich` : Enhanced terminal output (tables, colors, progress bars)
  - Install: `pip install rich`
  - Provides: Better formatted output, progress indicators for large files
  - Falls back gracefully if not available

### External Libraries/APIs
- None required for core functionality
- Optional: GreyNoise API integration for threat intelligence (future enhancement)
  - Would use `requests` library if implemented

## Implementation Details

### Script Structure
- Follows Python best practices and patterns from `what-is-left.py`
- Uses `#!/usr/bin/env python3` shebang
- Type hints for function signatures
- Docstrings for all functions and classes
- Main function pattern with `if __name__ == "__main__"`
- Proper exception handling with try/except blocks
- Uses `argparse` for CLI argument parsing

### Code Organization
```python
#!/usr/bin/env python3
"""
analyze-tcpdump.py - Analyze tcpdump output files
"""

# Standard library imports
import argparse
import re
import sys
from collections import defaultdict, Counter
from ipaddress import ip_address, IPv4Address
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

# Optional third-party imports
try:
    from rich.console import Console
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Classes and functions
class TcpdumpParser:
    """Parse tcpdump output lines"""
    ...

class ConnectionAnalyzer:
    """Analyze network connections from parsed data"""
    ...

def main():
    """Main entry point"""
    ...

if __name__ == "__main__":
    main()
```

### Key Classes and Functions

1. **`TcpdumpParser` class**
   - Purpose: Parse tcpdump output lines
   - Methods:
     - `parse_line(line: str) -> Optional[Dict]`: Parse single line
     - Returns: Dictionary with keys: `src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`, `length`
   - Handles: 
     - Standard IP packets with ports: `IP src.ip.src_port > dst.ip.dst_port: ...`
     - ICMP packets without ports: `IP src.ip > dst.ip: ICMP ...`
     - QUIC packets: `IP src.ip.src_port > dst.ip.dst_port: quic, ...`
     - UDP/TCP packets: `IP src.ip.src_port > dst.ip.dst_port: UDP/TCP, ...`

2. **`ConnectionAnalyzer` class**
   - Purpose: Analyze and aggregate connection data
   - Methods:
     - `add_connection(parsed_data: Dict)`: Add connection to analysis
     - `get_top_ips(n: int, direction: str) -> List[Tuple]`: Get top N IPs
     - `get_connection_counts() -> Dict`: Get connection pair counts
     - `get_protocol_counts() -> Counter`: Get protocol distribution
     - `get_port_counts(direction: str) -> Counter`: Get port usage

3. **`is_private_ip(ip: str) -> bool`**
   - Purpose: Check if IP is private/local
   - Uses: `ipaddress` module
   - Handles: 10.x.x.x, 172.16-31.x.x, 192.168.x.x, 127.x.x.x, 169.254.x.x

4. **`find_tcpdump_files(directory: Path) -> List[Path]`**
   - Purpose: Find tcpdump files in directory
   - Returns: List of Path objects, sorted by modification time

5. **`process_file(file_path: Path, analyzer: ConnectionAnalyzer, filters: Dict) -> int`**
   - Purpose: Process single tcpdump file
   - Returns: Number of packets processed
   - Uses: Streaming line-by-line processing

6. **`generate_summary(analyzer: ConnectionAnalyzer, file_info: Dict) -> str`**
   - Purpose: Generate summary statistics report
   - Returns: Formatted string

7. **`generate_top_ips_report(analyzer: ConnectionAnalyzer, n: int, direction: str) -> str`**
   - Purpose: Generate top N IPs report
   - Returns: Formatted string

8. **`generate_connections_report(analyzer: ConnectionAnalyzer, n: int) -> str`**
   - Purpose: Generate connection pairs report
   - Returns: Formatted string

9. **`generate_ports_report(analyzer: ConnectionAnalyzer, n: int, direction: str) -> str`**
   - Purpose: Generate port usage report
   - Returns: Formatted string

10. **`output_csv(analyzer: ConnectionAnalyzer, output_format: str)`**
    - Purpose: Output data in CSV format
    - Uses: `csv` module

### Error Handling
- **File not found:** Raise `FileNotFoundError` with clear message
- **Invalid format:** Log warning, continue processing (collect warnings, report at end)
- **Empty file:** Informative message, return gracefully
- **Parse errors:** Continue processing, collect errors/warnings, report summary at end
- **Exception handling:** Use try/except blocks with specific exception types
- **Exit codes:**
  - 0: Success
  - 1: General error (file not found, invalid arguments)
  - 2: Parse error (invalid file format)
- **Error output:** Use `sys.stderr` for error messages

### Edge Cases (Validated from Real Data)
- **Empty tcpdump files:** Handle gracefully with informative message
- **Malformed tcpdump lines:** Skip with warning, continue processing
- **ICMP packets (no ports):** Format is `ip > ip` not `ip.port > ip.port`
- **QUIC protocol:** Lowercase "quic" keyword, may have additional fields (dcid, scid, token, etc.)
- **Multicast addresses:** 224.0.0.251 (mDNS), 224.0.0.252, etc. - may have ports
- **Broadcast addresses:** 172.X.255.255, 172.X.255.255, etc. - may have ports
- **DNS queries embedded in UDP:** Contains query text, still parseable as UDP
- **Very large files:** 250K+ lines - MUST use streaming (line-by-line), not load all into memory
- **IPv6 addresses:** Not present in sample, but handle gracefully (may skip for v1)
- **TCP packets:** Not present in sample, but should handle "Flags" pattern
- **Fragmented packets:** May appear, handle gracefully
- **Non-IP packets (ARP, etc.):** Skip lines that don't start with "IP"
- **Local IP dominance:** Local IP (192.168.X.X) appears 216K times - filtering option important

## Testing Plan

### Unit Tests (pytest)
- [ ] Test `TcpdumpParser.parse_line()` with various line formats
- [ ] Test IP address extraction (with and without ports)
- [ ] Test protocol detection (TCP, UDP, ICMP, QUIC)
- [ ] Test port extraction (including ICMP no-port case)
- [ ] Test `is_private_ip()` function
- [ ] Test `ConnectionAnalyzer` methods
- [ ] Test connection counting and aggregation
- [ ] Test top N IPs selection
- [ ] Test file finding logic

### Integration Tests
- [ ] Test with real tcpdump output file (sample from actual data)
- [ ] Test with multiple input files
- [ ] Test all output formats (summary, ips, connections, ports, CSV)
- [ ] Test all filter options (protocol, IP, port, local IP exclusion)
- [ ] Test error handling (missing file, invalid format, empty file)
- [ ] Test large file processing (250K+ lines)

### Test File Location
- `tests/scripts/unit/test_analyze_tcpdump.py` (pytest)
- Or: `tests/python/unit/test_analyze_tcpdump.py` (if separate Python test directory)

### Test Data
- Create sample tcpdump output files in `tests/data/tcpdump/`
- Include various protocols, IP formats, edge cases
- Include real sample lines from actual tcpdump file

### Test Framework
- **pytest** for Python testing
- Use `pytest.fixture` for test data setup
- Use `pytest.parametrize` for testing multiple input formats

## Documentation

### README Updates
- [ ] Add tool to `network-tools/README.md` in Capture section:
  ```markdown
  - `capture/analyze-tcpdump.py` - Analyze tcpdump output files
    - Analyzes tcpdump output to extract IP addresses and connection statistics
    - Options: `-h` for help
    - See tool help (`-h`) for full usage and examples
  ```
- [ ] Add detailed description with usage examples
- [ ] Document tcpdump output format requirements
- [ ] Add to main `README.md` scripts section
- [ ] Update location information in documentation

### Code Comments
- [ ] Function headers with descriptions
- [ ] Complex parsing logic explanations
- [ ] Regex pattern explanations
- [ ] Usage examples in comments

## Implementation Checklist

### Phase 1: Core Parsing (Foundation)
- [ ] Create Python script file at `network-tools/capture/analyze-tcpdump.py`
- [ ] Make script executable: `chmod +x network-tools/capture/analyze-tcpdump.py`
- [ ] Add shebang: `#!/usr/bin/env python3`
- [ ] Implement CLI argument parsing with `argparse`
- [ ] Implement `TcpdumpParser` class with `parse_line()` method
- [ ] Test IP and port extraction with unit tests
- [ ] Test protocol detection (UDP, QUIC, ICMP, TCP)
- [ ] Add error handling for malformed lines
- [ ] Add type hints and docstrings

### Phase 2: Data Extraction and Aggregation
- [ ] Implement `ConnectionAnalyzer` class
- [ ] Implement streaming file reading (line-by-line)
- [ ] Implement connection counting and aggregation
- [ ] Test with sample tcpdump file
- [ ] Handle large files efficiently (streaming, no memory loading)
- [ ] Add progress indicator (if `rich` available)

### Phase 3: Filtering
- [ ] Implement `is_private_ip()` function using `ipaddress` module
- [ ] Add filtering logic to `ConnectionAnalyzer`
- [ ] Implement protocol filtering
- [ ] Implement IP address filtering
- [ ] Implement port filtering
- [ ] Implement local IP exclusion
- [ ] Test all filter combinations

### Phase 4: Reporting
- [ ] Implement `generate_summary()` function
- [ ] Implement `generate_top_ips_report()` function
- [ ] Implement `generate_connections_report()` function
- [ ] Implement `generate_ports_report()` function
- [ ] Implement all output formats (summary, ips, connections, ports)
- [ ] Implement CSV output format using `csv` module
- [ ] Add optional `rich` formatting for better output
- [ ] Add fallback plain text formatting

### Phase 5: File Management
- [ ] Implement `find_tcpdump_files()` function using `pathlib`
- [ ] Implement file validation
- [ ] Handle default file finding (latest in `log/` directory relative to script location)
- [ ] Support multiple input files
- [ ] Add file path resolution and validation
- [ ] Handle relative paths correctly (from script location or current working directory)

### Phase 6: Testing
- [ ] Write pytest test suite
- [ ] Create test data files in `tests/data/tcpdump/`
- [ ] Test all error cases
- [ ] Test edge cases (ICMP, malformed lines, empty files)
- [ ] Test with real tcpdump output sample
- [ ] Verify all output formats
- [ ] Test performance with large files

### Phase 7: Documentation
- [ ] Update `network-tools/README.md`
- [ ] Update main `README.md`
- [ ] Add comprehensive docstrings to all functions/classes
- [ ] Add module-level docstring
- [ ] Verify examples work
- [ ] Check README accuracy

### Phase 8: Code Quality
- [ ] Run `clean-emacs-files.sh`
- [ ] Check for trailing whitespace (Python linters)
- [ ] Verify files end with newline
- [ ] Run `pylint` or `flake8` for code quality
- [ ] Run `mypy` for type checking (optional)
- [ ] Review against AI coding standards
- [ ] Test on macOS and Linux if possible

## Future Enhancements

### Phase 2 Features (Post-MVP)
- [ ] DNS reverse lookup integration
- [ ] GreyNoise API integration for threat intelligence
- [ ] JSON output format
- [ ] Comparison between multiple captures
- [ ] Timeline analysis (connections over time)
- [ ] Port range grouping (well-known ports)
- [ ] IPv6 support
- [ ] Graphical output (if terminal supports)

## Python Implementation Details

### Why Python for This Tool?
- **Text processing:** Powerful regex and string manipulation for parsing tcpdump lines
- **Data structures:** Built-in `Counter`, `defaultdict`, sets, and dicts for efficient aggregation
- **Type safety:** Type hints help catch errors early and improve code documentation
- **Maintainability:** Easier to read and maintain complex parsing logic
- **Testing:** pytest provides robust testing framework for complex logic
- **Libraries:** `ipaddress` module for IP validation, `rich` for enhanced output formatting
- **Performance:** Fast enough for line-by-line streaming of large files (250K+ lines)

### Key Python Features and Patterns

**Type Hints:**
- Use type hints for all function signatures: `def parse_line(line: str) -> Optional[Dict[str, Any]]`
- Improves IDE support and catches errors early

**Data Structures:**
- `collections.Counter`: For counting IPs, protocols, ports efficiently
- `collections.defaultdict`: For aggregating connection data
- `set`: For tracking unique IP addresses
- `dict`: For structured data (parsed packet information)

**Standard Library Modules:**
- `ipaddress`: For IP validation and private IP detection
- `pathlib.Path`: For modern, cross-platform file path handling
- `argparse`: For CLI argument parsing
- `re`: Compiled regex patterns for parsing tcpdump lines
- `csv`: For CSV output formatting

**Best Practices:**
- Context managers: `with open()` for file handling
- Streaming: Line-by-line processing with `for line in file:`
- Compiled regex: Use `re.compile()` for repeated pattern matching
- Graceful degradation: Check for optional libraries (`rich`), fall back to plain text
- Docstrings: Use Google or NumPy style for all functions/classes

## Notes

### TCPDump Output Variations
- Different tcpdump versions may have slightly different output formats
- The `-n` flag ensures numeric IPs (no DNS resolution)
- May need to handle different verbosity levels
- Consider supporting `-r` (read from file) format if different

### Performance Considerations (Critical for Large Files)

> **Real data analysis:** See [analyze-tcpdump-data-analysis.md](analyze-tcpdump-data-analysis.md#recommendations-for-python-implementation) for performance recommendations based on actual 250K+ line files.

- **File size:** Real files can be 250K+ lines (28MB+)
- **Streaming required:** MUST use line-by-line processing, never load entire file into memory
  - Use: `with open(file_path) as f: for line in f: ...`
  - Never use: `f.read()` or `f.readlines()` for entire file
- **Efficient parsing:** Use compiled regex patterns (`re.compile()`) for repeated matching
- **Counting strategy:** Use `collections.Counter` and `defaultdict` for efficient counting
- **Memory efficiency:** Process and discard lines immediately, only keep aggregated statistics in memory
- **Data structures:** Use sets for unique IP tracking, dicts for counting
- **Multiple files:** Process sequentially, aggregate results at end
- **Progress indication:** Use `rich.progress` or simple counter for large files (optional)
- **Caching:** Consider caching parsed data if analyzing same file multiple times (future enhancement)
- **Performance testing:** Profile with `cProfile` if needed for optimization

### Integration Opportunities
- Could integrate with `greynoise-lookup.sh` to enrich IP data
- Could integrate with `record-whois.sh` for IP intelligence
- Could feed into monitoring/alerting systems

### Similar Tools Reference
- `what-is-left.py` - Python script structure, argparse usage, rich library integration
- `network-tools/diagnostics/sort-netstat-tcp.sh` - Analysis tool co-located with data source (similar pattern)
- `network-tools/capture/record-tcpdump.sh` - Related tool that generates the data this tool analyzes
- `azure/show-location-authenticationDetails.sh` - JSON parsing and formatting example
- `greynoise/greynoise-lookup.sh` - IP address validation patterns (useful reference for IP handling)

### Location and Integration
- **File location:** `network-tools/capture/analyze-tcpdump.py`
- **Related tool:** `network-tools/capture/record-tcpdump.sh` (generates input data)
- **Output location:** `network-tools/capture/log/record-tcpdump_*.txt` (default input files)
- **Pattern:** Follows same pattern as `sort-netstat-tcp.sh` being co-located with `record-netstat.sh`

### Code Quality Standards
- Follow Python PEP 8 style guidelines
- Use type hints throughout for better code documentation
- Use docstrings (Google or NumPy style) for all functions/classes
- Use `pathlib.Path` for file operations (modern, cross-platform)
- Use `argparse` for CLI (standard library, well-documented)
- Use `collections.Counter` and `defaultdict` for efficient counting
- Use `ipaddress` module for IP validation and private IP detection
- Graceful degradation: Check for optional libraries (`rich`), fall back to plain text
- Follow patterns from `what-is-left.py` for consistency
