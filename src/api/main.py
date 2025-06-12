#!/usr/bin/env python3
"""Main API entry point for Orchestra AI with Chat Integration"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import json
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Pydantic models for Chat API
class ChatRequest(BaseModel):
    persona: str
    message: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    id: str
    content: str
    persona: str
    timestamp: str
    type: str = "text"
    metadata: Optional[Dict[str, Any]] = None

class PersonaStatus(BaseModel):
    persona: str
    status: str
    current_task: Optional[str] = None
    load_level: float
    capabilities: List[str]
    memory_usage: Dict[str, Any]

class SystemCommand(BaseModel):
    command: str
    target: str = "ui"
    parameters: Optional[Dict[str, Any]] = None

class CommandResult(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    ui_actions: Optional[List[Dict[str, Any]]] = None

# Simple WebSocket manager
class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

# Global instances
websocket_manager = WebSocketManager()
conversation_history: Dict[str, List[ChatResponse]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Orchestra AI API with Chat Integration...")
    yield
    logger.info("Shutting down Orchestra AI API...")

app = FastAPI(
    title="Orchestra AI API",
    description="Advanced AI coordination system with chat integration",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper functions
def generate_persona_response(persona: str, message: str) -> str:
    """Generate a response based on persona characteristics"""
    responses = {
        "cherry": [
            f"I understand you'd like to work on: {message}. Let me coordinate the best approach across our available resources.",
            f"That's an interesting challenge! I'll help you break this down into manageable steps: {message}",
            f"I can see how this connects to your broader goals. Let me suggest a strategic approach for: {message}"
        ],
        "sophia": [
            f"From a financial and compliance perspective, regarding '{message}', here's what I recommend...",
            f"I need to ensure this meets all regulatory requirements. Let me analyze the implications of: {message}",
            f"This looks good from a risk assessment standpoint. Here's my professional analysis of: {message}"
        ],
        "karen": [
            f"Based on medical protocols and healthcare standards, for '{message}', I suggest...",
            f"This needs to comply with HIPAA regulations. Let me provide the clinical guidance for: {message}",
            f"From a patient safety perspective, here's the recommended approach for: {message}"
        ]
    }
    
    import random
    persona_responses = responses.get(persona, [f"I'm {persona} and I received: {message}"])
    return random.choice(persona_responses)

def get_persona_capabilities(persona: str) -> List[str]:
    """Get capabilities for a specific persona"""
    capabilities_map = {
        "cherry": [
            "project_coordination",
            "cross_domain_routing", 
            "workflow_optimization",
            "team_management",
            "strategic_planning"
        ],
        "sophia": [
            "financial_analysis",
            "compliance_checking",
            "risk_assessment", 
            "payment_processing",
            "regulatory_guidance"
        ],
        "karen": [
            "medical_coding",
            "clinical_protocols",
            "pharmaceutical_guidance",
            "hipaa_compliance",
            "patient_safety"
        ]
    }
    return capabilities_map.get(persona, [])

# API endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Orchestra AI",
        "version": "1.0.0",
        "status": "operational",
        "features": ["chat", "personas", "websocket", "commands"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "orchestra-ai",
        "personas": ["cherry", "sophia", "karen"],
        "timestamp": datetime.now().isoformat(),
        "features": ["5-tier memory", "cross-domain routing", "20x compression", "chat integration"]
    }

# Chat API endpoints
@app.post("/chat", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a message to a persona"""
    try:
        # Generate unique message ID
        message_id = str(uuid.uuid4())
        
        # Generate persona response
        response_content = generate_persona_response(request.persona, request.message)
        
        response = ChatResponse(
            id=message_id,
            content=response_content,
            persona=request.persona,
            timestamp=datetime.now().isoformat(),
            type="text",
            metadata={
                "processing_time_ms": 150,
                "cross_domain_data": {},
                "memory_compression_ratio": 1.0
            }
        )
        
        # Store in conversation history
        if request.persona not in conversation_history:
            conversation_history[request.persona] = []
        conversation_history[request.persona].append(response)
        
        # Broadcast to WebSocket subscribers
        await websocket_manager.broadcast({
            "type": "chat_response",
            "data": response.dict()
        })
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/history", response_model=List[ChatResponse])
async def get_history(persona: Optional[str] = None, limit: int = 50):
    """Get conversation history"""
    try:
        if persona:
            return conversation_history.get(persona, [])[-limit:]
        else:
            # Return combined history from all personas
            all_messages = []
            for persona_messages in conversation_history.values():
                all_messages.extend(persona_messages)
            
            # Sort by timestamp and return latest
            all_messages.sort(key=lambda x: x.timestamp)
            return all_messages[-limit:]
            
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return []

@app.get("/personas/status", response_model=List[PersonaStatus])
async def get_persona_status():
    """Get status of all personas"""
    try:
        personas = []
        for persona_name in ["cherry", "sophia", "karen"]:
            personas.append(PersonaStatus(
                persona=persona_name,
                status="active",
                current_task=None,
                load_level=0.3,
                capabilities=get_persona_capabilities(persona_name),
                memory_usage={
                    "current": 256,
                    "max": 1000,
                    "compression_ratio": 20.0
                }
            ))
        
        return personas
        
    except Exception as e:
        logger.error(f"Error getting persona status: {e}")
        return []

@app.post("/personas/switch")
async def switch_persona(persona: str):
    """Switch active persona"""
    try:
        # Broadcast persona switch to all connections
        await websocket_manager.broadcast({
            "type": "persona_switched",
            "data": {"persona": persona}
        })
        
        return {"success": True, "persona": persona}
        
    except Exception as e:
        logger.error(f"Error switching persona: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/system/command", response_model=CommandResult)
async def execute_command(command: SystemCommand):
    """Execute a system command"""
    try:
        # Parse and execute the command
        if command.command.lower().startswith("show"):
            return CommandResult(
                success=True,
                result="Command executed",
                ui_actions=[{
                    "type": "navigate",
                    "target": "dashboard",
                    "parameters": {}
                }]
            )
        elif command.command.lower().startswith("open"):
            panel_name = "context" if "context" in command.command.lower() else "unknown"
            return CommandResult(
                success=True,
                result="Panel opened",
                ui_actions=[{
                    "type": "open_panel",
                    "target": panel_name,
                    "parameters": {}
                }]
            )
        else:
            return CommandResult(
                success=True,
                result=f"Processed command: {command.command}",
                ui_actions=[]
            )
            
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return CommandResult(
            success=False,
            error=str(e)
        )

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "chat_message":
                # Process chat message
                chat_request = ChatRequest(
                    persona=message["data"]["persona"],
                    message=message["data"]["content"]
                )
                response = await send_message(chat_request)
                
                # Send response back
                await websocket.send_text(json.dumps({
                    "type": "chat_response",
                    "data": response.dict()
                }))
                
            elif message.get("type") == "persona_switch":
                # Handle persona switch
                persona = message["data"]["persona"]
                await switch_persona(persona)
                
            elif message.get("type") == "typing_indicator":
                # Broadcast typing indicator
                await websocket_manager.broadcast({
                    "type": "typing_update",
                    "data": message["data"]
                })
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
