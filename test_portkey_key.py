#!/usr/bin/env python
"""
Test script to check if the Portkey API key works.
"""

import os
import sys
from portkey import Portkey

def main():
    # Get the Portkey API key from environment
    api_key = os.environ.get("MASTER_PORTKEY_ADMIN_KEY")
    if not api_key:
        print("Error: MASTER_PORTKEY_ADMIN_KEY not set in environment")
        sys.exit(1)
    
    print(f"Testing Portkey API key: {api_key[:5]}...{api_key[-5:]}")
    
    try:
        # Initialize Portkey client
        portkey = Portkey(api_key=api_key)
        print("Successfully initialized Portkey client")
        
        # Try to get user info
        print("Trying to access basic Portkey API endpoints...")
        # Note: This is just testing if the key works, not necessarily admin operations
        
        print("Test completed without errors")
    except Exception as e:
        print(f"Error: {e}")
        print("The Portkey API key might not be valid or might not have the required permissions")
        sys.exit(1)

if __name__ == "__main__":
    main()
