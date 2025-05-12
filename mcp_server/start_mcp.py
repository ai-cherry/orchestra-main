#!/usr/bin/env python3
"""
start_mcp.py - Helper script to start the MCP server with proper import paths
"""

from mcp_server.main import main
import os
import sys
import argparse

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)


if __name__ == "__main__":
    main()
