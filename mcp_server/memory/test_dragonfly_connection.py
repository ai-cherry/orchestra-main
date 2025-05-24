#!/usr/bin/env python3
"""
Test script for DragonflyDB connection and performance.

This script verifies:
- DragonflyDB connectivity
- CRUD operations
- Performance benchmarking
- Connection pooling
"""

import sys
from pathlib import Path
from typing import Any, Dict

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_server.config.dragonfly_config import validate_dragonfly_config
from mcp_server.memory.dragonfly_cache import DragonflyCache


class DragonflyConnectionTest:
    """Test suite for DragonflyDB connection and operations."""

    def __init__(self):
        self.cache = DragonflyCache()
        self.test_results: Dict[str, Any] = {}

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        print("=" * 60)
        print("DragonflyDB Connection Test Suite")
        print("=" * 60)

        # Validate configuration
        print("\n1. Validating configuration...")
        if not validate_dragonfly_config():
            print("❌ Configuration validation failed")
            return {"error": "Invalid configuration"}
