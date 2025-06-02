#!/usr/bin/env python3
"""
mcp_server_runner.py - Entry point for MCP Server

This module serves as the main entry point for the MCP server application.
It provides a bridge between Poetry's entry point configuration and the
actual application code in main.py.
"""

import asyncio
import sys

from mcp_server.main import main_async

def main():
    """
    Main entry point for the MCP server when invoked via Poetry.

    This function is registered as the 'mcp-server' command in pyproject.toml
    and provides a simple wrapper around the main_async function.
    """
    import argparse

    parser = argparse.ArgumentParser(description="MCP Memory System")
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()

    exit_code = asyncio.run(main_async(args.config))
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
