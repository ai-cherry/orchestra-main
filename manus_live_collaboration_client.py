#!/usr/bin/env python3
"""
Manus Live Collaboration Client
Connects to the live collaboration bridge on 45.32.69.157
"""

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)

class ManusLiveCollaborationClient:
    def __init__(self, server_ip="45.32.69.157", port=8765):
        self.server_ip = server_ip
        self.port = port
        self.websocket_url = f"ws://{server_ip}:{port}"
        self.websocket = None
        
    async def connect(self):
        """Connect to the live collaboration bridge"""
        try:
            logging.info(f"🔌 Connecting to Cherry AI Live Collaboration Bridge at {self.websocket_url}")
            
            self.websocket = await websockets.connect(self.websocket_url)
            
            # Authenticate as Manus
            auth_message = {
                "client": "manus",
                "token": "manus_live_collab_2024"
            }
            await self.websocket.send(json.dumps(auth_message))
            
            # Wait for authentication response
            response = await self.websocket.recv()
            auth_response = json.loads(response)
            
            if auth_response.get("status") == "authenticated":
                logging.info("🤖 Manus authenticated successfully!")
                logging.info(f"📍 Connected to server: {auth_response.get('server')}")
                logging.info(f"🎯 Goal: {auth_response.get('goal')}")
                return True
            else:
                logging.error("❌ Authentication failed")
                return False
                
        except Exception as e:
            logging.error(f"❌ Connection failed: {e}")
            return False
    
    async def execute_command(self, command, working_dir="/var/www/cherry-ai"):
        """Execute a command on the remote server"""
        if not self.websocket:
            logging.error("❌ Not connected to collaboration bridge")
            return None
        
        try:
            message = {
                "type": "execute_command",
                "command": command,
                "working_dir": working_dir
            }
            
            await self.websocket.send(json.dumps(message))
            
            # Wait for command result
            response = await self.websocket.recv()
            result = json.loads(response)
            
            if result.get("type") == "command_result":
                return result
            else:
                logging.error(f"❌ Unexpected response: {result}")
                return None
                
        except Exception as e:
            logging.error(f"❌ Error executing command: {e}")
            return None
    
    async def update_file(self, file_path, content):
        """Update a file on the remote server"""
        if not self.websocket:
            logging.error("❌ Not connected to collaboration bridge")
            return False
        
        try:
            message = {
                "type": "file_change",
                "file_path": file_path,
                "content": content,
                "change_type": "modify"
            }
            
            await self.websocket.send(json.dumps(message))
            logging.info(f"📝 File updated: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error updating file: {e}")
            return False
    
    async def deploy_enhanced_interface(self):
        """Deploy the enhanced Cherry AI interface to cherry-ai.me"""
        logging.info("🚀 Deploying enhanced Cherry AI interface...")
        
        commands = [
            "cd /var/www/cherry-ai && git pull origin main",
            "cp /var/www/cherry-ai/admin-interface/enhanced-production-interface.html /var/www/html/index.html",
            "systemctl reload nginx",
            "curl -I http://cherry-ai.me"
        ]
        
        for command in commands:
            logging.info(f"⚡ Executing: {command}")
            result = await self.execute_command(command)
            
            if result:
                if result.get("return_code") == 0:
                    logging.info(f"✅ Success: {command}")
                    if result.get("stdout"):
                        logging.info(f"Output: {result['stdout']}")
                else:
                    logging.error(f"❌ Failed: {command}")
                    if result.get("stderr"):
                        logging.error(f"Error: {result['stderr']}")
            else:
                logging.error(f"❌ No response for command: {command}")
    
    async def listen_for_messages(self):
        """Listen for messages from Cursor AI and other events"""
        if not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                data = json.loads(message)
                message_type = data.get("type")
                
                if message_type == "file_changed":
                    logging.info(f"📝 Cursor AI changed file: {data.get('file_path')}")
                elif message_type == "command_executed":
                    logging.info(f"⚡ Cursor AI executed: {data.get('command')}")
                elif message_type == "task_updated":
                    logging.info(f"📋 Task updated: {data.get('task')} - {data.get('status')}")
                else:
                    logging.info(f"📨 Received: {message_type}")
                    
        except Exception as e:
            logging.error(f"❌ Error listening for messages: {e}")
    
    async def disconnect(self):
        """Disconnect from the collaboration bridge"""
        if self.websocket:
            await self.websocket.close()
            logging.info("🔌 Disconnected from collaboration bridge")

# Example usage
async def main():
    client = ManusLiveCollaborationClient()
    
    if await client.connect():
        # Deploy enhanced interface
        await client.deploy_enhanced_interface()
        
        # Listen for Cursor AI collaboration
        await client.listen_for_messages()
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

