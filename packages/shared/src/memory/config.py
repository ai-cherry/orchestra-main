"""
Memory configuration system for AI Orchestra.

This module provides a hierarchical configuration system for memory components
using Pydantic models. It supports environment variable overrides, default values,
and validation with helpful error messages.
"""

import os
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator, root_validator


class MemoryBackendType(str, Enum):
    """Enum for memory backend types."""

    FIRESTORE = "firestore"
    REDIS = "redis"
    IN_MEMORY = "in_memory"


class VectorSearchType(str, Enum):
    """Enum for vector search types."""

    IN_MEMORY = "in_memory"
    VERTEX = "vertex"
    NONE = "none"


class FirestoreConfig(BaseModel):
    """Configuration for Firestore backend."""

    project_id: Optional[str] = Field(
        default=None, description="Google Cloud project ID"
    )
    credentials_json: Optional[str] = Field(
        default=None, description="JSON string containing service account credentials"
    )
    credentials_path: Optional[str] = Field(
        default=None, description="Path to service account credentials file"
    )
    namespace: str = Field(
        default="default", description="Namespace for memory isolation"
    )
    connection_pool_size: int = Field(
        default=10, description="Size of the connection pool for Firestore", ge=1
    )
    batch_size: Optional[int] = Field(
        default=None, description="Batch size for Firestore operations"
    )
    max_errors_before_unhealthy: int = Field(
        default=10,
        description="Threshold for number of errors before health status is degraded",
        ge=1,
    )

    @validator("project_id", pre=True, always=True)
    def set_project_id_from_env(cls, v):
        """Set project_id from environment variable if not provided."""
        if v is None:
            return os.environ.get("GOOGLE_CLOUD_PROJECT")
        return v

    @validator("credentials_path", pre=True, always=True)
    def set_credentials_path_from_env(cls, v):
        """Set credentials_path from environment variable if not provided."""
        if v is None:
            return os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        return v


class RedisConfig(BaseModel):
    """Configuration for Redis backend."""

    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port", ge=1, le=65535)
    db: int = Field(default=0, description="Redis database number", ge=0)
    password: Optional[str] = Field(default=None, description="Redis password")
    ssl: bool = Field(
        default=False, description="Whether to use SSL for Redis connection"
    )
    namespace: str = Field(
        default="default", description="Namespace for memory isolation"
    )
    ttl: Optional[int] = Field(
        default=None, description="Default TTL for Redis keys in seconds"
    )
    connection_pool_size: int = Field(
        default=10, description="Size of the connection pool for Redis", ge=1
    )
    max_errors_before_unhealthy: int = Field(
        default=10,
        description="Threshold for number of errors before health status is degraded",
        ge=1,
    )

    @validator("host", pre=True, always=True)
    def set_host_from_env(cls, v):
        """Set host from environment variable if available."""
        return os.environ.get("REDIS_HOST", v)

    @validator("port", pre=True, always=True)
    def set_port_from_env(cls, v):
        """Set port from environment variable if available."""
        port_str = os.environ.get("REDIS_PORT")
        if port_str:
            try:
                return int(port_str)
            except ValueError:
                pass
        return v

    @validator("password", pre=True, always=True)
    def set_password_from_env(cls, v):
        """Set password from environment variable if available."""
        if v is None:
            return os.environ.get("REDIS_PASSWORD")
        return v


class InMemoryConfig(BaseModel):
    """Configuration for in-memory backend."""

    namespace: str = Field(
        default="default", description="Namespace for memory isolation"
    )
    max_items: int = Field(
        default=10000, description="Maximum number of items to store in memory", ge=1
    )
    ttl: Optional[int] = Field(
        default=None, description="Default TTL for memory items in seconds"
    )


class VertexVectorSearchConfig(BaseModel):
    """Configuration for Vertex AI Vector Search."""

    project_id: Optional[str] = Field(
        default=None, description="Google Cloud project ID"
    )
    location: str = Field(default="us-west4", description="Google Cloud region")
    index_endpoint_id: str = Field(..., description="Vector Search index endpoint ID")
    index_id: str = Field(..., description="Vector Search index ID")

    @validator("project_id", pre=True, always=True)
    def set_project_id_from_env(cls, v):
        """Set project_id from environment variable if not provided."""
        if v is None:
            return os.environ.get("GOOGLE_CLOUD_PROJECT")
        return v


class InMemoryVectorSearchConfig(BaseModel):
    """Configuration for in-memory vector search."""

    dimensions: int = Field(
        default=768, description="Dimensionality of the vectors", ge=1
    )


class VectorSearchConfig(BaseModel):
    """Configuration for vector search."""

    provider: VectorSearchType = Field(
        default=VectorSearchType.IN_MEMORY, description="Vector search provider to use"
    )
    in_memory: Optional[InMemoryVectorSearchConfig] = Field(
        default=None, description="Configuration for in-memory vector search"
    )
    vertex: Optional[VertexVectorSearchConfig] = Field(
        default=None, description="Configuration for Vertex AI Vector Search"
    )

    @root_validator
    def validate_provider_config(cls, values):
        """Validate that the appropriate provider config is provided."""
        provider = values.get("provider")
        if provider == VectorSearchType.IN_MEMORY and values.get("in_memory") is None:
            values["in_memory"] = InMemoryVectorSearchConfig()
        elif provider == VectorSearchType.VERTEX and values.get("vertex") is None:
            raise ValueError(
                "Vertex AI Vector Search configuration is required when provider is 'vertex'"
            )
        return values


class TelemetryConfig(BaseModel):
    """Configuration for telemetry."""

    enabled: bool = Field(default=True, description="Whether telemetry is enabled")
    log_level: str = Field(default="INFO", description="Log level for telemetry")
    trace_sampling_rate: float = Field(
        default=0.1, description="Sampling rate for distributed tracing", ge=0.0, le=1.0
    )
    metrics_export_interval_seconds: int = Field(
        default=60, description="Interval for exporting metrics in seconds", ge=1
    )


class MemoryConfig(BaseModel):
    """Root configuration for memory system."""

    backend: MemoryBackendType = Field(
        default=MemoryBackendType.FIRESTORE, description="Memory backend to use"
    )
    firestore: Optional[FirestoreConfig] = Field(
        default=None, description="Configuration for Firestore backend"
    )
    redis: Optional[RedisConfig] = Field(
        default=None, description="Configuration for Redis backend"
    )
    in_memory: Optional[InMemoryConfig] = Field(
        default=None, description="Configuration for in-memory backend"
    )
    vector_search: Optional[VectorSearchConfig] = Field(
        default=None, description="Configuration for vector search"
    )
    telemetry: Optional[TelemetryConfig] = Field(
        default=None, description="Configuration for telemetry"
    )

    @root_validator
    def validate_backend_config(cls, values):
        """Validate that the appropriate backend config is provided."""
        backend = values.get("backend")
        if backend == MemoryBackendType.FIRESTORE and values.get("firestore") is None:
            values["firestore"] = FirestoreConfig()
        elif backend == MemoryBackendType.REDIS and values.get("redis") is None:
            values["redis"] = RedisConfig()
        elif backend == MemoryBackendType.IN_MEMORY and values.get("in_memory") is None:
            values["in_memory"] = InMemoryConfig()

        # Ensure vector search config is present
        if values.get("vector_search") is None:
            values["vector_search"] = VectorSearchConfig()

        # Ensure telemetry config is present
        if values.get("telemetry") is None:
            values["telemetry"] = TelemetryConfig()

        return values

    @classmethod
    def from_env(cls) -> "MemoryConfig":
        """Create a configuration from environment variables."""
        backend_str = os.environ.get("MEMORY_BACKEND", "firestore").lower()
        try:
            backend = MemoryBackendType(backend_str)
        except ValueError:
            backend = MemoryBackendType.FIRESTORE

        vector_search_str = os.environ.get(
            "VECTOR_SEARCH_PROVIDER", "in_memory"
        ).lower()
        try:
            vector_search_provider = VectorSearchType(vector_search_str)
        except ValueError:
            vector_search_provider = VectorSearchType.IN_MEMORY

        # Create config with values from environment variables
        config_dict = {"backend": backend}

        # Add vector search config
        vector_search_config = {"provider": vector_search_provider}
        if vector_search_provider == VectorSearchType.VERTEX:
            vertex_config = {}
            if os.environ.get("VECTOR_SEARCH_INDEX_ENDPOINT_ID"):
                vertex_config["index_endpoint_id"] = os.environ[
                    "VECTOR_SEARCH_INDEX_ENDPOINT_ID"
                ]
            if os.environ.get("VECTOR_SEARCH_INDEX_ID"):
                vertex_config["index_id"] = os.environ["VECTOR_SEARCH_INDEX_ID"]
            if vertex_config:
                vector_search_config["vertex"] = vertex_config

        config_dict["vector_search"] = vector_search_config

        # Create the config
        return cls(**config_dict)
