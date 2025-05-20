#!/usr/bin/env python3
"""
Verification Script for AI Orchestra GCP Migration Toolkit

This script verifies that all components of the GCP migration toolkit
are properly installed and functional.
"""

import importlib
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("verify-implementation")

# Add parent directory to the Python path
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Define components to verify
COMPONENTS = [
    ("MCP Client", "gcp_migration.mcp_client_enhanced", ["get_client"]),
    (
        "Hybrid Config",
        "gcp_migration.hybrid_config_enhanced",
        ["get_config", "Environment"],
    ),
    (
        "Circuit Breaker",
        "gcp_migration.circuit_breaker_enhanced",
        ["circuit_break", "async_circuit_break"],
    ),
    (
        "Migration Monitor",
        "gcp_migration.migration_monitor",
        ["get_monitor", "MigrationPhase"],
    ),
    (
        "Unified Executor",
        "gcp_migration.execute_unified_migration",
        ["MigrationExecutor"],
    ),
]

# Define environment variables to check
ENV_VARS = [
    ("GOOGLE_CLOUD_PROJECT", "GCP project ID"),
    ("GOOGLE_CLOUD_LOCATION", "GCP location"),
    ("DEPLOYMENT_ENV", "Deployment environment"),
]


def check_imports() -> List[Tuple[str, str, bool]]:
    """Check that all components can be imported.

    Returns:
        List of (component_name, module_name, success) tuples
    """
    results = []

    for name, module_name, symbols in COMPONENTS:
        try:
            module = importlib.import_module(module_name)

            # Check that required symbols exist
            missing_symbols = []
            for symbol in symbols:
                if not hasattr(module, symbol):
                    missing_symbols.append(symbol)

            if missing_symbols:
                logger.error(
                    f"Module {module_name} is missing symbols: {', '.join(missing_symbols)}"
                )
                results.append((name, module_name, False))
            else:
                logger.info(f"Successfully imported {name} ({module_name})")
                results.append((name, module_name, True))

        except ImportError as e:
            logger.error(f"Failed to import {name} ({module_name}): {e}")

            # Check if the original (non-enhanced) module exists
            if "_enhanced" in module_name:
                original_module = module_name.replace("_enhanced", "")
                try:
                    importlib.import_module(original_module)
                    logger.info(
                        f"Original module {original_module} exists, but enhanced version not found"
                    )
                except ImportError:
                    logger.error(f"Neither enhanced nor original module found")

            results.append((name, module_name, False))

    return results


def check_environment() -> Dict[str, str]:
    """Check environment variables.

    Returns:
        Dictionary of environment variable values
    """
    env_values = {}

    for var_name, description in ENV_VARS:
        value = os.environ.get(var_name)
        if value:
            logger.info(f"Environment variable {var_name} ({description}): {value}")
        else:
            logger.warning(f"Environment variable {var_name} ({description}) not set")

        env_values[var_name] = value

    return env_values


def test_hybrid_config() -> bool:
    """Test hybrid configuration.

    Returns:
        True if successful
    """
    try:
        # First try enhanced version
        module_name = "gcp_migration.hybrid_config_enhanced"
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            # Fall back to basic version
            module_name = "gcp_migration.hybrid_config"
            module = importlib.import_module(module_name)

        get_config = getattr(module, "get_config")
        Environment = getattr(module, "Environment")

        # Test basic functionality
        config = get_config(force_new=True)
        logger.info(f"Detected environment: {config.environment}")

        # Test endpoint resolution
        admin_endpoint = config.get_endpoint("admin-api")
        logger.info(f"Admin API endpoint: {admin_endpoint}")

        # Test project ID
        project_id = config.get("project_id")
        logger.info(f"Project ID: {project_id}")

        return True
    except Exception as e:
        logger.error(f"Error testing hybrid config: {e}")
        return False


def test_circuit_breaker() -> bool:
    """Test circuit breaker.

    Returns:
        True if successful
    """
    try:
        # First try enhanced version
        module_name = "gcp_migration.circuit_breaker_enhanced"
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            # Fall back to basic version
            module_name = "gcp_migration.circuit_breaker"
            module = importlib.import_module(module_name)

        circuit_break = getattr(module, "circuit_break")
        CircuitBreaker = getattr(module, "CircuitBreaker")

        # Test basic functionality
        @circuit_break(name="verify_test", failure_threshold=2)
        def test_function() -> str:
            """Test function."""
            return "success"

        result = test_function()
        logger.info(f"Circuit breaker test function result: {result}")

        # Get circuit breaker instance
        circuit = CircuitBreaker.get_breaker("verify_test")

        # Test state
        state = circuit.get_state()
        logger.info(f"Circuit state: {state['state']}")

        # Reset circuit
        circuit.reset()
        logger.info("Circuit reset successfully")

        return True
    except Exception as e:
        logger.error(f"Error testing circuit breaker: {e}")
        return False


def test_mcp_client() -> bool:
    """Test MCP client.

    Returns:
        True if successful
    """
    try:
        # First try enhanced version
        module_name = "gcp_migration.mcp_client_enhanced"
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            # Fall back to basic version
            module_name = "gcp_migration.mcp_client"
            module = importlib.import_module(module_name)

        get_client = getattr(module, "get_client")

        # Test basic functionality
        client = get_client(force_new=True)
        logger.info(f"MCP client initialized")

        return True
    except Exception as e:
        logger.error(f"Error testing MCP client: {e}")
        return False


def main() -> int:
    """Main function.

    Returns:
        Exit code
    """
    print("\n=== AI Orchestra GCP Migration Toolkit Verification ===\n")

    # Check imports
    print("\n--- Checking imports ---\n")
    import_results = check_imports()

    # Check environment
    print("\n--- Checking environment ---\n")
    env_values = check_environment()

    # Test components
    print("\n--- Testing components ---\n")

    print("\nTesting Hybrid Config:")
    config_result = test_hybrid_config()

    print("\nTesting Circuit Breaker:")
    circuit_result = test_circuit_breaker()

    print("\nTesting MCP Client:")
    mcp_result = test_mcp_client()

    # Print summary
    print("\n=== Verification Summary ===\n")

    # Import results
    print("Component Imports:")
    all_imports_ok = True
    for name, module, success in import_results:
        status = "✅ OK" if success else "❌ FAILED"
        print(f"  {status} - {name} ({module})")
        all_imports_ok = all_imports_ok and success

    # Test results
    print("\nComponent Tests:")
    print(f"  {'✅ OK' if config_result else '❌ FAILED'} - Hybrid Config")
    print(f"  {'✅ OK' if circuit_result else '❌ FAILED'} - Circuit Breaker")
    print(f"  {'✅ OK' if mcp_result else '❌ FAILED'} - MCP Client")

    all_tests_ok = config_result and circuit_result and mcp_result

    # Overall result
    print("\nOverall Result:")
    if all_imports_ok and all_tests_ok:
        print(
            "✅ All checks passed! The migration toolkit is properly installed and functional."
        )
        return 0
    else:
        print("❌ Some checks failed. See detailed output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
