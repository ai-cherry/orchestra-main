"""
Force standard mode by patching the core/orchestrator/src/main.py module directly.
This script runs before the application starts and modifies the in-memory module.
"""

import sys
import importlib
import os

def patch_module():
    """
    Patch the core.orchestrator.src.main module to force standard mode
    """
    # First, ensure the Python path includes the project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    
    # Force environment variables
    os.environ["USE_RECOVERY_MODE"] = "false"
    os.environ["STANDARD_MODE"] = "true"
    os.environ["PYTHONPATH"] = script_dir
    
    # Reload the main module to ensure it picks up these changes
    if "core.orchestrator.src.main" in sys.modules:
        # Force reload the module if it's already loaded
        importlib.reload(sys.modules["core.orchestrator.src.main"])
    else:
        # Import it for the first time
        importlib.import_module("core.orchestrator.src.main")
    
    # Directly patch the module variables
    import core.orchestrator.src.main
    core.orchestrator.src.main.RECOVERY_MODE = False
    core.orchestrator.src.main.STANDARD_MODE = True
    
    print("=== FORCE STANDARD MODE ACTIVE ===")
    print("Patched core.orchestrator.src.main: RECOVERY_MODE=False, STANDARD_MODE=True")
    print("Environment variables set: USE_RECOVERY_MODE=false, STANDARD_MODE=true")
    print("=================================")

if __name__ == "__main__":
    patch_module()
