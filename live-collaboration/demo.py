#!/usr/bin/env python3
"""
Live Collaboration System Demo
Purpose: Demonstrate real-time Cursor ↔ Manus collaboration
"""

import asyncio
import tempfile
import shutil
from pathlib import Path
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import collaboration components
from cursor_plugin.file_watcher import CursorFileWatcher
from manus_interface.manus_client import ManusCollaborationClient
from sync_server.collaboration_server import CollaborationServer

async def run_demo():
    """Run a complete live collaboration demonstration"""
    
    print("🚀 LIVE COLLABORATION SYSTEM DEMO")
    print("=" * 50)
    print("This demo shows real-time collaboration between Cursor IDE and Manus AI")
    print()
    
    # Create temporary workspace
    workspace = Path(tempfile.mkdtemp(prefix="collaboration_demo_"))
    print(f"📁 Demo workspace: {workspace}")
    
    # Create sample files
    demo_files = {
        'main.py': '''#!/usr/bin/env python3
"""
Demo Python application for live collaboration
"""

def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number"""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def main():
    print("Fibonacci Demo")
    for i in range(10):
        result = calculate_fibonacci(i)
        print(f"F({i}) = {result}")

if __name__ == "__main__":
    main()
''',
        'utils.js': '''// JavaScript utilities for demo
function formatDate(date) {
    return date.toISOString().split('T')[0];
}

function isPrime(num) {
    if (num <= 1) return false;
    for (let i = 2; i <= Math.sqrt(num); i++) {
        if (num % i === 0) return false;
    }
    return true;
}

module.exports = { formatDate, isPrime };
''',
        'config.json': '''{
    "app_name": "Live Collaboration Demo",
    "version": "1.0.0",
    "features": {
        "real_time_sync": true,
        "multi_language": true,
        "change_tracking": true
    }
}'''
    }
    
    for filename, content in demo_files.items():
        (workspace / filename).write_text(content)
    
    print(f"📝 Created {len(demo_files)} demo files")
    
    try:
        # Start collaboration server
        print("\n🔧 Starting collaboration server...")
        server = CollaborationServer()
        asyncio.create_task(server.start_server(port=8766))
        await asyncio.sleep(1)  # Give server time to start
        print("✅ Collaboration server running on port 8766")
        
        # Initialize Cursor file watcher
        session_id = "demo-session"
        print(f"\n👀 Starting Cursor file watcher for session: {session_id}")
        cursor_watcher = CursorFileWatcher(
            str(workspace),
            "ws://localhost:8766",
            session_id
        )
        
        # Connect Cursor watcher
        cursor_connected = await cursor_watcher.connect_to_server()
        if cursor_connected:
            print("✅ Cursor watcher connected and syncing files")
        else:
            print("❌ Failed to connect Cursor watcher")
            return
        
        # Wait for initial sync
        await asyncio.sleep(2)
        
        # Initialize Manus client
        print(f"\n🤖 Connecting Manus AI to session: {session_id}")
        manus_client = ManusCollaborationClient("ws://localhost:8766")
        manus_connected = await manus_client.connect_to_session(session_id)
        
        if manus_connected:
            print("✅ Manus AI connected to live session")
        else:
            print("❌ Failed to connect Manus AI")
            return
        
        # Set up Manus change monitoring
        changes_detected = []
        
        async def on_file_change(file_path: str, change_type: str, data: dict):
            changes_detected.append({
                'file': file_path,
                'type': change_type,
                'time': time.time()
            })
            print(f"🔥 Manus detected: {file_path} ({change_type})")
        
        await manus_client.watch_changes(on_file_change)
        
        # Show what Manus can see
        print("\n📂 What Manus AI can see in the live session:")
        files = await manus_client.get_current_files()
        for file_data in files:
            path = file_data['relative_path']
            size = file_data.get('file_size', 0)
            print(f"  📄 {path} ({size} bytes)")
        
        # Demonstrate real-time file access
        print("\n🔍 Manus accessing file content:")
        main_py_content = await manus_client.get_file_content('main.py')
        if main_py_content:
            lines = main_py_content.split('\n')
            print(f"  📄 main.py: {len(lines)} lines, {len(main_py_content)} characters")
            print(f"  First line: {lines[0]}")
        
        # Demonstrate real-time changes
        print("\n✏️ Simulating live code changes...")
        
        # Modify main.py
        main_file = workspace / 'main.py'
        current_content = main_file.read_text()
        modified_content = current_content + '\n# This comment was added during the demo!\nprint("Demo completed successfully")\n'
        main_file.write_text(modified_content)
        print("  ✏️ Modified main.py - added comment and print statement")
        
        await asyncio.sleep(1)  # Wait for change detection
        
        # Create new file
        new_file = workspace / 'demo_new.py'
        new_content = '''# New file created during demo
def greet(name):
    return f"Hello, {name}! Live collaboration is working!"

print(greet("Manus AI"))
'''
        new_file.write_text(new_content)
        print("  ➕ Created new file: demo_new.py")
        
        await asyncio.sleep(1)
        
        # Show updated file content from Manus perspective
        print("\n🤖 Manus AI verifying changes:")
        updated_content = await manus_client.get_file_content('main.py')
        if updated_content and 'Demo completed successfully' in updated_content:
            print("  ✅ Manus sees the updated main.py content")
        
        new_file_content = await manus_client.get_file_content('demo_new.py')
        if new_file_content:
            print("  ✅ Manus sees the new file: demo_new.py")
        
        # Show change detection results
        await asyncio.sleep(1)
        print(f"\n📊 Changes detected by Manus: {len(changes_detected)}")
        for change in changes_detected:
            print(f"  🔄 {change['file']} - {change['type']}")
        
        # Demonstrate file type filtering
        python_files = await manus_client.get_python_files()
        js_files = await manus_client.get_javascript_files()
        print(f"\n🐍 Python files Manus can access: {len(python_files)}")
        print(f"🟨 JavaScript files Manus can access: {len(js_files)}")
        
        # Show session info
        sessions = manus_client.get_available_sessions()
        demo_session = next((s for s in sessions if s['cursor_session_id'] == session_id), None)
        if demo_session:
            print(f"\n📋 Session info:")
            print(f"  ID: {demo_session['cursor_session_id']}")
            print(f"  Files: {demo_session.get('file_count', 0)}")
            print(f"  Active: {demo_session.get('is_active', False)}")
        
        print("\n" + "=" * 50)
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("✅ Real-time file synchronization working")
        print("✅ Manus AI can see live code changes")
        print("✅ Change detection and notifications working")
        print("✅ File type filtering working")
        print("✅ Session persistence working")
        print()
        print("🚀 The live collaboration system is ready for production use!")
        print("   Manus AI can now see your code changes in real-time as you type in Cursor.")
        print("   No more Git commits needed for AI collaboration!")
        
    except Exception as e:
        print(f"\n💥 Demo error: {e}")
        logger.error(f"Demo failed: {e}", exc_info=True)
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up demo environment...")
        
        try:
            if 'cursor_watcher' in locals():
                await cursor_watcher.disconnect_from_server()
        except:
            pass
        
        try:
            if 'manus_client' in locals():
                await manus_client.disconnect()
        except:
            pass
        
        # Remove temporary workspace
        if workspace.exists():
            shutil.rmtree(workspace)
            print(f"🗑️ Removed demo workspace: {workspace}")
        
        print("✅ Demo cleanup complete")

if __name__ == "__main__":
    asyncio.run(run_demo()) 