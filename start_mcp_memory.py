#!/usr/bin/env python3
"""Launcher script for MCP Memory Server"""

import asyncio
import sys
import os
import uvicorn

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_servers.memory_management_server import MemoryManagementServer

if __name__ == "__main__":
    server = MemoryManagementServer()
    
    # Run the server
    uvicorn.run(
        server.app,
        host="0.0.0.0",
        port=server.port,
        log_level="info"
    ) 