#!/usr/bin/env python3
"""
Setup script for AI Orchestra System

This script initializes the AI Orchestra System, including:
1. Setting up necessary directories
2. Initializing the system components
3. Discovering resources in the current environment
4. Detecting and resolving conflicts
5. Creating initial configuration

Usage:
    python -m orchestra_system.setup [options]

Options:
    --init          Initialize the system (default)
    --discover      Discover resources
    --conflicts     Detect conflicts
    --config        Discover configuration
    --cleanup       Clean up artifacts (dry run by default)
    --apply         Apply cleanup (use with --cleanup)
    --integration   Set up MCP integration
    --gcp           Set up GCP integration
    --all           Run all operations
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("orchestra-setup")

# Add parent directory to path to import orchestra_system
parent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(parent_dir))

# Import orchestra_system components
try:
    from orchestra_system.api import get_api, initialize_system
except ImportError as e:
    logger.error(f"Failed to import orchestra_system: {e}")
    logger.error("Make sure the package is installed or in your PYTHONPATH")
    sys.exit(1)


async def run_initialization() -> Dict[str, Any]:
    """Initialize the system.

    Returns:
        System state after initialization
    """
    logger.info("Initializing AI Orchestra System...")
    api = get_api()
    state = await api.initialize_system()
    logger.info(
        f"System initialized with {state.get('resources_count', 0)} resources, "
        f"{state.get('configs_count', 0)} configurations, and "
        f"{state.get('conflicts_count', 0)} conflicts"
    )
    return state


async def run_resource_discovery() -> List[Dict[str, Any]]:
    """Discover resources in the current environment.

    Returns:
        List of discovered resources
    """
    logger.info("Discovering resources...")
    api = get_api()
    resources = await api.discover_resources()
    logger.info(f"Discovered {len(resources)} resources")

    # Log resource types
    resource_types = {}
    for resource in resources:
        resource_type = resource.get("resource_type")
        if resource_type not in resource_types:
            resource_types[resource_type] = 0
        resource_types[resource_type] += 1

    for resource_type, count in resource_types.items():
        logger.info(f"  - {resource_type}: {count} resources")

    return resources


def run_config_discovery() -> int:
    """Discover configuration from various sources.

    Returns:
        Number of configuration entries discovered
    """
    logger.info("Discovering configuration...")
    api = get_api()
    count = api.discover_configuration()
    logger.info(f"Discovered {count} configuration entries")

    # Validate configuration
    valid, errors = api.validate_configuration()
    if valid:
        logger.info("Configuration is valid")
    else:
        logger.warning(f"Configuration has {len(errors)} errors:")
        for error in errors:
            logger.warning(f"  - {error}")

    return count


def run_conflict_detection(directory: str = ".") -> List[Dict[str, Any]]:
    """Detect conflicts in a directory.

    Args:
        directory: Directory to scan

    Returns:
        List of detected conflicts
    """
    logger.info(f"Detecting conflicts in {directory}...")
    api = get_api()
    conflicts = api.detect_conflicts(directory)
    logger.info(f"Detected {len(conflicts)} conflicts")

    # Log conflict types
    conflict_types = {}
    for conflict in conflicts:
        conflict_type = conflict.get("conflict_type")
        if conflict_type not in conflict_types:
            conflict_types[conflict_type] = 0
        conflict_types[conflict_type] += 1

    for conflict_type, count in conflict_types.items():
        logger.info(f"  - {conflict_type}: {count} conflicts")

    return conflicts


async def run_cleanup(apply: bool = False) -> Dict[str, Any]:
    """Clean up development artifacts.

    Args:
        apply: Whether to actually delete files

    Returns:
        Cleanup report
    """
    logger.info("Cleaning up development artifacts...")
    api = get_api()
    report = await api.cleanup_artifacts(dry_run=not apply)

    if apply:
        logger.info(f"Deleted {report.get('files_deleted', 0)} files")
    else:
        logger.info(f"Found {report.get('files_found', 0)} files to clean up (dry run)")

    return report


async def setup_mcp_integration() -> bool:
    """Set up MCP integration.

    Returns:
        True if successful, False otherwise
    """
    logger.info("Setting up MCP integration...")

    try:
        # Check for MCP client
        try:
            from gcp_migration.mcp_client_enhanced import MCPClient, get_client

            logger.info("Using enhanced MCP client")
        except ImportError:
            try:
                from gcp_migration.mcp_client import MCPClient, get_client

                logger.info("Using basic MCP client")
            except ImportError:
                logger.error("MCP client not found")
                return False

        # Get MCP client
        mcp_client = get_client()
        if not mcp_client:
            logger.error("Failed to get MCP client")
            return False

        # Get API with MCP client
        api = get_api(mcp_client=mcp_client, force_new=True)

        # Initialize system
        state = await api.initialize_system()
        logger.info("MCP integration set up successfully")

        return True

    except Exception as e:
        logger.error(f"Failed to set up MCP integration: {e}")
        return False


async def setup_gcp_integration() -> bool:
    """Set up GCP integration.

    Returns:
        True if successful, False otherwise
    """
    logger.info("Setting up GCP integration...")

    try:
        # Check for GCP client libraries
        try:
            import google.cloud.storage
            import google.cloud.aiplatform

            logger.info("GCP client libraries found")
        except ImportError:
            logger.error("GCP client libraries not found")
            logger.error(
                "Install them with: pip install google-cloud-storage google-cloud-aiplatform"
            )
            return False

        # Check GCP authentication
        import subprocess

        result = subprocess.run(
            ["gcloud", "auth", "list"], capture_output=True, text=True
        )

        if result.returncode != 0:
            logger.error("Failed to check GCP authentication")
            logger.error(result.stderr)
            return False

        # Get API
        api = get_api()

        # Discover GCP resources
        resources = await api.get_resources(resource_type="gcp_service")
        logger.info(f"Found {len(resources)} GCP resources")

        # Verify GCP resources
        statuses = await api.verify_resources()
        available = sum(1 for status in statuses.values() if status == "available")
        logger.info(f"{available} out of {len(statuses)} resources are available")

        return True

    except Exception as e:
        logger.error(f"Failed to set up GCP integration: {e}")
        return False


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AI Orchestra System Setup")
    parser.add_argument("--init", action="store_true", help="Initialize the system")
    parser.add_argument("--discover", action="store_true", help="Discover resources")
    parser.add_argument("--conflicts", action="store_true", help="Detect conflicts")
    parser.add_argument("--config", action="store_true", help="Discover configuration")
    parser.add_argument("--cleanup", action="store_true", help="Clean up artifacts")
    parser.add_argument("--apply", action="store_true", help="Apply cleanup")
    parser.add_argument(
        "--integration", action="store_true", help="Set up MCP integration"
    )
    parser.add_argument("--gcp", action="store_true", help="Set up GCP integration")
    parser.add_argument("--all", action="store_true", help="Run all operations")
    parser.add_argument("--output", help="Output file for results")

    args = parser.parse_args()

    # If no arguments provided, default to init
    if not any(
        [
            args.init,
            args.discover,
            args.conflicts,
            args.config,
            args.cleanup,
            args.integration,
            args.gcp,
            args.all,
        ]
    ):
        args.init = True

    # If --all is specified, enable all options
    if args.all:
        args.init = True
        args.discover = True
        args.conflicts = True
        args.config = True
        args.cleanup = True
        args.integration = True
        args.gcp = True

    results = {}

    # Run operations
    if args.init:
        results["init"] = await run_initialization()

    if args.discover:
        results["resources"] = await run_resource_discovery()

    if args.config:
        results["config_count"] = run_config_discovery()

    if args.conflicts:
        results["conflicts"] = run_conflict_detection()

    if args.cleanup:
        results["cleanup"] = await run_cleanup(apply=args.apply)

    if args.integration:
        results["mcp_integration"] = await setup_mcp_integration()

    if args.gcp:
        results["gcp_integration"] = await setup_gcp_integration()

    # Save results if output file specified
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.output}")

    logger.info("Setup completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
