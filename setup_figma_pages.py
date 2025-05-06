#!/usr/bin/env python3
"""
setup_figma_pages.py - Creates standard page structure in a Figma file using the REST API.

Usage:
1. Run with PAT as an argument: python3 setup_figma_pages.py YOUR_FIGMA_PAT
   OR
   Set FIGMA_PAT environment variable: export FIGMA_PAT='your-token'
   Then run: python3 setup_figma_pages.py
"""

import os
import sys
import json
import time
import requests
from typing import List, Dict, Any, Optional, Tuple

# --- FILE_ID set to your Figma project ID ---
FILE_ID = '368236963'

# List of pages to create
PAGES_TO_CREATE = [
    '_Foundations & Variables',
    '_Core Components [Adapted]',
    'Web - Dashboard',
    'Web - Agents',
    'Web - Personas',
    'Web - Memory',
    'Web - Projects',
    'Web - Settings',
    'Web - TrainingGround',
    'Android - Core Screens',
    'Prototypes',
    'Archive'
]

def create_page(file_id: str, page_name: str, access_token: str) -> bool:
    """
    Create a single page in the Figma file.
    
    Args:
        file_id: Figma file ID
        page_name: Name of the page to create
        access_token: Figma Personal Access Token
        
    Returns:
        bool: True if successful, False otherwise
    """
    api_url = f"https://api.figma.com/v1/files/{file_id}/pages"
    
    print(f"📄 Attempting to create page: {page_name}...")
    
    headers = {
        'X-Figma-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    data = {
        'name': page_name
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data)
        
        if not response.ok:
            # Try to get detailed error info
            try:
                error_details = response.json()
                error_str = json.dumps(error_details)
            except:
                error_str = response.text
                
            print(f"   ❌ Failed: {response.status_code} {response.reason}. Details: {error_str}")
            return False
        else:
            print(f"   ✅ Success: Page '{page_name}' created.")
            return True
    except Exception as e:
        print(f"   ❌ Network or script error creating page '{page_name}': {str(e)}")
        return False

def main():
    print("🚀 Starting Figma page setup script...")
    
    # Try to get PAT from command line args first, then environment variable
    figma_pat = None
    if len(sys.argv) > 1:
        figma_pat = sys.argv[1]
        print("   Using Figma PAT from command line argument.")
    else:
        figma_pat = os.environ.get('FIGMA_PAT')
        if figma_pat:
            print("   Using Figma PAT from environment variable.")
    
    # Validate prerequisites
    if not figma_pat:
        print("❌ Error: Figma PAT not provided.")
        print("   Please provide it as a command line argument:")
        print("   python3 setup_figma_pages.py YOUR_FIGMA_PAT")
        print("   OR set the FIGMA_PAT environment variable:")
        print("   export FIGMA_PAT='your-token'")
        sys.exit(1)
    
    print(f"   Target Figma File ID: {FILE_ID}")
    print(f"   Pages to create: {len(PAGES_TO_CREATE)}")
    
    success_count = 0
    failure_count = 0
    
    # Loop through pages and attempt creation
    for page in PAGES_TO_CREATE:
        success = create_page(FILE_ID, page, figma_pat)
        if success:
            success_count += 1
        else:
            failure_count += 1
        
        # Add a small delay to avoid hitting API rate limits
        time.sleep(0.25)  # 250ms delay
    
    print("🏁 Page setup script finished.")
    print(f"   Summary: {success_count} pages created successfully, {failure_count} failed.")
    
    if failure_count > 0:
        print("⚠️ Please review errors above and potentially clean up/re-run if needed.")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"🚨 Unhandled error during script execution: {str(e)}")
        sys.exit(1)
