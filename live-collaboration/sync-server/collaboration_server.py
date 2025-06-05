#!/usr/bin/env python3
"""
Live Collaboration WebSocket Server
Purpose: Real-time sync between Cursor IDE and Manus AI
"""

import asyncio
import json
import hashlib
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Set, Optional, Any, List
import websockets
import psycopg2
import psycopg2.extras
from websockets.server import WebSocketServerProtocol
import redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CollaborationServer:
    """WebSocket server for live collaboration between Cursor and Manus"""
    
    def __init__(self):
        self.connections: Dict[str, Dict[str, Any]] = {}  # session_id -> connection info
        self.sessions: Dict[str, Dict[str, Any]] = {}     # session_id -> session data
        
        # Database connection
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'orchestra_main'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }
        
        # Redis for real-time caching
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 1)),
            decode_responses=True
        )
        
        logger.info("Collaboration server initialized")

    def get_db_connection(self):
        """Get a database connection"""
        return psycopg2.connect(**self.db_config)

    async def register_connection(self, websocket: WebSocketServerProtocol, session_id: str, client_type: str):
        """Register a new WebSocket connection"""
        connection_info = {
            'websocket': websocket,
            'client_type': client_type,  # 'cursor' or 'manus'
            'connected_at': datetime.now(),
            'last_activity': datetime.now()
        }
        
        if session_id not in self.connections:
            self.connections[session_id] = {}
        
        self.connections[session_id][client_type] = connection_info
        
        # Update database
        with self.get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if client_type == 'manus':
                    cur.execute(
                        "UPDATE collaboration_sessions SET manus_connected = true WHERE cursor_session_id = %s",
                        (session_id,)
                    )
                conn.commit()
        
        logger.info(f"Registered {client_type} connection for session {session_id}")

    async def unregister_connection(self, session_id: str, client_type: str):
        """Unregister a WebSocket connection"""
        if session_id in self.connections and client_type in self.connections[session_id]:
            del self.connections[session_id][client_type]
            
            if not self.connections[session_id]:
                del self.connections[session_id]
            
            # Update database
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    if client_type == 'manus':
                        cur.execute(
                            "UPDATE collaboration_sessions SET manus_connected = false WHERE cursor_session_id = %s",
                            (session_id,)
                        )
                    conn.commit()
        
        logger.info(f"Unregistered {client_type} connection for session {session_id}")

    async def broadcast_to_session(self, session_id: str, message: Dict[str, Any], exclude_client: Optional[str] = None):
        """Broadcast message to all clients in a session"""
        if session_id not in self.connections:
            return
        
        message_json = json.dumps(message)
        
        for client_type, conn_info in self.connections[session_id].items():
            if exclude_client and client_type == exclude_client:
                continue
                
            try:
                await conn_info['websocket'].send(message_json)
                conn_info['last_activity'] = datetime.now()
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"Connection closed for {client_type} in session {session_id}")
                await self.unregister_connection(session_id, client_type)

    async def handle_file_change(self, session_id: str, data: Dict[str, Any], client_type: str):
        """Handle file change from Cursor"""
        try:
            file_path = data.get('file_path')
            relative_path = data.get('relative_path')
            content = data.get('content', '')
            change_type = data.get('change_type', 'modify')
            
            # Calculate content hash
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Get or create session
                    cur.execute(
                        "SELECT id FROM collaboration_sessions WHERE cursor_session_id = %s AND is_active = true",
                        (session_id,)
                    )
                    session_row = cur.fetchone()
                    
                    if not session_row:
                        # Create new session
                        cur.execute("""
                            INSERT INTO collaboration_sessions (cursor_session_id, session_name, workspace_path)
                            VALUES (%s, %s, %s) RETURNING id
                        """, (session_id, f"Session-{session_id[:8]}", data.get('workspace_path', '')))
                        session_row = cur.fetchone()
                    
                    session_uuid = session_row['id']
                    
                    # Update or insert file
                    cur.execute("""
                        INSERT INTO live_files (session_id, file_path, relative_path, content, content_hash, file_size, cursor_last_edit)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (session_id, relative_path)
                        DO UPDATE SET 
                            content = EXCLUDED.content,
                            content_hash = EXCLUDED.content_hash,
                            file_size = EXCLUDED.file_size,
                            cursor_last_edit = NOW(),
                            last_modified = NOW()
                        RETURNING id
                    """, (session_uuid, file_path, relative_path, content, content_hash, len(content)))
                    
                    file_row = cur.fetchone()
                    file_id = file_row['id']
                    
                    # Log the change
                    cur.execute("""
                        INSERT INTO live_changes (file_id, session_id, change_type, content_after, change_size, timestamp)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                    """, (file_id, session_uuid, change_type, content, len(content)))
                    
                    conn.commit()
            
            # Cache in Redis for fast access
            cache_key = f"live_file:{session_id}:{relative_path}"
            self.redis_client.setex(cache_key, 3600, json.dumps({
                'content': content,
                'content_hash': content_hash,
                'last_modified': datetime.now().isoformat(),
                'file_size': len(content)
            }))
            
            # Broadcast to Manus
            await self.broadcast_to_session(session_id, {
                'type': 'file_change',
                'file_path': file_path,
                'relative_path': relative_path,
                'content': content,
                'change_type': change_type,
                'timestamp': datetime.now().isoformat(),
                'content_hash': content_hash
            }, exclude_client=client_type)
            
            logger.info(f"Processed file change: {relative_path} in session {session_id}")
            
        except Exception as e:
            logger.error(f"Error handling file change: {e}")
            await self.send_error(session_id, client_type, f"Failed to process file change: {str(e)}")

    async def handle_manus_request(self, session_id: str, data: Dict[str, Any], client_type: str):
        """Handle requests from Manus"""
        try:
            request_type = data.get('request_type')
            
            if request_type == 'get_files':
                # Get current files in session
                with self.get_db_connection() as conn:
                    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                        cur.execute("""
                            SELECT lf.relative_path, lf.content, lf.last_modified, lf.file_size, lf.content_hash
                            FROM live_files lf
                            JOIN collaboration_sessions cs ON lf.session_id = cs.id
                            WHERE cs.cursor_session_id = %s AND cs.is_active = true AND lf.manus_visible = true
                            ORDER BY lf.last_modified DESC
                        """, (session_id,))
                        
                        files = cur.fetchall()
                
                response = {
                    'type': 'files_list',
                    'files': [dict(f) for f in files],
                    'timestamp': datetime.now().isoformat()
                }
                
                await self.send_to_client(session_id, 'manus', response)
                
            elif request_type == 'get_file_content':
                file_path = data.get('file_path')
                
                # Try Redis cache first
                cache_key = f"live_file:{session_id}:{file_path}"
                cached_content = self.redis_client.get(cache_key)
                
                if cached_content:
                    file_data = json.loads(cached_content)
                    response = {
                        'type': 'file_content',
                        'file_path': file_path,
                        'content': file_data['content'],
                        'cached': True,
                        'timestamp': file_data['last_modified']
                    }
                else:
                    # Fallback to database
                    with self.get_db_connection() as conn:
                        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                            cur.execute("""
                                SELECT lf.content, lf.last_modified, lf.content_hash
                                FROM live_files lf
                                JOIN collaboration_sessions cs ON lf.session_id = cs.id
                                WHERE cs.cursor_session_id = %s AND lf.relative_path = %s AND cs.is_active = true
                            """, (session_id, file_path))
                            
                            file_row = cur.fetchone()
                    
                    if file_row:
                        response = {
                            'type': 'file_content',
                            'file_path': file_path,
                            'content': file_row['content'],
                            'cached': False,
                            'timestamp': file_row['last_modified'].isoformat()
                        }
                    else:
                        response = {
                            'type': 'error',
                            'message': f"File not found: {file_path}"
                        }
                
                await self.send_to_client(session_id, 'manus', response)
                
            # Log Manus activity
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO manus_activity (session_id, activity_type, activity_data)
                        SELECT cs.id, %s, %s
                        FROM collaboration_sessions cs
                        WHERE cs.cursor_session_id = %s AND cs.is_active = true
                    """, (request_type, json.dumps(data), session_id))
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"Error handling Manus request: {e}")
            await self.send_error(session_id, client_type, f"Failed to process request: {str(e)}")

    async def send_to_client(self, session_id: str, client_type: str, message: Dict[str, Any]):
        """Send message to specific client"""
        if session_id in self.connections and client_type in self.connections[session_id]:
            try:
                await self.connections[session_id][client_type]['websocket'].send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                await self.unregister_connection(session_id, client_type)

    async def send_error(self, session_id: str, client_type: str, error_message: str):
        """Send error message to client"""
        await self.send_to_client(session_id, client_type, {
            'type': 'error',
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        })

    async def handle_message(self, websocket: WebSocketServerProtocol, message: str, session_id: str, client_type: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            logger.info(f"Received {message_type} from {client_type} in session {session_id}")
            
            if message_type == 'file_change' and client_type == 'cursor':
                await self.handle_file_change(session_id, data, client_type)
            elif message_type == 'manus_request' and client_type == 'manus':
                await self.handle_manus_request(session_id, data, client_type)
            elif message_type == 'ping':
                await self.send_to_client(session_id, client_type, {'type': 'pong', 'timestamp': datetime.now().isoformat()})
            else:
                logger.warning(f"Unknown message type: {message_type} from {client_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from {client_type}: {message}")
            await self.send_error(session_id, client_type, "Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error(session_id, client_type, f"Server error: {str(e)}")

    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket client connection"""
        try:
            # Parse connection parameters from path
            # Expected: /collaborate/{session_id}/{client_type}
            path_parts = path.strip('/').split('/')
            if len(path_parts) != 3 or path_parts[0] != 'collaborate':
                await websocket.close(code=4000, reason="Invalid path format")
                return
            
            session_id = path_parts[1]
            client_type = path_parts[2]
            
            if client_type not in ['cursor', 'manus']:
                await websocket.close(code=4000, reason="Invalid client type")
                return
            
            logger.info(f"New {client_type} client connected for session {session_id}")
            
            await self.register_connection(websocket, session_id, client_type)
            
            # Send welcome message
            await self.send_to_client(session_id, client_type, {
                'type': 'welcome',
                'session_id': session_id,
                'client_type': client_type,
                'timestamp': datetime.now().isoformat()
            })
            
            # Handle messages
            async for message in websocket:
                await self.handle_message(websocket, message, session_id, client_type)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected from session {session_id}")
        except Exception as e:
            logger.error(f"Error in client handler: {e}")
        finally:
            if 'session_id' in locals() and 'client_type' in locals():
                await self.unregister_connection(session_id, client_type)

    async def start_server(self, host: str = "0.0.0.0", port: int = 8765):
        """Start the collaboration WebSocket server"""
        logger.info(f"Starting collaboration server on {host}:{port}")
        
        # Test database connection
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            logger.info("Database connection successful")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
        
        # Test Redis connection
        try:
            self.redis_client.ping()
            logger.info("Redis connection successful")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
        
        # Start WebSocket server
        async with websockets.serve(self.handle_client, host, port):
            logger.info(f"Collaboration server running on ws://{host}:{port}")
            await asyncio.Future()  # Run forever

if __name__ == "__main__":
    server = CollaborationServer()
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise 