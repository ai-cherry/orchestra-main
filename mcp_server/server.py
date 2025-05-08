#!/usr/bin/env python3
"""
mcp_server/server.py - Central Model Context Protocol (MCP) Server

This server acts as the central coordination point for all AI tools (Roo, Cline.bot, 
Gemini, Co-pilot) in the Orchestra framework. It provides a unified interface for 
memory management, context sharing, and workflow orchestration across all tools.

Key features:
- REST API for tool integrations
- WebSocket interface for real-time updates
- Persistent memory store with tiered access
- Cross-tool context synchronization
- Security and authentication layer
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

try:
    import flask
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    from flask_socketio import SocketIO
except ImportError:
    print("Flask dependencies not found. Install with: pip install flask flask-cors flask-socketio")
    print("Continuing with limited functionality...")

# Import extracted components
from .storage.memory_store import MemoryStore
from .tools.tool_manager import ToolManager
from .workflows.workflow_manager import WorkflowManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("mcp-server")

# Default configuration
DEFAULT_CONFIG = {
    "server": {
        "host": "0.0.0.0",
        "port": 8080,
        "debug": False,
    },
    "memory": {
        "storage_path": "/workspaces/orchestra-main/.mcp_memory",
        "ttl_seconds": 86400,  # 24 hours
        "max_items_per_key": 1000,
        "enable_compression": True,
    },
    "security": {
        "enable_auth": False,  # Simplified for single-user project
        "token_required": False,  # Simplified for single-user project
        "allowed_origins": ["*"],
    },
    "tools": {
        "roo": {
            "enabled": True,
            "api_endpoint": "http://localhost:8081",
            "memory_sync": True,
        },
        "cline": {
            "enabled": True,
            "api_endpoint": "http://localhost:8082",
            "memory_sync": True,
        },
        "gemini": {
            "enabled": False,
            "api_key_env": "GEMINI_API_KEY",
            "memory_sync": True,
        },
        "copilot": {
            "enabled": False,
            "memory_sync": False,
        }
    }
}

class MCPServer:
    """Model Context Protocol (MCP) Server."""
    
    def __init__(self, config_path: Optional[str] = None, 
                 memory_store=None, tool_manager=None, workflow_manager=None):
        """Initialize the MCP server with optional dependency injection.
        
        Args:
            config_path: Path to configuration file
            memory_store: Optional MemoryStore instance (for dependency injection)
            tool_manager: Optional ToolManager instance (for dependency injection)
            workflow_manager: Optional WorkflowManager instance (for dependency injection)
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Use injected dependencies or create new instances
        self.memory_store = memory_store or MemoryStore(self.config["memory"])
        self.tool_manager = tool_manager or ToolManager(self.config["tools"], self.memory_store)
        self.workflow_manager = workflow_manager or WorkflowManager(self.tool_manager, self.memory_store)
        
        # Initialize Flask application
        self.app = Flask(__name__)
        # Simplified CORS for single-user project
        CORS(self.app)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Configure routes
        self._configure_routes()
        
        logger.info("MCP server initialized")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Merged configuration dictionary
        """
        config = DEFAULT_CONFIG.copy()
        
        if config_path:
            try:
                with open(config_path, "r") as f:
                    user_config = json.load(f)
                    
                    # Update config with user settings
                    for section, section_config in user_config.items():
                        if section in config:
                            config[section].update(section_config)
                        else:
                            config[section] = section_config
                    
                    logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                logger.info("Using default configuration")
        else:
            logger.info("No configuration file provided, using defaults")
        
        return config
    
    def _configure_routes(self):
        """Configure Flask routes."""
        # Define API routes
        @self.app.route("/api/status", methods=["GET"])
        def status():
            return jsonify({
                "status": "running",
                "tools": self.tool_manager.get_enabled_tools(),
                "workflows": len(self.workflow_manager.get_available_workflows()),
            })
        
        @self.app.route("/api/memory", methods=["GET"])
        def get_memory():
            key = request.args.get("key")
            scope = request.args.get("scope", "session")
            tool = request.args.get("tool")
            
            if not key:
                return jsonify({"error": "Missing key parameter"}), 400
            
            content = self.memory_store.get(key, scope, tool)
            if content is None:
                return jsonify({"error": "Memory not found"}), 404
            
            return jsonify({"key": key, "content": content})
        
        @self.app.route("/api/memory", methods=["POST"])
        def set_memory():
            data = request.json
            
            if not data or "key" not in data or "content" not in data:
                return jsonify({"error": "Missing required parameters"}), 400
            
            key = data["key"]
            content = data["content"]
            scope = data.get("scope", "session")
            tool = data.get("tool")
            ttl = data.get("ttl")
            
            success = self.memory_store.set(key, content, scope, tool, ttl)
            if not success:
                return jsonify({"error": "Failed to set memory"}), 500
            
            return jsonify({"success": True})
        
        @self.app.route("/api/memory", methods=["DELETE"])
        def delete_memory():
            key = request.args.get("key")
            scope = request.args.get("scope", "session")
            tool = request.args.get("tool")
            
            if not key:
                return jsonify({"error": "Missing key parameter"}), 400
            
            success = self.memory_store.delete(key, scope, tool)
            if not success:
                return jsonify({"error": "Failed to delete memory"}), 500
            
            return jsonify({"success": True})
        
        @self.app.route("/api/memory/sync", methods=["POST"])
        def sync_memory():
            data = request.json
            
            if not data or "key" not in data or "source_tool" not in data or "target_tool" not in data:
                return jsonify({"error": "Missing required parameters"}), 400
            
            key = data["key"]
            source_tool = data["source_tool"]
            target_tool = data["target_tool"]
            scope = data.get("scope", "session")
            
            success = self.memory_store.sync(key, source_tool, target_tool, scope)
            if not success:
                return jsonify({"error": "Failed to sync memory"}), 500
            
            return jsonify({"success": True})
        
        @self.app.route("/api/execute", methods=["POST"])
        def execute():
            data = request.json
            
            if not data or "tool" not in data or "mode" not in data or "prompt" not in data:
                return jsonify({"error": "Missing required parameters"}), 400
            
            tool = data["tool"]
            mode = data["mode"]
            prompt = data["prompt"]
            context = data.get("context")
            
            result = self.tool_manager.execute(tool, mode, prompt, context)
            if result is None:
                return jsonify({"error": f"Failed to execute with tool {tool}"}), 500
            
            return jsonify({"result": result})
        
        # Workflow routes
        @self.app.route("/api/workflows", methods=["GET"])
        def get_workflows():
            return jsonify(self.workflow_manager.get_available_workflows())
        
        @self.app.route("/api/workflows/execute", methods=["POST"])
        def execute_workflow():
            data = request.json
            
            if not data or "workflow_id" not in data:
                return jsonify({"error": "Missing workflow_id parameter"}), 400
            
            workflow_id = data["workflow_id"]
            parameters = data.get("parameters")
            tool = data.get("tool")
            
            result = self.workflow_manager.execute_workflow(workflow_id, parameters, tool)
            if result is None:
                return jsonify({"error": f"Failed to execute workflow {workflow_id}"}), 500
            
            return jsonify({"result": result})
        
        @self.app.route("/api/workflows/cross-tool", methods=["POST"])
        def execute_cross_tool_workflow():
            data = request.json
            
            if not data or "workflow_id" not in data:
                return jsonify({"error": "Missing workflow_id parameter"}), 400
            
            workflow_id = data["workflow_id"]
            tools = data.get("tools")
            
            result = self.workflow_manager.execute_cross_tool_workflow(workflow_id, tools)
            if result is None:
                return jsonify({"error": f"Failed to execute cross-tool workflow {workflow_id}"}), 500
            
            return jsonify({"result": result})
    
    def run(self):
        """Run the MCP server."""
        host = self.config["server"]["host"]
        port = self.config["server"]["port"]
        debug = self.config["server"]["debug"]
        
        logger.info(f"Starting MCP server on {host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MCP Server")
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()
    
    server = MCPServer(args.config)
    server.run()


if __name__ == "__main__":
    main()