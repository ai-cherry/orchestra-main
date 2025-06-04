#!/usr/bin/env python3
"""
Cherry AI Orchestrator - Enhanced MCP Server
Provides comprehensive codebase context and AI coding assistance
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
logger = logging.getLogger("cherry-ai-mcp")

# Server configuration
server = Server("cherry-ai-orchestrator")

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODEBASE_PATHS = [
    PROJECT_ROOT / "admin-interface",
    PROJECT_ROOT / "infrastructure", 
    PROJECT_ROOT / "mcp_server",
    PROJECT_ROOT / ".ai-tools",
    PROJECT_ROOT / ".github",
    PROJECT_ROOT / "scripts"
]

class CodebaseAnalyzer:
    """Analyzes codebase structure and provides context"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.file_cache = {}
        
    def get_project_structure(self) -> Dict[str, Any]:
        """Get comprehensive project structure"""
        structure = {
            "root": str(self.project_root),
            "directories": {},
            "files": {},
            "technologies": self._detect_technologies(),
            "dependencies": self._get_dependencies(),
            "configuration": self._get_configuration_files()
        }
        
        for path in CODEBASE_PATHS:
            if path.exists():
                structure["directories"][path.name] = self._analyze_directory(path)
                
        return structure
    
    def _analyze_directory(self, directory: Path) -> Dict[str, Any]:
        """Analyze a specific directory"""
        analysis = {
            "path": str(directory),
            "files": [],
            "subdirectories": [],
            "file_types": {},
            "total_files": 0,
            "total_lines": 0
        }
        
        try:
            for item in directory.rglob("*"):
                if item.is_file() and not self._should_ignore_file(item):
                    file_info = self._analyze_file(item)
                    analysis["files"].append(file_info)
                    analysis["total_files"] += 1
                    analysis["total_lines"] += file_info.get("lines", 0)
                    
                    # Track file types
                    ext = item.suffix.lower()
                    analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1
                    
                elif item.is_dir() and item != directory:
                    analysis["subdirectories"].append(str(item.relative_to(directory)))
                    
        except Exception as e:
            logger.error(f"Error analyzing directory {directory}: {e}")
            
        return analysis
    
    def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a specific file"""
        try:
            stat = file_path.stat()
            analysis = {
                "name": file_path.name,
                "path": str(file_path.relative_to(self.project_root)),
                "size": stat.st_size,
                "extension": file_path.suffix.lower(),
                "modified": stat.st_mtime
            }
            
            # Read file content for text files
            if self._is_text_file(file_path):
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    analysis["lines"] = len(content.splitlines())
                    analysis["characters"] = len(content)
                    
                    # Analyze content based on file type
                    if file_path.suffix.lower() in ['.py', '.js', '.ts', '.html', '.css', '.json', '.yml', '.yaml']:
                        analysis["content_analysis"] = self._analyze_code_content(content, file_path.suffix.lower())
                        
                except Exception as e:
                    logger.warning(f"Could not read file {file_path}: {e}")
                    
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return {"name": file_path.name, "error": str(e)}
    
    def _analyze_code_content(self, content: str, extension: str) -> Dict[str, Any]:
        """Analyze code content for patterns and structure"""
        analysis = {
            "imports": [],
            "functions": [],
            "classes": [],
            "apis": [],
            "todos": [],
            "complexity_score": 0
        }
        
        lines = content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Find imports
            if extension == '.py':
                if line_stripped.startswith(('import ', 'from ')):
                    analysis["imports"].append(line_stripped)
                elif line_stripped.startswith('def '):
                    analysis["functions"].append({
                        "name": line_stripped.split('(')[0].replace('def ', ''),
                        "line": line_num
                    })
                elif line_stripped.startswith('class '):
                    analysis["classes"].append({
                        "name": line_stripped.split('(')[0].replace('class ', '').rstrip(':'),
                        "line": line_num
                    })
            elif extension in ['.js', '.ts']:
                if 'function ' in line_stripped or '=>' in line_stripped:
                    analysis["functions"].append({
                        "name": self._extract_js_function_name(line_stripped),
                        "line": line_num
                    })
                if line_stripped.startswith(('import ', 'require(')):
                    analysis["imports"].append(line_stripped)
                    
            # Find API endpoints
            if any(keyword in line_stripped.lower() for keyword in ['@app.route', 'app.get', 'app.post', 'fetch(', 'axios.']):
                analysis["apis"].append({
                    "line": line_num,
                    "content": line_stripped
                })
                
            # Find TODOs
            if any(keyword in line_stripped.upper() for keyword in ['TODO', 'FIXME', 'HACK', 'XXX']):
                analysis["todos"].append({
                    "line": line_num,
                    "content": line_stripped
                })
                
        # Calculate complexity score
        analysis["complexity_score"] = len(analysis["functions"]) + len(analysis["classes"]) * 2
        
        return analysis
    
    def _extract_js_function_name(self, line: str) -> str:
        """Extract function name from JavaScript line"""
        try:
            if 'function ' in line:
                return line.split('function ')[1].split('(')[0].strip()
            elif '=>' in line and '=' in line:
                return line.split('=')[0].strip()
            return "anonymous"
        except:
            return "unknown"
    
    def _detect_technologies(self) -> List[str]:
        """Detect technologies used in the project"""
        technologies = []
        
        # Check for specific files
        tech_indicators = {
            "package.json": "Node.js",
            "requirements.txt": "Python",
            "Dockerfile": "Docker",
            "docker-compose.yml": "Docker Compose",
            "Pulumi.yaml": "Pulumi",
            ".github/workflows": "GitHub Actions",
            "nginx.conf": "Nginx",
            "redis.conf": "Redis"
        }
        
        for indicator, tech in tech_indicators.items():
            if (self.project_root / indicator).exists():
                technologies.append(tech)
                
        return technologies
    
    def _get_dependencies(self) -> Dict[str, List[str]]:
        """Get project dependencies"""
        dependencies = {}
        
        # Python dependencies
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            try:
                dependencies["python"] = req_file.read_text().splitlines()
            except Exception as e:
                logger.error(f"Error reading requirements.txt: {e}")
                
        # Node.js dependencies
        package_file = self.project_root / "package.json"
        if package_file.exists():
            try:
                package_data = json.loads(package_file.read_text())
                dependencies["nodejs"] = list(package_data.get("dependencies", {}).keys())
                dependencies["nodejs_dev"] = list(package_data.get("devDependencies", {}).keys())
            except Exception as e:
                logger.error(f"Error reading package.json: {e}")
                
        return dependencies
    
    def _get_configuration_files(self) -> List[Dict[str, Any]]:
        """Get configuration files"""
        config_files = []
        config_patterns = ["*.json", "*.yml", "*.yaml", "*.toml", "*.ini", "*.conf", ".env*"]
        
        for pattern in config_patterns:
            for config_file in self.project_root.rglob(pattern):
                if not self._should_ignore_file(config_file):
                    config_files.append({
                        "name": config_file.name,
                        "path": str(config_file.relative_to(self.project_root)),
                        "type": config_file.suffix.lower()
                    })
                    
        return config_files
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored"""
        ignore_patterns = [
            ".git", "__pycache__", "node_modules", ".venv", "venv",
            ".DS_Store", "*.pyc", "*.log", "*.tmp", ".cache"
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in ignore_patterns)
    
    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is a text file"""
        text_extensions = {
            '.py', '.js', '.ts', '.html', '.css', '.json', '.yml', '.yaml',
            '.md', '.txt', '.sh', '.sql', '.xml', '.toml', '.ini', '.conf',
            '.jsx', '.tsx', '.vue', '.php', '.rb', '.go', '.rs', '.java'
        }
        return file_path.suffix.lower() in text_extensions

# Initialize codebase analyzer
analyzer = CodebaseAnalyzer(PROJECT_ROOT)

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available resources"""
    return [
        types.Resource(
            uri=AnyUrl("cherry-ai://codebase/structure"),
            name="Project Structure",
            description="Complete project structure and analysis",
            mimeType="application/json",
        ),
        types.Resource(
            uri=AnyUrl("cherry-ai://codebase/files"),
            name="File Listing",
            description="Detailed file listing with analysis",
            mimeType="application/json",
        ),
        types.Resource(
            uri=AnyUrl("cherry-ai://codebase/dependencies"),
            name="Dependencies",
            description="Project dependencies and technologies",
            mimeType="application/json",
        ),
        types.Resource(
            uri=AnyUrl("cherry-ai://infrastructure/status"),
            name="Infrastructure Status",
            description="Current infrastructure and deployment status",
            mimeType="application/json",
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read a specific resource"""
    
    if uri.scheme != "cherry-ai":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")
    
    path = uri.path
    
    if path == "/codebase/structure":
        structure = analyzer.get_project_structure()
        return json.dumps(structure, indent=2, default=str)
    
    elif path == "/codebase/files":
        files_info = {}
        for codebase_path in CODEBASE_PATHS:
            if codebase_path.exists():
                files_info[codebase_path.name] = analyzer._analyze_directory(codebase_path)
        return json.dumps(files_info, indent=2, default=str)
    
    elif path == "/codebase/dependencies":
        dependencies = analyzer._get_dependencies()
        technologies = analyzer._detect_technologies()
        return json.dumps({
            "dependencies": dependencies,
            "technologies": technologies
        }, indent=2)
    
    elif path == "/infrastructure/status":
        # Get infrastructure status
        status = {
            "servers": {
                "production": "45.32.69.157",
                "database": "45.77.87.106", 
                "staging": "207.246.108.201"
            },
            "services": ["nginx", "redis", "postgresql"],
            "deployment_status": "ready",
            "last_deployment": "pending"
        }
        return json.dumps(status, indent=2)
    
    else:
        raise ValueError(f"Unknown resource path: {path}")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="analyze_file",
            description="Analyze a specific file in the codebase",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to analyze"
                    }
                },
                "required": ["file_path"]
            },
        ),
        types.Tool(
            name="search_codebase",
            description="Search for patterns in the codebase",
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
                        "description": "File extensions to search in"
                    }
                },
                "required": ["query"]
            },
        ),
        types.Tool(
            name="get_git_info",
            description="Get Git repository information",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="run_tests",
            description="Run project tests",
            inputSchema={
                "type": "object",
                "properties": {
                    "test_type": {
                        "type": "string",
                        "enum": ["all", "unit", "integration", "lint"],
                        "description": "Type of tests to run"
                    }
                },
                "required": ["test_type"]
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls"""
    
    if name == "analyze_file":
        file_path = arguments.get("file_path")
        if not file_path:
            raise ValueError("file_path is required")
            
        full_path = PROJECT_ROOT / file_path
        if not full_path.exists():
            return [types.TextContent(type="text", text=f"File not found: {file_path}")]
            
        analysis = analyzer._analyze_file(full_path)
        
        # Include file content if it's a text file
        if analyzer._is_text_file(full_path):
            try:
                content = full_path.read_text(encoding='utf-8', errors='ignore')
                analysis["content"] = content[:5000]  # Limit content size
                if len(content) > 5000:
                    analysis["content"] += "\n... (truncated)"
            except Exception as e:
                analysis["content_error"] = str(e)
                
        return [types.TextContent(
            type="text",
            text=json.dumps(analysis, indent=2, default=str)
        )]
    
    elif name == "search_codebase":
        query = arguments.get("query")
        file_types = arguments.get("file_types", [])
        
        if not query:
            raise ValueError("query is required")
            
        results = []
        
        for codebase_path in CODEBASE_PATHS:
            if not codebase_path.exists():
                continue
                
            for file_path in codebase_path.rglob("*"):
                if not file_path.is_file() or analyzer._should_ignore_file(file_path):
                    continue
                    
                if file_types and file_path.suffix.lower() not in file_types:
                    continue
                    
                if analyzer._is_text_file(file_path):
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        lines = content.splitlines()
                        
                        for line_num, line in enumerate(lines, 1):
                            if query.lower() in line.lower():
                                results.append({
                                    "file": str(file_path.relative_to(PROJECT_ROOT)),
                                    "line": line_num,
                                    "content": line.strip(),
                                    "context": lines[max(0, line_num-2):line_num+2]
                                })
                                
                    except Exception as e:
                        logger.warning(f"Could not search file {file_path}: {e}")
                        
        return [types.TextContent(
            type="text",
            text=json.dumps(results[:50], indent=2)  # Limit results
        )]
    
    elif name == "get_git_info":
        try:
            # Get git information
            git_info = {}
            
            # Current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                git_info["current_branch"] = result.stdout.strip()
                
            # Recent commits
            result = subprocess.run(
                ["git", "log", "--oneline", "-10"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                git_info["recent_commits"] = result.stdout.strip().splitlines()
                
            # Status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                git_info["status"] = result.stdout.strip().splitlines()
                
            return [types.TextContent(
                type="text",
                text=json.dumps(git_info, indent=2)
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error getting git info: {e}"
            )]
    
    elif name == "run_tests":
        test_type = arguments.get("test_type", "all")
        
        try:
            results = {}
            
            if test_type in ["all", "lint"]:
                # Run Python linting
                result = subprocess.run(
                    ["python", "-m", "flake8", ".", "--count", "--statistics"],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True
                )
                results["python_lint"] = {
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
            if test_type in ["all", "unit"]:
                # Run Python tests
                result = subprocess.run(
                    ["python", "-m", "pytest", "-v"],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True
                )
                results["python_tests"] = {
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
            return [types.TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error running tests: {e}"
            )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Main entry point"""
    # Use stdin/stdout for communication
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="cherry-ai-orchestrator",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())

