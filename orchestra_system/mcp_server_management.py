#!/usr/bin/env python3
"""
MCP Server Management for AI Orchestra System

This module provides tools for configuring and managing MCP (Model Context Protocol) servers
that provide persistence and shared context for AI assistants. It includes functionality
for standalone MCP server mode and integration with a running MCP server.

Key features:
- MCP server integration with Orchestra System
- Standalone MCP server mode
- Persistent context management
- Memory synchronization between environments
"""

import asyncio
import json
import logging
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mcp-server-management")

# Try to import MCP client
try:
    from gcp_migration.mcp_client_enhanced import (
        MCPClient,
        MCPResponse,
        get_client as get_mcp_client,
    )
except ImportError:
    logger.warning("Could not import enhanced MCP client, attempting to import basic client")
    try:
        from gcp_migration.mcp_client import MCPClient, get_client as get_mcp_client
    except ImportError:
        logger.error("Failed to import MCP client. MCP server management will operate in standalone mode.")
        MCPClient = object

        def get_mcp_client(*args, **kwargs):
            return None


# Constants
DEFAULT_MCP_PORT = 8080
DEFAULT_MCP_HOST = "localhost"
MCP_SERVER_STARTUP_TIMEOUT = 30  # seconds
MCP_SERVER_CHECK_INTERVAL = 1  # seconds


class MCPServerConfig:
    """Configuration for MCP server."""

    def __init__(
        self,
        host: str = DEFAULT_MCP_HOST,
        port: int = DEFAULT_MCP_PORT,
        persistent_path: Optional[str] = None,
        log_level: str = "info",
        memory_backend: str = "in_memory",
        access_token: Optional[str] = None,
    ):
        """Initialize MCP server configuration.

        Args:
            host: Host to bind the MCP server to
            port: Port to bind the MCP server to
            persistent_path: Path to store persistent memory
            log_level: Logging level (debug, info, warning, error)
            memory_backend: Memory backend (in_memory, file, redis)
            access_token: Access token for authentication
        """
        self.host = host
        self.port = port
        self.persistent_path = persistent_path
        self.log_level = log_level
        self.memory_backend = memory_backend
        self.access_token = access_token

    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary.

        Returns:
            Dictionary representation of the configuration
        """
        config = {
            "host": self.host,
            "port": self.port,
            "log_level": self.log_level,
            "memory_backend": self.memory_backend,
        }

        if self.persistent_path:
            config["persistent_path"] = self.persistent_path

        if self.access_token:
            config["access_token"] = self.access_token

        return config

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "MCPServerConfig":
        """Create a configuration from a dictionary.

        Args:
            config: Dictionary containing configuration values

        Returns:
            MCP server configuration
        """
        return cls(
            host=config.get("host", DEFAULT_MCP_HOST),
            port=config.get("port", DEFAULT_MCP_PORT),
            persistent_path=config.get("persistent_path"),
            log_level=config.get("log_level", "info"),
            memory_backend=config.get("memory_backend", "in_memory"),
            access_token=config.get("access_token"),
        )

    @classmethod
    def from_env(cls) -> "MCPServerConfig":
        """Create a configuration from environment variables.

        Returns:
            MCP server configuration
        """
        return cls(
            host=os.environ.get("MCP_HOST", DEFAULT_MCP_HOST),
            port=int(os.environ.get("MCP_PORT", DEFAULT_MCP_PORT)),
            persistent_path=os.environ.get("MCP_PERSISTENT_PATH"),
            log_level=os.environ.get("MCP_LOG_LEVEL", "info"),
            memory_backend=os.environ.get("MCP_MEMORY_BACKEND", "in_memory"),
            access_token=os.environ.get("MCP_ACCESS_TOKEN"),
        )

    def to_env(self) -> Dict[str, str]:
        """Convert the configuration to environment variables.

        Returns:
            Dictionary of environment variables
        """
        env = {
            "MCP_HOST": str(self.host),
            "MCP_PORT": str(self.port),
            "MCP_LOG_LEVEL": self.log_level,
            "MCP_MEMORY_BACKEND": self.memory_backend,
        }

        if self.persistent_path:
            env["MCP_PERSISTENT_PATH"] = self.persistent_path

        if self.access_token:
            env["MCP_ACCESS_TOKEN"] = self.access_token

        return env

    def to_file(self, path: str) -> bool:
        """Write the configuration to a file.

        Args:
            path: Path to write the configuration to

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to write configuration to {path}: {e}")
            return False

    @classmethod
    def from_file(cls, path: str) -> Optional["MCPServerConfig"]:
        """Read configuration from a file.

        Args:
            path: Path to read the configuration from

        Returns:
            MCP server configuration if successful, None otherwise
        """
        try:
            with open(path, "r") as f:
                config = json.load(f)
            return cls.from_dict(config)
        except Exception as e:
            logger.error(f"Failed to read configuration from {path}: {e}")
            return None


class MCPServerManager:
    """Manager for MCP server."""

    def __init__(
        self,
        config: Optional[MCPServerConfig] = None,
        mcp_client: Optional[MCPClient] = None,
    ):
        """Initialize MCP server manager.

        Args:
            config: MCP server configuration, default from environment
            mcp_client: MCP client to use
        """
        self.config = config or MCPServerConfig.from_env()
        self.mcp_client = mcp_client or get_mcp_client()

        # Server process
        self.process: Optional[subprocess.Popen] = None
        self.process_log_path = "mcp_server.log"
        self.startup_time: Optional[float] = None

        # Server status
        self.is_running = False
        self.is_external = False
        self.memory_keys: List[str] = []

    def check_server_status(self) -> bool:
        """Check if the MCP server is running.

        Returns:
            True if running, False otherwise
        """
        try:
            # Try to connect to the MCP server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex((self.config.host, self.config.port))

                # Connection successful
                if result == 0:
                    # Try to get keys using MCP client
                    if self.mcp_client:
                        try:
                            keys_response = self.mcp_client.list_keys()
                            if keys_response and keys_response.success:
                                self.memory_keys = keys_response.value

                            # Get -ping to check server identity
                            ping_response = self.mcp_client.get("-ping")
                            if ping_response and ping_response.success:
                                logger.info(f"MCP server running with {len(self.memory_keys)} keys")
                                return True
                        except:
                            pass

                    # Without MCP client, just check the connection
                    self.is_running = True
                    return True

                # Connection failed
                self.is_running = False
                return False
        except Exception as e:
            logger.error(f"Failed to check MCP server status: {e}")
            self.is_running = False
            return False

    def start_server(self) -> bool:
        """Start the MCP server.

        Returns:
            True if successful, False otherwise
        """
        # Check if already running locally
        if self.process and self.process.poll() is None:
            logger.info("MCP server already running locally")
            return True

        # Check if running externally
        if self.check_server_status():
            logger.info("External MCP server already running")
            self.is_external = True
            return True

        try:
            # Find MCP server module
            try:
                from mcp_server import run_server

                # Use imported run_server function
                logger.info("Using imported MCP server module")

                # Create subprocess
                log_file = open(self.process_log_path, "w")
                env = os.environ.copy()
                env.update(self.config.to_env())

                self.process = subprocess.Popen(
                    [
                        sys.executable,
                        "-c",
                        "from mcp_server import run_server; run_server()",
                    ],
                    env=env,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                )

            except ImportError:
                # Try to find mcp_server.py file
                logger.info("MCP server module not found, looking for mcp_server.py")

                # Check common locations
                locations = [
                    "./mcp_server.py",
                    "./mcp_server/server.py",
                    "./mcp-server/server.py",
                    "../mcp_server/server.py",
                ]

                server_path = None
                for location in locations:
                    if os.path.exists(location):
                        server_path = location
                        break

                if not server_path:
                    logger.error("MCP server not found")
                    return False

                # Create subprocess
                log_file = open(self.process_log_path, "w")
                env = os.environ.copy()
                env.update(self.config.to_env())

                self.process = subprocess.Popen(
                    [sys.executable, server_path],
                    env=env,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                )

            # Wait for server to start
            self.startup_time = time.time()
            for _ in range(int(MCP_SERVER_STARTUP_TIMEOUT / MCP_SERVER_CHECK_INTERVAL)):
                if self.check_server_status():
                    logger.info("MCP server started successfully")
                    return True

                # Check if process is still running
                if self.process.poll() is not None:
                    logger.error("MCP server process exited prematurely")
                    return False

                time.sleep(MCP_SERVER_CHECK_INTERVAL)

            logger.error(f"MCP server did not start within {MCP_SERVER_STARTUP_TIMEOUT} seconds")
            return False

        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            return False

    def stop_server(self) -> bool:
        """Stop the MCP server.

        Returns:
            True if successful, False otherwise
        """
        # Don't stop external servers
        if self.is_external:
            logger.info("Not stopping external MCP server")
            return True

        # Stop local server
        if self.process:
            try:
                # Try graceful shutdown first
                self.process.terminate()

                # Wait for process to exit
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if not exiting
                    self.process.kill()
                    self.process.wait()

                logger.info("MCP server stopped")
                self.process = None
                self.is_running = False
                return True

            except Exception as e:
                logger.error(f"Failed to stop MCP server: {e}")
                return False

        logger.info("No local MCP server to stop")
        return True

    def restart_server(self) -> bool:
        """Restart the MCP server.

        Returns:
            True if successful, False otherwise
        """
        if not self.stop_server():
            logger.error("Failed to stop MCP server, cannot restart")
            return False

        return self.start_server()

    async def sync_memory(
        self,
        source_host: str,
        source_port: int,
        access_token: Optional[str] = None,
        keys: Optional[List[str]] = None,
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        """Synchronize memory from another MCP server.

        Args:
            source_host: Host of the source MCP server
            source_port: Port of the source MCP server
            access_token: Access token for the source MCP server
            keys: Keys to synchronize, None for all keys
            overwrite: Whether to overwrite existing keys

        Returns:
            Synchronization results
        """
        try:
            # Create source MCP client
            from gcp_migration.mcp_client import MCPClient as BasicMCPClient

            source_client = BasicMCPClient(
                host=source_host,
                port=source_port,
                access_token=access_token,
            )

            # Get keys to sync
            if keys is None:
                keys_response = source_client.list_keys()
                if keys_response and keys_response.success:
                    keys = keys_response.value
                else:
                    logger.error("Failed to get keys from source MCP server")
                    return {"success": False, "error": "Failed to get keys"}

            # Get local keys
            local_keys = []
            if not overwrite and self.mcp_client:
                keys_response = self.mcp_client.list_keys()
                if keys_response and keys_response.success:
                    local_keys = keys_response.value

            # For each key, get value and set in local MCP memory
            results = {}
            for key in keys:
                # Skip local keys if not overwriting
                if not overwrite and key in local_keys:
                    results[key] = "skipped"
                    continue

                # Get value from source
                value_response = source_client.get(key)
                if not value_response or not value_response.success:
                    results[key] = "get_failed"
                    continue

                # Set value in local MCP memory
                if self.mcp_client:
                    set_response = self.mcp_client.set(key, value_response.value)
                    if set_response and set_response.success:
                        results[key] = "success"
                    else:
                        results[key] = "set_failed"

            # Return results
            return {
                "success": True,
                "results": results,
                "synced": list(k for k, v in results.items() if v == "success"),
                "failed": list(k for k, v in results.items() if v != "success" and v != "skipped"),
                "skipped": list(k for k, v in results.items() if v == "skipped"),
            }

        except Exception as e:
            logger.error(f"Failed to sync memory: {e}")
            return {"success": False, "error": str(e)}

    def export_memory(
        self,
        output_path: str,
        keys: Optional[List[str]] = None,
        format: str = "json",
    ) -> bool:
        """Export memory to a file.

        Args:
            output_path: Path to export to
            keys: Keys to export, None for all keys
            format: Export format (json, binary)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if MCP client is available
            if not self.mcp_client:
                logger.error("MCP client not available")
                return False

            # Get keys to export
            if keys is None:
                keys_response = self.mcp_client.list_keys()
                if keys_response and keys_response.success:
                    keys = keys_response.value
                else:
                    logger.error("Failed to get keys from MCP server")
                    return False

            # Get values for all keys
            values = {}
            for key in keys:
                value_response = self.mcp_client.get(key)
                if value_response and value_response.success:
                    values[key] = value_response.value

            # Export to file
            if format == "json":
                with open(output_path, "w") as f:
                    json.dump(values, f, indent=2)
                logger.info(f"Exported {len(values)} keys to {output_path}")
                return True
            elif format == "binary":
                # Simple binary format: {"key": value} structure
                import pickle

                with open(output_path, "wb") as f:
                    pickle.dump(values, f)
                logger.info(f"Exported {len(values)} keys to {output_path}")
                return True
            else:
                logger.error(f"Unsupported export format: {format}")
                return False

        except Exception as e:
            logger.error(f"Failed to export memory: {e}")
            return False

    def import_memory(
        self,
        input_path: str,
        format: str = "auto",
        overwrite: bool = False,
    ) -> bool:
        """Import memory from a file.

        Args:
            input_path: Path to import from
            format: Import format (auto, json, binary)
            overwrite: Whether to overwrite existing keys

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if MCP client is available
            if not self.mcp_client:
                logger.error("MCP client not available")
                return False

            # Get local keys
            local_keys = []
            if not overwrite:
                keys_response = self.mcp_client.list_keys()
                if keys_response and keys_response.success:
                    local_keys = keys_response.value

            # Determine format if auto
            if format == "auto":
                if input_path.endswith(".json"):
                    format = "json"
                elif input_path.endswith(".bin") or input_path.endswith(".pickle"):
                    format = "binary"
                else:
                    # Try to detect format
                    try:
                        with open(input_path, "r") as f:
                            json.load(f)
                        format = "json"
                    except:
                        format = "binary"

            # Import from file
            if format == "json":
                with open(input_path, "r") as f:
                    values = json.load(f)
            elif format == "binary":
                import pickle

                with open(input_path, "rb") as f:
                    values = pickle.load(f)
            else:
                logger.error(f"Unsupported import format: {format}")
                return False

            # Set values in MCP memory
            for key, value in values.items():
                # Skip local keys if not overwriting
                if not overwrite and key in local_keys:
                    continue

                # Set value in MCP memory
                self.mcp_client.set(key, value)

            logger.info(f"Imported {len(values)} keys from {input_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to import memory: {e}")
            return False

    def get_server_info(self) -> Dict[str, Any]:
        """Get information about the MCP server.

        Returns:
            Server information
        """
        info = {
            "host": self.config.host,
            "port": self.config.port,
            "is_running": self.is_running,
            "is_external": self.is_external,
            "memory_backend": self.config.memory_backend,
            "memory_keys_count": len(self.memory_keys),
        }

        # Add startup time if available
        if self.startup_time:
            info["startup_time"] = self.startup_time
            info["uptime"] = time.time() - self.startup_time

        # Add more info if MCP client is available
        if self.mcp_client:
            # Get storage stats if available
            try:
                stats_response = self.mcp_client.get("-stats")
                if stats_response and stats_response.success:
                    info["stats"] = stats_response.value
            except:
                pass

        return info


class MCPIntegrationHelper:
    """Helper for integrating MCP server with Orchestra System."""

    def __init__(
        self,
        server_manager: Optional[MCPServerManager] = None,
    ):
        """Initialize MCP integration helper.

        Args:
            server_manager: MCP server manager to use
        """
        self.server_manager = server_manager or MCPServerManager()

    def get_integration_status(self) -> Dict[str, Any]:
        """Get integration status.

        Returns:
            Integration status
        """
        # Check if MCP server is running
        mcp_running = self.server_manager.check_server_status()

        # Check if MCP client is available
        mcp_client_available = self.server_manager.mcp_client is not None

        # Check Orchestra System components
        try:
            from orchestra_system.api import get_api

            api = get_api()

            # Get component status
            component_status = {
                "resource_registry": hasattr(api, "registry") and api.registry is not None,
                "config_manager": hasattr(api, "config_manager") and api.config_manager is not None,
                "conflict_resolver": hasattr(api, "conflict_resolver") and api.conflict_resolver is not None,
            }
        except:
            component_status = {
                "resource_registry": False,
                "config_manager": False,
                "conflict_resolver": False,
            }

        # Get server info
        server_info = self.server_manager.get_server_info()

        # Return status
        return {
            "mcp_running": mcp_running,
            "mcp_client_available": mcp_client_available,
            "component_status": component_status,
            "server_info": server_info,
        }

    def initialize_mcp_integration(self) -> bool:
        """Initialize MCP integration.

        Returns:
            True if successful, False otherwise
        """
        # Start MCP server if not running
        if not self.server_manager.is_running and not self.server_manager.start_server():
            logger.error("Failed to start MCP server")
            return False

        # Initialize Orchestra System with MCP client
        try:
            from orchestra_system.api import initialize_system
            from gcp_migration.mcp_client import get_client

            # Get MCP client
            mcp_client = get_client()

            # Initialize system with MCP client
            asyncio.run(initialize_system())

            logger.info("MCP integration initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize MCP integration: {e}")
            return False

    async def sync_orchestra_data_to_mcp(self) -> Dict[str, Any]:
        """Synchronize Orchestra System data to MCP memory.

        Returns:
            Synchronization results
        """
        try:
            # Check if MCP client is available
            if not self.server_manager.mcp_client:
                logger.error("MCP client not available")
                return {"success": False, "error": "MCP client not available"}

            # Initialize Orchestra System components
            from orchestra_system.api import get_api

            api = get_api()

            # Discover resources
            await api.discover_resources()

            # Discover configuration
            api.discover_configuration()

            # Detect conflicts
            api.detect_conflicts()

            # Get system state
            state = await api.get_system_state()

            # Get context
            context = await api.get_context()

            # Store context in MCP memory
            self.server_manager.mcp_client.set("orchestra:context", context)

            # Return results
            return {
                "success": True,
                "resources_count": state.get("resources_count", 0),
                "configs_count": state.get("configs_count", 0),
                "conflicts_count": state.get("conflicts_count", 0),
            }

        except Exception as e:
            logger.error(f"Failed to sync Orchestra data to MCP: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_default_manager: Optional[MCPServerManager] = None


def get_manager() -> MCPServerManager:
    """Get the default MCP server manager.

    Returns:
        Default MCP server manager
    """
    global _default_manager

    if _default_manager is None:
        _default_manager = MCPServerManager()

    return _default_manager


def start_mcp_server() -> bool:
    """Start the MCP server.

    Returns:
        True if successful, False otherwise
    """
    return get_manager().start_server()


def stop_mcp_server() -> bool:
    """Stop the MCP server.

    Returns:
        True if successful, False otherwise
    """
    return get_manager().stop_server()


def restart_mcp_server() -> bool:
    """Restart the MCP server.

    Returns:
        True if successful, False otherwise
    """
    return get_manager().restart_server()


def check_mcp_server() -> bool:
    """Check if the MCP server is running.

    Returns:
        True if running, False otherwise
    """
    return get_manager().check_server_status()


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="MCP Server Management")
    parser.add_argument("--start", action="store_true", help="Start MCP server")
    parser.add_argument("--stop", action="store_true", help="Stop MCP server")
    parser.add_argument("--restart", action="store_true", help="Restart MCP server")
    parser.add_argument("--check", action="store_true", help="Check server status")
    parser.add_argument("--sync", action="store_true", help="Sync Orchestra data to MCP memory")
    parser.add_argument("--info", action="store_true", help="Get server info")
    parser.add_argument("--export", metavar="PATH", help="Export memory to file")
    parser.add_argument("--import", dest="import_path", metavar="PATH", help="Import memory from file")
    parser.add_argument("--sync-from", metavar="HOST:PORT", help="Sync memory from another MCP server")
    parser.add_argument(
        "--format",
        choices=["json", "binary", "auto"],
        default="auto",
        help="Import/export format",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing keys")

    args = parser.parse_args()

    manager = get_manager()

    # If no arguments provided, default to showing server info
    if not any(
        [
            args.start,
            args.stop,
            args.restart,
            args.check,
            args.sync,
            args.info,
            args.export,
            args.import_path,
            getattr(args, "sync_from", None),
        ]
    ):
        args.info = True

    # Start server
    if args.start:
        if manager.start_server():
            print("MCP server started successfully")
        else:
            print("Failed to start MCP server")
            sys.exit(1)

    # Stop server
    if args.stop:
        if manager.stop_server():
            print("MCP server stopped successfully")
        else:
            print("Failed to stop MCP server")
            sys.exit(1)

    # Restart server
    if args.restart:
        if manager.restart_server():
            print("MCP server restarted successfully")
        else:
            print("Failed to restart MCP server")
            sys.exit(1)

    # Check server status
    if args.check:
        if manager.check_server_status():
            print(f"MCP server is running at {manager.config.host}:{manager.config.port}")
        else:
            print("MCP server is not running")
            sys.exit(1)

    # Sync Orchestra data to MCP memory
    if args.sync:
        helper = MCPIntegrationHelper(manager)
        results = await helper.sync_orchestra_data_to_mcp()

        if results.get("success", False):
            print(f"Orchestra data synchronized to MCP memory:")
            print(f"  - {results.get('resources_count', 0)} resources")
            print(f"  - {results.get('configs_count', 0)} configurations")
            print(f"  - {results.get('conflicts_count', 0)} conflicts")
        else:
            print(f"Failed to sync Orchestra data to MCP memory: {results.get('error')}")
            sys.exit(1)

    # Get server info
    if args.info:
        if manager.check_server_status():
            info = manager.get_server_info()
            print(f"MCP server info:")
            print(f"  - Host: {info['host']}")
            print(f"  - Port: {info['port']}")
            print(f"  - Running: {info['is_running']}")
            print(f"  - External: {info['is_external']}")
            print(f"  - Memory backend: {info['memory_backend']}")
            print(f"  - Memory keys: {info['memory_keys_count']}")

            if "uptime" in info:
                print(f"  - Uptime: {info['uptime']:.2f} seconds")

            if "stats" in info:
                print(f"  - Stats: {info['stats']}")
        else:
            print("MCP server is not running")

    # Export memory
    if args.export:
        if manager.export_memory(args.export, format=args.format):
            print(f"Memory exported to {args.export}")
        else:
            print("Failed to export memory")
            sys.exit(1)

    # Import memory
    if args.import_path:
        if manager.import_memory(args.import_path, format=args.format, overwrite=args.overwrite):
            print(f"Memory imported from {args.import_path}")
        else:
            print("Failed to import memory")
            sys.exit(1)

    # Sync memory from another MCP server
    if getattr(args, "sync_from", None):
        # Parse host:port
        sync_from = getattr(args, "sync_from")
        if ":" in sync_from:
            source_host, source_port = sync_from.split(":", 1)
            source_port = int(source_port)
        else:
            source_host = sync_from
            source_port = DEFAULT_MCP_PORT

        # Sync memory
        results = await manager.sync_memory(
            source_host=source_host,
            source_port=source_port,
            overwrite=args.overwrite,
        )

        if results.get("success", False):
            print(f"Memory synchronized from {source_host}:{source_port}:")
            print(f"  - {len(results.get('synced', []))} keys synchronized")
            print(f"  - {len(results.get('skipped', []))} keys skipped")
            print(f"  - {len(results.get('failed', []))} keys failed")
        else:
            print(f"Failed to sync memory: {results.get('error')}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
