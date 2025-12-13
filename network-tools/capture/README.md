# Network Capture Analysis Tools

Tools for capturing and analyzing network traffic using tcpdump.

## Tools

### analyze-tcpdump.py

Analyzes tcpdump output files to extract IP addresses, connection statistics, and protocol breakdowns.

**Features:**
- Parse tcpdump output (TCP, UDP, ICMP, QUIC, DNS)
- Extract IP addresses (source, destination, unique)
- Connection pair analysis
- Port usage statistics
- Protocol breakdown
- Filtering by protocol, IP, port
- Multiple output formats (summary, IPs, connections, ports, CSV)
- Exclude local/private IPs option

**Quick Start:**
```bash
# Analyze latest tcpdump file in log/ directory
./analyze-tcpdump.py

# Analyze specific file
./analyze-tcpdump.py log/record-tcpdump_2025-12-12_082910.txt

# Show top 20 IPs only
./analyze-tcpdump.py -o ips -t 20

# Filter TCP only, exclude local IPs
./analyze-tcpdump.py -p tcp -l

# Filter by specific IP address
./analyze-tcpdump.py -i 8.8.8.8

# Output as CSV
./analyze-tcpdump.py -c -o connections
```

**Options:**
- `-f, --file` - Input tcpdump file(s)
- `-o, --output-format` - Output format: summary, ips, connections, ports, all (default: all)
- `-p, --protocol` - Filter by protocol: tcp, udp, icmp, quic, all (default: all)
- `-i, --ip` - Filter by IP address
- `-P, --port` - Filter by port number
- `-l, --exclude-local` - Exclude private/local IPs
- `-t, --top` - Show top N results (default: 10)
- `-d, --directory` - Search directory for tcpdump files
- `-c, --csv` - Output as CSV
- `-q, --quiet` - Quiet mode
- `-v, --verbose` - Verbose output

### record-tcpdump.sh

Records network traffic using tcpdump and saves output to timestamped log files.

**Features:**
- Captures all network traffic on default interface
- Saves output to `log/record-tcpdump_YYYY-MM-DD_HHMMSS.txt`
- Runs continuously until stopped (Ctrl+C)
- Automatically runs tcpdump with sudo (no need to run script with sudo)
- Automatically creates log directory if needed

**Usage:**
```bash
# Record network traffic (runs continuously until stopped)
./record-tcpdump.sh

# Display help
./record-tcpdump.sh -h
```

**Note:** The script runs continuously until manually stopped. It automatically uses `sudo` to run tcpdump internally, so you don't need to run the script itself with sudo. Output is saved to timestamped files in the `log/` directory.

### sanitize-analysis-ipmask.py

Sanitizes analyze-tcpdump.py output for public publication by masking private IPs.

**Features:**
- Masks 2nd and 3rd octets with random two-letter combinations (G-Z, uppercase)
- Preserves 1st and 4th octets unchanged
- Separate random mappings for 2nd vs 3rd octets
- No hex letters (A-F) to avoid confusion
- Different mappings per run (randomized)
- Consistent mappings within each run

**Usage:**
```bash
# Basic sanitization (masks private IPs only)
./sanitize-analysis-ipmask.py log/record-tcpdump_2025-12-12_082910_analysis.txt

# Show mapping table
./sanitize-analysis-ipmask.py log/record-tcpdump_2025-12-12_082910_analysis.txt --show-mapping

# Also mask public IPs
./sanitize-analysis-ipmask.py log/record-tcpdump_2025-12-12_082910_analysis.txt --mask-public

# Use specific seed for reproducible mappings
./sanitize-analysis-ipmask.py log/record-tcpdump_2025-12-12_082910_analysis.txt --seed 12345
```

**Example:**
```
Original:  192.168.42.7
Masked:    192.GS.QS.7
           (2nd octet 168 -> GS, 3rd octet 42 -> QS)
```

**Real Example Output:**
See [`examples/record-tcpdump_2025-12-12_104608_analysis.ipmasked.txt`](examples/record-tcpdump_2025-12-12_104608_analysis.ipmasked.txt) for a complete example of sanitized output. The file shows:
- Private IPs masked (e.g., `192.168.1.12` → `192.JN.MU.12`)
- Public IPs remain unchanged (e.g., `151.101.67.5` stays as-is)
- All statistics and relationships preserved
- IP format maintained (looks like valid IP addresses)

Example from the file:
```
Top 10 Source IPs:
  192.JN.MU.12        18,134 packets
  151.101.67.5         4,590 packets
  151.101.3.5          3,664 packets
  192.JN.MU.7         1,781 packets
  23.63.157.145        1,310 packets
```

The masked IPs (like `192.JN.MU.12`) maintain the IP-like appearance while anonymizing private network addresses for safe public sharing.

## Development

### Running Tests

```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run integration tests
make test-integration

# Run with coverage
make test-coverage

# Run with verbose output
make test-verbose
```

### Code Quality

```bash
# Run linting (pylint + flake8)
make lint

# Run type checking (mypy)
make type-check
```

### Dependencies

Tools auto-install dependencies when needed:
- `pytest` and `pytest-cov` (for testing)
- `pylint` and `flake8` (for linting)
- `mypy` (for type checking)

## Documentation

- **Examples:** `examples/` - Example sanitized output files
- **Bug Documentation:** `docs/bugs/` - Historical bug fixes
- **Sanitization:** `docs/sanitization/` - IP masking documentation and examples
- **Test Coverage:** `docs/test-coverage-analysis.md` - Coverage analysis and recommendations
- **Organization:** `docs/ORGANIZATION-RECOMMENDATION.md` - Directory structure documentation

## Test Coverage

Current test coverage: **94%** (327/348 statements)

- 94 tests total
- Unit tests, integration tests, and CLI tests
- Comprehensive test suite in `tests/`

## File Structure

```
network-tools/capture/
├── analyze-tcpdump.py          # Main analysis tool
├── record-tcpdump.sh           # Recording script
├── sanitize-analysis-ipmask.py # Sanitization tool
├── Makefile                    # Build configuration
├── examples/                   # Example output files
│   └── record-tcpdump_2025-12-12_104608_analysis.ipmasked.txt
├── tests/                      # Test suite
│   ├── test_analyze_tcpdump.py
│   ├── test_cli_integration.py
│   ├── test_sanitize_ipmask.py
│   └── data/                   # Test data
├── docs/                       # Documentation
│   ├── bugs/                   # Bug documentation
│   ├── sanitization/           # Sanitization docs
│   └── test-coverage-analysis.md
└── log/                        # Output files (gitignored)
```

## Examples

### Basic Analysis
```bash
# Analyze latest capture
./analyze-tcpdump.py

# Output:
# TCPDump Analysis Summary
# ========================
# Total Packets: 111,199
# Unique Source IPs: 280
# Unique Destination IPs: 288
# Protocols: QUIC (72,097), UDP (24,879), TCP (10,449), ...
```

### Filtered Analysis
```bash
# Show only UDP traffic to port 53 (DNS)
./analyze-tcpdump.py -p udp -P 53

# Show only external traffic (exclude private IPs)
./analyze-tcpdump.py -l
```

### Sanitized Output
```bash
# Create sanitized version for public sharing
./sanitize-analysis-ipmask.py log/record-tcpdump_2025-12-12_104608_analysis.txt

# Output saved to: log/record-tcpdump_2025-12-12_104608_analysis.ipmasked.txt
```

**See:** [`examples/record-tcpdump_2025-12-12_104608_analysis.ipmasked.txt`](examples/record-tcpdump_2025-12-12_104608_analysis.ipmasked.txt) for a complete real-world example of sanitized output with masked private IPs.

## Requirements

- Python 3.8+
- tcpdump (for recording)
- Optional: rich library (for enhanced output)

## License

[Add license information if applicable]
