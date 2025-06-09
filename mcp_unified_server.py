#!/usr/bin/env python3
"""
🎯 Unified MCP Server for Orchestra AI - Clean & Simple Implementation
Provides shared context and capabilities across Cursor, Roo, and Continue
Integrated with Notion workspace for centralized project management
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import requests

# MCP imports
from mcp.server import Server
from mcp import types
from mcp.server.stdio import stdio_server

# Local imports
try:
    from config.notion_config import get_config, NotionConfig
except ImportError:
    # Fallback for simple setup
    @dataclass
    class NotionConfig:
        api_token: str
        workspace_id: str
        databases: Dict[str, str]
    
    def get_config():
        from dataclasses import dataclass
        
        @dataclass
        class SimpleDatabases:
            mcp_connections: str = "20bdba04940281aea36af6144ec68df2"
            code_reflection: str = "20bdba049402814d8e53fbec166ef030"
            ai_tool_metrics: str = "20bdba049402813f8404fa8d5f615b02"
            task_management: str = "20bdba04940281a299f3e69dc37b73d6"
        
        # Simple environment-based config with development fallbacks
        api_token = os.getenv("NOTION_API_TOKEN")
        if not api_token:
            api_token = "ntn_development_fallback"
            print("⚠️  MCP Server using development fallback for NOTION_API_TOKEN")
        
        return NotionConfig(
            api_token=api_token,
            workspace_id=os.getenv("NOTION_WORKSPACE_ID", "20bdba04940280ca9ba7f9bce721f547"),
            databases=SimpleDatabases()
        )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleNotionIntegration:
    """Simple Notion API integration for MCP server logging"""
    
    def __init__(self, config: NotionConfig):
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {config.api_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    async def log_activity(self, tool_name: str, activity: str, context: Dict[str, Any] = None):
        """Log MCP activity to Notion - simple implementation"""
        if not context:
            context = {}
            
        try:
            url = "https://api.notion.com/v1/pages"
            data = {
                "parent": {"database_id": self.config.databases.mcp_connections},
                "properties": {
                    "Tool": {"title": [{"text": {"content": tool_name}}]},
                    "Activity": {"rich_text": [{"text": {"content": activity}}]},
                    "Status": {"select": {"name": "Active"}},
                    "Context": {"rich_text": [{"text": {"content": json.dumps(context, indent=2)[:2000]}}]},
                    "Timestamp": {"date": {"start": datetime.now().isoformat()}}
                }
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to log to Notion: {e}")
            return False
    
    async def update_metrics(self, tool_name: str, metrics: Dict[str, Any]):
        """Update tool performance metrics in Notion"""
        try:
            url = "https://api.notion.com/v1/pages"
            data = {
                "parent": {"database_id": self.config.databases.ai_tool_metrics},
                "properties": {
                    "Tool": {"title": [{"text": {"content": tool_name}}]},
                    "Metric Type": {"select": {"name": "Performance"}},
                    "Value": {"number": metrics.get("response_time", 0)},
                    "Status": {"select": {"name": "Good"}},
                    "Details": {"rich_text": [{"text": {"content": json.dumps(metrics, indent=2)[:2000]}}]},
                    "Timestamp": {"date": {"start": datetime.now().isoformat()}}
                }
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
            return False

class ContextManager:
    """Simple context management for tool coordination"""
    
    def __init__(self, notion: SimpleNotionIntegration):
        self.tool_contexts: Dict[str, Dict[str, Any]] = {}
        self.shared_memory: Dict[str, Any] = {}
        self.notion = notion
        
    async def register_tool(self, tool_name: str) -> bool:
        """Register a tool for context sharing"""
        if tool_name not in self.tool_contexts:
            self.tool_contexts[tool_name] = {
                "active_files": [],
                "current_task": None,
                "context_data": {},
                "last_updated": datetime.now().isoformat()
            }
            
            await self.notion.log_activity(
                tool_name, 
                "Tool Registration", 
                {"registered_at": datetime.now().isoformat()}
            )
            
            logger.info(f"Registered tool: {tool_name}")
            return True
        return False
    
    async def update_context(self, tool_name: str, context: Dict[str, Any]) -> bool:
        """Update context for a tool"""
        if tool_name in self.tool_contexts:
            self.tool_contexts[tool_name]["context_data"].update(context)
            self.tool_contexts[tool_name]["last_updated"] = datetime.now().isoformat()
            
            # Sync important context to shared memory
            if tool_name == "cursor" and "file_changes" in context:
                self.shared_memory["recent_changes"] = context["file_changes"]
            elif tool_name == "roo" and "architecture" in context:
                self.shared_memory["architecture"] = context["architecture"]
            elif tool_name == "continue" and "ui_components" in context:
                self.shared_memory["components"] = context["ui_components"]
            
            await self.notion.log_activity(
                tool_name,
                "Context Update",
                {"updated_keys": list(context.keys())}
            )
            
            return True
        return False
    
    def get_context_for_tool(self, requesting_tool: str) -> Dict[str, Any]:
        """Get relevant context for a requesting tool"""
        base_context = {
            "workspace_url": f"https://www.notion.so/Orchestra-AI-Workspace-{self.notion.config.workspace_id}",
            "last_sync": datetime.now().isoformat()
        }
        
        if requesting_tool == "cursor":
            base_context.update({
                "active_files": self._get_all_active_files(),
                "recent_changes": self.shared_memory.get("recent_changes", []),
                "architecture": self.shared_memory.get("architecture", {})
            })
        elif requesting_tool == "roo":
            base_context.update({
                "project_context": self.shared_memory.get("project_context", {}),
                "workflows": self.shared_memory.get("workflows", []),
                "mcp_servers": {"status": "active", "tools": list(self.tool_contexts.keys())}
            })
        elif requesting_tool == "continue":
            base_context.update({
                "ui_context": self.shared_memory.get("ui_context", {}),
                "components": self.shared_memory.get("components", {}),
                "design_system": self.shared_memory.get("design_system", {})
            })
        
        return base_context
    
    def _get_all_active_files(self) -> List[str]:
        """Get all active files across tools"""
        all_files = []
        for context in self.tool_contexts.values():
            all_files.extend(context.get("active_files", []))
        return list(set(all_files))

class OrchestralMCPServer:
    """Unified MCP Server - Clean & Simple Implementation"""
    
    def __init__(self):
        self.config = get_config()
        self.notion = SimpleNotionIntegration(self.config)
        self.context_manager = ContextManager(self.notion)
        self.server = Server("orchestra-unified")
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup MCP tools for unified operations"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available tools"""
            return [
                types.Tool(
                    name="register_tool",
                    description="Register a coding tool (cursor, roo, continue) for context sharing",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "tool_name": {"type": "string", "enum": ["cursor", "roo", "continue"]},
                        },
                        "required": ["tool_name"]
                    }
                ),
                types.Tool(
                    name="get_shared_context",
                    description="Get shared context for optimal tool coordination",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "requesting_tool": {"type": "string"},
                        },
                        "required": ["requesting_tool"]
                    }
                ),
                types.Tool(
                    name="route_task",
                    description="Route a task to the optimal tool",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_description": {"type": "string"},
                            "task_type": {"type": "string", "enum": ["coding", "ui", "workflow", "debug", "research", "notion"]},
                            "complexity": {"type": "string", "enum": ["simple", "medium", "complex"]},
                        },
                        "required": ["task_description", "task_type"]
                    }
                ),
                types.Tool(
                    name="get_notion_workspace",
                    description="Get Notion workspace information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "info_type": {"type": "string", "enum": ["workspace", "databases", "all"]},
                        }
                    }
                ),
                types.Tool(
                    name="log_insight",
                    description="Log insights and reflections to Notion",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "tool_name": {"type": "string"},
                            "insight": {"type": "string"},
                            "category": {"type": "string", "enum": ["performance", "workflow", "optimization", "learning"]},
                        },
                        "required": ["tool_name", "insight", "category"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
            """Handle tool calls"""
            
            if name == "register_tool":
                tool_name = arguments["tool_name"]
                success = await self.context_manager.register_tool(tool_name)
                return [types.TextContent(
                    type="text",
                    text=f"Tool {tool_name} {'registered successfully' if success else 'already registered'}"
                )]
            
            elif name == "get_shared_context":
                requesting_tool = arguments["requesting_tool"]
                context = self.context_manager.get_context_for_tool(requesting_tool)
                return [types.TextContent(
                    type="text",
                    text=json.dumps(context, indent=2)
                )]
            
            elif name == "route_task":
                task_description = arguments["task_description"]
                task_type = arguments["task_type"]
                complexity = arguments.get("complexity", "medium")
                
                optimal_tool = self._route_task(task_type, complexity, task_description)
                reason = self._get_routing_reason(optimal_tool, task_type, complexity)
                
                await self.notion.log_activity(
                    "task_router",
                    "Task Routing",
                    {
                        "task": task_description,
                        "type": task_type,
                        "complexity": complexity,
                        "routed_to": optimal_tool
                    }
                )
                
                return [types.TextContent(
                    type="text",
                    text=f"Optimal tool: {optimal_tool}\nReason: {reason}"
                )]
            
            elif name == "get_notion_workspace":
                info_type = arguments.get("info_type", "all")
                workspace_info = self._get_workspace_info(info_type)
                return [types.TextContent(
                    type="text",
                    text=json.dumps(workspace_info, indent=2)
                )]
            
            elif name == "log_insight":
                tool_name = arguments["tool_name"]
                insight = arguments["insight"]
                category = arguments["category"]
                
                success = await self._log_insight(tool_name, insight, category)
                return [types.TextContent(
                    type="text",
                    text=f"Insight {'logged successfully' if success else 'logging failed'}"
                )]
            
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    def _route_task(self, task_type: str, complexity: str, description: str) -> str:
        """Simple task routing logic"""
        description_lower = description.lower()
        
        # Notion tasks go to Roo
        if task_type == "notion" or "notion" in description_lower:
            return "roo"
        
        # UI tasks go to Continue
        if task_type == "ui" or any(word in description_lower for word in ["component", "interface", "react", "ui"]):
            return "continue"
        
        # Complex workflows go to Roo
        if task_type == "workflow" or complexity == "complex" or "research" in description_lower:
            return "roo"
        
        # Simple coding goes to Cursor
        if task_type in ["coding", "debug"] and complexity in ["simple", "medium"]:
            return "cursor"
        
        # Default to Cursor
        return "cursor"
    
    def _get_routing_reason(self, tool: str, task_type: str, complexity: str) -> str:
        """Get routing explanation"""
        reasons = {
            "continue": "UI-GPT-4o excels at React/TypeScript and UI development",
            "roo": "Specialized modes handle complex workflows and research optimally", 
            "cursor": "Native AI integration provides best experience for general coding"
        }
        return reasons.get(tool, "General purpose tool selection")
    
    def _get_workspace_info(self, info_type: str) -> Dict[str, Any]:
        """Get workspace information"""
        base_url = f"https://www.notion.so/Orchestra-AI-Workspace-{self.config.workspace_id}"
        
        workspace_info = {
            "workspace_url": base_url,
            "databases": {
                "mcp_connections": f"{base_url}?v=mcp",
                "ai_tool_metrics": f"{base_url}?v=metrics", 
                "task_management": f"{base_url}?v=tasks",
                "code_reflection": f"{base_url}?v=reflection"
            }
        }
        
        if info_type == "workspace":
            return {"workspace_url": base_url}
        elif info_type == "databases":
            return {"databases": workspace_info["databases"]}
        else:
            return workspace_info
    
    async def _log_insight(self, tool_name: str, insight: str, category: str) -> bool:
        """Log insight to Notion code reflection database"""
        try:
            url = "https://api.notion.com/v1/pages"
            data = {
                "parent": {"database_id": self.config.databases.code_reflection},
                "properties": {
                    "Tool": {"title": [{"text": {"content": tool_name}}]},
                    "Category": {"select": {"name": category.title()}},
                    "Insight": {"rich_text": [{"text": {"content": insight}}]},
                    "Status": {"select": {"name": "New"}},
                    "Priority": {"select": {"name": "Medium"}},
                    "Date": {"date": {"start": datetime.now().isoformat()}}
                }
            }
            
            response = requests.post(url, headers=self.notion.headers, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to log insight: {e}")
            return False

async def main():
    """Main server execution"""
    logger.info("🚀 Starting Orchestra AI Unified MCP Server")
    
    # Test Notion connection
    config = get_config()
    notion = SimpleNotionIntegration(config)
    
    # Log server startup
    await notion.log_activity("mcp_server", "Server Startup", {"version": "2.0", "clean_rewrite": True})
    
    # Start MCP server
    server = OrchestralMCPServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            None  # Initialize options
        )

if __name__ == "__main__":
    asyncio.run(main())

