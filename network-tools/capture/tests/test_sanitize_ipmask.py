"""
Tests for sanitize-analysis-ipmask.py

Tests IP masking functionality including:
- Different mappings between runs
- Consistent mappings within a run
- Separate mappings for 2nd vs 3rd octets
- Preservation of 1st and 4th octets
"""

import sys
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

# Add parent directory (capture/) to Python path for imports
CAPTURE_DIR = Path(__file__).parent.parent
if str(CAPTURE_DIR) not in sys.path:
    sys.path.insert(0, str(CAPTURE_DIR))

# Import the sanitizer
import importlib.util
SCRIPT_PATH = CAPTURE_DIR / "sanitize-analysis-ipmask.py"
spec = importlib.util.spec_from_file_location("sanitize_analysis_ipmask", SCRIPT_PATH)
sanitize_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sanitize_module)

IPMaskSanitizer = sanitize_module.IPMaskSanitizer

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data" / "tcpdump"


################################################################################
# Test Data Setup
################################################################################

@pytest.fixture
def sample_analysis_file(tmp_path):
    """Create a sample analysis file with private IPs for testing."""
    content = """TCPDump Analysis Summary
========================
Files: log/sample.txt
Total Packets: 100
Unique Source IPs: 5
Unique Destination IPs: 5
Protocols: TCP (50), UDP (50)

Top 10 Source IPs:
  192.168.42.7         50 packets
  172.24.147.10        30 packets
  10.82.141.140        20 packets

Top 10 Destination IPs:
  192.168.42.7         50 packets
  172.24.147.10        30 packets
  10.82.141.140        20 packets

Connection Pairs (Source -> Destination)
========================================
  192.168.42.7:443 -> 172.24.147.10:80 (TCP) - 50 packets
  10.82.141.140:53 -> 192.168.42.7:443 (UDP) - 20 packets
"""
    test_file = tmp_path / "sample_analysis.txt"
    test_file.write_text(content)
    return test_file


################################################################################
# Test Different Mappings Between Runs
################################################################################

class TestDifferentMappingsBetweenRuns:
    """Test that different runs produce different mappings."""

    def test_different_mappings_no_seed(self, sample_analysis_file, tmp_path):
        """Test that two runs without seed produce different mappings."""
        output1 = tmp_path / "output1.txt"
        output2 = tmp_path / "output2.txt"
        
        # Run 1
        sanitizer1 = IPMaskSanitizer(seed=None, mask_public_ips=False)
        content1 = sample_analysis_file.read_text()
        sanitized1 = sanitizer1.sanitize(content1)
        output1.write_text(sanitized1)
        
        # Run 2
        sanitizer2 = IPMaskSanitizer(seed=None, mask_public_ips=False)
        content2 = sample_analysis_file.read_text()
        sanitized2 = sanitizer2.sanitize(content2)
        output2.write_text(sanitized2)
        
        # Extract masked IPs
        pattern = r'(\d+\.([A-Z]{2})\.([A-Z]{2})\.\d+)'
        run1_ips = {ip: (oct2, oct3) for ip, oct2, oct3 in re.findall(pattern, sanitized1)}
        run2_ips = {ip: (oct2, oct3) for ip, oct2, oct3 in re.findall(pattern, sanitized2)}
        
        # Find IPs that appear in both (same 1st and 4th octets)
        matching_ips = []
        for ip1, (oct2_1, oct3_1) in run1_ips.items():
            parts1 = ip1.split('.')
            for ip2, (oct2_2, oct3_2) in run2_ips.items():
                parts2 = ip2.split('.')
                if parts1[0] == parts2[0] and parts1[3] == parts2[3]:
                    # Same original IP, check if mappings differ
                    if oct2_1 == oct2_2 and oct3_1 == oct3_2:
                        matching_ips.append((ip1, ip2))
        
        # With random mapping, we expect different mappings (very unlikely to match)
        # But allow for extremely rare chance of collision
        assert len(matching_ips) == 0, f"Found {len(matching_ips)} IPs with identical mappings between runs"

    def test_same_seed_produces_same_mappings(self, sample_analysis_file, tmp_path):
        """Test that same seed produces same mappings."""
        seed = 12345
        
        # Run 1
        sanitizer1 = IPMaskSanitizer(seed=seed, mask_public_ips=False)
        content1 = sample_analysis_file.read_text()
        sanitized1 = sanitizer1.sanitize(content1)
        
        # Run 2 with same seed
        sanitizer2 = IPMaskSanitizer(seed=seed, mask_public_ips=False)
        content2 = sample_analysis_file.read_text()
        sanitized2 = sanitizer2.sanitize(content2)
        
        # Extract masked IPs
        pattern = r'(\d+\.([A-Z]{2})\.([A-Z]{2})\.\d+)'
        run1_ips = {ip: (oct2, oct3) for ip, oct2, oct3 in re.findall(pattern, sanitized1)}
        run2_ips = {ip: (oct2, oct3) for ip, oct2, oct3 in re.findall(pattern, sanitized2)}
        
        # With same seed, mappings should be identical
        assert run1_ips == run2_ips, "Same seed should produce identical mappings"


################################################################################
# Test Consistent Mappings Within Run
################################################################################

class TestConsistentMappingsWithinRun:
    """Test that same IP always maps to same masked IP within a run."""

    def test_same_ip_maps_consistently(self, sample_analysis_file):
        """Test that same original IP always maps to same masked IP."""
        sanitizer = IPMaskSanitizer(seed=42, mask_public_ips=False)
        content = sample_analysis_file.read_text()
        sanitized = sanitizer.sanitize(content)
        
        # Extract all occurrences of 192.168.42.7 (should all map to same)
        pattern = r'192\.168\.42\.7'
        original_matches = re.findall(pattern, content)
        
        # Find the masked version
        masked_pattern = r'192\.([A-Z]{2})\.([A-Z]{2})\.7'
        masked_matches = re.findall(masked_pattern, sanitized)
        
        # All occurrences should map to same masked IP
        if masked_matches:
            first_mapping = masked_matches[0]
            assert all(m == first_mapping for m in masked_matches), \
                "Same original IP should map to same masked IP throughout"


################################################################################
# Test Separate Mappings for 2nd and 3rd Octets
################################################################################

class TestSeparateOctetMappings:
    """Test that 2nd and 3rd octets use separate mappings."""

    def test_same_value_different_positions(self, sample_analysis_file):
        """Test that same value in 2nd vs 3rd position maps to different letters."""
        sanitizer = IPMaskSanitizer(seed=42, mask_public_ips=False)
        content = sample_analysis_file.read_text()
        sanitized = sanitizer.sanitize(content)
        
        # Extract mappings
        pattern = r'(\d+)\.(\d+)\.(\d+)\.(\d+)'
        original_ips = re.findall(pattern, content)
        
        # Find IPs where same value appears in both 2nd and 3rd positions
        # Example: 10.0.0.126 has 0 in both 2nd and 3rd positions
        for orig1, orig2, orig3, orig4 in original_ips:
            if orig2 == orig3:  # Same value in both positions
                # Find the masked version
                masked_pattern = rf'{orig1}\.([A-Z]{{2}})\.([A-Z]{{2}})\.{orig4}'
                match = re.search(masked_pattern, sanitized)
                if match:
                    oct2_letters = match.group(1)
                    oct3_letters = match.group(2)
                    # They should be different (same value in different positions)
                    assert oct2_letters != oct3_letters, \
                        f"Value {orig2} in 2nd position ({oct2_letters}) should map differently than in 3rd position ({oct3_letters})"

    def test_octet_mappings_are_independent(self):
        """Test that octet mappings are stored separately."""
        sanitizer = IPMaskSanitizer(seed=42, mask_public_ips=False)
        
        # Map value 0 in 2nd position
        letters_2nd_0 = sanitizer._get_letter_for_octet(0, position=2)
        
        # Map value 0 in 3rd position
        letters_3rd_0 = sanitizer._get_letter_for_octet(0, position=3)
        
        # They should be different
        assert letters_2nd_0 != letters_3rd_0, \
            f"Value 0 should map to different letters in 2nd ({letters_2nd_0}) vs 3rd ({letters_3rd_0}) position"
        
        # Verify they're stored in separate dictionaries
        assert 0 in sanitizer.octet2_map
        assert 0 in sanitizer.octet3_map
        assert sanitizer.octet2_map[0] != sanitizer.octet3_map[0]


################################################################################
# Test Preservation of 1st and 4th Octets
################################################################################

class TestOctetPreservation:
    """Test that 1st and 4th octets are preserved."""

    def test_first_and_last_octets_preserved(self, sample_analysis_file):
        """Test that 1st and 4th octets remain unchanged."""
        sanitizer = IPMaskSanitizer(seed=42, mask_public_ips=False)
        content = sample_analysis_file.read_text()
        sanitized = sanitizer.sanitize(content)
        
        # Extract original IPs
        pattern = r'(\d+)\.(\d+)\.(\d+)\.(\d+)'
        original_ips = re.findall(pattern, content)
        
        for orig1, orig2, orig3, orig4 in original_ips:
            # Find masked version
            masked_pattern = rf'({orig1})\.([A-Z]{{2}})\.([A-Z]{{2}})\.({orig4})'
            match = re.search(masked_pattern, sanitized)
            if match:
                masked1 = match.group(1)
                masked4 = match.group(4)
                # 1st and 4th octets should be unchanged
                assert masked1 == orig1, f"1st octet should be preserved: {orig1} -> {masked1}"
                assert masked4 == orig4, f"4th octet should be preserved: {orig4} -> {masked4}"


################################################################################
# Test No Hex Letters
################################################################################

class TestNoHexLetters:
    """Test that no hex letters (A-F) are used."""

    def test_no_hex_letters_in_mappings(self, sample_analysis_file):
        """Test that masked IPs don't contain hex letters A-F."""
        sanitizer = IPMaskSanitizer(seed=42, mask_public_ips=False)
        content = sample_analysis_file.read_text()
        sanitized = sanitizer.sanitize(content)
        
        # Extract all letter combinations
        pattern = r'\.([A-F][A-Z]|[A-Z][A-F]|[A-F]{2})\.'
        hex_matches = re.findall(pattern, sanitized)
        
        assert len(hex_matches) == 0, \
            f"Found hex letters (A-F) in masked IPs: {hex_matches}"

    def test_valid_letters_only(self):
        """Test that only valid letters (G-Z) are used."""
        sanitizer = IPMaskSanitizer(seed=42, mask_public_ips=False)
        
        # Generate mappings for several values
        for val in [0, 42, 168, 255]:
            letters_2nd = sanitizer._get_letter_for_octet(val, position=2)
            letters_3rd = sanitizer._get_letter_for_octet(val, position=3)
            
            # Check each letter is in G-Z range
            for letter in letters_2nd + letters_3rd:
                assert 'G' <= letter <= 'Z', \
                    f"Letter {letter} should be in range G-Z"


################################################################################
# Test CLI Integration
################################################################################

class TestCLIIntegration:
    """Test CLI interface."""

    def test_cli_produces_output(self, sample_analysis_file, tmp_path):
        """Test that CLI produces output file."""
        output_file = tmp_path / "output.txt"
        
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                str(sample_analysis_file),
                '-o', str(output_file)
            ],
            capture_output=True,
            text=True,
            cwd=str(CAPTURE_DIR)
        )
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert output_file.exists(), "Output file should be created"
        assert output_file.stat().st_size > 0, "Output file should not be empty"

    def test_cli_show_mapping(self, sample_analysis_file, tmp_path):
        """Test --show-mapping option."""
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                str(sample_analysis_file),
                '--show-mapping'
            ],
            capture_output=True,
            text=True,
            cwd=str(CAPTURE_DIR)
        )
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert "IP Address Mapping Table" in result.stdout
        assert "Private IPs:" in result.stdout or "Total IPs mapped" in result.stdout

    def test_cli_different_runs_different_output(self, sample_analysis_file, tmp_path):
        """Test that CLI produces different output on different runs."""
        output1 = tmp_path / "output1.txt"
        output2 = tmp_path / "output2.txt"
        
        # Run 1
        result1 = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                str(sample_analysis_file),
                '-o', str(output1)
            ],
            capture_output=True,
            text=True,
            cwd=str(CAPTURE_DIR)
        )
        assert result1.returncode == 0
        
        # Run 2
        result2 = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                str(sample_analysis_file),
                '-o', str(output2)
            ],
            capture_output=True,
            text=True,
            cwd=str(CAPTURE_DIR)
        )
        assert result2.returncode == 0
        
        # Read outputs
        content1 = output1.read_text()
        content2 = output2.read_text()
        
        # Extract masked IPs
        pattern = r'(\d+\.([A-Z]{2})\.([A-Z]{2})\.\d+)'
        ips1 = set(re.findall(pattern, content1))
        ips2 = set(re.findall(pattern, content2))
        
        # They should be different (very unlikely to match with random)
        assert ips1 != ips2, "Different runs should produce different IP mappings"
