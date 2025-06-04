from fastapi import APIRouter, Depends, HTTPException, status, Body, BackgroundTasks
from uuid import UUID, uuid4
from typing import List, Optional, Any, Dict, Literal
from datetime import datetime
from pydantic import BaseModel, Field
import asyncio
import logging

from core.models.mcp_instance_models import (
    UserDefinedMCPServerInstanceConfig, 
    MCPServerInstanceStatus, 
    MCPServerResourceConfig, 
    AIProvider, 
    ContextSourceConfig
)
from core.services.mcp_config_manager import OptimizedMCPConfigManager
from core.utils.performance import performance_monitor, AsyncBatchProcessor

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/mcp",
    tags=["MCP Server Management"]
)

# Initialize the optimized configuration manager
config_manager = OptimizedMCPConfigManager(config_filepath="config/mcp_servers.yaml")

# Initialize batch processor for bulk operations
batch_processor = AsyncBatchProcessor(batch_size=5, max_wait_time=2.0)


# Enhanced request models with validation
class MCPServerCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="User-friendly name for the MCP server instance")
    description: Optional[str] = Field(default=None, max_length=500)
    target_ai_coders: List[Literal["RooCoder", "CursorAI", "Claude", "OpenAI_GPT4", "OpenAI_GPT3_5", "Gemini", "Copilot", "Generic"]] = Field(
        ...,
        description="Primary AI Coder(s) this server instance is intended to support or emulate."
    )
    enabled_internal_tools: List[Literal["copilot", "gemini"]] = Field(
        default_factory=list,
        description="Internal MCP tools to enable"
    )
    copilot_config_override: Optional[Dict[str, Any]] = Field(default=None, description="Copilot configuration overrides")
    gemini_config_override: Optional[Dict[str, Any]] = Field(default=None, description="Gemini configuration overrides")
    base_docker_image: str = Field(default="mcp_server:latest", description="Base Docker image for this MCP instance")
    resources: MCPServerResourceConfig = Field(default_factory=MCPServerResourceConfig)
    custom_environment_variables: Dict[str, str] = Field(default_factory=dict)
    ai_providers: List[AIProvider] = Field(default_factory=list)
    context_sources: List[ContextSourceConfig] = Field(default_factory=list)
    desired_status: Literal["running", "stopped"] = Field(default="running")

    class Config:
        use_enum_values = True


class MCPServerUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=3, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    target_ai_coders: Optional[List[Literal["RooCoder", "CursorAI", "Claude", "OpenAI_GPT4", "OpenAI_GPT3_5", "Gemini", "Copilot", "Generic"]]] = None
    enabled_internal_tools: Optional[List[Literal["copilot", "gemini"]]] = None
    copilot_config_override: Optional[Dict[str, Any]] = None
    gemini_config_override: Optional[Dict[str, Any]] = None
    base_docker_image: Optional[str] = None
    resources: Optional[MCPServerResourceConfig] = None
    custom_environment_variables: Optional[Dict[str, str]] = None
    ai_providers: Optional[List[AIProvider]] = None
    context_sources: Optional[List[ContextSourceConfig]] = None
    desired_status: Optional[Literal["running", "stopped"]] = None

    class Config:
        use_enum_values = True


class MCPServerBulkCreateRequest(BaseModel):
    servers: List[MCPServerCreateRequest] = Field(..., min_items=1, max_items=50, description="List of servers to create (max 50)")


class MCPServerBulkUpdateRequest(BaseModel):
    updates: List[Dict[str, Any]] = Field(..., min_items=1, max_items=50, description="List of server updates with server_id and update_data")


class MCPServerValidationResponse(BaseModel):
    total_configs: int
    valid_configs: int
    invalid_configs: int
    errors: List[Dict[str, Any]]


class MCPPerformanceStats(BaseModel):
    cache_stats: Dict[str, Any]
    operation_stats: Dict[str, Any]
    system_info: Dict[str, Any]


# Enhanced error handling
class MCPServerError(HTTPException):
    def __init__(self, status_code: int, detail: str, error_type: str = "general"):
        super().__init__(status_code=status_code, detail=detail)
        self.error_type = error_type


async def validate_server_config(config: MCPServerCreateRequest) -> None:
    """Validate server configuration with enhanced checks"""
    # Check for duplicate names
    existing_configs = await config_manager.get_all_configs()
    existing_names = {c.name.lower() for c in existing_configs}
    
    if config.name.lower() in existing_names:
        raise MCPServerError(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Server name '{config.name}' already exists",
            error_type="duplicate_name"
        )
    
    # Validate resource constraints
    if config.resources:
        try:
            cpu_val = float(config.resources.cpu)
            if cpu_val <= 0 or cpu_val > 16:
                raise ValueError("CPU must be between 0 and 16")
        except ValueError as e:
            raise MCPServerError(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid CPU specification: {e}",
                error_type="invalid_resources"
            )


# Optimized endpoints with performance monitoring
@router.post("/servers", response_model=UserDefinedMCPServerInstanceConfig, status_code=status.HTTP_201_CREATED)
@performance_monitor("create_mcp_server")
async def create_mcp_server(
    server_data: MCPServerCreateRequest = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Create a new MCP Server instance configuration with validation"""
    try:
        # Validate configuration
        await validate_server_config(server_data)
        
        # Create configuration
        new_config = UserDefinedMCPServerInstanceConfig(**server_data.model_dump())
        saved_config = await config_manager.save_config(new_config)
        
        # Background task for cache warming
        background_tasks.add_task(warm_related_caches, saved_config.id)
        
        logger.info(f"Created MCP server: {saved_config.name} (ID: {saved_config.id})")
        return saved_config
        
    except MCPServerError:
        raise
    except Exception as e:
        logger.error(f"Error creating MCP server: {e}", exc_info=True)
        raise MCPServerError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create server: {str(e)}",
            error_type="creation_failed"
        )


@router.get("/servers", response_model=List[UserDefinedMCPServerInstanceConfig])
@performance_monitor("get_all_mcp_servers")
async def get_all_mcp_servers(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    status_filter: Optional[str] = None
):
    """Retrieve all MCP Server instance configurations with optional filtering"""
    try:
        configs = await config_manager.get_all_configs()
        
        # Apply status filter if provided
        if status_filter:
            configs = [c for c in configs if c.desired_status == status_filter]
        
        # Apply pagination
        if offset is not None:
            configs = configs[offset:]
        if limit is not None:
            configs = configs[:limit]
        
        return configs
        
    except Exception as e:
        logger.error(f"Error retrieving MCP servers: {e}", exc_info=True)
        raise MCPServerError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve servers: {str(e)}",
            error_type="retrieval_failed"
        )


@router.get("/servers/{server_id}", response_model=UserDefinedMCPServerInstanceConfig)
@performance_monitor("get_mcp_server")
async def get_mcp_server(server_id: UUID):
    """Retrieve a specific MCP Server instance configuration by ID"""
    try:
        config = await config_manager.get_config_by_id(server_id)
        if not config:
            raise MCPServerError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MCP Server configuration not found",
                error_type="not_found"
            )
        return config
        
    except MCPServerError:
        raise
    except Exception as e:
        logger.error(f"Error retrieving MCP server {server_id}: {e}", exc_info=True)
        raise MCPServerError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve server: {str(e)}",
            error_type="retrieval_failed"
        )


@router.put("/servers/{server_id}", response_model=UserDefinedMCPServerInstanceConfig)
@performance_monitor("update_mcp_server")
async def update_mcp_server(
    server_id: UUID,
    update_data: MCPServerUpdateRequest = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Update an existing MCP Server instance configuration"""
    try:
        existing_config = await config_manager.get_config_by_id(server_id)
        if not existing_config:
            raise MCPServerError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MCP Server configuration not found",
                error_type="not_found"
            )

        # Validate name uniqueness if name is being updated
        if update_data.name and update_data.name != existing_config.name:
            all_configs = await config_manager.get_all_configs()
            existing_names = {c.name.lower() for c in all_configs if c.id != server_id}
            if update_data.name.lower() in existing_names:
                raise MCPServerError(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Server name '{update_data.name}' already exists",
                    error_type="duplicate_name"
                )

        update_data_dict = update_data.model_dump(exclude_unset=True)
        updated_config = existing_config.model_copy(update=update_data_dict)
        saved_config = await config_manager.save_config(updated_config)
        
        # Background cache invalidation
        background_tasks.add_task(invalidate_related_caches, server_id)
        
        logger.info(f"Updated MCP server: {saved_config.name} (ID: {saved_config.id})")
        return saved_config
        
    except MCPServerError:
        raise
    except Exception as e:
        logger.error(f"Error updating MCP server {server_id}: {e}", exc_info=True)
        raise MCPServerError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update server: {str(e)}",
            error_type="update_failed"
        )


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
@performance_monitor("delete_mcp_server")
async def delete_mcp_server(
    server_id: UUID,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Delete an MCP Server instance configuration"""
    try:
        deleted = await config_manager.delete_config(server_id)
        if not deleted:
            raise MCPServerError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MCP Server configuration not found",
                error_type="not_found"
            )
        
        # Background cache cleanup
        background_tasks.add_task(cleanup_server_caches, server_id)
        
        logger.info(f"Deleted MCP server with ID: {server_id}")
        return None
        
    except MCPServerError:
        raise
    except Exception as e:
        logger.error(f"Error deleting MCP server {server_id}: {e}", exc_info=True)
        raise MCPServerError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete server: {str(e)}",
            error_type="deletion_failed"
        )


# New bulk operations endpoints
@router.post("/servers/bulk", response_model=List[UserDefinedMCPServerInstanceConfig])
@performance_monitor("bulk_create_mcp_servers")
async def bulk_create_mcp_servers(
    bulk_request: MCPServerBulkCreateRequest = Body(...)
):
    """Create multiple MCP Server instances in a single operation"""
    try:
        # Validate all configurations first
        for server_data in bulk_request.servers:
            await validate_server_config(server_data)
        
        # Convert to full configs
        configs = [
            UserDefinedMCPServerInstanceConfig(**server_data.model_dump())
            for server_data in bulk_request.servers
        ]
        
        # Bulk save
        saved_configs = await config_manager.bulk_save_configs(configs)
        
        logger.info(f"Bulk created {len(saved_configs)} MCP servers")
        return saved_configs
        
    except MCPServerError:
        raise
    except Exception as e:
        logger.error(f"Error in bulk create: {e}", exc_info=True)
        raise MCPServerError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk creation failed: {str(e)}",
            error_type="bulk_creation_failed"
        )


@router.get("/servers/{server_id}/status", response_model=MCPServerInstanceStatus)
@performance_monitor("get_mcp_server_status")
async def get_mcp_server_status(server_id: UUID):
    """Get the current status of a specific MCP Server instance"""
    try:
        config = await config_manager.get_config_by_id(server_id)
        if not config:
            raise MCPServerError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MCP Server configuration not found",
                error_type="not_found"
            )

        # Enhanced status with basic health simulation
        status_info = MCPServerInstanceStatus(
            instance_id=server_id,
            actual_status="RUNNING" if config.desired_status == "running" else "STOPPED",
            message=f"Server '{config.name}' is {config.desired_status}",
            last_status_check_at=datetime.utcnow()
        )
        
        return status_info
        
    except MCPServerError:
        raise
    except Exception as e:
        logger.error(f"Error getting server status {server_id}: {e}", exc_info=True)
        raise MCPServerError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get server status: {str(e)}",
            error_type="status_failed"
        )


# Performance and monitoring endpoints
@router.get("/admin/validate", response_model=MCPServerValidationResponse)
@performance_monitor("validate_all_configs")
async def validate_all_configurations():
    """Validate all MCP server configurations"""
    try:
        validation_report = await config_manager.validate_all_configs()
        return MCPServerValidationResponse(**validation_report)
        
    except Exception as e:
        logger.error(f"Error validating configurations: {e}", exc_info=True)
        raise MCPServerError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}",
            error_type="validation_failed"
        )


@router.get("/admin/performance", response_model=MCPPerformanceStats)
async def get_performance_stats():
    """Get performance statistics for the MCP system"""
    try:
        cache_stats = config_manager.get_cache_stats()
        
        # Get operation stats from performance monitor
        operation_stats = {}
        if hasattr(config_manager, 'get_all_stats'):
            operation_stats = config_manager.get_all_stats()
        
        system_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "config_file_path": config_manager.config_filepath,
            "cache_enabled": True
        }
        
        return MCPPerformanceStats(
            cache_stats=cache_stats,
            operation_stats=operation_stats,
            system_info=system_info
        )
        
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}", exc_info=True)
        raise MCPServerError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance stats: {str(e)}",
            error_type="stats_failed"
        )


@router.post("/admin/cache/clear")
async def clear_cache():
    """Clear all cached data"""
    try:
        config_manager.clear_cache()
        return {"message": "Cache cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        raise MCPServerError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}",
            error_type="cache_clear_failed"
        )


# Background task functions
async def warm_related_caches(server_id: UUID):
    """Warm caches for related operations"""
    try:
        # Pre-load the server config into cache
        await config_manager.get_config_by_id(server_id)
        logger.debug(f"Warmed cache for server {server_id}")
    except Exception as e:
        logger.error(f"Error warming cache for {server_id}: {e}")


async def invalidate_related_caches(server_id: UUID):
    """Invalidate caches related to a server"""
    try:
        # The optimized config manager handles this automatically
        logger.debug(f"Cache invalidation triggered for server {server_id}")
    except Exception as e:
        logger.error(f"Error invalidating cache for {server_id}: {e}")


async def cleanup_server_caches(server_id: UUID):
    """Clean up caches after server deletion"""
    try:
        # Additional cleanup if needed
        logger.debug(f"Cache cleanup completed for server {server_id}")
    except Exception as e:
        logger.error(f"Error cleaning up cache for {server_id}: {e}")


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for MCP admin system"""
    try:
        # Test basic operations
        configs = await config_manager.get_all_configs()
        cache_stats = config_manager.get_cache_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "total_servers": len(configs),
            "cache_entries": cache_stats.get("total_entries", 0)
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise MCPServerError(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}",
            error_type="health_check_failed"
        )

