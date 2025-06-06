#!/usr/bin/env python3
"""
Enhanced Manus AI Client for Public Endpoint Bridge
Connects to the AI Collaboration Bridge with authentication and security
"""

import asyncio
import websockets
import json
import logging
import os
import sys
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import jwt
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ManusAIClient:
    """Enhanced Manus AI client with public endpoint support"""
    
    def __init__(self, 
                 bridge_url: str,
                 api_key: str,
                 client_id: str = "manus-ai",
                 auto_reconnect: bool = True):
        
        self.bridge_url = bridge_url
        self.api_key = api_key
        self.client_id = client_id
        self.auto_reconnect = auto_reconnect
        
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.jwt_token: Optional[str] = None
        self.connected = False
        self.message_handlers: Dict[str, Callable] = {}
        self.shared_state = {}
        
        # Register default handlers
        self._register_default_handlers()
        
    def _register_default_handlers(self):
        """Register default message handlers"""
        self.register_handler("initial_state", self._handle_initial_state)
        self.register_handler("workflow_updated", self._handle_workflow_update)
        self.register_handler("collaboration_event", self._handle_collaboration_event)
        self.register_handler("system_health", self._handle_system_health)
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
                "client": "manus",
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
        self.shared_state = data.get("shared_state", {})
        logger.info("📊 Received initial state")
        logger.info(f"Active connections: {data.get('active_connections')}")
        logger.info(f"MCP status: {data.get('mcp_status')}")
        
    async def _handle_workflow_update(self, data: Dict[str, Any]):
        """Handle workflow update"""
        workflow_id = data.get("workflow_id")
        state = data.get("state")
        logger.info(f"🔄 Workflow {workflow_id} updated by {data.get('updated_by')}")
        
    async def _handle_collaboration_event(self, data: Dict[str, Any]):
        """Handle collaboration event"""
        event_type = data.get("event_type")
        source = data.get("source")
        logger.info(f"🤝 Collaboration event '{event_type}' from {source}")
        
    async def _handle_system_health(self, data: Dict[str, Any]):
        """Handle system health update"""
        logger.info(f"💚 System health: {data.get('active_connections')} connections")
        
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
            
    async def execute_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]):
        """Execute a workflow through the bridge"""
        message = {
            "type": "workflow_update",
            "workflow_id": workflow_id,
            "state": {
                "status": "started",
                "data": workflow_data,
                "started_at": datetime.utcnow().isoformat()
            }
        }
        
        return await self.send_message(message)
        
    async def query_mcp_server(self, server: str, query: Dict[str, Any]):
        """Query an MCP server"""
        message = {
            "type": "mcp_query",
            "server": server,
            "query": query
        }
        
        return await self.send_message(message)
        
    async def send_collaboration_event(self, event_type: str, event_data: Any):
        """Send a collaboration event"""
        message = {
            "type": "collaboration_event",
            "event_type": event_type,
            "event_data": event_data
        }
        
        return await self.send_message(message)
        
    async def request_sync(self):
        """Request state synchronization"""
        message = {"type": "sync_request"}
        return await self.send_message(message)
        
    async def close(self):
        """Close the connection"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("🔌 Connection closed")

class ManusAIOrchestrator:
    """High-level orchestrator for Manus AI operations"""
    
    def __init__(self, client: ManusAIClient):
        self.client = client
        self.active_workflows = {}
        
    async def orchestrate_task(self, task_description: str, context: Dict[str, Any]):
        """Orchestrate a complex task"""
        workflow_id = f"task_{datetime.utcnow().timestamp()}"
        
        # Decompose task into steps
        steps = self._decompose_task(task_description, context)
        
        # Create workflow
        workflow = {
            "id": workflow_id,
            "description": task_description,
            "steps": steps,
            "context": context,
            "status": "planning"
        }
        
        # Send workflow to bridge
        await self.client.execute_workflow(workflow_id, workflow)
        
        # Monitor workflow execution
        self.active_workflows[workflow_id] = workflow
        
        return workflow_id
        
    def _decompose_task(self, task: str, context: Dict[str, Any]) -> list:
        """Decompose task into atomic steps"""
        # This is a simplified example - in practice, this would use
        # AI to intelligently decompose the task
        steps = [
            {
                "id": "analyze",
                "type": "analysis",
                "description": f"Analyze requirements for: {task}",
                "dependencies": []
            },
            {
                "id": "plan",
                "type": "planning",
                "description": "Create execution plan",
                "dependencies": ["analyze"]
            },
            {
                "id": "execute",
                "type": "execution",
                "description": "Execute the plan",
                "dependencies": ["plan"]
            },
            {
                "id": "validate",
                "type": "validation",
                "description": "Validate results",
                "dependencies": ["execute"]
            }
        ]
        
        return steps
        
    async def collaborate_with_cursor(self, code_task: str, files: list):
        """Initiate collaboration with Cursor for code tasks"""
        event_data = {
            "task": code_task,
            "files": files,
            "requester": "manus",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.client.send_collaboration_event("code_assistance_request", event_data)
        
    async def query_knowledge_base(self, query: str):
        """Query the knowledge MCP server"""
        return await self.client.query_mcp_server("knowledge", {
            "query": query,
            "context": "manus_orchestration"
        })

async def main():
    """Example usage of Manus AI client"""
    
    # Configuration from environment or command line
    bridge_url = os.getenv("BRIDGE_URL", "ws://150.136.94.139:8765")
    api_key = os.getenv("MANUS_API_KEY", "manus_live_collab_2024")
    
    # Create client
    client = ManusAIClient(bridge_url, api_key)
    
    # Connect to bridge
    if await client.connect():
        # Create orchestrator
        orchestrator = ManusAIOrchestrator(client)
        
        # Example: Orchestrate a task
        workflow_id = await orchestrator.orchestrate_task(
            "Deploy the enhanced AI collaboration interface",
            {
                "target_server": "150.136.94.139",
                "components": ["websocket_bridge", "mcp_servers", "monitoring"]
            }
        )
        
        logger.info(f"Started workflow: {workflow_id}")
        
        # Example: Collaborate with Cursor
        await orchestrator.collaborate_with_cursor(
            "Optimize the WebSocket message handling",
            ["services/ai_collaboration/public_endpoint_bridge.py"]
        )
        
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
        logger.info("🛑 Manus AI client stopped")