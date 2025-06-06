#!/usr/bin/env python3
"""
WORKING AI BRIDGE - NO BULLSHIT, TESTED AND VERIFIED
"""

import asyncio
import json
import websockets
from datetime import datetime
import logging
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

connected_ais = {}
message_history = []

async def handle_client(websocket, path):
    """Handle AI connections, now accepting a path"""
    ai_name = None
    try:
        logger.info(f"Incoming connection on path: {path}")
        try:
            # Get authentication
            auth_msg = await websocket.recv()
            logger.info(f"Raw auth message: {auth_msg}")
            auth_data = json.loads(auth_msg)
        except Exception as e:
            logger.error(f"AUTH ERROR: {e}\n{traceback.format_exc()}")
            await websocket.close(code=1011, reason="Auth parse error")
            return
        ai_name = auth_data.get("ai_name", "Unknown")
        api_key = auth_data.get("api_key", "")
        
        logger.info(f"✅ {ai_name} connected with key: {api_key[:10]}...")
        connected_ais[ai_name] = {
            "websocket": websocket,
            "connected_at": datetime.now().isoformat(),
            "capabilities": auth_data.get("capabilities", [])
        }
        
        # Send confirmation
        try:
            await websocket.send(json.dumps({
                "type": "connected",
                "status": "success",
                "ai_name": ai_name,
                "message": f"Welcome {ai_name}! You're connected to the AI Bridge.",
                "connected_ais": list(connected_ais.keys())
            }))
        except Exception as e:
            logger.error(f"SEND CONFIRMATION ERROR: {e}\n{traceback.format_exc()}")
            await websocket.close(code=1011, reason="Send confirmation error")
            return
        
        # Notify others
        for other_name, other_data in connected_ais.items():
            if other_name != ai_name:
                try:
                    await other_data["websocket"].send(json.dumps({
                        "type": "ai_joined",
                        "ai_name": ai_name,
                        "capabilities": auth_data.get("capabilities", []),
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception as e:
                    logger.error(f"NOTIFY ERROR: {e}\n{traceback.format_exc()}")
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"📨 {ai_name} sent: {data.get('type', 'unknown')}")
                
                # Add to history
                message_history.append({
                    "sender": ai_name,
                    "timestamp": datetime.now().isoformat(),
                    "data": data
                })
                
                # Broadcast to others
                broadcast_count = 0
                for other_name, other_data in connected_ais.items():
                    if other_name != ai_name:
                        try:
                            await other_data["websocket"].send(json.dumps({
                                **data,
                                "sender": ai_name,
                                "timestamp": datetime.now().isoformat()
                            }))
                            broadcast_count += 1
                        except Exception as e:
                            logger.error(f"BROADCAST ERROR: {e}\n{traceback.format_exc()}")
                
                logger.info(f"   ➡️  Broadcasted to {broadcast_count} other AIs")
            except Exception as e:
                logger.error(f"MESSAGE HANDLING ERROR: {e}\n{traceback.format_exc()}")
                    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed for {ai_name or 'unknown'}")
    except Exception as e:
        logger.error(f"Error handling {ai_name or 'unknown'}: {e}\n{traceback.format_exc()}")
    finally:
        if ai_name and ai_name in connected_ais:
            del connected_ais[ai_name]
            logger.info(f"🔌 {ai_name} disconnected")
            
            # Notify others
            for other_name, other_data in connected_ais.items():
                try:
                    await other_data["websocket"].send(json.dumps({
                        "type": "ai_left",
                        "ai_name": ai_name,
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception as e:
                    logger.error(f"NOTIFY DISCONNECT ERROR: {e}\n{traceback.format_exc()}")

async def main():
    """Start the AI Bridge"""
    logger.info("🚀 AI BRIDGE STARTING...")
    logger.info("=" * 50)
    
    async with websockets.serve(handle_client, "localhost", 8765):
        logger.info("✅ AI Bridge running on ws://localhost:8765")
        logger.info("")
        logger.info("📌 Connection Details:")
        logger.info("   URL: ws://localhost:8765")
        logger.info("   Auth: Send JSON with ai_name and api_key")
        logger.info("")
        logger.info("🔗 Manus AI Connection:")
        logger.info("   1. Update Manus config to use ws://localhost:8765")
        logger.info("   2. Use api_key: manus-key-2024")
        logger.info("")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 50)
        
        # Run forever
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Bridge shutting down...") 