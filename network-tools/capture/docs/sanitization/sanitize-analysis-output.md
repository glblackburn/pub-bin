# Sanitization Process for TCPDump Analysis Output

## Overview

This document describes the filtering process to create a publicly-publishable version of `analyze-tcpdump.py` output while preserving high-level context and demonstrating the tool's capabilities.

## Sensitive Information to Mask

1. **Private/Local IP Addresses** - Reveal internal network structure:
   - `192.168.x.x` (RFC 1918 private)
   - `172.16-31.x.x` (RFC 1918 private)
   - `10.x.x.x` (RFC 1918 private)
   - `224.0.0.x` (multicast addresses)
   - `255.255.255.255` (broadcast)

2. **File Paths** - Contain user-specific directory structure:
   - Full paths like `/Users/lblackb/data/lblackb/git/pub-bin/...`

3. **Specific Public IPs** - May reveal infrastructure details (optional):
   - Can be replaced with example IPs or generic placeholders

4. **Non-Standard Ports** - May reveal specific services (optional):
   - Ports like `9993`, `33797`, etc. could be masked

## Recommended Filtering Strategy

### Phase 1: Mask Private IPs (Required)

**Approach:** Replace private IPs with consistent placeholders that maintain relationships.

**Rules:**
- Replace all `192.168.x.x` with `PRIVATE_LAN_1`, `PRIVATE_LAN_2`, etc. (maintain order)
- Replace all `172.16-31.x.x` with `PRIVATE_SUBNET_1`, `PRIVATE_SUBNET_2`, etc.
- Replace all `10.x.x.x` with `PRIVATE_NET_1`, `PRIVATE_NET_2`, etc.
- Replace `224.0.0.x` with `MULTICAST_1`, `MULTICAST_2`, etc.
- Replace `255.255.255.255` with `BROADCAST`

**Benefits:**
- Preserves network topology relationships
- Maintains packet counts and statistics
- Shows tool's ability to identify private vs public IPs

### Phase 2: Mask File Paths (Required)

**Approach:** Replace with generic example paths.

**Rules:**
- Replace full paths with: `log/record-tcpdump_YYYY-MM-DD_HHMMSS.txt`
- Or use: `example-tcpdump-capture.txt`

**Benefits:**
- Removes user-specific information
- Maintains file reference context

### Phase 3: Mask Public IPs (Optional - Recommended)

**Approach:** Replace with example/public IPs or generic placeholders.

**Options:**
1. **Replace with example IPs** - Use well-known example IPs:
   - `8.8.8.8` (Google DNS) → keep as-is (public example)
   - Other public IPs → replace with `PUBLIC_IP_1`, `PUBLIC_IP_2`, etc.

2. **Replace with RFC 5737 documentation IPs**:
   - `192.0.2.0/24` (TEST-NET-1)
   - `198.51.100.0/24` (TEST-NET-2)
   - `203.0.113.0/24` (TEST-NET-3)

**Benefits:**
- Further anonymizes infrastructure
- Still demonstrates tool capabilities

### Phase 4: Mask Non-Standard Ports (Optional)

**Approach:** Replace non-standard ports with generic placeholders.

**Rules:**
- Keep standard ports (80, 443, 53, 22, etc.) as-is
- Replace non-standard ports with `PORT_XXXX` or `HIGH_PORT_1`, etc.

**Benefits:**
- Hides specific service configurations
- Maintains port usage patterns

## Implementation Options

### Option 1: Manual Script (Python)

Create a Python script that:
1. Reads the analysis output file
2. Identifies and maps private IPs to placeholders
3. Replaces file paths
4. Optionally replaces public IPs
5. Outputs sanitized version

### Option 2: Sed/Awk Script (Shell)

Use shell tools for simple replacements:
- `sed` for pattern-based replacements
- `awk` for more complex logic

### Option 3: Add Sanitization Feature to analyze-tcpdump.py

Add a `--sanitize` flag to the tool itself that:
- Automatically masks private IPs
- Masks file paths
- Optionally masks public IPs

## Recommended Output Format

The sanitized output should:
- ✅ Preserve all statistics (packet counts, protocol breakdowns)
- ✅ Maintain structure and formatting
- ✅ Show relationships between IPs (same placeholder = same original IP)
- ✅ Include a header comment indicating sanitization
- ✅ Demonstrate tool's full capabilities

## Example Sanitized Output Structure

```
# Sanitized Analysis Output
# Private IPs have been replaced with placeholders (PRIVATE_LAN_*, PRIVATE_SUBNET_*, etc.)
# Public IPs have been replaced with example IPs or placeholders
# File paths have been anonymized

TCPDump Analysis Summary
========================
Files: log/record-tcpdump_2025-12-12_082910.txt
Total Packets: 111,199
Unique Source IPs: 280
Unique Destination IPs: 288
Protocols: QUIC (72,097), UDP (24,879), TCP (10,449), UNKNOWN (3,550), ICMP (224)

Top 10 Source IPs:
  PUBLIC_IP_1           38,426 packets
  PRIVATE_LAN_1         31,520 packets
  PUBLIC_IP_2           13,092 packets
  ...
```

## Security Considerations

1. **Consistency**: Same original IP must always map to same placeholder
2. **Relationships**: Connection pairs should maintain relationships
3. **Statistics**: All counts must remain accurate
4. **Review**: Manually review output before publishing
5. **No Leakage**: Ensure no original sensitive data remains

## Next Steps

1. Choose implementation approach (recommend Python script for flexibility)
2. Implement the filtering logic
3. Test on sample output
4. Review sanitized output manually
5. Create sanitized version for publication
