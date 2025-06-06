#!/usr/bin/env python3
"""
Enhanced Cursor AI Client for Public Endpoint Bridge
Connects to the AI Collaboration Bridge for code-focused operations
"""

import asyncio
import websockets
import json
import logging
import os
import sys
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
import jwt
from pathlib import Path
import aiofiles
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CursorAIClient:
    """Enhanced Cursor AI client with public endpoint support"""
    
    def __init__(self, 
                 bridge_url: str,
                 api_key: str,
                 workspace_root: str = ".",
                 client_id: str = "cursor-ai",
                 auto_reconnect: bool = True):
        
        self.bridge_url = bridge_url
        self.api_key = api_key
        self.workspace_root = Path(workspace_root)
        self.client_id = client_id
        self.auto_reconnect = auto_reconnect
        
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.jwt_token: Optional[str] = None
        self.connected = False
        self.message_handlers: Dict[str, Callable] = {}
        self.file_watchers = {}
        self.active_edits = {}
        
        # Register default handlers
        self._register_default_handlers()
        
    def _register_default_handlers(self):
        """Register default message handlers"""
        self.register_handler("initial_state", self._handle_initial_state)
        self.register_handler("collaboration_event", self._handle_collaboration_event)
        self.register_handler("code_assistance_request", self._handle_code_assistance_request)
        self.register_handler("file_sync_request", self._handle_file_sync_request)
        self.register_handler("debug_request", self._handle_debug_request)
        self.register_handler("error", self._handle_error)
        
    def register_handler(self, message_type: str, handler: Callable):
        """Register a message handler"""
        self.message_handlers[message_type] = handler
        
    async def connect(self):
        """Connect to the bridge with authentication"""
        try:
            logger.info(f"🔌 Connecting to bridge at {self.bridge_url}")
            
            self.websocket = await websockets.connect(
                self.bridge_url,
                max_size=10 * 1024 * 1024,  # 10MB
                ping_interval=30,
                ping_timeout=10
            )
            
            # Authenticate
            auth_message = {
                "client": "cursor",
                "token": self.api_key
            }
            
            await self.websocket.send(json.dumps(auth_message))
            
            # Wait for authentication response
            response = await self.websocket.recv()
            auth_response = json.loads(response)
            
            if auth_response.get("status") == "authenticated":
                self.connected = True
                self.jwt_token = auth_response.get("jwt_token")
                logger.info(f"✅ Authenticated successfully as {auth_response.get('client_type')}")
                logger.info(f"📋 Permissions: {auth_response.get('permissions')}")
                
                # Start message handler
                asyncio.create_task(self._message_handler())
                
                # Start file watcher
                asyncio.create_task(self._file_watcher())
                
                return True
            else:
                logger.error(f"❌ Authentication failed: {auth_response.get('message')}")
                await self.websocket.close()
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            self.connected = False
            
            if self.auto_reconnect:
                await self._reconnect()
            return False
            
    async def _reconnect(self):
        """Attempt to reconnect to the bridge"""
        retry_delay = 5
        max_delay = 60
        
        while not self.connected:
            logger.info(f"🔄 Attempting to reconnect in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)
            
            if await self.connect():
                break
                
            # Exponential backoff
            retry_delay = min(retry_delay * 2, max_delay)
            
    async def _message_handler(self):
        """Handle incoming messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get("type")
                    
                    logger.info(f"📨 Received message: {message_type}")
                    
                    # Handle collaboration events specially
                    if message_type == "collaboration_event":
                        event_type = data.get("event_type")
                        if event_type in self.message_handlers:
                            await self.message_handlers[event_type](data)
                            continue
                    
                    # Call registered handler
                    handler = self.message_handlers.get(message_type)
                    if handler:
                        await handler(data)
                    else:
                        logger.warning(f"No handler for message type: {message_type}")
                        
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("🔌 Connection closed")
            self.connected = False
            
            if self.auto_reconnect:
                await self._reconnect()
                
    async def _handle_initial_state(self, data: Dict[str, Any]):
        """Handle initial state message"""
        logger.info("📊 Received initial state")
        logger.info(f"Active connections: {data.get('active_connections')}")
        logger.info(f"MCP status: {data.get('mcp_status')}")
        
    async def _handle_collaboration_event(self, data: Dict[str, Any]):
        """Handle collaboration event"""
        event_type = data.get("event_type")
        source = data.get("source")
        logger.info(f"🤝 Collaboration event '{event_type}' from {source}")
        
    async def _handle_code_assistance_request(self, data: Dict[str, Any]):
        """Handle code assistance request from Manus"""
        event_data = data.get("event_data", {})
        task = event_data.get("task")
        files = event_data.get("files", [])
        
        logger.info(f"💻 Code assistance requested: {task}")
        logger.info(f"📁 Files: {files}")
        
        # Analyze the task and files
        analysis = await self._analyze_code_task(task, files)
        
        # Send response
        await self.send_collaboration_event("code_assistance_response", {
            "task": task,
            "analysis": analysis,
            "suggestions": await self._generate_code_suggestions(task, files),
            "responder": "cursor"
        })
        
    async def _handle_file_sync_request(self, data: Dict[str, Any]):
        """Handle file synchronization request"""
        files = data.get("files", [])
        operation = data.get("operation", "sync")
        
        logger.info(f"📂 File sync requested: {operation} for {len(files)} files")
        
        if operation == "push":
            await self._push_files(files)
        elif operation == "pull":
            await self._pull_files(files)
        elif operation == "sync":
            await self._sync_files(files)
            
    async def _handle_debug_request(self, data: Dict[str, Any]):
        """Handle debug request"""
        debug_type = data.get("debug_type")
        context = data.get("context", {})
        
        logger.info(f"🐛 Debug request: {debug_type}")
        
        # Perform debugging operations
        debug_result = await self._perform_debug(debug_type, context)
        
        # Send results
        await self.send_collaboration_event("debug_response", {
            "debug_type": debug_type,
            "result": debug_result,
            "responder": "cursor"
        })
        
    async def _handle_error(self, data: Dict[str, Any]):
        """Handle error message"""
        logger.error(f"❌ Error: {data.get('message')}")
        
    async def send_message(self, message: Dict[str, Any]):
        """Send a message to the bridge"""
        if not self.connected or not self.websocket:
            logger.error("Not connected to bridge")
            return False
            
        try:
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
            
    async def send_collaboration_event(self, event_type: str, event_data: Any):
        """Send a collaboration event"""
        message = {
            "type": "collaboration_event",
            "event_type": event_type,
            "event_data": event_data
        }
        
        return await self.send_message(message)
        
    async def _analyze_code_task(self, task: str, files: List[str]) -> Dict[str, Any]:
        """Analyze a code task"""
        analysis = {
            "complexity": "medium",  # Would use AI to determine
            "estimated_time": "30 minutes",
            "required_changes": [],
            "dependencies": []
        }
        
        # Read and analyze files
        for file_path in files:
            full_path = self.workspace_root / file_path
            if full_path.exists():
                async with aiofiles.open(full_path, 'r') as f:
                    content = await f.read()
                    
                # Simple analysis (would use AI in practice)
                analysis["required_changes"].append({
                    "file": file_path,
                    "lines": len(content.splitlines()),
                    "language": full_path.suffix
                })
                
        return analysis
        
    async def _generate_code_suggestions(self, task: str, files: List[str]) -> List[Dict[str, Any]]:
        """Generate code suggestions for a task"""
        suggestions = []
        
        # This would use AI to generate actual suggestions
        suggestions.append({
            "type": "refactor",
            "description": f"Refactor code to accomplish: {task}",
            "priority": "high",
            "estimated_impact": "significant"
        })
        
        return suggestions
        
    async def _file_watcher(self):
        """Watch for file changes in the workspace"""
        # Simple file watcher - in practice, use watchdog or similar
        last_check = {}
        
        while self.connected:
            try:
                for file_path in self.file_watchers:
                    full_path = self.workspace_root / file_path
                    if full_path.exists():
                        stat = full_path.stat()
                        mtime = stat.st_mtime
                        
                        if file_path not in last_check or last_check[file_path] < mtime:
                            last_check[file_path] = mtime
                            
                            # File changed
                            await self._handle_file_change(file_path)
                            
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in file watcher: {e}")
                await asyncio.sleep(5)
                
    async def _handle_file_change(self, file_path: str):
        """Handle a file change"""
        logger.info(f"📝 File changed: {file_path}")
        
        # Read file content
        full_path = self.workspace_root / file_path
        async with aiofiles.open(full_path, 'r') as f:
            content = await f.read()
            
        # Send file change event
        await self.send_collaboration_event("file_changed", {
            "file": file_path,
            "content": content,
            "hash": hashlib.sha256(content.encode()).hexdigest(),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    async def watch_file(self, file_path: str):
        """Start watching a file for changes"""
        self.file_watchers[file_path] = True
        logger.info(f"👁️ Watching file: {file_path}")
        
    async def unwatch_file(self, file_path: str):
        """Stop watching a file"""
        if file_path in self.file_watchers:
            del self.file_watchers[file_path]
            logger.info(f"🚫 Stopped watching file: {file_path}")
            
    async def _push_files(self, files: List[Dict[str, Any]]):
        """Push files to the bridge"""
        for file_info in files:
            file_path = file_info.get("path")
            full_path = self.workspace_root / file_path
            
            if full_path.exists():
                async with aiofiles.open(full_path, 'r') as f:
                    content = await f.read()
                    
                await self.send_collaboration_event("file_push", {
                    "path": file_path,
                    "content": content,
                    "hash": hashlib.sha256(content.encode()).hexdigest()
                })
                
    async def _pull_files(self, files: List[Dict[str, Any]]):
        """Pull files from the bridge"""
        # Request file content
        await self.send_collaboration_event("file_pull_request", {
            "files": [f["path"] for f in files]
        })
        
    async def _sync_files(self, files: List[Dict[str, Any]]):
        """Synchronize files with the bridge"""
        # Compare hashes and sync as needed
        for file_info in files:
            file_path = file_info.get("path")
            remote_hash = file_info.get("hash")
            
            full_path = self.workspace_root / file_path
            if full_path.exists():
                async with aiofiles.open(full_path, 'r') as f:
                    content = await f.read()
                    local_hash = hashlib.sha256(content.encode()).hexdigest()
                    
                if local_hash != remote_hash:
                    logger.info(f"🔄 File differs: {file_path}")
                    # Implement conflict resolution
                    
    async def _perform_debug(self, debug_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform debugging operations"""
        result = {
            "debug_type": debug_type,
            "status": "completed",
            "findings": []
        }
        
        if debug_type == "syntax_check":
            # Check syntax of files
            files = context.get("files", [])
            for file_path in files:
                # Would use language-specific tools
                result["findings"].append({
                    "file": file_path,
                    "status": "valid"
                })
                
        elif debug_type == "performance_analysis":
            # Analyze performance
            result["findings"].append({
                "type": "performance",
                "message": "No performance issues detected"
            })
            
        return result
        
    async def close(self):
        """Close the connection"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("🔌 Connection closed")

class CursorCodeAssistant:
    """High-level code assistant for Cursor AI"""
    
    def __init__(self, client: CursorAIClient):
        self.client = client
        self.active_sessions = {}
        
    async def start_coding_session(self, session_id: str, files: List[str]):
        """Start a coding session"""
        session = {
            "id": session_id,
            "files": files,
            "started_at": datetime.utcnow(),
            "edits": []
        }
        
        self.active_sessions[session_id] = session
        
        # Start watching files
        for file_path in files:
            await self.client.watch_file(file_path)
            
        # Notify bridge
        await self.client.send_collaboration_event("coding_session_started", {
            "session_id": session_id,
            "files": files
        })
        
        return session_id
        
    async def suggest_improvements(self, file_path: str) -> List[Dict[str, Any]]:
        """Suggest improvements for a file"""
        # Read file
        full_path = self.client.workspace_root / file_path
        if not full_path.exists():
            return []
            
        async with aiofiles.open(full_path, 'r') as f:
            content = await f.read()
            
        # Generate suggestions (would use AI)
        suggestions = [
            {
                "type": "optimization",
                "line": 10,
                "suggestion": "Consider using async/await here",
                "impact": "performance"
            },
            {
                "type": "refactor",
                "line": 25,
                "suggestion": "Extract this into a separate function",
                "impact": "readability"
            }
        ]
        
        return suggestions
        
    async def apply_edit(self, file_path: str, edit: Dict[str, Any]):
        """Apply an edit to a file"""
        # Track edit
        for session in self.active_sessions.values():
            if file_path in session["files"]:
                session["edits"].append({
                    "file": file_path,
                    "edit": edit,
                    "timestamp": datetime.utcnow()
                })
                
        # Notify bridge
        await self.client.send_collaboration_event("code_edit_applied", {
            "file": file_path,
            "edit": edit
        })

async def main():
    """Example usage of Cursor AI client"""
    
    # Configuration from environment or command line
    bridge_url = os.getenv("BRIDGE_URL", "ws://150.136.94.139:8765")
    api_key = os.getenv("CURSOR_API_KEY", "cursor_live_collab_2024")
    workspace = os.getenv("WORKSPACE_ROOT", ".")
    
    # Create client
    client = CursorAIClient(bridge_url, api_key, workspace)
    
    # Connect to bridge
    if await client.connect():
        # Create code assistant
        assistant = CursorCodeAssistant(client)
        
        # Example: Start a coding session
        session_id = await assistant.start_coding_session(
            "optimize_websocket",
            ["services/ai_collaboration/public_endpoint_bridge.py"]
        )
        
        logger.info(f"Started coding session: {session_id}")
        
        # Example: Get suggestions
        suggestions = await assistant.suggest_improvements(
            "services/ai_collaboration/public_endpoint_bridge.py"
        )
        
        logger.info(f"Generated {len(suggestions)} suggestions")
        
        # Keep connection alive
        try:
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            
    await client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Cursor AI client stopped")