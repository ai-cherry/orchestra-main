"""Agent service module for Orchestra AI."""

from core.services.agents.base import (
    Agent,
    AgentCapability,
    AgentConfig,
    AgentManager,
    AgentMessage,
    AgentState,
    AgentStatus,
    get_agent_manager,
)
from core.services.agents.examples import (
    CollaborativeAgent,
    ConversationalAgent,
    ResearchAgent,
    TaskExecutorAgent,
    create_example_agents,
    register_example_agents,
)

__all__ = [
    "Agent",
    "AgentCapability",
    "AgentConfig",
    "AgentManager",
    "AgentMessage",
    "AgentState",
    "AgentStatus",
    "get_agent_manager",
    "CollaborativeAgent",
    "ConversationalAgent",
    "ResearchAgent",
    "TaskExecutorAgent",
    "create_example_agents",
    "register_example_agents",
]
