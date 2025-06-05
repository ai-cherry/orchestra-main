#!/usr/bin/env python3
"""
Smart Live Collaboration Client for Cursor IDE
Uses intelligent filtering for large projects
"""

import os
import sys
import asyncio
import websockets
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import our smart filter
sys.path.append(os.path.dirname(__file__))
from cursor_plugin.smart_file_filter import SmartCollaborationFilter, filter_files_for_collaboration

class SmartFileWatcher(FileSystemEventHandler):
    """Intelligent file watcher that filters large projects"""
    
    def __init__(self, websocket, session_id: str, project_root: str):
        self.websocket = websocket
        self.session_id = session_id
        self.project_root = project_root
        self.filter = SmartCollaborationFilter()
        self.file_hashes: Dict[str, str] = {}
        self.pending_changes: Set[str] = set()
        
        # Get project context and determine strategy
        self.context = self.filter.get_project_context(project_root)
        self.is_large_project = self.context['file_count'] > 1000
        
        if self.is_large_project:
            print(f"🧠 Smart filtering enabled for large project ({self.context['file_count']} files)")
            self.relevant_files = set(filter_files_for_collaboration(project_root, max_files=100))
            print(f"📊 Monitoring {len(self.relevant_files)} most relevant files")
        else:
            print(f"📁 Standard monitoring for manageable project ({self.context['file_count']} files)")
            self.relevant_files = None
    
    def should_process_file(self, file_path: str) -> bool:
        """Determine if file should be processed based on smart filtering"""
        # Basic filter first
        if not self.filter.should_sync_file(file_path):
            return False
        
        # For large projects, only process files in our relevant set
        if self.is_large_project and self.relevant_files:
            return file_path in self.relevant_files
        
        return True
    
    def on_modified(self, event):
        if not event.is_directory:
            file_path = event.src_path
            
            if self.should_process_file(file_path):
                # Debounce rapid changes
                self.pending_changes.add(file_path)
                asyncio.create_task(self.process_change_delayed(file_path))
    
    async def process_change_delayed(self, file_path: str):
        """Process file change with debouncing"""
        await asyncio.sleep(0.5)  # Debounce delay
        
        if file_path in self.pending_changes:
            self.pending_changes.remove(file_path)
            await self.sync_file(file_path)
    
    async def sync_file(self, file_path: str):
        """Sync file to collaboration bridge"""
        try:
            # Calculate file hash to detect actual changes
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            file_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Only sync if content actually changed
            if self.file_hashes.get(file_path) != file_hash:
                self.file_hashes[file_path] = file_hash
                
                relative_path = os.path.relpath(file_path, self.project_root)
                
                message = {
                    "type": "file_change",
                    "session_id": self.session_id,
                    "file_path": relative_path,
                    "content": content,
                    "hash": file_hash,
                    "timestamp": datetime.now().isoformat(),
                    "smart_filtered": self.is_large_project
                }
                
                await self.websocket.send(json.dumps(message))
                print(f"📤 Synced: {relative_path}")
                
        except Exception as e:
            print(f"⚠️  Error syncing {file_path}: {e}")

async def smart_sync_project(websocket, session_id: str, project_root: str):
    """Intelligently sync project files"""
    filter = SmartCollaborationFilter()
    context = filter.get_project_context(project_root)
    
    print(f"\n📊 PROJECT ANALYSIS:")
    print(f"   📁 Total relevant files: {context['file_count']}")
    print(f"   🔥 Recent files (24h): {len(context['recent_files'])}")
    print(f"   ⚡ Active files (6h): {len(context['active_files'])}")
    
    if context['file_count'] > 1000:
        print(f"   🧠 Using smart filtering (large project detected)")
        files_to_sync = filter_files_for_collaboration(project_root, max_files=100)
        print(f"   ✅ Filtered to {len(files_to_sync)} most relevant files")
    else:
        print(f"   📋 Syncing all relevant files (manageable size)")
        files_to_sync = []
        for root, dirs, files in os.walk(project_root):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not any(pattern in d.lower() for pattern in filter.ignore_patterns)]
            
            for file in files:
                file_path = os.path.join(root, file)
                if filter.should_sync_file(file_path):
                    files_to_sync.append(file_path)
    
    print(f"\n📤 Syncing {len(files_to_sync)} files to Manus AI...")
    
    synced_count = 0
    for file_path in files_to_sync:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            relative_path = os.path.relpath(file_path, project_root)
            
            message = {
                "type": "file_sync",
                "session_id": session_id,
                "file_path": relative_path,
                "content": content,
                "hash": hashlib.md5(content.encode()).hexdigest(),
                "timestamp": datetime.now().isoformat(),
                "smart_filtered": context['file_count'] > 1000
            }
            
            await websocket.send(json.dumps(message))
            synced_count += 1
            
            # Progress indicator for large syncs
            if synced_count % 10 == 0:
                print(f"   📊 Progress: {synced_count}/{len(files_to_sync)} files synced")
                
        except Exception as e:
            print(f"   ⚠️  Skipped {relative_path}: {e}")
    
    return synced_count

async def main():
    if len(sys.argv) != 2:
        print("Usage: python connect_cursor_smart.py <project_path>")
        sys.exit(1)
    
    project_path = os.path.abspath(sys.argv[1])
    project_name = os.path.basename(project_path)
    session_id = f"{project_name}-{int(datetime.now().timestamp())}"
    
    # WebSocket bridge URL
    bridge_url = "ws://150.136.94.139:8765"
    ws_url = f"{bridge_url}/collaborate/{session_id}/cursor"
    
    print("🚀 SMART CURSOR → MANUS LIVE COLLABORATION")
    print("=" * 50)
    print(f"🔗 Connecting to: {ws_url}")
    print(f"📁 Workspace: {project_path}")
    print(f"🆔 Session: {session_id}")
    
    # Quick project analysis
    filter = SmartCollaborationFilter()
    context = filter.get_project_context(project_path)
    
    if context['file_count'] > 1000:
        print(f"🧠 SMART MODE: Large project detected ({context['file_count']} files)")
        print(f"🎯 Will intelligently filter to ~100 most relevant files")
    else:
        print(f"📋 STANDARD MODE: Manageable project size ({context['file_count']} files)")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("\n✅ CONNECTED TO LIVE COLLABORATION BRIDGE!")
            
            # Smart sync based on project size
            synced_count = await smart_sync_project(websocket, session_id, project_path)
            
            print(f"\n🎉 SYNC COMPLETE! {synced_count} files synced to Manus AI")
            
            # Start intelligent file watching
            event_handler = SmartFileWatcher(websocket, session_id, project_path)
            observer = Observer()
            observer.schedule(event_handler, project_path, recursive=True)
            observer.start()
            
            print(f"\n🔄 SMART LIVE MONITORING ACTIVE")
            if context['file_count'] > 1000:
                print(f"   🧠 Intelligent filtering enabled")
                print(f"   📊 Monitoring {len(event_handler.relevant_files)} priority files")
            print(f"   ✏️  Edit files in your project")
            print(f"   👀 Manus sees changes INSTANTLY")
            print(f"   🚫 No Git commits needed!")
            print(f"\nPress Ctrl+C to stop...")
            
            # Keep connection alive
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print(f"\n🛑 Stopping live collaboration...")
                observer.stop()
                observer.join()
                
    except websockets.exceptions.ConnectionClosedError:
        print(f"❌ Connection lost to collaboration bridge")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 