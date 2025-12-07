# Network Tools

Network diagnostic, scanning, intelligence, and capture tools.

## Categories

- **diagnostics/** - Network connection and configuration diagnostics
- **scanning/** - Network security scanning and enumeration
- **intelligence/** - IP address and network block information
- **capture/** - Deep packet inspection and traffic capture

## Quick Reference

### Diagnostics
- `diagnostics/record-netstat.sh` - Network connections and ports
- `diagnostics/record-nslookup.sh <ip>` - DNS lookups
- `diagnostics/record-network-config.sh` - Interface configuration
- `diagnostics/sort-netstat-tcp.sh [file]` - Sort and filter TCP connections from netstat output

### Scanning
- `scanning/record-nmap.sh <target>` - Port scanning and service detection

### Intelligence
- `intelligence/record-whois.sh <ip>` - WHOIS lookups
- `intelligence/record-ip-api-json.sh <ip>` - IP API data

### Capture
- `capture/record-tcpdump.sh` - Packet capture (requires sudo)

## Usage

All scripts follow a common pattern:
1. Execute a network command
2. Capture output with timestamps
3. Save to timestamped files

Most scripts create output files in the current directory. See individual script headers for details.
