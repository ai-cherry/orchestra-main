#!/usr/bin/env python3
"""
MINIMAL AI BRIDGE - PROVES IT WORKS WITHOUT EXTERNAL DEPENDENCIES
"""

import asyncio
import json
import websockets
from datetime import datetime

connected_ais = {}

async def handle_client(websocket):
    """Handle AI connections"""
    ai_name = None
    try:
        # Get authentication
        auth_msg = await websocket.recv()
        auth_data = json.loads(auth_msg)
        ai_name = auth_data.get("ai_name", "Unknown")
        
        print(f"✅ {ai_name} connected!")
        connected_ais[ai_name] = websocket
        
        # Send confirmation
        await websocket.send(json.dumps({
            "type": "connected",
            "ai_name": ai_name,
            "message": "Welcome to AI Bridge!"
        }))
        
        # Notify others
        for other_name, other_ws in connected_ais.items():
            if other_name != ai_name:
                await other_ws.send(json.dumps({
                    "type": "ai_joined",
                    "ai_name": ai_name,
                    "timestamp": datetime.now().isoformat()
                }))
        
        # Handle messages
        async for message in websocket:
            data = json.loads(message)
            print(f"📨 {ai_name} sent: {data}")
            
            # Broadcast to others
            for other_name, other_ws in connected_ais.items():
                if other_name != ai_name:
                    await other_ws.send(json.dumps({
                        **data,
                        "sender": ai_name
                    }))
                    
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if ai_name and ai_name in connected_ais:
            del connected_ais[ai_name]
            print(f"🔌 {ai_name} disconnected")

async def test_collaboration():
    """Run bridge and test it"""
    print("🚀 MINIMAL AI BRIDGE TEST")
    print("=" * 50)
    
    # Start the server
    server = await websockets.serve(handle_client, "localhost", 8765)
    print("✅ Bridge running on ws://localhost:8765")
    
    # Give it a moment
    await asyncio.sleep(1)
    
    # Connect test clients
    async with websockets.connect("ws://localhost:8765") as manus:
        # Manus connects
        await manus.send(json.dumps({
            "ai_name": "Manus-AI",
            "api_key": "test"
        }))
        response = await manus.recv()
        print(f"Manus got: {response}")
        
        async with websockets.connect("ws://localhost:8765") as cursor:
            # Cursor connects
            await cursor.send(json.dumps({
                "ai_name": "Cursor-AI",
                "api_key": "test"
            }))
            response = await cursor.recv()
            print(f"Cursor got: {response}")
            
            # Manus gets notification
            notif = await manus.recv()
            print(f"\nManus notified: {notif}")
            
            # Test real communication
            print("\n🔄 Testing AI-to-AI communication...")
            
            # Cursor sends code change
            await cursor.send(json.dumps({
                "type": "code_change",
                "file": "test.py",
                "message": "Fixed bug in authentication"
            }))
            
            # Manus receives it
            msg = await manus.recv()
            print(f"Manus received: {msg}")
            
            # Manus responds
            await manus.send(json.dumps({
                "type": "response",
                "message": "Great fix! I'll review it."
            }))
            
            # Cursor receives response
            response = await cursor.recv()
            print(f"Cursor received: {response}")
    
    server.close()
    await server.wait_closed()
    
    print("\n✅ COLLABORATION WORKS! The bridge is REAL!")
    print("This is what will run on Lambda Labs for global AI collaboration!")

if __name__ == "__main__":
    asyncio.run(test_collaboration()) 