"""
Configuration models for MCP server.

This module defines Pydantic models for configuration settings used by the MCP server
and its components.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator


class StorageConfig(BaseModel):
    """Configuration for storage backends."""
    
    type: str = Field(default="in_memory", description="Storage backend type")
    connection_string: Optional[str] = Field(default=None, description="Connection string for database-backed storage")
    max_entries: int = Field(default=10000, description="Maximum number of entries to store")
    ttl_seconds: int = Field(default=86400, description="Default TTL for entries (24 hours)")
    
    class Config:
        extra = "allow"


class CopilotConfig(BaseModel):
    """Configuration for GitHub Copilot adapter."""
    
    enabled: bool = Field(default=True, description="Whether to enable the Copilot adapter")
    api_key: Optional[str] = Field(default=None, description="GitHub Copilot API key")
    token_limit: int = Field(default=5000, description="Token limit for context window")
    vscode_extension_path: Optional[str] = Field(default=None, description="Path to VS Code Copilot extension")
    use_openai_fallback: bool = Field(default=True, description="Whether to use OpenAI as a fallback")
    openai_model: str = Field(default="gpt-3.5-turbo", description="OpenAI model to use as fallback")
    
    class Config:
        extra = "allow"


class GeminiConfig(BaseModel):
    """Configuration for Google Gemini adapter."""
    
    enabled: bool = Field(default=True, description="Whether to enable the Gemini adapter")
    api_key: Optional[str] = Field(default=None, description="Google Gemini API key")
    model: str = Field(default="gemini-pro", description="Gemini model to use")
    embeddings_model: str = Field(default="embedding-001", description="Embeddings model to use")
    token_limit: int = Field(default=200000, description="Token limit for context window")
    
    class Config:
        extra = "allow"


class MCPConfig(BaseModel):
    """Main configuration for MCP server."""
    
    storage: StorageConfig = Field(default_factory=StorageConfig, description="Storage configuration")
    copilot: CopilotConfig = Field(default_factory=CopilotConfig, description="GitHub Copilot configuration")
    gemini: GeminiConfig = Field(default_factory=GeminiConfig, description="Google Gemini configuration")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    port: int = Field(default=8080, description="HTTP server port")
    host: str = Field(default="0.0.0.0", description="HTTP server host")
    
    class Config:
        extra = "allow"
