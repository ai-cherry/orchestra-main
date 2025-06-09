#!/usr/bin/env python3
"""
🔧 Secure Notion Configuration System for Orchestra AI
Manages all Notion integration settings via environment variables
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Cache strategies for different data types"""
    AGGRESSIVE = "aggressive"  # Cache for 1 hour
    MODERATE = "moderate"     # Cache for 15 minutes  
    MINIMAL = "minimal"       # Cache for 5 minutes
    REALTIME = "realtime"     # No caching

class NotionEnvironment(Enum):
    """Environment configurations"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class NotionDatabaseConfig:
    """Configuration for Notion databases"""
    # Project Management Databases
    epic_tracking: str = field(default="")
    task_management: str = field(default="")
    development_log: str = field(default="")
    
    # AI Coding Databases
    coding_rules: str = field(default="")
    mcp_connections: str = field(default="")
    code_reflection: str = field(default="")
    ai_tool_metrics: str = field(default="")
    
    # Persona Databases
    cherry_features: str = field(default="")
    sophia_features: str = field(default="")
    karen_features: str = field(default="")
    
    # Operations Databases
    patrick_instructions: str = field(default="")
    knowledge_base: str = field(default="")

@dataclass
class NotionConfig:
    """Comprehensive Notion configuration with security best practices"""
    
    # Core API Configuration
    api_token: str = field(default="")
    workspace_id: str = field(default="")
    workspace_url: str = field(default="")
    
    # Database Configuration
    databases: NotionDatabaseConfig = field(default_factory=NotionDatabaseConfig)
    
    # Cache Configuration
    cache_ttl: Dict[str, int] = field(default_factory=lambda: {
        "tasks": 300,           # 5 minutes
        "instructions": 3600,   # 1 hour
        "features": 900,        # 15 minutes
        "knowledge": 1800,      # 30 minutes
        "metrics": 600,         # 10 minutes
        "logs": 300            # 5 minutes
    })
    
    # Environment Settings
    environment: NotionEnvironment = field(default=NotionEnvironment.DEVELOPMENT)
    debug_mode: bool = field(default=False)
    
    # Rate Limiting
    rate_limit_requests_per_second: int = field(default=3)
    rate_limit_burst: int = field(default=10)
    
    # Webhook Configuration (optional)
    webhook_secret: Optional[str] = field(default=None)
    webhook_enabled: bool = field(default=False)
    
    # Logging Configuration
    log_level: str = field(default="INFO")
    log_to_notion: bool = field(default=True)
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.api_token:
            raise ValueError("Notion API token is required")
        if not self.workspace_id:
            raise ValueError("Notion workspace ID is required")
        
        # Validate database IDs are present for required databases
        required_dbs = ["task_management", "development_log", "mcp_connections"]
        for db_name in required_dbs:
            if not getattr(self.databases, db_name):
                logger.warning(f"Database ID missing for {db_name}")

def load_notion_config() -> NotionConfig:
    """
    Load Notion configuration from environment variables with fallbacks
    
    Environment Variables Expected:
    - NOTION_API_TOKEN: Your Notion integration token
    - NOTION_WORKSPACE_ID: Your Notion workspace ID
    - NOTION_WORKSPACE_URL: Your Notion workspace URL
    - NOTION_DB_*: Database IDs for each database
    - NOTION_ENVIRONMENT: development/staging/production
    - NOTION_DEBUG: true/false
    """
    
    # Core configuration
    api_token = os.getenv("NOTION_API_TOKEN", "")
    workspace_id = os.getenv("NOTION_WORKSPACE_ID", "")
    workspace_url = os.getenv("NOTION_WORKSPACE_URL", "")
    
    # Fallback to hardcoded values if environment variables not set (development only)
    if not api_token and os.getenv("NOTION_ENVIRONMENT", "development") == "development":
        logger.warning("Using fallback API token - set NOTION_API_TOKEN environment variable for production")
        api_token = "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"
    
    if not workspace_id and os.getenv("NOTION_ENVIRONMENT", "development") == "development":
        logger.warning("Using fallback workspace ID - set NOTION_WORKSPACE_ID environment variable for production")
        workspace_id = "20bdba04940280ca9ba7f9bce721f547"
    
    if not workspace_url and workspace_id:
        workspace_url = f"https://www.notion.so/Orchestra-AI-Workspace-{workspace_id}"
    
    # Database configuration from environment
    databases = NotionDatabaseConfig(
        # Project Management
        epic_tracking=os.getenv("NOTION_DB_EPIC_TRACKING", "20bdba04-9402-8114-b57b-df7f1d4b2712"),
        task_management=os.getenv("NOTION_DB_TASK_MANAGEMENT", "20bdba04-9402-81a2-99f3-e69dc37b73d6"),
        development_log=os.getenv("NOTION_DB_DEVELOPMENT_LOG", "20bdba04-9402-81fd-9558-d66c07d9576c"),
        
        # AI Coding
        coding_rules=os.getenv("NOTION_DB_CODING_RULES", "20bdba04940281bdadf1e78f4e0989e8"),
        mcp_connections=os.getenv("NOTION_DB_MCP_CONNECTIONS", "20bdba04940281aea36af6144ec68df2"),
        code_reflection=os.getenv("NOTION_DB_CODE_REFLECTION", "20bdba049402814d8e53fbec166ef030"),
        ai_tool_metrics=os.getenv("NOTION_DB_AI_TOOL_METRICS", "20bdba049402813f8404fa8d5f615b02"),
        
        # Personas
        cherry_features=os.getenv("NOTION_DB_CHERRY_FEATURES", "20bdba04-9402-8162-9e3c-fa8c8e41fd16"),
        sophia_features=os.getenv("NOTION_DB_SOPHIA_FEATURES", "20bdba04-9402-811d-83b4-cdc1a2505623"),
        karen_features=os.getenv("NOTION_DB_KAREN_FEATURES", "20bdba04-9402-819c-b2ca-d3d3828691e6"),
        
        # Operations
        patrick_instructions=os.getenv("NOTION_DB_PATRICK_INSTRUCTIONS", "20bdba04-9402-81b4-9890-e663db2b50a3"),
        knowledge_base=os.getenv("NOTION_DB_KNOWLEDGE_BASE", "20bdba04-9402-81a4-bc27-e06d160e3378")
    )
    
    # Environment settings
    env_str = os.getenv("NOTION_ENVIRONMENT", "development").lower()
    try:
        environment = NotionEnvironment(env_str)
    except ValueError:
        logger.warning(f"Invalid environment '{env_str}', defaulting to development")
        environment = NotionEnvironment.DEVELOPMENT
    
    # Additional settings
    debug_mode = os.getenv("NOTION_DEBUG", "false").lower() == "true"
    log_level = os.getenv("NOTION_LOG_LEVEL", "INFO").upper()
    
    # Rate limiting
    rate_limit_rps = int(os.getenv("NOTION_RATE_LIMIT_RPS", "3"))
    rate_limit_burst = int(os.getenv("NOTION_RATE_LIMIT_BURST", "10"))
    
    # Webhook configuration
    webhook_secret = os.getenv("NOTION_WEBHOOK_SECRET")
    webhook_enabled = os.getenv("NOTION_WEBHOOK_ENABLED", "false").lower() == "true"
    
    return NotionConfig(
        api_token=api_token,
        workspace_id=workspace_id,
        workspace_url=workspace_url,
        databases=databases,
        environment=environment,
        debug_mode=debug_mode,
        rate_limit_requests_per_second=rate_limit_rps,
        rate_limit_burst=rate_limit_burst,
        webhook_secret=webhook_secret,
        webhook_enabled=webhook_enabled,
        log_level=log_level,
        log_to_notion=environment != NotionEnvironment.DEVELOPMENT
    )

def get_database_schemas() -> Dict[str, Dict[str, Any]]:
    """
    Get comprehensive database schemas for all Notion databases
    This serves as documentation and validation reference
    """
    return {
        "epic_tracking": {
            "name": "🎯 Epic & Feature Tracking",
            "purpose": "High-level feature planning and epic management",
            "properties": {
                "Epic Title": {"type": "title", "required": True},
                "Status": {"type": "select", "options": ["Planning", "In Progress", "Testing", "Done"]},
                "Priority": {"type": "select", "options": ["Low", "Medium", "High", "Critical"]},
                "Persona": {"type": "select", "options": ["Cherry", "Sophia", "Karen", "Platform"]},
                "Estimated Effort": {"type": "number"},
                "Actual Effort": {"type": "number"},
                "Start Date": {"type": "date"},
                "Target Date": {"type": "date"},
                "Description": {"type": "rich_text"},
                "Acceptance Criteria": {"type": "rich_text"},
                "Technical Notes": {"type": "rich_text"}
            }
        },
        "task_management": {
            "name": "📋 Task Management",
            "purpose": "Detailed task tracking and assignment",
            "properties": {
                "Task": {"type": "title", "required": True},
                "Status": {"type": "select", "options": ["Ready", "In Progress", "Review", "Done", "Blocked"]},
                "Assignee": {"type": "select", "options": ["Human Developer", "Cursor AI", "Roo AI", "Continue AI"]},
                "Priority": {"type": "select", "options": ["Low", "Medium", "High", "Critical"]},
                "Type": {"type": "select", "options": ["Feature", "Bug", "Refactor", "Documentation", "Infrastructure"]},
                "Epic": {"type": "relation", "relation_to": "epic_tracking"},
                "Estimated Hours": {"type": "number"},
                "Actual Hours": {"type": "number"},
                "Due Date": {"type": "date"},
                "Description": {"type": "rich_text"},
                "Technical Details": {"type": "rich_text"},
                "Completion Notes": {"type": "rich_text"}
            }
        },
        "development_log": {
            "name": "💻 Development Log",
            "purpose": "Comprehensive development activity tracking",
            "properties": {
                "Title": {"type": "title", "required": True},
                "Type": {"type": "select", "options": ["Code", "Config", "Deploy", "Debug", "Research", "Review"]},
                "Tool Used": {"type": "select", "options": ["Manual", "Cursor", "Roo", "Continue", "GitHub", "Notion"]},
                "Date": {"type": "date", "required": True},
                "Files Changed": {"type": "number"},
                "Lines Added": {"type": "number"},
                "Lines Removed": {"type": "number"},
                "Commit Hash": {"type": "rich_text"},
                "Notes": {"type": "rich_text"},
                "Performance Impact": {"type": "select", "options": ["Positive", "Neutral", "Negative"]},
                "Learning Insights": {"type": "rich_text"}
            }
        },
        "coding_rules": {
            "name": "📚 Coding Rules & Standards",
            "purpose": "AI coding assistant configuration and standards",
            "properties": {
                "Title": {"type": "title", "required": True},
                "Category": {"type": "select", "options": ["Python", "TypeScript", "React", "Infrastructure", "AI Tools", "Security"]},
                "Status": {"type": "select", "options": ["Active", "Draft", "Deprecated"]},
                "Priority": {"type": "select", "options": ["Low", "Medium", "High", "Critical"]},
                "Rule Content": {"type": "rich_text", "required": True},
                "Examples": {"type": "rich_text"},
                "Rationale": {"type": "rich_text"},
                "Tools Applied": {"type": "multi_select", "options": ["Cursor", "Roo", "Continue", "All"]},
                "Last Updated": {"type": "date"}
            }
        },
        "mcp_connections": {
            "name": "🔧 MCP Server Connections",
            "purpose": "Model Context Protocol server activity and health monitoring",
            "properties": {
                "Tool": {"type": "title", "required": True},
                "Activity": {"type": "rich_text"},
                "Status": {"type": "select", "options": ["Active", "Inactive", "Error", "Connecting"]},
                "Context": {"type": "rich_text"},
                "Timestamp": {"type": "date"},
                "Response Time": {"type": "number"},
                "Error Details": {"type": "rich_text"},
                "Success Rate": {"type": "number"}
            }
        },
        "code_reflection": {
            "name": "🤔 Code Reflection & Learning",
            "purpose": "AI insights and continuous improvement tracking",
            "properties": {
                "Tool": {"type": "title", "required": True},
                "Category": {"type": "select", "options": ["Performance", "Workflow", "Optimization", "Learning", "Error"]},
                "Insight": {"type": "rich_text", "required": True},
                "Status": {"type": "select", "options": ["New", "Reviewed", "Implemented", "Archived"]},
                "Priority": {"type": "select", "options": ["Low", "Medium", "High"]},
                "Implementation": {"type": "rich_text"},
                "Impact": {"type": "select", "options": ["Minor", "Moderate", "Major"]},
                "Date": {"type": "date"}
            }
        },
        "ai_tool_metrics": {
            "name": "📊 AI Tool Performance Metrics",
            "purpose": "Performance tracking for AI coding tools",
            "properties": {
                "Tool": {"type": "select", "options": ["Cursor", "Roo", "Continue", "MCP Server"], "required": True},
                "Metric Type": {"type": "select", "options": ["Performance", "Usage", "Quality", "Error Rate"]},
                "Value": {"type": "number"},
                "Unit": {"type": "select", "options": ["Milliseconds", "Requests", "Percentage", "Count"]},
                "Status": {"type": "select", "options": ["Good", "Warning", "Critical"]},
                "Details": {"type": "rich_text"},
                "Timestamp": {"type": "date"},
                "Context": {"type": "rich_text"}
            }
        }
    }

def validate_database_access(config: NotionConfig) -> Dict[str, bool]:
    """
    Validate access to all configured databases
    Returns dict with database names and access status
    """
    import requests
    
    headers = {
        "Authorization": f"Bearer {config.api_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    access_status = {}
    
    for db_name in ["epic_tracking", "task_management", "development_log", 
                    "coding_rules", "mcp_connections", "code_reflection", "ai_tool_metrics",
                    "cherry_features", "sophia_features", "karen_features",
                    "patrick_instructions", "knowledge_base"]:
        
        db_id = getattr(config.databases, db_name)
        if not db_id:
            access_status[db_name] = False
            continue
            
        try:
            url = f"https://api.notion.com/v1/databases/{db_id}"
            response = requests.get(url, headers=headers, timeout=10)
            access_status[db_name] = response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to validate access to {db_name}: {e}")
            access_status[db_name] = False
    
    return access_status

# Global configuration instance
_config_instance: Optional[NotionConfig] = None

def get_config() -> NotionConfig:
    """Get global configuration instance (singleton pattern)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = load_notion_config()
    return _config_instance

def reload_config() -> NotionConfig:
    """Reload configuration from environment variables"""
    global _config_instance
    _config_instance = load_notion_config()
    return _config_instance

# Example usage and testing
if __name__ == "__main__":
    # Load and validate configuration
    config = get_config()
    print(f"✅ Loaded configuration for environment: {config.environment.value}")
    print(f"🔧 Workspace: {config.workspace_url}")
    print(f"🐛 Debug mode: {config.debug_mode}")
    
    # Validate database access
    print("\n🔍 Validating database access...")
    access_results = validate_database_access(config)
    
    for db_name, accessible in access_results.items():
        status = "✅" if accessible else "❌"
        print(f"   {status} {db_name}")
    
    # Show database schemas
    print("\n📋 Available database schemas:")
    schemas = get_database_schemas()
    for db_name, schema in schemas.items():
        print(f"   📊 {schema['name']}: {schema['purpose']}") 