from typing import List, Dict, Optional, Any, Literal # Added Any for Dict values
from pydantic import BaseModel, Field, HttpUrl
from uuid import UUID, uuid4
from datetime import datetime

class MCPServerResourceConfig(BaseModel):
    cpu: str = Field(default="1", description="CPU allocation (e.g., '1', '0.5')")
    memory: str = Field(default="2Gi", description="Memory allocation (e.g., '2Gi', '512Mi')")
    gpu_type: Optional[str] = Field(default=None, description="Type of GPU requested, if any (e.g., 'nvidia-a100')")

class AIProvider(BaseModel):
    name: Literal["openai", "claude", "gemini", "copilot", "custom"] = Field(..., description="Name of the AI provider")
    api_key_secret_name: Optional[str] = Field(default=None, description="Name of the secret (e.g., environment variable name or vault path) holding the API key for this provider")
    model: Optional[str] = Field(default=None, description="Default model to use for this provider")
    # Potentially add base_url for custom OpenAI-compatible APIs if needed later

class ContextSourceConfig(BaseModel):
    type: Literal["git_repo", "weaviate_collection", "file_path", "url_list"] = Field(
        ...,
        description="Type of context source"
    )
    uri: Optional[str] = Field(default=None, description="URI for the context source (e.g., git repo URL, Weaviate collection name, base file path)")
    paths: List[str] = Field(default_factory=list, description="Specific paths or URLs within the URI (e.g., subdirectories, specific file names, list of web pages)")
    branch: Optional[str] = Field(default=None, description="Branch to use for git_repo context source")
    # Add other source-specific settings as needed

class UserDefinedMCPServerInstanceConfig(BaseModel):
    id: UUID = Field(default_factory=uuid4, description="Unique instance ID")
    name: str = Field(..., min_length=3, max_length=100, description="User-friendly name for the MCP server instance")
    description: Optional[str] = Field(default=None, max_length=500)

    target_ai_coders: List[Literal["Coder", "CursorAI", "Claude", "OpenAI_GPT4", "OpenAI_GPT3_5", "Gemini", "Copilot", "Generic"]] = Field(
        ...,
        description="Primary AI Coder(s) this server instance is intended to support or emulate."
    )

    enabled_internal_tools: List[Literal["copilot", "gemini"]] = Field(
        default_factory=list,
        description="Internal MCP tools to enable (
            maps to sections in the internal MCPConfig like 'copilot',
            'gemini'
        )"
    )

    copilot_config_override: Optional[Dict[str, Any]] = Field(default=None, description="Specific overrides for the 'copilot' section of the internal MCPConfig")
    gemini_config_override: Optional[Dict[str, Any]] = Field(default=None, description="Specific overrides for the 'gemini' section of the internal MCPConfig")
    # TODO: Add fields for other potential internal tools like 'claude_internal_config_override', 'openai_internal_config_override' as MCPConfig model evolves

    base_docker_image: str = Field(default="mcp_server:latest", description="Base Docker image for this MCP instance (e.g., my_registry/mcp_server:stable)")

    resources: MCPServerResourceConfig = Field(default_factory=MCPServerResourceConfig)

    custom_environment_variables: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom environment variables for the instance (excluding sensitive keys managed by ai_providers.api_key_secret_name)"
    )

    ai_providers: List[AIProvider] = Field(
        default_factory=list,
        description="Configuration for external AI providers whose API keys need to be securely injected into the environment"
    )

    context_sources: List[ContextSourceConfig] = Field(
        default_factory=list,
        description="Sources for contextual information for this MCP instance"
    )

    generated_mcp_internal_config_yaml: Optional[str] = Field(
        default=None,
        description="The actual MCPConfig YAML string generated for and used by this instance's container. Stored for audit/reference."
    )

    desired_status: Literal["running", "stopped"] = Field(default="running", description="User's desired state for the server")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True # For Literal types
        # For Pydantic v2, this would be: json_encoders = { UUID: str, datetime: lambda dt: dt.isoformat() }
        # For Pydantic v1, this is okay, or often default behavior is fine.
        # If using Pydantic v2 and FastAPI, default FastAPI JSON encoding handles UUID and datetime well.

class MCPServerInstanceStatus(BaseModel):
    instance_id: UUID
    actual_status: Literal["UNKNOWN", "PENDING", "PROVISIONING", "RUNNING", "STOPPED", "STOPPING", "ERROR", "DELETING"] = Field(default="UNKNOWN", description="The last observed actual status of the server")
    health_check_url: Optional[HttpUrl] = Field(default=None, description="URL for health checks if applicable") # Changed from str to HttpUrl
    last_health_status: Optional[str] = Field(default=None, description="Result of the last health check (e.g., 'OK', 'UNHEALTHY', error message)")
    last_status_check_at: Optional[datetime] = Field(default=None, description="Timestamp of the last status check")
    message: Optional[str] = Field(default=None, description="Additional status message, e.g., error details or provisioning logs")
    # TODO: Add other relevant status fields: cpu_usage, memory_usage, public_endpoints etc.

    class Config:
        use_enum_values = True

# Make sure HttpUrl is correctly processed by Pydantic. If it's a string, it should be HttpUrl type.
# Corrected health_check_url to use HttpUrl directly in the type hint.
# Added 'Any' to typing imports for Dict values.
