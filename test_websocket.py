#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_connection():
    uri = "ws://150.136.94.139:8765"
    print(f"🔌 Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected! Sending authentication...")
            
            # Send authentication
            auth_msg = {
                "type": "auth",
                "client": "cursor",
                "token": "cursor_live_collab_2024"
            }
            await websocket.send(json.dumps(auth_msg))
            print(f"📤 Sent: {auth_msg}")
            
            # Wait for response
            response = await websocket.recv()
            print(f"📥 Received: {response}")
            
            # Send a test message
            test_msg = {
                "type": "status",
                "message": "Hello from Cursor!"
            }
            await websocket.send(json.dumps(test_msg))
            print(f"📤 Sent: {test_msg}")
            
            # Wait for response
            response = await websocket.recv()
            print(f"📥 Received: {response}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection()) 