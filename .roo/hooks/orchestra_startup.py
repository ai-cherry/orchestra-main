#!/usr/bin/env python3
# Auto-generated Orchestra AI integration hook for Roo

import os
import sys
from pathlib import Path

# Add Orchestra AI to Python path
orchestra_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(orchestra_path))

# Import and initialize Orchestra integration
try:
    from mcp_server.roo.orchestra_integration import orchestra_roo
    print("🎭 Orchestra AI integration loaded for Roo")
    
    # Make it available globally
    import builtins
    builtins.orchestra_ai = orchestra_roo
    
except Exception as e:
    print(f"Warning: Could not load Orchestra AI integration: {e}")
