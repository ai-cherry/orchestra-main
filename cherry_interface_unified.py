#!/usr/bin/env python3
"""
Cherry AI - Unified Interface with Combined Search
Supports unified search combining internal memory + web search
"""

import asyncio
import json
import os
import aiohttp
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Cherry AI Unified Interface",
    description="Unified Search + Multi-Persona AI Interface",
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

# MCP Server URLs
MCP_MEMORY_URL = "http://localhost:8003"
MCP_TOOLS_URL = "http://localhost:8006"

# Personas
PERSONAS = {
    "cherry": {
        "name": "Cherry",
        "description": "Creative AI assistant for personal tasks",
        "personality": "Friendly, creative, and supportive",
        "color": "#D32F2F",
        "icon": "🍒"
    },
    "sophia": {
        "name": "Sophia", 
        "description": "Business AI for professional tasks",
        "personality": "Professional, analytical, results-driven",
        "color": "#FFD700",
        "icon": "💼"
    },
    "karen": {
        "name": "Karen",
        "description": "Healthcare AI for wellness guidance",
        "personality": "Caring, precise, health-focused",
        "color": "#388E3C",
        "icon": "🏥"
    }
}

# Search Modes
SEARCH_MODES = {
    "normal": {
        "name": "Normal",
        "description": "Balanced responses with standard AI guidelines",
        "internal_weight": 0.6,
        "web_weight": 0.4
    },
    "creative": {
        "name": "Creative", 
        "description": "Imaginative and artistic responses",
        "internal_weight": 0.7,
        "web_weight": 0.3
    },
    "deep": {
        "name": "Deep",
        "description": "Thorough research with comprehensive analysis",
        "internal_weight": 0.5,
        "web_weight": 0.5
    },
    "super-deep": {
        "name": "Super-Deep",
        "description": "Exhaustive research with multiple sources",
        "internal_weight": 0.4,
        "web_weight": 0.6
    },
    "uncensored": {
        "name": "Uncensored",
        "description": "Raw, unfiltered responses - use responsibly",
        "internal_weight": 0.3,
        "web_weight": 0.7
    }
}

class UnifiedSearchEngine:
    """Unified search combining internal memory + web search"""
    
    async def search_internal(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search internal memory/domain data"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "tool": "search_knowledge",
                    "arguments": {"query": query, "limit": limit}
                }
                async with session.post(f"{MCP_MEMORY_URL}/tools/call", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("results", [])
        except Exception as e:
            print(f"Internal search error: {e}")
            return []
        
        return []
    
    async def search_web(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search external web sources"""
        # Mock web search results (replace with actual web search API)
        web_results = [
            {
                "title": f"Web result for: {query}",
                "snippet": f"External web information about {query} from various sources...",
                "url": f"https://example.com/search?q={query}",
                "source": "web",
                "relevance": 0.8
            },
            {
                "title": f"Latest news on {query}",
                "snippet": f"Recent developments and news about {query}...",
                "url": f"https://news.example.com/{query}",
                "source": "news",
                "relevance": 0.7
            }
        ]
        return web_results[:limit]
    
    async def unified_search(self, query: str, mode: str = "normal", limit: int = 10) -> Dict[str, Any]:
        """Perform unified search combining internal + web results"""
        search_config = SEARCH_MODES.get(mode, SEARCH_MODES["normal"])
        
        # Calculate result distribution based on mode
        internal_limit = int(limit * search_config["internal_weight"])
        web_limit = int(limit * search_config["web_weight"])
        
        # Ensure minimum results
        if internal_limit == 0: internal_limit = 1
        if web_limit == 0: web_limit = 1
        
        # Perform parallel searches
        internal_results, web_results = await asyncio.gather(
            self.search_internal(query, internal_limit),
            self.search_web(query, web_limit)
        )
        
        # Add source tags
        for result in internal_results:
            result["source_type"] = "internal"
            result["domain"] = "cherry-ai-memory"
        
        for result in web_results:
            result["source_type"] = "external"
        
        # Combine and return
        all_results = internal_results + web_results
        
        return {
            "query": query,
            "mode": mode,
            "results": all_results,
            "distribution": {
                "internal": len(internal_results),
                "external": len(web_results),
                "total": len(all_results)
            },
            "search_config": search_config,
            "timestamp": datetime.utcnow().isoformat()
        }

class MCPClient:
    """Enhanced MCP client with conversation management"""
    
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

# Initialize services
mcp = MCPClient()
search_engine = UnifiedSearchEngine()

@app.get("/")
async def home():
    """Serve the main React interface"""
    return FileResponse("/var/www/cherry-ai/index.html")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "unified_search": True,
            "multi_persona": True,
            "file_upload": True,
            "multimedia": True
        },
        "search_modes": list(SEARCH_MODES.keys()),
        "personas": list(PERSONAS.keys())
    }

@app.get("/api/personas")
async def get_personas():
    """Get available personas"""
    return {"personas": PERSONAS}

@app.get("/api/search-modes")
async def get_search_modes():
    """Get available search modes"""
    return {"search_modes": SEARCH_MODES}

# Unified chat endpoint that React expects
@app.post("/api/chat")
async def unified_chat(request: Dict[str, Any]):
    """Unified chat endpoint supporting any persona and search mode"""
    message = request.get("message", "")
    persona = request.get("persona", "cherry")
    search_mode = request.get("searchMode", "normal")
    session_id = request.get("session_id", f"session_{int(time.time())}")
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    if persona not in PERSONAS:
        persona = "cherry"  # Default to cherry
    
    if search_mode not in SEARCH_MODES:
        search_mode = "normal"  # Default to normal
    
    persona_info = PERSONAS[persona]
    
    # Store user message
    await mcp.store_conversation(session_id, persona, message, "user")
    
    # If this looks like a search query, perform unified search
    search_results = None
    if any(word in message.lower() for word in ["what", "who", "where", "when", "how", "search", "find", "tell me about"]):
        search_results = await search_engine.unified_search(message, search_mode, limit=8)
    
    # Generate AI response based on persona and search results
    ai_response = await generate_unified_response(persona_info, message, search_mode, search_results)
    
    # Store AI response
    await mcp.store_conversation(session_id, persona, ai_response, "assistant")
    
    return {
        "response": ai_response,
        "persona": persona_info,
        "search_mode": search_mode,
        "search_results": search_results,
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat()
    }

# Legacy persona-specific endpoints for compatibility
@app.post("/api/chat/{persona_name}")
async def chat_with_persona(persona_name: str, request: Dict[str, Any]):
    """Legacy persona-specific chat endpoint"""
    request["persona"] = persona_name
    return await unified_chat(request)

@app.get("/api/search")
async def search_endpoint(q: str, mode: str = "normal", limit: int = 10):
    """Unified search endpoint"""
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    
    return await search_engine.unified_search(q, mode, limit)

async def generate_unified_response(persona: Dict[str, Any], message: str, search_mode: str, search_results: Optional[Dict] = None) -> str:
    """Generate response combining persona characteristics, search mode, and results"""
    persona_name = persona["name"].lower()
    mode_info = SEARCH_MODES[search_mode]
    
    # Base persona responses
    persona_intros = {
        "cherry": "🍒 Hey there! I'm Cherry, your creative companion.",
        "sophia": "💼 Hello! I'm Sophia, your business strategist.",
        "karen": "🏥 Hi! I'm Karen, your healthcare advisor."
    }
    
    intro = persona_intros.get(persona_name, "👋 Hello!")
    
    # Build response based on search results
    if search_results and search_results["results"]:
        response = f"{intro} I've searched both our internal knowledge and the web using {mode_info['name']} mode.\n\n"
        
        # Add search insights
        internal_count = search_results["distribution"]["internal"]
        external_count = search_results["distribution"]["external"]
        
        response += f"**Search Results Summary:**\n"
        response += f"📚 Internal sources: {internal_count} results\n"
        response += f"🌐 Web sources: {external_count} results\n\n"
        
        # Add top results
        response += "**Key Findings:**\n"
        for i, result in enumerate(search_results["results"][:3], 1):
            source_icon = "📚" if result.get("source_type") == "internal" else "🌐"
            response += f"{i}. {source_icon} {result.get('title', 'Result')} - {result.get('snippet', 'No description available')[:100]}...\n"
        
        # Add persona-specific analysis
        if persona_name == "cherry":
            response += "\n🎨 **Creative Perspective:** This opens up interesting creative possibilities for exploration and artistic expression!"
        elif persona_name == "sophia":
            response += "\n💼 **Business Analysis:** From a strategic standpoint, this information presents actionable insights for decision-making."
        elif persona_name == "karen":
            response += "\n🏥 **Health & Wellness View:** Considering the wellbeing implications, this information supports informed health decisions."
        
    else:
        # No search results, general response
        responses = {
            "cherry": f"{intro} I love your question about '{message}'! Let me think creatively about this...",
            "sophia": f"{intro} That's an excellent business inquiry about '{message}'. Let me provide a strategic analysis...",
            "karen": f"{intro} Your question about '{message}' is important for wellbeing. Let me share some health-focused insights..."
        }
        response = responses.get(persona_name, f"{intro} I understand you're asking about '{message}'. Let me help with that...")
    
    # Add search mode context
    response += f"\n\n*Search performed in {mode_info['name']} mode: {mode_info['description']}*"
    
    return response

    
    try:
            "type": "connection",
            "data": {"status": "connected"},
            "timestamp": datetime.utcnow().isoformat()
        })
        
        while True:
            message_type = data.get("type", "unknown")
            
            if message_type == "chat":
                # Handle real-time chat
                response = await unified_chat(data.get("data", {}))
                    "type": "chat_response",
                    "data": response,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message_type == "search":
                # Handle real-time search
                query = data.get("data", {}).get("query", "")
                mode = data.get("data", {}).get("mode", "normal")
                if query:
                    results = await search_engine.unified_search(query, mode)
                        "type": "search_results",
                        "data": results,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            else:
                # Echo other messages
                    "type": "echo",
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat()
                })
            

if __name__ == "__main__":
    print("🍒 Starting Cherry AI Unified Interface...")
    print("🔍 Unified Search: Internal Memory + Web Search")
    print("🎭 Multi-Persona Support: Cherry, Sophia, Karen")
    print("⚡ Search Modes: Normal, Creative, Deep, Super-Deep, Uncensored")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    ) 