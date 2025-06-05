import os
# TODO: Consider adding connection pooling configuration
"""
Cherry AI - Database Models
This module contains Pydantic models for database entities.
"""

from typing import List, Dict, Any, Optional
from typing_extensions import Optional, Union
from uuid import uuid4, UUID
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator

""
    """Memory storage types supported by the system."""
    REDIS = "redis"
    PGVECTOR = "pgvector"
    mongodb = "mongodb"
    OPENAI_VECTOR = "vertex_vector"
    IN_MEMORY = "in_memory"

class MemoryConfig(BaseModel):
    """Configuration for agent memory systems."""
    @validator("table_name")
    def validate_table_name(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        if values.get("memory_type") in [MemoryType.PGVECTOR] and not v:
            raise ValueError(f"table_name required for {values['memory_type']} memory type")
        return v

    @validator("vector_dimension")
    def validate_vector_dimension(cls, v: Optional[int], values: Dict[str, Any]) -> Optional[int]:
        if values.get("memory_type") in [MemoryType.PGVECTOR, MemoryType.OPENAI_VECTOR] and not v:
            raise ValueError(f"vector_dimension required for {values['memory_type']} memory type")
        return v

class ToolConfig(BaseModel):
    """Configuration for agent tools."""
    """Capabilities that agents can provide."""
    TEXT_GENERATION = "text_generation"
    QUESTION_ANSWERING = "question_answering"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    CREATIVE_WRITING = "creative_writing"
    FACTUAL_RESPONSE = "factual_response"
    CODE_GENERATION = "code_generation"
    MULTI_MODAL = "multi_modal"
    GENERAL = "general"

class AgentConfig(BaseModel):
    """Configuration for individual agents."""
    wrapper_type: str = Field(..., description="Framework integration type (phidata, langchain, etc)")
    agent_class: str = Field(..., description="Fully qualified class path")
    llm_ref: str
    tools: Optional[List[ToolConfig]] = None
    role: str
    instructions: List[str]
    memory: Optional[MemoryConfig] = None
    capabilities: List[AgentCapability] = [AgentCapability.GENERAL]
    priority: int = 0

    # Environment-specific overrides
    env_overrides: Optional[Dict[str, Dict[str, Any]]] = None

    # Validators for specific wrapper types
    @validator("agent_class")
    def validate_agent_class(cls, v: str, values: Dict[str, Any]) -> str:
        wrapper_type = values.get("wrapper_type")
        if wrapper_type == "phidata" and not v.startswith("agno."):
            raise ValueError(f"PhiData agents must use agno.* classes, got {v}")
        return v

class TeamMode(str, Enum):
    """Team coordination modes."""
    COORDINATE = "coordinate"
    COMPETE = "compete"
    COLLABORATE = "collaborate"
    DEBATE = "debate"

class ControllerConfig(BaseModel):
    """Configuration for team controllers."""
    """Configuration for agent teams."""
    """Registry of all agent and team configurations."""
        agent_defs = values.get("agent_definitions", {})
        agent_ids = set(agent_defs.keys())

        for agent_id, config in agent_defs.items():
            if hasattr(config, "members") and isinstance(config.members, list):
                for member in config.members:
                    if member not in agent_ids:
                        raise ValueError(f"Team {agent_id} references unknown agent {member}")
        return values

class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    AZURE = "azure"
    ANTHROPIC = "anthropic"
    OPENAI = "vertex"
PORTKEY = os.getenv("CORE_MODELS_KEY", "")
    OPENROUTER = "openrouter"

class LLMConfig(BaseModel):
    """Configuration for LLM models."""
    api_key_ref: str = Field(..., description="Reference to API key in Secret Manager")
    api_version: Optional[str] = None
    extra_headers: Optional[Dict[str, str]] = None

    # Provider-specific parameters
    provider_params: Optional[Dict[str, Any]] = None

class LLMRegistry(BaseModel):
    """Registry of all LLM configurations."""
    @validator("default_llm")
    def validate_default_llm(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        if v and v not in values.get("llm_definitions", {}):
            raise ValueError(f"Default LLM {v} not found in llm_definitions")
        return v
