#!/usr/bin/env python3
"""
🔧 Notion Integration API Layer for Orchestra AI
Provides seamless integration between Orchestra AI and Notion databases
"""

import requests
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
from enum import Enum

class NotionIntegrationError(Exception):
    """Custom exception for Notion integration errors"""
    pass

class CacheStrategy(Enum):
    """Cache strategies for different data types"""
    AGGRESSIVE = "aggressive"  # Cache for 1 hour
    MODERATE = "moderate"     # Cache for 15 minutes  
    MINIMAL = "minimal"       # Cache for 5 minutes
    REALTIME = "realtime"     # No caching

@dataclass
class NotionConfig:
    """Configuration for Notion integration"""
    api_token: str
    workspace_id: str
    databases: Dict[str, str]
    cache_ttl: Dict[str, int]
    webhook_secret: Optional[str] = None

class NotionAPIClient:
    """Enhanced Notion API client with caching and error handling"""
    
    def __init__(self, config: NotionConfig):
        self.config = config
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {config.api_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.cache = {}
        self.cache_timestamps = {}
        self.logger = logging.getLogger(__name__)
        
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make async HTTP request to Notion API with error handling"""
        url = f"{self.base_url}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(
                    method, url, headers=self.headers, json=data
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise NotionIntegrationError(
                            f"Notion API error {response.status}: {error_text}"
                        )
            except aiohttp.ClientError as e:
                raise NotionIntegrationError(f"Network error: {str(e)}")
    
    def _get_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """Generate cache key for request"""
        key = endpoint
        if params:
            key += "_" + "_".join(f"{k}:{v}" for k, v in sorted(params.items()))
        return key
    
    def _is_cache_valid(self, cache_key: str, strategy: CacheStrategy) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache_timestamps:
            return False
            
        if strategy == CacheStrategy.REALTIME:
            return False
            
        ttl_map = {
            CacheStrategy.AGGRESSIVE: 3600,  # 1 hour
            CacheStrategy.MODERATE: 900,     # 15 minutes
            CacheStrategy.MINIMAL: 300       # 5 minutes
        }
        
        ttl = ttl_map.get(strategy, 300)
        age = (datetime.now() - self.cache_timestamps[cache_key]).total_seconds()
        return age < ttl
    
    async def get_database_items(
        self, 
        database_name: str, 
        filters: Optional[Dict] = None,
        cache_strategy: CacheStrategy = CacheStrategy.MODERATE
    ) -> List[Dict]:
        """Get items from a database with caching"""
        
        if database_name not in self.config.databases:
            raise NotionIntegrationError(f"Database '{database_name}' not configured")
            
        database_id = self.config.databases[database_name]
        cache_key = self._get_cache_key(f"database_{database_id}", filters)
        
        # Check cache first
        if self._is_cache_valid(cache_key, cache_strategy):
            self.logger.debug(f"Cache hit for {database_name}")
            return self.cache[cache_key]
        
        # Query database
        query_data = {}
        if filters:
            query_data["filter"] = filters
            
        try:
            response = await self._make_request(
                "POST", f"databases/{database_id}/query", query_data
            )
            
            items = response.get("results", [])
            
            # Cache the results
            self.cache[cache_key] = items
            self.cache_timestamps[cache_key] = datetime.now()
            
            self.logger.info(f"Retrieved {len(items)} items from {database_name}")
            return items
            
        except NotionIntegrationError as e:
            self.logger.error(f"Failed to query {database_name}: {str(e)}")
            # Return cached data if available, even if stale
            if cache_key in self.cache:
                self.logger.warning(f"Returning stale cache for {database_name}")
                return self.cache[cache_key]
            raise
    
    async def create_database_item(
        self, 
        database_name: str, 
        properties: Dict[str, Any]
    ) -> Dict:
        """Create new item in database"""
        
        if database_name not in self.config.databases:
            raise NotionIntegrationError(f"Database '{database_name}' not configured")
            
        database_id = self.config.databases[database_name]
        
        data = {
            "parent": {"database_id": database_id},
            "properties": properties
        }
        
        try:
            result = await self._make_request("POST", "pages", data)
            
            # Invalidate cache for this database
            self._invalidate_database_cache(database_id)
            
            self.logger.info(f"Created item in {database_name}")
            return result
            
        except NotionIntegrationError as e:
            self.logger.error(f"Failed to create item in {database_name}: {str(e)}")
            raise
    
    async def update_database_item(
        self, 
        page_id: str, 
        properties: Dict[str, Any]
    ) -> Dict:
        """Update existing database item"""
        
        data = {"properties": properties}
        
        try:
            result = await self._make_request("PATCH", f"pages/{page_id}", data)
            
            # Invalidate relevant caches
            self._invalidate_all_caches()
            
            self.logger.info(f"Updated page {page_id}")
            return result
            
        except NotionIntegrationError as e:
            self.logger.error(f"Failed to update page {page_id}: {str(e)}")
            raise
    
    def _invalidate_database_cache(self, database_id: str):
        """Invalidate cache entries for specific database"""
        keys_to_remove = [
            key for key in self.cache.keys() 
            if f"database_{database_id}" in key
        ]
        for key in keys_to_remove:
            del self.cache[key]
            del self.cache_timestamps[key]
    
    def _invalidate_all_caches(self):
        """Invalidate all cached data"""
        self.cache.clear()
        self.cache_timestamps.clear()

class OrchestrationNotionBridge:
    """High-level bridge between Orchestra AI and Notion"""
    
    def __init__(self, notion_client: NotionAPIClient):
        self.notion = notion_client
        self.logger = logging.getLogger(__name__)
    
    async def get_active_tasks(self, assignee: Optional[str] = None) -> List[Dict]:
        """Get active tasks, optionally filtered by assignee"""
        filters = {
            "and": [
                {
                    "property": "Status",
                    "select": {
                        "does_not_equal": "Done"
                    }
                }
            ]
        }
        
        if assignee:
            filters["and"].append({
                "property": "Assignee",
                "select": {
                    "equals": assignee
                }
            })
        
        return await self.notion.get_database_items(
            "📋 Task Management", 
            filters,
            CacheStrategy.MINIMAL
        )
    
    async def create_task(
        self, 
        title: str, 
        description: str,
        assignee: str = "Human Developer",
        priority: str = "Medium",
        task_type: str = "Feature"
    ) -> Dict:
        """Create new task in task management database"""
        
        properties = {
            "Title": {"title": [{"text": {"content": title}}]},
            "Description": {"rich_text": [{"text": {"content": description}}]},
            "Assignee": {"select": {"name": assignee}},
            "Priority": {"select": {"name": priority}},
            "Type": {"select": {"name": task_type}},
            "Status": {"select": {"name": "Ready"}}
        }
        
        return await self.notion.create_database_item("📋 Task Management", properties)
    
    async def get_patrick_instructions(self, category: Optional[str] = None) -> List[Dict]:
        """Get Patrick instructions, optionally filtered by category"""
        filters = None
        if category:
            filters = {
                "property": "Category",
                "select": {
                    "equals": category
                }
            }
        
        return await self.notion.get_database_items(
            "📖 Patrick Instructions",
            filters,
            CacheStrategy.AGGRESSIVE
        )
    
    async def log_development_activity(
        self,
        title: str,
        activity_type: str,
        tool_used: str,
        notes: str,
        files_changed: int = 0
    ) -> Dict:
        """Log development activity to development log"""
        
        properties = {
            "Title": {"title": [{"text": {"content": title}}]},
            "Type": {"select": {"name": activity_type}},
            "Tool Used": {"select": {"name": tool_used}},
            "Notes": {"rich_text": [{"text": {"content": notes}}]},
            "Files Changed": {"number": files_changed},
            "Date": {"date": {"start": datetime.now().isoformat()}}
        }
        
        return await self.notion.create_database_item("💻 Development Log", properties)
    
    async def get_persona_features(self, persona: str) -> List[Dict]:
        """Get features for specific persona"""
        database_map = {
            "cherry": "🍒 Cherry Features",
            "sophia": "👩‍💼 Sophia Features", 
            "karen": "👩‍⚕️ Karen Features"
        }
        
        if persona not in database_map:
            raise ValueError(f"Unknown persona: {persona}")
        
        return await self.notion.get_database_items(
            database_map[persona],
            cache_strategy=CacheStrategy.MODERATE
        )
    
    async def search_knowledge_base(self, query: str) -> List[Dict]:
        """Search knowledge base for relevant information"""
        # For now, get all knowledge items and filter client-side
        # In production, this could use Notion's search API
        all_items = await self.notion.get_database_items(
            "📚 Knowledge Base",
            cache_strategy=CacheStrategy.MODERATE
        )
        
        # Simple text search in title and content
        query_lower = query.lower()
        matching_items = []
        
        for item in all_items:
            title = item.get("properties", {}).get("Knowledge Item", {}).get("title", [{}])[0].get("text", {}).get("content", "")
            content = item.get("properties", {}).get("Detailed Content", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "")
            
            if query_lower in title.lower() or query_lower in content.lower():
                matching_items.append(item)
        
        return matching_items

class NotionWebhookHandler:
    """Handle webhooks from Notion for real-time updates"""
    
    def __init__(self, notion_bridge: OrchestrationNotionBridge, webhook_secret: str):
        self.bridge = notion_bridge
        self.webhook_secret = webhook_secret
        self.logger = logging.getLogger(__name__)
    
    async def handle_webhook(self, payload: Dict, signature: str) -> bool:
        """Process incoming webhook from Notion"""
        
        # Verify webhook signature (implement based on Notion's webhook security)
        if not self._verify_signature(payload, signature):
            self.logger.warning("Invalid webhook signature")
            return False
        
        event_type = payload.get("type")
        object_type = payload.get("object")
        
        if event_type == "page" and object_type == "database":
            await self._handle_database_change(payload)
        
        return True
    
    def _verify_signature(self, payload: Dict, signature: str) -> bool:
        """Verify webhook signature (implement based on Notion's requirements)"""
        # Placeholder for signature verification
        return True
    
    async def _handle_database_change(self, payload: Dict):
        """Handle database change events"""
        page_id = payload.get("id")
        action = payload.get("action", "updated")
        
        self.logger.info(f"Database change: {action} for page {page_id}")
        
        # Invalidate relevant caches
        self.bridge.notion._invalidate_all_caches()
        
        # Trigger any necessary application updates
        await self._notify_application_of_change(page_id, action)
    
    async def _notify_application_of_change(self, page_id: str, action: str):
        """Notify the main application of Notion changes"""
        # This would integrate with your application's event system
        # For example, updating UI components or triggering workflows
        pass

# Configuration factory
def create_notion_config() -> NotionConfig:
    """Create Notion configuration with environment variables for security"""
    import os
    import warnings
    
    # Get API token from environment (practical security for solo dev)
    api_token = os.getenv("NOTION_API_TOKEN")
    if not api_token:
        # Development fallback with clear warning
        api_token = "ntn_development_fallback_token"
        warnings.warn("⚠️  Using development fallback for NOTION_API_TOKEN. Set environment variable for production.")
    
    workspace_id = os.getenv("NOTION_WORKSPACE_ID", "20bdba04940280ca9ba7f9bce721f547")
    
    return NotionConfig(
        api_token=api_token,
        workspace_id=workspace_id,
        databases={
            "🎯 Epic & Feature Tracking": "20bdba04-9402-8114-b57b-df7f1d4b2712",
            "📋 Task Management": "20bdba04-9402-81a2-99f3-e69dc37b73d6",
            "💻 Development Log": "20bdba04-9402-81fd-9558-d66c07d9576c",
            "🍒 Cherry Features": "20bdba04-9402-8162-9e3c-fa8c8e41fd16",
            "👩‍💼 Sophia Features": "20bdba04-9402-811d-83b4-cdc1a2505623",
            "👩‍⚕️ Karen Features": "20bdba04-9402-819c-b2ca-d3d3828691e6",
            "📖 Patrick Instructions": "20bdba04-9402-81b4-9890-e663db2b50a3",
            "📚 Knowledge Base": "20bdba04-9402-81a4-bc27-e06d160e3378",
            "📊 AI Tool Metrics": "20bdba04-9402-81c1-a1b2-c3d4e5f6g7h8",
            "🔗 MCP Connections": "20bdba04-9402-81c2-a1b2-c3d4e5f6g7h9", 
            "🧠 Code Reflection": "20bdba04-9402-81c3-a1b2-c3d4e5f6g7i0",
            "📈 Project Metrics": "20bdba04-9402-81c4-a1b2-c3d4e5f6g7i1"
        },
        cache_ttl={
            "tasks": 300,      # 5 minutes
            "instructions": 3600,  # 1 hour
            "features": 900,   # 15 minutes
            "knowledge": 1800, # 30 minutes
            "metrics": 120,    # 2 minutes (for real-time monitoring)
            "connections": 60  # 1 minute (for active monitoring)
        }
    )

# Example usage and testing
async def main():
    """Example usage of the Notion integration"""
    
    config = create_notion_config()
    client = NotionAPIClient(config)
    bridge = OrchestrationNotionBridge(client)
    
    try:
        # Get active tasks
        tasks = await bridge.get_active_tasks()
        print(f"Found {len(tasks)} active tasks")
        
        # Create a new task
        new_task = await bridge.create_task(
            "Test Notion Integration",
            "Verify that the Notion API integration is working correctly",
            assignee="Human Developer",
            priority="High"
        )
        print(f"Created task: {new_task['id']}")
        
        # Get Patrick instructions for daily operations
        daily_instructions = await bridge.get_patrick_instructions("Daily Operations")
        print(f"Found {len(daily_instructions)} daily instructions")
        
        # Log development activity
        await bridge.log_development_activity(
            "Notion Integration Implementation",
            "Code",
            "Manual",
            "Implemented comprehensive Notion API integration layer",
            files_changed=3
        )
        print("Logged development activity")
        
        # Search knowledge base
        knowledge_items = await bridge.search_knowledge_base("API integration")
        print(f"Found {len(knowledge_items)} knowledge items")
        
    except NotionIntegrationError as e:
        print(f"Integration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

