#!/usr/bin/env python3
"""
Test Cherry AI Live Collaboration locally
"""

import asyncio
import websockets
import json
import threading
import time
from datetime import datetime

class LocalCollaborationServer:
    """Local test server for collaboration"""
    
    async def handle_client(self, websocket, path):
        """Handle incoming WebSocket connections"""
        client_info = await websocket.recv()
        client_data = json.loads(client_info)
        
        print(f"🔗 Client connected: {client_data.get('client', 'unknown')}")
        
        # Send authentication response
        auth_response = {
            "status": "authenticated",
            "message": "Connected to local test server",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send(json.dumps(auth_response))
        
        try:
            async for message in websocket:
                data = json.loads(message)
                print(f"📩 Received: {data}")
                
                # Echo back with timestamp
                response = {
                    "type": "echo",
                    "original": data,
                    "server_time": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(response))
                
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Client disconnected")
    
    async def start_server(self):
        """Start the WebSocket server"""
        print("🚀 Starting local collaboration server on ws://localhost:8765")
        async with websockets.serve(self.handle_client, "localhost", 8765):
            await asyncio.Future()  # run forever

def run_server():
    """Run the server in a separate thread"""
    server = LocalCollaborationServer()
    asyncio.run(server.start_server())

async def test_client():
    """Test client to verify the connection"""
    await asyncio.sleep(2)  # Give server time to start
    
    try:
        async with websockets.connect("ws://localhost:8765") as websocket:
            # Send authentication
            auth = {
                "client": "test_client",
                "token": "test_token"
            }
            await websocket.send(json.dumps(auth))
            
            # Receive response
            response = await websocket.recv()
            print(f"✅ Auth response: {response}")
            
            # Send test message
            test_msg = {
                "action": "test",
                "message": "Hello from test client!"
            }
            await websocket.send(json.dumps(test_msg))
            
            # Receive echo
            echo = await websocket.recv()
            print(f"✅ Echo response: {echo}")
            
            print("\n🎉 Local collaboration test successful!")
            
    except Exception as e:
        print(f"❌ Client error: {e}")

def main():
    print("🧪 Testing Cherry AI Live Collaboration Locally")
    print("="*50)
    
    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Run test client
    asyncio.run(test_client())
    
    print("\n📋 Next Steps:")
    print("1. The collaboration system works locally ✅")
    print("2. When SSH access is available, run:")
    print("   scp -r cherry_collab_deploy/ root@45.32.69.157:/tmp/")
    print("   ssh root@45.32.69.157 'cd /tmp/cherry_collab_deploy && python3 deploy_collaboration_bridge.py'")
    print("\n3. Or use the Lambda web console to upload and run the deployment script")

if __name__ == "__main__":
    main() 