#!/usr/bin/env python3
"""
Activate Orchestra AI in current Roo session
Run this to enable Orchestra AI without restarting Roo
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("🎭 Activating Orchestra AI in current Roo session...")

try:
    # Import the integration
    from mcp_server.roo.orchestra_integration import orchestra_roo
    
    # Make it globally available
    import builtins
    builtins.orchestra_ai = orchestra_roo
    
    # Also inject into Roo's namespace if available
    if 'roo' in sys.modules:
        sys.modules['roo'].orchestra_ai = orchestra_roo
    
    print("✅ Orchestra AI is now active!")
    print("\nYou can now use Orchestra AI features:")
    print("  • All Roo operations are automatically enhanced")
    print("  • Access directly via: orchestra_ai")
    print("  • Check status: orchestra_ai.get_status()")
    print("  • Disable: orchestra_ai.disable_auto_mode()")
    print("  • Enable: orchestra_ai.enable_auto_mode()")
    
except Exception as e:
    print(f"❌ Failed to activate Orchestra AI: {e}")
    sys.exit(1)