import os
#!/usr/bin/env python3
"""
AI Coding Assistant MCP Server

Centralized coordination for all AI coding tools including Roo Coder, Cursor AI,
OpenAI Codex, Google Jules, and Factory AI. Focuses on performance, stability,
and optimization over security and cost.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiofiles
import aioredis
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AICodingAssistant:
    """Central coordinator for AI coding tools and optimization."""
    
    def __init__(self):
        self.redis_client = None
        self.project_root = Path(__file__).parent.parent.parent
        self.ai_tools_config = self.project_root / ".ai-tools"
        self.api_config = self._load_api_config()
        
    async def initialize(self):
        """Initialize the AI coding assistant."""
        try:
            # Connect to Redis for caching and coordination
            redis_url = os.getenv("REDIS_URL", "redis://45.77.87.106:6379")
            self.redis_client = await aioredis.from_url(redis_url)
            logger.info("Connected to Redis for AI tool coordination")
            
            # Ensure AI tools directory structure exists
            await self._ensure_directory_structure()
            
            # Initialize AI tool configurations
            await self._initialize_ai_tools()
            
        except Exception as e:
            logger.error(f"Failed to initialize AI coding assistant: {e}")
            
    def _load_api_config(self) -> Dict[str, Any]:
        """Load the unified API configuration."""
        config_path = self.ai_tools_config / "apis" / "unified_config.json"
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("API config not found, using defaults")
            return {}
            
    async def _ensure_directory_structure(self):
        """Ensure all required directories exist."""
        directories = [
            self.ai_tools_config / "cursor",
            self.ai_tools_config / "roo",
            self.ai_tools_config / "codex",
            self.ai_tools_config / "factory-ai",
            self.ai_tools_config / "apis",
            self.ai_tools_config / "prompts" / "coding",
            self.ai_tools_config / "prompts" / "debugging",
            self.ai_tools_config / "prompts" / "architecture",
            self.ai_tools_config / "prompts" / "optimization",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
    async def _initialize_ai_tools(self):
        """Initialize configurations for all AI tools."""
        await asyncio.gather(
            self._setup_cursor_config(),
            self._setup_roo_config(),
            self._setup_codex_config(),
            self._setup_factory_ai_config(),
        )
        
    async def _setup_cursor_config(self):
        """Set up Cursor IDE configuration for optimal AI coding."""
        cursor_config = {
            "workbench.colorTheme": "Default Dark+",
            "editor.fontSize": 14,
            "editor.tabSize": 4,
            "editor.insertSpaces": True,
            "editor.formatOnSave": True,
            "editor.codeActionsOnSave": {
                "source.organizeImports": True,
                "source.fixAll": True
            },
            "python.defaultInterpreterPath": "./venv/bin/python",
            "python.linting.enabled": True,
            "python.linting.pylintEnabled": True,
            "python.formatting.provider": "black",
            "git.autofetch": True,
            "git.enableSmartCommit": True,
            "extensions.autoUpdate": True,
            "ai.performance.priority": True,
            "ai.stability.focus": True,
            "ai.optimization.enabled": True
        }
        
        config_path = self.ai_tools_config / "cursor" / "settings.json"
        async with aiofiles.open(config_path, 'w') as f:
            await f.write(json.dumps(cursor_config, indent=2))
            
    async def _setup_roo_config(self):
        """Set up enhanced Roo Coder configuration."""
        roo_config = {
            "performance_rules": {
                "database_optimization": True,
                "api_efficiency": True,
                "memory_management": True,
                "caching_strategy": True
            },
            "stability_rules": {
                "error_handling": True,
                "graceful_degradation": True,
                "circuit_breakers": True,
                "health_checks": True
            },
            "optimization_focus": {
                "code_quality": True,
                "performance_metrics": True,
                "automated_testing": True,
                "continuous_monitoring": True
            }
        }
        
        config_path = self.ai_tools_config / "roo" / "enhanced_config.json"
        async with aiofiles.open(config_path, 'w') as f:
            await f.write(json.dumps(roo_config, indent=2))
            
    async def _setup_codex_config(self):
        """Set up OpenAI Codex configuration for SSH integration."""
        codex_setup = """#!/bin/bash
# OpenAI Codex SSH Setup Script
# Run this on the remote server via SSH

# Install Node.js if not present
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
fi

# Install Codex CLI
npm install -g @openai/codex

# Set up environment
export OPENAI_API_KEY = os.getenv('ORCHESTRA_MCP_API_KEY')
OPENAI_API_KEY = os.getenv("MCP_AI_CODING_ASSISTANT_API_KEY", "")

# Initialize in project directory
cd ~/orchestra-main
git init 2>/dev/null || true

echo "Codex setup complete. Usage:"
echo "  codex 'Add error handling to API endpoints'"
echo "  codex --approval-mode full-auto 'Optimize database queries'"
"""
        
        setup_path = self.ai_tools_config / "codex" / "setup.sh"
        async with aiofiles.open(setup_path, 'w') as f:
            await f.write(codex_setup)
            
    async def _setup_factory_ai_config(self):
        """Set up Factory AI configuration."""
        factory_config = {
            "workflows": {
                "code_review": {
                    "enabled": True,
                    "auto_fix": True,
                    "performance_check": True
                },
                "deployment": {
                    "enabled": True,
                    "auto_deploy": False,
                    "rollback_on_error": True
                },
                "monitoring": {
                    "enabled": True,
                    "performance_alerts": True,
                    "error_tracking": True
                }
            },
            "integration": {
                "github_actions": True,
                "mcp_servers": True,
                "database_monitoring": True
            }
        }
        
        config_path = self.ai_tools_config / "factory-ai" / "config.json"
        async with aiofiles.open(config_path, 'w') as f:
            await f.write(json.dumps(factory_config, indent=2))

# Initialize the AI coding assistant
ai_assistant = AICodingAssistant()

# Create MCP server
server = Server("ai-coding-assistant")

@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available AI coding tools."""
    return ListToolsResult(
        tools=[
            Tool(
                name="optimize_code",
                description="Analyze and optimize code for performance and stability",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to the file to optimize"},
                        "optimization_type": {
                            "type": "string", 
                            "enum": ["performance", "stability", "readability", "all"],
                            "description": "Type of optimization to perform"
                        }
                    },
                    "required": ["file_path"]
                }
            ),
            Tool(
                name="setup_ai_tool",
                description="Set up and configure AI coding tools (Roo, Cursor, Codex, Factory AI)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tool": {
                            "type": "string",
                            "enum": ["roo", "cursor", "codex", "factory-ai", "all"],
                            "description": "AI tool to set up"
                        },
                        "ssh_server": {"type": "string", "description": "SSH server for remote setup (optional)"}
                    },
                    "required": ["tool"]
                }
            ),
            Tool(
                name="analyze_performance",
                description="Analyze code performance and suggest optimizations",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "description": "Directory to analyze"},
                        "include_database": {"type": "boolean", "description": "Include database query analysis"}
                    },
                    "required": ["directory"]
                }
            ),
            Tool(
                name="manage_prompts",
                description="Manage AI tool prompts and templates",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["list", "create", "update", "delete"],
                            "description": "Action to perform on prompts"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["coding", "debugging", "architecture", "optimization"],
                            "description": "Prompt category"
                        },
                        "prompt_name": {"type": "string", "description": "Name of the prompt"},
                        "content": {"type": "string", "description": "Prompt content (for create/update)"}
                    },
                    "required": ["action"]
                }
            ),
            Tool(
                name="cleanup_repository",
                description="Clean up backup directories and optimize repository structure",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dry_run": {"type": "boolean", "description": "Show what would be deleted without actually deleting"},
                        "backup_patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Patterns to match for cleanup"
                        }
                    }
                }
            ),
            Tool(
                name="monitor_ai_tools",
                description="Monitor AI tool performance and usage",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tool": {"type": "string", "description": "Specific tool to monitor (optional)"},
                        "metrics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Metrics to collect"
                        }
                    }
                }
            )
        ]
    )

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
    """Handle tool calls for AI coding assistance."""
    try:
        if name == "optimize_code":
            return await optimize_code(arguments)
        elif name == "setup_ai_tool":
            return await setup_ai_tool(arguments)
        elif name == "analyze_performance":
            return await analyze_performance(arguments)
        elif name == "manage_prompts":
            return await manage_prompts(arguments)
        elif name == "cleanup_repository":
            return await cleanup_repository(arguments)
        elif name == "monitor_ai_tools":
            return await monitor_ai_tools(arguments)
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")]
            )
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )

async def optimize_code(arguments: dict) -> CallToolResult:
    """Optimize code for performance and stability."""
    file_path = arguments.get("file_path")
    optimization_type = arguments.get("optimization_type", "all")
    
    if not os.path.exists(file_path):
        return CallToolResult(
            content=[TextContent(type="text", text=f"File not found: {file_path}")]
        )
    
    # Analyze the file and suggest optimizations
    optimizations = []
    
    # Read file content
    async with aiofiles.open(file_path, 'r') as f:
        content = await f.read()
    
    # Performance optimizations
    if optimization_type in ["performance", "all"]:
        if "SELECT * FROM" in content:
            optimizations.append("Replace SELECT * with specific column names for better performance")
        if "for " in content and "append(" in content:
            optimizations.append("Consider using list comprehension instead of append in loops")
        # TODO: Replace with asyncio.sleep() for async code
        if "time.sleep(" in content:
            optimizations.append("Consider using asyncio.sleep() for non-blocking delays")
    
    # Stability optimizations
    if optimization_type in ["stability", "all"]:
        if "except:" in content:
            optimizations.append("Use specific exception types instead of bare except")
        if "requests.get(" in content and "timeout=" not in content:
            optimizations.append("Add timeout parameter to HTTP requests")
    
    result = f"Code optimization analysis for {file_path}:\n\n"
    if optimizations:
        result += "Suggested optimizations:\n"
        for i, opt in enumerate(optimizations, 1):
            result += f"{i}. {opt}\n"
    else:
        result += "No obvious optimizations found. Code looks good!"
    
    return CallToolResult(
        content=[TextContent(type="text", text=result)]
    )

async def setup_ai_tool(arguments: dict) -> CallToolResult:
    """Set up AI coding tools."""
    tool = arguments.get("tool")
    ssh_server = arguments.get("ssh_server")
    
    setup_results = []
    
    if tool in ["roo", "all"]:
        # Set up Roo Coder
        await ai_assistant._setup_roo_config()
        setup_results.append("✅ Roo Coder configuration updated")
    
    if tool in ["cursor", "all"]:
        # Set up Cursor IDE
        await ai_assistant._setup_cursor_config()
        setup_results.append("✅ Cursor IDE configuration updated")
    
    if tool in ["codex", "all"]:
        # Set up Codex
        await ai_assistant._setup_codex_config()
        if ssh_server:
            setup_results.append(f"✅ Codex setup script created. Run on {ssh_server}:")
            setup_results.append(f"scp .ai-tools/codex/setup.sh {ssh_server}:~/")
            setup_results.append(f"ssh {ssh_server} 'bash ~/setup.sh'")
        else:
            setup_results.append("✅ Codex setup script created in .ai-tools/codex/setup.sh")
    
    if tool in ["factory-ai", "all"]:
        # Set up Factory AI
        await ai_assistant._setup_factory_ai_config()
        setup_results.append("✅ Factory AI configuration created")
    
    result = "AI Tool Setup Complete:\n\n" + "\n".join(setup_results)
    return CallToolResult(
        content=[TextContent(type="text", text=result)]
    )

async def analyze_performance(arguments: dict) -> CallToolResult:
    """Analyze code performance."""
    directory = arguments.get("directory", ".")
    include_database = arguments.get("include_database", False)
    
    analysis_results = []
    
    # Analyze Python files
    python_files = list(Path(directory).rglob("*.py"))
    analysis_results.append(f"Found {len(python_files)} Python files")
    
    # Basic performance analysis
    performance_issues = 0
    for file_path in python_files[:10]:  # Limit to first 10 files
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Check for common performance issues
            if "SELECT * FROM" in content:
                performance_issues += 1
            if content.count("for ") > 5 and "append(" in content:
                # TODO: Replace with asyncio.sleep() for async code
                performance_issues += 1
            if "time.sleep(" in content:
                performance_issues += 1
                
        except Exception:
            continue
    
    analysis_results.append(f"Potential performance issues found: {performance_issues}")
    
    if include_database:
        analysis_results.append("Database analysis:")
        analysis_results.append("- Check for N+1 query patterns")
        analysis_results.append("- Verify proper indexing")
        analysis_results.append("- Monitor query execution times")
    
    result = "Performance Analysis Results:\n\n" + "\n".join(analysis_results)
    return CallToolResult(
        content=[TextContent(type="text", text=result)]
    )

async def manage_prompts(arguments: dict) -> CallToolResult:
    """Manage AI tool prompts."""
    action = arguments.get("action")
    category = arguments.get("category", "coding")
    prompt_name = arguments.get("prompt_name")
    content = arguments.get("content")
    
    prompts_dir = ai_assistant.ai_tools_config / "prompts" / category
    prompts_dir.mkdir(parents=True, exist_ok=True)
    
    if action == "list":
        prompt_files = list(prompts_dir.glob("*.md"))
        result = f"Available {category} prompts:\n\n"
        for prompt_file in prompt_files:
            result += f"- {prompt_file.stem}\n"
        return CallToolResult(
            content=[TextContent(type="text", text=result)]
        )
    
    elif action == "create" and prompt_name and content:
        prompt_file = prompts_dir / f"{prompt_name}.md"
        async with aiofiles.open(prompt_file, 'w') as f:
            await f.write(content)
        return CallToolResult(
            content=[TextContent(type="text", text=f"Created prompt: {prompt_name}")]
        )
    
    else:
        return CallToolResult(
            content=[TextContent(type="text", text="Invalid prompt management action")]
        )

async def cleanup_repository(arguments: dict) -> CallToolResult:
    """Clean up repository backup directories."""
    dry_run = arguments.get("dry_run", True)
    backup_patterns = arguments.get("backup_patterns", ["*backup*", "*migration*", "*refactor*"])
    
    cleanup_results = []
    total_size = 0
    
    for pattern in backup_patterns:
        matching_dirs = list(ai_assistant.project_root.glob(f"**/{pattern}"))
        for dir_path in matching_dirs:
            if dir_path.is_dir():
                # Calculate directory size
                size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                total_size += size
                
                if dry_run:
                    cleanup_results.append(f"Would delete: {dir_path} ({size / 1024 / 1024:.1f} MB)")
                else:
                    import shutil
                    shutil.rmtree(dir_path)
                    cleanup_results.append(f"Deleted: {dir_path} ({size / 1024 / 1024:.1f} MB)")
    
    action = "Would clean up" if dry_run else "Cleaned up"
    result = f"Repository Cleanup Results:\n\n"
    result += f"{action} {len(cleanup_results)} directories\n"
    result += f"Total space: {total_size / 1024 / 1024:.1f} MB\n\n"
    result += "\n".join(cleanup_results)
    
    if dry_run:
        result += "\n\nRun with dry_run=false to actually delete these directories."
    
    return CallToolResult(
        content=[TextContent(type="text", text=result)]
    )

async def monitor_ai_tools(arguments: dict) -> CallToolResult:
    """Monitor AI tool performance and usage."""
    tool = arguments.get("tool")
    metrics = arguments.get("metrics", ["usage", "performance", "errors"])
    
    monitoring_results = []
    
    # Check if AI tools are configured
    if (ai_assistant.ai_tools_config / "roo").exists():
        monitoring_results.append("✅ Roo Coder: Configured")
    else:
        monitoring_results.append("❌ Roo Coder: Not configured")
    
    if (ai_assistant.ai_tools_config / "cursor").exists():
        monitoring_results.append("✅ Cursor IDE: Configured")
    else:
        monitoring_results.append("❌ Cursor IDE: Not configured")
    
    if (ai_assistant.ai_tools_config / "codex").exists():
        monitoring_results.append("✅ OpenAI Codex: Setup script available")
    else:
        monitoring_results.append("❌ OpenAI Codex: Not configured")
    
    # Check API configurations
    if ai_assistant.api_config:
        monitoring_results.append("✅ API Configuration: Loaded")
        api_count = len(ai_assistant.api_config.get("ai_apis", {}))
        monitoring_results.append(f"📊 Configured APIs: {api_count}")
    else:
        monitoring_results.append("❌ API Configuration: Missing")
    
    result = "AI Tools Monitoring Report:\n\n" + "\n".join(monitoring_results)
    return CallToolResult(
        content=[TextContent(type="text", text=result)]
    )

async def main():
    """Main entry point for the AI coding assistant MCP server."""
    # Initialize the AI assistant
    await ai_assistant.initialize()
    
    # Run the MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ai-coding-assistant",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())

