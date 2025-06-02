#!/usr/bin/env python3
"""
Orchestra Memory MCP Server.

This server provides a unified MCP interface to the orchestra-main's
UnifiedMemoryService, allowing AI models (e.g., via Cursor IDE)
to interact with the multi-layered memory system (caching, document store, vector store).
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Literal

import uvicorn
import weaviate  # For Weaviate client types
import redis.asyncio as redis_async  # For Dragonfly
from motor.motor_asyncio import AsyncIOMotorClient  # For MongoDB

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field

# Assuming core modules are accessible in PYTHONPATH
from core.services.memory.unified_memory import (
    UnifiedMemoryService,
    get_memory_service,
    MemoryItem as CoreMemoryItem,
    SearchResult as CoreSearchResult,
)
from core.services.memory.base import MemoryLayer
from core.infrastructure.connectivity.base import ServiceRegistry
from core.infrastructure.config.settings import get_settings, AppSettings

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Orchestra Memory MCP Server",
    description="MCP server for interacting with the Unified Memory Service.",
    version="1.0.0",
)

# Global instances
unified_memory_service: Optional[UnifiedMemoryService] = None
mcp_service_registry: Optional["MCPServiceRegistry"] = None


class MCPServiceRegistry(ServiceRegistry):
    """
    A simplified ServiceRegistry for the MCP server context.
    Initializes and provides database client connections.
    """

    def __init__(self, settings: AppSettings):
        self._settings = settings
        self.dragonfly_client: Optional[redis_async.Redis] = None
        self.mongodb_client: Optional[AsyncIOMotorClient] = None
        self.weaviate_client_instance: Optional[weaviate.WeaviateClient] = None
        self._db_name_mongo = "orchestra_default_mongo_db"  # Default, can be from settings

    async def initialize_services(self):
        logger.info("MCPServiceRegistry: Initializing services...")
        try:
            # Dragonfly (Redis-compatible)
            if self._settings.dragonfly.enabled:
                df_url = f"redis://{self._settings.dragonfly.host}:{self._settings.dragonfly.port}/{self._settings.dragonfly.db_index}"
                if self._settings.dragonfly.password:
                    df_url = f"redis://:{self._settings.dragonfly.password}@{self._settings.dragonfly.host}:{self._settings.dragonfly.port}/{self._settings.dragonfly.db_index}"

                self.dragonfly_client = redis_async.from_url(
                    df_url, max_connections=self._settings.dragonfly.max_connections or 50
                )
                await self.dragonfly_client.ping()
                logger.info(
                    f"Connected to DragonflyDB at {self._settings.dragonfly.host}:{self._settings.dragonfly.port}"
                )

            # MongoDB
            if self._settings.mongodb.enabled:
                self.mongodb_client = AsyncIOMotorClient(self._settings.mongodb.uri)
                await self.mongodb_client.admin.command("ping")  # Verify connection
                self._db_name_mongo = self.mongodb_client.get_default_database().name  # Get actual DB name
                logger.info(
                    f"Connected to MongoDB at {self._settings.mongodb.uri}, using database '{self._db_name_mongo}'"
                )

            # Weaviate
            if self._settings.weaviate.enabled:
                auth_creds = None
                if self._settings.weaviate.api_key:
                    auth_creds = weaviate.auth.AuthApiKey(api_key=self._settings.weaviate.api_key)

                headers = {}
                if self._settings.weaviate.additional_headers:
                    try:
                        headers = json.loads(self._settings.weaviate.additional_headers)
                    except json.JSONDecodeError:
                        logger.error("Failed to parse Weaviate additional headers JSON.")

                connection_params = weaviate.config.ConnectionParams.from_params(
                    http_host=self._settings.weaviate.host,
                    http_port=self._settings.weaviate.port,
                    http_secure=self._settings.weaviate.secured,
                    grpc_host=self._settings.weaviate.grpc_host or self._settings.weaviate.host,
                    grpc_port=self._settings.weaviate.grpc_port,
                    grpc_secure=self._settings.weaviate.secured,
                )
                self.weaviate_client_instance = weaviate.WeaviateClient(
                    connection_params=connection_params,
                    auth_client_secret=auth_creds,
                    additional_headers=headers,
                    startup_period=self._settings.weaviate.startup_period or 30,
                )
                self.weaviate_client_instance.connect()
                if not self.weaviate_client_instance.is_ready():
                    raise ConnectionError("Weaviate client connected but instance is not ready.")
                logger.info(f"Connected to Weaviate at {self._settings.weaviate.host}:{self._settings.weaviate.port}")

        except Exception as e:
            logger.error(f"MCPServiceRegistry: Error during service initialization: {e}", exc_info=True)
            # Ensure clients are None if they failed to initialize
            if not (self.dragonfly_client and await self.dragonfly_client.ping()):
                self.dragonfly_client = None
            if not self.mongodb_client:
                self.mongodb_client = None  # Ping is implicit
            if not (self.weaviate_client_instance and self.weaviate_client_instance.is_ready()):
                self.weaviate_client_instance = None
            raise  # Re-raise to signal startup failure

    def get_service(self, service_name: str) -> Any:
        if service_name == "dragonfly" and self._settings.dragonfly.enabled:
            return self.dragonfly_client
        elif service_name == "mongodb" and self._settings.mongodb.enabled:
            # UnifiedMemoryService's MidTermStore expects a MongoDB database object, not the client
            if self.mongodb_client:
                return self.mongodb_client[self._settings.mongodb.database_name or self._db_name_mongo]
            return None
        elif (
            service_name == "weaviate_client" and self._settings.weaviate.enabled
        ):  # Match service name used in UnifiedMemoryService
            return self.weaviate_client_instance
        logger.warning(f"MCPServiceRegistry: Service '{service_name}' not found or not enabled.")
        return None

    async def shutdown_services(self):
        logger.info("MCPServiceRegistry: Shutting down services...")
        if self.dragonfly_client:
            await self.dragonfly_client.close()
            logger.info("DragonflyDB connection closed.")
        if self.mongodb_client:
            self.mongodb_client.close()  # Motor client close is synchronous
            logger.info("MongoDB connection closed.")
        if self.weaviate_client_instance and self.weaviate_client_instance.is_connected():
            self.weaviate_client_instance.close()
            logger.info("Weaviate client connection closed.")


@app.on_event("startup")
async def startup_event():
    global unified_memory_service, mcp_service_registry
    logger.info("Orchestra Memory MCP Server starting up...")
    try:
        settings = get_settings()
        mcp_service_registry = MCPServiceRegistry(settings)
        await mcp_service_registry.initialize_services()

        unified_memory_service = get_memory_service(mcp_service_registry)
        await unified_memory_service.initialize()  # Initialize stores within UnifiedMemoryService
        logger.info("UnifiedMemoryService initialized successfully.")
    except Exception as e:
        logger.critical(f"Critical error during MCP server startup: {e}", exc_info=True)
        # Optionally, sys.exit(1) if a clean startup is mandatory


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Orchestra Memory MCP Server shutting down...")
    if mcp_service_registry:
        await mcp_service_registry.shutdown_services()


async def get_ums() -> UnifiedMemoryService:
    if unified_memory_service is None:
        logger.error("UnifiedMemoryService not initialized.")
        raise HTTPException(status_code=503, detail="Memory service unavailable.")
    if not unified_memory_service._initialized:  # Accessing protected member, consider adding a public property
        logger.warning("UnifiedMemoryService accessed before full initialization.")
        await unified_memory_service.initialize()  # Attempt re-init
    return unified_memory_service


# --- Pydantic Models ---
class MemoryItemResponse(BaseModel):
    id: str
    content: Any
    metadata: Dict[str, Any]
    timestamp: str  # ISO format
    layer: str  # Enum value as string
    ttl: Optional[int] = None


class SearchResultResponse(BaseModel):
    item: MemoryItemResponse
    score: float


class RememberRequest(BaseModel):
    content: Any
    metadata: Optional[Dict[str, Any]] = None
    importance: Optional[float] = None
    ttl_seconds: Optional[int] = None


class RememberResponse(BaseModel):
    status: Literal["success", "failed"]
    item_id: Optional[str] = None
    error: Optional[str] = None


class RecallRequest(BaseModel):
    item_id: str


class SearchMemoriesRequest(BaseModel):
    query: str
    search_type: Literal["semantic", "keyword", "hybrid"] = "hybrid"
    limit: int = 10
    layers: Optional[List[Literal["SHORT_TERM", "MID_TERM", "LONG_TERM"]]] = None
    filters: Optional[Dict[str, Any]] = None


class SearchMemoriesResponse(BaseModel):
    results: List[SearchResultResponse]
    count: int


class ForgetRequest(BaseModel):
    item_id: str


class ForgetResponse(BaseModel):
    status: Literal["success", "failed", "not_found"]
    error: Optional[str] = None


class GetMemoryStatsResponse(BaseModel):
    stats: Dict[str, Any]


class MCPToolProperty(BaseModel):
    type: str
    description: Optional[str] = None
    items: Optional[Dict[str, Any]] = None


class MCPToolParameters(BaseModel):
    type: str = "object"
    properties: Dict[str, MCPToolProperty]
    required: Optional[List[str]] = None


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    parameters: MCPToolParameters


# --- MCP Tool Definitions Endpoint ---
@app.get("/mcp/orchestra_memory/tools", response_model=List[MCPToolDefinition])
async def get_mcp_tools_list():
    return [
        MCPToolDefinition(
            name="remember",
            description="Stores a piece of information in the orchestrated memory system. The system will decide the appropriate layer based on policy.",
            parameters=MCPToolParameters(
                properties={
                    "content": MCPToolProperty(
                        type="object", description="The content to store (can be any JSON-serializable type)."
                    ),
                    "metadata": MCPToolProperty(type="object", description="Optional dictionary of metadata."),
                    "importance": MCPToolProperty(
                        type="number", description="Optional importance score (e.g., 0.0 to 1.0)."
                    ),
                    "ttl_seconds": MCPToolProperty(
                        type="integer", description="Optional time-to-live in seconds for short-term memory."
                    ),
                },
                required=["content"],
            ),
        ),
        MCPToolDefinition(
            name="recall",
            description="Retrieves a specific memory item by its ID from any layer.",
            parameters=MCPToolParameters(
                properties={
                    "item_id": MCPToolProperty(type="string", description="The ID of the memory item to retrieve.")
                },
                required=["item_id"],
            ),
        ),
        MCPToolDefinition(
            name="search_memories",
            description="Searches across memory layers using a query. Can specify search type.",
            parameters=MCPToolParameters(
                properties={
                    "query": MCPToolProperty(type="string", description="The search query."),
                    "search_type": MCPToolProperty(
                        type="string",
                        description="Type of search: 'semantic', 'keyword', or 'hybrid' (default: 'hybrid').",
                    ),
                    "limit": MCPToolProperty(type="integer", description="Maximum number of results (default: 10)."),
                    "layers": MCPToolProperty(
                        type="array",
                        items={"type": "string"},
                        description="Optional list of layers to search: SHORT_TERM, MID_TERM, LONG_TERM.",
                    ),
                    "filters": MCPToolProperty(type="object", description="Optional dictionary of filters to apply."),
                },
                required=["query"],
            ),
        ),
        MCPToolDefinition(
            name="forget",
            description="Removes/evicts a memory item from all layers by its ID.",
            parameters=MCPToolParameters(
                properties={
                    "item_id": MCPToolProperty(type="string", description="The ID of the memory item to forget.")
                },
                required=["item_id"],
            ),
        ),
        MCPToolDefinition(
            name="get_memory_stats",
            description="Retrieves statistics about the memory system, including layer health and item counts.",
            parameters=MCPToolParameters(properties={}),
        ),
    ]


# --- Tool Endpoints ---
@app.post("/mcp/orchestra_memory/remember", response_model=RememberResponse)
async def remember_endpoint(request: RememberRequest, ums: UnifiedMemoryService = Depends(get_ums)):
    try:
        metadata = request.metadata or {}
        if request.importance is not None:
            metadata["importance_score"] = request.importance  # Store importance in metadata

        item_id = await ums.store(
            content=request.content,
            metadata=metadata,
            ttl=request.ttl_seconds,
            # Layer is determined by policy in UMS
        )
        return RememberResponse(status="success", item_id=item_id)
    except Exception as e:
        logger.error(f"MCP Remember error: {e}", exc_info=True)
        return RememberResponse(status="failed", error=str(e))


@app.post("/mcp/orchestra_memory/recall", response_model=Optional[MemoryItemResponse])
async def recall_endpoint(request: RecallRequest, ums: UnifiedMemoryService = Depends(get_ums)):
    try:
        item = await ums.retrieve(request.item_id)
        if item:
            return MemoryItemResponse(
                id=item.id,
                content=item.content,
                metadata=item.metadata,
                timestamp=item.timestamp.isoformat(),
                layer=item.layer.value,
                ttl=item.ttl,
            )
        return None
    except Exception as e:
        logger.error(f"MCP Recall error for item {request.item_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/orchestra_memory/search_memories", response_model=SearchMemoriesResponse)
async def search_memories_endpoint(request: SearchMemoriesRequest, ums: UnifiedMemoryService = Depends(get_ums)):
    try:
        target_layers: Optional[List[MemoryLayer]] = None
        if request.layers:
            target_layers = []
            for layer_str in request.layers:
                try:
                    target_layers.append(MemoryLayer[layer_str.upper()])
                except KeyError:
                    raise HTTPException(status_code=400, detail=f"Invalid memory layer specified: {layer_str}")

        # Note: The UnifiedMemoryService.search might need enhancement to fully distinguish
        # semantic/keyword/hybrid if it currently just queries all specified layers.
        # For now, we pass the query and let UMS handle it.
        # If specific stores need to be targeted based on search_type, that logic would go here
        # or be pushed down into UMS.search.

        # Example of how one might refine layer targeting based on search_type:
        if not target_layers:  # If user didn't specify layers, infer from search_type
            if request.search_type == "semantic":
                target_layers = [MemoryLayer.LONG_TERM]
            elif request.search_type == "keyword":
                target_layers = [MemoryLayer.MID_TERM]
            elif request.search_type == "hybrid":  # Hybrid typically involves vector store
                target_layers = [MemoryLayer.LONG_TERM]  # UMS search should pass this to Weaviate
            # If still None, UMS will search all its configured stores.

        search_results: List[CoreSearchResult] = await ums.search(
            query=request.query, limit=request.limit, layers=target_layers, filters=request.filters
        )

        response_results = [
            SearchResultResponse(
                item=MemoryItemResponse(
                    id=sr.item.id,
                    content=sr.item.content,
                    metadata=sr.item.metadata,
                    timestamp=sr.item.timestamp.isoformat(),
                    layer=sr.item.layer.value,
                    ttl=sr.item.ttl,
                ),
                score=sr.score,
            )
            for sr in search_results
        ]
        return SearchMemoriesResponse(results=response_results, count=len(response_results))
    except Exception as e:
        logger.error(f"MCP Search Memories error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/orchestra_memory/forget", response_model=ForgetResponse)
async def forget_endpoint(request: ForgetRequest, ums: UnifiedMemoryService = Depends(get_ums)):
    try:
        # Check if item exists first to provide a better "not_found" status
        # This adds an extra read, but improves API contract.
        # Alternatively, UMS.evict could return a more detailed status.
        item_exists = await ums.retrieve(request.item_id)
        if not item_exists:
            return ForgetResponse(status="not_found", error="Item ID not found in memory.")

        success = await ums.evict(request.item_id)
        if success:
            return ForgetResponse(status="success")
        else:
            # This case might be hard to distinguish from "not_found" if evict itself doesn't error
            # but simply finds nothing to delete across layers.
            return ForgetResponse(status="failed", error="Failed to evict item from all layers.")
    except Exception as e:
        logger.error(f"MCP Forget error for item {request.item_id}: {e}", exc_info=True)
        return ForgetResponse(status="failed", error=str(e))


@app.get("/mcp/orchestra_memory/get_memory_stats", response_model=GetMemoryStatsResponse)
async def get_memory_stats_endpoint(ums: UnifiedMemoryService = Depends(get_ums)):
    try:
        stats = await ums.get_stats()
        return GetMemoryStatsResponse(stats=stats)
    except Exception as e:
        logger.error(f"MCP Get Memory Stats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# --- Health Endpoint ---
@app.get("/health")
async def health_check_endpoint(ums: UnifiedMemoryService = Depends(get_ums)):
    try:
        stats = await ums.get_stats()
        overall_healthy = True
        layer_health_details = {}

        for layer_name, layer_info in stats.get("layers", {}).items():
            is_healthy = layer_info.get("available", False) and layer_info.get("healthy", False)
            layer_health_details[layer_name] = {"healthy": is_healthy, "details": layer_info}
            if not is_healthy:
                overall_healthy = False

        if not stats.get("layers"):  # No layers configured or stats failed
            overall_healthy = False

        if overall_healthy:
            return {"status": "healthy", "service": "orchestra-memory-mcp", "details": layer_health_details}
        else:
            logger.warning(f"Memory service health check failed: {layer_health_details}")
            raise HTTPException(
                status_code=503,
                detail={"message": "One or more memory layers are unhealthy.", "details": layer_health_details},
            )
    except Exception as e:
        logger.error(f"Health check endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


if __name__ == "__main__":
    port = int(os.getenv("MCP_ORCHESTRA_MEMORY_PORT", "8002"))
    host = os.getenv("MCP_ORCHESTRA_MEMORY_HOST", "0.0.0.0")

    logger.info(f"Starting Orchestra Memory MCP Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
