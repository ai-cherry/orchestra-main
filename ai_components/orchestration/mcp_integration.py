#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Integration for AI Agent Communication
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
import aiohttp
import websockets
from abc import ABC, abstractmethod
import weaviate
from weaviate.embedded import EmbeddedOptions

from shared.database import UnifiedDatabase
from shared.utils.performance import benchmark
from ai_components.orchestration.roo_mcp_adapter import RooMCPAdapter, RooMode

logger = logging.getLogger(__name__)

@dataclass
class MCPMessage:
    """Standard MCP message format"""
    id: str
    type: str  # request, response, notification
    method: str
    params: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class AgentCapability:
    """Defines what an agent can do"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    constraints: Dict[str, Any] = field(default_factory=dict)

class MCPAgent(ABC):
    """Base class for MCP-compatible agents"""
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.capabilities: List[AgentCapability] = []
        self.status = "idle"
        self.current_task = None
        
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task and return results"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """Return agent capabilities"""
        pass

class RooAgent(MCPAgent):
    """Roo AI coding assistant integration"""
    
    def __init__(self):
        super().__init__("roo_agent", "Roo AI Assistant")
        self.api_endpoint = os.getenv("ROO_API_ENDPOINT", "http://localhost:8001")
        
    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="code_generation",
                description="Generate code based on requirements",
                input_schema={"prompt": "string", "language": "string"},
                output_schema={"code": "string", "explanation": "string"}
            ),
            AgentCapability(
                name="code_review",
                description="Review code for quality and improvements",
                input_schema={"code": "string", "language": "string"},
                output_schema={"issues": "array", "suggestions": "array"}
            ),
            AgentCapability(
                name="refactoring",
                description="Suggest and apply code refactoring",
                input_schema={"code": "string", "goal": "string"},
                output_schema={"refactored_code": "string", "changes": "array"}
            )
        ]
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Roo agent task"""
        self.status = "executing"
        self.current_task = task
        
        try:
            # Simulate Roo API call - replace with actual integration
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_endpoint}/execute",
                    json=task
                ) as response:
                    result = await response.json()
                    
            self.status = "idle"
            self.current_task = None
            return result
            
        except Exception as e:
            logger.error(f"Roo agent execution error: {e}")
            self.status = "error"
            raise

class FactoryAIAgent(MCPAgent):
    """Factory AI integration for automated development"""
    
    def __init__(self):
        super().__init__("factory_ai_agent", "Factory AI")
        self.api_endpoint = os.getenv("FACTORY_AI_ENDPOINT", "http://localhost:8002")
        
    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="project_scaffolding",
                description="Create project structure and boilerplate",
                input_schema={"project_type": "string", "requirements": "object"},
                output_schema={"files_created": "array", "structure": "object"}
            ),
            AgentCapability(
                name="api_generation",
                description="Generate API endpoints from specifications",
                input_schema={"spec": "object", "framework": "string"},
                output_schema={"endpoints": "array", "models": "array"}
            ),
            AgentCapability(
                name="test_generation",
                description="Generate comprehensive test suites",
                input_schema={"code_path": "string", "coverage_target": "number"},
                output_schema={"tests": "array", "coverage": "number"}
            )
        ]
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Factory AI task"""
        self.status = "executing"
        self.current_task = task
        
        try:
            # Simulate Factory AI API call
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_endpoint}/execute",
                    json=task
                ) as response:
                    result = await response.json()
                    
            self.status = "idle"
            self.current_task = None
            return result
            
        except Exception as e:
            logger.error(f"Factory AI agent execution error: {e}")
            self.status = "error"
            raise

class MCPContextManager:
    """Manages context across MCP agents"""
    
    def __init__(self, vector_store_url: str):
        self.vector_store_url = vector_store_url
        self.contexts: Dict[str, Dict[str, Any]] = {}
        self.version_history: Dict[str, List[Dict[str, Any]]] = {}
        
    async def store_context(self, session_id: str, context: Dict[str, Any]):
        """Store context in vector database"""
        # Version the context
        if session_id not in self.version_history:
            self.version_history[session_id] = []
        
        version = len(self.version_history[session_id])
        versioned_context = {
            **context,
            "version": version,
            "timestamp": datetime.now().isoformat()
        }
        
        self.version_history[session_id].append(versioned_context)
        self.contexts[session_id] = context
        
        # Store in vector database for retrieval
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{self.vector_store_url}/store",
                json={
                    "id": f"{session_id}_v{version}",
                    "content": context,
                    "metadata": {"session_id": session_id, "version": version}
                }
            )
    
    async def retrieve_context(self, session_id: str, 
                             query: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve relevant context"""
        if query:
            # Semantic search in vector store
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.vector_store_url}/search",
                    json={"query": query, "filter": {"session_id": session_id}}
                ) as response:
                    results = await response.json()
                    return results.get("matches", [{}])[0].get("content", {})
        else:
            # Return latest context
            return self.contexts.get(session_id, {})
    
    def prune_context(self, session_id: str, max_size: int = 1000):
        """Prune context to maintain efficiency"""
        if session_id in self.contexts:
            context = self.contexts[session_id]
            # Simple pruning - keep most recent items
            if "messages" in context and len(context["messages"]) > max_size:
                context["messages"] = context["messages"][-max_size:]


class UnifiedContextManager(MCPContextManager):
    """Extended context manager with Roo integration and Weaviate indexing."""

    def __init__(self, vector_store_url: str, openrouter_api_key: str):
        """Initialize unified context manager.

        Args:
            vector_store_url: URL for vector store
            openrouter_api_key: API key for OpenRouter
        """
        super().__init__(vector_store_url)
        self.roo_adapter = RooMCPAdapter(openrouter_api_key)
        self.weaviate_client = None
        self._initialize_weaviate()
        self.mode_contexts: Dict[str, Dict[str, Any]] = {}
        self.transition_history: List[Dict[str, Any]] = []

    def _initialize_weaviate(self) -> None:
        """Initialize Weaviate client for vector indexing."""
        try:
            weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
            openai_key = os.getenv("OPENAI_API_KEY", "")
            
            if not openai_key:
                logger.warning("OPENAI_API_KEY not set, Weaviate vectorization disabled")
                self.weaviate_client = None
                return
                
            self.weaviate_client = weaviate.Client(
                url=weaviate_url,
                additional_headers={
                    "X-OpenAI-Api-Key": openai_key
                },
                timeout_config=(5, 15)  # Connect timeout, read timeout
            )

            # Create schema for Roo outputs if not exists
            schema = {
                "class": "RooOutput",
                "description": "Outputs from Roo AI modes",
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"],
                        "description": "The output content",
                    },
                    {
                        "name": "mode",
                        "dataType": ["string"],
                        "description": "The Roo mode that generated this",
                    },
                    {
                        "name": "task",
                        "dataType": ["text"],
                        "description": "The task description",
                    },
                    {
                        "name": "session_id",
                        "dataType": ["string"],
                        "description": "Session identifier",
                    },
                    {
                        "name": "timestamp",
                        "dataType": ["date"],
                        "description": "Creation timestamp",
                    },
                ],
                "vectorizer": "text2vec-openai",
                "moduleConfig": {
                    "text2vec-openai": {
                        "model": "ada",
                        "modelVersion": "002",
                        "type": "text"
                    }
                }
            }

            if not self.weaviate_client.schema.exists("RooOutput"):
                self.weaviate_client.schema.create_class(schema)
                logger.info("Created Weaviate schema for RooOutput")

        except Exception as e:
            logger.warning(f"Weaviate initialization failed: {e}")
            self.weaviate_client = None

    @benchmark
    async def sync_context_bidirectional(
        self, session_id: str, source: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sync context bidirectionally between Roo and orchestrator.

        Args:
            session_id: Session identifier
            source: Source of context ('roo' or 'orchestrator')
            context: Context to sync

        Returns:
            Synchronized context
        """
        try:
            if source == "roo":
                # Transform Roo context to MCP format
                mcp_context = await self.roo_adapter.transform_context(
                    "roo", "mcp", context
                )
                await self.store_context(session_id, mcp_context)

                # Index in Weaviate if available
                if self.weaviate_client and "result" in context:
                    await self._index_roo_output(session_id, context)

                return mcp_context

            elif source == "orchestrator":
                # Transform MCP context to Roo format
                roo_context = await self.roo_adapter.transform_context(
                    "mcp", "roo", context
                )
                self.mode_contexts[session_id] = roo_context
                return roo_context

            else:
                raise ValueError(f"Unknown context source: {source}")

        except Exception as e:
            logger.error(f"Context sync error: {e}")
            raise

    async def _index_roo_output(
        self, session_id: str, context: Dict[str, Any]
    ) -> None:
        """Index Roo output in Weaviate.

        Args:
            session_id: Session identifier
            context: Roo context with output
        """
        if not self.weaviate_client:
            return

        try:
            data_object = {
                "content": context.get("result", ""),
                "mode": context.get("mode", "unknown"),
                "task": context.get("task", ""),
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Run Weaviate operation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.weaviate_client.data_object.create(
                    data_object=data_object, class_name="RooOutput"
                )
            )
            
            logger.debug(f"Indexed output for session {session_id}")

        except Exception as e:
            logger.error(f"Weaviate indexing error: {e}")

    async def search_roo_outputs(
        self, query: str, mode: Optional[str] = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search Roo outputs using semantic search.

        Args:
            query: Search query
            mode: Optional mode filter
            limit: Maximum results

        Returns:
            List of matching outputs
        """
        if not self.weaviate_client:
            return []

        try:
            where_filter = None
            if mode:
                where_filter = {
                    "path": ["mode"],
                    "operator": "Equal",
                    "valueString": mode,
                }

            result = (
                self.weaviate_client.query.get("RooOutput", ["content", "mode", "task", "timestamp"])
                .with_near_text({"concepts": [query]})
                .with_where(where_filter)
                .with_limit(limit)
                .do()
            )

            return result.get("data", {}).get("Get", {}).get("RooOutput", [])

        except Exception as e:
            logger.error(f"Weaviate search error: {e}")
            return []

    async def track_mode_transition(
        self,
        session_id: str,
        from_mode: RooMode,
        to_mode: RooMode,
        context: Dict[str, Any],
    ) -> None:
        """Track mode transitions for analysis.

        Args:
            session_id: Session identifier
            from_mode: Source mode
            to_mode: Target mode
            context: Transition context
        """
        transition = {
            "session_id": session_id,
            "from_mode": from_mode.value,
            "to_mode": to_mode.value,
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.transition_history.append(transition)

        # Store in database
        async with UnifiedDatabase() as db:
            await db.execute(
                """
                INSERT INTO mode_transitions
                (session_id, from_mode, to_mode, context, created_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                session_id,
                from_mode.value,
                to_mode.value,
                json.dumps(context),
                datetime.utcnow(),
            )

    def get_transition_patterns(self) -> Dict[str, int]:
        """Analyze mode transition patterns.

        Returns:
            Dictionary of transition patterns and counts
        """
        patterns = {}
        for transition in self.transition_history:
            key = f"{transition['from_mode']} -> {transition['to_mode']}"
            patterns[key] = patterns.get(key, 0) + 1
        return patterns

class MCPOrchestrator:
    """Orchestrates communication between MCP agents"""
    
    def __init__(self, context_manager: MCPContextManager):
        self.agents: Dict[str, MCPAgent] = {}
        self.context_manager = context_manager
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        
    def register_agent(self, agent: MCPAgent):
        """Register an MCP agent"""
        self.agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.name}")
    
    async def route_message(self, message: MCPMessage) -> MCPMessage:
        """Route message to appropriate agent"""
        if message.method.startswith("agent."):
            agent_id = message.params.get("agent_id")
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                
                try:
                    result = await agent.execute(message.params.get("task", {}))
                    return MCPMessage(
                        id=message.id,
                        type="response",
                        method=message.method,
                        result=result
                    )
                except Exception as e:
                    return MCPMessage(
                        id=message.id,
                        type="response",
                        method=message.method,
                        error={"code": -32603, "message": str(e)}
                    )
        
        return MCPMessage(
            id=message.id,
            type="response",
            method=message.method,
            error={"code": -32601, "message": "Method not found"}
        )
    
    async def coordinate_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate multi-agent workflow"""
        workflow_id = workflow.get("id", f"wf_{datetime.now().timestamp()}")
        self.active_workflows[workflow_id] = {
            "status": "running",
            "started": datetime.now().isoformat(),
            "steps": workflow.get("steps", []),
            "results": {}
        }
        
        try:
            # Execute workflow steps
            for step in workflow.get("steps", []):
                agent_id = step.get("agent_id")
                if agent_id not in self.agents:
                    raise ValueError(f"Unknown agent: {agent_id}")
                
                # Get context for this step
                context = await self.context_manager.retrieve_context(
                    workflow_id, 
                    step.get("context_query")
                )
                
                # Execute step
                agent = self.agents[agent_id]
                task = {**step.get("task", {}), "context": context}
                result = await agent.execute(task)
                
                # Store result in context
                self.active_workflows[workflow_id]["results"][step["id"]] = result
                await self.context_manager.store_context(
                    workflow_id,
                    {"step": step["id"], "result": result}
                )
            
            self.active_workflows[workflow_id]["status"] = "completed"
            return self.active_workflows[workflow_id]
            
        except Exception as e:
            logger.error(f"Workflow coordination error: {e}")
            self.active_workflows[workflow_id]["status"] = "failed"
            self.active_workflows[workflow_id]["error"] = str(e)
            raise
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            agent_id: {
                "name": agent.name,
                "status": agent.status,
                "capabilities": len(agent.get_capabilities()),
                "current_task": agent.current_task is not None
            }
            for agent_id, agent in self.agents.items()
        }

class MCPWebSocketServer:
    """WebSocket server for real-time MCP communication"""
    
    def __init__(self, orchestrator: MCPOrchestrator, port: int = 8765):
        self.orchestrator = orchestrator
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        
    async def handle_client(self, websocket, path):
        """Handle WebSocket client connections"""
        self.clients.add(websocket)
        try:
            async for message in websocket:
                # Parse MCP message
                data = json.loads(message)
                mcp_message = MCPMessage(**data)
                
                # Route through orchestrator
                response = await self.orchestrator.route_message(mcp_message)
                
                # Send response
                await websocket.send(json.dumps({
                    "id": response.id,
                    "type": response.type,
                    "method": response.method,
                    "result": response.result,
                    "error": response.error,
                    "timestamp": response.timestamp
                }))
                
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if self.clients:
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.clients],
                return_exceptions=True
            )
    
    async def start(self):
        """Start WebSocket server"""
        async with websockets.serve(self.handle_client, "0.0.0.0", self.port):
            logger.info(f"MCP WebSocket server started on port {self.port}")
            await asyncio.Future()  # Run forever