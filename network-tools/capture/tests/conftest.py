"""
Pytest configuration and shared fixtures for analyze-tcpdump tests
"""

import sys
from pathlib import Path

# Add capture directory to Python path
CAPTURE_DIR = Path(__file__).parent.parent
if str(CAPTURE_DIR) not in sys.path:
    sys.path.insert(0, str(CAPTURE_DIR))
