"""
Pytest configuration for test discovery and imports.

Adds server/src to Python path so tests can import from src modules.
"""

import sys
from pathlib import Path

# Add server/src to Python path
server_root = Path(__file__).parent.parent
src_path = server_root / "src"
sys.path.insert(0, str(src_path))
