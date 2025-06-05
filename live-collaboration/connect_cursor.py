#!/usr/bin/env python3
"""
Simple Cursor Connection to Live Collaboration Bridge
Usage: python connect_cursor.py /path/to/your/project
"""

import asyncio
import websockets
import json
from pathlib import Path
from datetime import datetime
import sys
import time

async def connect_cursor_to_bridge(workspace_path, session_id="cursor-session"):
    """Connect Cursor workspace to live collaboration bridge"""
    
    server_url = "ws://150.136.94.139:8765"
    uri = f"{server_url}/collaborate/{session_id}/cursor"
    
    print("🚀 CURSOR → MANUS LIVE COLLABORATION")
    print("=" * 50)
    print(f"🔗 Connecting to: {uri}")
    print(f"📁 Workspace: {workspace_path}")
    print(f"🆔 Session: {session_id}")
    print()
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ CONNECTED TO LIVE COLLABORATION BRIDGE!")
            print()
            
            # Send initial file scan
            workspace = Path(workspace_path)
            if not workspace.exists():
                print(f"❌ Workspace path does not exist: {workspace_path}")
                return
            
            print("📤 Syncing files to Manus AI...")
            
            # Track files
            file_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.json', '.md', '.txt']
            synced_count = 0
            
            for ext in file_extensions:
                for file_path in workspace.glob(f"**/*{ext}"):
                    if file_path.is_file() and not any(skip in str(file_path) for skip in ['.git', 'node_modules', '__pycache__', '.vscode']):
                        try:
                            content = file_path.read_text(encoding='utf-8')
                            relative_path = str(file_path.relative_to(workspace))
                            
                            message = {
                                "type": "file_change",
                                "file_path": str(file_path),
                                "relative_path": relative_path,
                                "content": content,
                                "change_type": "scan",
                                "workspace_path": str(workspace),
                                "timestamp": datetime.now().isoformat(),
                                "session_id": session_id
                            }
                            
                            await websocket.send(json.dumps(message))
                            print(f"  📄 {relative_path}")
                            synced_count += 1
                            
                            # Small delay to avoid overwhelming
                            await asyncio.sleep(0.01)
                            
                        except Exception as e:
                            print(f"  ⚠️ Skipped {file_path.name}: {e}")
            
            print(f"\n🎉 SYNC COMPLETE! {synced_count} files synced to Manus AI")
            print()
            print("🔄 LIVE MONITORING ACTIVE")
            print("   - Edit files in your project")
            print("   - Manus sees changes INSTANTLY")
            print("   - No Git commits needed!")
            print()
            print("Press Ctrl+C to stop...")
            
            # Keep connection alive and monitor
            ping_count = 0
            while True:
                try:
                    await asyncio.sleep(30)
                    await websocket.send(json.dumps({
                        "type": "ping", 
                        "timestamp": datetime.now().isoformat()
                    }))
                    ping_count += 1
                    if ping_count % 2 == 0:  # Every minute
                        print(f"💓 Heartbeat {ping_count//2} - Connection healthy")
                        
                except websockets.exceptions.ConnectionClosed:
                    print("❌ Connection lost to collaboration bridge")
                    break
                except KeyboardInterrupt:
                    print("\n🛑 Stopping live collaboration...")
                    break
                    
    except ConnectionRefusedError:
        print("❌ CONNECTION REFUSED")
        print("   Bridge may not be running on Lambda Labs server")
        print("   Check server status and try again")
    except Exception as e:
        print(f"❌ CONNECTION FAILED: {e}")
        print("   Verify network connectivity and server status")

def main():
    if len(sys.argv) != 2:
        print("🚀 CURSOR LIVE COLLABORATION")
        print("=" * 30)
        print()
        print("Usage:")
        print(f"  python {sys.argv[0]} /path/to/your/project")
        print()
        print("Example:")
        print(f"  python {sys.argv[0]} /Users/username/my-coding-project")
        print()
        print("This will connect your project to Manus AI for real-time collaboration!")
        sys.exit(1)
    
    workspace_path = sys.argv[1]
    
    # Generate session ID based on workspace name and timestamp
    workspace_name = Path(workspace_path).name
    session_id = f"{workspace_name}-{int(time.time())}"
    
    try:
        asyncio.run(connect_cursor_to_bridge(workspace_path, session_id))
    except KeyboardInterrupt:
        print("\n✅ Live collaboration stopped")
    except Exception as e:
        print(f"\n💥 Error: {e}")

if __name__ == "__main__":
    main() 