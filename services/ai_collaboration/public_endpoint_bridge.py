#!/usr/bin/env python3
"""
Enhanced AI Collaboration Bridge with Public Endpoint Exposure
Implements Option 1 from the comprehensive implementation guide
"""

import asyncio
import websockets
import json
import logging
import os
import time
import jwt
import hashlib
import ssl
from pathlib import Path
from typing import Dict, Set, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import aioredis
from contextlib import asynccontextmanager
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ClientConnection:
    """Represents a connected AI client"""
    client_id: str
    client_type: str  # 'manus' or 'cursor'
    websocket: websockets.WebSocketServerProtocol
    authenticated_at: datetime
    last_activity: datetime
    permissions: Set[str]
    rate_limit_tokens: int = 100
    
class RateLimiter:
    """Token bucket rate limiter"""
    def __init__(self, tokens_per_minute: int = 60):
        self.tokens_per_minute = tokens_per_minute
        self.buckets = {}
        
    async def check_rate_limit(self, client_id: str) -> bool:
        """Check if client has tokens available"""
        now = time.time()
        if client_id not in self.buckets:
            self.buckets[client_id] = {
                'tokens': self.tokens_per_minute,
                'last_refill': now
            }
            
        bucket = self.buckets[client_id]
        # Refill tokens
        time_passed = now - bucket['last_refill']
        tokens_to_add = time_passed * (self.tokens_per_minute / 60)
        bucket['tokens'] = min(self.tokens_per_minute, bucket['tokens'] + tokens_to_add)
        bucket['last_refill'] = now
        
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            return True
        return False

class SecurityManager:
    """Handles authentication and authorization"""
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.valid_tokens = {
            "manus": os.getenv("MANUS_API_KEY", "manus_live_collab_2024"),
            "cursor": os.getenv("CURSOR_API_KEY", "cursor_live_collab_2024")
        }
        
    def generate_jwt_token(self, client_id: str, client_type: str) -> str:
        """Generate JWT token for authenticated client"""
        payload = {
            'client_id': client_id,
            'client_type': client_type,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
        
    def verify_jwt_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
            
    def authenticate_client(self, client_type: str, provided_token: str) -> bool:
        """Authenticate client with API key"""
        expected_token = self.valid_tokens.get(client_type)
        return expected_token and provided_token == expected_token

class PublicEndpointBridge:
    """Enhanced AI Collaboration Bridge with public endpoint exposure"""
    
    def __init__(self, 
                 host: str = "0.0.0.0",
                 port: int = 8765,
                 mcp_ports: Dict[str, int] = None,
                 redis_url: str = "redis://localhost:6379",
                 project_root: str = "/var/www/orchestra"):
        
        self.host = host
        self.port = port
        self.mcp_ports = mcp_ports or {
            "knowledge": 8001,
            "context": 8002,
            "workflow": 8003,
            "analytics": 8004
        }
        self.redis_url = redis_url
        self.project_root = Path(project_root)
        
        # Security components
        self.security_manager = SecurityManager(
            secret_key=os.getenv("BRIDGE_SECRET_KEY", "your-secret-key-here")
        )
        self.rate_limiter = RateLimiter(tokens_per_minute=60)
        
        # Connection management
        self.connections: Dict[str, ClientConnection] = {}
        self.manus_connection: Optional[ClientConnection] = None
        self.cursor_connection: Optional[ClientConnection] = None
        
        # Shared state
        self.shared_state = {
            "bridge_version": "1.0",
            "public_endpoint": True,
            "security_enabled": True,
            "mcp_servers": self.mcp_ports,
            "active_workflows": {},
            "collaboration_context": {},
            "last_sync": time.time()
        }
        
        # Redis connection for distributed state
        self.redis = None
        
    async def setup_redis(self):
        """Initialize Redis connection for distributed state management"""
        try:
            self.redis = await aioredis.create_redis_pool(self.redis_url)
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            # Continue without Redis - use in-memory state
            
    async def cleanup_redis(self):
        """Clean up Redis connection"""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
            
    @asynccontextmanager
    async def managed_redis(self):
        """Context manager for Redis lifecycle"""
        await self.setup_redis()
        try:
            yield
        finally:
            await self.cleanup_redis()
            
    async def start_server(self):
        """Start the WebSocket server with public endpoint configuration"""
        logger.info(f"🚀 Starting Public Endpoint Bridge on {self.host}:{self.port}")
        
        # SSL context for secure WebSocket connections (optional)
        ssl_context = None
        cert_path = os.getenv("SSL_CERT_PATH")
        key_path = os.getenv("SSL_KEY_PATH")
        
        if cert_path and key_path and os.path.exists(cert_path) and os.path.exists(key_path):
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(cert_path, key_path)
            logger.info("🔒 SSL enabled for secure WebSocket connections")
            
        async with self.managed_redis():
            async with websockets.serve(
                self.handle_connection,
                self.host,
                self.port,
                ssl=ssl_context,
                max_size=10 * 1024 * 1024,  # 10MB max message size
                max_queue=1000,
                compression=None  # Disable compression for lower latency
            ):
                logger.info("✅ Public Endpoint Bridge is running!")
                logger.info(f"🌐 WebSocket URL: {'wss' if ssl_context else 'ws'}://{self.host}:{self.port}")
                logger.info(f"🔧 MCP Servers: {self.mcp_ports}")
                
                # Start background tasks
                await asyncio.gather(
                    self.health_check_loop(),
                    self.cleanup_inactive_connections(),
                    asyncio.Future()  # Keep server running
                )
                
    async def handle_connection(self, websocket, path):
        """Handle incoming WebSocket connections with enhanced security"""
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        client_id = str(uuid.uuid4())
        logger.info(f"🔌 New connection attempt from {client_ip} (ID: {client_id})")
        
        try:
            # Set connection timeout
            auth_message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            auth_data = json.loads(auth_message)
            
            # Validate authentication
            client_type = auth_data.get("client")
            provided_token = auth_data.get("token")
            
            if not self.security_manager.authenticate_client(client_type, provided_token):
                await websocket.send(json.dumps({
                    "status": "authentication_failed",
                    "message": "Invalid credentials"
                }))
                await websocket.close(code=1008, reason="Authentication failed")
                logger.warning(f"❌ Authentication failed for {client_ip}")
                return
                
            # Check rate limit
            if not await self.rate_limiter.check_rate_limit(client_ip):
                await websocket.send(json.dumps({
                    "status": "rate_limited",
                    "message": "Too many requests"
                }))
                await websocket.close(code=1008, reason="Rate limited")
                logger.warning(f"⚠️ Rate limit exceeded for {client_ip}")
                return
                
            # Create client connection
            connection = ClientConnection(
                client_id=client_id,
                client_type=client_type,
                websocket=websocket,
                authenticated_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                permissions=self._get_client_permissions(client_type)
            )
            
            # Store connection
            self.connections[client_id] = connection
            if client_type == "manus":
                self.manus_connection = connection
            elif client_type == "cursor":
                self.cursor_connection = connection
                
            # Generate JWT for future requests
            jwt_token = self.security_manager.generate_jwt_token(client_id, client_type)
            
            # Send authentication success
            await websocket.send(json.dumps({
                "status": "authenticated",
                "client_id": client_id,
                "client_type": client_type,
                "jwt_token": jwt_token,
                "permissions": list(connection.permissions),
                "bridge_info": {
                    "version": self.shared_state["bridge_version"],
                    "mcp_servers": self.mcp_ports,
                    "features": ["real-time-sync", "mcp-integration", "secure-collaboration"]
                }
            }))
            
            logger.info(f"✅ {client_type} authenticated successfully (ID: {client_id})")
            
            # Send initial state
            await self.send_initial_state(connection)
            
            # Handle messages
            await self.handle_client_messages(connection)
            
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Connection timeout for {client_ip}")
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 Client {client_ip} disconnected")
        except Exception as e:
            logger.error(f"❌ Error handling connection: {e}")
        finally:
            # Cleanup
            if client_id in self.connections:
                del self.connections[client_id]
            if self.manus_connection and self.manus_connection.client_id == client_id:
                self.manus_connection = None
                logger.info("🤖 Manus disconnected")
            elif self.cursor_connection and self.cursor_connection.client_id == client_id:
                self.cursor_connection = None
                logger.info("💻 Cursor disconnected")
                
    def _get_client_permissions(self, client_type: str) -> Set[str]:
        """Get permissions for client type"""
        base_permissions = {"read", "write", "execute", "sync"}
        
        if client_type == "manus":
            return base_permissions | {"admin", "deploy", "mcp_full_access"}
        elif client_type == "cursor":
            return base_permissions | {"code_edit", "debug", "mcp_read_access"}
        else:
            return {"read"}
            
    async def send_initial_state(self, connection: ClientConnection):
        """Send initial state to newly connected client"""
        state_message = {
            "type": "initial_state",
            "timestamp": time.time(),
            "shared_state": self.shared_state,
            "active_connections": {
                "manus": self.manus_connection is not None,
                "cursor": self.cursor_connection is not None,
                "total": len(self.connections)
            },
            "mcp_status": await self.check_mcp_servers_status()
        }
        
        await connection.websocket.send(json.dumps(state_message))
        
    async def handle_client_messages(self, connection: ClientConnection):
        """Handle messages from authenticated client"""
        async for message in connection.websocket:
            try:
                # Update last activity
                connection.last_activity = datetime.utcnow()
                
                # Parse message
                data = json.loads(message)
                message_type = data.get("type")
                
                # Check permissions
                required_permission = self._get_required_permission(message_type)
                if required_permission and required_permission not in connection.permissions:
                    await connection.websocket.send(json.dumps({
                        "type": "error",
                        "message": f"Permission denied: {required_permission} required"
                    }))
                    continue
                    
                # Process message
                await self.process_message(data, connection)
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {connection.client_id}")
                await connection.websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await connection.websocket.send(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
                
    def _get_required_permission(self, message_type: str) -> Optional[str]:
        """Get required permission for message type"""
        permission_map = {
            "execute_command": "execute",
            "file_change": "write",
            "deploy_request": "deploy",
            "mcp_query": "mcp_read_access",
            "mcp_update": "mcp_full_access"
        }
        return permission_map.get(message_type)
        
    async def process_message(self, data: Dict[str, Any], connection: ClientConnection):
        """Process authenticated message"""
        message_type = data.get("type")
        
        logger.info(f"📨 Processing {message_type} from {connection.client_type}")
        
        # Route to appropriate handler
        handlers = {
            "sync_request": self.handle_sync_request,
            "workflow_update": self.handle_workflow_update,
            "mcp_query": self.handle_mcp_query,
            "collaboration_event": self.handle_collaboration_event,
            "health_check": self.handle_health_check
        }
        
        handler = handlers.get(message_type)
        if handler:
            await handler(data, connection)
        else:
            # Broadcast to other clients
            await self.broadcast_to_others(data, connection)
            
    async def handle_sync_request(self, data: Dict, connection: ClientConnection):
        """Handle state synchronization request"""
        await self.send_initial_state(connection)
        
    async def handle_workflow_update(self, data: Dict, connection: ClientConnection):
        """Handle workflow state update"""
        workflow_id = data.get("workflow_id")
        workflow_state = data.get("state")
        
        if workflow_id:
            self.shared_state["active_workflows"][workflow_id] = {
                "state": workflow_state,
                "updated_by": connection.client_type,
                "timestamp": time.time()
            }
            
            # Store in Redis if available
            if self.redis:
                await self.redis.set(
                    f"workflow:{workflow_id}",
                    json.dumps(workflow_state),
                    expire=3600  # 1 hour TTL
                )
                
            # Broadcast update
            await self.broadcast_to_all({
                "type": "workflow_updated",
                "workflow_id": workflow_id,
                "state": workflow_state,
                "updated_by": connection.client_type
            })
            
    async def handle_mcp_query(self, data: Dict, connection: ClientConnection):
        """Handle MCP server query"""
        mcp_server = data.get("server")
        query = data.get("query")
        
        if mcp_server in self.mcp_ports:
            # Forward to MCP server (implementation depends on MCP protocol)
            response = {
                "type": "mcp_response",
                "server": mcp_server,
                "query": query,
                "result": f"MCP query forwarded to {mcp_server}",
                "timestamp": time.time()
            }
            await connection.websocket.send(json.dumps(response))
            
    async def handle_collaboration_event(self, data: Dict, connection: ClientConnection):
        """Handle collaboration event"""
        event_type = data.get("event_type")
        event_data = data.get("event_data")
        
        # Update collaboration context
        self.shared_state["collaboration_context"][event_type] = {
            "data": event_data,
            "source": connection.client_type,
            "timestamp": time.time()
        }
        
        # Broadcast to all clients
        await self.broadcast_to_all({
            "type": "collaboration_event",
            "event_type": event_type,
            "event_data": event_data,
            "source": connection.client_type
        })
        
    async def handle_health_check(self, data: Dict, connection: ClientConnection):
        """Handle health check request"""
        health_status = {
            "type": "health_response",
            "status": "healthy",
            "uptime": time.time() - self.shared_state["last_sync"],
            "connections": len(self.connections),
            "mcp_status": await self.check_mcp_servers_status(),
            "timestamp": time.time()
        }
        await connection.websocket.send(json.dumps(health_status))
        
    async def broadcast_to_others(self, message: Dict, sender: ClientConnection):
        """Broadcast message to all clients except sender"""
        message_json = json.dumps(message)
        
        for client_id, connection in self.connections.items():
            if connection.client_id != sender.client_id:
                try:
                    await connection.websocket.send(message_json)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    
    async def broadcast_to_all(self, message: Dict):
        """Broadcast message to all connected clients"""
        message_json = json.dumps(message)
        
        for client_id, connection in list(self.connections.items()):
            try:
                await connection.websocket.send(message_json)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                
    async def check_mcp_servers_status(self) -> Dict[str, bool]:
        """Check status of MCP servers"""
        status = {}
        for server_name, port in self.mcp_ports.items():
            # Simple port check - can be enhanced with actual health endpoint
            status[server_name] = await self._check_port_open("localhost", port)
        return status
        
    async def _check_port_open(self, host: str, port: int) -> bool:
        """Check if a port is open"""
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=1.0
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False
            
    async def health_check_loop(self):
        """Periodic health check of all components"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Check MCP servers
                mcp_status = await self.check_mcp_servers_status()
                
                # Broadcast health status
                await self.broadcast_to_all({
                    "type": "system_health",
                    "mcp_status": mcp_status,
                    "active_connections": len(self.connections),
                    "timestamp": time.time()
                })
                
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                
    async def cleanup_inactive_connections(self):
        """Clean up inactive connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                now = datetime.utcnow()
                inactive_threshold = timedelta(minutes=5)
                
                for client_id, connection in list(self.connections.items()):
                    if now - connection.last_activity > inactive_threshold:
                        logger.info(f"Cleaning up inactive connection: {client_id}")
                        await connection.websocket.close()
                        
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Collaboration Bridge with Public Endpoints")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind to")
    parser.add_argument("--redis-url", default="redis://localhost:6379", help="Redis URL")
    parser.add_argument("--project-root", default="/var/www/orchestra", help="Project root directory")
    
    args = parser.parse_args()
    
    # Create and start bridge
    bridge = PublicEndpointBridge(
        host=args.host,
        port=args.port,
        redis_url=args.redis_url,
        project_root=args.project_root
    )
    
    try:
        asyncio.run(bridge.start_server())
    except KeyboardInterrupt:
        logger.info("🛑 Bridge stopped by user")

if __name__ == "__main__":
    main()