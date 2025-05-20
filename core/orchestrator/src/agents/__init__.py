"""
Agents module for AI Orchestration System.

This module provides the agent interfaces and implementations used
by the orchestration system to process user interactions.
"""

from core.orchestrator.src.agents.agent_base import Agent, AgentContext, AgentResponse
from core.orchestrator.src.agents.agent_registry import (
    AgentRegistry,
    get_agent_registry,
)
from core.orchestrator.src.agents.llm_agent import LLMAgent, ConversationFormatter

# Import PersonaAwareAgent instead of PersonaAgent
from core.orchestrator.src.agents.persona_agent import PersonaAwareAgent

__all__ = [
    "Agent",
    "AgentContext",
    "AgentResponse",
    "AgentRegistry",
    "get_agent_registry",
    # Include PersonaAwareAgent in __all__
    "PersonaAwareAgent",
    "LLMAgent",
    "ConversationFormatter",
]
