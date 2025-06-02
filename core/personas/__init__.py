"""
Orchestrator persona configuration system.

This package provides comprehensive models for managing AI personas
in the admin interface, including configuration, traits, behaviors,
and runtime settings.
"""

from core.personas.manager import (
    PersonaConfigError,
    PersonaConfigManager,
    PersonaNotFoundError,
)
from core.personas.models import (
    BehaviorRule,
    InteractionMode,
    KnowledgeDomain,
    MemoryConfiguration,
    PersonaConfiguration,
    PersonaMetrics,
    PersonaStatus,
    PersonaTemplate,
    PersonaTrait,
    ResponseStyle,
    ResponseStyleType,
    TraitCategory,
    VoiceConfiguration,
)

__all__ = [
    # Enums
    "PersonaStatus",
    "TraitCategory",
    "ResponseStyleType",
    "InteractionMode",
    # Core Models
    "PersonaTrait",
    "ResponseStyle",
    "KnowledgeDomain",
    "BehaviorRule",
    # Configuration Models
    "MemoryConfiguration",
    "VoiceConfiguration",
    # Template and Metrics
    "PersonaTemplate",
    "PersonaMetrics",
    # Main Configuration
    "PersonaConfiguration",
    # Manager and Exceptions
    "PersonaConfigManager",
    "PersonaConfigError",
    "PersonaNotFoundError",
]

__version__ = "1.0.0"
