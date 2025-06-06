#!/usr/bin/env python3
"""
Manus AI Client - Connect your Manus AI Coder to Cherry AI Bridge
Simple, lightweight client with full collaboration features
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime
from typing import Dict, List, Optional, Callable

class ManusAIClient:
    """
    Simple client for connecting Manus AI to Cherry AI Bridge
    
    Usage:
        client = ManusAIClient("cherry-ai.me")
        await client.connect()
        await client.send_code_change("file.py", "def hello(): print('world')")
    """
    
    def __init__(
        self, 
        bridge_host: str = "cherry-ai.me",
        bridge_port: int = 443,
        use_ssl: bool = True,
        api_key: str = "manus-key-2024",
        internal_mode: bool = False
    ):
        self.bridge_host = bridge_host
        self.bridge_port = bridge_port
        self.use_ssl = use_ssl
        self.api_key = api_key
        
        # Connection details
        protocol = "wss" if use_ssl else "ws"
        # External connections go through Nginx at /bridge/ws
        # Internal connections go directly to the service at /ws
        path = "/bridge/ws" if not internal_mode else "/ws"
        self.bridge_url = f"{protocol}://{bridge_host}:{bridge_port}{path}"
        
        self.websocket = None
        self.connected = False
        self.session_id = None
        self._connection_event = asyncio.Event()  # Event to signal connection is ready
        
        # Capabilities - what your Manus AI can do
        self.capabilities = [
            "deployment",
            "infrastructure", 
            "debugging",
            "production",
            "server-management",
            "devops",
            "monitoring"
        ]
        
        # Message handlers
        self.message_handlers = {
            "connected": self._handle_connected,
            "ai_joined": self._handle_ai_joined,
            "ai_disconnected": self._handle_ai_disconnected,
            "code_change": self._handle_code_change,
            "help_request": self._handle_help_request,
            "broadcast": self._handle_broadcast,
            "error": self._handle_error
        }
        
        # User-defined handlers
        self.on_code_change: Optional[Callable] = None
        self.on_help_request: Optional[Callable] = None
        self.on_ai_joined: Optional[Callable] = None
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("manus-ai-client")
    
    async def connect(self):
        """Connect to the Cherry AI Bridge"""
        try:
            self.logger.info(f"🔗 Connecting to Cherry AI Bridge at {self.bridge_url}")
            self._connection_event.clear()
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(self.bridge_url)
            
            # Send authentication
            auth_message = {
                "ai_name": "manus-ai",
                "api_key": self.api_key,
                "capabilities": self.capabilities
            }
            
            await self.websocket.send(json.dumps(auth_message))
            self.logger.info("🔐 Authentication sent, waiting for confirmation...")
            
            # Start message handler
            asyncio.create_task(self._message_handler_loop())
            
            # Wait for the connection to be confirmed by the server
            await asyncio.wait_for(self._connection_event.wait(), timeout=10)
            
            self.logger.info("✅ Connected to Cherry AI Bridge!")
            
        except Exception as e:
            self.logger.error(f"❌ Connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from the bridge"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            self.logger.info("🔌 Disconnected from Cherry AI Bridge")
    
    async def send_code_change(self, file_path: str, content: str, change_type: str = "modified"):
        """Send a code change notification to other AIs"""
        message = {
            "type": "code_change",
            "file_path": file_path,
            "content": content,
            "change_type": change_type,  # "created", "modified", "deleted"
            "timestamp": datetime.now().isoformat(),
            "ai_name": "manus-ai"
        }
        
        await self._send_message(message)
        self.logger.info(f"📝 Sent code change: {file_path}")
    
    async def request_help(self, request: str, capabilities_needed: List[str] = None):
        """Request help from other AIs with specific capabilities"""
        message = {
            "type": "request_help",
            "request": request,
            "capabilities": capabilities_needed or [],
            "timestamp": datetime.now().isoformat()
        }
        
        await self._send_message(message)
        self.logger.info(f"🆘 Requested help: {request}")
    
    async def broadcast_message(self, message: str, data: Dict = None):
        """Broadcast a message to all connected AIs"""
        broadcast_msg = {
            "type": "broadcast",
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        }
        
        await self._send_message(broadcast_msg)
        self.logger.info(f"📢 Broadcast: {message}")
    
    async def send_deployment_status(self, status: str, details: Dict = None):
        """Send deployment status update"""
        message = {
            "type": "deployment_status",
            "status": status,  # "starting", "in_progress", "completed", "failed"
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
        await self._send_message(message)
        self.logger.info(f"🚀 Deployment status: {status}")
    
    async def send_infrastructure_update(self, component: str, status: str, metrics: Dict = None):
        """Send infrastructure component update"""
        message = {
            "type": "infrastructure_update",
            "component": component,
            "status": status,
            "metrics": metrics or {},
            "timestamp": datetime.now().isoformat()
        }
        
        await self._send_message(message)
        self.logger.info(f"🏗️ Infrastructure update: {component} - {status}")
    
    async def ping(self):
        """Send ping to keep connection alive"""
        await self._send_message({"type": "ping"})
    
    async def _send_message(self, message: Dict):
        """Send a message to the bridge"""
        if not self.websocket or not self.connected:
            self.logger.error("❌ Not connected to bridge")
            return
        
        try:
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            self.logger.error(f"❌ Failed to send message: {e}")
    
    async def _message_handler_loop(self):
        """Handle incoming messages from the bridge"""
        try:
            async for message_raw in self.websocket:
                try:
                    message = json.loads(message_raw)
                    message_type = message.get("type")
                    
                    # Handle message with registered handler
                    if message_type in self.message_handlers:
                        await self.message_handlers[message_type](message)
                    else:
                        self.logger.info(f"📨 Unhandled message type: {message_type}")
                        
                except json.JSONDecodeError:
                    self.logger.error("❌ Invalid JSON received")
                except Exception as e:
                    self.logger.error(f"❌ Message handling error: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.info("🔌 Connection closed by server")
            self.connected = False
        except Exception as e:
            self.logger.error(f"❌ Message loop error: {e}")
            self.connected = False
    
    # Message handlers
    async def _handle_connected(self, message: Dict):
        """Handle connection confirmation"""
        self.connected = True
        self.session_id = message.get("session_id")
        bridge_info = message.get("bridge_info", {})
        
        self.logger.info(f"✅ Connection Confirmed! Bridge version: {bridge_info.get('version')}")
        self.logger.info(f"🤖 Other AIs connected: {bridge_info.get('connected_ais', [])}")
        
        # Signal that the connection is fully established
        self._connection_event.set()
    
    async def _handle_ai_joined(self, message: Dict):
        """Handle when another AI joins"""
        ai_name = message.get("ai_name")
        capabilities = message.get("capabilities", [])
        
        self.logger.info(f"👋 {ai_name} joined with capabilities: {capabilities}")
        
        if self.on_ai_joined:
            await self.on_ai_joined(ai_name, capabilities)
    
    async def _handle_ai_disconnected(self, message: Dict):
        """Handle when another AI disconnects"""
        ai_name = message.get("ai_name")
        self.logger.info(f"👋 {ai_name} disconnected")
    
    async def _handle_code_change(self, message: Dict):
        """Handle code change from another AI"""
        sender = message.get("sender")
        data = message.get("data", {})
        file_path = data.get("file_path")
        content = data.get("content")
        change_type = data.get("change_type")
        
        self.logger.info(f"📝 Code change from {sender}: {file_path} ({change_type})")
        
        if self.on_code_change:
            await self.on_code_change(sender, file_path, content, change_type)
    
    async def _handle_help_request(self, message: Dict):
        """Handle help request from another AI"""
        requester = message.get("requester")
        request = message.get("request")
        capabilities_needed = message.get("capabilities_needed", [])
        
        # Check if we can help (if we have any of the needed capabilities)
        can_help = any(cap in self.capabilities for cap in capabilities_needed)
        
        if can_help:
            self.logger.info(f"🆘 Help request from {requester}: {request}")
            
            if self.on_help_request:
                await self.on_help_request(requester, request, capabilities_needed)
        else:
            self.logger.debug(f"🤔 Can't help with request from {requester} (capabilities mismatch)")
    
    async def _handle_broadcast(self, message: Dict):
        """Handle broadcast message"""
        sender = message.get("sender")
        msg = message.get("message")
        data = message.get("data", {})
        
        self.logger.info(f"📢 Broadcast from {sender}: {msg}")
    
    async def _handle_error(self, message: Dict):
        """Handle error message"""
        error = message.get("message", "Unknown error")
        self.logger.error(f"❌ Bridge error: {error}")

# Example usage
async def example_usage():
    """Example of how to use the Manus AI Client"""
    
    # Create client
    client = ManusAIClient("cherry-ai.me")
    
    # Set up event handlers
    async def on_code_change(sender, file_path, content, change_type):
        print(f"Code changed by {sender}: {file_path} ({change_type})")
        # Your Manus AI can react to code changes here
    
    async def on_help_request(requester, request, capabilities_needed):
        print(f"Help request from {requester}: {request}")
        # Your Manus AI can provide help here
        
        # Example: automatically respond to deployment help requests
        if "deployment" in capabilities_needed:
            await client.broadcast_message(
                f"@{requester} I can help with deployment! Let me check the current status..."
            )
    
    client.on_code_change = on_code_change
    client.on_help_request = on_help_request
    
    try:
        # Connect
        await client.connect()
        
        # Send a deployment status update
        await client.send_deployment_status("completed", {
            "services": ["api", "database", "bridge"],
            "uptime": "100%",
            "last_deployment": datetime.now().isoformat()
        })
        
        # Keep alive
        while True:
            await client.ping()
            await asyncio.sleep(30)
            
    except KeyboardInterrupt:
        print("\n👋 Disconnecting...")
        await client.disconnect()

if __name__ == "__main__":
    # Run the example
    asyncio.run(example_usage()) 