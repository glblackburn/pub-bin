# TCPDump Data Analysis - Real File Examination

**Related Documents:**
- **[Planning Document](analyze-tcpdump-plan.md)** - Complete planning and implementation guide for `analyze-tcpdump.py`
- This document provides detailed analysis of real tcpdump output data to inform the Python implementation

**Note:** This document analyzes real tcpdump output data to inform the Python implementation of `analyze-tcpdump.py`.

## File Analyzed
- **File:** `network-tools/capture/log/record-tcpdump_2025-12-09_215604.txt`
- **Size:** 250,513 lines (~28MB)
- **Time Range:** 21:56:11 to 23:06:21 (approximately 1 hour 10 minutes)

## Protocol Distribution

| Protocol | Count | Percentage |
|----------|-------|------------|
| UDP      | 159,407 | 63.7% |
| QUIC     | 17,827  | 7.1% |
| ICMP     | 1,985   | 0.8% |
| TCP      | 0       | 0% |

**Note:** TCP not present in this sample, but tool should handle it.

## Top IP Addresses (by packet count)

| IP Address | Count | Type |
|------------|-------|------|
| 192.168.X.X | 216,473 | Local (source/destination) |
| 203.0.113.1 | 31,520 | External |
| 224.0.0.251 | 21,148 | Multicast (mDNS) |
| 203.0.113.2 | 20,433 | External |
| 203.0.113.3 | 16,147 | External |
| 203.0.113.4 | 9,816 | External |
| 203.0.113.5 | 8,194 | External |
| 203.0.113.6 | 7,423 | External |
| 203.0.113.7 | 7,131 | External |
| 203.0.113.8 | 6,919 | External |

## Line Format Patterns Observed

### 1. Standard UDP Packets (Most Common)
```
21:56:11.886998 IP 203.0.113.10.46102 > 192.168.X.X.59922: UDP, length 28
```
- Format: `HH:MM:SS.microseconds IP src.ip.src_port > dst.ip.dst_port: UDP, length X`
- Has ports for both source and destination
- Protocol: "UDP" (uppercase)

### 2. QUIC Packets
```
21:56:16.643287 IP 192.168.X.X.59524 > 203.0.113.11.443: quic, protected
23:06:20.794967 IP 192.168.X.X.54275 > 203.0.113.12.443: quic, initial, dcid <example_id>, token ..., length 1161
```
- Format: `IP src.ip.src_port > dst.ip.dst_port: quic, [flags], [additional fields], length X`
- Has ports
- Protocol: "quic" (lowercase)
- May have additional fields: `initial`, `protected`, `dcid`, `scid`, `token`, etc.

### 3. ICMP Packets (No Ports)
```
21:56:12.338504 IP 192.168.X.254 > 192.168.X.X: ICMP time exceeded in-transit, length 40
23:06:21.395971 IP 203.0.113.13 > 192.168.X.X: ICMP host 203.0.113.13 unreachable, length 64
```
- Format: `IP src.ip > dst.ip: ICMP message_type, length X`
- **NO PORTS** - format is `ip > ip` not `ip.port > ip.port`
- Protocol: "ICMP" (uppercase)
- Various message types: `time exceeded in-transit`, `host unreachable`, etc.

### 4. DNS Queries (Embedded in UDP)
```
23:06:20.782221 IP 192.168.X.X.12863 > 192.168.X.1.53: 52898+ Type65? example.com. (37)
23:06:20.782360 IP 192.168.X.X.42299 > 192.168.X.1.53: 5267+ A? example.com. (37)
```
- Format: `IP src.ip.src_port > dst.ip.dst_port: query_id+ query_type? domain_name. (length)`
- Still parseable as UDP packets
- Contains DNS query information (optional enhancement for tool)

### 5. Multicast/Broadcast Packets
```
21:56:14.655689 IP 172.X.X.10.57621 > 172.X.255.255.57621: UDP, length 44
21:56:14.718036 IP 172.X.X.10.5353 > 224.0.0.251.5353: 0 PTR (QM)? _example_service._tcp.local. (41)
```
- Multicast: 224.0.0.251 (mDNS), 224.0.0.252, etc.
- Broadcast: 172.X.255.255, 172.X.255.255, etc.
- May have ports
- mDNS uses port 5353

## Parsing Requirements (Python Implementation)

### IP Address Extraction
- **Source IP:** Field 3 in line (after "IP") - `parts[2]` in Python (0-indexed)
- **Destination IP:** Field 5 in line (after ">") - `parts[4]` in Python (0-indexed)
- **Format with ports:** `ip.port` - use regex `(\d+\.\d+\.\d+\.\d+)\.(\d+)` to extract IP and port separately
- **Format without ports (ICMP):** `ip` - use regex `(\d+\.\d+\.\d+\.\d+)` to extract IP only
- **Example:** `203.0.113.10.46102` → IP: `203.0.113.10`, Port: `46102`
- **Python approach:** Use compiled regex patterns for efficient matching

### Port Extraction
- **Standard format:** Extract number after last dot using regex group capture
- **ICMP:** No ports (return `None` in Python)
- **Edge case:** Some IPs may have multiple dots (valid IPv4 addresses) - regex handles this correctly
- **Python approach:** Use `int()` conversion after regex match, handle `None` for ICMP

### Protocol Detection
- **UDP:** Look for "UDP" (uppercase, case-sensitive) - use `' UDP' in line` or `', UDP' in line`
- **QUIC:** Look for "quic" (lowercase) - use `'quic' in line.lower()`
- **ICMP:** Look for "ICMP" (uppercase, case-sensitive) - use `' ICMP' in line` or `', ICMP' in line`
- **TCP:** Look for "Flags" or "tcp" (not in sample, but should handle) - use `'Flags' in line` or `' tcp' in line.lower()`
- **Python approach:** Use string membership testing (`in` operator) for efficiency

### Packet Length
- Format: `length X` or `length X, ...`
- Available for most packets
- Can be extracted for statistics
- **Python approach:** Use regex `r'length (\d+)'` to extract length value

## Key Insights for Tool Design

1. **File Size:** 250K+ lines requires streaming processing - never load entire file
2. **Local IP Dominance:** Local IP (192.168.X.X) appears 216K times - filtering option critical
3. **Protocol Variety:** UDP dominant, but QUIC and ICMP present - must handle all
4. **ICMP Special Case:** No ports - requires special parsing logic
5. **Multicast/Broadcast:** Present in significant numbers - may want to filter or highlight
6. **DNS Embedded:** DNS queries in UDP - could be enhanced feature
7. **QUIC Complexity:** Additional fields present - parse basic info, ignore extras for v1

## Recommended Parsing Approach (Python)

> **See also:** [analyze-tcpdump-plan.md](analyze-tcpdump-plan.md) for complete implementation details, class structure, and function specifications.

### Single-Pass Python Implementation
```python
import re
from collections import Counter, defaultdict
from ipaddress import ip_address

# Compiled regex patterns for performance
IP_PORT_PATTERN = re.compile(r'(\d+\.\d+\.\d+\.\d+)\.(\d+)')
IP_ONLY_PATTERN = re.compile(r'(\d+\.\d+\.\d+\.\d+)')
TIMESTAMP_PATTERN = re.compile(r'^(\d{2}:\d{2}:\d{2}\.\d+)')

def parse_tcpdump_line(line: str) -> Optional[Dict]:
    """Parse a single tcpdump line into structured data"""
    # Check if line starts with timestamp (valid tcpdump line)
    if not TIMESTAMP_PATTERN.match(line):
        return None
    
    parts = line.split()
    if len(parts) < 5 or parts[1] != 'IP':
        return None  # Not an IP packet
    
    src_field = parts[2]  # Field 3 (0-indexed: 2)
    dst_field = parts[4]  # Field 5 (0-indexed: 4)
    
    # Extract source IP and port
    src_match = IP_PORT_PATTERN.match(src_field)
    if src_match:
        src_ip = src_match.group(1)
        src_port = int(src_match.group(2))
    else:
        # ICMP case - no port
        src_match = IP_ONLY_PATTERN.match(src_field)
        if src_match:
            src_ip = src_match.group(1)
            src_port = None
        else:
            return None
    
    # Extract destination IP and port
    dst_match = IP_PORT_PATTERN.match(dst_field)
    if dst_match:
        dst_ip = dst_match.group(1)
        dst_port = int(dst_match.group(2))
    else:
        # ICMP case - no port
        dst_match = IP_ONLY_PATTERN.match(dst_field)
        if dst_match:
            dst_ip = dst_match.group(1)
            dst_port = None
        else:
            return None
    
    # Detect protocol
    line_lower = line.lower()
    if ' UDP' in line or ', UDP' in line:
        protocol = 'UDP'
    elif 'quic' in line_lower:
        protocol = 'QUIC'
    elif ' ICMP' in line or ', ICMP' in line:
        protocol = 'ICMP'
    elif 'Flags' in line or ' tcp' in line_lower:
        protocol = 'TCP'
    else:
        protocol = 'UNKNOWN'
    
    # Extract packet length if available
    length_match = re.search(r'length (\d+)', line)
    length = int(length_match.group(1)) if length_match else None
    
    return {
        'src_ip': src_ip,
        'dst_ip': dst_ip,
        'src_port': src_port,
        'dst_port': dst_port,
        'protocol': protocol,
        'length': length
    }

# Usage: Stream processing
ip_counts = Counter()
connection_counts = defaultdict(int)
protocol_counts = Counter()

with open('tcpdump_file.txt') as f:
    for line in f:
        parsed = parse_tcpdump_line(line)
        if parsed:
            ip_counts[parsed['src_ip']] += 1
            ip_counts[parsed['dst_ip']] += 1
            connection_counts[(parsed['src_ip'], parsed['dst_ip'])] += 1
            protocol_counts[parsed['protocol']] += 1
```

### Key Python Implementation Points
- **Compiled regex patterns:** Use `re.compile()` for repeated matching (performance)
- **Streaming processing:** Use `for line in file:` never `file.read()` or `file.readlines()`
- **Efficient data structures:** Use `Counter` and `defaultdict` for counting
- **Type hints:** Add type hints for better code quality
- **Error handling:** Return `None` for unparseable lines, continue processing
- **Single pass:** Extract all needed data in one pass through the file

## Statistics Available

From this file, we can extract:
- Total packets: 250,513
- Unique source IPs: ~hundreds
- Unique destination IPs: ~hundreds
- Unique IP pairs: ~thousands
- Protocol breakdown: UDP/QUIC/ICMP counts
- Port usage: Most common source/destination ports
- Connection patterns: Most frequent IP pairs
- Time analysis: Packet distribution over time (if timestamps parsed)

### Python Data Structures for Statistics

**Recommended approach:**
- **Total packets:** Simple counter variable
- **Unique IPs:** Use `set()` to track unique source/destination IPs
- **IP counts:** Use `Counter()` for efficient counting
- **Connection pairs:** Use `defaultdict(int)` with tuple keys: `(src_ip, dst_ip, src_port, dst_port, protocol)`
- **Protocol counts:** Use `Counter()` for protocol distribution
- **Port usage:** Use `Counter()` for source/destination ports separately
- **Top N queries:** Use `Counter.most_common(n)` for efficient top N selection

**Example:**
```python
from collections import Counter, defaultdict

# Initialize data structures
unique_src_ips = set()
unique_dst_ips = set()
src_ip_counts = Counter()
dst_ip_counts = Counter()
connection_counts = defaultdict(int)  # Key: (src_ip, dst_ip, protocol)
protocol_counts = Counter()
src_port_counts = Counter()
dst_port_counts = Counter()

# During processing
for line in file:
    parsed = parse_tcpdump_line(line)
    if parsed:
        unique_src_ips.add(parsed['src_ip'])
        unique_dst_ips.add(parsed['dst_ip'])
        src_ip_counts[parsed['src_ip']] += 1
        dst_ip_counts[parsed['dst_ip']] += 1
        connection_counts[(parsed['src_ip'], parsed['dst_ip'], parsed['protocol'])] += 1
        protocol_counts[parsed['protocol']] += 1
        if parsed['src_port']:
            src_port_counts[parsed['src_port']] += 1
        if parsed['dst_port']:
            dst_port_counts[parsed['dst_port']] += 1

# Get top 10 source IPs
top_src_ips = src_ip_counts.most_common(10)
```

## Recommendations for Python Implementation

> **Implementation details:** See [analyze-tcpdump-plan.md](analyze-tcpdump-plan.md#implementation-details) for complete class structure, function specifications, and implementation checklist.

1. **Streaming is mandatory** - files are too large for in-memory processing
   - Use: `with open(file_path) as f: for line in f: ...`
   - Never: `f.read()` or `f.readlines()` for entire file

2. **ICMP handling is critical** - special case with no ports
   - Use separate regex patterns for IP with/without ports
   - Handle `None` for ports in ICMP packets

3. **Local IP filtering** - essential given dominance of local traffic
   - Use `ipaddress` module: `ip_address(ip).is_private`
   - Filter out 10.x, 172.16-31.x, 192.168.x, 127.x, 169.254.x

4. **Protocol filtering** - useful for focusing on specific traffic types
   - Use string matching with case sensitivity (UDP/ICMP uppercase, quic lowercase)

5. **Top N reporting** - most useful feature given large number of unique IPs
   - Use `Counter.most_common(n)` for efficient top N selection

6. **Efficient counting** - use Python's built-in data structures
   - `collections.Counter` for counting IPs, protocols, ports
   - `collections.defaultdict(int)` for connection pair counting
   - Much more efficient than bash `sort|uniq -c`

7. **Error tolerance** - skip malformed lines, continue processing
   - Return `None` from parser for unparseable lines
   - Collect warnings/errors, report summary at end

8. **Performance optimization**
   - Compile regex patterns once with `re.compile()`
   - Process line-by-line, discard after parsing
   - Only keep aggregated statistics in memory
   - Use `rich.progress` for progress indication on large files (optional)
