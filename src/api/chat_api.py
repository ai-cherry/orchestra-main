#!/usr/bin/env python3
"""
Chat API for Orchestra AI Frontend Integration
Handles chat messages, persona routing, and real-time communication
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json
import logging
from datetime import datetime
import uuid

# Import Orchestra AI components
try:
    from mcp_unified_server import AdvancedOrchestralMCPServer
    from persona_profiles import PersonaManager
    from memory_architecture import PersonaDomain
except ImportError:
    # Fallback for development
    class AdvancedOrchestralMCPServer:
        async def process_request(self, persona, query, context=None):
            return {
                "response": f"Mock response from {persona}: {query}",
                "processing_time_ms": 100,
                "cross_domain_data": {}
            }
    
    class PersonaManager:
        def get_persona_status(self):
            return {
                "cherry": {"status": "active", "load_level": 0.3},
                "sophia": {"status": "active", "load_level": 0.2},
                "karen": {"status": "active", "load_level": 0.4}
            }

logger = logging.getLogger(__name__)

# Pydantic models for API
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

class WebSocketManager:
    """Manages WebSocket connections for real-time communication"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.persona_connections: Dict[str, List[WebSocket]] = {
            "cherry": [],
            "sophia": [],
            "karen": []
        }
    
    async def connect(self, websocket: WebSocket, persona: Optional[str] = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if persona and persona in self.persona_connections:
            self.persona_connections[persona].append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from persona connections
        for persona_list in self.persona_connections.values():
            if websocket in persona_list:
                persona_list.remove(websocket)
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_to_persona_subscribers(self, persona: str, message: dict):
        if persona not in self.persona_connections:
            return
        
        disconnected = []
        for connection in self.persona_connections[persona]:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending to persona subscribers: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

class ChatAPI:
    """Main Chat API class for Orchestra AI integration"""
    
    def __init__(self):
        self.orchestrator = None
        self.persona_manager = PersonaManager()
        self.websocket_manager = WebSocketManager()
        self.conversation_history: Dict[str, List[ChatResponse]] = {}
        
    async def initialize(self):
        """Initialize the orchestrator and other components"""
        try:
            self.orchestrator = AdvancedOrchestralMCPServer()
            await self.orchestrator.initialize_orchestrator()
            logger.info("✅ Chat API initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Chat API: {e}")
            # Use mock orchestrator for development
            self.orchestrator = AdvancedOrchestralMCPServer()
    
    async def send_message(self, request: ChatRequest) -> ChatResponse:
        """Send a message to a persona and get response"""
        try:
            # Generate unique message ID
            message_id = str(uuid.uuid4())
            
            # Process message through orchestrator
            if self.orchestrator:
                context = request.context or {}
                result = await self.orchestrator.process_request(
                    request.persona, 
                    request.message, 
                    context
                )
                
                response = ChatResponse(
                    id=message_id,
                    content=result.get("response", "I'm processing your request..."),
                    persona=request.persona,
                    timestamp=datetime.now().isoformat(),
                    type="text",
                    metadata={
                        "processing_time_ms": result.get("processing_time_ms", 0),
                        "cross_domain_data": result.get("cross_domain_data", {}),
                        "memory_compression_ratio": result.get("memory_compression_ratio", 1.0)
                    }
                )
            else:
                # Fallback response
                response = ChatResponse(
                    id=message_id,
                    content=f"Hello! I'm {request.persona.title()}. I received your message: {request.message}",
                    persona=request.persona,
                    timestamp=datetime.now().isoformat(),
                    type="text",
                    metadata={"processing_time_ms": 50}
                )
            
            # Store in conversation history
            if request.persona not in self.conversation_history:
                self.conversation_history[request.persona] = []
            self.conversation_history[request.persona].append(response)
            
            # Broadcast to WebSocket subscribers
            await self.websocket_manager.send_to_persona_subscribers(
                request.persona,
                {
                    "type": "chat_response",
                    "data": response.dict()
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_conversation_history(self, persona: Optional[str] = None, limit: int = 50) -> List[ChatResponse]:
        """Get conversation history for a persona or all personas"""
        try:
            if persona:
                return self.conversation_history.get(persona, [])[-limit:]
            else:
                # Return combined history from all personas
                all_messages = []
                for persona_messages in self.conversation_history.values():
                    all_messages.extend(persona_messages)
                
                # Sort by timestamp and return latest
                all_messages.sort(key=lambda x: x.timestamp)
                return all_messages[-limit:]
                
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    async def get_persona_status(self) -> List[PersonaStatus]:
        """Get status of all personas"""
        try:
            status_data = self.persona_manager.get_persona_status()
            
            personas = []
            for persona_name, status in status_data.items():
                personas.append(PersonaStatus(
                    persona=persona_name,
                    status=status.get("status", "active"),
                    current_task=status.get("current_task"),
                    load_level=status.get("load_level", 0.0),
                    capabilities=self._get_persona_capabilities(persona_name),
                    memory_usage={
                        "current": status.get("memory_usage", 0),
                        "max": 1000,
                        "compression_ratio": status.get("compression_ratio", 1.0)
                    }
                ))
            
            return personas
            
        except Exception as e:
            logger.error(f"Error getting persona status: {e}")
            return []
    
    def _get_persona_capabilities(self, persona: str) -> List[str]:
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
    
    async def execute_command(self, command: SystemCommand) -> CommandResult:
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
    
    async def switch_persona(self, persona: str):
        """Handle persona switching"""
        try:
            # Broadcast persona switch to all connections
            await self.websocket_manager.broadcast({
                "type": "persona_switched",
                "data": {"persona": persona}
            })
            
        except Exception as e:
            logger.error(f"Error switching persona: {e}")

# Global chat API instance
chat_api = ChatAPI()

# FastAPI app setup
app = FastAPI(title="Orchestra AI Chat API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await chat_api.initialize()

# REST API Endpoints
@app.post("/chat", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a message to a persona"""
    return await chat_api.send_message(request)

@app.get("/chat/history", response_model=List[ChatResponse])
async def get_history(persona: Optional[str] = None, limit: int = 50):
    """Get conversation history"""
    return await chat_api.get_conversation_history(persona, limit)

@app.get("/personas/status", response_model=List[PersonaStatus])
async def get_persona_status():
    """Get status of all personas"""
    return await chat_api.get_persona_status()

@app.post("/personas/switch")
async def switch_persona(persona: str):
    """Switch active persona"""
    await chat_api.switch_persona(persona)
    return {"success": True, "persona": persona}

@app.post("/system/command", response_model=CommandResult)
async def execute_command(command: SystemCommand):
    """Execute a system command"""
    return await chat_api.execute_command(command)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "orchestra-chat-api",
        "personas": ["cherry", "sophia", "karen"],
        "timestamp": datetime.now().isoformat(),
        "features": ["chat", "personas", "websocket", "commands"]
    }

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await chat_api.websocket_manager.connect(websocket)
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
                response = await chat_api.send_message(chat_request)
                
                # Send response back
                await chat_api.websocket_manager.send_personal_message({
                    "type": "chat_response",
                    "data": response.dict()
                }, websocket)
                
            elif message.get("type") == "persona_switch":
                # Handle persona switch
                persona = message["data"]["persona"]
                await chat_api.switch_persona(persona)
                
            elif message.get("type") == "typing_indicator":
                # Broadcast typing indicator
                await chat_api.websocket_manager.broadcast({
                    "type": "typing_update",
                    "data": message["data"]
                })
                
    except WebSocketDisconnect:
        chat_api.websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        chat_api.websocket_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010) 