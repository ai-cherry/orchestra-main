"""
Services module for AI Orchestration System.

This module provides various services used by the orchestration system,
including event bus, registry, memory service, and LLM providers.
"""

from core.orchestrator.src.services.event_bus import EventBus, get_event_bus
from core.orchestrator.src.services.registry import (
    ServiceRegistry,
    get_service_registry,
)
from core.orchestrator.src.services.memory_service import (
    MemoryService,
    get_memory_service,
)
from core.orchestrator.src.services.agent_orchestrator import (
    AgentOrchestrator,
    get_agent_orchestrator,
)
from core.orchestrator.src.services.enhanced_agent_orchestrator import (
    EnhancedAgentOrchestrator,
    get_enhanced_agent_orchestrator,
)
from core.orchestrator.src.services.llm import (
    LLMProvider,
    OpenRouterProvider,
    get_llm_provider,
    register_llm_provider,
)

__all__ = [
    # Event bus
    "EventBus",
    "get_event_bus",
    # Service registry
    "ServiceRegistry",
    "get_service_registry",
    # Memory service
    "MemoryService",
    "get_memory_service",
    # Orchestrators
    "AgentOrchestrator",
    "get_agent_orchestrator",
    "EnhancedAgentOrchestrator",
    "get_enhanced_agent_orchestrator",
    # LLM providers
    "LLMProvider",
    "OpenRouterProvider",
    "get_llm_provider",
    "register_llm_provider",
]
