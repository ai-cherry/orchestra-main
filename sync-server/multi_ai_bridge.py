#!/usr/bin/env python3
"""
Multi-AI Collaboration Bridge
Extends the proven live collaboration foundation with intelligent multi-AI capabilities
"""

import asyncio
import json
import websockets
import logging
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Import our proven smart filtering
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'cursor-plugin'))
from smart_file_filter import SmartCollaborationFilter

class AICapability(Enum):
    """AI specialization areas"""
    DEPLOYMENT = "deployment"
    INFRASTRUCTURE = "infrastructure" 
    DEBUGGING = "debugging"
    PRODUCTION = "production"
    CODE_GENERATION = "code_generation"
    UI_DESIGN = "ui_design"
    REFACTORING = "refactoring"
    RAPID_PROTOTYPING = "rapid_prototyping"
    ARCHITECTURE = "architecture"
    DOCUMENTATION = "documentation"
    ANALYSIS = "analysis"
    DESIGN = "design"
    CREATIVE_SOLUTIONS = "creative_solutions"
    COMPLEX_REASONING = "complex_reasoning"
    INTEGRATION = "integration"

@dataclass
class ConnectedAI:
    """Represents a connected AI assistant"""
    name: str
    websocket: websockets.WebSocketServerProtocol
    capabilities: List[AICapability]
    connected_at: datetime
    session_id: Optional[str] = None
    status: str = "active"
    message_count: int = 0

class SimpleMultiAIBridge:
    """
    Multi-AI Collaboration Bridge
    Builds on proven WebSocket + Smart Filtering foundation
    """
    
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        
        # Proven components from our success
        self.smart_filter = SmartCollaborationFilter()
        
        # Multi-AI extensions
        self.connected_ais: Dict[str, ConnectedAI] = {}
        self.active_sessions: Dict[str, Dict] = {}
        self.ai_specialties: Dict[str, List[AICapability]] = {
            "manus": [
                AICapability.DEPLOYMENT, 
                AICapability.INFRASTRUCTURE, 
                AICapability.DEBUGGING, 
                AICapability.PRODUCTION
            ],
            "cursor": [
                AICapability.CODE_GENERATION, 
                AICapability.UI_DESIGN, 
                AICapability.REFACTORING, 
                AICapability.RAPID_PROTOTYPING
            ],
            "claude": [
                AICapability.ARCHITECTURE, 
                AICapability.DOCUMENTATION, 
                AICapability.ANALYSIS, 
                AICapability.DESIGN
            ],
            "gpt4": [
                AICapability.CREATIVE_SOLUTIONS, 
                AICapability.COMPLEX_REASONING, 
                AICapability.INTEGRATION
            ]
        }
        
        # Simple message routing
        self.message_handlers = {
            "ai_connect": self.handle_ai_connection,
            "file_change": self.handle_file_change,
            "ai_request": self.handle_ai_request,
            "multi_ai_collaboration": self.handle_multi_ai_collaboration,
            "session_join": self.handle_session_join
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def start_server(self):
        """Start the multi-AI collaboration bridge"""
        self.logger.info(f"🚀 Starting Multi-AI Collaboration Bridge on {self.host}:{self.port}")
        self.logger.info(f"🧠 Smart filtering enabled (proven 97.5% efficiency)")
        self.logger.info(f"🤖 Supporting AIs: {list(self.ai_specialties.keys())}")
        
        async def handle_connection(websocket, path):
            """Handle new AI connections"""
            await self.handle_websocket_connection(websocket, path)
        
        start_server = websockets.serve(handle_connection, self.host, self.port)
        await start_server
        
        self.logger.info("✅ Multi-AI Bridge ready for connections!")
        await asyncio.Future()  # Run forever
    
    async def handle_websocket_connection(self, websocket, path):
        """Handle incoming WebSocket connections from AIs"""
        remote_addr = websocket.remote_address
        self.logger.info(f"🔗 New connection from {remote_addr} on path: {path}")
        
        try:
            async for message in websocket:
                await self.process_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            await self.handle_ai_disconnection(websocket)
        except Exception as e:
            self.logger.error(f"❌ Connection error: {e}")
            await self.handle_ai_disconnection(websocket)
    
    async def process_message(self, websocket, raw_message: str):
        """Process incoming messages with intelligent routing"""
        try:
            message = json.loads(raw_message)
            message_type = message.get("type", "unknown")
            
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](websocket, message)
            else:
                await self.send_error(websocket, f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error(websocket, "Invalid JSON message")
        except Exception as e:
            self.logger.error(f"❌ Message processing error: {e}")
            await self.send_error(websocket, f"Processing error: {str(e)}")
    
    async def handle_ai_connection(self, websocket, message: Dict):
        """Handle AI registration and authentication"""
        ai_name = message.get("ai_name", "unknown")
        capabilities = message.get("capabilities", [])
        api_key = message.get("api_key")  # Simple auth
        
        # Simple API key validation (good enough security)
        if not self.validate_api_key(ai_name, api_key):
            await self.send_error(websocket, "Invalid API key")
            return
        
        # Convert capability strings to enums
        ai_capabilities = []
        for cap in capabilities:
            try:
                ai_capabilities.append(AICapability(cap))
            except ValueError:
                self.logger.warning(f"Unknown capability: {cap}")
        
        # Use default capabilities if none provided
        if not ai_capabilities and ai_name in self.ai_specialties:
            ai_capabilities = self.ai_specialties[ai_name]
        
        # Register the AI
        connected_ai = ConnectedAI(
            name=ai_name,
            websocket=websocket,
            capabilities=ai_capabilities,
            connected_at=datetime.now()
        )
        
        self.connected_ais[ai_name] = connected_ai
        
        await self.send_to_ai(ai_name, {
            "type": "connection_confirmed",
            "ai_name": ai_name,
            "capabilities": [cap.value for cap in ai_capabilities],
            "bridge_status": "operational",
            "connected_ais": list(self.connected_ais.keys()),
            "smart_filtering": "enabled"
        })
        
        # Notify other AIs
        await self.broadcast_to_others(ai_name, {
            "type": "ai_joined",
            "ai_name": ai_name,
            "capabilities": [cap.value for cap in ai_capabilities],
            "timestamp": datetime.now().isoformat()
        })
        
        self.logger.info(f"✅ {ai_name} connected with capabilities: {[cap.value for cap in ai_capabilities]}")
    
    async def handle_file_change(self, websocket, message: Dict):
        """Handle file changes with our proven smart filtering"""
        file_path = message.get("file_path")
        content = message.get("content")
        session_id = message.get("session_id")
        from_ai = message.get("from_ai", "unknown")
        
        # Apply our proven smart filtering
        if not self.smart_filter.should_sync_file(file_path):
            self.logger.debug(f"📋 File filtered out by smart filtering: {file_path}")
            return
        
        # Determine which AIs should receive this change
        interested_ais = await self.determine_interested_ais(file_path, content)
        
        enhanced_message = {
            **message,
            "smart_filtered": True,
            "interested_ais": interested_ais,
            "from_ai": from_ai,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to interested AIs
        for ai_name in interested_ais:
            if ai_name != from_ai and ai_name in self.connected_ais:
                await self.send_to_ai(ai_name, enhanced_message)
        
        self.logger.info(f"📤 File change {file_path} routed to: {interested_ais}")
    
    async def handle_ai_request(self, websocket, message: Dict):
        """Handle AI-to-AI requests with intelligent routing"""
        request_text = message.get("message", "")
        context = message.get("context", {})
        target_ai = message.get("target_ai")
        from_ai = message.get("from_ai", "unknown")
        
        # Smart AI routing based on request content
        if target_ai:
            target_ais = [target_ai]
        else:
            target_ais = await self.route_request_to_best_ais(request_text, context)
        
        enhanced_message = {
            **message,
            "routed_to": target_ais,
            "routing_reason": await self.explain_routing(request_text, target_ais),
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to target AIs
        for ai_name in target_ais:
            if ai_name != from_ai and ai_name in self.connected_ais:
                await self.send_to_ai(ai_name, enhanced_message)
        
        self.logger.info(f"🧠 Request from {from_ai} routed to: {target_ais}")
    
    async def handle_multi_ai_collaboration(self, websocket, message: Dict):
        """Handle multi-AI collaboration scenarios"""
        request = message.get("request", "")
        context = message.get("context", {})
        target_ais = message.get("target_ais", "all")
        from_ai = message.get("from_ai", "unknown")
        collaboration_type = message.get("collaboration_type", "general")
        
        if target_ais == "all":
            target_ais = [name for name in self.connected_ais.keys() if name != from_ai]
        
        # Create collaboration session
        collab_id = f"collab_{int(datetime.now().timestamp())}"
        
        collaboration_message = {
            "type": "collaboration_request",
            "collaboration_id": collab_id,
            "request": request,
            "context": context,
            "collaboration_type": collaboration_type,
            "participants": target_ais + [from_ai],
            "from_ai": from_ai,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all target AIs
        for ai_name in target_ais:
            if ai_name in self.connected_ais:
                await self.send_to_ai(ai_name, collaboration_message)
        
        self.logger.info(f"🤝 Multi-AI collaboration {collab_id} started: {target_ais}")
    
    async def handle_session_join(self, websocket, message: Dict):
        """Handle AI joining development sessions"""
        session_id = message.get("session_id")
        ai_name = message.get("ai_name")
        project_path = message.get("project_path")
        
        if ai_name in self.connected_ais:
            self.connected_ais[ai_name].session_id = session_id
            
            # Get smart project context
            if project_path:
                context = self.smart_filter.get_project_context(project_path)
                await self.send_to_ai(ai_name, {
                    "type": "session_context",
                    "session_id": session_id,
                    "project_context": context,
                    "smart_filtered": True
                })
        
        self.logger.info(f"📁 {ai_name} joined session {session_id}")
    
    async def determine_interested_ais(self, file_path: str, content: str) -> List[str]:
        """Determine which AIs should receive this file change"""
        interested = []
        
        # File type based routing
        if file_path.endswith(('.py', '.js', '.ts')):
            interested.extend(['cursor', 'claude'])
        
        if file_path.endswith(('.md', '.txt', '.rst')):
            interested.extend(['claude'])
            
        if 'deploy' in file_path.lower() or 'docker' in file_path.lower():
            interested.append('manus')
            
        # Content based routing
        if any(keyword in content.lower() for keyword in ['component', 'react', 'vue', 'ui']):
            if 'cursor' not in interested:
                interested.append('cursor')
        
        if any(keyword in content.lower() for keyword in ['deploy', 'server', 'infrastructure']):
            if 'manus' not in interested:
                interested.append('manus')
        
        # Default to all connected AIs if unclear
        if not interested:
            interested = list(self.connected_ais.keys())
        
        return [ai for ai in interested if ai in self.connected_ais]
    
    async def route_request_to_best_ais(self, request_text: str, context: Dict) -> List[str]:
        """Smart AI routing based on request content"""
        request_lower = request_text.lower()
        best_ais = []
        
        # Deployment and infrastructure requests
        if any(word in request_lower for word in ["deploy", "server", "infrastructure", "production", "debug"]):
            best_ais.append("manus")
        
        # UI and frontend requests  
        if any(word in request_lower for word in ["ui", "component", "frontend", "design", "interface"]):
            best_ais.append("cursor")
        
        # Architecture and documentation requests
        if any(word in request_lower for word in ["architecture", "design", "documentation", "analysis"]):
            best_ais.append("claude")
        
        # Complex reasoning requests
        if any(word in request_lower for word in ["complex", "strategy", "planning", "integration"]):
            best_ais.append("gpt4")
        
        # Default to most appropriate general AI
        if not best_ais:
            best_ais = ["claude"]  # Good general purpose AI
        
        return [ai for ai in best_ais if ai in self.connected_ais]
    
    async def explain_routing(self, request_text: str, target_ais: List[str]) -> str:
        """Explain why request was routed to specific AIs"""
        explanations = []
        
        for ai in target_ais:
            if ai == "manus":
                explanations.append("deployment/infrastructure expertise")
            elif ai == "cursor":
                explanations.append("UI/code generation capabilities")
            elif ai == "claude":
                explanations.append("analysis/architecture strengths")
            elif ai == "gpt4":
                explanations.append("complex reasoning abilities")
        
        return f"Routed based on: {', '.join(explanations)}"
    
    async def send_to_ai(self, ai_name: str, message: Dict):
        """Send message to specific AI"""
        if ai_name in self.connected_ais:
            try:
                await self.connected_ais[ai_name].websocket.send(json.dumps(message))
                self.connected_ais[ai_name].message_count += 1
            except Exception as e:
                self.logger.error(f"❌ Failed to send to {ai_name}: {e}")
                await self.handle_ai_disconnection(self.connected_ais[ai_name].websocket)
    
    async def broadcast_to_others(self, exclude_ai: str, message: Dict):
        """Broadcast message to all AIs except one"""
        for ai_name in self.connected_ais:
            if ai_name != exclude_ai:
                await self.send_to_ai(ai_name, message)
    
    async def send_error(self, websocket, error_message: str):
        """Send error message to websocket"""
        try:
            await websocket.send(json.dumps({
                "type": "error",
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            self.logger.error(f"❌ Failed to send error: {e}")
    
    async def handle_ai_disconnection(self, websocket):
        """Handle AI disconnection"""
        # Find and remove the disconnected AI
        disconnected_ai = None
        for ai_name, ai in self.connected_ais.items():
            if ai.websocket == websocket:
                disconnected_ai = ai_name
                break
        
        if disconnected_ai:
            del self.connected_ais[disconnected_ai]
            
            # Notify remaining AIs
            await self.broadcast_to_others("", {
                "type": "ai_disconnected",
                "ai_name": disconnected_ai,
                "timestamp": datetime.now().isoformat()
            })
            
            self.logger.info(f"❌ {disconnected_ai} disconnected")
    
    def validate_api_key(self, ai_name: str, api_key: str) -> bool:
        """Simple API key validation (good enough security)"""
        # In production, store these securely
        valid_keys = {
            "manus": "manus_key_2025",
            "cursor": "cursor_key_2025", 
            "claude": "claude_key_2025",
            "gpt4": "gpt4_key_2025"
        }
        
        return valid_keys.get(ai_name) == api_key
    
    def get_bridge_status(self) -> Dict:
        """Get current bridge status"""
        return {
            "connected_ais": len(self.connected_ais),
            "active_sessions": len(self.active_sessions),
            "ai_list": [
                {
                    "name": ai.name,
                    "capabilities": [cap.value for cap in ai.capabilities],
                    "connected_at": ai.connected_at.isoformat(),
                    "message_count": ai.message_count,
                    "status": ai.status
                }
                for ai in self.connected_ais.values()
            ],
            "smart_filtering": "enabled",
            "bridge_uptime": datetime.now().isoformat()
        }

# Multi-AI Bridge Configuration
MULTI_AI_CONFIG = {
    "name": "multi-ai-collaboration-bridge",
    "version": "1.0.0",
    "description": "Simple, stable multi-AI collaboration platform",
    "supported_ais": ["manus", "cursor", "claude", "gpt4"],
    "features": [
        "smart_filtering",
        "intelligent_routing", 
        "multi_ai_collaboration",
        "session_management",
        "simple_authentication"
    ]
}

async def main():
    """Start the Multi-AI Collaboration Bridge"""
    bridge = SimpleMultiAIBridge()
    await bridge.start_server()

if __name__ == "__main__":
    print("🚀 MULTI-AI COLLABORATION BRIDGE")
    print("=" * 50)
    print(f"📋 Building on proven smart filtering success")
    print(f"🤖 Supporting: Manus, Cursor, Claude, GPT-4")
    print(f"🧠 Intelligent routing enabled")
    print(f"🔒 Simple API key authentication")
    print(f"⚡ Single developer maintainable")
    print("")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Multi-AI Bridge stopped")
    except Exception as e:
        print(f"❌ Bridge error: {e}") 