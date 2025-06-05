#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging

class CursorLiveCollaborationClient:
    def __init__(self, server_ip="45.32.69.157", port=8765):
        self.websocket_url = f"ws://{server_ip}:{port}"
        self.websocket = None
        
    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            
            # Authenticate as Cursor AI
            auth_message = {
                "client": "cursor",
                "token": "cursor_live_collab_2024"
            }
            await self.websocket.send(json.dumps(auth_message))
            
            response = await self.websocket.recv()
            auth_response = json.loads(response)
            
            if auth_response.get("status") == "authenticated":
                print("💻 Cursor AI connected to live collaboration!")
                print(f"🎯 Goal: {auth_response.get('goal')}")
                return True
            else:
                print("❌ Authentication failed")
                return False
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def execute_command(self, command, working_dir="/var/www/cherry-ai"):
        if not self.websocket:
            return None
        
        try:
            message = {
                "type": "execute_command",
                "command": command,
                "working_dir": working_dir
            }
            
            await self.websocket.send(json.dumps(message))
            response = await self.websocket.recv()
            return json.loads(response)
            
        except Exception as e:
            print(f"❌ Error executing command: {e}")
            return None
    
    async def update_file(self, file_path, content):
        if not self.websocket:
            return False
        
        try:
            message = {
                "type": "file_change",
                "file_path": file_path,
                "content": content,
                "change_type": "modify"
            }
            
            await self.websocket.send(json.dumps(message))
            print(f"📝 File updated: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating file: {e}")
            return False
    
    async def listen_for_manus(self):
        if not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                data = json.loads(message)
                message_type = data.get("type")
                
                if message_type == "file_changed":
                    print(f"📝 Manus changed file: {data.get('file_path')}")
                elif message_type == "command_executed":
                    print(f"⚡ Manus executed: {data.get('command')}")
                elif message_type == "task_updated":
                    print(f"📋 Task updated: {data.get('task')}")
                    
        except Exception as e:
            print(f"❌ Error listening: {e}")

# Usage example
async def main():
    client = CursorLiveCollaborationClient()
    
    if await client.connect():
        print("\n🚀 Starting Live Collaboration Session...")
        print("="*50)
        
        # Goal 1: Check cherry-ai.me status
        print("\n📊 Checking cherry-ai.me status...")
        result = await client.execute_command("curl -I http://cherry-ai.me")
        if result:
            print(f"Status check result:\n{result.get('stdout', '')}")
        
        # Goal 2: Check current web directory
        print("\n📁 Checking web directory contents...")
        result = await client.execute_command("ls -la /var/www/html/")
        if result:
            print(f"Current web directory:\n{result.get('stdout', '')}")
        
        # Goal 3: Look for the enhanced interface
        print("\n🔍 Looking for enhanced interface...")
        result = await client.execute_command("ls -la /var/www/cherry-ai/admin-interface/")
        if result:
            print(f"Admin interface files:\n{result.get('stdout', '')}")
        
        # Goal 4: Deploy enhanced interface
        print("\n🚀 Deploying enhanced interface to cherry-ai.me...")
        result = await client.execute_command(
            "cp /var/www/cherry-ai/admin-interface/enhanced-production-interface.html /var/www/html/index.html"
        )
        if result and result.get('return_code') == 0:
            print("✅ Enhanced interface deployed!")
        else:
            print(f"❌ Deployment error: {result}")
        
        # Goal 5: Reload nginx
        print("\n🔄 Reloading nginx...")
        result = await client.execute_command("systemctl reload nginx")
        if result and result.get('return_code') == 0:
            print("✅ Nginx reloaded!")
        
        # Goal 6: Test the deployment
        print("\n🧪 Testing cherry-ai.me...")
        result = await client.execute_command("curl -s http://cherry-ai.me | head -20")
        if result:
            print(f"Cherry AI homepage (first 20 lines):\n{result.get('stdout', '')}")
        
        # Listen for Manus collaboration
        print("\n👂 Listening for Manus collaboration events...")
        print("Real-time sync active! Any changes Manus makes will appear here.")
        await client.listen_for_manus()

if __name__ == "__main__":
    asyncio.run(main()) 