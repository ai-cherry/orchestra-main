#!/usr/bin/env python3
"""
Cherry AI - Functional Interface with MCP Integration
Connects to Orchestra MCP servers for real functionality
"""

import asyncio
import json
import os
import aiohttp
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Cherry AI Interface",
    description="MCP-Powered AI Interface",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MCP Server URLs
MCP_MEMORY_URL = "http://localhost:8003"
MCP_TOOLS_URL = "http://localhost:8006"

# Personas
PERSONAS = {
    "cherry": {
        "name": "Cherry",
        "description": "Creative AI assistant for personal tasks",
        "personality": "Friendly, creative, and supportive",
        "color": "#ff6b9d",
        "icon": "🍒"
    },
    "sophia": {
        "name": "Sophia", 
        "description": "Business AI for professional tasks",
        "personality": "Professional, analytical, results-driven",
        "color": "#4ecdc4",
        "icon": "💼"
    },
    "karen": {
        "name": "Karen",
        "description": "Healthcare AI for wellness guidance",
        "personality": "Caring, precise, health-focused",
        "color": "#45b7d1",
        "icon": "🏥"
    }
}

class MCPClient:
    """Client for communicating with MCP servers"""
    
    async def call_mcp_tool(self, server_url: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on an MCP server"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "tool": tool_name,
                    "arguments": arguments
                }
                async with session.post(f"{server_url}/tools/call", json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"MCP server error: {response.status}"}
        except Exception as e:
            return {"error": f"Failed to connect to MCP server: {str(e)}"}
    
    async def store_conversation(self, session_id: str, agent_id: str, message: str, role: str) -> Dict[str, Any]:
        """Store conversation in memory server"""
        return await self.call_mcp_tool(MCP_MEMORY_URL, "store_conversation", {
            "session_id": session_id,
            "agent_id": agent_id,
            "message": message,
            "role": role
        })
    
    async def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get conversation history from memory server"""
        result = await self.call_mcp_tool(MCP_MEMORY_URL, "get_conversation_history", {
            "session_id": session_id,
            "limit": limit
        })
        return result.get("messages", [])
    
    async def search_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search knowledge base"""
        result = await self.call_mcp_tool(MCP_MEMORY_URL, "search_knowledge", {
            "query": query,
            "limit": limit
        })
        return result.get("results", [])

# Initialize MCP client
mcp = MCPClient()

@app.get("/")
async def home():
    """Serve the main Cherry interface"""
    return FileResponse("/var/www/cherry-ai/index.html")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    # Check MCP server health
    mcp_status = {}
    try:
        async with aiohttp.ClientSession() as session:
            # Test memory server
            async with session.get(f"{MCP_MEMORY_URL}/health") as response:
                mcp_status["memory"] = response.status == 200
    except:
        mcp_status["memory"] = False
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test tools server  
            async with session.get(f"{MCP_TOOLS_URL}/health") as response:
                mcp_status["tools"] = response.status == 200
    except:
        mcp_status["tools"] = False
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "mcp_servers": mcp_status,
        "personas": list(PERSONAS.keys())
    }

@app.get("/api/personas")
async def get_personas():
    """Get available personas"""
    return {"personas": PERSONAS}

@app.post("/api/chat/{persona_name}")
async def chat_with_persona(persona_name: str, request: Dict[str, Any]):
    """Chat with a persona using MCP memory"""
    if persona_name not in PERSONAS:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    message = request.get("message", "")
    session_id = request.get("session_id", f"session_{int(time.time())}")
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    persona = PERSONAS[persona_name]
    
    # Store user message
    await mcp.store_conversation(session_id, persona_name, message, "user")
    
    # Generate AI response based on persona
    ai_response = await generate_persona_response(persona, message, session_id)
    
    # Store AI response
    await mcp.store_conversation(session_id, persona_name, ai_response, "assistant")
    
    return {
        "response": ai_response,
        "persona": persona,
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat()
    }

async def generate_persona_response(persona: Dict[str, Any], message: str, session_id: str) -> str:
    """Generate a response based on persona characteristics"""
    # Get conversation history for context
    history = await mcp.get_conversation_history(session_id, limit=5)
    
    # Simple persona-based responses (you can enhance this with actual LLM integration)
    responses = {
        "cherry": [
            f"That's such a creative question! 🍒 {message} sounds interesting...",
            f"I love your creative energy! Let me think about {message} from an artistic perspective...",
            f"Oh, {message}! That reminds me of something beautiful..."
        ],
        "sophia": [
            f"From a business perspective, {message} presents interesting opportunities...",
            f"Let me analyze {message} strategically for you...",
            f"That's a professional inquiry about {message}. Here's my assessment..."
        ],
        "karen": [
            f"Regarding {message}, I want to ensure we consider the health implications...",
            f"That's important for your wellbeing. About {message}, I recommend...",
            f"From a healthcare standpoint, {message} requires careful consideration..."
        ]
    }
    
    persona_responses = responses.get(persona["name"].lower(), ["I understand your question..."])
    import random
    base_response = random.choice(persona_responses)
    
    # Add context if there's history
    if history:
        base_response += f"\n\nBased on our conversation, I remember we were discussing related topics."
    
    return base_response

@app.get("/api/search")
async def search_content(q: str, limit: int = 10):
    """Search content using MCP knowledge base"""
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    
    # Search knowledge base
    results = await mcp.search_knowledge(q, limit=limit)
    
    return {
        "query": q,
        "results": results,
        "count": len(results),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/status")
async def system_status():
    """Get system status"""
    # Check database connections and MCP servers
    status = {
        "overall": "operational",
        "mcp_servers": {
            "memory": False,
            "tools": False
        },
        "features": {
            "chat": True,
            "search": True,
            "websocket": True,
            "personas": True
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Test MCP connections
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{MCP_MEMORY_URL}/health", timeout=5) as response:
                status["mcp_servers"]["memory"] = response.status == 200
    except:
        pass
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{MCP_TOOLS_URL}/health", timeout=5) as response:
                status["mcp_servers"]["tools"] = response.status == 200
    except:
        pass
    
    return status

# WebSocket for real-time features
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time collaboration"""
    await websocket.accept()
    
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "🍒 Cherry AI WebSocket connected!",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        while True:
            data = await websocket.receive_json()
            
            # Echo back with processing
            response = {
                "type": "response",
                "original": data,
                "processed": f"Cherry AI processed: {data.get('message', 'No message')}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        print("WebSocket disconnected")

if __name__ == "__main__":
    print("🍒 Starting Cherry AI Interface...")
    print("🔗 Connecting to MCP servers:")
    print(f"   Memory: {MCP_MEMORY_URL}")
    print(f"   Tools:  {MCP_TOOLS_URL}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    ) 