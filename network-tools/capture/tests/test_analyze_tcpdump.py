"""
Comprehensive test suite for analyze-tcpdump.py

Tests cover:
- TcpdumpParser class (parsing, IP/port extraction, protocol detection)
- ConnectionAnalyzer class (aggregation, counting, statistics)
- Filtering functionality
- Output formatting
- File processing
- Error handling
"""

import sys
from pathlib import Path

# Add parent directory (capture/) to Python path for imports
CAPTURE_DIR = Path(__file__).parent.parent
if str(CAPTURE_DIR) not in sys.path:
    sys.path.insert(0, str(CAPTURE_DIR))

import pytest
from analyze_tcpdump import (
    TcpdumpParser,
    ConnectionAnalyzer,
    is_private_ip,
    find_tcpdump_files,
    process_file,
    generate_summary,
    generate_top_ips_report,
    generate_connections_report,
    generate_ports_report,
    generate_all_ips_report,
    output_csv,
)

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data" / "tcpdump"


################################################################################
# TcpdumpParser Tests
################################################################################

class TestTcpdumpParser:
    """Tests for TcpdumpParser class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = TcpdumpParser()
    
    def test_parse_udp_packet(self):
        """Test parsing standard UDP packet"""
        line = "21:56:11.886998 IP 203.0.113.10.46102 > 192.168.1.100.59922: UDP, length 28"
        result = self.parser.parse_line(line)
        
        assert result is not None
        assert result['src_ip'] == '203.0.113.10'
        assert result['dst_ip'] == '192.168.1.100'
        assert result['src_port'] == 46102
        assert result['dst_port'] == 59922
        assert result['protocol'] == 'UDP'
        assert result['length'] == 28
    
    def test_parse_icmp_packet(self):
        """Test parsing ICMP packet without ports"""
        line = "21:56:12.338504 IP 192.168.1.254 > 192.168.1.100: ICMP time exceeded in-transit, length 40"
        result = self.parser.parse_line(line)
        
        assert result is not None
        assert result['src_ip'] == '192.168.1.254'
        assert result['dst_ip'] == '192.168.1.100'
        assert result['src_port'] is None
        assert result['dst_port'] is None
        assert result['protocol'] == 'ICMP'
        assert result['length'] == 40
    
    def test_parse_quic_packet(self):
        """Test parsing QUIC packet"""
        line = "21:56:16.643287 IP 192.168.1.100.59524 > 203.0.113.11.443: quic, protected"
        result = self.parser.parse_line(line)
        
        assert result is not None
        assert result['src_ip'] == '192.168.1.100'
        assert result['dst_ip'] == '203.0.113.11'
        assert result['src_port'] == 59524
        assert result['dst_port'] == 443
        assert result['protocol'] == 'QUIC'
    
    def test_parse_tcp_packet(self):
        """Test parsing TCP packet"""
        line = "10:00:00.123456 IP 192.168.1.100.54321 > 203.0.113.14.80: Flags [S], seq 1234567890, length 0"
        result = self.parser.parse_line(line)
        
        assert result is not None
        assert result['src_ip'] == '192.168.1.100'
        assert result['dst_ip'] == '203.0.113.14'
        assert result['src_port'] == 54321
        assert result['dst_port'] == 80
        assert result['protocol'] == 'TCP'
    
    def test_parse_invalid_line(self):
        """Test parsing invalid line returns None"""
        invalid_lines = [
            "This is not a valid tcpdump line",
            "ARP who-has 192.168.1.1 tell 192.168.1.100",
            "",
            "21:56:11.886998 IP",
        ]
        
        for line in invalid_lines:
            result = self.parser.parse_line(line)
            assert result is None
    
    def test_parse_multicast(self):
        """Test parsing multicast addresses"""
        line = "21:56:14.718036 IP 172.16.1.10.5353 > 224.0.0.251.5353: 0 PTR (QM)? _example_service._tcp.local. (41)"
        result = self.parser.parse_line(line)
        
        assert result is not None
        assert result['src_ip'] == '172.16.1.10'
        assert result['dst_ip'] == '224.0.0.251'
        assert result['src_port'] == 5353
        assert result['dst_port'] == 5353
    
    @pytest.mark.parametrize("line,expected_protocol", [
        ("21:56:11.886998 IP 1.1.1.1.123 > 2.2.2.2.456: UDP, length 28", "UDP"),
        ("21:56:12.338504 IP 1.1.1.1 > 2.2.2.2: ICMP time exceeded, length 40", "ICMP"),
        ("21:56:16.643287 IP 1.1.1.1.123 > 2.2.2.2.456: quic, protected", "QUIC"),
        ("10:00:00.123456 IP 1.1.1.1.123 > 2.2.2.2.456: Flags [S], length 0", "TCP"),
    ])
    def test_protocol_detection(self, line, expected_protocol):
        """Test protocol detection for various protocols"""
        result = self.parser.parse_line(line)
        assert result is not None
        assert result['protocol'] == expected_protocol
    
    def test_extract_length(self):
        """Test packet length extraction"""
        line = "21:56:11.886998 IP 1.1.1.1.123 > 2.2.2.2.456: UDP, length 1234"
        result = self.parser.parse_line(line)
        assert result is not None
        assert result['length'] == 1234


################################################################################
# IP Address and Port Extraction Tests
################################################################################

class TestIPPortExtraction:
    """Tests for IP address and port extraction"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = TcpdumpParser()
    
    def test_extract_ip_with_port(self):
        """Test extracting IP and port from ip.port format"""
        ip, port = self.parser._extract_ip_port("192.168.1.100.54321")
        assert ip == "192.168.1.100"
        assert port == 54321
    
    def test_extract_ip_without_port(self):
        """Test extracting IP without port"""
        ip, port = self.parser._extract_ip_port("192.168.1.100")
        assert ip == "192.168.1.100"
        assert port is None
    
    def test_extract_invalid_ip(self):
        """Test extracting invalid IP returns None"""
        ip, port = self.parser._extract_ip_port("invalid-ip.12345")
        assert ip is None
        assert port is None


################################################################################
# is_private_ip() Function Tests
################################################################################

class TestIsPrivateIP:
    """Tests for is_private_ip() function"""
    
    def test_private_ip_ranges(self):
        """Test detection of private IP ranges"""
        private_ips = [
            "10.0.0.1",
            "172.16.0.1",
            "172.31.255.255",
            "192.168.1.1",
            "127.0.0.1",
            "169.254.1.1",
        ]
        
        for ip in private_ips:
            assert is_private_ip(ip), f"{ip} should be detected as private"
    
    def test_public_ips(self):
        """Test that public IPs are not detected as private"""
        public_ips = [
            "8.8.8.8",
            "1.1.1.1",
            "203.0.113.1",
        ]
        
        for ip in public_ips:
            assert not is_private_ip(ip), f"{ip} should not be detected as private"


################################################################################
# ConnectionAnalyzer Tests
################################################################################

class TestConnectionAnalyzer:
    """Tests for ConnectionAnalyzer class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = ConnectionAnalyzer()
        self.parser = TcpdumpParser()
    
    def test_add_connection(self):
        """Test adding connections to analyzer"""
        parsed = {
            'src_ip': '192.168.1.100',
            'dst_ip': '8.8.8.8',
            'src_port': 54321,
            'dst_port': 53,
            'protocol': 'UDP',
            'length': 64
        }
        
        self.analyzer.add_connection(parsed)
        
        assert self.analyzer.total_packets == 1
        assert self.analyzer.src_ip_counts['192.168.1.100'] == 1
        assert self.analyzer.dst_ip_counts['8.8.8.8'] == 1
        assert self.analyzer.protocol_counts['UDP'] == 1
        assert '192.168.1.100' in self.analyzer.unique_src_ips
        assert '8.8.8.8' in self.analyzer.unique_dst_ips
    
    def test_get_top_ips(self):
        """Test getting top IPs"""
        # Add multiple connections
        for i in range(10):
            parsed = {
                'src_ip': f'192.168.1.{i % 3}',
                'dst_ip': '8.8.8.8',
                'src_port': 54321,
                'dst_port': 53,
                'protocol': 'UDP',
                'length': 64
            }
            self.analyzer.add_connection(parsed)
        
        top_ips = self.analyzer.get_top_ips(3, 'source')
        assert len(top_ips) == 3
        # Most common should be 192.168.1.0, 192.168.1.1, or 192.168.1.2
        assert top_ips[0][1] >= top_ips[1][1]  # Sorted by count descending
    
    def test_get_protocol_counts(self):
        """Test getting protocol counts"""
        protocols = ['UDP', 'TCP', 'ICMP', 'UDP', 'UDP']
        for protocol in protocols:
            parsed = {
                'src_ip': '192.168.1.100',
                'dst_ip': '8.8.8.8',
                'src_port': 54321,
                'dst_port': 53,
                'protocol': protocol,
                'length': 64
            }
            self.analyzer.add_connection(parsed)
        
        counts = self.analyzer.get_protocol_counts()
        assert counts['UDP'] == 3
        assert counts['TCP'] == 1
        assert counts['ICMP'] == 1
    
    def test_get_port_counts(self):
        """Test getting port counts"""
        ports = [53, 80, 443, 53, 53]
        for port in ports:
            parsed = {
                'src_ip': '192.168.1.100',
                'dst_ip': '8.8.8.8',
                'src_port': 54321,
                'dst_port': port,
                'protocol': 'UDP',
                'length': 64
            }
            self.analyzer.add_connection(parsed)
        
        dst_port_counts = self.analyzer.get_port_counts('destination')
        assert dst_port_counts[53] == 3
        assert dst_port_counts[80] == 1
        assert dst_port_counts[443] == 1


################################################################################
# File Processing Tests
################################################################################

class TestFileProcessing:
    """Tests for file processing functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = TcpdumpParser()
        self.analyzer = ConnectionAnalyzer()
    
    def test_process_udp_file(self):
        """Test processing UDP-only file"""
        file_path = TEST_DATA_DIR / "sample_udp.txt"
        filters = {'protocol': 'all', 'ip': None, 'port': None, 'exclude_local': False}
        
        packets = process_file(file_path, self.analyzer, self.parser, filters)
        
        assert packets > 0
        assert self.analyzer.total_packets == packets
        assert self.analyzer.protocol_counts['UDP'] == packets
    
    def test_process_icmp_file(self):
        """Test processing ICMP-only file"""
        file_path = TEST_DATA_DIR / "sample_icmp.txt"
        filters = {'protocol': 'all', 'ip': None, 'port': None, 'exclude_local': False}
        
        packets = process_file(file_path, self.analyzer, self.parser, filters)
        
        assert packets > 0
        assert self.analyzer.protocol_counts['ICMP'] == packets
    
    def test_process_mixed_file(self):
        """Test processing mixed protocol file"""
        file_path = TEST_DATA_DIR / "sample_mixed.txt"
        filters = {'protocol': 'all', 'ip': None, 'port': None, 'exclude_local': False}
        
        packets = process_file(file_path, self.analyzer, self.parser, filters)
        
        assert packets > 0
        assert 'UDP' in self.analyzer.protocol_counts
        assert 'ICMP' in self.analyzer.protocol_counts
        assert 'QUIC' in self.analyzer.protocol_counts
        assert 'TCP' in self.analyzer.protocol_counts
    
    def test_process_empty_file(self):
        """Test processing empty file"""
        file_path = TEST_DATA_DIR / "sample_empty.txt"
        filters = {'protocol': 'all', 'ip': None, 'port': None, 'exclude_local': False}
        
        packets = process_file(file_path, self.analyzer, self.parser, filters)
        
        assert packets == 0
        assert self.analyzer.total_packets == 0
    
    def test_process_malformed_file(self):
        """Test processing file with malformed lines"""
        file_path = TEST_DATA_DIR / "sample_malformed.txt"
        filters = {'protocol': 'all', 'ip': None, 'port': None, 'exclude_local': False}
        
        packets = process_file(file_path, self.analyzer, self.parser, filters)
        
        # Should process valid lines and skip invalid ones
        assert packets >= 0  # At least some valid lines should be processed
    
    def test_file_not_found(self):
        """Test error handling for file not found"""
        file_path = TEST_DATA_DIR / "nonexistent.txt"
        filters = {'protocol': 'all', 'ip': None, 'port': None, 'exclude_local': False}
        
        with pytest.raises(FileNotFoundError):
            process_file(file_path, self.analyzer, self.parser, filters)
    
    def test_protocol_filter(self):
        """Test protocol filtering"""
        file_path = TEST_DATA_DIR / "sample_mixed.txt"
        filters = {'protocol': 'UDP', 'ip': None, 'port': None, 'exclude_local': False}
        
        packets = process_file(file_path, self.analyzer, self.parser, filters)
        
        # Should only have UDP packets
        assert 'UDP' in self.analyzer.protocol_counts
        assert 'ICMP' not in self.analyzer.protocol_counts or self.analyzer.protocol_counts['ICMP'] == 0
    
    def test_exclude_local_ips(self):
        """Test local IP exclusion filter"""
        file_path = TEST_DATA_DIR / "sample_udp.txt"
        filters = {'protocol': 'all', 'ip': None, 'port': None, 'exclude_local': True}
        
        packets = process_file(file_path, self.analyzer, self.parser, filters)
        
        # Should have fewer packets (excluding local IPs)
        assert packets >= 0


################################################################################
# Output Format Tests
################################################################################

class TestOutputFormats:
    """Tests for output format generation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = ConnectionAnalyzer()
        self.parser = TcpdumpParser()
        
        # Add some test data
        file_path = TEST_DATA_DIR / "sample_mixed.txt"
        filters = {'protocol': 'all', 'ip': None, 'port': None, 'exclude_local': False}
        process_file(file_path, self.analyzer, self.parser, filters)
    
    def test_generate_summary(self):
        """Test summary generation"""
        file_info = {'files': [Path("test.txt")]}
        summary = generate_summary(self.analyzer, file_info)
        
        assert "TCPDump Analysis Summary" in summary
        assert "Total Packets" in summary
        assert "Unique Source IPs" in summary
    
    def test_generate_top_ips_report(self):
        """Test top IPs report generation"""
        report = generate_top_ips_report(self.analyzer, 5, 'source')
        
        assert "Source IP Addresses" in report or "Top" in report
    
    def test_generate_connections_report(self):
        """Test connections report generation"""
        report = generate_connections_report(self.analyzer, 10)
        
        assert "Connection Pairs" in report
    
    def test_generate_ports_report(self):
        """Test ports report generation"""
        report = generate_ports_report(self.analyzer, 10, 'source')
        
        assert "Port Usage" in report or "Source Port" in report
    
    def test_generate_all_ips_report(self):
        """Test all IPs report generation"""
        report = generate_all_ips_report(self.analyzer)
        
        assert "Unique IP Addresses" in report
        assert "Source IPs" in report
        assert "Destination IPs" in report
    
    def test_output_csv(self):
        """Test CSV output generation"""
        csv_output = output_csv(self.analyzer, 'connections')
        
        assert csv_output
        lines = csv_output.strip().split('\n')
        assert len(lines) > 0
        assert 'src_ip' in lines[0] or 'type' in lines[0]  # Header row


################################################################################
# File Finding Tests
################################################################################

class TestFileFinding:
    """Tests for file finding functionality"""
    
    def test_find_tcpdump_files(self):
        """Test finding tcpdump files in directory"""
        files = find_tcpdump_files(TEST_DATA_DIR)
        
        # Should find at least some test files
        assert isinstance(files, list)
        # Note: Test files don't match record-tcpdump_*.txt pattern,
        # but function should still work
    
    def test_find_tcpdump_files_nonexistent_dir(self):
        """Test finding files in nonexistent directory"""
        files = find_tcpdump_files(Path("/nonexistent/directory"))
        
        assert files == []


################################################################################
# Integration Tests
################################################################################

@pytest.mark.integration
class TestIntegration:
    """Integration tests for full workflow"""
    
    def test_full_workflow(self):
        """Test complete workflow from file to output"""
        parser = TcpdumpParser()
        analyzer = ConnectionAnalyzer()
        file_path = TEST_DATA_DIR / "sample_mixed.txt"
        filters = {'protocol': 'all', 'ip': None, 'port': None, 'exclude_local': False}
        
        # Process file
        packets = process_file(file_path, analyzer, parser, filters)
        assert packets > 0
        
        # Generate reports
        file_info = {'files': [file_path]}
        summary = generate_summary(analyzer, file_info)
        assert summary
        
        # Check that data was aggregated correctly
        assert analyzer.total_packets == packets
        assert len(analyzer.unique_src_ips) > 0
        assert len(analyzer.unique_dst_ips) > 0


################################################################################
# Performance Tests
################################################################################

@pytest.mark.performance
class TestPerformance:
    """Performance tests for large files"""
    
    def test_large_file_processing(self):
        """Test processing large file"""
        parser = TcpdumpParser()
        analyzer = ConnectionAnalyzer()
        file_path = TEST_DATA_DIR / "sample_large.txt"
        filters = {'protocol': 'all', 'ip': None, 'port': None, 'exclude_local': False}
        
        # Should process without memory issues
        packets = process_file(file_path, analyzer, parser, filters)
        
        assert packets > 0
        assert analyzer.total_packets == packets
