#!/usr/bin/env python3
"""
Cursor File Watcher - Live Collaboration Client
Purpose: Watch for file changes in Cursor workspace and stream to collaboration server
"""

import asyncio
import json
import os
import hashlib
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, Optional, Any, List
import websockets
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import argparse
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CursorFileWatcher:
    """Watches Cursor workspace for file changes and streams to collaboration server"""
    
    def __init__(self, workspace_path: str, server_url: str = "ws://localhost:8765", session_id: Optional[str] = None):
        self.workspace_path = Path(workspace_path).resolve()
        self.server_url = server_url
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.websocket = None
        self.observer = None
        self.connected = False
        self.file_cache: Dict[str, str] = {}  # relative_path -> content_hash
        self.pending_changes: Dict[str, Dict[str, Any]] = {}  # debounce changes
        self.debounce_delay = 0.5  # seconds
        
        # Files to ignore
        self.ignore_patterns = {
            '.git', '.vscode', '__pycache__', 'node_modules', '.env',
            '.DS_Store', 'Thumbs.db', '*.log', '*.tmp', '*.swp'
        }
        
        # File extensions to track
        self.track_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss',
            '.json', '.md', '.txt', '.sql', '.yaml', '.yml', '.toml',
            '.cpp', '.c', '.h', '.java', '.go', '.rs', '.php', '.rb'
        }
        
        logger.info(f"Initialized file watcher for workspace: {self.workspace_path}")
        logger.info(f"Session ID: {self.session_id}")

    def should_track_file(self, file_path: Path) -> bool:
        """Determine if a file should be tracked"""
        try:
            # Check if file is in workspace
            relative_path = file_path.relative_to(self.workspace_path)
            
            # Skip files in ignore patterns
            for ignore in self.ignore_patterns:
                if ignore.startswith('*'):
                    if str(relative_path).endswith(ignore[1:]):
                        return False
                elif any(part.startswith(ignore) for part in relative_path.parts):
                    return False
            
            # Check file extension
            if file_path.suffix.lower() not in self.track_extensions:
                return False
            
            # Skip binary files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read(1024)  # Try to read a bit
                return True
            except (UnicodeDecodeError, PermissionError):
                return False
                
        except ValueError:
            # File not in workspace
            return False
        except Exception as e:
            logger.debug(f"Error checking file {file_path}: {e}")
            return False

    def get_relative_path(self, file_path: Path) -> str:
        """Get relative path from workspace root"""
        try:
            return str(file_path.relative_to(self.workspace_path))
        except ValueError:
            return str(file_path)

    def get_file_content_hash(self, file_path: Path) -> Optional[str]:
        """Get SHA256 hash of file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.debug(f"Error reading file {file_path}: {e}")
            return None

    def read_file_content(self, file_path: Path) -> Optional[str]:
        """Read file content safely"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.debug(f"Error reading file content {file_path}: {e}")
            return None

    async def connect_to_server(self):
        """Connect to collaboration server"""
        try:
            # WebSocket path: /collaborate/{session_id}/cursor
            uri = f"{self.server_url}/collaborate/{self.session_id}/cursor"
            logger.info(f"Connecting to collaboration server: {uri}")
            
            self.websocket = await websockets.connect(uri)
            self.connected = True
            logger.info("Connected to collaboration server")
            
            # Send initial workspace scan
            await self.send_initial_scan()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            self.connected = False
            return False

    async def disconnect_from_server(self):
        """Disconnect from collaboration server"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from collaboration server")

    async def send_message(self, message: Dict[str, Any]):
        """Send message to collaboration server"""
        if not self.connected or not self.websocket:
            logger.warning("Not connected to server, cannot send message")
            return False
        
        try:
            await self.websocket.send(json.dumps(message))
            logger.debug(f"Sent message: {message.get('type', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.connected = False
            return False

    async def send_file_change(self, file_path: Path, change_type: str = 'modify'):
        """Send file change to collaboration server"""
        if not self.should_track_file(file_path):
            return
        
        relative_path = self.get_relative_path(file_path)
        content = self.read_file_content(file_path)
        
        if content is None:
            return
        
        message = {
            'type': 'file_change',
            'file_path': str(file_path),
            'relative_path': relative_path,
            'content': content,
            'change_type': change_type,
            'workspace_path': str(self.workspace_path),
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id
        }
        
        await self.send_message(message)
        
        # Update cache
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        self.file_cache[relative_path] = content_hash
        
        logger.info(f"Sent file change: {relative_path} ({change_type})")

    async def send_initial_scan(self):
        """Send initial scan of workspace files"""
        logger.info("Scanning workspace for initial file sync...")
        
        file_count = 0
        for root, dirs, files in os.walk(self.workspace_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not any(ignore in d for ignore in self.ignore_patterns if not ignore.startswith('*'))]
            
            for file in files:
                file_path = Path(root) / file
                
                if self.should_track_file(file_path):
                    await self.send_file_change(file_path, 'scan')
                    file_count += 1
                    
                    # Small delay to avoid overwhelming the server
                    await asyncio.sleep(0.01)
        
        logger.info(f"Initial scan complete: {file_count} files synced")

    def schedule_file_change(self, file_path: Path, change_type: str):
        """Schedule a file change with debouncing"""
        relative_path = self.get_relative_path(file_path)
        
        # Cancel previous change for this file
        if relative_path in self.pending_changes:
            self.pending_changes[relative_path]['task'].cancel()
        
        # Schedule new change
        task = asyncio.create_task(self.debounced_file_change(file_path, change_type))
        self.pending_changes[relative_path] = {
            'task': task,
            'file_path': file_path,
            'change_type': change_type,
            'scheduled_at': time.time()
        }

    async def debounced_file_change(self, file_path: Path, change_type: str):
        """Handle file change with debouncing"""
        await asyncio.sleep(self.debounce_delay)
        
        relative_path = self.get_relative_path(file_path)
        
        # Check if file still exists and content changed
        if not file_path.exists() and change_type != 'delete':
            return
        
        if change_type != 'delete':
            current_hash = self.get_file_content_hash(file_path)
            cached_hash = self.file_cache.get(relative_path)
            
            if current_hash == cached_hash:
                logger.debug(f"No content change detected for {relative_path}")
                return
        
        # Send the change
        await self.send_file_change(file_path, change_type)
        
        # Clean up pending changes
        if relative_path in self.pending_changes:
            del self.pending_changes[relative_path]

class CursorFileEventHandler(FileSystemEventHandler):
    """Handle file system events for Cursor workspace"""
    
    def __init__(self, watcher: CursorFileWatcher):
        self.watcher = watcher
        super().__init__()

    def on_modified(self, event):
        if not event.is_directory:
            file_path = Path(event.src_path)
            if self.watcher.should_track_file(file_path):
                self.watcher.schedule_file_change(file_path, 'modify')

    def on_created(self, event):
        if not event.is_directory:
            file_path = Path(event.src_path)
            if self.watcher.should_track_file(file_path):
                self.watcher.schedule_file_change(file_path, 'create')

    def on_deleted(self, event):
        if not event.is_directory:
            file_path = Path(event.src_path)
            if self.watcher.should_track_file(file_path):
                self.watcher.schedule_file_change(file_path, 'delete')

    def on_moved(self, event):
        if not event.is_directory:
            # Handle as delete old + create new
            old_path = Path(event.src_path)
            new_path = Path(event.dest_path)
            
            if self.watcher.should_track_file(old_path):
                self.watcher.schedule_file_change(old_path, 'delete')
            
            if self.watcher.should_track_file(new_path):
                self.watcher.schedule_file_change(new_path, 'create')

async def start_cursor_watcher(workspace_path: str, server_url: str = "ws://localhost:8765", session_id: Optional[str] = None):
    """Start the Cursor file watcher"""
    watcher = CursorFileWatcher(workspace_path, server_url, session_id)
    
    # Connect to server
    if not await watcher.connect_to_server():
        logger.error("Failed to connect to collaboration server")
        return
    
    # Set up file system watcher
    event_handler = CursorFileEventHandler(watcher)
    observer = Observer()
    observer.schedule(event_handler, str(watcher.workspace_path), recursive=True)
    
    try:
        # Start file system monitoring
        observer.start()
        logger.info(f"Started monitoring workspace: {watcher.workspace_path}")
        
        # Handle WebSocket messages
        while watcher.connected:
            try:
                message = await asyncio.wait_for(watcher.websocket.recv(), timeout=1.0)
                data = json.loads(message)
                logger.debug(f"Received message: {data.get('type', 'unknown')}")
                
                # Handle server messages (like welcome, pong, etc.)
                if data.get('type') == 'welcome':
                    logger.info(f"Server welcomed session: {data.get('session_id')}")
                
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await watcher.send_message({'type': 'ping'})
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connection to server lost")
                break
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON from server")
            except Exception as e:
                logger.error(f"Error handling server message: {e}")
                break
    
    except KeyboardInterrupt:
        logger.info("Shutting down file watcher...")
    except Exception as e:
        logger.error(f"Error in file watcher: {e}")
    finally:
        # Clean up
        observer.stop()
        observer.join()
        await watcher.disconnect_from_server()
        
        # Cancel pending changes
        for change_info in watcher.pending_changes.values():
            change_info['task'].cancel()
        
        logger.info("File watcher stopped")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Cursor Live Collaboration File Watcher")
    parser.add_argument("workspace", help="Path to Cursor workspace directory")
    parser.add_argument("--server", default="ws://localhost:8765", help="Collaboration server URL")
    parser.add_argument("--session-id", help="Custom session ID (default: auto-generated)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate workspace path
    workspace_path = Path(args.workspace).resolve()
    if not workspace_path.exists() or not workspace_path.is_dir():
        logger.error(f"Invalid workspace path: {workspace_path}")
        return 1
    
    # Start the watcher
    try:
        asyncio.run(start_cursor_watcher(str(workspace_path), args.server, args.session_id))
        return 0
    except Exception as e:
        logger.error(f"Failed to start file watcher: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 