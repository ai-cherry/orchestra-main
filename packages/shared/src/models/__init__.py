# TODO: Consider adding connection pooling configuration
"""
Orchestra AI - Database Models
This module contains Pydantic models for database entities.
"""

from typing import List, Dict, Any, Optional, Union
from uuid import uuid4, UUID
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator

""
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
