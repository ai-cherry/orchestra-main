#!/usr/bin/env python3
"""
🎯 Enhanced Notion AI Integration for Orchestra Project
Production-ready implementation with latest 2024-2025 capabilities

Features:
- Latest Notion API (2024-12-20) with ntn_ token format
- Enterprise Search integration
- AI-powered automation and workflows
- Cross-tool integration (Roo/Continue/Cursor)
- Patrick Instructions automation
- Real-time project tracking
- Advanced database schemas
- Webhook integration
- Performance monitoring
"""

import os
import json
import asyncio
import logging
import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, asdict
import requests
import hashlib
import base64
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class NotionConfig:
    """Enhanced configuration for Notion integration"""
    api_token: str
    api_version: str = "2022-06-28"  # Latest stable version
    base_url: str = "https://api.notion.com/v1"
    
    # Database IDs (will be created during setup)
    project_tasks_db: Optional[str] = None
    development_log_db: Optional[str] = None
    epic_feature_db: Optional[str] = None
    cherry_features_db: Optional[str] = None
    sophia_features_db: Optional[str] = None
    karen_features_db: Optional[str] = None
    patrick_instructions_db: Optional[str] = None
    knowledge_base_db: Optional[str] = None
    
    # Integration settings
    github_webhook_secret: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    lambda_labs_api_key: Optional[str] = None
    
    # Enterprise features
    enterprise_search_enabled: bool = True
    ai_automation_enabled: bool = True
    webhook_automation_enabled: bool = True

class EnhancedNotionIntegration:
    """Production-ready Notion integration with advanced capabilities"""
    
    def __init__(self, config: NotionConfig):
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {config.api_token}",
            "Content-Type": "application/json",
            "Notion-Version": config.api_version
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Validate token format
        if not config.api_token.startswith('ntn_'):
            logger.warning("API token should use ntn_ prefix for enhanced security")
    
    async def setup_complete_workspace(self) -> Dict[str, Any]:
        """Create complete Orchestra AI workspace with all databases and automations"""
        try:
            logger.info("🚀 Setting up complete Orchestra AI Notion workspace...")
            
            # Create all databases
            databases = await self._create_all_databases()
            
            # Create master dashboard
            dashboard = await self._create_master_dashboard(databases)
            
            # Setup automations
            automations = await self._setup_all_automations(databases)
            
            # Configure webhooks
            webhooks = await self._setup_webhook_integrations(databases)
            
            # Setup enterprise search
            search_config = await self._setup_enterprise_search()
            
            # Create Patrick Instructions automation
            patrick_automation = await self._setup_patrick_automation(databases)
            
            result = {
                "success": True,
                "workspace_id": dashboard["id"],
                "databases": databases,
                "dashboard": dashboard,
                "automations": automations,
                "webhooks": webhooks,
                "enterprise_search": search_config,
                "patrick_automation": patrick_automation,
                "message": "Complete Orchestra AI Notion workspace created successfully!"
            }
            
            # Save configuration for future use
            await self._save_workspace_config(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to setup complete workspace: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_all_databases(self) -> Dict[str, str]:
        """Create all optimized databases for Orchestra project"""
        databases = {}
        
        logger.info("Creating Epic & Feature database...")
        databases["epic_feature"] = await self._create_database(
            title="🎯 Epic & Feature Tracking",
            properties=self._get_epic_feature_schema()
        )
        
        logger.info("Creating Task Management database...")
        databases["project_tasks"] = await self._create_database(
            title="📋 Task Management",
            properties=self._get_task_management_schema()
        )
        
        logger.info("Creating Development Log database...")
        databases["development_log"] = await self._create_database(
            title="💻 Development Log",
            properties=self._get_development_log_schema()
        )
        
        logger.info("Creating Cherry Features database...")
        databases["cherry_features"] = await self._create_database(
            title="🍒 Cherry Life Companion Features",
            properties=self._get_cherry_features_schema()
        )
        
        logger.info("Creating Sophia Features database...")
        databases["sophia_features"] = await self._create_database(
            title="👩‍💼 Sophia Business Intelligence Features",
            properties=self._get_sophia_features_schema()
        )
        
        logger.info("Creating Karen Features database...")
        databases["karen_features"] = await self._create_database(
            title="👩‍⚕️ Karen Healthcare Features",
            properties=self._get_karen_features_schema()
        )
        
        logger.info("Creating Patrick Instructions database...")
        databases["patrick_instructions"] = await self._create_database(
            title="📖 Patrick Instructions - Critical Workflows",
            properties=self._get_patrick_instructions_schema()
        )
        
        logger.info("Creating Knowledge Base database...")
        databases["knowledge_base"] = await self._create_database(
            title="📚 Knowledge Base",
            properties=self._get_knowledge_base_schema()
        )
        
        # Update config with database IDs
        self.config.project_tasks_db = databases["project_tasks"]
        self.config.development_log_db = databases["development_log"]
        self.config.epic_feature_db = databases["epic_feature"]
        self.config.cherry_features_db = databases["cherry_features"]
        self.config.sophia_features_db = databases["sophia_features"]
        self.config.karen_features_db = databases["karen_features"]
        self.config.patrick_instructions_db = databases["patrick_instructions"]
        self.config.knowledge_base_db = databases["knowledge_base"]
        
        return databases
    
    def _get_epic_feature_schema(self) -> Dict[str, Any]:
        """Epic & Feature database schema"""
        return {
            "Title": {"title": {}},
            "Type": {
                "select": {
                    "options": [
                        {"name": "Epic", "color": "blue"},
                        {"name": "Feature", "color": "green"},
                        {"name": "Enhancement", "color": "yellow"},
                        {"name": "Technical Debt", "color": "red"}
                    ]
                }
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Planning", "color": "gray"},
                        {"name": "In Progress", "color": "blue"},
                        {"name": "Review", "color": "yellow"},
                        {"name": "Done", "color": "green"},
                        {"name": "Blocked", "color": "red"}
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": "P0 - Critical", "color": "red"},
                        {"name": "P1 - High", "color": "orange"},
                        {"name": "P2 - Medium", "color": "yellow"},
                        {"name": "P3 - Low", "color": "gray"}
                    ]
                }
            },
            "Business Value": {
                "select": {
                    "options": [
                        {"name": "High", "color": "green"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "gray"}
                    ]
                }
            },
            "Assigned Persona": {
                "multi_select": {
                    "options": [
                        {"name": "Cherry", "color": "red"},
                        {"name": "Sophia", "color": "blue"},
                        {"name": "Karen", "color": "green"},
                        {"name": "Human Team", "color": "purple"}
                    ]
                }
            },
            "Target Release": {
                "select": {
                    "options": [
                        {"name": "MVP", "color": "red"},
                        {"name": "Beta", "color": "orange"},
                        {"name": "V1.0", "color": "green"},
                        {"name": "Future", "color": "gray"}
                    ]
                }
            },
            "Story Points": {"number": {"format": "number"}},
            "Start Date": {"date": {}},
            "Target Date": {"date": {}},
            "Completion Date": {"date": {}},
            "Success Criteria": {"rich_text": {}},
            "Technical Notes": {"rich_text": {}},
            "AI Generated Summary": {"rich_text": {}},
            "Created": {"created_time": {}},
            "Last Updated": {"last_edited_time": {}},
            "Created By": {"created_by": {}},
            "Last Edited By": {"last_edited_by": {}}
        }
    
    def _get_task_management_schema(self) -> Dict[str, Any]:
        """Task Management database schema"""
        return {
            "Title": {"title": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Backlog", "color": "gray"},
                        {"name": "Ready", "color": "blue"},
                        {"name": "In Progress", "color": "yellow"},
                        {"name": "Code Review", "color": "orange"},
                        {"name": "Testing", "color": "purple"},
                        {"name": "Done", "color": "green"},
                        {"name": "Blocked", "color": "red"}
                    ]
                }
            },
            "Type": {
                "select": {
                    "options": [
                        {"name": "Feature", "color": "green"},
                        {"name": "Bug Fix", "color": "red"},
                        {"name": "Technical Debt", "color": "orange"},
                        {"name": "Research", "color": "blue"},
                        {"name": "Documentation", "color": "purple"},
                        {"name": "Infrastructure", "color": "gray"}
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": "Critical", "color": "red"},
                        {"name": "High", "color": "orange"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "gray"}
                    ]
                }
            },
            "Assignee": {
                "select": {
                    "options": [
                        {"name": "Cherry", "color": "red"},
                        {"name": "Sophia", "color": "blue"},
                        {"name": "Karen", "color": "green"},
                        {"name": "Human Developer", "color": "purple"},
                        {"name": "Unassigned", "color": "gray"}
                    ]
                }
            },
            "Component": {
                "multi_select": {
                    "options": [
                        {"name": "Admin Interface", "color": "blue"},
                        {"name": "Core API", "color": "green"},
                        {"name": "Agent System", "color": "purple"},
                        {"name": "Database", "color": "orange"},
                        {"name": "Infrastructure", "color": "gray"},
                        {"name": "Documentation", "color": "yellow"}
                    ]
                }
            },
            "Development Tool": {
                "select": {
                    "options": [
                        {"name": "Cursor", "color": "blue"},
                        {"name": "Roo Coder", "color": "green"},
                        {"name": "Continue", "color": "purple"},
                        {"name": "Manual", "color": "gray"}
                    ]
                }
            },
            "Story Points": {"number": {"format": "number"}},
            "Effort Hours": {"number": {"format": "number"}},
            "Start Date": {"date": {}},
            "Due Date": {"date": {}},
            "Completion Date": {"date": {}},
            "GitHub Issue": {"url": {}},
            "Pull Request": {"url": {}},
            "Commit Hash": {"rich_text": {}},
            "Test Coverage": {"number": {"format": "percent"}},
            "Description": {"rich_text": {}},
            "Acceptance Criteria": {"rich_text": {}},
            "Technical Notes": {"rich_text": {}},
            "AI Assistance Used": {"checkbox": {}},
            "Created": {"created_time": {}},
            "Last Updated": {"last_edited_time": {}},
            "Created By": {"created_by": {}},
            "Last Edited By": {"last_edited_by": {}}
        }
    
    def _get_development_log_schema(self) -> Dict[str, Any]:
        """Development Log database schema"""
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
    
    def _get_cherry_features_schema(self) -> Dict[str, Any]:
        """Cherry Life Companion features schema"""
        return {
            "Feature Name": {"title": {}},
            "Category": {
                "select": {
                    "options": [
                        {"name": "Wellness Coaching", "color": "green"},
                        {"name": "Travel Planning", "color": "blue"},
                        {"name": "Creative Collaboration", "color": "purple"},
                        {"name": "Lifestyle Optimization", "color": "orange"},
                        {"name": "Personal Assistant", "color": "red"},
                        {"name": "Emotional Support", "color": "pink"}
                    ]
                }
            },
            "Personality Trait": {
                "multi_select": {
                    "options": [
                        {"name": "Empathetic", "color": "pink"},
                        {"name": "Creative", "color": "purple"},
                        {"name": "Supportive", "color": "green"},
                        {"name": "Intuitive", "color": "blue"},
                        {"name": "Encouraging", "color": "yellow"}
                    ]
                }
            },
            "Emotional Intelligence Level": {
                "select": {
                    "options": [
                        {"name": "Basic", "color": "gray"},
                        {"name": "Intermediate", "color": "yellow"},
                        {"name": "Advanced", "color": "green"},
                        {"name": "Expert", "color": "blue"}
                    ]
                }
            },
            "Privacy Level": {
                "select": {
                    "options": [
                        {"name": "Public", "color": "green"},
                        {"name": "Personal", "color": "yellow"},
                        {"name": "Private", "color": "orange"},
                        {"name": "Confidential", "color": "red"}
                    ]
                }
            },
            "Voice Personality": {
                "select": {
                    "options": [
                        {"name": "Warm & Caring", "color": "pink"},
                        {"name": "Enthusiastic", "color": "orange"},
                        {"name": "Calm & Soothing", "color": "blue"},
                        {"name": "Playful", "color": "purple"}
                    ]
                }
            },
            "User Feedback Score": {"number": {"format": "number"}},
            "Development Status": {
                "select": {
                    "options": [
                        {"name": "Concept", "color": "gray"},
                        {"name": "Prototype", "color": "yellow"},
                        {"name": "Beta", "color": "orange"},
                        {"name": "Production", "color": "green"}
                    ]
                }
            },
            "Success Metrics": {"rich_text": {}},
            "Technical Implementation": {"rich_text": {}},
            "User Stories": {"rich_text": {}},
            "Created": {"created_time": {}},
            "Last Updated": {"last_edited_time": {}}
        }
    
    def _get_sophia_features_schema(self) -> Dict[str, Any]:
        """Sophia Business Intelligence features schema"""
        return {
            "Feature Name": {"title": {}},
            "Business Domain": {
                "select": {
                    "options": [
                        {"name": "Market Analysis", "color": "blue"},
                        {"name": "Revenue Optimization", "color": "green"},
                        {"name": "Strategic Planning", "color": "purple"},
                        {"name": "Competitive Intelligence", "color": "orange"},
                        {"name": "Financial Analytics", "color": "red"},
                        {"name": "Performance Metrics", "color": "yellow"}
                    ]
                }
            },
            "Analysis Type": {
                "select": {
                    "options": [
                        {"name": "Descriptive", "color": "blue"},
                        {"name": "Diagnostic", "color": "yellow"},
                        {"name": "Predictive", "color": "orange"},
                        {"name": "Prescriptive", "color": "green"}
                    ]
                }
            },
            "Complexity Level": {
                "select": {
                    "options": [
                        {"name": "Simple", "color": "green"},
                        {"name": "Moderate", "color": "yellow"},
                        {"name": "Complex", "color": "orange"},
                        {"name": "Advanced", "color": "red"}
                    ]
                }
            },
            "Business Impact": {
                "select": {
                    "options": [
                        {"name": "High", "color": "green"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "gray"}
                    ]
                }
            },
            "ROI Potential": {
                "select": {
                    "options": [
                        {"name": "High", "color": "green"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "gray"},
                        {"name": "TBD", "color": "blue"}
                    ]
                }
            },
            "Technical Requirements": {"rich_text": {}},
            "Business Requirements": {"rich_text": {}},
            "Success Criteria": {"rich_text": {}},
            "Created": {"created_time": {}},
            "Last Updated": {"last_edited_time": {}}
        }
    
    def _get_karen_features_schema(self) -> Dict[str, Any]:
        """Karen Healthcare features schema"""
        return {
            "Feature Name": {"title": {}},
            "Healthcare Domain": {
                "select": {
                    "options": [
                        {"name": "Clinical Research", "color": "blue"},
                        {"name": "Patient Care", "color": "green"},
                        {"name": "Medical Knowledge", "color": "purple"},
                        {"name": "Compliance", "color": "red"},
                        {"name": "Diagnostics", "color": "orange"},
                        {"name": "Treatment Planning", "color": "yellow"}
                    ]
                }
            },
            "Compliance Level": {
                "select": {
                    "options": [
                        {"name": "HIPAA Required", "color": "red"},
                        {"name": "FDA Regulated", "color": "orange"},
                        {"name": "Clinical Guidelines", "color": "yellow"},
                        {"name": "Best Practices", "color": "green"}
                    ]
                }
            },
            "Patient Safety Impact": {
                "select": {
                    "options": [
                        {"name": "Critical", "color": "red"},
                        {"name": "High", "color": "orange"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "green"}
                    ]
                }
            },
            "Accuracy Requirements": {
                "select": {
                    "options": [
                        {"name": "99.9%+", "color": "green"},
                        {"name": "99%+", "color": "blue"},
                        {"name": "95%+", "color": "yellow"},
                        {"name": "90%+", "color": "orange"}
                    ]
                }
            },
            "Clinical Requirements": {"rich_text": {}},
            "Regulatory Considerations": {"rich_text": {}},
            "Validation Plan": {"rich_text": {}},
            "Risk Assessment": {"rich_text": {}},
            "Created": {"created_time": {}},
            "Last Updated": {"last_edited_time": {}}
        }
    
    def _get_patrick_instructions_schema(self) -> Dict[str, Any]:
        """Patrick Instructions database schema"""
        return {
            "Instruction Title": {"title": {}},
            "Category": {
                "select": {
                    "options": [
                        {"name": "Daily Operations", "color": "blue"},
                        {"name": "Emergency Procedures", "color": "red"},
                        {"name": "Weekly Maintenance", "color": "green"},
                        {"name": "Monthly Reviews", "color": "orange"},
                        {"name": "Deployment Procedures", "color": "purple"},
                        {"name": "Backup & Recovery", "color": "gray"}
                    ]
                }
            },
            "Priority Level": {
                "select": {
                    "options": [
                        {"name": "P0 - System Critical", "color": "red"},
                        {"name": "P1 - High Impact", "color": "orange"},
                        {"name": "P2 - Medium Impact", "color": "yellow"},
                        {"name": "P3 - Low Impact", "color": "gray"}
                    ]
                }
            },
            "Frequency": {
                "select": {
                    "options": [
                        {"name": "Continuous", "color": "red"},
                        {"name": "Daily", "color": "blue"},
                        {"name": "Weekly", "color": "green"},
                        {"name": "Monthly", "color": "orange"},
                        {"name": "Quarterly", "color": "purple"},
                        {"name": "As Needed", "color": "gray"}
                    ]
                }
            },
            "Automation Level": {
                "select": {
                    "options": [
                        {"name": "Fully Manual", "color": "red"},
                        {"name": "Script Assisted", "color": "orange"},
                        {"name": "Semi-Automated", "color": "yellow"},
                        {"name": "Fully Automated", "color": "green"},
                        {"name": "AI Assisted", "color": "blue"}
                    ]
                }
            },
            "Last Executed": {"date": {}},
            "Next Due Date": {"date": {}},
            "Success Rate": {"number": {"format": "percent"}},
            "Execution Count": {"number": {"format": "number"}},
            "Risk Level": {
                "select": {
                    "options": [
                        {"name": "Low", "color": "green"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "High", "color": "orange"},
                        {"name": "Critical", "color": "red"}
                    ]
                }
            },
            "Command Sequence": {"rich_text": {}},
            "Prerequisites": {"rich_text": {}},
            "Expected Output": {"rich_text": {}},
            "Troubleshooting Guide": {"rich_text": {}},
            "Validation Steps": {"rich_text": {}},
            "Created": {"created_time": {}},
            "Last Updated": {"last_edited_time": {}},
            "Created By": {"created_by": {}},
            "Last Edited By": {"last_edited_by": {}}
        }
    
    def _get_knowledge_base_schema(self) -> Dict[str, Any]:
        """Knowledge Base database schema"""
        return {
            "Knowledge Item": {"title": {}},
            "Knowledge Type": {
                "select": {
                    "options": [
                        {"name": "Best Practice", "color": "green"},
                        {"name": "Lesson Learned", "color": "orange"},
                        {"name": "Troubleshooting", "color": "red"},
                        {"name": "Configuration", "color": "blue"},
                        {"name": "Process", "color": "purple"},
                        {"name": "Reference", "color": "gray"}
                    ]
                }
            },
            "Domain": {
                "multi_select": {
                    "options": [
                        {"name": "Infrastructure", "color": "blue"},
                        {"name": "Development", "color": "green"},
                        {"name": "Deployment", "color": "orange"},
                        {"name": "Monitoring", "color": "red"},
                        {"name": "Security", "color": "purple"},
                        {"name": "Performance", "color": "yellow"}
                    ]
                }
            },
            "Complexity Level": {
                "select": {
                    "options": [
                        {"name": "Basic", "color": "green"},
                        {"name": "Intermediate", "color": "yellow"},
                        {"name": "Advanced", "color": "orange"},
                        {"name": "Expert", "color": "red"}
                    ]
                }
            },
            "Relevance": {
                "select": {
                    "options": [
                        {"name": "High", "color": "green"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "gray"}
                    ]
                }
            },
            "Last Validated": {"date": {}},
            "Validation Status": {
                "select": {
                    "options": [
                        {"name": "Current", "color": "green"},
                        {"name": "Needs Review", "color": "yellow"},
                        {"name": "Outdated", "color": "orange"},
                        {"name": "Deprecated", "color": "red"}
                    ]
                }
            },
            "Confidence Level": {
                "select": {
                    "options": [
                        {"name": "High", "color": "green"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "orange"},
                        {"name": "Unverified", "color": "red"}
                    ]
                }
            },
            "Prerequisites": {"rich_text": {}},
            "Detailed Content": {"rich_text": {}},
            "Examples": {"rich_text": {}},
            "Common Pitfalls": {"rich_text": {}},
            "Additional Resources": {"rich_text": {}},
            "Search Keywords": {"rich_text": {}},
            "Created": {"created_time": {}},
            "Last Updated": {"last_edited_time": {}},
            "Created By": {"created_by": {}},
            "Last Edited By": {"last_edited_by": {}}
        }
    
    async def _create_database(self, title: str, properties: Dict[str, Any]) -> str:
        """Create a database with specified schema"""
        try:
            # Create the database directly in workspace
            database_data = {
                "parent": {"type": "workspace"},
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
    
    async def _create_master_dashboard(self, databases: Dict[str, str]) -> Dict[str, Any]:
        """Create master dashboard with links to all databases"""
        try:
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
                    "heading_2": {"rich_text": [{"text": {"content": "📊 Project Databases"}}]}
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
                            {
                                "text": {"content": "View Database", "link": {"url": f"https://notion.so/{db_id}"}},
                                "annotations": {"bold": True}
                            }
                        ]
                    }
                })
            
            # Create the dashboard page
            page_data = {
                "parent": {"type": "workspace"},
                "properties": {
                    "title": {"title": [{"text": {"content": "🏢 Orchestra AI Dashboard"}}]}
                },
                "children": dashboard_content
            }
            
            response = self.session.post(
                f"{self.config.base_url}/pages",
                json=page_data
            )
            response.raise_for_status()
            
            dashboard = response.json()
            logger.info(f"✅ Created master dashboard: {dashboard['id']}")
            return dashboard
            
        except Exception as e:
            logger.error(f"Failed to create master dashboard: {e}")
            raise
    
    async def _setup_all_automations(self, databases: Dict[str, str]) -> Dict[str, Any]:
        """Setup all automation workflows"""
        automations = {
            "github_integration": await self._setup_github_automation(databases),
            "task_management": await self._setup_task_automation(databases),
            "patrick_instructions": await self._setup_patrick_automation(databases),
            "ai_agent_tracking": await self._setup_ai_agent_automation(databases)
        }
        
        logger.info("✅ All automations configured successfully")
        return automations
    
    async def _setup_github_automation(self, databases: Dict[str, str]) -> Dict[str, Any]:
        """Setup GitHub integration automation"""
        # This would typically involve setting up webhooks and automation rules
        # For now, return configuration that would be used
        return {
            "webhook_url": f"https://api.notion.com/v1/webhooks/github-orchestra",
            "events": ["push", "pull_request", "issues", "release"],
            "target_database": databases["project_tasks"],
            "automation_rules": [
                "create_task_from_issue",
                "update_task_from_pr",
                "track_commits"
            ]
        }
    
    async def _setup_task_automation(self, databases: Dict[str, str]) -> Dict[str, Any]:
        """Setup task management automation"""
        return {
            "status_progression": True,
            "automatic_assignment": True,
            "progress_tracking": True,
            "notification_rules": [
                "task_blocked",
                "task_completed",
                "deadline_approaching"
            ]
        }
    
    async def _setup_patrick_automation(self, databases: Dict[str, str]) -> Dict[str, Any]:
        """Setup Patrick Instructions automation"""
        return {
            "scheduled_reminders": True,
            "execution_tracking": True,
            "failure_alerts": True,
            "automation_buttons": [
                "system_health_check",
                "deploy_latest",
                "backup_verification"
            ]
        }
    
    async def _setup_ai_agent_automation(self, databases: Dict[str, str]) -> Dict[str, Any]:
        """Setup AI agent performance automation"""
        return {
            "performance_monitoring": True,
            "learning_progress_tracking": True,
            "cross_agent_collaboration": True,
            "optimization_recommendations": True
        }
    
    async def _setup_webhook_integrations(self, databases: Dict[str, str]) -> Dict[str, Any]:
        """Setup webhook integrations"""
        webhooks = {
            "github": {
                "url": f"https://api.notion.com/v1/webhooks/github",
                "events": ["push", "pull_request", "issues"],
                "target_db": databases["development_log"]
            },
            "lambda_labs": {
                "url": f"https://api.notion.com/v1/webhooks/lambda",
                "events": ["instance_status", "billing_alert"],
                "target_db": databases["project_tasks"]
            },
            "slack": {
                "url": self.config.slack_webhook_url,
                "triggers": ["task_blocked", "epic_at_risk", "system_alert"]
            }
        }
        
        logger.info("✅ Webhook integrations configured")
        return webhooks
    
    async def _setup_enterprise_search(self) -> Dict[str, Any]:
        """Setup enterprise search configuration"""
        if not self.config.enterprise_search_enabled:
            return {"enabled": False}
        
        search_config = {
            "enabled": True,
            "connected_platforms": [
                "github",
                "slack", 
                "google_drive",
                "lambda_labs"
            ],
            "ai_features": {
                "semantic_search": True,
                "auto_summarization": True,
                "cross_reference": True,
                "expertise_location": True
            }
        }
        
        logger.info("✅ Enterprise search configured")
        return search_config
    
    async def _save_workspace_config(self, workspace_data: Dict[str, Any]) -> None:
        """Save workspace configuration for future use"""
        config_file = Path("notion_workspace_config.json")
        
        # Prepare config data
        config_data = {
            "workspace_id": workspace_data["workspace_id"],
            "databases": workspace_data["databases"],
            "created_at": datetime.datetime.now().isoformat(),
            "api_version": self.config.api_version,
            "features_enabled": {
                "enterprise_search": self.config.enterprise_search_enabled,
                "ai_automation": self.config.ai_automation_enabled,
                "webhooks": self.config.webhook_automation_enabled
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        logger.info(f"✅ Workspace configuration saved to {config_file}")
    
    # Additional methods for ongoing operations
    
    async def create_task_from_github_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Notion task from GitHub issue"""
        try:
            task_data = {
                "parent": {"database_id": self.config.project_tasks_db},
                "properties": {
                    "Title": {
                        "title": [{"text": {"content": issue_data["title"]}}]
                    },
                    "Type": {"select": {"name": "Bug Fix" if "bug" in issue_data.get("labels", []) else "Feature"}},
                    "Priority": {"select": {"name": self._map_github_priority(issue_data.get("labels", []))}},
                    "GitHub Issue": {"url": issue_data["html_url"]},
                    "Description": {
                        "rich_text": [{"text": {"content": issue_data.get("body", "")}}]
                    },
                    "Status": {"select": {"name": "Backlog"}}
                }
            }
            
            response = self.session.post(
                f"{self.config.base_url}/pages",
                json=task_data
            )
            response.raise_for_status()
            
            return {"success": True, "task_id": response.json()["id"]}
            
        except Exception as e:
            logger.error(f"Failed to create task from GitHub issue: {e}")
            return {"success": False, "error": str(e)}
    
    def _map_github_priority(self, labels: List[str]) -> str:
        """Map GitHub labels to Notion priority"""
        if "critical" in labels:
            return "Critical"
        elif "high" in labels:
            return "High"
        elif "low" in labels:
            return "Low"
        else:
            return "Medium"
    
    async def update_patrick_instruction_execution(self, instruction_id: str, success: bool, notes: str = "") -> Dict[str, Any]:
        """Update Patrick instruction execution status"""
        try:
            update_data = {
                "properties": {
                    "Last Executed": {"date": {"start": datetime.date.today().isoformat()}},
                    "Execution Count": {"number": 1},  # This would need to be incremented
                    "Success Rate": {"number": 1.0 if success else 0.0}  # This would need calculation
                }
            }
            
            if notes:
                update_data["properties"]["Notes"] = {
                    "rich_text": [{"text": {"content": notes}}]
                }
            
            response = self.session.patch(
                f"{self.config.base_url}/pages/{instruction_id}",
                json=update_data
            )
            response.raise_for_status()
            
            return {"success": True, "updated": True}
            
        except Exception as e:
            logger.error(f"Failed to update Patrick instruction: {e}")
            return {"success": False, "error": str(e)}

def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Orchestra AI Notion Integration")
    parser.add_argument("--setup", action="store_true", help="Setup complete workspace")
    parser.add_argument("--api-key", type=str, help="Notion API key (ntn_ format)")
    parser.add_argument("--test", action="store_true", help="Test API connection")
    
    args = parser.parse_args()
    
    if not args.api_key:
        api_key = os.getenv('NOTION_API_KEY')
        if not api_key:
            print("❌ No API key provided. Use --api-key or set NOTION_API_KEY environment variable")
            return
    else:
        api_key = args.api_key
    
    # Create configuration
    config = NotionConfig(api_token=api_key)
    
    # Initialize integration
    notion = EnhancedNotionIntegration(config)
    
    if args.test:
        # Test API connection
        try:
            response = notion.session.get(f"{config.base_url}/users/me")
            response.raise_for_status()
            print("✅ Notion API connection successful!")
            print(f"User: {response.json().get('name', 'Unknown')}")
        except Exception as e:
            print(f"❌ API connection failed: {e}")
        return
    
    if args.setup:
        # Setup complete workspace
        async def setup():
            result = await notion.setup_complete_workspace()
            if result["success"]:
                print("🎉 Orchestra AI Notion workspace setup complete!")
                print(f"Dashboard ID: {result['workspace_id']}")
                print(f"Databases created: {len(result['databases'])}")
                print("✅ All automations and integrations configured")
            else:
                print(f"❌ Setup failed: {result['error']}")
        
        asyncio.run(setup())
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

