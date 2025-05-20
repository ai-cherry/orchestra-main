"""
Toggle between standard mode and recovery mode by patching the core/orchestrator/src/main.py module directly.
This script runs before the application starts and modifies the in-memory module.

IMPORTANT: This script has been modified to always force standard mode regardless of input parameters.
"""

import sys
import importlib
import os
import argparse


def patch_module(use_recovery_mode=False):
    """
    Patch the core.orchestrator.src.main module to set the desired mode

    Args:
        use_recovery_mode: Parameter is ignored - always forces standard mode
    """
    # Override requested mode - ALWAYS use standard mode
    use_recovery_mode = False

    # First, ensure the Python path includes the project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    # Set environment variables based on desired mode
    os.environ["USE_RECOVERY_MODE"] = "false"
    os.environ["STANDARD_MODE"] = "true"
    os.environ["PYTHONPATH"] = script_dir

    # Reload the main module to ensure it picks up these changes
    if "core.orchestrator.src.main" in sys.modules:
        # Force reload the module if it's already loaded
        importlib.reload(sys.modules["core.orchestrator.src.main"])
    else:
        # Import it for the first time
        try:
            importlib.import_module("core.orchestrator.src.main")
        except ModuleNotFoundError:
            print(
                "Warning: core.orchestrator.src.main module not found. This is normal during container setup."
            )

    # Try to directly patch the module variables
    try:
        import core.orchestrator.src.main

        core.orchestrator.src.main.RECOVERY_MODE = False
        core.orchestrator.src.main.STANDARD_MODE = True
        print("Successfully patched core.orchestrator.src.main module variables")
    except (ModuleNotFoundError, AttributeError):
        print(
            "Note: Could not patch core.orchestrator.src.main directly. Environment variables still set."
        )

    print(f"=== FORCE STANDARD MODE ACTIVE ===")
    print(f"Environment variables set: USE_RECOVERY_MODE=false, STANDARD_MODE=true")
    print("=================================")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Toggle between standard and recovery modes"
    )
    parser.add_argument(
        "--recovery",
        action="store_true",
        help="Use recovery mode (DISABLED - will always use standard mode)",
    )
    parser.add_argument(
        "--standard", action="store_true", help="Use standard mode (default)"
    )

    args = parser.parse_args()

    # Always use standard mode regardless of arguments
    patch_module(False)
