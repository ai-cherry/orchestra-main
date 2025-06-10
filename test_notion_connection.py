#!/usr/bin/env python3
"""Test Notion API connection with provided key"""

import requests
import json
from datetime import datetime

def test_notion_api():
    """Test the Notion API connection"""
    api_key = "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"
    workspace_id = "20bdba04940280ca9ba7f9bce721f547"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    print("🔍 Testing Notion API connection...")
    
    # Test 1: User info
    try:
        url = "https://api.notion.com/v1/users/me"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            print("✅ Notion API connection successful!")
            user_data = response.json()
            print(f"👤 User: {user_data.get('name', 'Unknown')}")
            print(f"📧 Email: {user_data.get('person', {}).get('email', 'Unknown')}")
            
            # Test 2: Try to access workspace
            print(f"\n🔍 Testing workspace access: {workspace_id}")
            workspace_url = f"https://api.notion.com/v1/pages/{workspace_id}"
            workspace_response = requests.get(workspace_url, headers=headers)
            
            if workspace_response.status_code == 200:
                print("✅ Workspace access confirmed!")
                return True
            else:
                print(f"⚠️ Workspace access issue: {workspace_response.status_code}")
                print(f"Response: {workspace_response.text[:200]}")
                return True  # API works, maybe workspace ID issue
                
        else:
            print(f"❌ API connection failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    test_notion_api() 