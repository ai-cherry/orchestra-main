#!/usr/bin/env python3
"""
🍒 Notion Setup Helper - Step-by-Step Database Creation
Guides you through creating the perfect Cherry AI development dashboard
"""

import requests
import json
from datetime import datetime
import os

def test_connection():
    """Test Notion API connection"""
    token = os.getenv('NOTION_API_TOKEN')
    if not token:
        print("❌ NOTION_API_TOKEN not found. Run: source .env")
        return False
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Notion-Version': '2022-06-28'
    }
    
    try:
        response = requests.get('https://api.notion.com/v1/users', headers=headers)
        if response.status_code == 200:
            print("✅ Notion API connection verified!")
            return True
        else:
            print(f"❌ API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def create_database_with_parent_id(parent_page_id):
    """Create the Cherry AI database under a specific parent page"""
    
    token = os.getenv('NOTION_API_TOKEN')
    headers = {
        'Authorization': f'Bearer {token}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    print(f'\n🗃️ Creating Cherry AI Development Database under page {parent_page_id}...')
    
    database_data = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": "🍒 Cherry AI Development Log"}}],
        "properties": {
            "Title": {"title": {}},
            "Date": {"date": {}},
            "Type": {
                "select": {
                    "options": [
                        {"name": "Mockup Report", "color": "blue"},
                        {"name": "Screenshot", "color": "green"}, 
                        {"name": "Daily Status", "color": "yellow"},
                        {"name": "Build Report", "color": "purple"},
                        {"name": "System Health", "color": "red"},
                        {"name": "GitHub Action", "color": "gray"},
                        {"name": "Live Test", "color": "pink"}
                    ]
                }
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Generated", "color": "green"},
                        {"name": "In Progress", "color": "yellow"},
                        {"name": "Complete", "color": "blue"},
                        {"name": "Failed", "color": "red"},
                        {"name": "Live", "color": "purple"}
                    ]
                }
            },
            "Mockup Count": {"number": {}},
            "Build Time": {"number": {}},
            "File Size": {"rich_text": {}},
            "Notes": {"rich_text": {}},
            "URLs": {"rich_text": {}},
            "Priority": {
                "select": {
                    "options": [
                        {"name": "High", "color": "red"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "gray"}
                    ]
                }
            },
            "Source": {"rich_text": {}},
            "Environment": {
                "select": {
                    "options": [
                        {"name": "Local", "color": "blue"},
                        {"name": "GitHub Actions", "color": "purple"},
                        {"name": "Production", "color": "red"}
                    ]
                }
            }
        }
    }
    
    try:
        response = requests.post('https://api.notion.com/v1/databases', headers=headers, json=database_data)
        
        if response.status_code == 200:
            db_id = response.json()['id']
            print(f'🎉 SUCCESS! Created Cherry AI Development Database!')
            print(f'📄 Database ID: {db_id}')
            print(f'🔗 Database URL: https://notion.so/{db_id.replace("-", "")}')
            
            # Update .env file
            with open('.env', 'w') as f:
                f.write(f'NOTION_API_TOKEN={token}\n')
                f.write(f'NOTION_DATABASE_ID={db_id}\n')
            
            print(f'✅ Updated .env file with new database ID')
            return db_id
        else:
            print(f'❌ Failed to create database: {response.status_code}')
            print(f'Response: {response.text}')
            return None
            
    except Exception as e:
        print(f'❌ Error creating database: {e}')
        return None

def create_initial_entries(database_id):
    """Create initial entries to demonstrate the system"""
    
    token = os.getenv('NOTION_API_TOKEN')
    headers = {
        'Authorization': f'Bearer {token}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    print(f'\n🎯 Creating initial development log entries...')
    
    initial_entries = [
        {
            "Title": "🎉 LIVE: Cherry AI Development Dashboard Created!",
            "Type": "Live Test",
            "Status": "Live",
            "Mockup Count": 9,
            "Build Time": 0,
            "File Size": "Complete",
            "Notes": "✅ SUCCESS! Your Notion integration is now LIVE and working perfectly! This entry was created automatically by the Cherry AI system. All automation scripts are connected and ready.",
            "URLs": "http://localhost:8001/mockups-index.html | GitHub Actions Ready",
            "Priority": "High",
            "Source": "Live API Integration",
            "Environment": "Local"
        },
        {
            "Title": "🚀 Mockup Automation System Deployed",
            "Type": "Mockup Report",
            "Status": "Complete",
            "Mockup Count": 9,
            "Build Time": 15,
            "File Size": "450KB total",
            "Notes": "All mockup variants ready: Enhanced Production Interface (108KB), AI Tools Dashboard (40KB), Chat Interface (36KB), and 6 others. Gallery accessible at localhost:8001.",
            "URLs": "Enhanced Production, AI Tools, Chat, Index, Working variants",
            "Priority": "High",
            "Source": "mockup-automation.sh",
            "Environment": "Local"
        },
        {
            "Title": "📸 Screenshot Generation Pipeline Ready",
            "Type": "Screenshot",
            "Status": "Complete",
            "Mockup Count": 8,
            "Build Time": 30,
            "File Size": "~2MB",
            "Notes": "Puppeteer-based automated screenshot generation with metadata tracking. Enhanced script includes load time metrics and automatic Notion upload integration.",
            "URLs": "screenshots/ directory | Puppeteer automation",
            "Priority": "Medium",
            "Source": "mockup-automation-enhanced.sh",
            "Environment": "Local"
        },
        {
            "Title": "🔧 GitHub Actions Workflows Configured",
            "Type": "GitHub Action", 
            "Status": "Generated",
            "Mockup Count": 0,
            "Build Time": 0,
            "File Size": "2 workflows",
            "Notes": "Auto-mockups.yml and notion-daily-report.yml ready. Will automatically generate mockups on commits and send daily status reports to this Notion database.",
            "URLs": ".github/workflows/auto-mockups.yml | .github/workflows/notion-daily-report.yml",
            "Priority": "High",
            "Source": "GitHub Actions",
            "Environment": "GitHub Actions"
        },
        {
            "Title": "📋 Patrick Instructions System Protected",
            "Type": "System Health",
            "Status": "Complete", 
            "Mockup Count": 0,
            "Build Time": 0,
            "File Size": "Protected",
            "Notes": "Critical workflow instructions stored in .patrick/ directory with read-only protection. Searchable by 'Patrick Instructions' for emergency recovery and human-operated processes.",
            "URLs": ".patrick/README.md | Emergency procedures documented",
            "Priority": "Medium",
            "Source": "Protection System",
            "Environment": "Local"
        }
    ]
    
    created_count = 0
    
    for entry in initial_entries:
        entry_data = {
            "parent": {"database_id": database_id},
            "properties": {
                "Title": {"title": [{"text": {"content": entry["Title"]}}]},
                "Date": {"date": {"start": datetime.now().date().isoformat()}},
                "Type": {"select": {"name": entry["Type"]}},
                "Status": {"select": {"name": entry["Status"]}},
                "Mockup Count": {"number": entry["Mockup Count"]},
                "Build Time": {"number": entry["Build Time"]},
                "File Size": {"rich_text": [{"text": {"content": entry["File Size"]}}]},
                "Notes": {"rich_text": [{"text": {"content": entry["Notes"]}}]},
                "URLs": {"rich_text": [{"text": {"content": entry["URLs"]}}]},
                "Priority": {"select": {"name": entry["Priority"]}},
                "Source": {"rich_text": [{"text": {"content": entry["Source"]}}]},
                "Environment": {"select": {"name": entry["Environment"]}}
            }
        }
        
        try:
            response = requests.post('https://api.notion.com/v1/pages', headers=headers, json=entry_data)
            
            if response.status_code == 200:
                created_count += 1
                print(f'  ✅ Created: {entry["Title"][:60]}...')
            else:
                print(f'  ❌ Failed: {entry["Title"][:30]}... - {response.status_code}')
                
        except Exception as e:
            print(f'  ❌ Error: {e}')
    
    print(f'\n🎉 Created {created_count}/{len(initial_entries)} initial entries!')
    return created_count

def guide_manual_setup():
    """Guide user through manual setup steps"""
    
    print('\n🎯 MANUAL SETUP REQUIRED')
    print('=' * 50)
    print()
    print('Since your Notion workspace is empty, please follow these steps:')
    print()
    print('1. 📝 Go to Notion: https://www.notion.so/')
    print('2. ➕ Create a new page:')
    print('   • Click "Add a page" or "+"')
    print('   • Title it: "🍒 Cherry AI Development Hub"')
    print('   • Leave it as a regular page (not database)')
    print()
    print('3. 🔗 Share with your integration:')
    print('   • Click "Share" in the top right')
    print('   • Click "Invite"') 
    print('   • Search for "Cherry AI Automation"')
    print('   • Give it "Full access"')
    print()
    print('4. 📋 Copy the page ID:')
    print('   • Copy the page URL')
    print('   • Page ID is the long string after notion.so/')
    print('   • Example: notion.so/abc123def456... → abc123def456... is the page ID')
    print()
    print('5. 🔄 Run this script again with your page ID:')
    print('   • python3 notion-setup-helper.py YOUR_PAGE_ID')
    print()

def main():
    """Main setup function"""
    
    print('🍒 Cherry AI Notion Setup Helper')
    print('=' * 50)
    
    # Test connection first
    if not test_connection():
        return
    
    # Check if page ID provided as argument
    import sys
    if len(sys.argv) > 1:
        page_id = sys.argv[1].replace('-', '').replace('https://notion.so/', '').replace('https://www.notion.so/', '')
        
        # Ensure proper format (add dashes back)
        if len(page_id) == 32 and '-' not in page_id:
            page_id = f"{page_id[:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:]}"
        
        print(f'\n🎯 Using page ID: {page_id}')
        
        # Create database under this page
        database_id = create_database_with_parent_id(page_id)
        
        if database_id:
            # Create initial entries
            created_count = create_initial_entries(database_id)
            
            print(f'\n' + '=' * 50)
            print(f'🎉 NOTION INTEGRATION COMPLETE!')
            print(f'📊 Database ID: {database_id}')
            print(f'📝 Initial entries: {created_count}')
            print(f'🔗 Access: https://notion.so/{database_id.replace("-", "")}')
            print(f'✅ .env file updated automatically')
            
            print(f'\n🚀 TEST YOUR INTEGRATION:')
            print(f'python3 test-notion-live.py')
            print(f'cd ../admin-interface && ./mockup-automation-enhanced.sh all')
        else:
            print(f'\n❌ Setup failed. Check the page ID and permissions.')
    else:
        # No page ID provided, guide through manual setup
        guide_manual_setup()

if __name__ == "__main__":
    main() 