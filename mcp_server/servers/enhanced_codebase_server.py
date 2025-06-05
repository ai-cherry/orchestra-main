#!/usr/bin/env python3
"""
Cherry AI Orchestrator - Optimized MCP Codebase Server
Streamlined for Cursor AI Max Mode and Roo integration
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from pydantic import AnyUrl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cherry-ai-codebase")

# Server configuration
server = Server("cherry-ai-codebase")

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODEBASE_PATHS = [
    PROJECT_ROOT / "admin-interface",
    PROJECT_ROOT / "infrastructure", 
    PROJECT_ROOT / "mcp_server",
    PROJECT_ROOT / "agent",
    PROJECT_ROOT / ".cursor",
    PROJECT_ROOT / ".roo",
    PROJECT_ROOT / "scripts"
]

class CherryAICodebaseManager:
    """Optimized codebase management for Cursor AI and Roo with enhanced capabilities"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.file_cache = {}
        self.command_history = []
        self.context_cache = {}
        self.cursor_integration = os.getenv("ENABLE_CURSOR_INTEGRATION", "false").lower() == "true"
        self.roo_integration = os.getenv("ENABLE_ROO_INTEGRATION", "false").lower() == "true"
        
    def add_command_to_history(self, command: str, context: Dict[str, Any]) -> None:
        """Add command to history for pattern recognition"""
        self.command_history.append({
            "timestamp": asyncio.get_event_loop().time(),
            "command": command,
            "context": context,
            "project_state": self._get_project_state_snapshot()
        })
        # Keep only last 100 commands
        if len(self.command_history) > 100:
            self.command_history.pop(0)
    
    def _get_project_state_snapshot(self) -> Dict[str, Any]:
        """Get current project state for context awareness"""
        try:
            # Get recent git activity
            git_status = subprocess.run(
                ["git", "status", "--porcelain"], 
                cwd=self.project_root, 
                capture_output=True, 
                text=True
            ).stdout.strip()
            
            git_branch = subprocess.run(
                ["git", "branch", "--show-current"], 
                cwd=self.project_root, 
                capture_output=True, 
                text=True
            ).stdout.strip()
            
            return {
                "git_status": git_status,
                "git_branch": git_branch,
                "modified_files": len(git_status.split('\n')) if git_status else 0,
                "timestamp": asyncio.get_event_loop().time()
            }
        except Exception:
            return {"error": "Could not get git status"}
    
    def get_smart_context_suggestions(self, current_task: str) -> Dict[str, Any]:
        """Provide smart context suggestions based on current task and history"""
        suggestions = {
            "relevant_files": [],
            "suggested_commands": [],
            "context_patterns": [],
            "workflow_recommendations": []
        }
        
        # Analyze current task for context clues
        task_lower = current_task.lower()
        
        # File suggestions based on task keywords
        if any(word in task_lower for word in ["database", "db", "sql", "postgres", "redis"]):
            suggestions["relevant_files"].extend([
                "infrastructure/database_layer/",
                "infrastructure/database_schema.sql",
                "test_mcp_data.py"
            ])
            suggestions["suggested_commands"].extend([
                "analyze_project database",
                "search_codebase database",
                "read_file infrastructure/database_schema.sql"
            ])
        
        if any(word in task_lower for word in ["deploy", "infrastructure", "server", "vultr"]):
            suggestions["relevant_files"].extend([
                "infrastructure/",
                "deploy_to_production.sh",
                ".github/workflows/"
            ])
            suggestions["suggested_commands"].extend([
                "analyze_project infrastructure",
                "search_codebase deploy",
                "get_file_structure infrastructure"
            ])
        
        if any(word in task_lower for word in ["admin", "interface", "ui", "frontend"]):
            suggestions["relevant_files"].extend([
                "admin-interface/",
                "admin-interface/enhanced-production-interface.html"
            ])
            suggestions["suggested_commands"].extend([
                "get_file_structure admin-interface",
                "search_codebase interface",
                "read_file admin-interface/enhanced-production-interface.html"
            ])
        
        # Pattern recognition from command history
        recent_commands = self.command_history[-10:] if self.command_history else []
        if recent_commands:
            command_patterns = {}
            for cmd in recent_commands:
                cmd_type = cmd["command"].split()[0] if cmd["command"] else "unknown"
                command_patterns[cmd_type] = command_patterns.get(cmd_type, 0) + 1
            
            suggestions["context_patterns"] = [
                f"Recent focus on {cmd_type} commands ({count} times)"
                for cmd_type, count in command_patterns.items()
            ]
        
        # Workflow recommendations
        if "test" in task_lower:
            suggestions["workflow_recommendations"].append(
                "Consider running system integration tests: python3 test_system_integration.py"
            )
        
        if "deploy" in task_lower:
            suggestions["workflow_recommendations"].append(
                "Recommended deployment workflow: test locally → staging → production"
            )
        
        return suggestions
        
    def get_project_overview(self) -> Dict[str, Any]:
        """Get comprehensive project overview optimized for AI assistants"""
        return {
            "project_name": "Cherry AI Orchestrator",
            "architecture": {
                "production_server": "45.32.69.157 (16 vCPUs, 64GB RAM)",
                "database_server": "45.77.87.106 (PostgreSQL, Redis)",
                "staging_server": "207.246.108.201",
                "infrastructure": "Vultr cloud with Pulumi IaC"
            },
            "end_user_application": {
                "note": "The final application has three AI personas (Cherry, Sophia, Karen) for END USERS",
                "cherry_personal": "Personal assistant for end users",
                "sophia_business": "Business intelligence for end users", 
                "karen_healthcare": "Healthcare AI for end users",
                "important": "These personas are for the application users, NOT for development workflow"
            },
            "tech_stack": {
                "frontend": ["HTML5", "CSS3", "Vanilla JavaScript"],
                "backend": ["Python 3.11", "Flask", "FastAPI"],
                "databases": ["PostgreSQL", "Redis", "Weaviate", "Pinecone"],
                "ai_services": ["Anthropic Claude", "Google Gemini"],
                "infrastructure": ["Vultr", "Pulumi", "GitHub Actions"]
            },
            "key_directories": {
                "admin_interface": "Three AI personas interface for end users",
                "infrastructure": "Infrastructure management and deployment",
                "mcp_server": "MCP servers for development tool integration",
                "agent": "FastAPI agent application",
                ".cursor": "Cursor AI configuration",
                ".roo": "Roo integration and custom development modes"
            },
            "development_tools": {
                "cursor_ai": "Primary IDE with Max Mode for large context",
                "roo_code": "Custom modes for development tasks (cherry-dev, infra, database)",
                "mcp_servers": "Three optimized servers (codebase, infrastructure, database)"
            }
        }
    
    def get_file_structure(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Get file structure for specific path or entire project"""
        target_path = Path(path) if path else self.project_root
        if not target_path.exists():
            return {"error": f"Path {target_path} does not exist"}
        
        structure = {}
        try:
            if target_path.is_file():
                return {
                    "type": "file",
                    "name": target_path.name,
                    "size": target_path.stat().st_size,
                    "extension": target_path.suffix
                }
            
            for item in target_path.iterdir():
                if item.name.startswith('.') and item.name not in ['.cursor', '.roo', '.github']:
                    continue
                if item.name in ['__pycache__', 'node_modules', '.git']:
                    continue
                    
                if item.is_dir():
                    structure[item.name] = {
                        "type": "directory",
                        "items": len(list(item.iterdir())) if item.exists() else 0
                    }
                else:
                    structure[item.name] = {
                        "type": "file",
                        "size": item.stat().st_size,
                        "extension": item.suffix
                    }
        except PermissionError:
            return {"error": f"Permission denied accessing {target_path}"}
        
        return structure
    
    def read_file_content(self, file_path: str, max_lines: int = 1000) -> Dict[str, Any]:
        """Read file content with intelligent truncation"""
        try:
            full_path = self.project_root / file_path
            if not full_path.exists():
                return {"error": f"File {file_path} does not exist"}
            
            if full_path.suffix in ['.pyc', '.so', '.dll', '.exe']:
                return {"error": f"Binary file {file_path} cannot be read as text"}
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if len(lines) <= max_lines:
                content = ''.join(lines)
            else:
                # Intelligent truncation for large files
                header_lines = lines[:50]
                footer_lines = lines[-50:]
                middle_info = f"\n\n... [File truncated: {len(lines) - 100} lines omitted] ...\n\n"
                content = ''.join(header_lines) + middle_info + ''.join(footer_lines)
            
            return {
                "file_path": file_path,
                "content": content,
                "total_lines": len(lines),
                "truncated": len(lines) > max_lines,
                "file_type": full_path.suffix,
                "size_bytes": full_path.stat().st_size
            }
        except Exception as e:
            return {"error": f"Error reading {file_path}: {str(e)}"}
    
    def search_codebase(self, query: str, file_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Search codebase for specific patterns"""
        if not file_types:
            file_types = ['.py', '.js', '.html', '.css', '.md', '.json', '.yaml', '.yml']
        
        results = []
        try:
            for path in CODEBASE_PATHS:
                if not path.exists():
                    continue
                
                for file_path in path.rglob('*'):
                    if file_path.is_file() and file_path.suffix in file_types:
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if query.lower() in content.lower():
                                    # Find line numbers with matches
                                    lines = content.split('\n')
                                    matching_lines = []
                                    for i, line in enumerate(lines, 1):
                                        if query.lower() in line.lower():
                                            matching_lines.append({
                                                "line_number": i,
                                                "content": line.strip()
                                            })
                                    
                                    results.append({
                                        "file": str(file_path.relative_to(self.project_root)),
                                        "matches": len(matching_lines),
                                        "matching_lines": matching_lines[:10]  # Limit to first 10 matches
                                    })
                        except Exception:
                            continue
        except Exception as e:
            return {"error": f"Search error: {str(e)}"}
        
        return {
            "query": query,
            "total_files_found": len(results),
            "results": results[:20]  # Limit to top 20 results
        }
    
    def get_cherry_ai_context(self) -> Dict[str, Any]:
        """Get Cherry AI specific context for development tools"""
        return {
            "development_modes": {
                "cherry_dev": {
                    "role": "General full-stack development",
                    "capabilities": ["Python", "JavaScript", "HTML/CSS", "testing", "debugging"],
                    "model_preference": "claude-3-sonnet"
                },
                "infra": {
                    "role": "Infrastructure and DevOps",
                    "capabilities": ["Pulumi", "Docker", "GitHub Actions", "server management"],
                    "model_preference": "claude-3-sonnet"
                },
                "database": {
                    "role": "Database operations and optimization", 
                    "capabilities": ["PostgreSQL", "Redis", "vector databases", "query optimization"],
                    "model_preference": "claude-3-sonnet"
                }
            },
            "end_user_personas_note": "The application has Cherry/Sophia/Karen personas for END USERS, not for development",
            "development_workflow": {
                "primary_ide": "Cursor AI with Max Mode",
                "ai_assistant": "Roo Code with custom development modes",
                "version_control": "GitHub with organization secrets",
                "deployment": "Automated via GitHub Actions to production"
            },
            "coding_standards": {
                "python": "PEP 8, type hints, comprehensive docstrings",
                "javascript": "ES6+, async/await, error handling",
                "security": "No hardcoded secrets, environment variables",
                "testing": "Comprehensive tests for all new functionality"
            }
        }

# Initialize the codebase manager
codebase_manager = CherryAICodebaseManager(PROJECT_ROOT)

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available codebase resources"""
    return [
        types.Resource(
            uri=AnyUrl("cherry-ai://project/overview"),
            name="Project Overview",
            description="Comprehensive Cherry AI project overview",
            mimeType="application/json",
        ),
        types.Resource(
            uri=AnyUrl("cherry-ai://project/structure"),
            name="Project Structure", 
            description="Complete project file structure",
            mimeType="application/json",
        ),
        types.Resource(
            uri=AnyUrl("cherry-ai://project/context"),
            name="Cherry AI Context",
            description="Cherry AI specific context and configuration",
            mimeType="application/json",
        ),
    ]

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read specific codebase resource"""
    if uri.scheme != "cherry-ai":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")
    
    path = str(uri).replace("cherry-ai://", "")
    
    if path == "project/overview":
        return json.dumps(codebase_manager.get_project_overview(), indent=2)
    elif path == "project/structure":
        return json.dumps(codebase_manager.get_file_structure(), indent=2)
    elif path == "project/context":
        return json.dumps(codebase_manager.get_cherry_ai_context(), indent=2)
    else:
        raise ValueError(f"Unknown resource path: {path}")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available codebase tools"""
    return [
        types.Tool(
            name="read_file",
            description="Read content of a specific file in the codebase",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file relative to project root"
                    },
                    "max_lines": {
                        "type": "integer", 
                        "description": "Maximum number of lines to read (default: 1000)",
                        "default": 1000
                    }
                },
                "required": ["file_path"]
            },
        ),
        types.Tool(
            name="search_codebase",
            description="Search for patterns across the codebase",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query or pattern"
                    },
                    "file_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "File extensions to search (e.g., ['.py', '.js'])"
                    }
                },
                "required": ["query"]
            },
        ),
        types.Tool(
            name="get_file_structure",
            description="Get file structure for a specific directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path relative to project root (optional)"
                    }
                }
            },
        ),
        types.Tool(
            name="analyze_project",
            description="Get comprehensive project analysis for AI assistants",
            inputSchema={
                "type": "object",
                "properties": {
                    "focus_area": {
                        "type": "string",
                        "description": "Specific area to focus on (optional)",
                        "enum": ["architecture", "personas", "infrastructure", "development"]
                    }
                }
            },
        ),
        types.Tool(
            name="get_smart_suggestions",
            description="Get smart context suggestions based on current task and command history",
            inputSchema={
                "type": "object",
                "properties": {
                    "current_task": {
                        "type": "string",
                        "description": "Description of the current development task"
                    },
                    "include_history": {
                        "type": "boolean",
                        "description": "Include command history analysis (default: true)",
                        "default": True
                    }
                },
                "required": ["current_task"]
            },
        ),
        types.Tool(
            name="get_command_history",
            description="Get recent command history and usage patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of recent commands to return (default: 10)",
                        "default": 10
                    }
                }
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls"""
    if arguments is None:
        arguments = {}
    
    if name == "read_file":
        file_path = arguments.get("file_path")
        max_lines = arguments.get("max_lines", 1000)
        if not file_path:
            raise ValueError("file_path is required")
        
        result = codebase_manager.read_file_content(file_path, max_lines)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "search_codebase":
        query = arguments.get("query")
        file_types = arguments.get("file_types")
        if not query:
            raise ValueError("query is required")
        
        result = codebase_manager.search_codebase(query, file_types)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "get_file_structure":
        path = arguments.get("path")
        result = codebase_manager.get_file_structure(path)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "analyze_project":
        focus_area = arguments.get("focus_area")
        overview = codebase_manager.get_project_overview()
        context = codebase_manager.get_cherry_ai_context()
        
        if focus_area:
            if focus_area == "architecture":
                result = {"architecture": overview["architecture"], "tech_stack": overview["tech_stack"]}
            elif focus_area == "personas":
                result = {"ai_personas": overview["ai_personas"], "personas": context["personas"]}
            elif focus_area == "infrastructure":
                result = {"architecture": overview["architecture"], "development_tools": overview["development_tools"]}
            elif focus_area == "development":
                result = {"development_workflow": context["development_workflow"], "coding_standards": context["coding_standards"]}
            else:
                result = {"overview": overview, "context": context}
        else:
            result = {"overview": overview, "context": context}
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "get_smart_suggestions":
        current_task = arguments.get("current_task")
        include_history = arguments.get("include_history", True)
        if not current_task:
            raise ValueError("current_task is required")
        
        # Add this command to history for future pattern recognition
        codebase_manager.add_command_to_history(f"get_smart_suggestions: {current_task}", arguments)
        
        suggestions = codebase_manager.get_smart_context_suggestions(current_task)
        
        if not include_history:
            suggestions.pop("context_patterns", None)
        
        return [types.TextContent(type="text", text=json.dumps(suggestions, indent=2))]
    
    elif name == "get_command_history":
        limit = arguments.get("limit", 10)
        recent_commands = codebase_manager.command_history[-limit:] if codebase_manager.command_history else []
        
        # Format command history for readability
        formatted_history = []
        for cmd in recent_commands:
            formatted_history.append({
                "command": cmd["command"],
                "timestamp": cmd["timestamp"],
                "git_branch": cmd.get("project_state", {}).get("git_branch", "unknown"),
                "modified_files": cmd.get("project_state", {}).get("modified_files", 0)
            })
        
        result = {
            "total_commands": len(codebase_manager.command_history),
            "recent_commands": formatted_history,
            "current_project_state": codebase_manager._get_project_state_snapshot()
        }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Main server entry point"""
    # Use stdin/stdout for communication
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="cherry-ai-codebase",
                server_version="2.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())

