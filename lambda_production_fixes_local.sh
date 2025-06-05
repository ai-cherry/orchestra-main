#!/bin/bash
# 🚀 Lambda Labs Production Fixes Script
# Fixes all identified issues and gets Cherry AI running

set -e
echo "🔧 Applying Lambda Labs Production Fixes..."

# Fix 1: Update main.py with proper Pinecone import
echo "📝 Fixing main.py imports..."
cat > /opt/cherry-ai/main.py << 'EOF'
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import redis
import weaviate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Cherry AI Production API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connections
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cherry_ai:CherryAI2024!@localhost/cherry_ai_production")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")

# Initialize connections
try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("✅ PostgreSQL connected")
except Exception as e:
    logger.error(f"PostgreSQL connection failed: {e}")

try:
    redis_client = redis.from_url(REDIS_URL)
    redis_client.ping()
    logger.info("✅ Redis connected")
except Exception as e:
    logger.error(f"Redis connection failed: {e}")

try:
    weaviate_client = weaviate.Client(WEAVIATE_URL)
    logger.info("✅ Weaviate connected")
except Exception as e:
    logger.error(f"Weaviate connection failed: {e}")

# Optional Pinecone integration
pinecone_available = False
try:
    import pinecone
    # Only initialize if API key is provided
    if os.getenv("PINECONE_API_KEY"):
        pinecone.init(api_key=os.getenv("PINECONE_API_KEY"))
        pinecone_available = True
        logger.info("✅ Pinecone initialized")
except ImportError:
    logger.warning("Pinecone not available - install pinecone-client if needed")
except Exception as e:
    logger.warning(f"Pinecone initialization skipped: {e}")

@app.get("/")
async def root():
    return {
        "message": "Cherry AI Production API",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "api_status": "/api/status",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "cherry-ai",
        "version": "1.0.0",
        "instance": "lambda-labs-production"
    }

@app.get("/api/status")
async def api_status():
    status = {
        "api": "operational",
        "database": {
            "postgresql": False,
            "redis": False,
            "weaviate": False,
            "pinecone": pinecone_available
        }
    }
    
    # Check PostgreSQL
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        status["database"]["postgresql"] = True
    except:
        pass
    
    # Check Redis
    try:
        redis_client.ping()
        status["database"]["redis"] = True
    except:
        pass
    
    # Check Weaviate
    try:
        weaviate_client.schema.get()
        status["database"]["weaviate"] = True
    except:
        pass
    
    return status

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
EOF

# Fix 2: Create systemd service for Cherry AI
echo "⚙️ Creating cherry-ai.service..."
cat > /etc/systemd/system/cherry-ai.service << 'EOF'
[Unit]
Description=Cherry AI Production Service
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/cherry-ai
Environment="PATH=/opt/cherry-ai/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="DATABASE_URL=postgresql://cherry_ai:CherryAI2024!@localhost/cherry_ai_production"
Environment="REDIS_URL=redis://localhost:6379"
Environment="WEAVIATE_URL=http://localhost:8080"
ExecStart=/opt/cherry-ai/venv/bin/python /opt/cherry-ai/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Fix 3: Create systemd service for Collaboration Bridge
echo "⚙️ Creating cherry-ai-bridge.service..."
cat > /etc/systemd/system/cherry-ai-bridge.service << 'EOF'
[Unit]
Description=Cherry AI Collaboration Bridge
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/cherry-ai
Environment="PATH=/opt/cherry-ai/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/cherry-ai/venv/bin/python /opt/cherry-ai/cherry_ai_live_collaboration_bridge.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Fix 4: Update Nginx configuration
echo "🌐 Configuring Nginx..."
cat > /etc/nginx/sites-available/cherry-ai << 'EOF'
server {
    listen 80;
    server_name cherry-ai.me www.cherry-ai.me 150.136.94.139;

    # Main application
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket for collaboration bridge
    location /ws {
        proxy_pass http://localhost:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable nginx site
ln -sf /etc/nginx/sites-available/cherry-ai /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Fix 5: Configure firewall
echo "🔥 Configuring firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
ufw allow 8765/tcp
ufw --force enable

# Fix 6: Ensure permissions
echo "🔐 Setting permissions..."
chown -R ubuntu:ubuntu /opt/cherry-ai
chown -R ubuntu:ubuntu /var/www/cherry-ai

# Fix 7: Kill any existing processes
echo "🛑 Stopping existing processes..."
pkill -f "python.*main.py" || true
pkill -f "python.*cherry_ai_live" || true

# Fix 8: Reload and start services
echo "🚀 Starting services..."
systemctl daemon-reload
systemctl enable cherry-ai cherry-ai-bridge
systemctl restart cherry-ai
systemctl restart cherry-ai-bridge
systemctl restart nginx
systemctl restart redis-server
systemctl restart postgresql

# Wait for services to start
sleep 5

# Fix 9: Check status
echo "📊 Checking service status..."
echo "=== Cherry AI Service ==="
systemctl status cherry-ai --no-pager | head -n 10
echo ""
echo "=== Collaboration Bridge ==="
systemctl status cherry-ai-bridge --no-pager | head -n 10
echo ""
echo "=== Testing endpoints ==="
curl -s http://localhost:8000/health | jq . || echo "Health check failed"
echo ""

echo "✅ Lambda Labs Production Fixes Complete!"
echo ""
echo "🔗 Access points:"
echo "   Main App: http://150.136.94.139"
echo "   Health: http://150.136.94.139/health"
echo "   API Status: http://150.136.94.139/api/status"
echo "   WebSocket: ws://150.136.94.139:8765"
echo ""
echo "📋 Check logs with:"
echo "   journalctl -u cherry-ai -f"
echo "   journalctl -u cherry-ai-bridge -f" 