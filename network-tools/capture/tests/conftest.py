"""
Pytest configuration and shared fixtures for analyze-tcpdump tests
"""

import sys
from pathlib import Path
import pytest

# Add capture directory to Python path
CAPTURE_DIR = Path(__file__).parent.parent
if str(CAPTURE_DIR) not in sys.path:
    sys.path.insert(0, str(CAPTURE_DIR))

# Register custom pytest marks to avoid warnings
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
