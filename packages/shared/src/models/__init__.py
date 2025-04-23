"""
Models package initialization.

This module exports all models for easy importing throughout the application.
"""

# Export classes from base_models (legacy models)
from .base_models import PersonaConfig as LegacyPersonaConfig
from .base_models import MemoryItem
from .base_models import AgentData as LegacyAgentData

# Export classes from domain_models
from .domain_models import (
    UserRequest,
    AgentResponse,
    MemoryRecord,
    WorkflowState,
    PayReadyContact,
    PayReadyLead,
    Configuration,
)

# Export classes from core_models (definitive versions going forward)
from .core_models import PersonaConfig, UserInteraction, AgentData

__all__ = [
    # Legacy base models
    "LegacyPersonaConfig",
    "MemoryItem",
    "LegacyAgentData",
    # Domain models
    "UserRequest",
    "AgentResponse",
    "MemoryRecord",
    "WorkflowState",
    "PayReadyContact",
    "PayReadyLead",
    "Configuration",
    # Core models (definitive versions)
    "PersonaConfig",
    "UserInteraction",
    "AgentData",
]
