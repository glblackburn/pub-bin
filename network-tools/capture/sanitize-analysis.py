#!/usr/bin/env python3
"""
Sanitize analyze-tcpdump.py output for public publication.

Masks sensitive information (private IPs, file paths) while preserving
high-level context and statistics.
"""

import sys
import re
from pathlib import Path
from ipaddress import ip_address, AddressValueError
from collections import OrderedDict


class AnalysisSanitizer:
    """Sanitize tcpdump analysis output."""

    def __init__(self, mask_public_ips=False, mask_ports=False):
        """
        Initialize sanitizer.

        Args:
            mask_public_ips: If True, mask public IPs too (default: False)
            mask_ports: If True, mask non-standard ports (default: False)
        """
        self.mask_public_ips = mask_public_ips
        self.mask_ports = mask_ports
        
        # IP mapping: original -> placeholder
        self.ip_map = OrderedDict()
        self.private_counters = {
            'lan': 1,      # 192.168.x.x
            'subnet': 1,   # 172.16-31.x.x
            'net': 1,      # 10.x.x.x
            'multicast': 1, # 224.x.x.x
            'public': 1,   # Public IPs (if masking)
        }
        
        # Port mapping: original -> placeholder
        self.port_map = OrderedDict()
        self.port_counter = 1
        
        # Standard ports to keep unmasked
        self.standard_ports = {80, 443, 53, 22, 25, 110, 143, 993, 995, 21, 23, 3389}

    def _is_private_ip(self, ip_str: str) -> bool:
        """Check if IP is private/local."""
        try:
            addr = ip_address(ip_str)
            return addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_multicast
        except (AddressValueError, ValueError):
            return False

    def _get_ip_placeholder(self, ip_str: str) -> str:
        """Get or create placeholder for IP address."""
        if ip_str in self.ip_map:
            return self.ip_map[ip_str]
        
        try:
            addr = ip_address(ip_str)
            
            # Private IPs
            if addr.is_private:
                if ip_str.startswith('192.168.'):
                    placeholder = f"PRIVATE_LAN_{self.private_counters['lan']}"
                    self.private_counters['lan'] += 1
                elif ip_str.startswith('172.') and 16 <= int(ip_str.split('.')[1]) <= 31:
                    placeholder = f"PRIVATE_SUBNET_{self.private_counters['subnet']}"
                    self.private_counters['subnet'] += 1
                elif ip_str.startswith('10.'):
                    placeholder = f"PRIVATE_NET_{self.private_counters['net']}"
                    self.private_counters['net'] += 1
                else:
                    placeholder = f"PRIVATE_{self.private_counters['net']}"
                    self.private_counters['net'] += 1
            # Multicast
            elif addr.is_multicast:
                placeholder = f"MULTICAST_{self.private_counters['multicast']}"
                self.private_counters['multicast'] += 1
            # Broadcast
            elif ip_str == '255.255.255.255':
                placeholder = "BROADCAST"
            # Public IPs (if masking enabled)
            elif self.mask_public_ips:
                placeholder = f"PUBLIC_IP_{self.private_counters['public']}"
                self.private_counters['public'] += 1
            else:
                # Keep public IPs as-is
                placeholder = ip_str
                
            self.ip_map[ip_str] = placeholder
            return placeholder
            
        except (AddressValueError, ValueError):
            # Invalid IP, return as-is
            return ip_str

    def _get_port_placeholder(self, port_str: str) -> str:
        """Get or create placeholder for port number."""
        if not self.mask_ports:
            return port_str
        
        try:
            port = int(port_str)
            if port in self.standard_ports:
                return port_str  # Keep standard ports
            
            if port_str in self.port_map:
                return self.port_map[port_str]
            
            placeholder = f"PORT_{port}"
            self.port_map[port_str] = placeholder
            return placeholder
        except ValueError:
            return port_str

    def _sanitize_file_path(self, line: str) -> str:
        """Sanitize file paths in line."""
        # Match file paths like /Users/... or ./log/...
        pattern = r'(Files:\s+)([^\s,]+)'
        
        def replace_path(match):
            prefix = match.group(1)
            path = match.group(2)
            # Extract filename if it's a tcpdump file
            filename = Path(path).name
            if 'tcpdump' in filename.lower():
                return f"{prefix}log/{filename}"
            else:
                return f"{prefix}example-tcpdump-capture.txt"
        
        return re.sub(pattern, replace_path, line)

    def _sanitize_ip_addresses(self, line: str) -> str:
        """Sanitize IP addresses in line."""
        # Match IPv4 addresses
        ip_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
        
        def replace_ip(match):
            ip_str = match.group(1)
            return self._get_ip_placeholder(ip_str)
        
        return re.sub(ip_pattern, replace_ip, line)

    def _sanitize_ports(self, line: str) -> str:
        """Sanitize port numbers in line."""
        if not self.mask_ports:
            return line
        
        # Match port patterns like :443, :58564, etc.
        # But avoid matching IP addresses
        port_pattern = r':(\d{1,5})(?:\s|$|\)|,|-)'
        
        def replace_port(match):
            port_str = match.group(1)
            placeholder = self._get_port_placeholder(port_str)
            return f":{placeholder}"
        
        return re.sub(port_pattern, replace_port, line)

    def sanitize(self, content: str) -> str:
        """Sanitize entire content."""
        lines = content.split('\n')
        sanitized_lines = []
        
        for line in lines:
            # Sanitize file paths first
            line = self._sanitize_file_path(line)
            
            # Sanitize IP addresses
            line = self._sanitize_ip_addresses(line)
            
            # Sanitize ports (if enabled)
            line = self._sanitize_ports(line)
            
            sanitized_lines.append(line)
        
        return '\n'.join(sanitized_lines)

    def add_header_comment(self, content: str) -> str:
        """Add header comment explaining sanitization."""
        header = """# Sanitized Analysis Output
# ============================
# This output has been sanitized for public publication:
# - Private IPs (192.168.x.x, 172.16-31.x.x, 10.x.x.x) replaced with PRIVATE_* placeholders
# - Multicast addresses (224.x.x.x) replaced with MULTICAST_* placeholders
# - Broadcast address (255.255.255.255) replaced with BROADCAST
"""
        if self.mask_public_ips:
            header += "# - Public IPs replaced with PUBLIC_IP_* placeholders\n"
        if self.mask_ports:
            header += "# - Non-standard ports replaced with PORT_* placeholders\n"
        header += "# - File paths anonymized\n"
        header += "# - All statistics and relationships preserved\n"
        header += "\n"
        
        return header + content


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Sanitize analyze-tcpdump.py output for public publication'
    )
    parser.add_argument(
        'input_file',
        type=str,
        help='Input analysis file to sanitize'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output file (default: input_file with .sanitized suffix)'
    )
    parser.add_argument(
        '--mask-public',
        action='store_true',
        help='Also mask public IP addresses'
    )
    parser.add_argument(
        '--mask-ports',
        action='store_true',
        help='Mask non-standard port numbers'
    )
    
    args = parser.parse_args()
    
    # Read input
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    content = input_path.read_text()
    
    # Sanitize
    sanitizer = AnalysisSanitizer(
        mask_public_ips=args.mask_public,
        mask_ports=args.mask_ports
    )
    sanitized = sanitizer.sanitize(content)
    sanitized = sanitizer.add_header_comment(sanitized)
    
    # Write output
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.parent / f"{input_path.stem}.sanitized{input_path.suffix}"
    
    output_path.write_text(sanitized)
    print(f"Sanitized output written to: {output_path}")
    print(f"  - {len(sanitizer.ip_map)} unique IPs mapped")
    if args.mask_ports:
        print(f"  - {len(sanitizer.port_map)} unique ports mapped")


if __name__ == '__main__':
    main()
