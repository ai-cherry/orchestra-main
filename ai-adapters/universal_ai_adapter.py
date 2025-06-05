#!/usr/bin/env python3
"""
Universal AI Adapter for Multi-AI Collaboration
Makes it dead simple for any AI to join the collaboration bridge
"""

import asyncio
import json
import websockets
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from abc import ABC, abstractmethod

class SimpleAIAdapter:
    """
    Dead simple adapter for any AI to join multi-AI collaboration
    One class, minimal setup, maximum compatibility
    """
    
    def __init__(
        self, 
        ai_name: str, 
        capabilities: List[str], 
        api_key: str,
        bridge_url: str = "ws://150.136.94.139:8765"
    ):
        self.ai_name = ai_name
        self.capabilities = capabilities
        self.api_key = api_key
        self.bridge_url = bridge_url
        self.websocket = None
        self.connected = False
        self.session_id = None
        
        # Message handlers - override these in subclasses
        self.message_handlers = {
            "connection_confirmed": self.handle_connection_confirmed,
            "ai_joined": self.handle_ai_joined,
            "ai_disconnected": self.handle_ai_disconnected,
            "file_change": self.handle_file_change,
            "ai_request": self.handle_ai_request,
            "collaboration_request": self.handle_collaboration_request,
            "session_context": self.handle_session_context,
            "error": self.handle_error
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"AI-{ai_name}")
    
    async def connect_to_collaboration(self) -> bool:
        """One method to join the collaboration bridge"""
        try:
            self.logger.info(f"🔗 Connecting {self.ai_name} to collaboration bridge...")
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(self.bridge_url)
            
            # Authenticate and register
            await self.authenticate()
            
            # Start message handling
            asyncio.create_task(self.message_loop())
            
            self.connected = True
            self.logger.info(f"✅ {self.ai_name} connected to multi-AI collaboration!")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Connection failed: {e}")
            return False
    
    async def authenticate(self):
        """Authenticate with the collaboration bridge"""
        auth_message = {
            "type": "ai_connect",
            "ai_name": self.ai_name,
            "capabilities": self.capabilities,
            "api_key": self.api_key,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket.send(json.dumps(auth_message))
        self.logger.info(f"🔐 Authentication sent for {self.ai_name}")
    
    async def message_loop(self):
        """Handle incoming messages from collaboration bridge"""
        try:
            async for raw_message in self.websocket:
                message = json.loads(raw_message)
                await self.handle_collaboration_message(message)
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"🔌 Connection closed for {self.ai_name}")
            self.connected = False
        except Exception as e:
            self.logger.error(f"❌ Message loop error: {e}")
            self.connected = False
    
    async def handle_collaboration_message(self, message: Dict[str, Any]):
        """Route incoming messages to appropriate handlers"""
        message_type = message.get("type", "unknown")
        
        if message_type in self.message_handlers:
            try:
                await self.message_handlers[message_type](message)
            except Exception as e:
                self.logger.error(f"❌ Handler error for {message_type}: {e}")
        else:
            self.logger.warning(f"⚠️ Unknown message type: {message_type}")
    
    # Default message handlers (override these in AI-specific implementations)
    
    async def handle_connection_confirmed(self, message: Dict):
        """Handle connection confirmation from bridge"""
        self.logger.info(f"✅ Connection confirmed for {self.ai_name}")
        self.logger.info(f"🤖 Connected AIs: {message.get('connected_ais', [])}")
        self.logger.info(f"🧠 Smart filtering: {message.get('smart_filtering', 'unknown')}")
    
    async def handle_ai_joined(self, message: Dict):
        """Handle notification of new AI joining"""
        new_ai = message.get("ai_name", "unknown")
        capabilities = message.get("capabilities", [])
        self.logger.info(f"👋 {new_ai} joined with capabilities: {capabilities}")
    
    async def handle_ai_disconnected(self, message: Dict):
        """Handle notification of AI disconnecting"""
        departed_ai = message.get("ai_name", "unknown")
        self.logger.info(f"👋 {departed_ai} disconnected")
    
    async def handle_file_change(self, message: Dict):
        """Handle file change notifications - OVERRIDE THIS"""
        file_path = message.get("file_path", "unknown")
        from_ai = message.get("from_ai", "unknown")
        self.logger.info(f"📄 File change: {file_path} from {from_ai}")
        
        # Default behavior: log the change
        # Override this method in AI-specific implementations
        await self.process_file_change(message)
    
    async def handle_ai_request(self, message: Dict):
        """Handle requests from other AIs - OVERRIDE THIS"""
        request_text = message.get("message", "")
        from_ai = message.get("from_ai", "unknown")
        context = message.get("context", {})
        
        self.logger.info(f"🤖 Request from {from_ai}: {request_text[:100]}...")
        
        # Default behavior: acknowledge the request
        # Override this method in AI-specific implementations
        response = await self.process_ai_request(request_text, context, from_ai)
        
        if response:
            await self.send_response(from_ai, response, message)
    
    async def handle_collaboration_request(self, message: Dict):
        """Handle multi-AI collaboration requests - OVERRIDE THIS"""
        collaboration_id = message.get("collaboration_id", "unknown")
        request = message.get("request", "")
        participants = message.get("participants", [])
        from_ai = message.get("from_ai", "unknown")
        
        self.logger.info(f"🤝 Collaboration {collaboration_id} from {from_ai}")
        self.logger.info(f"📋 Request: {request[:100]}...")
        self.logger.info(f"👥 Participants: {participants}")
        
        # Default behavior: participate in collaboration
        # Override this method in AI-specific implementations
        response = await self.process_collaboration_request(message)
        
        if response:
            await self.send_collaboration_response(collaboration_id, response, participants)
    
    async def handle_session_context(self, message: Dict):
        """Handle session context updates"""
        session_id = message.get("session_id", "unknown")
        project_context = message.get("project_context", {})
        
        self.session_id = session_id
        self.logger.info(f"📁 Session context for {session_id}")
        self.logger.info(f"📊 Files: {project_context.get('file_count', 0)}")
        self.logger.info(f"🔥 Recent: {len(project_context.get('recent_files', []))}")
    
    async def handle_error(self, message: Dict):
        """Handle error messages from bridge"""
        error_message = message.get("message", "Unknown error")
        self.logger.error(f"❌ Bridge error: {error_message}")
    
    # Methods to override in AI-specific implementations
    
    async def process_file_change(self, message: Dict) -> Optional[str]:
        """
        Process file changes - OVERRIDE THIS in AI implementations
        Return response if you want to send feedback about the change
        """
        # Default: no response
        return None
    
    async def process_ai_request(self, request: str, context: Dict, from_ai: str) -> Optional[str]:
        """
        Process requests from other AIs - OVERRIDE THIS in AI implementations
        Return your response to the requesting AI
        """
        # Default: polite acknowledgment
        return f"Hello {from_ai}! I received your request: {request[:50]}..."
    
    async def process_collaboration_request(self, message: Dict) -> Optional[str]:
        """
        Process multi-AI collaboration requests - OVERRIDE THIS in AI implementations
        Return your contribution to the collaboration
        """
        # Default: simple participation
        request = message.get("request", "")
        return f"Hi! I'm {self.ai_name}. Regarding: {request[:50]}... I'm here to help!"
    
    # Utility methods for sending messages
    
    async def send_message_to_ai(self, target_ai: str, message: str, context: Dict = None):
        """Send a message to specific AI"""
        if not self.connected:
            self.logger.error("❌ Not connected to collaboration bridge")
            return
        
        message_data = {
            "type": "ai_request",
            "target_ai": target_ai,
            "message": message,
            "context": context or {},
            "from_ai": self.ai_name,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket.send(json.dumps(message_data))
        self.logger.info(f"📤 Sent message to {target_ai}")
    
    async def send_file_change(self, file_path: str, content: str, session_id: str = None):
        """Send file change notification"""
        if not self.connected:
            self.logger.error("❌ Not connected to collaboration bridge")
            return
        
        message_data = {
            "type": "file_change",
            "file_path": file_path,
            "content": content,
            "session_id": session_id or self.session_id,
            "from_ai": self.ai_name,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket.send(json.dumps(message_data))
        self.logger.info(f"📤 Sent file change: {file_path}")
    
    async def request_collaboration(self, request: str, target_ais: List[str] = None, context: Dict = None):
        """Request multi-AI collaboration"""
        if not self.connected:
            self.logger.error("❌ Not connected to collaboration bridge")
            return
        
        message_data = {
            "type": "multi_ai_collaboration",
            "request": request,
            "target_ais": target_ais or "all",
            "context": context or {},
            "collaboration_type": "general",
            "from_ai": self.ai_name,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket.send(json.dumps(message_data))
        self.logger.info(f"🤝 Requested collaboration: {request[:50]}...")
    
    async def join_session(self, session_id: str, project_path: str = None):
        """Join a development session"""
        if not self.connected:
            self.logger.error("❌ Not connected to collaboration bridge")
            return
        
        message_data = {
            "type": "session_join",
            "session_id": session_id,
            "ai_name": self.ai_name,
            "project_path": project_path,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket.send(json.dumps(message_data))
        self.logger.info(f"📁 Joining session: {session_id}")
    
    async def send_response(self, target_ai: str, response: str, original_message: Dict):
        """Send response to an AI request"""
        await self.send_message_to_ai(target_ai, f"Response: {response}")
    
    async def send_collaboration_response(self, collaboration_id: str, response: str, participants: List[str]):
        """Send response to a collaboration request"""
        for participant in participants:
            if participant != self.ai_name:
                await self.send_message_to_ai(
                    participant, 
                    f"Collaboration {collaboration_id}: {response}"
                )
    
    async def disconnect(self):
        """Disconnect from collaboration bridge"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            self.logger.info(f"🔌 {self.ai_name} disconnected from collaboration")


# Specialized AI Adapters

class ManusAdapter(SimpleAIAdapter):
    """Manus AI specialized adapter"""
    
    def __init__(self, api_key: str, bridge_url: str = "ws://150.136.94.139:8765"):
        super().__init__(
            ai_name="manus",
            capabilities=["deployment", "infrastructure", "debugging", "production"],
            api_key=api_key,
            bridge_url=bridge_url
        )
    
    async def process_file_change(self, message: Dict) -> Optional[str]:
        """Manus focuses on deployment and infrastructure changes"""
        file_path = message.get("file_path", "")
        content = message.get("content", "")
        
        # Look for deployment-related changes
        if any(keyword in file_path.lower() for keyword in ['deploy', 'docker', 'infrastructure', '.yml', '.yaml']):
            self.logger.info(f"🚀 Manus analyzing deployment file: {file_path}")
            return f"Manus: Reviewed {file_path} for deployment implications"
        
        return None
    
    async def process_ai_request(self, request: str, context: Dict, from_ai: str) -> Optional[str]:
        """Manus handles deployment and infrastructure requests"""
        request_lower = request.lower()
        
        if any(keyword in request_lower for keyword in ['deploy', 'server', 'infrastructure', 'production', 'debug']):
            self.logger.info(f"🛠️ Manus handling infrastructure request from {from_ai}")
            return f"Manus: I can help with that deployment/infrastructure issue. {request[:100]}..."
        
        return f"Manus: That's outside my deployment expertise, but I'm here if you need infrastructure help!"


class CursorAdapter(SimpleAIAdapter):
    """Cursor AI specialized adapter"""
    
    def __init__(self, api_key: str, bridge_url: str = "ws://150.136.94.139:8765"):
        super().__init__(
            ai_name="cursor",
            capabilities=["code_generation", "ui_design", "refactoring", "rapid_prototyping"],
            api_key=api_key,
            bridge_url=bridge_url
        )
    
    async def process_file_change(self, message: Dict) -> Optional[str]:
        """Cursor focuses on code and UI changes"""
        file_path = message.get("file_path", "")
        content = message.get("content", "")
        
        # Look for code-related changes
        if any(ext in file_path.lower() for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.vue', '.css', '.html']):
            self.logger.info(f"💻 Cursor analyzing code file: {file_path}")
            return f"Cursor: Analyzed {file_path} for code quality and UI patterns"
        
        return None
    
    async def process_ai_request(self, request: str, context: Dict, from_ai: str) -> Optional[str]:
        """Cursor handles code and UI requests"""
        request_lower = request.lower()
        
        if any(keyword in request_lower for keyword in ['code', 'ui', 'component', 'frontend', 'refactor']):
            self.logger.info(f"⌨️ Cursor handling code request from {from_ai}")
            return f"Cursor: I can help with that code/UI challenge! {request[:100]}..."
        
        return f"Cursor: I specialize in code and UI - let me know if you need help with that!"


class ClaudeAdapter(SimpleAIAdapter):
    """Claude AI specialized adapter"""
    
    def __init__(self, api_key: str, bridge_url: str = "ws://150.136.94.139:8765"):
        super().__init__(
            ai_name="claude",
            capabilities=["architecture", "documentation", "analysis", "design"],
            api_key=api_key,
            bridge_url=bridge_url
        )
    
    async def process_file_change(self, message: Dict) -> Optional[str]:
        """Claude focuses on architecture and documentation"""
        file_path = message.get("file_path", "")
        content = message.get("content", "")
        
        # Look for documentation and architecture files
        if any(ext in file_path.lower() for ext in ['.md', '.rst', '.txt', 'readme', 'doc']):
            self.logger.info(f"📚 Claude analyzing documentation: {file_path}")
            return f"Claude: Reviewed {file_path} for documentation quality and clarity"
        
        return None
    
    async def process_ai_request(self, request: str, context: Dict, from_ai: str) -> Optional[str]:
        """Claude handles architecture and analysis requests"""
        request_lower = request.lower()
        
        if any(keyword in request_lower for keyword in ['architecture', 'design', 'documentation', 'analysis', 'explain']):
            self.logger.info(f"🏗️ Claude handling architecture request from {from_ai}")
            return f"Claude: I'd be happy to help with that architectural analysis! {request[:100]}..."
        
        return f"Claude: I can help with architecture, documentation, and analysis tasks!"


# Utility function for easy setup
def create_ai_adapter(ai_name: str, api_key: str, bridge_url: str = "ws://150.136.94.139:8765") -> SimpleAIAdapter:
    """Factory function to create the right adapter for each AI"""
    
    adapters = {
        "manus": ManusAdapter,
        "cursor": CursorAdapter,
        "claude": ClaudeAdapter
    }
    
    if ai_name.lower() in adapters:
        return adapters[ai_name.lower()](api_key, bridge_url)
    else:
        # Generic adapter for unknown AIs
        return SimpleAIAdapter(
            ai_name=ai_name,
            capabilities=["general"],
            api_key=api_key,
            bridge_url=bridge_url
        )


# Example usage
if __name__ == "__main__":
    async def demo_multi_ai_collaboration():
        """Demonstrate multi-AI collaboration"""
        
        print("🚀 MULTI-AI COLLABORATION DEMO")
        print("=" * 40)
        
        # Create AI adapters (in real use, each AI would run this separately)
        manus = ManusAdapter("manus_key_2025")
        cursor = CursorAdapter("cursor_key_2025")
        claude = ClaudeAdapter("claude_key_2025")
        
        # Connect all AIs
        print("🔗 Connecting AIs to collaboration bridge...")
        
        connections = await asyncio.gather(
            manus.connect_to_collaboration(),
            cursor.connect_to_collaboration(),
            claude.connect_to_collaboration(),
            return_exceptions=True
        )
        
        print(f"✅ Connections: {connections}")
        
        # Wait a moment for connections to establish
        await asyncio.sleep(2)
        
        # Demo file change
        print("\n📄 Demo: File change notification...")
        await cursor.send_file_change("src/components/App.jsx", "// React component code here")
        
        # Demo AI request
        print("\n🤖 Demo: AI-to-AI request...")
        await cursor.send_message_to_ai("manus", "Can you help me deploy this React app?")
        
        # Demo collaboration request
        print("\n🤝 Demo: Multi-AI collaboration...")
        await claude.request_collaboration(
            "Let's design the architecture for a new e-commerce platform",
            target_ais=["manus", "cursor"]
        )
        
        # Keep demo running for a bit
        print("\n⏳ Running demo for 10 seconds...")
        await asyncio.sleep(10)
        
        # Disconnect
        print("\n🔌 Disconnecting AIs...")
        await asyncio.gather(
            manus.disconnect(),
            cursor.disconnect(),
            claude.disconnect()
        )
        
        print("✅ Demo complete!")
    
    try:
        asyncio.run(demo_multi_ai_collaboration())
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped")
    except Exception as e:
        print(f"❌ Demo error: {e}") 