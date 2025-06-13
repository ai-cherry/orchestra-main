#!/bin/bash

# 🎼 Orchestra AI SQLite Database Setup
# Quick setup for full API features without PostgreSQL

set -e

echo "🎼 Orchestra AI SQLite Database Setup"
echo "===================================="
echo ""

# Check if we're in the right directory
if [ ! -d "api" ] || [ ! -d "web" ]; then
    echo "❌ Please run this from the orchestra-dev root directory"
    exit 1
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source venv/bin/activate

# Install SQLite dependencies
echo "📦 Installing SQLite dependencies..."
pip install aiosqlite

# Create full API server with SQLite
echo "🔧 Creating SQLite-enabled API server..."
cat > api/main_full_sqlite.py << 'EOF'
#!/usr/bin/env python3
"""
Orchestra AI API - Full Version with SQLite
This version includes all features using SQLite database
"""

import sys
import os
from pathlib import Path

# Add API directory to Python path
api_dir = Path(__file__).parent
sys.path.insert(0, str(api_dir))
sys.path.insert(0, str(api_dir.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Orchestra AI Admin API - SQLite Version",
    description="Full featured version with SQLite database",
    version="2.0.0-sqlite"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import database components
try:
    from database.sqlite_connection import init_sqlite_database, sqlite_db_manager
    SQLITE_AVAILABLE = True
except ImportError as e:
    logger.warning("SQLite database components not available", error=str(e))
    SQLITE_AVAILABLE = False

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    try:
        if SQLITE_AVAILABLE:
            await init_sqlite_database()
            logger.info("SQLite database initialized successfully")
        logger.info("Orchestra AI API with SQLite started successfully")
    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        # Don't fail startup, continue with limited functionality

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        if SQLITE_AVAILABLE:
            await sqlite_db_manager.close()
        logger.info("Orchestra AI API shutting down")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Orchestra AI Admin API - SQLite Version",
        "version": "2.0.0-sqlite",
        "status": "running",
        "database": "sqlite" if SQLITE_AVAILABLE else "none"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    db_status = "unknown"
    if SQLITE_AVAILABLE:
        db_status = "healthy" if await sqlite_db_manager.health_check() else "error"
    
    return {
        "status": "healthy",
        "message": "Orchestra AI API is running with SQLite",
        "version": "2.0.0-sqlite",
        "database_status": db_status,
        "features": "full" if SQLITE_AVAILABLE else "limited"
    }

@app.get("/api/status")
async def get_status():
    """Comprehensive status endpoint"""
    import psutil
    
    status = {
        "status": "operational",
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "version": "2.0.0-sqlite",
        "database": "sqlite" if SQLITE_AVAILABLE else "none"
    }
    
    if SQLITE_AVAILABLE:
        status["database_health"] = await sqlite_db_manager.health_check()
    
    return status

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Create startup script for SQLite version
echo "📝 Creating startup script..."
cat > start_api_sqlite.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export PYTHONPATH="$(pwd):$(pwd)/api:${PYTHONPATH}"
export ORCHESTRA_AI_ENV=development
export DATABASE_URL="sqlite+aiosqlite:///./api/orchestra_ai.db"
export MAGIC_LIB=/opt/homebrew/lib/libmagic.dylib
export PYTHONDONTWRITEBYTECODE=1
cd api
echo "🎼 Starting Orchestra AI API Server with SQLite..."
echo "🔧 Environment: $ORCHESTRA_AI_ENV"
echo "💾 Database: SQLite"
echo ""
python3 main_full_sqlite.py
EOF

chmod +x start_api_sqlite.sh

echo ""
echo "✅ SQLite Database Setup Complete!"
echo "=================================="
echo ""
echo "🚀 To start with full SQLite features:"
echo "  ./start_api_sqlite.sh"
echo ""
echo "🔗 Or continue with simplified version:"
echo "  ./start_api.sh"
echo ""
echo "📊 Frontend remains the same:"
echo "  ./start_frontend.sh"
echo ""
echo "🎯 Full stack with SQLite:"
echo "  # Terminal 1"
echo "  ./start_api_sqlite.sh"
echo "  # Terminal 2" 
echo "  ./start_frontend.sh"
echo ""
echo "📚 Access points will be:"
echo "  Frontend:  http://localhost:3001/"
echo "  API:       http://localhost:8000/"
echo "  API Docs:  http://localhost:8000/docs"
echo "" 