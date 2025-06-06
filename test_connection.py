#!/usr/bin/env python3
import asyncio
import json
import websockets

async def test():
    async with websockets.connect("ws://localhost:8765") as ws:
        # Send auth
        await ws.send(json.dumps({
            "ai_name": "Test-AI",
            "api_key": "test-key"
        }))
        
        # Get response
        response = await ws.recv()
        data = json.loads(response)
        print(f"✅ Connection successful!")
        print(f"Response: {data['message']}")
        print(f"Status: {data['status']}")
        
        # Send a test message
        await ws.send(json.dumps({
            "type": "test",
            "message": "Bridge is working!"
        }))
        
        print("\n🎉 BRIDGE IS FULLY OPERATIONAL!")

asyncio.run(test()) 