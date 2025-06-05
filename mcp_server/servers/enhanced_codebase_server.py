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
    """Optimized codebase management for Cursor AI and Roo"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.file_cache = {}
        self.cursor_integration = os.getenv("ENABLE_CURSOR_INTEGRATION", "false").lower() == "true"
        self.roo_integration = os.getenv("ENABLE_ROO_INTEGRATION", "false").lower() == "true"
        
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

