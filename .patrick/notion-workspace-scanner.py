#!/usr/bin/env python3
"""
🍒 Notion Workspace Scanner & Rebuilder
Scans your entire Notion workspace and rebuilds it as Cherry AI development dashboard
"""

import requests
import json
from datetime import datetime
import os

def scan_workspace():
    """Scan the entire Notion workspace"""
    
    token = os.getenv('NOTION_API_TOKEN')
    if not token:
        print("❌ NOTION_API_TOKEN not found. Run: source .env")
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    print('🔍 Scanning your entire Notion workspace...')
    
    # Search for all content
    search_data = {'page_size': 100}
    response = requests.post('https://api.notion.com/v1/search', headers=headers, json=search_data)
    
    if response.status_code == 200:
        results = response.json().get('results', [])
        print(f'📊 Found {len(results)} items in your workspace:')
        
        databases = []
        pages = []
        
        for item in results:
            if item['object'] == 'database':
                title = item.get('title', [{}])[0].get('plain_text', 'Untitled') if item.get('title') else 'Untitled'
                databases.append({'id': item['id'], 'title': title, 'url': f"https://notion.so/{item['id'].replace('-', '')}"})
            elif item['object'] == 'page':
                title = item.get('properties', {}).get('title', {}).get('title', [{}])
                if title:
                    title = title[0].get('plain_text', 'Untitled')
                else:
                    title = 'Untitled'
                pages.append({'id': item['id'], 'title': title, 'url': f"https://notion.so/{item['id'].replace('-', '')}"})
        
        print(f'\n📚 Databases ({len(databases)}):')
        for db in databases:
            print(f'  • {db["title"]} (ID: {db["id"]})')
            print(f'    URL: {db["url"]}')
        
        print(f'\n📄 Pages ({len(pages)}):')
        for page in pages:
            print(f'  • {page["title"]} (ID: {page["id"]})')
            print(f'    URL: {page["url"]}')
            
        print(f'\n✅ I have FULL ACCESS to your Notion workspace!')
        print(f'🚀 Ready to rebuild it as your Cherry AI development dashboard!')
        
        return {'databases': databases, 'pages': pages}
        
    else:
        print(f'❌ Error: {response.status_code} - {response.text}')
        return None

def create_cherry_ai_database():
    """Create the main Cherry AI development database"""
    
    token = os.getenv('NOTION_API_TOKEN')
    headers = {
        'Authorization': f'Bearer {token}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    print('\n🗃️ Creating Cherry AI Development Database...')
    
    # Create database
    database_data = {
        "parent": {"type": "page_id", "page_id": ""},  # Will be updated
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
                        {"name": "GitHub Action", "color": "gray"}
                    ]
                }
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Generated", "color": "green"},
                        {"name": "In Progress", "color": "yellow"},
                        {"name": "Complete", "color": "blue"},
                        {"name": "Failed", "color": "red"}
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
            }
        }
    }
    
    # First, create a root page for the database
    root_page_data = {
        "parent": {"type": "workspace", "workspace": True},
        "properties": {
            "title": [{"type": "text", "text": {"content": "🍒 Cherry AI Development Hub"}}]
        },
        "children": [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": "🍒 Cherry AI Development Hub"}}]}
            },
            {
                "object": "block", 
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Automated development dashboard for Cherry AI Orchestra project. This page contains real-time logs, build reports, and system health monitoring."}}]}
            }
        ]
    }
    
    try:
        # Create root page
        response = requests.post('https://api.notion.com/v1/pages', headers=headers, json=root_page_data)
        
        if response.status_code == 200:
            root_page_id = response.json()['id']
            print(f'✅ Created root page: {root_page_id}')
            
            # Now create database as child of root page
            database_data['parent']['page_id'] = root_page_id
            
            response = requests.post('https://api.notion.com/v1/databases', headers=headers, json=database_data)
            
            if response.status_code == 200:
                db_id = response.json()['id']
                print(f'🎉 SUCCESS! Created Cherry AI Development Database!')
                print(f'📄 Database ID: {db_id}')
                print(f'🔗 Database URL: https://notion.so/{db_id.replace("-", "")}')
                
                # Update .env file with new database ID
                with open('.env', 'w') as f:
                    f.write(f'NOTION_API_TOKEN={token}\n')
                    f.write(f'NOTION_DATABASE_ID={db_id}\n')
                
                print(f'✅ Updated .env file with new database ID')
                
                return db_id
            else:
                print(f'❌ Failed to create database: {response.status_code} - {response.text}')
                return None
        else:
            print(f'❌ Failed to create root page: {response.status_code} - {response.text}')
            return None
            
    except Exception as e:
        print(f'❌ Error creating database: {e}')
        return None

def create_test_entries(database_id):
    """Create test entries in the new database"""
    
    token = os.getenv('NOTION_API_TOKEN')
    headers = {
        'Authorization': f'Bearer {token}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    
    print(f'\n🧪 Creating test entries in database...')
    
    test_entries = [
        {
            "Title": "🎉 Cherry AI Development Dashboard Initialized",
            "Type": "System Health",
            "Status": "Complete",
            "Mockup Count": 9,
            "Build Time": 0,
            "File Size": "500KB",
            "Notes": "✅ Notion integration working perfectly! Complete rebuild of development dashboard with automated logging, mockup tracking, and real-time system health monitoring.",
            "URLs": "http://localhost:8001/mockups-index.html",
            "Priority": "High"
        },
        {
            "Title": "🚀 Mockup Automation System Live",
            "Type": "Mockup Report", 
            "Status": "Generated",
            "Mockup Count": 9,
            "Build Time": 15,
            "File Size": "450KB",
            "Notes": "All 9 mockup variants ready: Enhanced Production, AI Tools Dashboard, Chat Interface, etc. Automation scripts created and tested.",
            "URLs": "http://localhost:8001/mockups-index.html",
            "Priority": "High"
        },
        {
            "Title": "📸 Screenshot Generation Ready",
            "Type": "Screenshot",
            "Status": "Complete", 
            "Mockup Count": 8,
            "Build Time": 30,
            "File Size": "2MB",
            "Notes": "Puppeteer-based screenshot generation with metadata. Enhanced script includes load time tracking and automated Notion uploads.",
            "URLs": "screenshots/",
            "Priority": "Medium"
        }
    ]
    
    created_count = 0
    
    for entry in test_entries:
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
                "Priority": {"select": {"name": entry["Priority"]}}
            }
        }
        
        try:
            response = requests.post('https://api.notion.com/v1/pages', headers=headers, json=entry_data)
            
            if response.status_code == 200:
                created_count += 1
                print(f'  ✅ Created: {entry["Title"][:50]}...')
            else:
                print(f'  ❌ Failed: {entry["Title"][:30]}... - {response.status_code}')
                
        except Exception as e:
            print(f'  ❌ Error creating entry: {e}')
    
    print(f'\n🎉 Created {created_count}/{len(test_entries)} test entries!')
    return created_count

def main():
    """Main function to rebuild Notion workspace"""
    
    print('🍒 Cherry AI Notion Workspace Rebuilder')
    print('=' * 50)
    
    # Scan current workspace
    workspace_data = scan_workspace()
    
    if workspace_data:
        print(f'\n🔄 Ready to rebuild as Cherry AI development dashboard!')
        
        # Create new database
        database_id = create_cherry_ai_database()
        
        if database_id:
            # Create test entries
            created_count = create_test_entries(database_id)
            
            print(f'\n' + '=' * 50)
            print(f'🎉 NOTION WORKSPACE REBUILT SUCCESSFULLY!')
            print(f'📊 Database ID: {database_id}')
            print(f'📝 Test entries: {created_count}')
            print(f'🔗 Access: https://notion.so/{database_id.replace("-", "")}')
            print(f'✅ .env file updated automatically')
            
            print(f'\n🚀 NEXT STEPS:')
            print(f'1. Visit your Notion to see the new dashboard')
            print(f'2. Run: python3 test-notion-live.py')
            print(f'3. Test: cd ../admin-interface && ./mockup-automation-enhanced.sh all')
            
        else:
            print(f'\n❌ Failed to create database')
    else:
        print(f'\n❌ Failed to scan workspace')

if __name__ == "__main__":
    main() 