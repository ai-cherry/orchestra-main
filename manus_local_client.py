#!/usr/bin/env python3
"""
Manus Local Collaboration Client
Connects Manus to the local collaboration bridge for live development
"""

import asyncio
import websockets
import json
import subprocess
import os
from datetime import datetime

class ManusCollaborationClient:
    def __init__(self, bridge_url="ws://localhost:8765"):
        self.bridge_url = bridge_url
        self.websocket = None
        self.client_id = None
        
    async def connect(self):
        """Connect to the collaboration bridge"""
        try:
            print(f"🔗 Manus connecting to {self.bridge_url}...")
            self.websocket = await websockets.connect(self.bridge_url)
            
            # Authenticate as Manus
            auth_message = {
                "client": "manus",
                "token": "manus_live_collab_2024",
                "capabilities": [
                    "infrastructure_management",
                    "server_deployment", 
                    "api_integration",
                    "production_fixes"
                ]
            }
            
            await self.websocket.send(json.dumps(auth_message))
            
            # Wait for welcome message
            welcome = await self.websocket.recv()
            welcome_data = json.loads(welcome)
            self.client_id = welcome_data.get("client_id")
            
            print(f"✅ Manus connected as: {self.client_id}")
            print(f"📋 Current task: {welcome_data['shared_state']['current_task']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    async def send_command(self, command, working_dir="/home/ubuntu/orchestra-main-2"):
        """Send a command to be executed"""
        if not self.websocket:
            print("❌ Not connected to bridge")
            return
            
        message = {
            "type": "command",
            "command": command,
            "working_dir": working_dir,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket.send(json.dumps(message))
        print(f"📤 Sent command: {command}")
    
    async def edit_file(self, file_path, content, operation="write"):
        """Edit a file through the collaboration bridge"""
        if not self.websocket:
            print("❌ Not connected to bridge")
            return
            
        message = {
            "type": "file_edit",
            "file_path": file_path,
            "content": content,
            "operation": operation,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket.send(json.dumps(message))
        print(f"📝 Editing file: {file_path}")
    
    async def send_chat(self, message):
        """Send a chat message to other clients"""
        if not self.websocket:
            print("❌ Not connected to bridge")
            return
            
        chat_message = {
            "type": "chat",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket.send(json.dumps(chat_message))
        print(f"💬 Sent: {message}")
    
    async def update_priorities(self, new_priorities):
        """Update shared priorities"""
        if not self.websocket:
            print("❌ Not connected to bridge")
            return
            
        message = {
            "type": "status_update",
            "updates": {
                "priorities": new_priorities,
                "last_updated_by": "manus",
                "last_updated_at": datetime.now().isoformat()
            }
        }
        
        await self.websocket.send(json.dumps(message))
        print(f"📋 Updated priorities")
    
    async def listen_for_messages(self):
        """Listen for messages from the collaboration bridge"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
                
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection to bridge closed")
        except Exception as e:
            print(f"🚨 Error listening for messages: {e}")
    
    async def handle_message(self, data):
        """Handle incoming messages from the bridge"""
        message_type = data.get("type")
        
        if message_type == "command_result":
            await self.handle_command_result(data)
        elif message_type == "file_edit_result":
            await self.handle_file_edit_result(data)
        elif message_type == "chat":
            await self.handle_chat(data)
        elif message_type == "state_updated":
            await self.handle_state_update(data)
    
    async def handle_command_result(self, data):
        """Handle command execution results"""
        client_id = data.get("client_id", "unknown")
        command = data.get("command", "")
        stdout = data.get("stdout", "")
        stderr = data.get("stderr", "")
        return_code = data.get("return_code", -1)
        
        if client_id != self.client_id:  # Only show results from other clients
            print(f"\n📊 Command result from {client_id}:")
            print(f"   Command: {command}")
            if stdout:
                print(f"   Output: {stdout[:200]}...")
            if stderr:
                print(f"   Error: {stderr[:200]}...")
            print(f"   Return code: {return_code}")
    
    async def handle_file_edit_result(self, data):
        """Handle file edit results"""
        client_id = data.get("client_id", "unknown")
        file_path = data.get("file_path", "")
        operation = data.get("operation", "")
        success = data.get("success", False)
        
        if client_id != self.client_id:
            status = "✅" if success else "❌"
            print(f"\n📝 {status} File {operation} by {client_id}: {file_path}")
    
    async def handle_chat(self, data):
        """Handle chat messages"""
        from_client = data.get("from", "unknown")
        message = data.get("message", "")
        timestamp = data.get("timestamp", "")
        
        print(f"\n💬 {from_client.upper()}: {message}")
    
    async def handle_state_update(self, data):
        """Handle shared state updates"""
        shared_state = data.get("shared_state", {})
        print(f"\n📋 Shared state updated:")
        print(f"   Task: {shared_state.get('current_task', 'Unknown')}")
        priorities = shared_state.get("priorities", [])
        for i, priority in enumerate(priorities, 1):
            print(f"   {i}. {priority}")

async def main():
    """Main function for Manus collaboration client"""
    client = ManusCollaborationClient()
    
    # Connect to bridge
    if not await client.connect():
        return
    
    # Send initial status
    await client.send_chat("🤖 Manus is online and ready for collaboration!")
    
    # Update priorities with current focus
    await client.update_priorities([
        "Fix SSH access to production servers (45.32.69.157, 45.77.87.106)",
        "Deploy nginx configuration and restart web services",
        "Upload and deploy enhanced Cherry AI interface",
        "Test cherry-ai.me with three AI personas working",
        "Establish production live collaboration bridge"
    ])
    
    # Example: Deploy server fix script
    await client.send_chat("📋 Deploying server fix script to resolve SSH and nginx issues...")
    
    # Listen for messages (this will run forever)
    await client.listen_for_messages()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Manus collaboration client stopped")
    except Exception as e:
        print(f"🚨 Error: {e}")

