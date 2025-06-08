#!/usr/bin/env python3
"""
🪃 Simple MCP Server for Roo Code Integration
Compatible with current MCP library version
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Simple HTTP server for basic MCP functionality
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RooMCPHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for Roo MCP integration"""
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            if self.path == "/health":
                self.send_health_response()
            elif self.path == "/capabilities":
                self.send_capabilities()
            elif self.path == "/tools":
                self.send_tools()
            else:
                self.send_error(404, "Not found")
        except Exception as e:
            logger.error(f"GET error: {e}")
            self.send_error(500, str(e))
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                request = json.loads(post_data.decode('utf-8'))
                
                if self.path == "/call":
                    response = self.handle_tool_call(request)
                    self.send_json_response(response)
                else:
                    self.send_error(404, "Not found")
            else:
                self.send_error(400, "No content")
        except Exception as e:
            logger.error(f"POST error: {e}")
            self.send_error(500, str(e))
    
    def send_health_response(self):
        """Send health check response"""
        response = {
            "status": "healthy",
            "service": "roo-mcp-server",
            "version": "1.0.0",
            "timestamp": time.time()
        }
        self.send_json_response(response)
    
    def send_capabilities(self):
        """Send server capabilities"""
        capabilities = {
            "tools": True,
            "resources": False,
            "prompts": False,
            "experimental": {}
        }
        self.send_json_response(capabilities)
    
    def send_tools(self):
        """Send available tools"""
        tools = [
            {
                "name": "get_project_context",
                "description": "Get current project context and recent changes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "depth": {"type": "integer", "default": 5}
                    }
                }
            },
            {
                "name": "analyze_code_structure",
                "description": "Analyze project code structure and dependencies",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "default": "."}
                    }
                }
            },
            {
                "name": "get_roo_config",
                "description": "Get current Roo configuration and mode settings",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "optimize_workflow",
                "description": "Optimize development workflow based on current task",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_type": {"type": "string"},
                        "complexity": {"type": "string", "enum": ["low", "medium", "high"]}
                    },
                    "required": ["task_type"]
                }
            }
        ]
        self.send_json_response({"tools": tools})
    
    def handle_tool_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call requests"""
        tool_name = request.get("tool")
        arguments = request.get("arguments", {})
        
        try:
            if tool_name == "get_project_context":
                return self.get_project_context(arguments)
            elif tool_name == "analyze_code_structure":
                return self.analyze_code_structure(arguments)
            elif tool_name == "get_roo_config":
                return self.get_roo_config(arguments)
            elif tool_name == "optimize_workflow":
                return self.optimize_workflow(arguments)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Tool call error: {e}")
            return {"error": str(e)}
    
    def get_project_context(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get project context"""
        try:
            context = {
                "project_name": "Orchestra AI",
                "current_directory": os.getcwd(),
                "git_branch": "main",
                "recent_files": [],
                "active_modes": [],
                "mcp_servers": ["roo-mcp-server"]
            }
            
            # Get recent files
            try:
                for file_path in Path(".").glob("**/*.py"):
                    if file_path.is_file() and file_path.stat().st_size < 100000:
                        context["recent_files"].append(str(file_path))
                        if len(context["recent_files"]) >= 10:
                            break
            except Exception:
                pass
            
            # Get Roo modes
            try:
                roo_config_path = Path(".roo/config.json")
                if roo_config_path.exists():
                    with open(roo_config_path) as f:
                        roo_config = json.load(f)
                    context["active_modes"] = [mode["name"] for mode in roo_config.get("modes", [])]
            except Exception:
                pass
            
            return {"result": context}
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_code_structure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code structure"""
        try:
            path = args.get("path", ".")
            structure = {
                "directories": [],
                "python_files": [],
                "config_files": [],
                "total_lines": 0
            }
            
            base_path = Path(path)
            if base_path.exists():
                for item in base_path.rglob("*"):
                    if item.is_dir() and not any(part.startswith('.') for part in item.parts):
                        structure["directories"].append(str(item))
                    elif item.suffix == ".py":
                        structure["python_files"].append(str(item))
                        try:
                            with open(item) as f:
                                structure["total_lines"] += len(f.readlines())
                        except Exception:
                            pass
                    elif item.suffix in [".json", ".yaml", ".yml", ".toml"]:
                        structure["config_files"].append(str(item))
            
            return {"result": structure}
        except Exception as e:
            return {"error": str(e)}
    
    def get_roo_config(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get Roo configuration"""
        try:
            config_data = {}
            
            # Main config
            roo_config_path = Path(".roo/config.json")
            if roo_config_path.exists():
                with open(roo_config_path) as f:
                    config_data["main"] = json.load(f)
            
            # MCP config
            mcp_config_path = Path(".roo/mcp.json")
            if mcp_config_path.exists():
                with open(mcp_config_path) as f:
                    config_data["mcp"] = json.load(f)
            
            # Mode files
            modes_dir = Path(".roo/modes")
            if modes_dir.exists():
                config_data["modes"] = {}
                for mode_file in modes_dir.glob("*.json"):
                    try:
                        with open(mode_file) as f:
                            config_data["modes"][mode_file.stem] = json.load(f)
                    except Exception:
                        pass
            
            return {"result": config_data}
        except Exception as e:
            return {"error": str(e)}
    
    def optimize_workflow(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize workflow"""
        try:
            task_type = args.get("task_type", "general")
            complexity = args.get("complexity", "medium")
            
            recommendations = {
                "suggested_mode": "orchestrator",
                "estimated_time": "15-30 minutes",
                "tools_needed": ["code-intelligence", "git-operations"],
                "best_practices": [],
                "cost_optimization": True
            }
            
            # Task-specific recommendations
            if task_type == "ui":
                recommendations.update({
                    "suggested_mode": "implementation",
                    "tools_needed": ["weaviate-direct", "web-scraping"],
                    "best_practices": ["Use UI-GPT-4O for frontend", "Component-based architecture"]
                })
            elif task_type == "debug":
                recommendations.update({
                    "suggested_mode": "debug",
                    "tools_needed": ["code-intelligence", "git-intelligence"],
                    "best_practices": ["Systematic debugging", "Error reproduction"]
                })
            elif task_type == "research":
                recommendations.update({
                    "suggested_mode": "research",
                    "tools_needed": ["web-scraping", "prompt-management"],
                    "best_practices": ["Use Gemini for research", "Comprehensive documentation"]
                })
            
            # Complexity adjustments
            if complexity == "high":
                recommendations["suggested_mode"] = "orchestrator"
                recommendations["estimated_time"] = "45-90 minutes"
                recommendations["best_practices"].append("Break into subtasks")
            elif complexity == "low":
                recommendations["estimated_time"] = "5-15 minutes"
            
            return {"result": recommendations}
        except Exception as e:
            return {"error": str(e)}
    
    def send_json_response(self, data: Dict[str, Any]):
        """Send JSON response"""
        json_data = json.dumps(data, indent=2)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(json_data)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to reduce noise"""
        if self.path not in ["/health"]:
            logger.info(f"{self.address_string()} - {format % args}")

class RooMCPServer:
    """Simple MCP Server for Roo integration"""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        
    def start(self):
        """Start the server"""
        try:
            self.server = HTTPServer((self.host, self.port), RooMCPHandler)
            logger.info(f"🪃 Roo MCP Server starting on {self.host}:{self.port}")
            
            # Start in thread for non-blocking operation
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            
            logger.info(f"✅ Roo MCP Server running on http://{self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
            return False
    
    def stop(self):
        """Stop the server"""
        if self.server:
            logger.info("Stopping Roo MCP Server...")
            self.server.shutdown()
            if self.thread:
                self.thread.join(timeout=5)
            logger.info("✅ Server stopped")
    
    def is_running(self) -> bool:
        """Check if server is running"""
        return self.server is not None and self.thread is not None and self.thread.is_alive()

def main():
    """Main entry point"""
    # Get port from environment or use default
    port = int(os.environ.get("MCP_SERVER_PORT", 8000))
    
    # Create and start server
    server = RooMCPServer(port=port)
    
    try:
        if server.start():
            logger.info("🎯 Server ready for Roo Code integration")
            logger.info("📋 Available endpoints:")
            logger.info(f"   • Health: http://localhost:{port}/health")
            logger.info(f"   • Capabilities: http://localhost:{port}/capabilities")
            logger.info(f"   • Tools: http://localhost:{port}/tools")
            logger.info("🪃 Roo Code can now connect to this MCP server")
            
            # Keep running until interrupted
            while server.is_running():
                time.sleep(1)
        else:
            logger.error("Failed to start server")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Received interrupt signal")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
    finally:
        server.stop()
        logger.info("👋 Roo MCP Server shutdown complete")

if __name__ == "__main__":
    main() 