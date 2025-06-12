#!/usr/bin/env python3
"""
Test Notion API Connection
"""

import requests
import os
from utils.fast_secrets import get_secret, notion_headers

# Use environment variable instead of hardcoded key
api_key = get_secret('NOTION_API_TOKEN')
if not api_key:
    print("❌ NOTION_API_TOKEN environment variable not set")
    print("💡 Set it with: export NOTION_API_TOKEN=your_token_here")
    exit(1)

workspace_id = get_secret('NOTION_WORKSPACE_ID') or "20bdba04940280ca9ba7f9bce721f547"
headers = notion_headers()

def test_notion_connection():
    """Test basic Notion API connectivity"""
    try:
        # Test API connectivity
        url = "https://api.notion.com/v1/users/me"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ Notion API connection successful!")
            print(f"📧 User: {user_data.get('name', 'Unknown')}")
            print(f"🆔 User ID: {user_data.get('id', 'Unknown')}")
            return True
        else:
            print(f"❌ Notion API connection failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Notion connection: {e}")
        return False

if __name__ == "__main__":
    print("🔗 Testing Notion API Connection...")
    test_notion_connection() 