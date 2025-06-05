#!/usr/bin/env python3
"""
Manus Live Collaboration Client
Purpose: Interface for Manus AI to access live development files and changes
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import websockets
from websockets.exceptions import ConnectionClosed
import psycopg2
import psycopg2.extras

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ManusCollaborationClient:
    """Manus interface for live collaboration with Cursor IDE"""
    
    def __init__(self, server_url: str = "ws://localhost:8765"):
        self.server_url = server_url
        self.websocket = None
        self.connected = False
        self.current_session_id = None
        self.file_change_callbacks: List[Callable] = []
        self.live_files: Dict[str, Dict[str, Any]] = {}  # relative_path -> file_data
        
        # Database connection for direct queries
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'orchestra_main'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }
        
        logger.info("Manus collaboration client initialized")

    def get_db_connection(self):
        """Get a database connection"""
        return psycopg2.connect(**self.db_config)

    async def connect_to_session(self, session_id: str) -> bool:
        """Connect to a specific collaboration session"""
        try:
            # WebSocket path: /collaborate/{session_id}/manus
            uri = f"{self.server_url}/collaborate/{session_id}/manus"
            logger.info(f"Connecting to collaboration session: {session_id}")
            
            self.websocket = await websockets.connect(uri)
            self.connected = True
            self.current_session_id = session_id
            
            # Start message handling
            asyncio.create_task(self._handle_messages())
            
            logger.info(f"Connected to collaboration session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to session {session_id}: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from collaboration server"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            self.current_session_id = None
            logger.info("Disconnected from collaboration server")

    async def send_request(self, request_type: str, data: Dict[str, Any] = None) -> bool:
        """Send request to collaboration server"""
        if not self.connected or not self.websocket:
            logger.warning("Not connected to server, cannot send request")
            return False
        
        message = {
            'type': 'manus_request',
            'request_type': request_type,
            'timestamp': datetime.now().isoformat()
        }
        
        if data:
            message.update(data)
        
        try:
            await self.websocket.send(json.dumps(message))
            logger.debug(f"Sent request: {request_type}")
            return True
        except Exception as e:
            logger.error(f"Error sending request: {e}")
            self.connected = False
            return False

    async def _handle_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type')
                    
                    logger.debug(f"Received message: {message_type}")
                    
                    if message_type == 'welcome':
                        await self._handle_welcome(data)
                    elif message_type == 'file_change':
                        await self._handle_file_change(data)
                    elif message_type == 'files_list':
                        await self._handle_files_list(data)
                    elif message_type == 'file_content':
                        await self._handle_file_content(data)
                    elif message_type == 'error':
                        logger.error(f"Server error: {data.get('message')}")
                    
                except json.JSONDecodeError:
                    logger.warning("Received invalid JSON from server")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
        
        except ConnectionClosed:
            logger.info("Connection to server closed")
            self.connected = False
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
            self.connected = False

    async def _handle_welcome(self, data: Dict[str, Any]):
        """Handle welcome message from server"""
        logger.info(f"Welcomed to session: {data.get('session_id')}")
        
        # Request initial file list
        await self.send_request('get_files')

    async def _handle_file_change(self, data: Dict[str, Any]):
        """Handle file change notification"""
        relative_path = data.get('relative_path')
        change_type = data.get('change_type')
        content = data.get('content')
        
        # Update local cache
        if change_type == 'delete':
            if relative_path in self.live_files:
                del self.live_files[relative_path]
        else:
            self.live_files[relative_path] = {
                'content': content,
                'change_type': change_type,
                'timestamp': data.get('timestamp'),
                'content_hash': data.get('content_hash'),
                'file_path': data.get('file_path')
            }
        
        logger.info(f"File changed: {relative_path} ({change_type})")
        
        # Notify callbacks
        for callback in self.file_change_callbacks:
            try:
                await callback(relative_path, change_type, data)
            except Exception as e:
                logger.error(f"Error in file change callback: {e}")

    async def _handle_files_list(self, data: Dict[str, Any]):
        """Handle files list from server"""
        files = data.get('files', [])
        
        # Update local cache
        self.live_files.clear()
        for file_data in files:
            relative_path = file_data['relative_path']
            self.live_files[relative_path] = file_data
        
        logger.info(f"Received file list: {len(files)} files")

    async def _handle_file_content(self, data: Dict[str, Any]):
        """Handle file content response"""
        file_path = data.get('file_path')
        content = data.get('content')
        
        if file_path in self.live_files:
            self.live_files[file_path]['content'] = content
        
        logger.debug(f"Received content for: {file_path}")

    def add_file_change_callback(self, callback: Callable):
        """Add callback for file change notifications"""
        self.file_change_callbacks.append(callback)

    def remove_file_change_callback(self, callback: Callable):
        """Remove file change callback"""
        if callback in self.file_change_callbacks:
            self.file_change_callbacks.remove(callback)

    # Public API methods for Manus

    async def get_current_files(self) -> List[Dict[str, Any]]:
        """Get list of current files in the collaboration session"""
        if not self.connected:
            logger.warning("Not connected to collaboration session")
            return []
        
        await self.send_request('get_files')
        
        # Wait a moment for response
        await asyncio.sleep(0.1)
        
        return list(self.live_files.values())

    async def get_file_content(self, file_path: str) -> Optional[str]:
        """Get content of a specific file"""
        # Try cache first
        if file_path in self.live_files:
            content = self.live_files[file_path].get('content')
            if content is not None:
                return content
        
        # Request from server
        if self.connected:
            await self.send_request('get_file_content', {'file_path': file_path})
            
            # Wait for response
            await asyncio.sleep(0.1)
            
            if file_path in self.live_files:
                return self.live_files[file_path].get('content')
        
        return None

    async def watch_changes(self, callback: Callable):
        """Start watching for file changes"""
        self.add_file_change_callback(callback)
        logger.info("Started watching for file changes")

    async def stop_watching(self, callback: Callable):
        """Stop watching for file changes"""
        self.remove_file_change_callback(callback)
        logger.info("Stopped watching for file changes")

    def get_available_sessions(self) -> List[Dict[str, Any]]:
        """Get list of available collaboration sessions from database"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM active_collaboration_overview
                        ORDER BY last_active DESC
                    """)
                    
                    sessions = cur.fetchall()
                    return [dict(session) for session in sessions]
                    
        except Exception as e:
            logger.error(f"Error getting available sessions: {e}")
            return []

    def get_session_activity(self, session_id: str) -> List[Dict[str, Any]]:
        """Get recent activity for a specific session"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            lc.change_type,
                            lc.timestamp,
                            lf.relative_path,
                            lc.change_size,
                            lc.content_delta
                        FROM live_changes lc
                        JOIN live_files lf ON lc.file_id = lf.id
                        JOIN collaboration_sessions cs ON lc.session_id = cs.id
                        WHERE cs.cursor_session_id = %s
                        ORDER BY lc.timestamp DESC
                        LIMIT 50
                    """, (session_id,))
                    
                    changes = cur.fetchall()
                    return [dict(change) for change in changes]
                    
        except Exception as e:
            logger.error(f"Error getting session activity: {e}")
            return []

    def get_file_history(self, session_id: str, file_path: str) -> List[Dict[str, Any]]:
        """Get change history for a specific file"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            lc.change_type,
                            lc.timestamp,
                            lc.content_before,
                            lc.content_after,
                            lc.change_size
                        FROM live_changes lc
                        JOIN live_files lf ON lc.file_id = lf.id
                        JOIN collaboration_sessions cs ON lc.session_id = cs.id
                        WHERE cs.cursor_session_id = %s AND lf.relative_path = %s
                        ORDER BY lc.timestamp DESC
                        LIMIT 20
                    """, (session_id, file_path))
                    
                    history = cur.fetchall()
                    return [dict(change) for change in history]
                    
        except Exception as e:
            logger.error(f"Error getting file history: {e}")
            return []

    # Convenience methods for common use cases

    async def monitor_session(self, session_id: str, on_file_change: Callable = None):
        """Monitor a session with optional file change callback"""
        await self.connect_to_session(session_id)
        
        if on_file_change:
            await self.watch_changes(on_file_change)
        
        logger.info(f"Monitoring session: {session_id}")

    async def get_recent_changes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent changes in the current session"""
        if not self.current_session_id:
            return []
        
        return self.get_session_activity(self.current_session_id)[:limit]

    async def search_files_by_extension(self, extension: str) -> List[Dict[str, Any]]:
        """Search for files by extension in current session"""
        files = await self.get_current_files()
        return [f for f in files if f.get('relative_path', '').endswith(extension)]

    async def get_python_files(self) -> List[Dict[str, Any]]:
        """Get all Python files in current session"""
        return await self.search_files_by_extension('.py')

    async def get_javascript_files(self) -> List[Dict[str, Any]]:
        """Get all JavaScript/TypeScript files in current session"""
        files = await self.get_current_files()
        return [f for f in files if f.get('relative_path', '').endswith(('.js', '.ts', '.jsx', '.tsx'))]

    def is_connected(self) -> bool:
        """Check if connected to a collaboration session"""
        return self.connected and self.current_session_id is not None

    def get_session_id(self) -> Optional[str]:
        """Get current session ID"""
        return self.current_session_id

    async def ping_server(self) -> bool:
        """Ping the collaboration server"""
        if not self.connected:
            return False
        
        try:
            await self.websocket.send(json.dumps({'type': 'ping'}))
            return True
        except Exception as e:
            logger.error(f"Error pinging server: {e}")
            return False

# Example usage and testing
async def example_usage():
    """Example of how Manus would use this client"""
    client = ManusCollaborationClient()
    
    # Get available sessions
    sessions = client.get_available_sessions()
    if not sessions:
        logger.info("No active collaboration sessions found")
        return
    
    # Connect to the most recent session
    session_id = sessions[0]['cursor_session_id']
    await client.monitor_session(session_id)
    
    # Define file change handler
    async def on_file_change(file_path: str, change_type: str, data: Dict[str, Any]):
        print(f"🔥 File changed: {file_path} ({change_type})")
        if change_type in ['modify', 'create']:
            content = data.get('content', '')
            print(f"   Content length: {len(content)} characters")
    
    # Start monitoring
    await client.watch_changes(on_file_change)
    
    # Get current files
    files = await client.get_current_files()
    print(f"📁 Current files in session: {len(files)}")
    
    # Get Python files specifically
    python_files = await client.get_python_files()
    print(f"🐍 Python files: {len(python_files)}")
    
    for py_file in python_files[:3]:  # Show first 3
        content = await client.get_file_content(py_file['relative_path'])
        print(f"   {py_file['relative_path']}: {len(content or '')} characters")
    
    # Monitor for changes
    print("👀 Monitoring for changes... (Press Ctrl+C to stop)")
    try:
        while client.is_connected():
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping monitoring...")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(example_usage()) 