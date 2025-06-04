#!/usr/bin/env python3
"""
Activate Cherry AI in current Roo session
Run this to enable Cherry AI without restarting Roo
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("🎭 Activating Cherry AI in current Roo session...")

try:
    # Import the integration
    from mcp_server.roo.cherry_ai_integration import cherry_ai_roo
    
    # Make it globally available
    import builtins
    builtins.cherry_ai_ai = cherry_ai_roo
    
    # Also inject into Roo's namespace if available
    if 'roo' in sys.modules:
        sys.modules['roo'].cherry_ai_ai = cherry_ai_roo
    
    print("✅ Cherry AI is now active!")
    print("\nYou can now use Cherry AI features:")
    print("  • All Roo operations are automatically enhanced")
    print("  • Access directly via: cherry_ai_ai")
    print("  • Check status: cherry_ai_ai.get_status()")
    print("  • Disable: cherry_ai_ai.disable_auto_mode()")
    print("  • Enable: cherry_ai_ai.enable_auto_mode()")
    
except Exception as e:
    print(f"❌ Failed to activate Cherry AI: {e}")
    sys.exit(1)