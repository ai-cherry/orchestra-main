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
import time
import logging
import argparse
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

try:
    import flask
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    from flask_socketio import SocketIO
except ImportError:
    print("Flask dependencies not found. Install with: pip install flask flask-cors flask-socketio")
    print("Continuing with limited functionality...")

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
        "enable_auth": False,
        "token_required": False,
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

class MemoryStore:
    """Persistent memory store for MCP server."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the memory store with configuration."""
        self.config = config
        self.storage_path = Path(config["storage_path"])
        self.ttl_seconds = config["ttl_seconds"]
        self.max_items = config["max_items_per_key"]
        self.enable_compression = config["enable_compression"]
        
        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(exist_ok=True, parents=True)
        
        # Initialize memory cache
        self.memory_cache = {}
        
        # Load existing memory items
        self._load_memory()
        
        # Start background cleanup thread
        self._start_cleanup_thread()
    
    def _load_memory(self):
        """Load existing memory items from storage."""
        try:
            memory_files = list(self.storage_path.glob("*.json"))
            logger.info(f"Loading {len(memory_files)} memory files from storage")
            
            for memory_file in memory_files:
                try:
                    with open(memory_file, "r") as f:
                        memory_data = json.load(f)
                        
                        # Check if the memory item has expired
                        if "expiry" in memory_data:
                            expiry_time = datetime.fromisoformat(memory_data["expiry"])
                            if expiry_time < datetime.now():
                                # Memory item has expired, delete it
                                memory_file.unlink()
                                continue
                        
                        # Add memory item to cache
                        key = memory_file.stem
                        self.memory_cache[key] = memory_data["content"]
                except Exception as e:
                    logger.error(f"Error loading memory file {memory_file}: {e}")
        except Exception as e:
            logger.error(f"Error loading memory: {e}")
    
    def _start_cleanup_thread(self):
        """Start a background thread to clean up expired memory items."""
        def cleanup_task():
            while True:
                try:
                    # Sleep for a while before cleaning up
                    time.sleep(3600)  # Run every hour
                    
                    # Find and delete expired memory files
                    memory_files = list(self.storage_path.glob("*.json"))
                    for memory_file in memory_files:
                        try:
                            with open(memory_file, "r") as f:
                                memory_data = json.load(f)
                                
                                # Check if the memory item has expired
                                if "expiry" in memory_data:
                                    expiry_time = datetime.fromisoformat(memory_data["expiry"])
                                    if expiry_time < datetime.now():
                                        # Memory item has expired, delete it
                                        memory_file.unlink()
                                        
                                        # Remove from cache if present
                                        key = memory_file.stem
                                        if key in self.memory_cache:
                                            del self.memory_cache[key]
                        except Exception as e:
                            logger.error(f"Error checking memory file {memory_file}: {e}")
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
        
        # Start the cleanup thread
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
    
    def get(self, key: str, scope: str = "session", tool: Optional[str] = None) -> Optional[Any]:
        """Get a memory item."""
        # Construct the full key based on scope and tool
        full_key = self._get_full_key(key, scope, tool)
        
        # Check if the memory item is in the cache
        if full_key in self.memory_cache:
            return self.memory_cache[full_key]
        
        # Check if the memory item is in storage
        memory_file = self.storage_path / f"{full_key}.json"
        if memory_file.exists():
            try:
                with open(memory_file, "r") as f:
                    memory_data = json.load(f)
                    
                    # Check if the memory item has expired
                    if "expiry" in memory_data:
                        expiry_time = datetime.fromisoformat(memory_data["expiry"])
                        if expiry_time < datetime.now():
                            # Memory item has expired, delete it
                            memory_file.unlink()
                            return None
                    
                    # Add to cache and return
                    self.memory_cache[full_key] = memory_data["content"]
                    return memory_data["content"]
            except Exception as e:
                logger.error(f"Error reading memory file {memory_file}: {e}")
        
        return None
    
    def set(self, key: str, content: Any, scope: str = "session", 
            tool: Optional[str] = None, ttl: Optional[int] = None) -> bool:
        """Set a memory item."""
        # Construct the full key based on scope and tool
        full_key = self._get_full_key(key, scope, tool)
        
        # Add to cache
        self.memory_cache[full_key] = content
        
        # Calculate expiry time
        ttl = ttl or self.ttl_seconds
        expiry_time = datetime.now() + timedelta(seconds=ttl)
        
        # Prepare memory data
        memory_data = {
            "content": content,
            "scope": scope,
            "tool": tool,
            "created": datetime.now().isoformat(),
            "expiry": expiry_time.isoformat(),
        }
        
        # Write to storage
        memory_file = self.storage_path / f"{full_key}.json"
        try:
            with open(memory_file, "w") as f:
                json.dump(memory_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error writing memory file {memory_file}: {e}")
            return False
    
    def delete(self, key: str, scope: str = "session", tool: Optional[str] = None) -> bool:
        """Delete a memory item."""
        # Construct the full key based on scope and tool
        full_key = self._get_full_key(key, scope, tool)
        
        # Remove from cache
        if full_key in self.memory_cache:
            del self.memory_cache[full_key]
        
        # Remove from storage
        memory_file = self.storage_path / f"{full_key}.json"
        if memory_file.exists():
            try:
                memory_file.unlink()
                return True
            except Exception as e:
                logger.error(f"Error deleting memory file {memory_file}: {e}")
                return False
        
        return True
    
    def sync(self, key: str, source_tool: str, target_tool: str, 
            scope: str = "session") -> bool:
        """Sync a memory item between tools."""
        # Get the memory item from the source tool
        source_content = self.get(key, scope, source_tool)
        if source_content is None:
            return False
        
        # Set the memory item for the target tool
        return self.set(key, source_content, scope, target_tool)
    
    def _get_full_key(self, key: str, scope: str, tool: Optional[str] = None) -> str:
        """Construct the full key based on scope and tool."""
        if tool:
            return f"{scope}:{tool}:{key}"
        return f"{scope}:{key}"

class ToolManager:
    """Manager for AI tool integrations."""
    
    def __init__(self, config: Dict[str, Any], memory_store: MemoryStore):
        """Initialize the tool manager with configuration."""
        self.config = config
        self.memory_store = memory_store
        self.tools = {}
        
        # Initialize tool integrations
        for tool_name, tool_config in config.items():
            if tool_config.get("enabled", False):
                self.tools[tool_name] = {
                    "config": tool_config,
                    "status": "initialized",
                }
                logger.info(f"Initialized tool integration: {tool_name}")
    
    def get_enabled_tools(self) -> List[str]:
        """Get the names of all enabled tools."""
        return list(self.tools.keys())
    
    def execute(self, tool: str, mode: str, prompt: str, 
               context: Optional[str] = None) -> Optional[str]:
        """Execute a prompt with a specific tool and mode."""
        if tool not in self.tools:
            logger.error(f"Tool not enabled: {tool}")
            return None
        
        tool_config = self.tools[tool]["config"]
        
        # Execute based on the tool type
        if tool == "roo":
            return self._execute_roo(mode, prompt, context)
        elif tool == "cline":
            return self._execute_cline(mode, prompt, context)
        elif tool == "gemini":
            return self._execute_gemini(mode, prompt, context)
        elif tool == "copilot":
            return self._execute_copilot(mode, prompt, context)
        
        logger.error(f"Unsupported tool: {tool}")
        return None
    
    def _execute_roo(self, mode: str, prompt: str, context: Optional[str] = None) -> Optional[str]:
        """Execute a prompt with Roo."""
        try:
            import subprocess
            
            # Prepare command
            cmd = ["roo-cli", mode, prompt]
            if context:
                # Write context to a temporary file
                context_file = Path("/tmp/roo_context.txt")
                with open(context_file, "w") as f:
                    f.write(context)
                cmd.extend(["--context-file", str(context_file)])
            
            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except ImportError:
            logger.error("roo-cli not found in PATH")
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing Roo: {e}")
            return None
        except Exception as e:
            logger.error(f"Error: {e}")
            return None
    
    def _execute_cline(self, mode: str, prompt: str, context: Optional[str] = None) -> Optional[str]:
        """Execute a prompt with Cline.bot."""
        try:
            from cline_integration import ClineModeManager
            
            # Create mode manager
            mode_manager = ClineModeManager()
            
            # Execute in the specified mode
            result = mode_manager.execute_in_mode(mode, prompt, context)
            return result
        except ImportError:
            logger.error("cline_integration module not found")
            return None
        except Exception as e:
            logger.error(f"Error executing Cline: {e}")
            return None
    
    def _execute_gemini(self, mode: str, prompt: str, context: Optional[str] = None) -> Optional[str]:
        """Execute a prompt with Gemini."""
        # Placeholder for Gemini integration
        logger.error("Gemini integration not yet implemented")
        return None
    
    def _execute_copilot(self, mode: str, prompt: str, context: Optional[str] = None) -> Optional[str]:
        """Execute a prompt with Co-pilot."""
        # Placeholder for Co-pilot integration
        logger.error("Co-pilot integration not yet implemented")
        return None

class WorkflowManager:
    """Manager for cross-tool workflows."""
    
    def __init__(self, tool_manager: ToolManager, memory_store: MemoryStore):
        """Initialize the workflow manager."""
        self.tool_manager = tool_manager
        self.memory_store = memory_store
        self.workflows = {}
        
        # Load workflows from directories
        self._load_workflows()
    
    def _load_workflows(self):
        """Load workflows from directories."""
        # Directories to search for workflows
        workflow_dirs = [
            Path("/workspaces/orchestra-main/mcp_workflows"),
            Path("/workspaces/orchestra-main/user_workflows"),
        ]
        
        for workflow_dir in workflow_dirs:
            if workflow_dir.exists():
                for workflow_file in workflow_dir.glob("*.json"):
                    try:
                        with open(workflow_file, "r") as f:
                            workflow_def = json.load(f)
                            workflow_id = workflow_def.get("workflow_id")
                            if workflow_id:
                                self.workflows[workflow_id] = workflow_def
                                logger.info(f"Loaded workflow: {workflow_id}")
                    except Exception as e:
                        logger.error(f"Error loading workflow {workflow_file}: {e}")
    
    def get_available_workflows(self) -> Dict[str, Any]:
        """Get all available workflows."""
        return {
            workflow_id: {
                "description": workflow_def.get("description", ""),
                "target_tools": workflow_def.get("target_tools", []),
                "steps": len(workflow_def.get("steps", [])),
            }
            for workflow_id, workflow_def in self.workflows.items()
        }
    
    def execute_workflow(self, workflow_id: str, parameters: Dict[str, Any] = None, 
                        tool: Optional[str] = None) -> Optional[str]:
        """Execute a workflow."""
        if workflow_id not in self.workflows:
            logger.error(f"Workflow not found: {workflow_id}")
            return None
        
        workflow_def = self.workflows[workflow_id]
        target_tools = workflow_def.get("target_tools", [])
        
        # Determine the tool to use
        if not tool:
            if target_tools:
                # Use the first target tool that is enabled
                for target_tool in target_tools:
                    if target_tool in self.tool_manager.get_enabled_tools():
                        tool = target_tool
                        break
            
            if not tool:
                # Use the first enabled tool
                enabled_tools = self.tool_manager.get_enabled_tools()
                if enabled_tools:
                    tool = enabled_tools[0]
                else:
                    logger.error("No enabled tools available")
                    return None
        
        # Execute the workflow
        logger.info(f"Executing workflow {workflow_id} with tool {tool}")
        
        # Extract steps
        steps = workflow_def.get("steps", [])
        if not steps:
            logger.error(f"Workflow {workflow_id} has no steps")
            return None
        
        # Execute steps
        results = []
        for i, step in enumerate(steps):
            step_type = step.get("type")
            
            if step_type == "mode":
                mode = step.get("mode")
                task = step.get("task")
                
                # Replace parameters in the task
                if parameters:
                    for param_key, param_value in parameters.items():
                        task = task.replace(f"{{{param_key}}}", str(param_value))
                
                # Get context from previous steps if needed
                context = None
                if i > 0:
                    context = "\n\n".join(results)
                
                # Execute the step
                result = self.tool_manager.execute(tool, mode, task, context)
                if result:
                    results.append(result)
                else:
                    logger.error(f"Failed to execute step {i+1} of workflow {workflow_id}")
            else:
                logger.error(f"Unsupported step type: {step_type}")
        
        # Combine results
        final_result = "\n\n".join(results)
        
        # Store workflow result in memory
        self.memory_store.set(
            f"workflow_{workflow_id}_result",
            final_result,
            scope="session",
            tool=tool
        )
        
        return final_result
    
    def execute_cross_tool_workflow(self, workflow_id: str, 
                                   tools: List[str] = None) -> Optional[str]:
        """Execute a workflow across multiple tools."""
        if workflow_id not in self.workflows:
            logger.error(f"Workflow not found: {workflow_id}")
            return None
        
        workflow_def = self.workflows[workflow_id]
        steps = workflow_def.get("steps", [])
        
        if not steps:
            logger.error(f"Workflow {workflow_id} has no steps")
            return None
        
        # Determine the tools to use
        if not tools:
            tools = self.tool_manager.get_enabled_tools()
        
        if not tools:
            logger.error("No enabled tools available")
            return None
        
        # Assign steps to tools
        steps_per_tool = len(steps) // len(tools)
        tool_assignments = {}
        
        for i, step in enumerate(steps):
            tool_index = min(i // steps_per_tool, len(tools) - 1)
            tool = tools[tool_index]
            
            if tool not in tool_assignments:
                tool_assignments[tool] = []
            
            tool_assignments[tool].append(step)
        
        # Execute steps for each tool
        results = []
        for tool, tool_steps in tool_assignments.items():
            # Execute steps for this tool
            tool_results = []
            for i, step in enumerate(tool_steps):
                step_type = step.get("type")
                
                if step_type == "mode":
                    mode = step.get("mode")
                    task = step.get("task")
                    
                    # Get context from previous steps if needed
                    context = None
                    if i > 0:
                        context = "\n\n".join(tool_results)
                    
                    # Execute the step
                    result = self.tool_manager.execute(tool, mode, task, context)
                    if result:
                        tool_results.append(result)
                    else:
                        logger.error(f"Failed to execute step for {tool}")
                else:
                    logger.error(f"Unsupported step type: {step_type}")
            
            # Add this tool's results
            results.append(f"=== Results from {tool} ===\n\n{' '.join(tool_results)}")
            
            # Store tool's results in memory
            self.memory_store.set(
                f"workflow_{workflow_id}_result_{tool}",
                " ".join(tool_results),
                scope="session",
                tool=tool
            )
        
        # Combine results from all tools
        final_result = "\n\n".join(results)
        
        # Store combined results in memory
        self.memory_store.set(
            f"workflow_{workflow_id}_result",
            final_result,
            scope="global"
        )
        
        return final_result

class MCPServer:
    """Model Context Protocol (MCP) Server."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the MCP server."""
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.memory_store = MemoryStore(self.config["memory"])
        self.tool_manager = ToolManager(self.config["tools"], self.memory_store)
        self.workflow_manager = WorkflowManager(self.tool_manager, self.memory_store)
        
        # Initialize Flask application
        self.app = Flask(__name__)
        CORS(self.app, origins=self.config["security"]["allowed_origins"])
        self.socketio = SocketIO(self.app, cors_allowed_origins=self.config["security"]["allowed_origins"])
        
        # Configure routes
        self._configure_routes()
        
        logger.info("MCP server initialized")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
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
                return jsonify({"error": "Memory item not found"}), 404
            
            return jsonify({"content": content})
        
        @self.app.route("/api/memory", methods=["POST"])
        def set_memory():
            data = request.json
            if not data:
                return jsonify({"error": "Missing request body"}), 400
            
            key = data.get("key")
            content = data.get("content")
            scope = data.get("scope", "session")
            tool = data.get("tool")
            ttl = data.get("ttl")
            
            if not key or content is None:
                return jsonify({"error": "Missing key or content parameter"}), 400
            
            result = self.memory_store.set(key, content, scope, tool, ttl)
            if not result:
                return jsonify({"error": "Failed to set memory item"}), 500
            
            return jsonify({"success": True})
        
        @self.app.route("/api/memory", methods=["DELETE"])
        def delete_memory():
            key = request.args.get("key")
            scope = request.args.get("scope", "session")
            tool = request.args.get("tool")
            
            if not key:
                return jsonify({"error": "Missing key parameter"}), 400
            
            result = self.memory_store.delete(key, scope, tool)
            if not result:
                return jsonify({"error": "Failed to delete memory item"}), 500
            
            return jsonify({"success": True})
        
        @self.app.route("/api/memory/sync", methods=["POST"])
        def sync_memory():
            data = request.json
            if not data:
                return jsonify({"error": "Missing request body"}), 400
            
            key = data.get("key")
            source_tool = data.get("source_tool")
            target_tool = data.get("target_tool")
            scope = data.get("scope", "session")
            
            if not key or not source_tool or not target_tool:
                return jsonify({"error": "Missing parameters"}), 400
            
            result = self.memory_store.sync(key, source_tool, target_tool, scope)
            if not result:
                return jsonify({"error": "Failed to sync memory item"}), 500
            
            return jsonify({"success": True})
        
        @self.app.route("/api/execute", methods=["POST"])
        def execute():
            data = request.json
            if not data:
                return jsonify({"error": "Missing request body"}), 400
            
            tool = data.get("tool")
            mode = data.get("mode")
            prompt = data.get("prompt")
            context = data.get("context")
            
            if not tool or not mode or not prompt:
                return jsonify({"error": "Missing parameters"}), 400
            
            result = self.tool_manager.execute(tool, mode, prompt, context)
            if result is None:
                return jsonify({"error": "Failed to execute"}), 500
            
            return jsonify({"result": result})
        
        @self.app.route("/api/workflows", methods=["GET"])
        def get_workflows():
            return jsonify(self.workflow_manager.get_available_workflows())
        
        @self.app.route("/api/workflows/execute", methods=["POST"])
        def execute_workflow():
            data = request.json
            if not data:
                return jsonify({"error": "Missing request body"}), 400
            
            workflow_id = data.get("workflow_id")
            parameters = data.get("parameters")
            tool = data.get("tool")
            
            if not workflow_id:
                return jsonify({"error": "Missing workflow_id parameter"}), 400
            
            result = self.workflow_manager.execute_workflow(workflow_id, parameters, tool)
            if result is None:
                return jsonify({"error": "Failed to execute workflow"}), 500
            
            return jsonify({"result": result})
        
        @self.app.route("/api/workflows/cross-tool", methods=["POST"])
        def execute_cross_tool_workflow():
            data = request.json
            if not data:
                return jsonify({"error": "Missing request body"}), 400
            
            workflow_id = data.get("workflow_id")
            tools = data.get("tools")
            
            if not workflow_id:
                return jsonify({"error": "Missing workflow_id parameter"}), 400
            
            result = self.workflow_manager.execute_cross_tool_workflow(workflow_id, tools)
            if result is None:
                return jsonify({"error": "Failed to execute cross-tool workflow"}), 500
            
            return jsonify({"result": result})
    
    def run(self):
        """Run the MCP server."""
        host = self.config["server"]["host"]
        port = self.config["server"]["port"]
        debug = self.config["server"]["debug"]
        
        logger.info(f"Starting MCP server on {host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug)

def main():
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="Model Context Protocol (MCP) Server")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--host", help="Host to bind to")
    parser.add_argument("--port", type=int, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Create server
    server = MCPServer(args.config)
    
    # Override configuration with command-line arguments
    if args.host:
        server.config["server"]["host"] = args.host
    if args.port:
        server.config["server"]["port"] = args.port
    if args.debug:
        server.config["server"]["debug"] = True
    
    # Run server
    server.run()

if __name__ == "__main__":
    main()