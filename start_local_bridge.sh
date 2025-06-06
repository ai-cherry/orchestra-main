#!/bin/bash

echo "🚀 Starting AI Collaboration Bridge Locally"
echo "=========================================="
echo ""
echo "This will start the AI bridge on your machine RIGHT NOW"
echo "You can connect Manus AI and any other AI to collaborate!"
echo ""

# Check if Redis is installed
if ! command -v redis-server &> /dev/null; then
    echo "⚠️  Redis not found. Starting minimal bridge without Redis..."
    echo ""
    
    # Create a minimal bridge without Redis
    cat > temp_bridge.py << 'EOF'
import asyncio
import json
import websockets
from datetime import datetime

connected_ais = {}

async def handle_client(websocket):
    """Handle AI connections"""
    ai_name = None
    try:
        auth_msg = await websocket.recv()
        auth_data = json.loads(auth_msg)
        ai_name = auth_data.get("ai_name", "Unknown")
        
        print(f"✅ {ai_name} connected!")
        connected_ais[ai_name] = websocket
        
        await websocket.send(json.dumps({
            "type": "connected",
            "ai_name": ai_name,
            "message": "Welcome to AI Bridge!"
        }))
        
        # Notify others
        for other_name, other_ws in connected_ais.items():
            if other_name != ai_name:
                try:
                    await other_ws.send(json.dumps({
                        "type": "ai_joined",
                        "ai_name": ai_name,
                        "timestamp": datetime.now().isoformat()
                    }))
                except:
                    pass
        
        async for message in websocket:
            data = json.loads(message)
            print(f"📨 {ai_name} sent: {data}")
            
            # Broadcast to others
            for other_name, other_ws in connected_ais.items():
                if other_name != ai_name:
                    try:
                        await other_ws.send(json.dumps({
                            **data,
                            "sender": ai_name
                        }))
                    except:
                        pass
                    
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if ai_name and ai_name in connected_ais:
            del connected_ais[ai_name]
            print(f"🔌 {ai_name} disconnected")

async def main():
    print("✅ AI Bridge running on ws://localhost:8765")
    print("\n📌 Connect your AIs to: ws://localhost:8765")
    print("   - Manus AI: Update connection to ws://localhost:8765")
    print("   - Other AIs: Use the same URL")
    print("\nPress Ctrl+C to stop")
    
    async with websockets.serve(handle_client, "localhost", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
EOF

    python temp_bridge.py
    
else
    echo "✅ Redis found. Starting full bridge with caching..."
    
    # Start Redis in background
    redis-server --daemonize yes
    
    # Check if bridge exists
    if [ -f "services/ai_bridge.py" ]; then
        python services/ai_bridge.py
    else
        echo "⚠️  Bridge not found in services/. Using minimal bridge..."
        python temp_bridge.py
    fi
fi 