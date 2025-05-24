#!/usr/bin/env python3
"""
run_optimized_server.py - Performance-Optimized MCP Server Launcher

This script launches the MCP server with performance-optimized settings
for single-developer, single-user projects. It prioritizes speed and
reduced overhead over security measures.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the simple MCP server
try:
    from simple_mcp import SimpleMCPServer
except ImportError:
    print("simple_mcp.py not found. Make sure it's in the correct location.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("optimized-mcp-server")


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        logger.info("Using default configuration")
        return {}


def optimize_for_memory(config: Dict[str, Any]) -> Dict[str, Any]:
    """Optimize configuration for low memory usage."""
    config["memory"]["cache_size_mb"] = 64
    config["memory"]["max_items_per_key"] = 500
    config["performance"]["enable_caching"] = False
    config["performance"]["lazy_loading"] = True

    # Reduce context windows for tools
    for tool in config.get("tools", {}).values():
        if "context_window" in tool:
            tool["context_window"] = tool["context_window"] // 2

    return config


def optimize_for_cpu(config: Dict[str, Any]) -> Dict[str, Any]:
    """Optimize configuration for low CPU usage."""
    config["server"]["workers"] = 1
    config["server"]["timeout"] = 60
    config["memory"]["flush_interval"] = 300
    config["performance"]["batch_operations"] = False

    # Increase update intervals for tools
    for tool in config.get("tools", {}).values():
        if "update_interval" in tool:
            tool["update_interval"] = tool["update_interval"] * 2

    return config


def optimize_for_speed(config: Dict[str, Any]) -> Dict[str, Any]:
    """Optimize configuration for maximum speed."""
    config["server"]["workers"] = os.cpu_count() or 1
    config["server"]["keepalive"] = 2
    config["memory"]["enable_compression"] = False
    config["performance"]["enable_caching"] = True
    config["performance"]["cache_ttl"] = 600
    config["performance"]["batch_operations"] = True
    config["performance"]["max_batch_size"] = 200

    # Minimize update intervals for tools
    for tool in config.get("tools", {}).values():
        if "update_interval" in tool:
            tool["update_interval"] = 0.5

    return config


def run_server(config: Dict[str, Any], debug: bool = False) -> None:
    """Run the MCP server with the provided configuration."""
    # Extract server configuration
    server_config = config.get("server", {})
    memory_config = config.get("memory", {})

    # Set up server parameters
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8080)
    storage_path = memory_config.get("storage_path", "./.mcp_memory")

    # Override debug mode if specified
    if debug:
        server_config["debug"] = True

    # Create and run the server
    logger.info(f"Starting optimized MCP server on {host}:{port}")
    logger.info(f"Using storage path: {storage_path}")

    if server_config.get("debug", False):
        logger.info("Debug mode enabled")

    # Create the server instance
    server = SimpleMCPServer(storage_path=storage_path, port=port)

    # Run the server
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running server: {e}")
        sys.exit(1)


def main():
    """Main entry point for the optimized MCP server."""
    parser = argparse.ArgumentParser(description="Run MCP server with performance optimizations")
    parser.add_argument(
        "--config",
        default="mcp_server/performance_config.json",
        help="Path to configuration file",
    )
    parser.add_argument("--port", type=int, help="Port to bind to (overrides config)")
    parser.add_argument("--storage", help="Path to storage directory (overrides config)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--optimize",
        choices=["memory", "cpu", "speed"],
        help="Optimization profile to use",
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Apply optimization profile if specified
    if args.optimize == "memory":
        logger.info("Applying memory optimization profile")
        config = optimize_for_memory(config)
    elif args.optimize == "cpu":
        logger.info("Applying CPU optimization profile")
        config = optimize_for_cpu(config)
    elif args.optimize == "speed":
        logger.info("Applying speed optimization profile")
        config = optimize_for_speed(config)

    # Override configuration with command-line arguments
    if args.port:
        config["server"]["port"] = args.port

    if args.storage:
        config["memory"]["storage_path"] = args.storage

    # Run the server
    run_server(config, args.debug)


if __name__ == "__main__":
    main()
