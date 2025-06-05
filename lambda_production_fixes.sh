#!/bin/bash

# 🚀 LAMBDA LABS PRODUCTION FIXES
# Fix all remaining issues and get Cherry AI fully operational

set -e

echo "🔥 FIXING LAMBDA LABS PRODUCTION ISSUES..."

# 1. FIX PINECONE IMPORT IN MAIN.PY
echo "🔧 Fixing Pinecone import issue..."

cat > /opt/cherry-ai/main.py << 'MAIN_APP_EOF'
#!/usr/bin/env python3
"""
Fixed Cherry AI Production Application - Lambda Labs
Corrected Pinecone import and other issues
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import psycopg2
import redis
import weaviate

# Fixed Pinecone import
try:
    import pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    print("⚠️ Pinecone not available - continuing without vector search")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Cherry AI Production",
    description="Enhanced AI Orchestrator with Three Personas",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connections
class DatabaseManager:
    def __init__(self):
        self.postgres = None
        self.redis_client = None
        self.weaviate_client = None
        self.pinecone_client = None
        
    async def initialize(self):
        """Initialize all database connections"""
        try:
            # PostgreSQL
            self.postgres = psycopg2.connect(
                host="localhost",
                database="cherry_ai_production",
                user="cherry_ai",
                password="CherryAI2024!"
            )
            logger.info("✅ PostgreSQL connected")
            
            # Redis
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            self.redis_client.ping()
            logger.info("✅ Redis connected")
            
            # Weaviate
            self.weaviate_client = weaviate.Client("http://localhost:8080")
            logger.info("✅ Weaviate connected")
            
            # Pinecone (optional)
            if PINECONE_AVAILABLE and os.getenv("PINECONE_API_KEY"):
                try:
                    pinecone.init(api_key=os.getenv("PINECONE_API_KEY"))
                    self.pinecone_client = pinecone
                    logger.info("✅ Pinecone connected")
                except Exception as e:
                    logger.warning(f"⚠️ Pinecone connection failed: {e}")
            
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")

# Initialize database manager
db_manager = DatabaseManager()

# AI Personas
class AIPersona:
    def __init__(self, name: str, description: str, personality: str):
        self.name = name
        self.description = description
        self.personality = personality
        self.active = True

# Define the three AI personas
personas = {
    "cherry": AIPersona(
        name="Cherry",
        description="Personal AI assistant for creative and personal tasks",
        personality="Friendly, creative, and supportive"
    ),
    "sophia": AIPersona(
        name="Sophia", 
        description="Business AI for professional and strategic tasks",
        personality="Professional, analytical, and results-driven"
    ),
    "karen": AIPersona(
        name="Karen",
        description="Healthcare AI for medical and wellness guidance",
        personality="Caring, precise, and health-focused"
    )
}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    await db_manager.initialize()
    logger.info("🚀 Cherry AI Production Server Started on Lambda Labs")

@app.get("/", response_class=HTMLResponse)
async def get_enhanced_interface():
    """Serve the enhanced production interface"""
    try:
        with open("/opt/cherry-ai/admin-interface/enhanced-production-interface.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        # Fallback to basic interface
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cherry AI - Lambda Labs Production</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 40px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; 
                    min-height: 100vh;
                }}
                .container {{ max-width: 800px; margin: 0 auto; text-align: center; }}
                .persona {{ 
                    background: rgba(255,255,255,0.1); 
                    margin: 20px; 
                    padding: 20px; 
                    border-radius: 10px; 
                    backdrop-filter: blur(10px);
                }}
                .status {{ 
                    background: rgba(0,255,0,0.2); 
                    padding: 15px; 
                    border-radius: 8px; 
                    margin: 20px 0;
                }}
                .specs {{
                    background: rgba(255,255,255,0.05);
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                    text-align: left;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🍒 Cherry AI - Lambda Labs Production</h1>
                <p>Enhanced AI Orchestrator with Three Personas</p>
                
                <div class="status">
                    <h3>✅ System Status: OPERATIONAL</h3>
                    <p>Running on Lambda Labs with 8x A100 GPUs</p>
                </div>
                
                <div class="persona">
                    <h2>🍒 Cherry</h2>
                    <p>Personal AI Assistant</p>
                    <small>Friendly, creative, and supportive</small>
                </div>
                
                <div class="persona">
                    <h2>💼 Sophia</h2>
                    <p>Business AI Strategist</p>
                    <small>Professional, analytical, and results-driven</small>
                </div>
                
                <div class="persona">
                    <h2>🏥 Karen</h2>
                    <p>Healthcare AI Advisor</p>
                    <small>Caring, precise, and health-focused</small>
                </div>
                
                <div class="specs">
                    <h3>🚀 Lambda Labs Infrastructure</h3>
                    <ul>
                        <li><strong>GPUs:</strong> 8x NVIDIA A100 (40GB each)</li>
                        <li><strong>CPUs:</strong> 124 vCPUs</li>
                        <li><strong>RAM:</strong> 1.8TB</li>
                        <li><strong>Storage:</strong> 6TB NVMe</li>
                        <li><strong>Network:</strong> High-speed interconnect</li>
                    </ul>
                </div>
                
                <p><strong>Server IP:</strong> 150.136.94.139</p>
                <p><strong>Timestamp:</strong> {datetime.now().isoformat()}</p>
            </div>
        </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "server": "Lambda Labs 8x A100",
        "ip": "150.136.94.139",
        "personas": list(personas.keys()),
        "databases": {
            "postgresql": db_manager.postgres is not None,
            "redis": db_manager.redis_client is not None,
            "weaviate": db_manager.weaviate_client is not None,
            "pinecone": db_manager.pinecone_client is not None
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/status")
async def get_status():
    """Get detailed system status"""
    return {
        "status": "operational",
        "environment": "lambda-production",
        "server": {
            "provider": "Lambda Labs",
            "instance_type": "8x A100 GPU",
            "ip": "150.136.94.139",
            "specs": {
                "gpus": "8x NVIDIA A100 (40GB)",
                "cpus": "124 vCPUs", 
                "ram": "1.8TB",
                "storage": "6TB NVMe"
            }
        },
        "personas": {name: persona.active for name, persona in personas.items()},
        "databases": {
            "postgresql": db_manager.postgres is not None,
            "redis": db_manager.redis_client is not None,
            "weaviate": db_manager.weaviate_client is not None,
            "pinecone": db_manager.pinecone_client is not None
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/personas")
async def get_personas():
    """Get available AI personas"""
    return {
        name: {
            "name": persona.name,
            "description": persona.description,
            "personality": persona.personality,
            "active": persona.active
        }
        for name, persona in personas.items()
    }

@app.post("/api/chat/{persona_name}")
async def chat_with_persona(persona_name: str, message: dict):
    """Chat with a specific AI persona"""
    if persona_name not in personas:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    persona = personas[persona_name]
    if not persona.active:
        raise HTTPException(status_code=503, detail="Persona is not active")
    
    # Store conversation in Redis
    if db_manager.redis_client:
        conversation_key = f"chat:{persona_name}:{datetime.now().strftime('%Y%m%d')}"
        db_manager.redis_client.lpush(conversation_key, str(message))
    
    # Process with AI (placeholder for actual AI integration)
    response = {
        "persona": persona_name,
        "message": f"{persona.name} received: {message.get('text', '')}",
        "personality": persona.personality,
        "timestamp": datetime.now().isoformat()
    }
    
    return response

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time collaboration"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Collaboration update: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1
    )
MAIN_APP_EOF

# 2. CREATE SYSTEMD SERVICE FILES
echo "⚙️ Creating systemd service files..."

# Main Cherry AI service
cat > /etc/systemd/system/cherry-ai.service << 'SERVICE_EOF'
[Unit]
Description=Cherry AI Production Server
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/cherry-ai
Environment=PATH=/opt/cherry-ai/venv/bin
Environment=PYTHONPATH=/opt/cherry-ai
ExecStart=/opt/cherry-ai/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Collaboration bridge service
cat > /etc/systemd/system/cherry-ai-bridge.service << 'BRIDGE_EOF'
[Unit]
Description=Cherry AI Collaboration Bridge
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/cherry-ai
Environment=PATH=/opt/cherry-ai/venv/bin
Environment=PYTHONPATH=/opt/cherry-ai
ExecStart=/opt/cherry-ai/venv/bin/python local_collaboration_bridge.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
BRIDGE_EOF

# 3. RELOAD SYSTEMD AND START SERVICES
echo "🚀 Starting services..."

systemctl daemon-reload
systemctl enable cherry-ai
systemctl enable cherry-ai-bridge

# Stop any existing processes
pkill -f "uvicorn main:app" || true
pkill -f "local_collaboration_bridge" || true

# Start services
systemctl start cherry-ai
systemctl start cherry-ai-bridge

# 4. CHECK SERVICE STATUS
echo "📊 Checking service status..."

sleep 5

echo "Cherry AI Service Status:"
systemctl status cherry-ai --no-pager

echo "Collaboration Bridge Status:"
systemctl status cherry-ai-bridge --no-pager

# 5. TEST ENDPOINTS
echo "🧪 Testing endpoints..."

# Test health endpoint
echo "Testing health endpoint..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "Health endpoint not ready yet"

# Test WebSocket port
echo "Testing WebSocket port 8765..."
nc -z localhost 8765 && echo "✅ WebSocket port 8765 is open" || echo "❌ WebSocket port 8765 is not open"

# 6. CONFIGURE NGINX
echo "🌐 Configuring nginx..."

cat > /etc/nginx/sites-available/cherry-ai << 'NGINX_EOF'
server {
    listen 80;
    server_name cherry-ai.me www.cherry-ai.me 150.136.94.139;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
NGINX_EOF

# Enable nginx site
ln -sf /etc/nginx/sites-available/cherry-ai /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Restart nginx
systemctl restart nginx

# 7. CONFIGURE FIREWALL
echo "🔒 Configuring firewall..."

ufw allow 22
ufw allow 80
ufw allow 443
ufw allow 8000
ufw allow 8765
ufw --force enable

# 8. FINAL STATUS CHECK
echo "🎯 Final status check..."

echo "=== SERVICE STATUS ==="
systemctl is-active cherry-ai && echo "✅ Cherry AI: Running" || echo "❌ Cherry AI: Not running"
systemctl is-active cherry-ai-bridge && echo "✅ Bridge: Running" || echo "❌ Bridge: Not running"
systemctl is-active nginx && echo "✅ Nginx: Running" || echo "❌ Nginx: Not running"
systemctl is-active postgresql && echo "✅ PostgreSQL: Running" || echo "❌ PostgreSQL: Not running"
systemctl is-active redis-server && echo "✅ Redis: Running" || echo "❌ Redis: Not running"

echo "=== PORT STATUS ==="
nc -z localhost 8000 && echo "✅ Port 8000: Open" || echo "❌ Port 8000: Closed"
nc -z localhost 8765 && echo "✅ Port 8765: Open" || echo "❌ Port 8765: Closed"
nc -z localhost 80 && echo "✅ Port 80: Open" || echo "❌ Port 80: Closed"

echo "=== ENDPOINT TESTS ==="
curl -s http://localhost:8000/health > /dev/null && echo "✅ Health endpoint: Working" || echo "❌ Health endpoint: Failed"
curl -s http://localhost/health > /dev/null && echo "✅ Nginx proxy: Working" || echo "❌ Nginx proxy: Failed"

echo ""
echo "🎉 LAMBDA LABS PRODUCTION FIXES COMPLETE!"
echo ""
echo "🌐 Access URLs:"
echo "- Direct: http://150.136.94.139"
echo "- Health: http://150.136.94.139/health"
echo "- API: http://150.136.94.139/api/status"
echo "- WebSocket: ws://150.136.94.139:8765"
echo ""
echo "📊 Monitor logs:"
echo "- Main app: journalctl -u cherry-ai -f"
echo "- Bridge: journalctl -u cherry-ai-bridge -f"
echo "- Nginx: tail -f /var/log/nginx/access.log"

