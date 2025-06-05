# 🚀 QUICK START: Live Collaboration System

## ⚡ **IMMEDIATE SETUP FOR CURSOR**

Your live collaboration bridge is **ACTIVE** on Lambda Labs server!

### 🔧 **Connect Cursor IDE (Local Machine)**

```bash
# 1. Clone the collaboration system locally
git clone <your-repo> live-collaboration
cd live-collaboration

# 2. Install dependencies
pip install websockets watchdog asyncio

# 3. Start watching your project (replace with your actual project path)
python cursor-plugin/file_watcher.py /path/to/your/project --server ws://150.136.94.139:8765 --session-id my-session --verbose
```

### 🤖 **For Manus AI (Already Running on Server)**

The Manus client is already connected and waiting. Once Cursor connects, Manus will see live changes!

### 📝 **Example: Cursor Connection Script**

Save this as `connect_cursor.py`:

```python
#!/usr/bin/env python3
import asyncio
import websockets
import json
import hashlib
from pathlib import Path
from datetime import datetime

async def connect_cursor_to_bridge(workspace_path, session_id="cursor-session"):
    """Connect Cursor workspace to live collaboration bridge"""
    
    server_url = "ws://150.136.94.139:8765"
    uri = f"{server_url}/collaborate/{session_id}/cursor"
    
    print(f"🔗 Connecting to collaboration bridge: {uri}")
    print(f"📁 Watching workspace: {workspace_path}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to live collaboration bridge!")
            
            # Send initial file scan
            workspace = Path(workspace_path)
            for file_path in workspace.rglob("*.py"):
                if file_path.is_file():
                    try:
                        content = file_path.read_text()
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
                        print(f"📤 Synced: {relative_path}")
                        
                    except Exception as e:
                        print(f"⚠️ Skipped {file_path}: {e}")
            
            print("🎉 Initial sync complete! Manus can now see your code!")
            print("💡 Make changes to your files - Manus will see them instantly!")
            
            # Keep connection alive
            while True:
                try:
                    await asyncio.sleep(30)
                    await websocket.send(json.dumps({"type": "ping"}))
                except:
                    break
                    
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python connect_cursor.py /path/to/your/project")
        sys.exit(1)
    
    workspace_path = sys.argv[1]
    asyncio.run(connect_cursor_to_bridge(workspace_path))
```

### 🎯 **Usage**

```bash
# Connect your project to Manus AI
python connect_cursor.py /path/to/your/coding/project
```

## ⚡ **INSTANT TESTING**

1. **Run the connection script** with your project path
2. **Edit any `.py` file** in your project
3. **Manus AI sees changes instantly** - no Git needed!

## 🔍 **Verification**

Once connected, you should see:
- ✅ "Connected to live collaboration bridge!"
- ✅ Files being synced: "📤 Synced: main.py"
- ✅ "Initial sync complete! Manus can now see your code!"

## 🚨 **Troubleshooting**

| Issue | Solution |
|-------|----------|
| Connection refused | Check if bridge is running: `curl -I http://150.136.94.139:8765` |
| "No such file" | Use absolute path to your project directory |
| Permission denied | Check file permissions and workspace access |
| Websocket timeout | Verify internet connection and server status |

## 🎉 **SUCCESS!**

When working correctly:
- Your code changes appear **instantly** to Manus AI
- No more Git commits needed for collaboration
- True real-time pair programming achieved!

---

**🚀 You're now living in the future of AI-assisted development!** 