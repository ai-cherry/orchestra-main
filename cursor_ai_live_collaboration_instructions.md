# CURSOR AI LIVE COLLABORATION SETUP

## 🎯 **WHAT CURSOR NEEDS TO DO:**

### **1. Connect to Live Collaboration Server**

The live collaboration bridge is deployed on **45.32.69.157:8765**

Create this file in your Cherry AI project: `cursor_live_client.py`

```python
#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging

class CursorLiveCollaborationClient:
    def __init__(self, server_ip="45.32.69.157", port=8765):
        self.websocket_url = f"ws://{server_ip}:{port}"
        self.websocket = None
        
    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            
            # Authenticate as Cursor AI
            auth_message = {
                "client": "cursor",
                "token": "cursor_live_collab_2024"
            }
            await self.websocket.send(json.dumps(auth_message))
            
            response = await self.websocket.recv()
            auth_response = json.loads(response)
            
            if auth_response.get("status") == "authenticated":
                print("💻 Cursor AI connected to live collaboration!")
                print(f"🎯 Goal: {auth_response.get('goal')}")
                return True
            else:
                print("❌ Authentication failed")
                return False
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def execute_command(self, command, working_dir="/var/www/cherry-ai"):
        if not self.websocket:
            return None
        
        try:
            message = {
                "type": "execute_command",
                "command": command,
                "working_dir": working_dir
            }
            
            await self.websocket.send(json.dumps(message))
            response = await self.websocket.recv()
            return json.loads(response)
            
        except Exception as e:
            print(f"❌ Error executing command: {e}")
            return None
    
    async def update_file(self, file_path, content):
        if not self.websocket:
            return False
        
        try:
            message = {
                "type": "file_change",
                "file_path": file_path,
                "content": content,
                "change_type": "modify"
            }
            
            await self.websocket.send(json.dumps(message))
            print(f"📝 File updated: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating file: {e}")
            return False
    
    async def listen_for_manus(self):
        if not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                data = json.loads(message)
                message_type = data.get("type")
                
                if message_type == "file_changed":
                    print(f"📝 Manus changed file: {data.get('file_path')}")
                elif message_type == "command_executed":
                    print(f"⚡ Manus executed: {data.get('command')}")
                elif message_type == "task_updated":
                    print(f"📋 Task updated: {data.get('task')}")
                    
        except Exception as e:
            print(f"❌ Error listening: {e}")

# Usage example
async def main():
    client = CursorLiveCollaborationClient()
    
    if await client.connect():
        # Example: Fix cherry-ai.me deployment
        result = await client.execute_command("ls -la /var/www/html/")
        print(f"Current web directory: {result.get('stdout')}")
        
        # Listen for Manus collaboration
        await client.listen_for_manus()

if __name__ == "__main__":
    asyncio.run(main())
```

### **2. Install Dependencies**

```bash
pip install websockets asyncio
```

### **3. Test Connection**

```bash
python3 cursor_live_client.py
```

### **4. Live Collaboration Commands**

Once connected, you can:

```python
# Execute commands on production server
await client.execute_command("git pull origin main")
await client.execute_command("systemctl status nginx")

# Update files in real-time
await client.update_file("index.html", "<html>Updated by Cursor!</html>")

# Deploy enhanced interface
await client.execute_command("cp admin-interface/enhanced-production-interface.html /var/www/html/index.html")
```

## 🚀 **IMMEDIATE GOALS FOR CURSOR:**

### **Goal 1: Fix cherry-ai.me**
```python
# Check current status
await client.execute_command("curl -I http://cherry-ai.me")

# Deploy enhanced interface
await client.execute_command("cp /var/www/cherry-ai/admin-interface/enhanced-production-interface.html /var/www/html/index.html")

# Reload nginx
await client.execute_command("systemctl reload nginx")

# Test the fix
await client.execute_command("curl http://cherry-ai.me")
```

### **Goal 2: Test Three AI Personas**
```python
# Check if personas are working
await client.execute_command("grep -n 'Cherry\\|Sophia\\|Karen' /var/www/html/index.html")
```

### **Goal 3: Database Connectivity**
```python
# Test database connection to 45.77.87.106
await client.execute_command("ping -c 3 45.77.87.106")
```

## 🎯 **COLLABORATION WORKFLOW:**

1. **Cursor connects** to live collaboration bridge
2. **Manus connects** to same bridge  
3. **Real-time sync** - changes appear instantly for both
4. **Shared commands** - see what each other is doing
5. **Live deployment** - deploy directly to cherry-ai.me

## 🔧 **AUTHENTICATION TOKENS:**

- **Cursor Token**: `cursor_live_collab_2024`
- **Manus Token**: `manus_live_collab_2024`
- **Server**: `ws://45.32.69.157:8765`

## ✅ **SUCCESS CRITERIA:**

- ✅ Cursor AI connects to live collaboration bridge
- ✅ cherry-ai.me shows enhanced interface (not basic landing page)
- ✅ Three AI personas (Cherry, Sophia, Karen) are functional
- ✅ Real-time collaboration between Manus and Cursor
- ✅ Direct deployment to production server

**This is revolutionary AI pair programming with shared production environment!** 🚀

