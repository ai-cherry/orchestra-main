#!/usr/bin/env python3
"""
Enhanced Cursor AI Live Collaboration Client
Includes offline mode for testing and better error handling
"""

import asyncio
import websockets
import json
import logging
import sys
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedCursorLiveClient:
    def __init__(self, server_ip="45.32.69.157", port=8765, offline_mode=False):
        self.server_ip = server_ip
        self.port = port
        self.websocket_url = f"ws://{server_ip}:{port}"
        self.websocket = None
        self.offline_mode = offline_mode
        
    async def connect(self):
        if self.offline_mode:
            print("🔧 Running in OFFLINE MODE - Simulating connection")
            print("💻 Cursor AI connected to live collaboration (simulated)!")
            print("🎯 Goal: Fix cherry-ai.me deployment and test AI personas")
            return True
            
        print(f"🔌 Attempting to connect to {self.websocket_url}...")
        
        try:
            # Try connection with timeout
            self.websocket = await asyncio.wait_for(
                websockets.connect(self.websocket_url),
                timeout=10.0
            )
            
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
                
        except asyncio.TimeoutError:
            print("⏱️ Connection timeout - server may be offline")
            print("\n🔧 TIP: The collaboration server may need to be deployed first.")
            print("📍 Server should be at: 45.32.69.157:8765")
            return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print(f"\n💡 Possible issues:")
            print("  1. Server not running at 45.32.69.157:8765")
            print("  2. Firewall blocking port 8765")
            print("  3. Network connectivity issues")
            return False
    
    async def execute_command(self, command, working_dir="/var/www/cherry-ai"):
        if self.offline_mode:
            print(f"\n[OFFLINE] Would execute: {command}")
            print(f"[OFFLINE] In directory: {working_dir}")
            return {"stdout": "[Simulated output]", "return_code": 0}
            
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
            logger.error(f"Error executing command: {e}")
            return None
    
    async def check_server_status(self):
        """Check if the server is reachable"""
        import socket
        
        print(f"\n🔍 Checking server status at {self.server_ip}:{self.port}...")
        
        try:
            # Check if host is reachable
            socket.setdefaulttimeout(5)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((self.server_ip, self.port))
            print("✅ Server is reachable!")
            return True
        except socket.timeout:
            print("⏱️ Connection timed out")
            return False
        except socket.error as e:
            print(f"❌ Cannot reach server: {e}")
            return False

async def main():
    # Check command line arguments
    offline_mode = "--offline" in sys.argv
    
    print("🚀 Cherry AI Live Collaboration Client")
    print("="*50)
    
    client = EnhancedCursorLiveClient(offline_mode=offline_mode)
    
    # First check if server is reachable
    if not offline_mode:
        await client.check_server_status()
    
    if await client.connect():
        print("\n📋 Live Collaboration Session Started")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)
        
        # Execute deployment tasks
        tasks = [
            ("Check cherry-ai.me status", "curl -I http://cherry-ai.me"),
            ("List web directory", "ls -la /var/www/html/"),
            ("Find enhanced interface", "find /var/www/cherry-ai -name '*enhanced*.html' -type f"),
            ("Deploy interface", "cp /var/www/cherry-ai/admin-interface/enhanced-production-interface.html /var/www/html/index.html"),
            ("Reload nginx", "systemctl reload nginx"),
            ("Verify deployment", "curl -s http://cherry-ai.me | grep -E 'Cherry|Sophia|Karen'")
        ]
        
        for task_name, command in tasks:
            print(f"\n📌 {task_name}...")
            result = await client.execute_command(command)
            if result:
                print(f"Result: {result.get('stdout', '')[:200]}...")
                if result.get('return_code') == 0:
                    print("✅ Success")
                else:
                    print(f"⚠️ Return code: {result.get('return_code')}")
        
        if not offline_mode:
            print("\n👂 Listening for real-time collaboration events...")
            print("Press Ctrl+C to exit")
            # Would listen for events here
            
    else:
        print("\n💡 To test locally, run with: python cursor_live_client_enhanced.py --offline")
        print("📚 Or deploy the server first using cherry_ai_live_collaboration_bridge.py")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Collaboration session ended") 