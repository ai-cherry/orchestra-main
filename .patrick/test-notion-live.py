#!/usr/bin/env python3
"""
🍒 Live Notion API Test & Database ID Helper
Tests your actual Notion API connection and helps you get the database ID
"""

import os
import requests
import json
from datetime import datetime

def test_notion_api():
    """Test the Notion API connection with your actual credentials"""
    
    api_token = os.getenv('NOTION_API_TOKEN')
    
    if not api_token:
        print("❌ NOTION_API_TOKEN not found in environment")
        print("💡 Make sure you've run: source .env")
        return False
    
    print(f"🔑 Testing Notion API with token: {api_token[:20]}...")
    
    # Test API connection by listing users
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Notion-Version": "2022-06-28"
    }
    
    try:
        # Test basic API access
        response = requests.get("https://api.notion.com/v1/users", headers=headers)
        
        if response.status_code == 200:
            print("✅ Notion API connection successful!")
            users = response.json()
            print(f"📊 Found {len(users.get('results', []))} users in your workspace")
            return True
        else:
            print(f"❌ API test failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def search_databases():
    """Search for existing databases in your Notion workspace"""
    
    api_token = os.getenv('NOTION_API_TOKEN')
    
    if not api_token:
        print("❌ NOTION_API_TOKEN not found")
        return
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    # Search for databases
    search_data = {
        "filter": {
            "value": "database",
            "property": "object"
        }
    }
    
    try:
        response = requests.post(
            "https://api.notion.com/v1/search", 
            headers=headers, 
            json=search_data
        )
        
        if response.status_code == 200:
            results = response.json().get('results', [])
            print(f"\n📊 Found {len(results)} databases in your workspace:")
            
            if results:
                for i, db in enumerate(results):
                    db_id = db['id']
                    title = db.get('title', [{}])[0].get('plain_text', 'Untitled') if db.get('title') else 'Untitled'
                    print(f"  {i+1}. {title}")
                    print(f"     ID: {db_id}")
                    print(f"     URL: https://notion.so/{db_id.replace('-', '')}")
                    print()
                
                print("💡 To use one of these databases:")
                print("   1. Copy the database ID above")
                print("   2. Update your .env file: NOTION_DATABASE_ID=<database_id>")
                print("   3. Make sure the database is shared with your integration")
                
            else:
                print("   No databases found. You need to:")
                print("   1. Create a new database in Notion")
                print("   2. Share it with your 'Cherry AI Automation' integration") 
                print("   3. Copy the database ID from the URL")
                
        else:
            print(f"❌ Database search failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Search error: {e}")

def create_test_database():
    """Helper instructions for creating a test database"""
    
    print("\n🎯 Quick Database Setup Guide:")
    print()
    print("1. 📝 Go to Notion and create a new page")
    print("2. 🗃️ Type '/database' and select 'Table - Full page'")
    print("3. 📋 Name it 'Cherry AI Development Log'")
    print("4. ➕ Add these columns:")
    print("   • Title (already exists)")
    print("   • Date (type: Date)")
    print("   • Type (type: Select, options: Mockup Report, Screenshot, Daily Status)")
    print("   • Status (type: Select, options: Generated, In Progress, Complete)")
    print("   • Mockup Count (type: Number)")
    print("   • Notes (type: Text)")
    print()
    print("5. 🔗 Share with integration:")
    print("   • Click 'Share' button in top right")
    print("   • Click 'Invite' and search for 'Cherry AI Automation'")
    print("   • Give it full access")
    print()
    print("6. 📋 Copy database ID:")
    print("   • Copy the URL of your database page")
    print("   • Database ID is the long string after /database/")
    print("   • Example: notion.so/database/abc123... → abc123 is your ID")
    print()

def test_with_database():
    """Test actual database operations if database ID is available"""
    
    api_token = os.getenv('NOTION_API_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not api_token:
        print("❌ NOTION_API_TOKEN not found")
        return
    
    if not database_id or database_id == 'your_database_id_here':
        print("⚠️  NOTION_DATABASE_ID not configured")
        print("💡 Update your .env file with your actual database ID")
        return
    
    print(f"\n🧪 Testing database operations...")
    print(f"Database ID: {database_id}")
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    # Try to create a test entry
    test_entry = {
        "parent": {"database_id": database_id},
        "properties": {
            "Title": {
                "title": [{"text": {"content": f"🧪 Live API Test - {datetime.now().strftime('%Y-%m-%d %H:%M')}"}}]
            },
            "Date": {"date": {"start": datetime.now().date().isoformat()}},
            "Type": {"select": {"name": "Daily Status"}},
            "Status": {"select": {"name": "Generated"}},
            "Mockup Count": {"number": 9},
            "Notes": {"rich_text": [{"text": {"content": "✅ Live API test successful! Your Notion integration is working perfectly."}}]}
        }
    }
    
    try:
        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=test_entry
        )
        
        if response.status_code == 200:
            page_id = response.json().get('id')
            print("🎉 SUCCESS! Test entry created in your Notion database!")
            print(f"📄 Page ID: {page_id}")
            print("✅ Your Notion integration is working perfectly!")
            
            # Test the actual integration script
            print("\n🔧 Now testing the main integration script...")
            os.system("python3 notion-integration.py --daily-status")
            
        else:
            print(f"❌ Failed to create test entry: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 404:
                print("💡 This usually means:")
                print("   • Database ID is incorrect")
                print("   • Database not shared with your integration")
                
    except Exception as e:
        print(f"❌ Test error: {e}")

def main():
    """Main test function"""
    
    print("🍒 Live Notion API Testing & Setup")
    print("=" * 50)
    
    # Step 1: Test basic API connection
    if not test_notion_api():
        print("\n❌ Basic API test failed. Check your NOTION_API_TOKEN.")
        return
    
    # Step 2: Search for existing databases
    search_databases()
    
    # Step 3: Show setup instructions
    create_test_database()
    
    # Step 4: Test database operations if configured
    test_with_database()
    
    print("\n" + "=" * 50)
    print("🎯 NEXT STEPS:")
    print("1. If you don't have a database yet, follow the setup guide above")
    print("2. Update .env file with your database ID")
    print("3. Run this script again to test database operations")
    print("4. Your GitHub Actions will use the same credentials!")
    
if __name__ == "__main__":
    main() 