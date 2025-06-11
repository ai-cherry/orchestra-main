#!/usr/bin/env python3
"""
Orchestra AI Environment Configuration
Centralized configuration management using Pydantic Settings
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class OrchestryAISettings(BaseSettings):
    """Centralized settings for Orchestra AI"""
    
    # Core API Configuration
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    api_url: str = Field(default="http://localhost:8000", env="API_URL")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # Lambda Labs Configuration
    lambda_api_key: Optional[str] = Field(default=None, env="LAMBDA_API_KEY")
    lambda_credentials_path: Optional[str] = Field(default=None, env="LAMBDA_CREDENTIALS_PATH")

    # GitHub and CI/CD
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    k_service: Optional[str] = Field(default=None, env="K_SERVICE")
    cloud_workstations_agent: Optional[str] = Field(default=None, env="CLOUD_WORKSTATIONS_AGENT")
    ci: Optional[str] = Field(default=None, env="CI")
    github_actions: Optional[str] = Field(default=None, env="GITHUB_ACTIONS")

    # Weaviate Configuration (Primary Vector Database)
    weaviate_endpoint: Optional[str] = Field(default=None, env="WEAVIATE_ENDPOINT")
    weaviate_api_key: Optional[str] = Field(default=None, env="WEAVIATE_API_KEY")
    weaviate_grpc_endpoint: Optional[str] = Field(default=None, env="WEAVIATE_GRPC_ENDPOINT")
    weaviate_batch_size: int = Field(default=100, env="WEAVIATE_BATCH_SIZE")
    weaviate_enable_acorn: bool = Field(default=True, env="WEAVIATE_ENABLE_ACORN")
    weaviate_enable_agents: bool = Field(default=True, env="WEAVIATE_ENABLE_AGENTS")

    # PostgreSQL Configuration (ACID Operations)
    postgres_dsn: Optional[str] = Field(default=None, env="POSTGRES_DSN")
    postgres_host: Optional[str] = Field(default=None, env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_user: Optional[str] = Field(default=None, env="POSTGRES_USER")
    postgres_password: Optional[str] = Field(default=None, env="POSTGRES_PASSWORD")
    postgres_db: Optional[str] = Field(default=None, env="POSTGRES_DB")

    # Cache Configuration
    enable_micro_cache: bool = Field(default=False, env="ENABLE_MICRO_CACHE")
    use_redis: bool = Field(default=False, env="USE_REDIS")

    # Vector Database Alternatives
    pinecone_environment: Optional[str] = Field(default=None, env="PINECONE_ENVIRONMENT")
    qdrant_url: Optional[str] = Field(default=None, env="QDRANT_URL")

    # MCP Configuration
    mcp_api_key: Optional[str] = Field(default=None, env="MCP_API_KEY")
    mcp_server_endpoint: Optional[str] = Field(default=None, env="MCP_SERVER_ENDPOINT")

    # Monitoring and Observability
    langfuse_host: Optional[str] = Field(default=None, env="LANGFUSE_HOST")
    langfuse_public_key: Optional[str] = Field(default=None, env="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: Optional[str] = Field(default=None, env="LANGFUSE_SECRET_KEY")
    enable_performance_monitoring: bool = Field(default=True, env="ENABLE_PERFORMANCE_MONITORING")

    # Domain Configuration
    default_domain: str = Field(default="Personal", env="DEFAULT_DOMAIN")
    available_domains: str = Field(default="Personal,PayReady,ParagonRX", env="AVAILABLE_DOMAINS")

    # Recraft API Key for Recraft integrations
    recraft_api_key: Optional[str] = Field(default=None, env="RECRAFT_API_KEY")

    # Deployment Environment
    environment: str = Field(default="dev", env="ENVIRONMENT")
    paperspace_env: Optional[str] = Field(default=None, env="PAPERSPACE_ENV")

    # Notion Integration
    notion_api_token: Optional[str] = Field(default=None, env="NOTION_API_TOKEN")
    notion_workspace_id: Optional[str] = Field(default=None, env="NOTION_WORKSPACE_ID")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields not defined in the model

# Singleton instance for use throughout the project
settings = OrchestryAISettings()

# Usage example (in other modules):
# from legacy.core.env_config import settings
# weaviate_endpoint = settings.weaviate_endpoint
