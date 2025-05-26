#!/usr/bin/env python
"""
Orchestra Adapter for SuperAGI Integration
==========================================
This module provides the adapter layer between SuperAGI and Orchestra systems.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

import redis.asyncio as redis
from google.cloud import firestore

# Import Orchestra components
from core.orchestrator.src.agents.agent_base import Agent, AgentContext, AgentResponse
from core.orchestrator.src.agents.simplified_agent_registry import AgentRegistry
from core.orchestrator.src.memory.memory_manager import MemoryManager
from core.orchestrator.src.personas.persona_manager import PersonaManager
from core.orchestrator.src.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class SuperAGIAgent(Agent):
    """
    SuperAGI-compatible agent that extends the Orchestra Agent base class.
    """

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        """Initialize SuperAGI agent"""
        super().__init__()
        self.agent_id = agent_id
        self.config = config
        self.tools: List[Dict[str, Any]] = []
        self.memory_enabled = config.get("memory_enabled", True)
        self.max_iterations = config.get("max_iterations", 5)

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a request using SuperAGI capabilities"""
        start_time = asyncio.get_event_loop().time()

        try:
            # Extract task and parameters
            task = context.user_input
            memory_context = context.metadata.get("memory", {})

            # Execute autonomous agent logic
            result = await self._execute_autonomous_task(
                task=task,
                context=memory_context,
                tools=self.tools,
                max_iterations=self.max_iterations,
            )

            # Calculate execution time
            execution_time = asyncio.get_event_loop().time() - start_time

            return AgentResponse(
                content=result["output"],
                metadata={
                    "agent_id": self.agent_id,
                    "execution_time": execution_time,
                    "iterations": result.get("iterations", 1),
                    "tools_used": result.get("tools_used", []),
                    "tokens_used": result.get("tokens_used", 0),
                    "store_memory": self.memory_enabled,
                },
            )

        except Exception as e:
            logger.error(f"SuperAGI agent processing failed: {str(e)}")
            return AgentResponse(
                content=f"Error: {str(e)}",
                metadata={"error": True, "agent_id": self.agent_id},
            )

    async def _execute_autonomous_task(
        self,
        task: str,
        context: Dict[str, Any],
        tools: List[Dict[str, Any]],
        max_iterations: int,
    ) -> Dict[str, Any]:
        """Execute an autonomous task with reasoning and tool usage"""
        # This is a simplified implementation
        # In production, this would integrate with SuperAGI's reasoning engine

        iterations = 0
        tools_used = []
        total_tokens = 0

        # Simulate autonomous execution
        for i in range(min(max_iterations, 5)):
            iterations += 1

            # Simulate tool selection and execution
            if tools and i < len(tools):
                tool = tools[i]
                tools_used.append(tool["name"])

            # Simulate token usage
            total_tokens += 100 + (i * 50)

            # Check if task is complete (simplified logic)
            if "simple" in task.lower() or i >= 2:
                break

        # Generate output based on task
        output = f"Completed task: {task}\n"
        output += f"Used {iterations} iterations and {len(tools_used)} tools.\n"
        if context:
            output += f"Context utilized: {list(context.keys())}\n"

        return {
            "output": output,
            "iterations": iterations,
            "tools_used": tools_used,
            "tokens_used": total_tokens,
        }

    def add_tool(self, tool_config: Dict[str, Any]) -> None:
        """Add a tool to the agent"""
        self.tools.append(tool_config)


class OrchestraAdapter:
    """
    Adapter that bridges SuperAGI with Orchestra components.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        firestore_client: Optional[firestore.Client],
        config: Dict[str, Any],
    ):
        """Initialize the adapter"""
        self.redis_client = redis_client
        self.firestore_client = firestore_client
        self.config = config

        # Orchestra components
        self.memory_manager: Optional[MemoryManager] = config.get("memory_manager")
        self.persona_manager: Optional[PersonaManager] = config.get("persona_manager")
        self.agent_registry = AgentRegistry()
        self.orchestrator: Optional[Orchestrator] = None

        # SuperAGI agents
        self.superagi_agents: Dict[str, SuperAGIAgent] = {}

    async def initialize(self) -> None:
        """Initialize the adapter and register agents"""
        logger.info("Initializing Orchestra adapter...")

        # Initialize orchestrator if components are available
        if self.memory_manager and self.persona_manager:
            from core.orchestrator.src.orchestrator import Orchestrator

            self.orchestrator = Orchestrator(
                memory_manager=self.memory_manager,
                persona_manager=self.persona_manager,
                agent_registry=self.agent_registry,
            )

        # Register default SuperAGI agents
        await self._register_default_agents()

        logger.info("Orchestra adapter initialized successfully")

    async def _register_default_agents(self) -> None:
        """Register default SuperAGI agents"""
        default_agents = [
            {
                "id": "researcher",
                "name": "Research Agent",
                "description": "Autonomous agent for research tasks",
                "config": {
                    "memory_enabled": True,
                    "max_iterations": 5,
                    "capabilities": ["web_search", "summarization", "analysis"],
                },
            },
            {
                "id": "coder",
                "name": "Coding Agent",
                "description": "Autonomous agent for coding tasks",
                "config": {
                    "memory_enabled": True,
                    "max_iterations": 10,
                    "capabilities": ["code_generation", "debugging", "refactoring"],
                },
            },
            {
                "id": "analyst",
                "name": "Analysis Agent",
                "description": "Autonomous agent for data analysis",
                "config": {
                    "memory_enabled": True,
                    "max_iterations": 7,
                    "capabilities": ["data_analysis", "visualization", "reporting"],
                },
            },
        ]

        for agent_config in default_agents:
            agent = SuperAGIAgent(
                agent_id=agent_config["id"], config=agent_config["config"]
            )
            self.superagi_agents[agent_config["id"]] = agent
            self.agent_registry.register(agent_config["id"], agent)

            # Store agent metadata in Firestore if available
            if self.firestore_client:
                doc_ref = self.firestore_client.collection("agents").document(
                    agent_config["id"]
                )
                await asyncio.to_thread(
                    doc_ref.set,
                    {
                        **agent_config,
                        "created_at": datetime.utcnow(),
                        "status": "active",
                    },
                )

    async def execute_agent(
        self, agent_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an agent with the given context"""
        # Get the agent
        agent = self.superagi_agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Create agent context
        agent_context = AgentContext(
            user_input=context.get("task", ""), metadata=context
        )

        # Execute through orchestrator if available
        if self.orchestrator and context.get("persona_id"):
            result = await self.orchestrator.process_interaction(
                user_input=context.get("task", ""),
                persona_id=context.get("persona_id"),
                agent_type=agent_id,
            )
            return {
                "output": result.response,
                "execution_time": result.metadata.get("execution_time", 0),
                "tokens_used": result.metadata.get("tokens_used", 0),
                "store_memory": True,
            }
        else:
            # Direct agent execution
            response = await agent.process(agent_context)
            return {"output": response.content, **response.metadata}

    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all available agents"""
        agents = []

        # Get from memory
        for agent_id, agent in self.superagi_agents.items():
            agents.append(
                {
                    "id": agent_id,
                    "type": "superagi",
                    "config": agent.config,
                    "tools": len(agent.tools),
                }
            )

        # Get from Firestore if available
        if self.firestore_client:
            agents_ref = self.firestore_client.collection("agents")
            docs = await asyncio.to_thread(agents_ref.get)
            for doc in docs:
                agent_data = doc.to_dict()
                if doc.id not in self.superagi_agents:
                    agents.append({"id": doc.id, "type": "superagi", **agent_data})

        return agents

    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent details"""
        # Check in memory first
        if agent_id in self.superagi_agents:
            agent = self.superagi_agents[agent_id]
            return {
                "id": agent_id,
                "type": "superagi",
                "config": agent.config,
                "tools": [tool["name"] for tool in agent.tools],
                "memory_enabled": agent.memory_enabled,
                "max_iterations": agent.max_iterations,
            }

        # Check Firestore
        if self.firestore_client:
            doc_ref = self.firestore_client.collection("agents").document(agent_id)
            doc = await asyncio.to_thread(doc_ref.get)
            if doc.exists:
                return {"id": agent_id, "type": "superagi", **doc.to_dict()}

        return None

    async def add_agent_tool(
        self, agent_id: str, tool_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add a tool to an agent"""
        agent = self.superagi_agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Validate tool config
        if "name" not in tool_config:
            raise ValueError("Tool config must include 'name'")

        # Add tool to agent
        agent.add_tool(tool_config)

        # Update Firestore if available
        if self.firestore_client:
            doc_ref = self.firestore_client.collection("agents").document(agent_id)
            await asyncio.to_thread(
                doc_ref.update,
                {
                    "tools": firestore.ArrayUnion([tool_config]),
                    "updated_at": datetime.utcnow(),
                },
            )

        return {"agent_id": agent_id, "tool": tool_config["name"], "status": "added"}

    async def shutdown(self) -> None:
        """Cleanup resources"""
        logger.info("Shutting down Orchestra adapter...")
        # Add any cleanup logic here
        pass
