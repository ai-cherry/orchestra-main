#!/usr/bin/env python3
"""Quick test of the live collaboration bridge connection"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_bridge():
    try:
        # Test connection to production bridge
        uri = 'ws://150.136.94.139:8765/collaborate/test-session/cursor'
        print('🔧 Testing connection to live collaboration bridge...')
        
        async with websockets.connect(uri) as websocket:
            print('✅ Successfully connected to collaboration bridge!')
            
            # Send a test message
            test_message = {
                'type': 'ping',
                'timestamp': datetime.now().isoformat()
            }
            await websocket.send(json.dumps(test_message))
            print('📤 Sent test ping to bridge')
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            print(f'📥 Received response: {data.get("type", "unknown")}')
            print('🎉 BRIDGE IS FULLY OPERATIONAL!')
            return True
            
    except Exception as e:
        print(f'❌ Connection test failed: {e}')
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bridge())
    if success:
        print("\n🚀 READY FOR CURSOR CONNECTION!")
    else:
        print("\n🔧 Bridge may need troubleshooting") 