#!/usr/bin/env python3
"""
analyze-tcpdump.py - Analyze tcpdump output files

Analyzes tcpdump output files to extract IP addresses, monitor network
connections, and generate connection statistics.
"""

# Standard library imports
import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from ipaddress import ip_address, IPv4Address
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any

# Optional third-party imports
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

################################################################################
# Constants
################################################################################

# Well-known port names (common ports)
WELL_KNOWN_PORTS = {
    20: "FTP-DATA", 21: "FTP", 22: "SSH", 23: "TELNET", 25: "SMTP",
    53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS",
    993: "IMAPS", 995: "POP3S", 3306: "MySQL", 5432: "PostgreSQL",
    8080: "HTTP-ALT", 8443: "HTTPS-ALT"
}

################################################################################
# TcpdumpParser Class
################################################################################

class TcpdumpParser:
    """Parse tcpdump output lines and extract connection information."""
    
    # Compiled regex patterns for performance
    IP_PACKET_PATTERN = re.compile(
        r'^\d{2}:\d{2}:\d{2}\.\d+\s+IP\s+'
        r'([\d.]+(?:\.\d+)?)\s+>\s+([\d.]+(?:\.\d+)?)\s*:'
    )
    
    PROTOCOL_PATTERNS = {
        'UDP': re.compile(r'\bUDP\b'),
        'ICMP': re.compile(r'\bICMP\b'),
        'QUIC': re.compile(r'\bquic\b'),
        'TCP': re.compile(r'\b(?:tcp|Flags)\b', re.IGNORECASE),
    }
    
    LENGTH_PATTERN = re.compile(r'length\s+(\d+)')
    
    def parse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single tcpdump output line.
        
        Args:
            line: A line from tcpdump output
            
        Returns:
            Dictionary with keys: src_ip, dst_ip, src_port, dst_port, protocol, length
            Returns None if line cannot be parsed
        """
        line = line.strip()
        if not line:
            return None
        
        # Match IP packet pattern
        match = self.IP_PACKET_PATTERN.match(line)
        if not match:
            return None
        
        src_field = match.group(1)
        dst_field = match.group(2)
        
        # Extract IP addresses and ports
        src_ip, src_port = self._extract_ip_port(src_field)
        dst_ip, dst_port = self._extract_ip_port(dst_field)
        
        if not src_ip or not dst_ip:
            return None
        
        # Detect protocol
        protocol = self._detect_protocol(line)
        
        # Extract packet length
        length = self._extract_length(line)
        
        return {
            'src_ip': src_ip,
            'dst_ip': dst_ip,
            'src_port': src_port,
            'dst_port': dst_port,
            'protocol': protocol,
            'length': length
        }
    
    def _extract_ip_port(self, field: str) -> Tuple[Optional[str], Optional[int]]:
        """
        Extract IP address and port from a field like '192.168.1.1.54321' or '192.168.1.1'.
        
        Args:
            field: Field containing IP and optionally port
            
        Returns:
            Tuple of (ip_address, port_number) where port may be None
        """
        # Try to split by last dot to separate IP from port
        # Format: ip.port or just ip
        parts = field.rsplit('.', 1)
        
        if len(parts) == 2:
            ip_str, port_str = parts
            # Check if port_str is a valid port number
            try:
                port = int(port_str)
                if 0 <= port <= 65535:
                    # Validate IP address
                    try:
                        ip_address(ip_str)
                        return ip_str, port
                    except ValueError:
                        pass
            except ValueError:
                pass
        
        # No port found, treat entire field as IP
        try:
            ip_address(field)
            return field, None
        except ValueError:
            return None, None
    
    def _detect_protocol(self, line: str) -> str:
        """
        Detect protocol from tcpdump line.
        
        Args:
            line: Tcpdump output line
            
        Returns:
            Protocol name: UDP, TCP, ICMP, QUIC, or UNKNOWN
        """
        # Check protocols in order of specificity
        if self.PROTOCOL_PATTERNS['ICMP'].search(line):
            return 'ICMP'
        elif self.PROTOCOL_PATTERNS['UDP'].search(line):
            return 'UDP'
        elif self.PROTOCOL_PATTERNS['QUIC'].search(line):
            return 'QUIC'
        elif self.PROTOCOL_PATTERNS['TCP'].search(line):
            return 'TCP'
        else:
            return 'UNKNOWN'
    
    def _extract_length(self, line: str) -> Optional[int]:
        """
        Extract packet length from tcpdump line.
        
        Args:
            line: Tcpdump output line
            
        Returns:
            Packet length in bytes, or None if not found
        """
        match = self.LENGTH_PATTERN.search(line)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return None

################################################################################
# ConnectionAnalyzer Class
################################################################################

class ConnectionAnalyzer:
    """Analyze and aggregate network connection data."""
    
    def __init__(self):
        """Initialize analyzer with empty counters."""
        self.src_ip_counts: Counter = Counter()
        self.dst_ip_counts: Counter = Counter()
        self.connection_counts: Dict[Tuple[str, str, str, Optional[int], Optional[int]], int] = defaultdict(int)
        self.protocol_counts: Counter = Counter()
        self.src_port_counts: Counter = Counter()
        self.dst_port_counts: Counter = Counter()
        self.total_packets = 0
        self.unique_src_ips: Set[str] = set()
        self.unique_dst_ips: Set[str] = set()
    
    def add_connection(self, parsed_data: Dict[str, Any]) -> None:
        """
        Add a connection to the analysis.
        
        Args:
            parsed_data: Dictionary from TcpdumpParser.parse_line()
        """
        if not parsed_data:
            return
        
        src_ip = parsed_data.get('src_ip')
        dst_ip = parsed_data.get('dst_ip')
        protocol = parsed_data.get('protocol', 'UNKNOWN')
        src_port = parsed_data.get('src_port')
        dst_port = parsed_data.get('dst_port')
        
        if not src_ip or not dst_ip:
            return
        
        # Update counters
        self.src_ip_counts[src_ip] += 1
        self.dst_ip_counts[dst_ip] += 1
        self.protocol_counts[protocol] += 1
        
        # Update unique IP sets
        self.unique_src_ips.add(src_ip)
        self.unique_dst_ips.add(dst_ip)
        
        # Update port counts (only if ports exist)
        if src_port is not None:
            self.src_port_counts[src_port] += 1
        if dst_port is not None:
            self.dst_port_counts[dst_port] += 1
        
        # Update connection pair counts
        connection_key = (src_ip, dst_ip, protocol, src_port, dst_port)
        self.connection_counts[connection_key] += 1
        
        self.total_packets += 1
    
    def get_top_ips(self, n: int, direction: str = 'source') -> List[Tuple[str, int]]:
        """
        Get top N IP addresses by packet count.
        
        Args:
            n: Number of top IPs to return
            direction: 'source' or 'destination'
            
        Returns:
            List of (ip, count) tuples sorted by count descending
        """
        counter = self.src_ip_counts if direction == 'source' else self.dst_ip_counts
        return counter.most_common(n)
    
    def get_connection_counts(self) -> Dict[Tuple[str, str, str, Optional[int], Optional[int]], int]:
        """
        Get connection pair counts.
        
        Returns:
            Dictionary mapping (src_ip, dst_ip, protocol, src_port, dst_port) to count
        """
        return dict(self.connection_counts)
    
    def get_protocol_counts(self) -> Counter:
        """
        Get protocol distribution.
        
        Returns:
            Counter of protocol counts
        """
        return self.protocol_counts
    
    def get_port_counts(self, direction: str = 'source') -> Counter:
        """
        Get port usage counts.
        
        Args:
            direction: 'source' or 'destination'
            
        Returns:
            Counter of port counts
        """
        return self.src_port_counts if direction == 'source' else self.dst_port_counts

################################################################################
# Utility Functions
################################################################################

def is_private_ip(ip: str) -> bool:
    """
    Check if an IP address is private/local.
    
    Args:
        ip: IP address string
        
    Returns:
        True if IP is private (10.x, 172.16-31.x, 192.168.x, 127.x, 169.254.x)
    """
    try:
        addr = ip_address(ip)
        return addr.is_private or addr.is_loopback or addr.is_link_local
    except ValueError:
        return False

def find_tcpdump_files(directory: Path) -> List[Path]:
    """
    Find tcpdump files in a directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of Path objects, sorted by modification time (newest first)
    """
    if not directory.exists():
        return []
    
    pattern = 'record-tcpdump_*.txt'
    files = list(directory.glob(pattern))
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files

################################################################################
# File Processing
################################################################################

def process_file(
    file_path: Path,
    analyzer: ConnectionAnalyzer,
    parser: TcpdumpParser,
    filters: Dict[str, Any],
    verbose: bool = False
) -> int:
    """
    Process a tcpdump file and add data to analyzer.
    
    Args:
        file_path: Path to tcpdump file
        analyzer: ConnectionAnalyzer instance
        parser: TcpdumpParser instance
        filters: Dictionary of filter criteria
        verbose: Whether to show verbose output
        
    Returns:
        Number of packets processed
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    packets_processed = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                parsed = parser.parse_line(line)
                
                if not parsed:
                    continue
                
                # Apply filters
                if not _matches_filters(parsed, filters):
                    continue
                
                analyzer.add_connection(parsed)
                packets_processed += 1
                
                if verbose and packets_processed % 10000 == 0:
                    print(f"Processed {packets_processed:,} packets...", file=sys.stderr)
    
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")
    
    return packets_processed

def _matches_filters(parsed: Dict[str, Any], filters: Dict[str, Any]) -> bool:
    """
    Check if parsed data matches filter criteria.
    
    Args:
        parsed: Parsed packet data
        filters: Filter criteria dictionary
        
    Returns:
        True if packet matches all filters
    """
    # Protocol filter
    if filters.get('protocol') and filters['protocol'] != 'all':
        if parsed.get('protocol', '').upper() != filters['protocol'].upper():
            return False
    
    # IP filter
    if filters.get('ip'):
        filter_ip = filters['ip']
        if parsed.get('src_ip') != filter_ip and parsed.get('dst_ip') != filter_ip:
            return False
    
    # Port filter
    if filters.get('port') is not None:
        filter_port = filters['port']
        if parsed.get('src_port') != filter_port and parsed.get('dst_port') != filter_port:
            return False
    
    # Local IP exclusion
    if filters.get('exclude_local'):
        if is_private_ip(parsed.get('src_ip', '')) or is_private_ip(parsed.get('dst_ip', '')):
            return False
    
    return True

################################################################################
# Output Formatting
################################################################################

def generate_summary(analyzer: ConnectionAnalyzer, file_info: Dict[str, Any]) -> str:
    """
    Generate summary statistics report.
    
    Args:
        analyzer: ConnectionAnalyzer instance
        file_info: Dictionary with file information
        
    Returns:
        Formatted summary string
    """
    lines = []
    lines.append("TCPDump Analysis Summary")
    lines.append("=" * len("TCPDump Analysis Summary"))
    
    if file_info.get('files'):
        files_str = ', '.join(str(f) for f in file_info['files'])
        lines.append(f"Files: {files_str}")
    
    lines.append(f"Total Packets: {analyzer.total_packets:,}")
    lines.append(f"Unique Source IPs: {len(analyzer.unique_src_ips)}")
    lines.append(f"Unique Destination IPs: {len(analyzer.unique_dst_ips)}")
    
    # Protocol breakdown
    protocol_counts = analyzer.get_protocol_counts()
    if protocol_counts:
        protocol_str = ", ".join(
            f"{proto} ({count:,})" for proto, count in protocol_counts.most_common()
        )
        lines.append(f"Protocols: {protocol_str}")
    
    # Top source IPs
    top_src = analyzer.get_top_ips(10, 'source')
    if top_src:
        lines.append("\nTop 10 Source IPs:")
        for ip, count in top_src:
            lines.append(f"  {ip:20s} {count:,} packets")
    
    # Top destination IPs
    top_dst = analyzer.get_top_ips(10, 'destination')
    if top_dst:
        lines.append("\nTop 10 Destination IPs:")
        for ip, count in top_dst:
            lines.append(f"  {ip:20s} {count:,} packets")
    
    return "\n".join(lines)

def generate_top_ips_report(analyzer: ConnectionAnalyzer, n: int, direction: str = 'source') -> str:
    """
    Generate top N IPs report.
    
    Args:
        analyzer: ConnectionAnalyzer instance
        n: Number of IPs to show
        direction: 'source' or 'destination'
        
    Returns:
        Formatted report string
    """
    lines = []
    direction_label = "Source" if direction == 'source' else "Destination"
    lines.append(f"Top {n} {direction_label} IP Addresses")
    lines.append("=" * len(lines[0]))
    
    top_ips = analyzer.get_top_ips(n, direction)
    if not top_ips:
        lines.append("No IP addresses found.")
    else:
        for ip, count in top_ips:
            lines.append(f"  {ip:20s} {count:,} packets")
    
    return "\n".join(lines)

def generate_connections_report(analyzer: ConnectionAnalyzer, n: int = 20) -> str:
    """
    Generate connection pairs report.
    
    Args:
        analyzer: ConnectionAnalyzer instance
        n: Number of top connections to show
        
    Returns:
        Formatted report string
    """
    lines = []
    lines.append("Connection Pairs (Source -> Destination)")
    lines.append("=" * len(lines[0]))
    
    connections = analyzer.get_connection_counts()
    if not connections:
        lines.append("No connections found.")
    else:
        # Sort by count descending
        sorted_connections = sorted(connections.items(), key=lambda x: x[1], reverse=True)
        
        for (src_ip, dst_ip, protocol, src_port, dst_port), count in sorted_connections[:n]:
            src_str = f"{src_ip}:{src_port}" if src_port is not None else src_ip
            dst_str = f"{dst_ip}:{dst_port}" if dst_port is not None else dst_ip
            lines.append(f"  {src_str} -> {dst_str} ({protocol}) - {count:,} packets")
    
    return "\n".join(lines)

def generate_ports_report(analyzer: ConnectionAnalyzer, n: int = 20, direction: str = 'source') -> str:
    """
    Generate port usage report.
    
    Args:
        analyzer: ConnectionAnalyzer instance
        n: Number of top ports to show
        direction: 'source' or 'destination'
        
    Returns:
        Formatted report string
    """
    lines = []
    direction_label = "Source" if direction == 'source' else "Destination"
    lines.append(f"{direction_label} Port Usage Analysis")
    lines.append("=" * len(lines[0]))
    
    port_counts = analyzer.get_port_counts(direction)
    if not port_counts:
        lines.append(f"No {direction_label.lower()} ports found.")
    else:
        top_ports = port_counts.most_common(n)
        for port, count in top_ports:
            port_name = WELL_KNOWN_PORTS.get(port, "")
            port_str = f"{port} ({port_name})" if port_name else str(port)
            lines.append(f"  {port_str:20s} {count:,} packets")
    
    return "\n".join(lines)

def generate_all_ips_report(analyzer: ConnectionAnalyzer) -> str:
    """
    Generate list of all unique IP addresses.
    
    Args:
        analyzer: ConnectionAnalyzer instance
        
    Returns:
        Formatted report string
    """
    lines = []
    lines.append("Unique IP Addresses")
    lines.append("=" * len(lines[0]))
    
    src_ips = sorted(analyzer.unique_src_ips)
    dst_ips = sorted(analyzer.unique_dst_ips)
    
    lines.append(f"\nSource IPs ({len(src_ips)}):")
    for ip in src_ips:
        lines.append(f"  {ip}")
    
    lines.append(f"\nDestination IPs ({len(dst_ips)}):")
    for ip in dst_ips:
        lines.append(f"  {ip}")
    
    return "\n".join(lines)

def output_csv(analyzer: ConnectionAnalyzer, output_format: str) -> str:
    """
    Generate CSV output.
    
    Args:
        analyzer: ConnectionAnalyzer instance
        output_format: Type of CSV output ('ips', 'connections', 'ports')
        
    Returns:
        CSV formatted string
    """
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    
    if output_format == 'ips':
        writer.writerow(['type', 'ip', 'count'])
        for ip, count in analyzer.src_ip_counts.items():
            writer.writerow(['source', ip, count])
        for ip, count in analyzer.dst_ip_counts.items():
            writer.writerow(['destination', ip, count])
    
    elif output_format == 'connections':
        writer.writerow(['src_ip', 'dst_ip', 'src_port', 'dst_port', 'protocol', 'count'])
        for (src_ip, dst_ip, protocol, src_port, dst_port), count in analyzer.get_connection_counts().items():
            writer.writerow([src_ip, dst_ip, src_port or '', dst_port or '', protocol, count])
    
    elif output_format == 'ports':
        writer.writerow(['type', 'port', 'count'])
        for port, count in analyzer.src_port_counts.items():
            writer.writerow(['source', port, count])
        for port, count in analyzer.dst_port_counts.items():
            writer.writerow(['destination', port, count])
    
    return output.getvalue()

################################################################################
# Main Function
################################################################################

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Analyze tcpdump output files to extract IP addresses and connection statistics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze latest tcpdump file in log/ directory
  %(prog)s

  # Analyze specific file
  %(prog)s log/record-tcpdump_2025-12-07_120000.txt

  # Show top 20 IPs only
  %(prog)s -o ips -t 20

  # Filter TCP only, exclude local IPs
  %(prog)s -p tcp -l

  # Filter by specific IP address
  %(prog)s -i 8.8.8.8

  # Output as CSV
  %(prog)s -c -o connections
        """
    )
    
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Quiet mode (output as little as possible)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output (show detailed processing information)')
    parser.add_argument('-f', '--file', type=str, action='append', dest='files',
                       help='Input tcpdump file (can be specified multiple times)')
    parser.add_argument('-o', '--output-format', type=str, default='all',
                       choices=['summary', 'ips', 'connections', 'ports', 'all'],
                       help='Output format (default: all)')
    parser.add_argument('-p', '--protocol', type=str, default='all',
                       choices=['tcp', 'udp', 'icmp', 'quic', 'all'],
                       help='Filter by protocol (default: all)')
    parser.add_argument('-i', '--ip', type=str,
                       help='Filter by IP address (show connections involving this IP)')
    parser.add_argument('-P', '--port', type=int,
                       help='Filter by port number')
    parser.add_argument('-t', '--top', type=int, default=10,
                       help='Show top N IPs/connections (default: 10)')
    parser.add_argument('-l', '--exclude-local', action='store_true',
                       help='Exclude local/private IP addresses')
    parser.add_argument('-c', '--csv', action='store_true',
                       help='Output as CSV format')
    parser.add_argument('-d', '--directory', type=str,
                       help='Directory containing tcpdump files (auto-finds latest if no file specified)')
    parser.add_argument('tcpdump_files', nargs='*',
                       help='Tcpdump output files to analyze')
    
    args = parser.parse_args()
    
    # Determine input files
    input_files: List[Path] = []
    
    # Get script directory for relative paths
    script_dir = Path(__file__).parent.resolve()
    default_log_dir = script_dir / 'log'
    
    if args.files:
        for f in args.files:
            file_path = Path(f)
            if not file_path.is_absolute():
                file_path = (script_dir / file_path).resolve()
            input_files.append(file_path)
    
    if args.tcpdump_files:
        for f in args.tcpdump_files:
            file_path = Path(f)
            if not file_path.is_absolute():
                file_path = (script_dir / file_path).resolve()
            input_files.append(file_path)
    
    # If no files specified, try to find latest in directory
    if not input_files:
        search_dir = default_log_dir
        if args.directory:
            search_dir = Path(args.directory)
            if not search_dir.is_absolute():
                search_dir = (script_dir / search_dir).resolve()
        
        if search_dir.exists():
            found_files = find_tcpdump_files(search_dir)
            if found_files:
                input_files = [found_files[0]]  # Use latest
                if not args.quiet:
                    print(f"Using latest file: {input_files[0]}", file=sys.stderr)
            else:
                print(f"Error: No tcpdump files found in {search_dir}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Error: Directory not found: {search_dir}", file=sys.stderr)
            sys.exit(1)
    
    # Validate files exist
    for file_path in input_files:
        if not file_path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
    
    # Setup filters
    filters = {
        'protocol': args.protocol,
        'ip': args.ip,
        'port': args.port,
        'exclude_local': args.exclude_local
    }
    
    # Initialize components
    parser_obj = TcpdumpParser()
    analyzer = ConnectionAnalyzer()
    
    # Process files
    total_packets = 0
    for file_path in input_files:
        try:
            packets = process_file(file_path, analyzer, parser_obj, filters, args.verbose)
            total_packets += packets
            if args.verbose:
                print(f"Processed {packets:,} packets from {file_path}", file=sys.stderr)
        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)
            sys.exit(1)
    
    if total_packets == 0:
        if not args.quiet:
            print("No packets found matching criteria.", file=sys.stderr)
        sys.exit(0)
    
    # Generate output
    file_info = {'files': input_files}
    
    if args.csv:
        # CSV output
        csv_format = args.output_format if args.output_format != 'all' else 'connections'
        print(output_csv(analyzer, csv_format))
    else:
        # Text output
        if args.output_format in ('summary', 'all'):
            print(generate_summary(analyzer, file_info))
            if args.output_format == 'all':
                print()
        
        if args.output_format in ('ips', 'all'):
            print(generate_all_ips_report(analyzer))
            if args.output_format == 'all':
                print()
        
        if args.output_format == 'connections' or (args.output_format == 'all' and not args.quiet):
            print(generate_connections_report(analyzer, args.top))
            if args.output_format == 'all':
                print()
        
        if args.output_format == 'ports' or (args.output_format == 'all' and not args.quiet):
            print(generate_ports_report(analyzer, args.top, 'source'))
            if args.output_format == 'all':
                print()
            print(generate_ports_report(analyzer, args.top, 'destination'))

if __name__ == "__main__":
    main()
