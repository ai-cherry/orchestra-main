#!/bin/bash
# Cherry AI Collaboration Bridge - Quick Deploy
# Copy and paste this into Vultr console

echo "🚀 Deploying Cherry AI Live Collaboration Bridge..."

# Create directories
mkdir -p /var/www/cherry-ai
cd /var/www/cherry-ai

# Create the collaboration bridge server
cat > cherry_ai_live_collaboration_bridge.py << 'EOF'
import asyncio
import websockets
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CherryAILiveCollaborationBridge:
    def __init__(self):
        self.clients = {}
        self.manus_client = None
        self.cursor_clients = []
        
    async def handle_client(self, websocket):
        """Handle incoming WebSocket connections"""
        try:
            # Get client info
            client_info = await websocket.recv()
            client_data = json.loads(client_info)
            
            client_type = client_data.get("client", "unknown")
            logger.info(f"Client connected: {client_type}")
            
            # Authenticate
            if client_data.get("token") == "cursor_live_collab_2024":
                auth_response = {
                    "status": "authenticated",
                    "message": f"Welcome {client_type}!",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(auth_response))
                
                # Store client
                if client_type == "manus":
                    self.manus_client = websocket
                elif client_type == "cursor":
                    self.cursor_clients.append(websocket)
                
                # Handle messages
                async for message in websocket:
                    data = json.loads(message)
                    logger.info(f"Received from {client_type}: {data}")
                    
                    # Broadcast to other clients
                    broadcast_data = {
                        "from": client_type,
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Send to Manus if from Cursor
                    if client_type == "cursor" and self.manus_client:
                        await self.manus_client.send(json.dumps(broadcast_data))
                    
                    # Send to Cursor clients if from Manus
                    elif client_type == "manus":
                        for cursor in self.cursor_clients:
                            await cursor.send(json.dumps(broadcast_data))
                            
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_type}")
            if client_type == "manus":
                self.manus_client = None
            elif client_type == "cursor" and websocket in self.cursor_clients:
                self.cursor_clients.remove(websocket)
        except Exception as e:
            logger.error(f"Error: {e}")
    
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info("Starting Cherry AI Live Collaboration Bridge on port 8765")
        async with websockets.serve(self.handle_client, "0.0.0.0", 8765):
            await asyncio.Future()  # run forever

if __name__ == "__main__":
    bridge = CherryAILiveCollaborationBridge()
    asyncio.run(bridge.start_server())
EOF

# Install dependencies
apt-get update -y
apt-get install -y python3-pip python3-venv
python3 -m pip install websockets

# Create systemd service
cat > /etc/systemd/system/cherry-collab.service << 'EOF'
[Unit]
Description=Cherry AI Live Collaboration Bridge
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/cherry-ai
ExecStart=/usr/bin/python3 /var/www/cherry-ai/cherry_ai_live_collaboration_bridge.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure firewall
ufw allow 8765/tcp
ufw reload

# Start service
systemctl daemon-reload
systemctl enable cherry-collab.service
systemctl start cherry-collab.service

# Check status
sleep 2
systemctl status cherry-collab.service

echo "✅ Deployment complete!"
echo "🔗 WebSocket server running on ws://45.32.69.157:8765"
echo "🌐 Cherry AI admin interface at https://cherry-ai.me" 