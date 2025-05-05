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
    
    print("=== DEBUG: Environment Variables at Startup ===")
    for key, value in sorted(os.environ.items()):
        if key in ["ENVIRONMENT", "PYTHONPATH", "STANDARD_MODE", "USE_RECOVERY_MODE"]:
            print(f"{key}={value}")
    
    print("=== DEBUG: Python Path ===")
    for path in sys.path:
        print(path)
    print("=== DEBUG: End Environment Info ===")
    
    # Try to load the module
    try:
        # Reload the main module to ensure it picks up these changes
        if "core.orchestrator.src.main" in sys.modules:
            # Force reload the module if it's already loaded
            importlib.reload(sys.modules["core.orchestrator.src.main"])
        else:
            # Import it for the first time
            importlib.import_module("core.orchestrator.src.main")
        
        # Directly patch the module variables
        import core.orchestrator.src.main
        
        # Print debug info
        print(f"DEBUG: Environment would set RECOVERY_MODE={core.orchestrator.src.main.RECOVERY_MODE}")
        print(f"DEBUG: Environment would set STANDARD_MODE={core.orchestrator.src.main.STANDARD_MODE}")
        
        # Force override the mode
        core.orchestrator.src.main.RECOVERY_MODE = False
        core.orchestrator.src.main.STANDARD_MODE = True
        
        print(f"DEBUG: HARD OVERRIDE ACTIVE: RECOVERY_MODE=False, STANDARD_MODE=True")
        print(f"Starting with RECOVERY_MODE=False, STANDARD_MODE=True (HARD OVERRIDE)")
    except ImportError as e:
        print(f"Warning: Could not import core.orchestrator.src.main module: {e}")
        print("Will continue with environment variables only.")
    
    print("тЪая╕П APPLYING HARD OVERRIDE: Forcing standard mode and disabling recovery mode!")

if __name__ == "__main__":
    patch_module()
