#!/usr/bin/env python3
"""
🍒 Patrick Instructions - Notion API Integration
Auto-saves mockup reports, screenshots, and development notes to Notion

Usage:
    python3 notion-integration.py --mockup-report
    python3 notion-integration.py --screenshot-upload
    python3 notion-integration.py --daily-status
"""

import os
import json
import datetime
from typing import Dict, List, Optional
import requests
from pathlib import Path

class NotionIntegration:
    def __init__(self, notion_token: str = None, database_id: str = None):
        """Initialize Notion integration with API credentials"""
        self.notion_token = notion_token or os.getenv('NOTION_API_TOKEN')
        self.database_id = database_id or os.getenv('NOTION_DATABASE_ID')
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def upload_mockup_report(self) -> Dict:
        """Upload mockup generation report to Notion"""
        try:
            # Collect mockup data
            mockup_data = self._collect_mockup_data()
            
            # Create Notion page
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": {
                    "Title": {
                        "title": [{"text": {"content": f"Mockup Report - {datetime.date.today()}"}}]
                    },
                    "Date": {"date": {"start": datetime.date.today().isoformat()}},
                    "Type": {"select": {"name": "Mockup Report"}},
                    "Status": {"select": {"name": "Generated"}},
                    "Mockup Count": {"number": mockup_data['count']},
                    "Total Size": {"rich_text": [{"text": {"content": mockup_data['total_size']}}]}
                },
                "children": self._create_mockup_content(mockup_data)
            }
            
            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=page_data
            )
            
            return {"success": True, "page_id": response.json().get("id")}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def upload_screenshot(self, screenshot_path: str, mockup_name: str) -> Dict:
        """Upload screenshot to Notion with metadata"""
        try:
            # Upload file to Notion
            # Note: Notion doesn't support direct file uploads via API
            # You'd need to upload to a service like S3 first, then link
            
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": {
                    "Title": {
                        "title": [{"text": {"content": f"Screenshot: {mockup_name}"}}]
                    },
                    "Date": {"date": {"start": datetime.date.today().isoformat()}},
                    "Type": {"select": {"name": "Screenshot"}},
                    "Mockup Name": {"rich_text": [{"text": {"content": mockup_name}}]},
                    "File Path": {"rich_text": [{"text": {"content": screenshot_path}}]}
                }
            }
            
            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=page_data
            )
            
            return {"success": True, "page_id": response.json().get("id")}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_daily_status(self) -> Dict:
        """Create daily status report in Notion"""
        try:
            # Check server health
            server_status = self._check_server_health()
            
            # Collect system metrics
            system_metrics = self._collect_system_metrics()
            
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": {
                    "Title": {
                        "title": [{"text": {"content": f"Daily Status - {datetime.date.today()}"}}]
                    },
                    "Date": {"date": {"start": datetime.date.today().isoformat()}},
                    "Type": {"select": {"name": "Daily Status"}},
                    "Server Status": {"select": {"name": server_status}},
                    "Mockup Count": {"number": system_metrics['mockup_count']}
                },
                "children": [
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {"rich_text": [{"text": {"content": "System Health"}}]}
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": f"Mockup Server: {server_status}"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": f"Available Mockups: {system_metrics['mockup_count']}"}}]
                        }
                    }
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=page_data
            )
            
            return {"success": True, "page_id": response.json().get("id")}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _collect_mockup_data(self) -> Dict:
        """Collect mockup file information"""
        admin_interface_path = Path("../admin-interface")
        
        if not admin_interface_path.exists():
            admin_interface_path = Path("./")
        
        mockups = []
        total_size = 0
        
        for html_file in admin_interface_path.glob("*.html"):
            if html_file.name != "index.html":
                size = html_file.stat().st_size
                total_size += size
                mockups.append({
                    "name": html_file.name,
                    "size": size,
                    "size_human": f"{size // 1024}KB",
                    "modified": datetime.datetime.fromtimestamp(html_file.stat().st_mtime)
                })
        
        return {
            "mockups": mockups,
            "count": len(mockups),
            "total_size": f"{total_size // 1024}KB"
        }
    
    def _create_mockup_content(self, mockup_data: Dict) -> List[Dict]:
        """Create Notion content blocks for mockup data"""
        blocks = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "Available Mockups"}}]}
            }
        ]
        
        for mockup in mockup_data['mockups']:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": f"• {mockup['name']} ({mockup['size_human']})"}}
                    ]
                }
            })
        
        return blocks
    
    def _check_server_health(self) -> str:
        """Check if mockup server is running"""
        try:
            response = requests.get("http://localhost:8001/mockups-index.html", timeout=5)
            return "Healthy" if response.status_code == 200 else "Error"
        except:
            return "Offline"
    
    def _collect_system_metrics(self) -> Dict:
        """Collect system metrics"""
        admin_interface_path = Path("../admin-interface")
        if not admin_interface_path.exists():
            admin_interface_path = Path("./")
        
        mockup_count = len(list(admin_interface_path.glob("*.html"))) - 1  # Exclude index.html
        
        return {
            "mockup_count": mockup_count,
            "timestamp": datetime.datetime.now().isoformat()
        }

def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cherry AI Notion Integration")
    parser.add_argument("--mockup-report", action="store_true", help="Upload mockup report")
    parser.add_argument("--screenshot-upload", type=str, help="Upload screenshot file")
    parser.add_argument("--daily-status", action="store_true", help="Create daily status report")
    parser.add_argument("--setup", action="store_true", help="Setup Notion integration")
    
    args = parser.parse_args()
    
    if args.setup:
        print("🍒 Notion Integration Setup")
        print("\n1. Create a Notion integration at: https://www.notion.so/my-integrations")
        print("2. Create a database for Cherry AI logs")
        print("3. Share the database with your integration")
        print("4. Set environment variables:")
        print("   export NOTION_API_TOKEN='your_token_here'")
        print("   export NOTION_DATABASE_ID='your_database_id_here'")
        print("\n5. Test with: python3 notion-integration.py --daily-status")
        return
    
    # Check for required environment variables
    if not os.getenv('NOTION_API_TOKEN') or not os.getenv('NOTION_DATABASE_ID'):
        print("❌ Missing Notion credentials. Run --setup for instructions.")
        return
    
    notion = NotionIntegration()
    
    if args.mockup_report:
        result = notion.upload_mockup_report()
        if result['success']:
            print(f"✅ Mockup report uploaded to Notion: {result['page_id']}")
        else:
            print(f"❌ Failed to upload report: {result['error']}")
    
    elif args.screenshot_upload:
        mockup_name = Path(args.screenshot_upload).stem
        result = notion.upload_screenshot(args.screenshot_upload, mockup_name)
        if result['success']:
            print(f"✅ Screenshot uploaded to Notion: {result['page_id']}")
        else:
            print(f"❌ Failed to upload screenshot: {result['error']}")
    
    elif args.daily_status:
        result = notion.create_daily_status()
        if result['success']:
            print(f"✅ Daily status created in Notion: {result['page_id']}")
        else:
            print(f"❌ Failed to create status: {result['error']}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 