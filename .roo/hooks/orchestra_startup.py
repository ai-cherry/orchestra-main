#!/usr/bin/env python3
# Auto-generated Cherry AI integration hook for Roo

import os
import sys
from pathlib import Path

# Add Cherry AI to Python path
cherry_ai_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(cherry_ai_path))

# Import and initialize cherry_ai integration
try:
    from mcp_server.roo.cherry_ai_integration import cherry_ai_roo
    print("🎭 Cherry AI integration loaded for Roo")
    
    # Make it available globally
    import builtins
    builtins.cherry_ai_ai = cherry_ai_roo
    
except Exception as e:
    print(f"Warning: Could not load Cherry AI integration: {e}")
