"""
Models package initialization.

This module exports all models for easy importing throughout the application.
"""

# Export classes from base_models (legacy models)
from .base_models import MemoryItem, PersonaConfig as LegacyPersonaConfig

# Export classes from core_models (definitive versions going forward)
from .core_models import AgentData, PersonaConfig, UserInteraction

# Export classes from domain_models
from .domain_models import (
    AgentResponse,
    Configuration,
    MemoryRecord,
    PayReadyContact,
    PayReadyLead,
    UserRequest,
    WorkflowState,
)

__all__ = [
    # Legacy base models
    "LegacyPersonaConfig",
    "MemoryItem",
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
