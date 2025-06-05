#!/usr/bin/env python3
"""
Cursor AI Collaboration Session
Connects to Cherry AI production WebSocket for live sync with Manus
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime

class CursorCollabSession:
    def __init__(self, server_ip="150.136.94.139", port=8765):
        self.uri = f"ws://{server_ip}:{port}"
        self.websocket = None
        
    async def connect(self):
        print(f"🚀 Starting Cursor AI Collaboration Session")
        print(f"📡 Connecting to: {self.uri}")
        
        try:
            self.websocket = await websockets.connect(self.uri)
            print("✅ Connected to Cherry AI production server!")
            
            # Authenticate
            auth_msg = {
                "type": "auth",
                "client": "cursor",
                "token": "cursor_live_collab_2024"
            }
            await self.websocket.send(json.dumps(auth_msg))
            
            # Get response
            response = await self.websocket.recv()
            auth_data = json.loads(response)
            print(f"✅ Authenticated: {auth_data['message']}")
            
            # Get initial state
            state_response = await self.websocket.recv()
            state_data = json.loads(state_response)
            
            print("\n📋 Current Status:")
            print(f"   Task: {state_data['shared_state']['current_task']}")
            print(f"   Production: {state_data['shared_state']['context']['production_server']}")
            print(f"   Database: {state_data['shared_state']['context']['database_server']}")
            print(f"   Domain: {state_data['shared_state']['context']['domain']}")
            
            print("\n🎯 Priorities:")
            for i, priority in enumerate(state_data['shared_state']['priorities'], 1):
                print(f"   {i}. {priority}")
            
            print("\n⚠️  Issues Found:")
            server_info = state_data['server_info']
            if not server_info['cherry_ai_status']['enhanced_interface_exists']:
                print("   ❌ Enhanced interface missing")
            if not server_info['cherry_ai_status']['domain_accessible']:
                print("   ❌ Domain not accessible")
                
            print(f"\n💬 Manus connected: {'✅' if state_data['connected_clients']['manus'] else '❌'}")
            print("\n⏳ Waiting for commands... (Ctrl+C to exit)")
            
            # Listen for messages
            async for message in self.websocket:
                data = json.loads(message)
                self.handle_message(data)
                
        except KeyboardInterrupt:
            print("\n👋 Closing collaboration session...")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            if self.websocket:
                await self.websocket.close()
    
    def handle_message(self, data):
        msg_type = data.get('type', '')
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if msg_type == 'command':
            print(f"\n[{timestamp}] 🔧 Command from {data.get('from', 'unknown')}: {data.get('command', '')}")
            if 'result' in data:
                print(f"   Result: {data['result']}")
        elif msg_type == 'file_update':
            print(f"\n[{timestamp}] 📝 File update: {data.get('file', '')}")
        elif msg_type == 'chat':
            print(f"\n[{timestamp}] 💬 {data.get('from', 'unknown')}: {data.get('message', '')}")
        elif msg_type == 'status_update':
            print(f"\n[{timestamp}] 📊 Status: {data.get('status', '')}")
        else:
            print(f"\n[{timestamp}] 📨 {msg_type}: {json.dumps(data, indent=2)}")

async def main():
    session = CursorCollabSession()
    await session.connect()

if __name__ == "__main__":
    asyncio.run(main()) 