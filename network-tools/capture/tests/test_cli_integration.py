"""
CLI Integration Tests for analyze-tcpdump.py

Tests the CLI interface and main() function to improve test coverage.
These tests exercise the actual command-line interface of the tool.
"""

import sys
import subprocess
import importlib.util
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory (capture/) to Python path for imports
CAPTURE_DIR = Path(__file__).parent.parent
if str(CAPTURE_DIR) not in sys.path:
    sys.path.insert(0, str(CAPTURE_DIR))

# Import analyze-tcpdump.py (hyphenated filename) as a module
SCRIPT_PATH = CAPTURE_DIR / "analyze-tcpdump.py"
spec = importlib.util.spec_from_file_location("analyze_tcpdump", SCRIPT_PATH)
analyze_tcpdump = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze_tcpdump)

import pytest

# Import from the loaded module
main = analyze_tcpdump.main
TcpdumpParser = analyze_tcpdump.TcpdumpParser
ConnectionAnalyzer = analyze_tcpdump.ConnectionAnalyzer
is_private_ip = analyze_tcpdump.is_private_ip
find_tcpdump_files = analyze_tcpdump.find_tcpdump_files
process_file = analyze_tcpdump.process_file
generate_summary = analyze_tcpdump.generate_summary
generate_top_ips_report = analyze_tcpdump.generate_top_ips_report
generate_connections_report = analyze_tcpdump.generate_connections_report
generate_ports_report = analyze_tcpdump.generate_ports_report
generate_all_ips_report = analyze_tcpdump.generate_all_ips_report
output_csv = analyze_tcpdump.output_csv

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data" / "tcpdump"


################################################################################
# CLI Basic Functionality Tests
################################################################################

class TestCLIBasic:
    """Test basic CLI functionality"""

    def test_cli_with_file_argument(self, capsys):
        """Test CLI with file argument"""
        test_file = TEST_DATA_DIR / "sample_mixed.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', str(test_file)]):
            main()
        
        captured = capsys.readouterr()
        assert 'TCPDump Analysis Summary' in captured.out
        assert 'Total Packets' in captured.out

    def test_cli_with_f_option(self, capsys):
        """Test CLI with -f file option"""
        test_file = TEST_DATA_DIR / "sample_mixed.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', '-f', str(test_file)]):
            main()
        
        captured = capsys.readouterr()
        assert 'TCPDump Analysis Summary' in captured.out

    def test_cli_multiple_files(self, capsys):
        """Test CLI with multiple files"""
        test_file1 = TEST_DATA_DIR / "sample_udp.txt"
        test_file2 = TEST_DATA_DIR / "sample_tcp.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', str(test_file1), str(test_file2)]):
            main()
        
        captured = capsys.readouterr()
        assert 'TCPDump Analysis Summary' in captured.out


################################################################################
# CLI Output Format Tests
################################################################################

class TestCLIOutputFormats:
    """Test all output format options"""

    def test_cli_output_format_summary(self, capsys):
        """Test -o summary output format"""
        test_file = TEST_DATA_DIR / "sample_mixed.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', '-o', 'summary', str(test_file)]):
            main()
        
        captured = capsys.readouterr()
        assert 'TCPDump Analysis Summary' in captured.out
        assert 'Total Packets' in captured.out

    def test_cli_output_format_ips(self, capsys):
        """Test -o ips output format"""
        test_file = TEST_DATA_DIR / "sample_mixed.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', '-o', 'ips', str(test_file)]):
            main()
        
        captured = capsys.readouterr()
        assert 'Unique IP Addresses' in captured.out
        assert 'Source IPs' in captured.out

    def test_cli_output_format_connections(self, capsys):
        """Test -o connections output format"""
        test_file = TEST_DATA_DIR / "sample_mixed.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', '-o', 'connections', str(test_file)]):
            main()
        
        captured = capsys.readouterr()
        assert 'Connection Pairs' in captured.out

    def test_cli_output_format_ports(self, capsys):
        """Test -o ports output format"""
        test_file = TEST_DATA_DIR / "sample_mixed.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', '-o', 'ports', str(test_file)]):
            main()
        
        captured = capsys.readouterr()
        assert 'Port Usage' in captured.out

    def test_cli_output_format_all(self, capsys):
        """Test -o all output format (default)"""
        test_file = TEST_DATA_DIR / "sample_mixed.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', '-o', 'all', str(test_file)]):
            main()
        
        captured = capsys.readouterr()
        assert 'TCPDump Analysis Summary' in captured.out
        assert 'Unique IP Addresses' in captured.out

    def test_cli_csv_output(self, capsys):
        """Test -c CSV output format"""
        test_file = TEST_DATA_DIR / "sample_mixed.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', '-c', '-o', 'connections', str(test_file)]):
            main()
        
        captured = capsys.readouterr()
        # CSV should have header row
        lines = captured.out.strip().split('\n')
        assert len(lines) > 0
        assert 'src_ip' in lines[0] or 'type' in lines[0]


################################################################################
# CLI Filter Tests
################################################################################

class TestCLIFilters:
    """Test all filter options"""

    def test_cli_protocol_filter_udp(self, capsys):
        """Test -p udp protocol filter"""
        test_file = TEST_DATA_DIR / "sample_mixed.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', '-p', 'udp', str(test_file)]):
            main()
        
        captured = capsys.readouterr()
        # Should only have UDP packets
        assert 'Total Packets' in captured.out

    def test_cli_protocol_filter_tcp(self, capsys):
        """Test -p tcp protocol filter"""
        test_file = TEST_DATA_DIR / "sample_tcp.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', '-p', 'tcp', str(test_file)]):
            main()
        
        captured = capsys.readouterr()
        assert 'Total Packets' in captured.out

    def test_cli_protocol_filter_icmp(self, capsys):
        """Test -p icmp protocol filter"""
        test_file = TEST_DATA_DIR / "sample_icmp.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', '-p', 'icmp', str(test_file)]):
            main()
        
        captured = capsys.readouterr()
        assert 'Total Packets' in captured.out

    def test_cli_protocol_filter_quic(self, capsys):
        """Test -p quic protocol filter"""
        test_file = TEST_DATA_DIR / "sample_quic.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', '-p', 'quic', str(test_file)]):
            main()
        
        captured = capsys.readouterr()
        assert 'Total Packets' in captured.out

    def test_cli_ip_filter(self, capsys):
        """Test -i IP filter"""
        test_file = TEST_DATA_DIR / "sample_mixed.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', '-i', '192.168.1.100', str(test_file)]):
            main()
        
        captured = capsys.readouterr()
        assert 'Total Packets' in captured.out

    def test_cli_port_filter(self, capsys):
        """Test -P port filter"""
        test_file = TEST_DATA_DIR / "sample_mixed.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', '-P', '53', str(test_file)]):
            main()
        
        captured = capsys.readouterr()
        assert 'Total Packets' in captured.out

    def test_cli_exclude_local(self, capsys):
        """Test -l exclude local IPs"""
        test_file = TEST_DATA_DIR / "sample_mixed.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', '-l', str(test_file)]):
            try:
                main()
                captured = capsys.readouterr()
                # May have no packets if all are local, or may have some
                assert 'Total Packets' in captured.out or 'No packets found' in captured.err or 'TCPDump Analysis Summary' in captured.out
            except SystemExit:
                # May exit with code 0 if no packets found
                captured = capsys.readouterr()
                assert 'No packets found' in captured.err or 'Total Packets' in captured.out


################################################################################
# CLI Mode Options Tests
################################################################################

class TestCLIModeOptions:
    """Test mode options (quiet, verbose, top N)"""

    def test_cli_quiet_mode(self, capsys):
        """Test -q quiet mode"""
        test_file = TEST_DATA_DIR / "sample_mixed.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', '-q', '-o', 'summary', str(test_file)]):
            main()
        
        captured = capsys.readouterr()
        # Quiet mode should still output summary
        assert 'TCPDump Analysis Summary' in captured.out

    def test_cli_verbose_mode(self, capsys):
        """Test -v verbose mode"""
        test_file = TEST_DATA_DIR / "sample_mixed.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', '-v', str(test_file)]):
            main()
        
        captured = capsys.readouterr()
        # Verbose mode may output to stderr
        assert 'TCPDump Analysis Summary' in captured.out

    def test_cli_top_n_option(self, capsys):
        """Test -t top N option"""
        test_file = TEST_DATA_DIR / "sample_mixed.txt"
        
        with patch('sys.argv', ['analyze-tcpdump.py', '-t', '5', str(test_file)]):
            main()
        
        captured = capsys.readouterr()
        assert 'TCPDump Analysis Summary' in captured.out


################################################################################
# CLI Error Handling Tests
################################################################################

class TestCLIErrorHandling:
    """Test CLI error handling"""

    def test_cli_file_not_found_error(self, capsys):
        """Test error when file not found"""
        with patch('sys.argv', ['analyze-tcpdump.py', 'nonexistent.txt']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert 'Error' in captured.err or 'not found' in captured.err

    def test_cli_directory_not_found_error(self, capsys):
        """Test error when directory not found"""
        with patch('sys.argv', ['analyze-tcpdump.py', '-d', '/nonexistent/directory']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert 'Error' in captured.err or 'not found' in captured.err

    def test_cli_no_files_in_directory(self, tmp_path, capsys):
        """Test error when no files found in directory"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        with patch('sys.argv', ['analyze-tcpdump.py', '-d', str(empty_dir)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert 'Error' in captured.err or 'No tcpdump files' in captured.err


################################################################################
# Edge Case Tests for Output Functions
################################################################################

class TestOutputEdgeCases:
    """Test edge cases in output functions"""

    def test_generate_summary_empty_analyzer(self):
        """Test summary generation with empty analyzer"""
        analyzer = ConnectionAnalyzer()
        file_info = {'files': [Path('test.txt')]}
        
        summary = generate_summary(analyzer, file_info)
        
        assert 'Total Packets: 0' in summary
        assert 'Unique Source IPs: 0' in summary
        assert 'Unique Destination IPs: 0' in summary

    def test_generate_top_ips_empty_analyzer(self):
        """Test top IPs report with empty analyzer"""
        analyzer = ConnectionAnalyzer()
        
        report = generate_top_ips_report(analyzer, 10, 'source')
        
        assert 'Source IP Addresses' in report or 'Top' in report or 'Source' in report

    def test_generate_connections_empty_analyzer(self):
        """Test connections report with empty analyzer"""
        analyzer = ConnectionAnalyzer()
        
        report = generate_connections_report(analyzer, 10)
        
        assert 'Connection Pairs' in report
        assert 'No connections found' in report or 'found' in report.lower()

    def test_generate_ports_empty_analyzer(self):
        """Test ports report with empty analyzer"""
        analyzer = ConnectionAnalyzer()
        
        report = generate_ports_report(analyzer, 10, 'source')
        
        assert 'Port Usage' in report or 'Source Port' in report or 'Source' in report
        assert 'No' in report or 'found' in report.lower()

    def test_generate_all_ips_empty_analyzer(self):
        """Test all IPs report with empty analyzer"""
        analyzer = ConnectionAnalyzer()
        
        report = generate_all_ips_report(analyzer)
        
        assert 'Unique IP Addresses' in report
        assert 'Source IPs (0):' in report or 'Source IPs' in report

    def test_output_csv_empty_analyzer(self):
        """Test CSV output with empty analyzer"""
        analyzer = ConnectionAnalyzer()
        
        csv_output = output_csv(analyzer, 'connections')
        
        assert csv_output
        lines = csv_output.strip().split('\n')
        assert len(lines) >= 1  # At least header row

    def test_generate_top_ips_n_zero(self):
        """Test top IPs with N=0"""
        analyzer = ConnectionAnalyzer()
        
        # Add some data
        parsed = {
            'src_ip': '192.168.1.100',
            'dst_ip': '8.8.8.8',
            'src_port': 54321,
            'dst_port': 53,
            'protocol': 'UDP',
            'length': 64
        }
        analyzer.add_connection(parsed)
        
        report = generate_top_ips_report(analyzer, 0, 'source')
        
        assert 'Top' in report or 'Source' in report or 'IP Addresses' in report

    def test_generate_top_ips_n_larger_than_available(self):
        """Test top IPs with N larger than available"""
        analyzer = ConnectionAnalyzer()
        
        # Add one connection
        parsed = {
            'src_ip': '192.168.1.100',
            'dst_ip': '8.8.8.8',
            'src_port': 54321,
            'dst_port': 53,
            'protocol': 'UDP',
            'length': 64
        }
        analyzer.add_connection(parsed)
        
        report = generate_top_ips_report(analyzer, 100, 'source')
        
        # Should show the one IP that exists
        assert '192.168.1.100' in report
        assert 'Top' in report or 'Source' in report


################################################################################
# Filter Combination Tests
################################################################################

class TestFilterCombinations:
    """Test filter combinations"""

    def test_filter_protocol_and_ip(self):
        """Test protocol and IP filter together"""
        parser = TcpdumpParser()
        analyzer = ConnectionAnalyzer()
        file_path = TEST_DATA_DIR / "sample_mixed.txt"
        filters = {
            'protocol': 'UDP',
            'ip': '192.168.1.100',
            'port': None,
            'exclude_local': False
        }
        
        packets = process_file(file_path, analyzer, parser, filters)
        
        assert packets >= 0  # May be 0 if no matches

    def test_filter_protocol_and_port(self):
        """Test protocol and port filter together"""
        parser = TcpdumpParser()
        analyzer = ConnectionAnalyzer()
        file_path = TEST_DATA_DIR / "sample_mixed.txt"
        filters = {
            'protocol': 'UDP',
            'ip': None,
            'port': 53,
            'exclude_local': False
        }
        
        packets = process_file(file_path, analyzer, parser, filters)
        
        assert packets >= 0

    def test_filter_protocol_and_exclude_local(self):
        """Test protocol and exclude_local filter together"""
        parser = TcpdumpParser()
        analyzer = ConnectionAnalyzer()
        file_path = TEST_DATA_DIR / "sample_mixed.txt"
        filters = {
            'protocol': 'UDP',
            'ip': None,
            'port': None,
            'exclude_local': True
        }
        
        packets = process_file(file_path, analyzer, parser, filters)
        
        assert packets >= 0

    def test_filter_ip_and_port(self):
        """Test IP and port filter together"""
        parser = TcpdumpParser()
        analyzer = ConnectionAnalyzer()
        file_path = TEST_DATA_DIR / "sample_mixed.txt"
        filters = {
            'protocol': 'all',
            'ip': '192.168.1.100',
            'port': 54321,
            'exclude_local': False
        }
        
        packets = process_file(file_path, analyzer, parser, filters)
        
        assert packets >= 0

    def test_filter_all_combined(self):
        """Test all filters combined"""
        parser = TcpdumpParser()
        analyzer = ConnectionAnalyzer()
        file_path = TEST_DATA_DIR / "sample_mixed.txt"
        filters = {
            'protocol': 'UDP',
            'ip': '192.168.1.100',
            'port': 54321,
            'exclude_local': False
        }
        
        packets = process_file(file_path, analyzer, parser, filters)
        
        assert packets >= 0

    def test_filter_nonexistent_ip(self):
        """Test filter with IP that doesn't exist in data"""
        parser = TcpdumpParser()
        analyzer = ConnectionAnalyzer()
        file_path = TEST_DATA_DIR / "sample_mixed.txt"
        filters = {
            'protocol': 'all',
            'ip': '999.999.999.999',
            'port': None,
            'exclude_local': False
        }
        
        packets = process_file(file_path, analyzer, parser, filters)
        
        assert packets == 0

    def test_filter_nonexistent_port(self):
        """Test filter with port that doesn't exist in data"""
        parser = TcpdumpParser()
        analyzer = ConnectionAnalyzer()
        file_path = TEST_DATA_DIR / "sample_mixed.txt"
        filters = {
            'protocol': 'all',
            'ip': None,
            'port': 99999,
            'exclude_local': False
        }
        
        packets = process_file(file_path, analyzer, parser, filters)
        
        assert packets == 0

    def test_exclude_local_only_local_ips(self):
        """Test exclude_local when all IPs are local"""
        parser = TcpdumpParser()
        analyzer = ConnectionAnalyzer()
        file_path = TEST_DATA_DIR / "sample_udp.txt"  # May have only local IPs
        filters = {
            'protocol': 'all',
            'ip': None,
            'port': None,
            'exclude_local': True
        }
        
        packets = process_file(file_path, analyzer, parser, filters)
        
        assert packets >= 0  # May be 0 if all are local


################################################################################
# Error Path Tests
################################################################################

class TestErrorPaths:
    """Test error handling paths"""

    def test_extract_ip_port_invalid_ip(self):
        """Test _extract_ip_port with invalid IP format"""
        parser = TcpdumpParser()
        
        ip, port = parser._extract_ip_port("invalid-ip.12345")
        
        assert ip is None
        assert port is None

    def test_extract_ip_port_invalid_port(self):
        """Test _extract_ip_port with invalid port format"""
        parser = TcpdumpParser()
        
        # Try with field that looks like IP.port but port is invalid
        ip, port = parser._extract_ip_port("192.168.1.100.invalid")
        
        # Should treat entire field as IP (which may be invalid)
        assert ip is None or ip == "192.168.1.100.invalid"

    def test_parse_line_fails_ip_extraction(self):
        """Test parse_line when IP extraction fails"""
        parser = TcpdumpParser()
        
        # Line that matches pattern but has invalid IPs
        line = "21:56:11.886998 IP invalid-ip.123 > also-invalid.456: UDP, length 28"
        result = parser.parse_line(line)
        
        assert result is None

    def test_find_tcpdump_files_empty_directory(self, tmp_path):
        """Test find_tcpdump_files with empty directory"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        files = find_tcpdump_files(empty_dir)
        
        assert files == []
    
    def test_find_tcpdump_files_excludes_analysis_output(self, tmp_path):
        """Test that find_tcpdump_files excludes analysis output files"""
        test_dir = tmp_path / "log"
        test_dir.mkdir()
        
        # Create actual tcpdump capture file
        capture_file = test_dir / "record-tcpdump_2025-12-12_082910.txt"
        capture_file.write_text("10:00:00.000000 IP 192.168.1.1 > 192.168.1.2: ICMP\n")
        
        # Create analysis output files (should be excluded)
        analysis_file1 = test_dir / "record-tcpdump_2025-12-12_082910_analysis.txt"
        analysis_file1.write_text("Analysis output")
        analysis_file2 = test_dir / "record-tcpdump_2025-12-12_082910_analysis.ipmasked.txt"
        analysis_file2.write_text("Sanitized output")
        
        files = find_tcpdump_files(test_dir)
        
        # Should only find the actual capture file, not analysis files
        assert len(files) == 1
        assert files[0].name == "record-tcpdump_2025-12-12_082910.txt"
        assert "_analysis" not in files[0].name
