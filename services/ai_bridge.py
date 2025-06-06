#!/usr/bin/env python3
"""
Cherry AI Coding Bridge - Simple WebSocket Bridge for All AI Coders
Connects Manus AI, Cursor, Claude, GPT-4, and any other AI coding assistant
Focuses on performance and simplicity over complex authentication
"""

import asyncio
import json
import logging
import os
import time
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path

import websockets
import aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, WebSocketException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cherry-ai-bridge")

@dataclass
class ConnectedAI:
    """Represents a connected AI coder"""
    name: str
    websocket: WebSocket
    connected_at: datetime
    capabilities: List[str] = field(default_factory=list)
    last_ping: float = field(default_factory=time.time)
    message_count: int = 0

class CherryAIBridge:
    """
    Simple WebSocket bridge for AI coding assistants
    No complex auth - just simple API keys for basic security
    """
    
    def __init__(self):
        self.host = os.getenv("BRIDGE_HOST", "0.0.0.0")
        self.port = int(os.getenv("BRIDGE_PORT", "8765"))
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/1")
        
        # Connected AI assistants
        self.connected_ais: Dict[str, ConnectedAI] = {}
        
        # Simple API key validation (good enough for our needs)
        self.valid_api_keys = {
            "manus-ai": "manus-key-2024",
            "cursor-ai": "cursor-key-2024", 
            "claude-ai": "claude-key-2024",
            "gpt4-ai": "gpt4-key-2024",
            "admin": "admin-key-2024"
        }
        
        # Redis for state sharing
        self.redis = None
        
        # FastAPI app for HTTP endpoints
        self.app = FastAPI(title="Cherry AI Coding Bridge", version="1.0.0")
        self.setup_fastapi()
        
    async def setup_redis(self):
        """Setup Redis connection for state sharing"""
        try:
            self.redis = await aioredis.from_url(self.redis_url)
            logger.info("✅ Redis connected for state sharing")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e} (continuing without Redis)")
            self.redis = None
    
    def setup_fastapi(self):
        """Setup FastAPI routes and middleware"""
        # CORS middleware for web clients
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Simplified for development
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @self.app.get("/")
        async def root():
            return {"message": "Cherry AI Coding Bridge", "status": "running"}
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "connected_ais": len(self.connected_ais),
                "ai_names": list(self.connected_ais.keys()),
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/ais")
        async def list_ais():
            """List connected AIs and their capabilities"""
            return {
                "connected_ais": {
                    name: {
                        "capabilities": ai.capabilities,
                        "connected_at": ai.connected_at.isoformat(),
                        "message_count": ai.message_count,
                        "last_ping": ai.last_ping
                    }
                    for name, ai in self.connected_ais.items()
                }
            }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for AI connections"""
            await self.handle_websocket_connection(websocket)
    
    async def handle_websocket_connection(self, websocket: WebSocket):
        """Handle WebSocket connections from AI assistants with proper error handling"""
        ai_name = None
        logger.info("🔌 New WebSocket connection attempt")
        
        try:
            # Accept the WebSocket connection
            await websocket.accept()
            logger.info("✅ WebSocket connection accepted")
            
            # Wait for authentication message with timeout
            try:
                logger.debug("⏳ Waiting for authentication message...")
                auth_message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second timeout for auth
                )
                logger.debug(f"📨 Received auth message: {auth_message[:100]}...")
            except asyncio.TimeoutError:
                logger.error("❌ Authentication timeout - no message received within 30 seconds")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "code": 1002,
                    "message": "Authentication timeout"
                }))
                await websocket.close(code=1002, reason="Authentication timeout")
                return
            
            # Parse authentication data
            try:
                auth_data = json.loads(auth_message)
                logger.debug(f"📋 Parsed auth data: {json.dumps(auth_data, indent=2)}")
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON in auth message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "code": 1007,
                    "message": "Invalid JSON format in authentication"
                }))
                await websocket.close(code=1007, reason="Invalid JSON")
                return
            
            ai_name = auth_data.get("ai_name", "unknown")
            api_key = auth_data.get("api_key", "")
            capabilities = auth_data.get("capabilities", [])
            
            logger.info(f"🤖 Authentication attempt from: {ai_name}")
            
            # Validate API key
            if api_key not in self.valid_api_keys.values():
                logger.error(f"❌ Invalid API key from {ai_name}: {api_key}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "code": 1008,
                    "message": "Invalid API key"
                }))
                await websocket.close(code=1008, reason="Invalid API key")
                return
            
            # Check if AI is already connected
            if ai_name in self.connected_ais:
                logger.warning(f"⚠️ {ai_name} is already connected, disconnecting old connection")
                old_ws = self.connected_ais[ai_name].websocket
                try:
                    await old_ws.close()
                except:
                    pass
            
            # Register the AI
            connected_ai = ConnectedAI(
                name=ai_name,
                websocket=websocket,
                connected_at=datetime.now(),
                capabilities=capabilities
            )
            
            self.connected_ais[ai_name] = connected_ai
            logger.info(f"✅ {ai_name} registered successfully")
            
            # Send connection confirmation
            confirmation = {
                "type": "connected",
                "ai_name": ai_name,
                "capabilities": capabilities,
                "bridge_info": {
                    "version": "1.0.0",
                    "connected_ais": list(self.connected_ais.keys()),
                    "features": ["real-time-sync", "multi-ai-collaboration", "code-sharing"]
                }
            }
            
            await websocket.send_text(json.dumps(confirmation))
            logger.info(f"✅ Sent connection confirmation to {ai_name}")
            
            # Notify other AIs
            await self.broadcast_to_others(ai_name, {
                "type": "ai_joined",
                "ai_name": ai_name,
                "capabilities": capabilities,
                "timestamp": datetime.now().isoformat()
            })
            
            # Now handle incoming messages
            logger.info(f"📡 Starting message loop for {ai_name}")
            
            while True:
                try:
                    # Receive message with timeout to allow periodic checks
                    message = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=60.0  # 60 second timeout
                    )
                    await self.handle_message(ai_name, message)
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    try:
                        await websocket.send_text(json.dumps({
                            "type": "ping",
                            "timestamp": datetime.now().isoformat()
                        }))
                    except:
                        logger.error(f"❌ Failed to send ping to {ai_name}")
                        break
                except WebSocketDisconnect:
                    logger.info(f"🔌 {ai_name} disconnected normally")
                    break
                except Exception as e:
                    logger.error(f"❌ Error in message loop for {ai_name}: {e}")
                    logger.debug(traceback.format_exc())
                    break
                    
        except WebSocketDisconnect:
            logger.info(f"🔌 {ai_name or 'Unknown AI'} disconnected during setup")
        except Exception as e:
            logger.error(f"❌ Unexpected error in connection handler: {e}")
            logger.debug(traceback.format_exc())
            
            # Try to send error to client if possible
            try:
                if websocket.client_state.value == 1:  # CONNECTED
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "code": 1011,
                        "message": f"Internal server error: {str(e)}"
                    }))
            except:
                pass
        finally:
            # Cleanup
            if ai_name and ai_name in self.connected_ais:
                logger.info(f"🧹 Cleaning up connection for {ai_name}")
                del self.connected_ais[ai_name]
                
                # Notify other AIs
                try:
                    await self.broadcast_to_others(ai_name, {
                        "type": "ai_disconnected",
                        "ai_name": ai_name,
                        "timestamp": datetime.now().isoformat()
                    })
                except:
                    pass
            
            # Ensure WebSocket is closed
            try:
                if websocket.client_state.value == 1:  # CONNECTED
                    await websocket.close()
            except:
                pass
    
    async def handle_message(self, sender_name: str, message: str):
        """Handle incoming messages from AIs"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            # Update sender stats
            if sender_name in self.connected_ais:
                self.connected_ais[sender_name].message_count += 1
                self.connected_ais[sender_name].last_ping = time.time()
            
            logger.info(f"📨 MSG IN: {sender_name} -> {message_type}")
            logger.debug(f"Message data: {json.dumps(data, indent=2)}")
            
            # Handle different message types
            if message_type == "ping":
                await self.handle_ping(sender_name)
            elif message_type == "code_change":
                await self.handle_code_change(sender_name, data)
            elif message_type == "request_help":
                await self.handle_help_request(sender_name, data)
            elif message_type == "broadcast":
                await self.handle_broadcast(sender_name, data)
            else:
                # Forward to all other AIs
                await self.broadcast_to_others(sender_name, data)
                
        except json.JSONDecodeError:
            logger.error(f"❌ Invalid JSON from {sender_name}: {message}")
            if sender_name in self.connected_ais:
                await self.connected_ais[sender_name].websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format."
                }))
        except Exception as e:
            logger.error(f"❌ Error handling message from {sender_name}: {e}", exc_info=True)
            if sender_name in self.connected_ais:
                try:
                    await self.connected_ais[sender_name].websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Server-side error: {str(e)}"
                    }))
                except Exception as send_e:
                    logger.error(f"❌ Failed to send error to client: {send_e}")
    
    async def handle_ping(self, sender_name: str):
        """Handle ping from AI (keep-alive)"""
        if sender_name in self.connected_ais:
            ai = self.connected_ais[sender_name]
            await ai.websocket.send_text(json.dumps({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }))
    
    async def handle_code_change(self, sender_name: str, data: Dict):
        """Handle code change notifications"""
        # Store in Redis if available
        if self.redis:
            try:
                await self.redis.set(
                    f"code_change:{sender_name}:{time.time()}",
                    json.dumps(data),
                    ex=3600  # 1 hour TTL
                )
            except Exception as e:
                logger.warning(f"Redis storage failed: {e}")
        
        # Broadcast to other AIs
        await self.broadcast_to_others(sender_name, {
            "type": "code_change",
            "sender": sender_name,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
    
    async def handle_help_request(self, sender_name: str, data: Dict):
        """Handle help requests from AIs"""
        requested_capabilities = data.get("capabilities", [])
        
        # Find AIs with matching capabilities
        matching_ais = []
        for name, ai in self.connected_ais.items():
            if name != sender_name:
                for capability in requested_capabilities:
                    if capability in ai.capabilities:
                        matching_ais.append(name)
                        break
        
        # Send help request to matching AIs
        help_message = {
            "type": "help_request",
            "requester": sender_name,
            "request": data.get("request", ""),
            "capabilities_needed": requested_capabilities,
            "timestamp": datetime.now().isoformat()
        }
        
        for ai_name in matching_ais:
            if ai_name in self.connected_ais:
                await self.connected_ais[ai_name].websocket.send_text(
                    json.dumps(help_message)
                )
        
        logger.info(f"🆘 Help request from {sender_name} sent to {matching_ais}")
    
    async def handle_broadcast(self, sender_name: str, data: Dict):
        """Handle broadcast messages"""
        broadcast_data = {
            "type": "broadcast",
            "sender": sender_name,
            "message": data.get("message", ""),
            "data": data.get("data", {}),
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_to_all(broadcast_data, exclude=sender_name)
    
    async def broadcast_to_others(self, sender_name: str, message: Dict):
        """Broadcast message to all AIs except sender"""
        message_json = json.dumps(message)
        
        for name, ai in self.connected_ais.items():
            if name != sender_name:
                try:
                    await ai.websocket.send_text(message_json)
                except Exception as e:
                    logger.error(f"Failed to send to {name}: {e}")
    
    async def broadcast_to_all(self, message: Dict, exclude: Optional[str] = None):
        """Broadcast message to all connected AIs"""
        message_json = json.dumps(message)
        
        for name, ai in self.connected_ais.items():
            if exclude and name == exclude:
                continue
            try:
                await ai.websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"Failed to broadcast to {name}: {e}")
    
    async def start_server(self):
        """Start the bridge server"""
        await self.setup_redis()
        
        logger.info(f"🚀 Cherry AI Bridge starting on {self.host}:{self.port}")
        logger.info(f"🤖 Supported AIs: Manus, Cursor, Claude, GPT-4, and more")
        logger.info(f"🔗 WebSocket endpoint: ws://{self.host}:{self.port}/ws")
        logger.info(f"🌐 HTTP endpoints: http://{self.host}:{self.port}")
        
        # Start the FastAPI server
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

# Standalone script entry point
async def main():
    """Main entry point"""
    bridge = CherryAIBridge()
    await bridge.start_server()

if __name__ == "__main__":
    asyncio.run(main()) 