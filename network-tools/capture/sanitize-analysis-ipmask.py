#!/usr/bin/env python3
"""
Sanitize analyze-tcpdump.py output using IP-like masking.

Masks IPs by replacing octets with letters (a-z) that map to the original
values, maintaining IP-like appearance while anonymizing.
"""

import sys
import re
from pathlib import Path
from ipaddress import ip_address, AddressValueError
from collections import OrderedDict
from typing import Optional
import random
import string


class IPMaskSanitizer:
    """Sanitize using IP-like masking with random letter substitution."""

    def __init__(self, seed=None, mask_public_ips=False):
        """
        Initialize sanitizer.

        Args:
            seed: Random seed for consistent mapping within a run (default: None for new random each run)
            mask_public_ips: If True, also mask public IPs (default: False)
        """
        self.mask_public_ips = mask_public_ips
        self.seed = seed
        
        # IP mapping: original -> masked
        self.ip_map = OrderedDict()
        
        # Separate mappings for 2nd and 3rd octets
        # Octet value -> random two-letter mapping (uppercase, non-hex)
        self.octet2_map = OrderedDict()  # For 2nd octet
        self.octet3_map = OrderedDict()  # For 3rd octet
        
        # Generate pool of valid letters (G-Z, uppercase, excluding hex A-F)
        # A-F are hex digits (0-15), so we exclude them
        self.valid_letters = [c for c in string.ascii_uppercase if c not in 'ABCDEF']
        # G-Z gives us 20 letters: G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z
        # That's 20 * 20 = 400 possible combinations, enough for 0-255 (256 values)
        
        # Track used letter combinations to avoid duplicates (separate for each position)
        self.used_combinations_octet2 = set()
        self.used_combinations_octet3 = set()
        
        # Initialize random with seed if provided, otherwise use system randomness
        if seed is not None:
            random.seed(seed)
        else:
            # Use current time or system randomness for different runs
            random.seed()

    def _get_letter_for_octet(self, octet_value: int, position: int) -> str:
        """
        Map octet value (0-255) to random two-letter combination.
        
        Always uses two uppercase letters (G-Z, excluding hex A-F).
        Same octet value always maps to same letter combination within a run.
        Different runs produce different mappings.
        Different positions (2nd vs 3rd octet) use independent mappings.
        
        Args:
            octet_value: The octet value to map (0-255)
            position: 2 for 2nd octet, 3 for 3rd octet
        """
        # Select the appropriate map and used combinations set
        if position == 2:
            octet_map = self.octet2_map
            used_combinations = self.used_combinations_octet2
        elif position == 3:
            octet_map = self.octet3_map
            used_combinations = self.used_combinations_octet3
        else:
            raise ValueError(f"Position must be 2 or 3, got {position}")
        
        if octet_value in octet_map:
            return octet_map[octet_value]
        
        # Generate random two-letter combination that hasn't been used for this position
        max_attempts = 1000  # Safety limit
        attempts = 0
        
        while attempts < max_attempts:
            first_letter = random.choice(self.valid_letters)
            second_letter = random.choice(self.valid_letters)
            letter_combo = first_letter + second_letter
            
            if letter_combo not in used_combinations:
                used_combinations.add(letter_combo)
                octet_map[octet_value] = letter_combo
                return letter_combo
            
            attempts += 1
        
        # Fallback if we somehow run out (shouldn't happen with 400 combinations for 256 values)
        # Use a deterministic fallback based on value and position
        first_idx = ((octet_value * 7) + position) % len(self.valid_letters)
        second_idx = ((octet_value * 11) + position) % len(self.valid_letters)
        letter_combo = self.valid_letters[first_idx] + self.valid_letters[second_idx]
        octet_map[octet_value] = letter_combo
        return letter_combo

    def _get_randomized_octet(self, octet_value: int) -> int:
        """Get randomized but consistent octet value."""
        if octet_value in self.random_mapping:
            return self.random_mapping[octet_value]
        
        # Generate random value in same range
        if octet_value < 10:
            # Private network first octet (10, 172, 192)
            new_value = random.choice([10, 172, 192])
        elif octet_value < 172:
            # Could be 10.x or other private ranges
            new_value = random.randint(10, 172)
        elif octet_value < 192:
            # 172.16-31.x.x range
            new_value = random.randint(172, 192)
        else:
            # 192.168.x.x or 192.169-255.x.x
            new_value = random.randint(192, 255)
        
        self.random_mapping[octet_value] = new_value
        return new_value

    def _mask_ip_with_letters(self, ip_str: str, use_randomization: bool = False) -> str:
        """
        Mask IP by replacing 2nd and 3rd octets with random two-letter combinations.
        
        Strategy:
        - For private IPs: Replace the 2nd and 3rd octets with random two-letter mappings
        - Always uses two uppercase letters (G-Z, excluding hex A-F)
        - Maintains IP-like appearance
        - Same original IP always maps to same masked IP within a run
        - First and last octets remain unchanged
        """
        if ip_str in self.ip_map:
            return self.ip_map[ip_str]
        
        try:
            addr = ip_address(ip_str)
            parts = ip_str.split('.')
            
            # Replace 2nd and 3rd octets (indices 1 and 2) with random two-letter combinations
            # For 192.168.42.7 -> 192.XX.YY.7 (where XX maps to 168 in 2nd position, YY maps to 42 in 3rd position)
            # Note: Same value in 2nd vs 3rd position will map to different letters
            if len(parts) == 4:
                octet2_value = int(parts[1])  # 2nd octet
                octet3_value = int(parts[2])  # 3rd octet
                letter_combo2 = self._get_letter_for_octet(octet2_value, position=2)
                letter_combo3 = self._get_letter_for_octet(octet3_value, position=3)
                masked_parts = parts.copy()
                masked_parts[1] = letter_combo2  # Replace 2nd octet
                masked_parts[2] = letter_combo3  # Replace 3rd octet
                masked_ip = '.'.join(masked_parts)
            else:
                masked_ip = ip_str
                    
            self.ip_map[ip_str] = masked_ip
            return masked_ip
            
        except (AddressValueError, ValueError, IndexError):
            # Invalid IP, return as-is
            return ip_str

    def _should_mask_ip(self, ip_str: str) -> bool:
        """Determine if IP should be masked."""
        try:
            addr = ip_address(ip_str)
            if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_multicast:
                return True
            if ip_str == '255.255.255.255':
                return True
            if self.mask_public_ips:
                return True
            return False
        except (AddressValueError, ValueError):
            return False

    def _sanitize_file_path(self, line: str) -> str:
        """Sanitize file paths in line."""
        pattern = r'(Files:\s+)([^\s,]+)'
        
        def replace_path(match):
            prefix = match.group(1)
            path = match.group(2)
            filename = Path(path).name
            if 'tcpdump' in filename.lower():
                return f"{prefix}log/{filename}"
            else:
                return f"{prefix}example-tcpdump-capture.txt"
        
        return re.sub(pattern, replace_path, line)

    def _sanitize_ip_addresses(self, line: str, use_randomization: bool = False) -> str:
        """Sanitize IP addresses in line."""
        ip_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
        
        def replace_ip(match):
            ip_str = match.group(1)
            if self._should_mask_ip(ip_str):
                return self._mask_ip_with_letters(ip_str, use_randomization)
            return ip_str
        
        return re.sub(ip_pattern, replace_ip, line)

    def sanitize(self, content: str, use_randomization: bool = False) -> str:
        """Sanitize entire content."""
        lines = content.split('\n')
        sanitized_lines = []
        
        for line in lines:
            line = self._sanitize_file_path(line)
            line = self._sanitize_ip_addresses(line, use_randomization)
            sanitized_lines.append(line)
        
        return '\n'.join(sanitized_lines)

    def generate_mapping_table(self) -> str:
        """Generate a mapping table showing original -> masked IPs."""
        lines = ["IP Address Mapping Table", "=" * 50, ""]
        
        # Group by type
        private_ips = []
        public_ips = []
        other_ips = []
        
        for orig_ip, masked_ip in self.ip_map.items():
            try:
                addr = ip_address(orig_ip)
                if addr.is_private:
                    private_ips.append((orig_ip, masked_ip))
                elif addr.is_multicast:
                    other_ips.append((orig_ip, masked_ip))
                elif orig_ip == '255.255.255.255':
                    other_ips.append((orig_ip, masked_ip))
                elif self.mask_public_ips:
                    public_ips.append((orig_ip, masked_ip))
            except:
                pass
        
        if private_ips:
            lines.append("Private IPs:")
            for orig, masked in sorted(private_ips):
                lines.append(f"  {orig:20s} -> {masked}")
            lines.append("")
        
        if public_ips:
            lines.append("Public IPs:")
            for orig, masked in sorted(public_ips):
                lines.append(f"  {orig:20s} -> {masked}")
            lines.append("")
        
        if other_ips:
            lines.append("Other (Multicast/Broadcast):")
            for orig, masked in sorted(other_ips):
                lines.append(f"  {orig:20s} -> {masked}")
            lines.append("")
        
        lines.append(f"Total IPs mapped: {len(self.ip_map)}")
        lines.append(f"2nd octet mappings: {len(self.octet2_map)} unique values")
        lines.append(f"3rd octet mappings: {len(self.octet3_map)} unique values")
        
        return '\n'.join(lines)

    def add_header_comment(self, content: str, use_randomization: bool = False) -> str:
        """Add header comment explaining sanitization."""
        header = """# Sanitized Analysis Output (IP-like Masking)
# ============================================================
# This output has been sanitized for public publication:
# - Private IPs masked by replacing 2nd and 3rd octets with random two-letter combinations (G-Z, uppercase)
# - First and last octets remain unchanged
# - Letters exclude hex values (A-F) to avoid confusion
# - Same original IP always maps to same masked IP within this run
# - Different runs will produce different mappings (randomized)
# - IP format preserved (looks like IP address)
"""
        if self.mask_public_ips:
            header += "# - Public IPs also masked\n"
        header += "# - File paths anonymized\n"
        header += "# - All statistics and relationships preserved\n"
        header += "\n"
        
        return header + content


def find_latest_analysis_file(directory: Path) -> Optional[Path]:
    """
    Find the latest analysis file in a directory.
    
    Looks for files matching the pattern '*_analysis.txt' created by
    analyze-tcpdump.py.
    
    Args:
        directory: Directory to search
        
    Returns:
        Path to latest analysis file, or None if not found
    """
    if not directory.exists():
        return None
    
    pattern = '*_analysis.txt'
    files = list(directory.glob(pattern))
    if not files:
        return None
    
    # Sort by modification time (newest first)
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Sanitize analyze-tcpdump.py output using IP-like masking'
    )
    parser.add_argument(
        'input_file',
        type=str,
        nargs='?',
        help='Input analysis file to sanitize (default: find latest in log directory)'
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
        '--seed',
        type=int,
        help='Random seed for consistent mapping (default: random each run)'
    )
    parser.add_argument(
        '--show-mapping',
        action='store_true',
        help='Show IP mapping table'
    )
    
    args = parser.parse_args()
    
    # Get script directory for log path
    script_dir = Path(__file__).parent.resolve()
    log_dir = script_dir / 'log'
    
    # Determine input file
    if args.input_file:
        # Use provided input file
        input_path = Path(args.input_file)
        if not input_path.is_absolute():
            input_path = (script_dir / input_path).resolve()
    else:
        # Find latest analysis file in log directory
        if not log_dir.exists():
            print(f"Error: Log directory not found: {log_dir}", file=sys.stderr)
            sys.exit(1)
        
        input_path = find_latest_analysis_file(log_dir)
        if not input_path:
            print(f"Error: No analysis files found in {log_dir}", file=sys.stderr)
            print("  (Looking for files matching pattern: *_analysis.txt)", file=sys.stderr)
            sys.exit(1)
        
        print(f"Using latest analysis file: {input_path}", file=sys.stderr)
    
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    content = input_path.read_text()
    
    # Sanitize
    sanitizer = IPMaskSanitizer(
        seed=args.seed,
        mask_public_ips=args.mask_public
    )
    sanitized = sanitizer.sanitize(content, use_randomization=False)
    sanitized = sanitizer.add_header_comment(sanitized, use_randomization=False)
    
    # Determine output file path
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = (script_dir / output_path).resolve()
    else:
        # Save to log directory with .ipmasked suffix
        log_dir.mkdir(exist_ok=True)
        # Generate output filename based on input filename
        if '_analysis' in input_path.stem:
            # If input is an analysis file, add .ipmasked before extension
            # record-tcpdump_2025-12-12_082910_analysis.txt -> record-tcpdump_2025-12-12_082910_analysis.ipmasked.txt
            output_name = f"{input_path.stem}.ipmasked{input_path.suffix}"
        else:
            # Otherwise, create analysis.ipmasked file
            output_name = f"{input_path.stem}_analysis.ipmasked{input_path.suffix}"
        output_path = log_dir / output_name
    
    # Display output to stdout
    print(sanitized)
    
    # Write output to file
    output_path.write_text(sanitized)
    
    # Show mapping table if requested (to stdout so it can be captured/piped)
    if args.show_mapping:
        print(sanitizer.generate_mapping_table())
        print()
    
    # Show output file name at the end (to stderr so it doesn't interfere with output)
    print(f"Sanitized output written to: {output_path}", file=sys.stderr)
    print(f"  - {len(sanitizer.ip_map)} unique IPs mapped", file=sys.stderr)


if __name__ == '__main__':
    main()
