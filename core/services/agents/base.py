"""
Base agent abstractions for Orchestra AI.

This module provides interfaces for creating and managing AI agents
with specific capabilities and behaviors.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from core.business.workflows.base import WorkflowContext, get_workflow_engine
from core.services.events.event_bus import Event, get_event_bus
from core.services.memory.unified_memory import get_memory_service


logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent lifecycle status."""

    IDLE = "idle"
    BUSY = "busy"
    THINKING = "thinking"
    EXECUTING = "executing"
    ERROR = "error"
    STOPPED = "stopped"


class AgentCapability(Enum):
    """Agent capabilities."""

    CONVERSATION = "conversation"
    TASK_EXECUTION = "task_execution"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    CREATIVITY = "creativity"
    PLANNING = "planning"
    MONITORING = "monitoring"
    COLLABORATION = "collaboration"


@dataclass
class AgentMessage:
    """Message between agents or from users."""

    id: UUID = field(default_factory=uuid4)
    sender_id: str = ""
    recipient_id: Optional[str] = None
    content: str = ""
    message_type: str = "text"
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentConfig:
    """Configuration for an agent."""

    id: str
    name: str
    description: str
    capabilities: Set[AgentCapability] = field(default_factory=set)
    persona_id: Optional[str] = None
    workflow_names: List[str] = field(default_factory=list)
    max_concurrent_tasks: int = 5
    memory_enabled: bool = True
    collaboration_enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentState:
    """Current state of an agent."""

    agent_id: str
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    active_workflows: List[UUID] = field(default_factory=list)
    message_queue: List[AgentMessage] = field(default_factory=list)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class Agent(ABC):
    """Abstract base class for AI agents."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.state = AgentState(agent_id=config.id)
        self._event_bus = get_event_bus()
        self._memory_service = get_memory_service() if config.memory_enabled else None
        self._workflow_engine = get_workflow_engine()
        self._running = False
        self._tasks: Set[asyncio.Task] = set()

    @abstractmethod
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process an incoming message and optionally return a response."""
        pass

    @abstractmethod
    async def think(self) -> None:
        """Agent's thinking/reasoning process."""
        pass

    @abstractmethod
    async def act(self) -> None:
        """Agent's action execution process."""
        pass

    async def start(self) -> None:
        """Start the agent."""
        self._running = True
        self.state.status = AgentStatus.IDLE

        # Start main loop
        main_task = asyncio.create_task(self._main_loop())
        self._tasks.add(main_task)

        # Subscribe to events
        await self._subscribe_to_events()

        # Emit agent started event
        await self._event_bus.publish(
            Event(
                type="agent.started",
                data={
                    "agent_id": self.config.id,
                    "agent_name": self.config.name,
                    "capabilities": [cap.value for cap in self.config.capabilities],
                },
            )
        )

        logger.info(f"Agent {self.config.name} started")

    async def stop(self) -> None:
        """Stop the agent."""
        self._running = False
        self.state.status = AgentStatus.STOPPED

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)

        # Emit agent stopped event
        await self._event_bus.publish(
            Event(
                type="agent.stopped",
                data={"agent_id": self.config.id, "agent_name": self.config.name},
            )
        )

        logger.info(f"Agent {self.config.name} stopped")

    async def send_message(
        self, recipient_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send a message to another agent or user."""
        message = AgentMessage(
            sender_id=self.config.id,
            recipient_id=recipient_id,
            content=content,
            metadata=metadata or {},
        )

        # Publish message event
        await self._event_bus.publish(
            Event(
                type="agent.message",
                data={
                    "message": message.__dict__,
                    "sender_id": self.config.id,
                    "recipient_id": recipient_id,
                },
            )
        )

    async def receive_message(self, message: AgentMessage) -> None:
        """Receive a message."""
        # Add to queue
        self.state.message_queue.append(message)

        # Process immediately if idle
        if self.state.status == AgentStatus.IDLE:
            await self._process_message_queue()

    async def execute_workflow(
        self, workflow_name: str, inputs: Dict[str, Any]
    ) -> WorkflowContext:
        """Execute a workflow."""
        if workflow_name not in self.config.workflow_names:
            raise ValueError(f"Workflow '{workflow_name}' not available for this agent")

        # Update status
        self.state.status = AgentStatus.EXECUTING

        try:
            # Execute workflow
            context = await self._workflow_engine.execute_workflow(
                workflow_name, inputs
            )

            # Track active workflow
            self.state.active_workflows.append(context.workflow_id)

            return context

        finally:
            # Update status
            if not self.state.active_workflows:
                self.state.status = AgentStatus.IDLE

    async def remember(
        self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store information in agent's memory."""
        if not self._memory_service:
            return

        agent_metadata = {
            "agent_id": self.config.id,
            "agent_name": self.config.name,
            **(metadata or {}),
        }

        await self._memory_service.store(
            key=f"agent:{self.config.id}:{key}", value=value, metadata=agent_metadata
        )

    async def recall(self, query: str, limit: int = 10) -> List[Any]:
        """Recall information from agent's memory."""
        if not self._memory_service:
            return []

        results = await self._memory_service.search(
            query=query, limit=limit, metadata_filter={"agent_id": self.config.id}
        )

        return results

    async def collaborate_with(
        self, agent_id: str, task: str, context: Dict[str, Any]
    ) -> Any:
        """Collaborate with another agent on a task."""
        if not self.config.collaboration_enabled:
            raise ValueError("Collaboration is not enabled for this agent")

        # Send collaboration request
        await self.send_message(
            recipient_id=agent_id,
            content=f"Collaboration request: {task}",
            metadata={
                "type": "collaboration_request",
                "task": task,
                "context": context,
            },
        )

        # Wait for response (simplified - in practice would be more complex)
        # This is a placeholder for actual collaboration logic
        await asyncio.sleep(1)

        return {"status": "collaboration_initiated", "task": task}

    async def _main_loop(self) -> None:
        """Main agent loop."""
        while self._running:
            try:
                # Process message queue
                if self.state.message_queue:
                    await self._process_message_queue()

                # Think
                if self.state.status == AgentStatus.IDLE:
                    self.state.status = AgentStatus.THINKING
                    await self.think()

                # Act
                if self.state.status == AgentStatus.THINKING:
                    self.state.status = AgentStatus.EXECUTING
                    await self.act()
                    self.state.status = AgentStatus.IDLE

                # Update last activity
                self.state.last_activity = datetime.utcnow()

                # Small delay to prevent busy loop
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(
                    f"Error in agent {self.config.name} main loop: {e}", exc_info=True
                )
                self.state.status = AgentStatus.ERROR
                await asyncio.sleep(1)  # Back off on error

    async def _process_message_queue(self) -> None:
        """Process queued messages."""
        while self.state.message_queue:
            message = self.state.message_queue.pop(0)

            try:
                response = await self.process_message(message)

                if response and message.sender_id:
                    await self.send_message(
                        recipient_id=message.sender_id,
                        content=response.content,
                        metadata=response.metadata,
                    )

            except Exception as e:
                logger.error(
                    f"Error processing message in agent {self.config.name}: {e}",
                    exc_info=True,
                )

    async def _subscribe_to_events(self) -> None:
        """Subscribe to relevant events."""

        # Subscribe to messages for this agent
        async def handle_message(event: Event) -> None:
            if event.data.get("recipient_id") == self.config.id:
                message_data = event.data.get("message", {})
                message = AgentMessage(**message_data)
                await self.receive_message(message)

        await self._event_bus.subscribe("agent.message", handle_message)

        # Subscribe to collaboration requests if enabled
        if self.config.collaboration_enabled:

            async def handle_collaboration(event: Event) -> None:
                if event.data.get("recipient_id") == self.config.id:
                    # Handle collaboration request
                    pass

            await self._event_bus.subscribe("agent.collaboration", handle_collaboration)


class AgentManager:
    """Manages multiple agents and their interactions."""

    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._event_bus = get_event_bus()

    def register_agent(self, agent: Agent) -> None:
        """Register an agent with the manager."""
        self._agents[agent.config.id] = agent
        logger.info(f"Registered agent: {agent.config.name}")

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        return self._agents.get(agent_id)

    def list_agents(self) -> List[AgentConfig]:
        """List all registered agents."""
        return [agent.config for agent in self._agents.values()]

    async def start_agent(self, agent_id: str) -> bool:
        """Start a specific agent."""
        agent = self._agents.get(agent_id)
        if not agent:
            return False

        await agent.start()
        return True

    async def stop_agent(self, agent_id: str) -> bool:
        """Stop a specific agent."""
        agent = self._agents.get(agent_id)
        if not agent:
            return False

        await agent.stop()
        return True

    async def start_all_agents(self) -> None:
        """Start all registered agents."""
        tasks = [agent.start() for agent in self._agents.values()]
        await asyncio.gather(*tasks)

    async def stop_all_agents(self) -> None:
        """Stop all registered agents."""
        tasks = [agent.stop() for agent in self._agents.values()]
        await asyncio.gather(*tasks)

    async def broadcast_message(
        self, sender_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Broadcast a message to all agents."""
        message = AgentMessage(
            sender_id=sender_id, content=content, metadata=metadata or {}
        )

        # Send to all agents except sender
        for agent_id, agent in self._agents.items():
            if agent_id != sender_id:
                await agent.receive_message(message)

    def find_agents_by_capability(self, capability: AgentCapability) -> List[Agent]:
        """Find agents with a specific capability."""
        return [
            agent
            for agent in self._agents.values()
            if capability in agent.config.capabilities
        ]

    async def assign_task(
        self, task: str, required_capability: AgentCapability
    ) -> Optional[str]:
        """Assign a task to the most suitable agent."""
        suitable_agents = self.find_agents_by_capability(required_capability)

        if not suitable_agents:
            return None

        # Find the least busy agent
        best_agent = min(suitable_agents, key=lambda a: len(a.state.active_workflows))

        # Send task to agent
        await best_agent.receive_message(
            AgentMessage(
                sender_id="system", content=task, metadata={"type": "task_assignment"}
            )
        )

        return best_agent.config.id


# Global agent manager instance
_agent_manager: Optional[AgentManager] = None


def get_agent_manager() -> AgentManager:
    """Get the global agent manager instance."""
    global _agent_manager

    if _agent_manager is None:
        _agent_manager = AgentManager()

    return _agent_manager
