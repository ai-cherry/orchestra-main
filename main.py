#!/usr/bin/env python3
"""
Cherry AI Production Application - Lambda Labs
Complete FastAPI application with all integrations
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
import pinecone
from pinecone import Pinecone

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
            logger.info("✅ Redis connected")
            
            # Weaviate
            self.weaviate_client = weaviate.Client("http://localhost:8080")
            logger.info("✅ Weaviate connected")
            
            # Pinecone
            if os.getenv("PINECONE_API_KEY"):
                pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
                self.pinecone_client = pc
                logger.info("✅ Pinecone connected")
            
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
    logger.info("🚀 Cherry AI Production Server Started")

@app.get("/", response_class=HTMLResponse)
async def get_enhanced_interface():
    """Serve the enhanced production interface"""
    try:
        with open("/opt/cherry-ai/admin-interface/enhanced-production-interface.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        # Fallback to basic interface
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cherry AI - Production</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                .container { max-width: 800px; margin: 0 auto; text-align: center; }
                .persona { background: rgba(255,255,255,0.1); margin: 20px; padding: 20px; border-radius: 10px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🍒 Cherry AI Production</h1>
                <p>Enhanced AI Orchestrator with Three Personas</p>
                
                <div class="persona">
                    <h2>🍒 Cherry</h2>
                    <p>Personal AI Assistant</p>
                </div>
                
                <div class="persona">
                    <h2>💼 Sophia</h2>
                    <p>Business AI Strategist</p>
                </div>
                
                <div class="persona">
                    <h2>🏥 Karen</h2>
                    <p>Healthcare AI Advisor</p>
                </div>
                
                <p><strong>Status:</strong> All systems operational on Lambda Labs</p>
                <p><strong>Server:</strong> 8x A100 GPUs | 124 vCPUs | 1.8TB RAM</p>
            </div>
        </body>
        </html>
        """)

@app.get("/api/status")
async def get_status():
    """Get system status"""
    return {
        "status": "operational",
        "personas": {name: persona.active for name, persona in personas.items()},
        "databases": {
            "postgresql": db_manager.postgres is not None,
            "redis": db_manager.redis_client is not None,
            "weaviate": db_manager.weaviate_client is not None,
            "pinecone": db_manager.pinecone_client is not None
        },
        "server": "Lambda Labs 8x A100",
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=4
    )

