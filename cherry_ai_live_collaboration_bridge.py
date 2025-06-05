#!/usr/bin/env python3
"""
Live Collaboration Bridge for Cherry AI
Deploy this to 45.32.69.157 for real-time Manus + Cursor collaboration
"""

import asyncio
import websockets
import json
import subprocess
import logging
import os
from pathlib import Path
import time

logging.basicConfig(level=logging.INFO)

class CherryAILiveCollaborationBridge:
    def __init__(self, project_root="/var/www/cherry-ai"):
        self.project_root = Path(project_root)
        self.connected_clients = set()
        self.manus_connection = None
        self.cursor_connection = None
        
        self.shared_state = {
            "current_task": "Deploy Cherry AI enhanced interface to cherry-ai.me",
            "priorities": [
                "Fix cherry-ai.me to show enhanced interface",
                "Deploy admin-interface/enhanced-production-interface.html",
                "Test three AI personas (Cherry, Sophia, Karen)",
                "Verify database connectivity to 45.77.87.106",
                "Get real users accessing cherry-ai.me"
            ],
            "context": {
                "production_server": "45.32.69.157",
                "database_server": "45.77.87.106", 
                "domain": "cherry-ai.me",
                "enhanced_interface": "/var/www/cherry-ai/admin-interface/enhanced-production-interface.html",
                "status": "collaboration_bridge_active",
                "github_repo": "ai-cherry/orchestra-main"
            },
            "last_sync": time.time()
        }
    
    async def start_server(self, host="0.0.0.0", port=8765):
        logging.info(f"🚀 Starting Cherry AI Live Collaboration Bridge on {host}:{port}")
        self.project_root.mkdir(parents=True, exist_ok=True)
        
        async with websockets.serve(self.handle_connection, host, port):
            logging.info("🎉 Bridge server running - ready for Manus + Cursor collaboration!")
            logging.info(f"📁 Project root: {self.project_root}")
            logging.info(f"🔗 WebSocket URL: ws://{host}:{port}")
            logging.info("🎯 Goal: Get cherry-ai.me working with enhanced interface")
            await asyncio.Future()
    
    async def handle_connection(self, websocket, path):
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        logging.info(f"🔌 New connection from {client_ip}")
        
        try:
            # Authenticate client
            auth_message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            auth_data = json.loads(auth_message)
            
            client = auth_data.get("client")
            token = auth_data.get("token")
            
            if client == "manus" and token == "manus_live_collab_2024":
                self.manus_connection = websocket
                await websocket.send(json.dumps({
                    "status": "authenticated", 
                    "client_type": "manus",
                    "message": "Welcome Manus! Cherry AI live collaboration ready.",
                    "server": "45.32.69.157",
                    "goal": "Deploy enhanced interface to cherry-ai.me"
                }))
                logging.info("🤖 Manus connected to live collaboration bridge")
                
            elif client == "cursor" and token == "cursor_live_collab_2024":
                self.cursor_connection = websocket
                await websocket.send(json.dumps({
                    "status": "authenticated", 
                    "client_type": "cursor",
                    "message": "Welcome Cursor AI! Ready for live collaboration.",
                    "server": "45.32.69.157", 
                    "goal": "Deploy enhanced interface to cherry-ai.me"
                }))
                logging.info("💻 Cursor AI connected to live collaboration bridge")
                
            else:
                await websocket.send(json.dumps({
                    "status": "authentication_failed",
                    "message": "Invalid credentials"
                }))
                await websocket.close()
                return
            
            self.connected_clients.add(websocket)
            await self.send_current_state(websocket)
            await self.handle_messages(websocket)
            
        except websockets.exceptions.ConnectionClosed:
            logging.info(f"🔌 Client {client_ip} disconnected")
        except Exception as e:
            logging.error(f"❌ Error handling connection: {e}")
        finally:
            self.connected_clients.discard(websocket)
            if websocket == self.manus_connection:
                self.manus_connection = None
                logging.info("🤖 Manus disconnected")
            elif websocket == self.cursor_connection:
                self.cursor_connection = None
                logging.info("💻 Cursor AI disconnected")
    
    async def send_current_state(self, websocket):
        """Send current project state to newly connected client"""
        state_message = {
            "type": "initial_state",
            "shared_state": self.shared_state,
            "project_files": await self.get_project_files(),
            "connected_clients": {
                "manus": self.manus_connection is not None,
                "cursor": self.cursor_connection is not None
            },
            "server_info": {
                "hostname": os.uname().nodename,
                "working_directory": str(self.project_root),
                "cherry_ai_status": await self.check_cherry_ai_status()
            },
            "timestamp": time.time()
        }
        await websocket.send(json.dumps(state_message))
    
    async def handle_messages(self, websocket):
        """Handle incoming messages from clients"""
        async for message in websocket:
            try:
                data = json.loads(message)
                await self.process_message(data, websocket)
            except Exception as e:
                logging.error(f"Error processing message: {e}")
    
    async def process_message(self, data, websocket):
        """Process different types of messages"""
        message_type = data.get("type")
        client_type = "manus" if websocket == self.manus_connection else "cursor"
        
        logging.info(f"📨 Received {message_type} from {client_type}")
        
        if message_type == "execute_command":
            await self.handle_command_execution(data, websocket, client_type)
        elif message_type == "file_change":
            await self.handle_file_change(data, client_type)
        elif message_type == "sync_request":
            await self.send_current_state(websocket)
        elif message_type == "task_update":
            await self.handle_task_update(data, client_type)
        elif message_type == "deploy_request":
            await self.handle_deploy_request(data, websocket, client_type)
    
    async def handle_command_execution(self, data, websocket, client_type):
        """Execute shell commands and return results"""
        command = data.get("command")
        working_dir = data.get("working_dir", str(self.project_root))
        timeout = data.get("timeout", 30)
        
        if not command:
            await websocket.send(json.dumps({
                "type": "command_result",
                "error": "No command provided",
                "return_code": -1
            }))
            return
        
        logging.info(f"⚡ Executing command from {client_type}: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            response = {
                "type": "command_result",
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "executed_by": client_type,
                "working_dir": working_dir,
                "timestamp": time.time()
            }
            
            await websocket.send(json.dumps(response))
            
            # Notify other client about command execution
            if result.returncode == 0:
                await self.broadcast_to_others({
                    "type": "command_executed",
                    "command": command,
                    "executed_by": client_type,
                    "success": True
                }, client_type)
            
        except subprocess.TimeoutExpired:
            error_response = {
                "type": "command_result",
                "command": command,
                "error": f"Command timed out after {timeout} seconds",
                "return_code": -1,
                "timestamp": time.time()
            }
            await websocket.send(json.dumps(error_response))
            
        except Exception as e:
            error_response = {
                "type": "command_result",
                "command": command,
                "error": str(e),
                "return_code": -1,
                "timestamp": time.time()
            }
            await websocket.send(json.dumps(error_response))
    
    async def handle_file_change(self, data, client_type):
        """Handle file changes and sync between clients"""
        file_path = data.get("file_path")
        content = data.get("content")
        change_type = data.get("change_type", "modify")
        
        if not file_path:
            return
        
        full_path = self.project_root / file_path
        
        try:
            if change_type in ["modify", "create"]:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding='utf-8')
                logging.info(f"📝 File {change_type}: {file_path} by {client_type}")
            elif change_type == "delete":
                if full_path.exists():
                    full_path.unlink()
                    logging.info(f"🗑️ File deleted: {file_path} by {client_type}")
        except Exception as e:
            logging.error(f"Error updating file {file_path}: {e}")
            return
        
        # Notify other client about file change
        notification = {
            "type": "file_changed",
            "file_path": file_path,
            "content": content if change_type != "delete" else None,
            "change_type": change_type,
            "changed_by": client_type,
            "timestamp": time.time()
        }
        await self.broadcast_to_others(notification, client_type)
    
    async def handle_task_update(self, data, client_type):
        """Handle task status updates"""
        task = data.get("task")
        status = data.get("status")
        
        self.shared_state["current_task"] = {
            "task": task,
            "status": status,
            "assigned_to": client_type,
            "timestamp": time.time()
        }
        
        notification = {
            "type": "task_updated",
            "task": task,
            "status": status,
            "assigned_to": client_type,
            "timestamp": time.time()
        }
        await self.broadcast_to_others(notification, client_type)
    
    async def handle_deploy_request(self, data, websocket, client_type):
        """Handle deployment requests"""
        deploy_type = data.get("deploy_type", "enhanced_interface")
        
        if deploy_type == "enhanced_interface":
            # Deploy enhanced interface to cherry-ai.me
            commands = [
                "cd /var/www/cherry-ai",
                "git pull origin main",
                "cp admin-interface/enhanced-production-interface.html /var/www/html/index.html",
                "systemctl reload nginx",
                "systemctl status nginx"
            ]
            
            for command in commands:
                await self.handle_command_execution({
                    "command": command,
                    "working_dir": "/var/www/cherry-ai"
                }, websocket, client_type)
    
    async def get_project_files(self):
        """Get list of project files"""
        files = []
        try:
            for file_path in self.project_root.rglob("*"):
                if file_path.is_file():
                    # Skip hidden files and common ignore patterns
                    if any(part.startswith('.') for part in file_path.parts):
                        continue
                    if any(ignore in str(file_path) for ignore in ['__pycache__', 'node_modules', '.git']):
                        continue
                    
                    relative_path = file_path.relative_to(self.project_root)
                    files.append({
                        "path": str(relative_path),
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime
                    })
        except Exception as e:
            logging.error(f"Error getting project files: {e}")
        return files
    
    async def check_cherry_ai_status(self):
        """Check current Cherry AI deployment status"""
        try:
            # Check if enhanced interface exists
            enhanced_interface = Path("/var/www/cherry-ai/admin-interface/enhanced-production-interface.html")
            current_index = Path("/var/www/html/index.html")
            
            status = {
                "enhanced_interface_exists": enhanced_interface.exists(),
                "current_index_exists": current_index.exists(),
                "nginx_running": False,
                "domain_accessible": False
            }
            
            # Check nginx status
            try:
                result = subprocess.run("systemctl is-active nginx", shell=True, capture_output=True, text=True)
                status["nginx_running"] = result.returncode == 0
            except:
                pass
            
            return status
        except Exception as e:
            logging.error(f"Error checking Cherry AI status: {e}")
            return {"error": str(e)}
    
    async def broadcast_to_others(self, message, sender_type):
        """Broadcast message to other connected clients"""
        message_json = json.dumps(message)
        
        for client in self.connected_clients:
            if (sender_type == "manus" and client == self.cursor_connection) or \
               (sender_type == "cursor" and client == self.manus_connection):
                try:
                    await client.send(message_json)
                except Exception as e:
                    logging.error(f"Error broadcasting to client: {e}")

if __name__ == "__main__":
    bridge = CherryAILiveCollaborationBridge()
    try:
        asyncio.run(bridge.start_server())
    except KeyboardInterrupt:
        logging.info("🛑 Cherry AI Live Collaboration Bridge stopped")

