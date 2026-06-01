# Network Tools

Network diagnostic, scanning, intelligence, and capture tools.

## Categories

- **diagnostics/** - Network connection and configuration diagnostics
- **scanning/** - Network security scanning and enumeration
- **intelligence/** - IP address and network block information
- **capture/** - Deep packet inspection and traffic capture

## Quick Reference

### Diagnostics
- `diagnostics/what-is-my-ip.sh [-h] [-j|--json]` - Discover this host's public IP + geo
  - Discovers this host's public IPv4 and IPv6 addresses (via DNS queries to Cloudflare and Google) and looks up geo / ISP / ASN information for the IPv4 via `ip-api-json.sh`
  - Default output: human-readable IPv4, IPv6, and Location/ISP summary
  - `--json` (or `-j`) output: single JSON object `{ts, ipv4, ipv6, geo:{...}}`
  - Log file: `~/log/ip_log/what-is-my-ip_YYYY-MM-DD_HHMMSS.log` (always written, both modes)
  - Options: `-h` for help
- `diagnostics/record-netstat.sh` - Network connections and ports
  - Records network connection information using `netstat -an`
  - Output: `record-netstat_YYYY-MM-DD_HHMMSS.txt`
  - Options: `-h` for help
- `diagnostics/record-nslookup.sh <ip>` - DNS lookups
  - Records DNS lookup results for an IP address using `nslookup`
  - Output: `nslookup_<ip>_YYYY-MM-DD_HHMMSS.txt`
  - Options: `-h` for help
  - Requires: IP address as argument
- `diagnostics/record-network-config.sh` - Interface configuration
  - Records network interface configuration using `ifconfig`
  - Output: `net_all_info.txt`, `net_wifi_info.txt`, `net_lan_info.txt`
  - Options: `-h` for help
  - Handles missing interfaces gracefully
- `diagnostics/sort-netstat-tcp.sh [file]` - Sort and filter TCP connections from netstat output
  - Sorts and filters TCP connections from netstat output files
  - Usage: `sort-netstat-tcp.sh [netstat_file]`
  - Default: Uses `record-netstat_*.txt` if no file specified
  - Output: `{input_file}_tcp_sort.txt`

### Scanning
- `scanning/record-nmap.sh <target>` - Port scanning and service detection
  - Records network port scanning results using `nmap`
  - Output: `<target>_nmap_oG_YYYY-MM-DD_HHMMSS.txt`
  - Options: `-h` for help
  - Requires: Target IP address or hostname as argument

### Intelligence
- `intelligence/record-whois.sh <ip>` - WHOIS lookups
  - Records WHOIS information for an IP address
  - Output: `whois_<ip>_YYYY-MM-DD_HHMMSS.txt`
  - Options: `-h` for help
  - Requires: IP address as argument
- `intelligence/record-ip-api-json.sh <ip>` - IP API data
  - Records IP API/WHOIS data in JSON format using `ip-api-json.sh`
  - Output: `ip-api-whois_<ip>_YYYY-MM-DD_HHMMSS.txt`
  - Options: `-h` for help
  - Requires: IP address as argument
- `intelligence/ip-api-json.sh <ip>` - IP geo / ISP / ASN lookup
  - Looks up geo, ISP, and ASN information for an IP address using the public ip-api.com API and pretty-prints the JSON via `jq`
  - Output: pretty JSON to stdout (no file written)
  - Options: `-h` for help
  - Requires: IP address as argument
  - Notes: free tier rate limit is 45 requests/minute per source IP

### Capture
- `capture/record-tcpdump.sh` - Packet capture (requires sudo)
  - Records network packet captures using `tcpdump`
  - Output: `log/record-tcpdump_YYYY-MM-DD_HHMMSS.txt`
  - Options: `-h` for help
  - Requires: sudo privileges
  - Note: Runs continuously until stopped (Ctrl+C)
- `capture/analyze-tcpdump.py` - Analyze tcpdump output files
  - Analyzes tcpdump output to extract IP addresses and connection statistics
  - Supports UDP, TCP, ICMP, and QUIC protocols
  - Multiple output formats: summary, IPs, connections, ports, CSV
  - Filtering by protocol, IP address, port, and local IP exclusion
  - Usage: `analyze-tcpdump.py [options] [tcpdump_file...]`
  - Options: `-h` for help, see tool help for full usage and examples
  - Default: Analyzes latest file in `log/` directory if no file specified

## Usage

All scripts follow a common pattern:
1. Execute a network command
2. Capture output with timestamps
3. Save to timestamped files

Most scripts create output files in the current directory. See individual script headers for details.
