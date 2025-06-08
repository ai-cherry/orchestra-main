#!/usr/bin/env python3
"""
🎯 Unified MCP Server for Orchestra AI Ecosystem
Provides shared context and capabilities across Cursor, Roo, and Continue
Integrated with Notion workspace for centralized project management
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import requests
from datetime import datetime

# MCP imports
from mcp.server import Server
from mcp import types
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ToolContext:
    """Context information for different tools"""
    tool_name: str
    active_files: List[str]
    current_task: Optional[str]
    context_data: Dict[str, Any]
    last_updated: datetime

class NotionIntegration:
    """Notion API integration for MCP server"""
    
    def __init__(self):
        self.api_key = "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"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.databases = {
            "mcp_connections": "20bdba04940281aea36af6144ec68df2",
            "code_reflection": "20bdba049402814d8e53fbec166ef030",
            "ai_tool_metrics": "20bdba049402813f8404fa8d5f615b02",
            "task_management": "20bdba04940281a299f3e69dc37b73d6"
        }
    
    async def log_mcp_activity(self, tool_name: str, activity: str, context: Dict[str, Any]):
        """Log MCP activity to Notion"""
        try:
            url = f"https://api.notion.com/v1/pages"
            data = {
                "parent": {"database_id": self.databases["mcp_connections"]},
                "properties": {
                    "Tool": {"title": [{"text": {"content": tool_name}}]},
                    "Activity": {"rich_text": [{"text": {"content": activity}}]},
                    "Status": {"select": {"name": "Active"}},
                    "Context": {"rich_text": [{"text": {"content": json.dumps(context, indent=2)[:2000]}}]}
                }
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to log MCP activity: {e}")
            return False
    
    async def update_tool_metrics(self, tool_name: str, metrics: Dict[str, Any]):
        """Update tool performance metrics in Notion"""
        try:
            url = f"https://api.notion.com/v1/pages"
            data = {
                "parent": {"database_id": self.databases["ai_tool_metrics"]},
                "properties": {
                    "Tool": {"title": [{"text": {"content": tool_name}}]},
                    "Metric Type": {"select": {"name": "Performance"}},
                    "Value": {"number": metrics.get("response_time", 0)},
                    "Details": {"rich_text": [{"text": {"content": json.dumps(metrics, indent=2)[:2000]}}]}
                }
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to update tool metrics: {e}")
            return False

class UnifiedContextManager:
    """Manages shared context between Cursor, Roo, and Continue with Notion integration"""
    
    def __init__(self):
        self.contexts: Dict[str, ToolContext] = {}
        self.shared_memory: Dict[str, Any] = {}
        self.notion = NotionIntegration()
        
    async def register_tool(self, tool_name: str) -> bool:
        """Register a new tool for context sharing"""
        if tool_name not in self.contexts:
            self.contexts[tool_name] = ToolContext(
                tool_name=tool_name,
                active_files=[],
                current_task=None,
                context_data={},
                last_updated=datetime.now()
            )
            
            # Log registration to Notion
            await self.notion.log_mcp_activity(
                tool_name, 
                "Tool Registration", 
                {"registered_at": datetime.now().isoformat()}
            )
            
            logger.info(f"Registered tool: {tool_name}")
            return True
        return False
    
    async def update_context(self, tool_name: str, context: Dict[str, Any]) -> bool:
        """Update context for a specific tool"""
        if tool_name in self.contexts:
            self.contexts[tool_name].context_data.update(context)
            self.contexts[tool_name].last_updated = datetime.now()
            
            # Sync important context to shared memory
            await self._sync_to_shared_memory(tool_name, context)
            
            # Log context update to Notion
            await self.notion.log_mcp_activity(
                tool_name,
                "Context Update",
                {"updated_keys": list(context.keys()), "timestamp": datetime.now().isoformat()}
            )
            
            return True
        return False
    
    async def get_shared_context(self, requesting_tool: str) -> Dict[str, Any]:
        """Get shared context for a requesting tool"""
        # Filter context based on requesting tool's needs
        if requesting_tool == "cursor":
            context = {
                "active_files": self._get_all_active_files(),
                "recent_changes": self.shared_memory.get("recent_changes", []),
                "current_architecture": self.shared_memory.get("architecture", {}),
                "notion_workspace": "https://www.notion.so/Orchestra-AI-Workspace-20bdba04940280ca9ba7f9bce721f547"
            }
        elif requesting_tool == "roo":
            context = {
                "project_context": self.shared_memory.get("project_context", {}),
                "active_workflows": self.shared_memory.get("workflows", []),
                "mcp_servers": self.shared_memory.get("mcp_servers", {}),
                "notion_databases": self.notion.databases
            }
        elif requesting_tool == "continue":
            context = {
                "ui_context": self.shared_memory.get("ui_context", {}),
                "component_library": self.shared_memory.get("components", {}),
                "design_system": self.shared_memory.get("design_system", {}),
                "admin_interface": "/orchestra-admin-mvp/"
            }
        else:
            context = self.shared_memory
        
        # Log context access
        await self.notion.log_mcp_activity(
            requesting_tool,
            "Context Access",
            {"context_keys": list(context.keys()), "timestamp": datetime.now().isoformat()}
        )
        
        return context
    
    def _get_all_active_files(self) -> List[str]:
        """Get all active files across all tools"""
        all_files = []
        for context in self.contexts.values():
            all_files.extend(context.active_files)
        return list(set(all_files))  # Remove duplicates
    
    async def _sync_to_shared_memory(self, tool_name: str, context: Dict[str, Any]):
        """Sync important context to shared memory"""
        # Sync based on tool type and context importance
        if tool_name == "cursor" and "file_changes" in context:
            self.shared_memory["recent_changes"] = context["file_changes"]
        elif tool_name == "roo" and "architecture" in context:
            self.shared_memory["architecture"] = context["architecture"]
        elif tool_name == "continue" and "ui_components" in context:
            self.shared_memory["components"] = context["ui_components"]
        
        # Always update last sync time
        self.shared_memory["last_sync"] = datetime.now().isoformat()

class OrchestralMCPServer:
    """Unified MCP Server for Orchestra AI Ecosystem with Notion Integration"""
    
    def __init__(self):
        self.context_manager = UnifiedContextManager()
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
                    name="update_context",
                    description="Update context for a specific tool",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "tool_name": {"type": "string"},
                            "context": {"type": "object"},
                        },
                        "required": ["tool_name", "context"]
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
                    description="Route a task to the optimal tool (cursor, roo, or continue)",
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
                    name="sync_project_state",
                    description="Synchronize project state across all tools and Notion",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "force_sync": {"type": "boolean", "default": False},
                            "include_notion": {"type": "boolean", "default": True},
                        }
                    }
                ),
                types.Tool(
                    name="get_notion_workspace",
                    description="Get Notion workspace information and database links",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database_type": {"type": "string", "enum": ["all", "project", "ai_coding", "personas", "operations"]},
                        }
                    }
                ),
                types.Tool(
                    name="log_reflection",
                    description="Log insights and reflections to Notion for continuous improvement",
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
            
            elif name == "update_context":
                tool_name = arguments["tool_name"]
                context = arguments["context"]
                success = await self.context_manager.update_context(tool_name, context)
                return [types.TextContent(
                    type="text",
                    text=f"Context {'updated' if success else 'update failed'} for {tool_name}"
                )]
            
            elif name == "get_shared_context":
                requesting_tool = arguments["requesting_tool"]
                context = await self.context_manager.get_shared_context(requesting_tool)
                return [types.TextContent(
                    type="text",
                    text=json.dumps(context, indent=2)
                )]
            
            elif name == "route_task":
                task_description = arguments["task_description"]
                task_type = arguments["task_type"]
                complexity = arguments.get("complexity", "medium")
                
                # Intelligent task routing with Notion integration
                optimal_tool = self._route_task_to_tool(task_type, complexity, task_description)
                
                # Log routing decision to Notion
                await self.context_manager.notion.log_mcp_activity(
                    "task_router",
                    "Task Routing",
                    {
                        "task": task_description,
                        "type": task_type,
                        "complexity": complexity,
                        "routed_to": optimal_tool,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                return [types.TextContent(
                    type="text",
                    text=f"Optimal tool for task: {optimal_tool}\nReason: {self._get_routing_reason(optimal_tool, task_type, complexity)}"
                )]
            
            elif name == "sync_project_state":
                force_sync = arguments.get("force_sync", False)
                include_notion = arguments.get("include_notion", True)
                await self._sync_project_state(force_sync, include_notion)
                return [types.TextContent(
                    type="text",
                    text="Project state synchronized across all tools and Notion"
                )]
            
            elif name == "get_notion_workspace":
                database_type = arguments.get("database_type", "all")
                workspace_info = self._get_notion_workspace_info(database_type)
                return [types.TextContent(
                    type="text",
                    text=json.dumps(workspace_info, indent=2)
                )]
            
            elif name == "log_reflection":
                tool_name = arguments["tool_name"]
                insight = arguments["insight"]
                category = arguments["category"]
                
                # Log reflection to Notion
                success = await self._log_reflection_to_notion(tool_name, insight, category)
                
                return [types.TextContent(
                    type="text",
                    text=f"Reflection {'logged successfully' if success else 'logging failed'} for {tool_name}"
                )]
            
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    def _route_task_to_tool(self, task_type: str, complexity: str, description: str) -> str:
        """Route task to optimal tool based on type and complexity"""
        
        # Notion-related tasks
        if task_type == "notion" or "notion" in description.lower():
            return "roo"  # Roo handles Notion integration best
        
        # UI-related tasks go to Continue (UI-GPT-4o)
        if task_type == "ui" or "component" in description.lower() or "interface" in description.lower():
            return "continue"
        
        # Complex workflows and orchestration go to Roo
        if task_type == "workflow" or complexity == "complex" or "boomerang" in description.lower():
            return "roo"
        
        # Research tasks go to Roo (specialized research mode)
        if task_type == "research" or "research" in description.lower():
            return "roo"
        
        # Simple coding and debugging go to Cursor
        if task_type in ["coding", "debug"] and complexity in ["simple", "medium"]:
            return "cursor"
        
        # Complex coding goes to Roo (specialized modes)
        if task_type == "coding" and complexity == "complex":
            return "roo"
        
        # Default to Cursor for general tasks
        return "cursor"
    
    def _get_routing_reason(self, tool: str, task_type: str, complexity: str) -> str:
        """Get explanation for routing decision"""
        reasons = {
            "continue": "UI-GPT-4o excels at React/TypeScript component generation and UI tasks",
            "roo": "Specialized modes and boomerang tasks handle complex workflows and Notion integration optimally",
            "cursor": "Native AI integration provides best experience for general coding tasks"
        }
        return reasons.get(tool, "General purpose tool selection")
    
    def _get_notion_workspace_info(self, database_type: str) -> Dict[str, Any]:
        """Get Notion workspace information"""
        base_url = "https://www.notion.so/Orchestra-AI-Workspace-20bdba04940280ca9ba7f9bce721f547"
        
        all_databases = {
            "project": {
                "epic_tracking": "https://notion.so/20bdba0494028114b57bdf7f1d4b2712",
                "task_management": "https://notion.so/20bdba04940281a299f3e69dc37b73d6",
                "development_log": "https://notion.so/20bdba04940281fd9558d66c07d9576c"
            },
            "ai_coding": {
                "coding_rules": "https://notion.so/20bdba04940281bdadf1e78f4e0989e8",
                "mcp_connections": "https://notion.so/20bdba04940281aea36af6144ec68df2",
                "code_reflection": "https://notion.so/20bdba049402814d8e53fbec166ef030",
                "tool_metrics": "https://notion.so/20bdba049402813f8404fa8d5f615b02"
            },
            "personas": {
                "cherry_features": "https://notion.so/20bdba04940281629e3cfa8c8e41fd16",
                "sophia_features": "https://notion.so/20bdba049402811d83b4cdc1a2505623",
                "karen_features": "https://notion.so/20bdba049402819cb2cad3d3828691e6"
            },
            "operations": {
                "patrick_instructions": "https://notion.so/20bdba04940281b49890e663db2b50a3",
                "knowledge_base": "https://notion.so/20bdba04940281a4bc27e06d160e3378"
            }
        }
        
        if database_type == "all":
            return {"workspace_url": base_url, "databases": all_databases}
        elif database_type in all_databases:
            return {"workspace_url": base_url, "databases": {database_type: all_databases[database_type]}}
        else:
            return {"workspace_url": base_url, "databases": {}}
    
    async def _log_reflection_to_notion(self, tool_name: str, insight: str, category: str) -> bool:
        """Log reflection to Notion code reflection database"""
        try:
            url = f"https://api.notion.com/v1/pages"
            data = {
                "parent": {"database_id": self.context_manager.notion.databases["code_reflection"]},
                "properties": {
                    "Tool": {"title": [{"text": {"content": tool_name}}]},
                    "Category": {"select": {"name": category.title()}},
                    "Insight": {"rich_text": [{"text": {"content": insight}}]},
                    "Status": {"select": {"name": "New"}},
                    "Priority": {"select": {"name": "Medium"}}
                }
            }
            
            response = requests.post(url, headers=self.context_manager.notion.headers, json=data)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to log reflection: {e}")
            return False
    
    async def _sync_project_state(self, force_sync: bool = False, include_notion: bool = True):
        """Synchronize project state across all tools and Notion"""
        logger.info(f"Synchronizing project state (force: {force_sync}, notion: {include_notion})")
        
        # Read current project files
        project_files = self._scan_project_files()
        
        # Update shared memory with current state
        self.context_manager.shared_memory.update({
            "project_files": project_files,
            "last_sync": datetime.now().isoformat(),
            "sync_forced": force_sync,
            "notion_included": include_notion
        })
        
        # Log sync to Notion if enabled
        if include_notion:
            await self.context_manager.notion.log_mcp_activity(
                "sync_manager",
                "Project State Sync",
                {
                    "files_scanned": len(project_files.get("source_files", [])),
                    "force_sync": force_sync,
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    def _scan_project_files(self) -> Dict[str, Any]:
        """Scan project files for current state"""
        project_root = Path.cwd()
        important_files = {
            "config_files": [],
            "source_files": [],
            "documentation": [],
            "notion_integration": []
        }
        
        # Scan for important file types
        for file_path in project_root.rglob("*"):
            if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts[1:]):
                if file_path.suffix in [".py", ".ts", ".tsx", ".js", ".jsx"]:
                    important_files["source_files"].append(str(file_path))
                elif file_path.suffix in [".md", ".txt", ".rst"]:
                    important_files["documentation"].append(str(file_path))
                elif file_path.name in [".roomodes", ".continue", "package.json", "requirements.txt"]:
                    important_files["config_files"].append(str(file_path))
                elif "notion" in file_path.name.lower():
                    important_files["notion_integration"].append(str(file_path))
        
        return important_files

async def main():
    """Main entry point for the unified MCP server"""
    server_instance = OrchestralMCPServer()
    
    # Initialize context for known tools
    await server_instance.context_manager.register_tool("cursor")
    await server_instance.context_manager.register_tool("roo")
    await server_instance.context_manager.register_tool("continue")
    
    logger.info("Starting Orchestra Unified MCP Server with Notion Integration...")
    
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="orchestra-unified",
                server_version="2.0.0",
                            capabilities=server_instance.server.get_capabilities(
                notification_options=types.NotificationParams(),
                experimental_capabilities={}
            )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())

