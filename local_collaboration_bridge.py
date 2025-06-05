#!/usr/bin/env python3
"""
Local Cherry AI Collaboration Bridge
Run this on your local machine to enable live collaboration with Manus
"""

import asyncio
import websockets
import json
import subprocess
import os
import sys
from datetime import datetime

class LocalCollaborationBridge:
    def __init__(self):
        self.clients = {}
        self.shared_state = {
            "current_task": "Fix cherry-ai.me deployment",
            "priorities": [
                "Get nginx running on production servers",
                "Deploy enhanced interface to cherry-ai.me", 
                "Test live collaboration between Manus and Cursor",
                "Verify three AI personas are working"
            ],
            "server_status": {
                "web_server": "45.32.69.157 - SSH timeout, nginx down",
                "database_server": "45.77.87.106 - SSH timeout"
            }
        }
        
    async def handle_client(self, websocket, path):
        """Handle new client connections"""
        try:
            # Wait for authentication
            auth_message = await websocket.recv()
            auth_data = json.loads(auth_message)
            
            client_type = auth_data.get("client", "unknown")
            client_id = f"{client_type}_{datetime.now().strftime('%H%M%S')}"
            
            self.clients[client_id] = {
                "websocket": websocket,
                "type": client_type,
                "connected_at": datetime.now()
            }
            
            print(f"✅ {client_type.upper()} connected: {client_id}")
            
            # Send welcome message with current state
            await websocket.send(json.dumps({
                "type": "welcome",
                "client_id": client_id,
                "shared_state": self.shared_state,
                "message": f"Connected to Cherry AI Local Collaboration Bridge"
            }))
            
            # Handle messages from this client
            async for message in websocket:
                await self.handle_message(client_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            if client_id in self.clients:
                print(f"❌ {self.clients[client_id]['type'].upper()} disconnected: {client_id}")
                del self.clients[client_id]
        except Exception as e:
            print(f"🚨 Error handling client: {e}")
    
    async def handle_message(self, client_id, message):
        """Handle messages from clients"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "command":
                await self.execute_command(client_id, data)
            elif message_type == "file_edit":
                await self.handle_file_edit(client_id, data)
            elif message_type == "status_update":
                await self.update_shared_state(client_id, data)
            elif message_type == "chat":
                await self.broadcast_chat(client_id, data)
                
        except Exception as e:
            print(f"🚨 Error handling message: {e}")
    
    async def execute_command(self, client_id, data):
        """Execute shell commands and broadcast results"""
        command = data.get("command", "")
        working_dir = data.get("working_dir", "/home/ubuntu/orchestra-main-2")
        
        print(f"🔧 {self.clients[client_id]['type'].upper()} executing: {command}")
        
        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            response = {
                "type": "command_result",
                "client_id": client_id,
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast to all clients
            await self.broadcast_to_all(response)
            
        except subprocess.TimeoutExpired:
            await self.broadcast_to_all({
                "type": "command_result",
                "client_id": client_id,
                "command": command,
                "error": "Command timed out after 30 seconds",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            await self.broadcast_to_all({
                "type": "command_result", 
                "client_id": client_id,
                "command": command,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def handle_file_edit(self, client_id, data):
        """Handle file editing operations"""
        file_path = data.get("file_path")
        content = data.get("content")
        operation = data.get("operation", "write")  # write, append, read
        
        print(f"📝 {self.clients[client_id]['type'].upper()} editing: {file_path}")
        
        try:
            if operation == "write":
                with open(file_path, 'w') as f:
                    f.write(content)
            elif operation == "append":
                with open(file_path, 'a') as f:
                    f.write(content)
            elif operation == "read":
                with open(file_path, 'r') as f:
                    content = f.read()
            
            response = {
                "type": "file_edit_result",
                "client_id": client_id,
                "file_path": file_path,
                "operation": operation,
                "success": True,
                "content": content if operation == "read" else None,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.broadcast_to_all(response)
            
        except Exception as e:
            await self.broadcast_to_all({
                "type": "file_edit_result",
                "client_id": client_id,
                "file_path": file_path,
                "operation": operation,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def update_shared_state(self, client_id, data):
        """Update shared collaboration state"""
        updates = data.get("updates", {})
        self.shared_state.update(updates)
        
        response = {
            "type": "state_updated",
            "client_id": client_id,
            "shared_state": self.shared_state,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_all(response)
    
    async def broadcast_chat(self, client_id, data):
        """Broadcast chat messages between clients"""
        message = data.get("message", "")
        client_type = self.clients[client_id]['type']
        
        response = {
            "type": "chat",
            "from": client_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_all(response)
    
    async def broadcast_to_all(self, message):
        """Broadcast message to all connected clients"""
        if not self.clients:
            return
            
        message_json = json.dumps(message)
        disconnected_clients = []
        
        for client_id, client_info in self.clients.items():
            try:
                await client_info["websocket"].send(message_json)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            del self.clients[client_id]
    
    async def start_server(self, host="localhost", port=8765):
        """Start the collaboration bridge server"""
        print(f"🚀 Starting Cherry AI Local Collaboration Bridge...")
        print(f"📡 Server: ws://{host}:{port}")
        print(f"🎯 Current task: {self.shared_state['current_task']}")
        print(f"📋 Priorities:")
        for i, priority in enumerate(self.shared_state['priorities'], 1):
            print(f"   {i}. {priority}")
        print(f"\n⏳ Waiting for Cursor AI and Manus to connect...")
        
        async with websockets.serve(self.handle_client, host, port):
            await asyncio.Future()  # Run forever

def main():
    """Main function to start the collaboration bridge"""
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 8765
    
    bridge = LocalCollaborationBridge()
    
    try:
        asyncio.run(bridge.start_server(port=port))
    except KeyboardInterrupt:
        print("\n🛑 Collaboration bridge stopped by user")
    except Exception as e:
        print(f"🚨 Error starting collaboration bridge: {e}")

if __name__ == "__main__":
    main()

