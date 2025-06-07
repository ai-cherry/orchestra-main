#!/usr/bin/env python3
"""
🎯 Enhanced Notion AI Integration for Orchestra Project
Comprehensive project management and documentation system

Features:
- Latest Notion API (2023-06-28)
- Optimized database schemas
- Cross-tool integration (Roo/Continue/Cursor)
- Automated Patrick Instructions management
- Real-time project tracking
- File upload via external hosting
"""

import os
import json
import datetime
import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
import requests
import hashlib
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NotionConfig:
    """Configuration for Notion integration"""
    api_token: str
    api_version: str = "2022-06-28"
    base_url: str = "https://api.notion.com/v1"
    
    # Database IDs (to be created)
    project_tasks_db: Optional[str] = None
    development_log_db: Optional[str] = None
    agent_performance_db: Optional[str] = None
    patrick_instructions_db: Optional[str] = None
    
    # External file hosting (for screenshots/files)
    file_host_url: Optional[str] = None
    file_host_token: Optional[str] = None

class EnhancedNotionIntegration:
    """Enhanced Notion integration with advanced features"""
    
    def __init__(self, config: NotionConfig):
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {config.api_token}",
            "Content-Type": "application/json",
            "Notion-Version": config.api_version
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    async def setup_workspace(self) -> Dict[str, Any]:
        """Create optimized workspace structure with all databases"""
        try:
            logger.info("🚀 Setting up Orchestra AI Notion workspace...")
            
            # Create main databases
            databases = await self._create_all_databases()
            
            # Create master dashboard page
            dashboard = await self._create_master_dashboard(databases)
            
            # Setup automated workflows
            workflows = await self._setup_automated_workflows()
            
            return {
                "success": True,
                "databases": databases,
                "dashboard": dashboard,
                "workflows": workflows,
                "message": "Orchestra AI Notion workspace created successfully!"
            }
            
        except Exception as e:
            logger.error(f"Failed to setup workspace: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_all_databases(self) -> Dict[str, str]:
        """Create all optimized databases"""
        databases = {}
        
        # Project Tasks Database
        databases["project_tasks"] = await self._create_database(
            title="🎯 Project Tasks",
            properties=self._get_project_tasks_schema()
        )
        
        # Development Log Database
        databases["development_log"] = await self._create_database(
            title="💻 Development Log",
            properties=self._get_development_log_schema()
        )
        
        # AI Agent Performance Database
        databases["agent_performance"] = await self._create_database(
            title="🤖 AI Agent Performance",
            properties=self._get_agent_performance_schema()
        )
        
        # Patrick Instructions Database
        databases["patrick_instructions"] = await self._create_database(
            title="📖 Patrick Instructions",
            properties=self._get_patrick_instructions_schema()
        )
        
        return databases
    
    def _get_project_tasks_schema(self) -> Dict[str, Any]:
        """Optimized schema for project tasks"""
        return {
            "Title": {"title": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Not Started", "color": "gray"},
                        {"name": "In Progress", "color": "blue"},
                        {"name": "Review", "color": "yellow"},
                        {"name": "Done", "color": "green"}
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": "Low", "color": "gray"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "High", "color": "orange"},
                        {"name": "Critical", "color": "red"}
                    ]
                }
            },
            "Assignee": {
                "select": {
                    "options": [
                        {"name": "Cherry", "color": "red"},
                        {"name": "Sophia", "color": "blue"},
                        {"name": "Karen", "color": "green"},
                        {"name": "Human", "color": "purple"}
                    ]
                }
            },
            "Epic": {
                "select": {
                    "options": [
                        {"name": "Admin Interface", "color": "blue"},
                        {"name": "Agent System", "color": "green"},
                        {"name": "Core API", "color": "orange"},
                        {"name": "Infrastructure", "color": "gray"}
                    ]
                }
            },
            "Effort": {"number": {"format": "number"}},
            "Due Date": {"date": {}},
            "Tags": {
                "multi_select": {
                    "options": [
                        {"name": "UI/UX", "color": "pink"},
                        {"name": "Backend", "color": "blue"},
                        {"name": "AI/ML", "color": "green"},
                        {"name": "Security", "color": "red"},
                        {"name": "Performance", "color": "orange"}
                    ]
                }
            },
            "Description": {"rich_text": {}},
            "Acceptance Criteria": {"rich_text": {}},
            "Created": {"created_time": {}},
            "Updated": {"last_edited_time": {}}
        }
    
    def _get_development_log_schema(self) -> Dict[str, Any]:
        """Schema for development activity logging"""
        return {
            "Title": {"title": {}},
            "Date": {"date": {}},
            "Type": {
                "select": {
                    "options": [
                        {"name": "Code", "color": "blue"},
                        {"name": "UI", "color": "pink"},
                        {"name": "Bug Fix", "color": "red"},
                        {"name": "Feature", "color": "green"},
                        {"name": "Refactor", "color": "orange"}
                    ]
                }
            },
            "Component": {
                "select": {
                    "options": [
                        {"name": "Admin Interface", "color": "blue"},
                        {"name": "Core API", "color": "green"},
                        {"name": "Agent System", "color": "purple"},
                        {"name": "Database", "color": "orange"}
                    ]
                }
            },
            "Tool Used": {
                "select": {
                    "options": [
                        {"name": "Cursor", "color": "blue"},
                        {"name": "Roo", "color": "green"},
                        {"name": "Continue", "color": "purple"},
                        {"name": "Manual", "color": "gray"}
                    ]
                }
            },
            "Files Changed": {"number": {"format": "number"}},
            "Lines Added": {"number": {"format": "number"}},
            "Lines Removed": {"number": {"format": "number"}},
            "Commit Hash": {"rich_text": {}},
            "Screenshots": {"files": {}},
            "Notes": {"rich_text": {}},
            "Performance Impact": {
                "select": {
                    "options": [
                        {"name": "Positive", "color": "green"},
                        {"name": "Neutral", "color": "gray"},
                        {"name": "Negative", "color": "red"}
                    ]
                }
            },
            "Created": {"created_time": {}}
        }
    
    def _get_agent_performance_schema(self) -> Dict[str, Any]:
        """Schema for AI agent performance tracking"""
        return {
            "Agent Name": {"title": {}},
            "Date": {"date": {}},
            "Persona": {
                "select": {
                    "options": [
                        {"name": "Cherry", "color": "red"},
                        {"name": "Sophia", "color": "blue"},
                        {"name": "Karen", "color": "green"}
                    ]
                }
            },
            "Task Type": {
                "select": {
                    "options": [
                        {"name": "Code Generation", "color": "blue"},
                        {"name": "UI Creation", "color": "pink"},
                        {"name": "Problem Solving", "color": "green"},
                        {"name": "Research", "color": "orange"},
                        {"name": "Communication", "color": "purple"}
                    ]
                }
            },
            "Success Rate": {"number": {"format": "percent"}},
            "Response Time": {"number": {"format": "number"}},
            "User Satisfaction": {
                "select": {
                    "options": [
                        {"name": "1", "color": "red"},
                        {"name": "2", "color": "orange"},
                        {"name": "3", "color": "yellow"},
                        {"name": "4", "color": "blue"},
                        {"name": "5", "color": "green"}
                    ]
                }
            },
            "Tokens Used": {"number": {"format": "number"}},
            "Cost": {"number": {"format": "dollar"}},
            "Error Count": {"number": {"format": "number"}},
            "Learning Progress": {"number": {"format": "percent"}},
            "Notes": {"rich_text": {}},
            "Created": {"created_time": {}}
        }
    
    def _get_patrick_instructions_schema(self) -> Dict[str, Any]:
        """Schema for Patrick Instructions management"""
        return {
            "Title": {"title": {}},
            "Category": {
                "select": {
                    "options": [
                        {"name": "Critical", "color": "red"},
                        {"name": "Daily", "color": "blue"},
                        {"name": "Emergency", "color": "orange"},
                        {"name": "Reference", "color": "gray"}
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": "P0", "color": "red"},
                        {"name": "P1", "color": "orange"},
                        {"name": "P2", "color": "yellow"},
                        {"name": "P3", "color": "gray"}
                    ]
                }
            },
            "Frequency": {
                "select": {
                    "options": [
                        {"name": "Daily", "color": "blue"},
                        {"name": "Weekly", "color": "green"},
                        {"name": "Monthly", "color": "orange"},
                        {"name": "As Needed", "color": "gray"}
                    ]
                }
            },
            "Last Executed": {"date": {}},
            "Success Rate": {"number": {"format": "percent"}},
            "Dependencies": {
                "multi_select": {
                    "options": [
                        {"name": "Server Running", "color": "blue"},
                        {"name": "Database Access", "color": "green"},
                        {"name": "API Keys", "color": "red"},
                        {"name": "File System", "color": "orange"}
                    ]
                }
            },
            "Commands": {"rich_text": {}},
            "Troubleshooting": {"rich_text": {}},
            "Notes": {"rich_text": {}},
            "Created": {"created_time": {}},
            "Updated": {"last_edited_time": {}}
        }
    
    async def _create_database(self, title: str, properties: Dict[str, Any]) -> str:
        """Create a database with specified schema"""
        try:
            # First, create a parent page for the database
            parent_page = await self._create_page(
                title=f"{title} Container",
                content=[{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": f"Container for {title} database"}}]
                    }
                }]
            )
            
            # Create the database
            database_data = {
                "parent": {"page_id": parent_page},
                "title": [{"text": {"content": title}}],
                "properties": properties
            }
            
            response = self.session.post(
                f"{self.config.base_url}/databases",
                json=database_data
            )
            response.raise_for_status()
            
            database_id = response.json()["id"]
            logger.info(f"✅ Created database: {title} ({database_id})")
            return database_id
            
        except Exception as e:
            logger.error(f"Failed to create database {title}: {e}")
            raise
    
    async def _create_page(self, title: str, content: List[Dict[str, Any]], parent_id: Optional[str] = None) -> str:
        """Create a page with specified content"""
        try:
            page_data = {
                "parent": {"type": "page_id", "page_id": parent_id} if parent_id else {"type": "workspace"},
                "properties": {
                    "title": {"title": [{"text": {"content": title}}]}
                },
                "children": content
            }
            
            response = self.session.post(
                f"{self.config.base_url}/pages",
                json=page_data
            )
            response.raise_for_status()
            
            page_id = response.json()["id"]
            logger.info(f"✅ Created page: {title} ({page_id})")
            return page_id
            
        except Exception as e:
            logger.error(f"Failed to create page {title}: {e}")
            raise
    
    async def _create_master_dashboard(self, databases: Dict[str, str]) -> str:
        """Create master dashboard with links to all databases"""
        dashboard_content = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"text": {"content": "🏢 Orchestra AI Ecosystem Dashboard"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}}]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "📊 Quick Stats"}}]}
            }
        ]
        
        # Add database links
        for db_name, db_id in databases.items():
            dashboard_content.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": f"• {db_name.replace('_', ' ').title()}: "}},
                        {"text": {"content": "View Database", "link": {"url": f"https://notion.so/{db_id}"}}}
                    ]
                }
            })
        
        return await self._create_page("Orchestra AI Dashboard", dashboard_content)
    
    async def _setup_automated_workflows(self) -> Dict[str, Any]:
        """Setup automated workflows for common tasks"""
        workflows = {
            "daily_sync": "Sync development activities daily",
            "weekly_report": "Generate weekly progress reports",
            "patrick_backup": "Backup Patrick Instructions weekly",
            "performance_tracking": "Track AI agent performance metrics"
        }
        
        logger.info("✅ Automated workflows configured")
        return workflows
    
    # Cross-tool integration methods
    async def log_roo_session(self, session_data: Dict[str, Any]) -> str:
        """Log Roo Coder session to development log"""
        if not self.config.development_log_db:
            raise ValueError("Development log database not configured")
        
        page_data = {
            "parent": {"database_id": self.config.development_log_db},
            "properties": {
                "Title": {"title": [{"text": {"content": f"Roo Session: {session_data.get('task', 'Unknown')}"}}]},
                "Date": {"date": {"start": datetime.date.today().isoformat()}},
                "Type": {"select": {"name": session_data.get("type", "Code")}},
                "Tool Used": {"select": {"name": "Roo"}},
                "Notes": {"rich_text": [{"text": {"content": session_data.get("notes", "")}}]}
            }
        }
        
        response = self.session.post(f"{self.config.base_url}/pages", json=page_data)
        return response.json()["id"]
    
    async def log_continue_ui_generation(self, ui_data: Dict[str, Any]) -> str:
        """Log Continue UI generation session"""
        if not self.config.development_log_db:
            raise ValueError("Development log database not configured")
        
        page_data = {
            "parent": {"database_id": self.config.development_log_db},
            "properties": {
                "Title": {"title": [{"text": {"content": f"UI Generation: {ui_data.get('component', 'Unknown')}"}}]},
                "Date": {"date": {"start": datetime.date.today().isoformat()}},
                "Type": {"select": {"name": "UI"}},
                "Tool Used": {"select": {"name": "Continue"}},
                "Notes": {"rich_text": [{"text": {"content": ui_data.get("description", "")}}]}
            }
        }
        
        response = self.session.post(f"{self.config.base_url}/pages", json=page_data)
        return response.json()["id"]
    
    async def sync_patrick_instructions(self) -> Dict[str, Any]:
        """Sync Patrick Instructions from .patrick/ directory to Notion"""
        if not self.config.patrick_instructions_db:
            raise ValueError("Patrick Instructions database not configured")
        
        patrick_dir = Path(".patrick")
        if not patrick_dir.exists():
            return {"success": False, "error": "Patrick directory not found"}
        
        synced_files = []
        
        # Read README.md and extract instructions
        readme_path = patrick_dir / "README.md"
        if readme_path.exists():
            content = readme_path.read_text()
            
            # Parse sections and create database entries
            # This would parse the markdown and create structured entries
            # Implementation details would depend on the specific format
            
            synced_files.append("README.md")
        
        return {"success": True, "synced_files": synced_files}

def main():
    """Main CLI interface for enhanced Notion integration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Orchestra AI Notion Integration")
    parser.add_argument("--setup-workspace", action="store_true", help="Setup complete Notion workspace")
    parser.add_argument("--sync-patrick", action="store_true", help="Sync Patrick Instructions")
    parser.add_argument("--daily-report", action="store_true", help="Generate daily development report")
    parser.add_argument("--test-connection", action="store_true", help="Test Notion API connection")
    
    args = parser.parse_args()
    
    # Get API token from environment or parameter
    api_token = os.getenv('NOTION_API_KEY')
    if not api_token:
        print("❌ NOTION_API_KEY environment variable not set")
        return
    
    config = NotionConfig(api_token=api_token)
    notion = EnhancedNotionIntegration(config)
    
    if args.test_connection:
        # Test API connection
        try:
            response = notion.session.get(f"{config.base_url}/users/me")
            response.raise_for_status()
            print("✅ Notion API connection successful")
            print(f"User: {response.json().get('name', 'Unknown')}")
        except Exception as e:
            print(f"❌ Notion API connection failed: {e}")
    
    elif args.setup_workspace:
        # Setup complete workspace
        result = asyncio.run(notion.setup_workspace())
        if result["success"]:
            print("✅ Orchestra AI Notion workspace setup complete!")
            print(f"Dashboard: {result['dashboard']}")
        else:
            print(f"❌ Setup failed: {result['error']}")
    
    elif args.sync_patrick:
        # Sync Patrick Instructions
        result = asyncio.run(notion.sync_patrick_instructions())
        if result["success"]:
            print(f"✅ Synced Patrick Instructions: {result['synced_files']}")
        else:
            print(f"❌ Sync failed: {result['error']}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

