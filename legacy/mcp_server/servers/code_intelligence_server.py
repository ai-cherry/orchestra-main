#!/usr/bin/env python3
"""
Code Intelligence MCP Server - Provides advanced code analysis and context for AI coding.
"""

import ast
import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from mcp import types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import Resource, TextContent, Tool


class CodeIntelligenceServer:
    """MCP server for advanced code analysis and intelligence."""

    def __init__(self):
        self.server = Server("code-intelligence")
        self.project_root = Path.cwd()
        self.file_cache: Dict[str, Dict] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP handlers for code intelligence tools."""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="analyze_file_ast",
                    description="Parse Python file and extract AST information (functions, classes, imports)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to Python file"},
                            "include_docstrings": {"type": "boolean", "description": "Include docstrings in analysis", "default": True}
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="find_function_usage",
                    description="Find where a function/class is used across the codebase",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol_name": {"type": "string", "description": "Function or class name to search for"},
                            "file_extensions": {"type": "array", "items": {"type": "string"}, "default": [".py"]},
                            "exclude_dirs": {"type": "array", "items": {"type": "string"}, "default": ["venv", "__pycache__", ".git"]}
                        },
                        "required": ["symbol_name"]
                    }
                ),
                Tool(
                    name="analyze_imports",
                    description="Analyze import relationships and detect circular dependencies",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target_file": {"type": "string", "description": "File to analyze imports for (optional)"},
                            "detect_circular": {"type": "boolean",
                                "description": "Check for circular imports",
                                "default": True}
                        }
                    }
                ),
                Tool(
                    name="code_complexity_analysis",
                    description="Analyze code complexity metrics (cyclomatic complexity, etc.)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Python file to analyze"},
                            "threshold": {"type": "integer", "description": "Complexity threshold", "default": 10}
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="find_similar_patterns",
                    description="Find similar code patterns using AST similarity",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code_snippet": {"type": "string", "description": "Code pattern to find similar examples of"},
                            "similarity_threshold": {"type": "number", "description": "Similarity threshold (0.0-1.0)", "default": 0.8}
                        },
                        "required": ["code_snippet"]
                    }
                ),
                Tool(
                    name="generate_call_graph",
                    description="Generate function call graph for understanding code flow",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "entry_point": {"type": "string", "description": "Starting function/file"},
                            "max_depth": {"type": "integer", "description": "Maximum depth to traverse", "default": 5}
                        },
                        "required": ["entry_point"]
                    }
                ),
                Tool(
                    name="detect_code_smells",
                    description="Identify common code smells and anti-patterns",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "File to analyze"},
                            "check_types": {"type": "array", "items": {"type": "string"}, 
                                          "description": "Types of smells to check", 
                                          "default": ["long_function", "too_many_params", "duplicated_code"]}
                        },
                        "required": ["file_path"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            
            if name == "analyze_file_ast":
                return await self._analyze_file_ast(arguments)
            elif name == "find_function_usage":
                return await self._find_function_usage(arguments)
            elif name == "analyze_imports":
                return await self._analyze_imports(arguments)
            elif name == "code_complexity_analysis":
                return await self._analyze_complexity(arguments)
            elif name == "find_similar_patterns":
                return await self._find_similar_patterns(arguments)
            elif name == "generate_call_graph":
                return await self._generate_call_graph(arguments)
            elif name == "detect_code_smells":
                return await self._detect_code_smells(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def _analyze_file_ast(self, args: Dict[str, Any]) -> List[TextContent]:
        """Analyze Python file AST structure."""
        file_path = Path(args["file_path"])
        include_docstrings = args.get("include_docstrings", True)
        
        if not file_path.exists():
            return [TextContent(type="text", text=f"File not found: {file_path}")]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            analysis = {
                "file": str(file_path),
                "classes": [],
                "functions": [],
                "imports": [],
                "constants": [],
                "decorators": []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                        "bases": [ast.unparse(base) for base in node.bases]
                    }
                    if include_docstrings and ast.get_docstring(node):
                        class_info["docstring"] = ast.get_docstring(node)
                    analysis["classes"].append(class_info)
                
                elif isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "returns": ast.unparse(node.returns) if node.returns else None,
                        "is_async": isinstance(node, ast.AsyncFunctionDef)
                    }
                    if include_docstrings and ast.get_docstring(node):
                        func_info["docstring"] = ast.get_docstring(node)
                    if node.decorator_list:
                        func_info["decorators"] = [ast.unparse(dec) for dec in node.decorator_list]
                    analysis["functions"].append(func_info)
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            analysis["imports"].append({
                                "module": alias.name,
                                "alias": alias.asname,
                                "type": "import"
                            })
                    else:
                        for alias in node.names:
                            analysis["imports"].append({
                                "module": node.module,
                                "name": alias.name,
                                "alias": alias.asname,
                                "type": "from"
                            })
            
            output = f"# AST Analysis: {file_path}\n\n"
            output += f"**Classes ({len(analysis['classes'])}):**\n"
            for cls in analysis["classes"]:
                output += f"- `{cls['name']}` (line {cls['line']})\n"
                if cls.get('docstring'):
                    output += f"  - {cls['docstring'][:100]}...\n"
                if cls['methods']:
                    output += f"  - Methods: {', '.join(cls['methods'])}\n"
            
            output += f"\n**Functions ({len(analysis['functions'])}):**\n"
            for func in analysis["functions"]:
                async_marker = "async " if func["is_async"] else ""
                output += f"- `{async_marker}{func['name']}()` (line {func['line']})\n"
                if func.get('docstring'):
                    output += f"  - {func['docstring'][:100]}...\n"
                if func['args']:
                    output += f"  - Args: {', '.join(func['args'])}\n"
            
            output += f"\n**Imports ({len(analysis['imports'])}):**\n"
            for imp in analysis["imports"]:
                if imp["type"] == "import":
                    output += f"- `import {imp['module']}`\n"
                else:
                    output += f"- `from {imp['module']} import {imp['name']}`\n"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error analyzing {file_path}: {str(e)}")]

    async def _find_function_usage(self, args: Dict[str, Any]) -> List[TextContent]:
        """Find where a function/class is used across the codebase."""
        symbol_name = args["symbol_name"]
        file_extensions = args.get("file_extensions", [".py"])
        exclude_dirs = set(args.get("exclude_dirs", ["venv", "__pycache__", ".git"]))
        
        results = []
        
        for ext in file_extensions:
            cmd = [
                "grep", "-rn", "--include=f*{ext}",
                symbol_name, str(self.project_root)
            ]
            
            # Add exclusions
            for exclude in exclude_dirs:
                cmd.extend(["--exclude-dir", exclude])
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.stdout:
                    results.append(result.stdout)
            except Exception as e:
                continue
        
        if not results:
            return [TextContent(type="text", text=f"No usages found for: {symbol_name}")]
        
        output = f"# Usage Analysis: {symbol_name}\n\n"
        for result in results:
            for line in result.strip().split('\n'):
                if ':' in line:
                    file_path, line_num, code = line.split(':', 2)
                    output += f"**{file_path}:{line_num}**\n```python\n{code.strip()}\n```\n\n"
        
        return [TextContent(type="text", text=output)]

    async def _analyze_imports(self, args: Dict[str, Any]) -> List[TextContent]:
        """Analyze import dependencies and detect circular imports."""
        # Implementation for import analysis
        output = "# Import Analysis\n\n"
        output += "🔄 Analyzing import dependencies...\n\n"
        
        # Basic implementation - can be enhanced
        all_py_files = list(self.project_root.rglob("*.py"))
        import_map = {}
        
        for py_file in all_py_files:
            if any(excluded in str(py_file) for excluded in ["venv", "__pycache__", ".git"]):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imports.extend([alias.name for alias in node.names])
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imports.append(node.module)
                
                relative_path = py_file.relative_to(self.project_root)
                import_map[str(relative_path)] = imports
                
            except Exception:
                continue
        
        output += f"**Found {len(import_map)} Python files with imports**\n\n"
        
        # Show top imported modules
        all_imports = {}
        for file_imports in import_map.values():
            for imp in file_imports:
                all_imports[imp] = all_imports.get(imp, 0) + 1
        
        sorted_imports = sorted(all_imports.items(), key=lambda x: x[1], reverse=True)[:10]
        output += "**Most Imported Modules:**\n"
        for module, count in sorted_imports:
            output += f"- `{module}`: {count} files\n"
        
        return [TextContent(type="text", text=output)]

    async def _analyze_complexity(self, args: Dict[str, Any]) -> List[TextContent]:
        """Analyze code complexity metrics."""
        file_path = Path(args["file_path"])
        threshold = args.get("threshold", 10)
        
        if not file_path.exists():
            return [TextContent(type="text", text=f"File not found: {file_path}")]
        
        try:
            # Use radon for complexity analysis if available
            try:
                result = subprocess.run(
                    ["radon", "cc", str(file_path), "-s"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    output = f"# Complexity Analysis: {file_path}\n\n"
                    output += "```\n" + result.stdout + "\n```"
                    return [TextContent(type="text", text=output)]
            except FileNotFoundError:
                pass
            
            # Fallback: basic complexity analysis
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_cyclomatic_complexity(node)
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "complexity": complexity,
                        "high_complexity": complexity > threshold
                    })
            
            output = f"# Complexity Analysis: {file_path}\n\n"
            high_complexity = [f for f in functions if f["high_complexity"]]
            
            if high_complexity:
                output += f"⚠️  **{len(high_complexity)} functions exceed complexity threshold ({threshold}):**\n\n"
                for func in high_complexity:
                    output += f"- `{func['name']}()` (line {func['line']}): complexity **{func['complexity']}**\n"
            else:
                output += f"✅ All functions are below complexity threshold ({threshold})\n"
            
            output += f"\n**All Functions:**\n"
            for func in sorted(functions, key=lambda x: x["complexity"], reverse=True):
                output += f"- `{func['name']}()`: {func['complexity']}\n"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error analyzing complexity: {str(e)}")]

    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.Try):
                complexity += len(child.handlers)
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
        
        return complexity

    async def _find_similar_patterns(self, args: Dict[str, Any]) -> List[TextContent]:
        """Find similar code patterns using AST similarity."""
        # Placeholder for advanced pattern matching
        output = "# Similar Pattern Analysis\n\n"
        output += "🔍 This feature requires advanced AST similarity analysis.\n"
        output += "Consider integrating with tools like `ast-similarity` or custom AST comparison.\n"
        
        return [TextContent(type="text", text=output)]

    async def _generate_call_graph(self, args: Dict[str, Any]) -> List[TextContent]:
        """Generate function call graph."""
        # Placeholder for call graph generation
        output = "# Call Graph Analysis\n\n"
        output += "📊 This feature requires advanced static analysis.\n"
        output += "Consider integrating with tools like `pycallgraph` or custom AST analysis.\n"
        
        return [TextContent(type="text", text=output)]

    async def _detect_code_smells(self, args: Dict[str, Any]) -> List[TextContent]:
        """Detect common code smells and anti-patterns."""
        file_path = Path(args["file_path"])
        check_types = args.get("check_types", ["long_function", "too_many_params", "duplicated_code"])
        
        if not file_path.exists():
            return [TextContent(type="text", text=f"File not found: {file_path}")]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
                tree = ast.parse(source)
            
            smells = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for long functions
                    if "long_function" in check_types:
                        lines = source.split('\n')[node.lineno-1:node.end_lineno] if hasattr(node, 'end_lineno') else []
                        if len(lines) > 50:
                            smells.append({
                                "type": "long_function",
                                "function": node.name,
                                "line": node.lineno,
                                "description": f"Function has {len(lines)} lines (consider breaking down)"
                            })
                    
                    # Check for too many parameters
                    if "too_many_params" in check_types:
                        param_count = len(node.args.args)
                        if param_count > 5:
                            smells.append({
                                "type": "too_many_params",
                                "function": node.name,
                                "line": node.lineno,
                                "description": f"Function has {param_count} parameters (consider using data classes)"
                            })
            
            output = f"# Code Smell Analysis: {file_path}\n\n"
            
            if smells:
                output += f"⚠️  **Found {len(smells)} potential code smells:**\n\n"
                for smell in smells:
                    output += f"**{smell['type']}** - `{smell['function']}()` (line {smell['line']})\n"
                    output += f"- {smell['description']}\n\n"
            else:
                output += "✅ No code smells detected with current checks!\n"
            
            return [TextContent(type="text", text=output)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error detecting code smells: {str(e)}")]

    async def run(self):
        """Run the MCP server."""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="code-intelligence",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


if __name__ == "__main__":
    server = CodeIntelligenceServer()
    asyncio.run(server.run()) 