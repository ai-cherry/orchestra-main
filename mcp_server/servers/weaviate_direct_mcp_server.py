#!/usr/bin/env python3
"""
Weaviate Direct MCP Server.

This server provides direct access to Weaviate functionalities,
allowing AI models (e.g., via Cursor IDE) or other services to perform
fine-grained operations like schema inspection, object manipulation,
hybrid search, and raw GraphQL queries.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

import uvicorn
import weaviate
import weaviate.classes as wvc  # For Weaviate Client v4 classes
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field

# Assuming the config module is in the parent directory relative to this file's location
# Adjust if your project structure is different.
from mcp_server.config.weaviate_mcp_config import (
    get_weaviate_client_params,
    validate_weaviate_config,
    log_weaviate_config,
)

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Weaviate Direct MCP Server",
    description="MCP server for direct and advanced Weaviate operations.",
    version="1.0.0",
)

# Global Weaviate client instance
weaviate_client: Optional[weaviate.WeaviateClient] = None


# --- Pydantic Models for Requests and Responses ---
class GetSchemaRequest(BaseModel):
    class_names: Optional[List[str]] = Field(
        None, description="List of class names to get schema for. If None, get full schema."
    )


class AddObjectRequest(BaseModel):
    collection_name: str = Field(..., description="Name of the Weaviate collection (class).")
    properties: Dict[str, Any] = Field(..., description="Properties of the object.")
    vector: Optional[List[float]] = Field(None, description="Optional pre-computed vector.")
    uuid: Optional[str] = Field(None, description="Optional UUID for the object.")


class AddObjectResponse(BaseModel):
    status: str = Field(..., description="Status of the operation ('success' or 'failed').")
    uuid: Optional[str] = Field(None, description="UUID of the added object.")
    error: Optional[str] = Field(None, description="Error message if operation failed.")


class GetObjectRequest(BaseModel):
    collection_name: str = Field(..., description="Name of the Weaviate collection.")
    uuid: str = Field(..., description="UUID of the object to retrieve.")
    include_vector: bool = Field(False, description="Whether to include the object's vector.")


class GetObjectResponse(BaseModel):
    properties: Optional[Dict[str, Any]] = Field(None, description="Properties of the retrieved object.")
    uuid: Optional[str] = None
    vector: Optional[List[float]] = None
    error: Optional[str] = None


class DeleteObjectRequest(BaseModel):
    collection_name: str = Field(..., description="Name of the Weaviate collection.")
    uuid: str = Field(..., description="UUID of the object to delete.")


class DeleteObjectResponse(BaseModel):
    status: str = Field(..., description="Status of the operation ('success' or 'failed').")
    error: Optional[str] = Field(None, description="Error message if operation failed.")


class HybridSearchRequest(BaseModel):
    collection_name: str = Field(..., description="Name of the Weaviate collection.")
    query_text: str = Field(..., description="Text to search for.")
    alpha: float = Field(0.5, description="Weighting factor for hybrid search (0=keyword, 1=vector).")
    vector: Optional[List[float]] = Field(None, description="Optional query vector.")
    query_properties: Optional[List[str]] = Field(None, description="Properties to search in for keyword part.")
    limit: int = Field(10, description="Maximum number of results to return.")
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Simple key-value filters for properties (e.g., {'property': 'value'}). More complex filters need GraphQL.",
    )
    properties_to_return: Optional[List[str]] = Field(
        None, description="Specific properties to return for each object."
    )
    include_vector: bool = Field(False, description="Whether to include the object's vector in results.")


class SearchResultItem(BaseModel):
    uuid: str
    properties: Dict[str, Any]
    score: Optional[float] = None
    explain_score: Optional[str] = None
    vector: Optional[List[float]] = None


class HybridSearchResponse(BaseModel):
    results: List[SearchResultItem]
    count: int


class RawGraphQLRequest(BaseModel):
    graphql_query: str = Field(..., description="The raw GraphQL query string.")


class RawGraphQLResponse(BaseModel):
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[Dict[str, Any]]] = None


class MCPToolProperty(BaseModel):
    type: str
    description: Optional[str] = None
    items: Optional[Dict[str, Any]] = None  # For array type


class MCPToolParameters(BaseModel):
    type: str = "object"
    properties: Dict[str, MCPToolProperty]
    required: Optional[List[str]] = None


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    parameters: MCPToolParameters


# --- Weaviate Client Management ---
async def init_weaviate_client():
    global weaviate_client
    if not validate_weaviate_config():
        raise RuntimeError("Invalid Weaviate configuration. MCP server cannot start.")

    client_params = get_weaviate_client_params()
    logger.info(f"Attempting to connect to Weaviate with params: {client_params}")

    # Extract connection parameters for connect_to_custom
    # Note: weaviate-client v4 uses connect_to_custom or connect_to_local, etc.
    # For a generic setup, connect_to_custom is versatile.

    connection_params = weaviate.config.ConnectionParams.from_params(
        http_host=client_params.get("http_host", "localhost"),
        http_port=client_params.get("http_port", 8080),
        http_secure=client_params.get("http_secure", False),
        grpc_host=client_params.get("grpc_host", "localhost"),  # Ensure gRPC host is correctly set
        grpc_port=client_params.get("grpc_port", 50051),
        grpc_secure=client_params.get("grpc_secure", False),
    )

    try:
        weaviate_client = weaviate.WeaviateClient(
            connection_params=connection_params,
            auth_client_secret=client_params.get("auth_client_secret"),
            additional_headers=client_params.get("additional_headers"),
            # startup_period specifies how long to wait for Weaviate to be ready.
            # Set to None to disable startup checks if Weaviate might not be up immediately,
            # but then health checks become more critical.
            startup_period=int(os.getenv("WEAVIATE_STARTUP_PERIOD", "30")),
        )
        weaviate_client.connect()  # Explicitly connect
        if not weaviate_client.is_ready():
            raise ConnectionError("Weaviate client connected but instance is not ready.")
        logger.info("Successfully connected to Weaviate and instance is ready.")
    except Exception as e:
        logger.error(f"Failed to initialize Weaviate client: {e}", exc_info=True)
        weaviate_client = None  # Ensure client is None if connection failed
        raise RuntimeError(f"Weaviate connection failed: {e}")


async def get_client() -> weaviate.WeaviateClient:
    if weaviate_client is None or not weaviate_client.is_connected():
        logger.warning("Weaviate client not initialized or not connected. Attempting to re-initialize.")
        await init_weaviate_client()  # This will raise if it fails
    if weaviate_client is None:  # Check again after attempt
        raise HTTPException(status_code=503, detail="Weaviate service unavailable - client not initialized.")
    return weaviate_client


@app.on_event("startup")
async def startup_event():
    logger.info("Weaviate Direct MCP Server starting up...")
    try:
        await init_weaviate_client()
    except Exception as e:
        # If init fails, the server might still start but endpoints will fail.
        # Consider exiting if a connection is critical for startup.
        logger.critical(
            f"Critical error during Weaviate client initialization: {e}. Server might not function correctly."
        )


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Weaviate Direct MCP Server shutting down...")
    if weaviate_client and weaviate_client.is_connected():
        weaviate_client.close()
        logger.info("Weaviate client connection closed.")


# --- MCP Tool Definitions ---
@app.get("/mcp/weaviate_direct/tools", response_model=List[MCPToolDefinition])
async def get_mcp_tools():
    tools = [
        MCPToolDefinition(
            name="get_schema",
            description="Get the full Weaviate schema or schema for specific classes.",
            parameters=MCPToolParameters(
                properties={
                    "class_names": MCPToolProperty(
                        type="array", items={"type": "string"}, description="Optional list of class names."
                    )
                }
            ),
        ),
        MCPToolDefinition(
            name="add_object",
            description="Add a single object to a Weaviate collection.",
            parameters=MCPToolParameters(
                properties={
                    "collection_name": MCPToolProperty(type="string", description="Name of the collection (class)."),
                    "properties": MCPToolProperty(type="object", description="Object properties."),
                    "vector": MCPToolProperty(
                        type="array", items={"type": "number"}, description="Optional pre-computed vector."
                    ),
                    "uuid": MCPToolProperty(type="string", description="Optional UUID for the object."),
                },
                required=["collection_name", "properties"],
            ),
        ),
        MCPToolDefinition(
            name="get_object",
            description="Get a single object by UUID from a Weaviate collection.",
            parameters=MCPToolParameters(
                properties={
                    "collection_name": MCPToolProperty(type="string", description="Name of the collection."),
                    "uuid": MCPToolProperty(type="string", description="UUID of the object."),
                    "include_vector": MCPToolProperty(
                        type="boolean", description="Include vector in response (default: false)."
                    ),
                },
                required=["collection_name", "uuid"],
            ),
        ),
        MCPToolDefinition(
            name="delete_object",
            description="Delete a single object by UUID from a Weaviate collection.",
            parameters=MCPToolParameters(
                properties={
                    "collection_name": MCPToolProperty(type="string", description="Name of the collection."),
                    "uuid": MCPToolProperty(type="string", description="UUID of the object to delete."),
                },
                required=["collection_name", "uuid"],
            ),
        ),
        MCPToolDefinition(
            name="hybrid_search",
            description="Perform a hybrid search (vector + keyword) on a Weaviate collection.",
            parameters=MCPToolParameters(
                properties={
                    "collection_name": MCPToolProperty(type="string", description="Name of the collection."),
                    "query_text": MCPToolProperty(type="string", description="Text to search for."),
                    "alpha": MCPToolProperty(
                        type="number", description="Weighting for hybrid (0=keyword, 1=vector, default 0.5)."
                    ),
                    "vector": MCPToolProperty(
                        type="array", items={"type": "number"}, description="Optional query vector."
                    ),
                    "query_properties": MCPToolProperty(
                        type="array", items={"type": "string"}, description="Properties for keyword search."
                    ),
                    "limit": MCPToolProperty(type="integer", description="Max results (default 10)."),
                    "filters": MCPToolProperty(type="object", description="Simple key-value filters."),
                    "properties_to_return": MCPToolProperty(
                        type="array", items={"type": "string"}, description="Specific properties to return."
                    ),
                    "include_vector": MCPToolProperty(
                        type="boolean", description="Include vector in results (default false)."
                    ),
                },
                required=["collection_name", "query_text"],
            ),
        ),
        MCPToolDefinition(
            name="raw_graphql_query",
            description="Execute a raw GraphQL query against Weaviate.",
            parameters=MCPToolParameters(
                properties={"graphql_query": MCPToolProperty(type="string", description="The GraphQL query string.")},
                required=["graphql_query"],
            ),
        ),
    ]
    return tools


# --- Tool Endpoints ---
@app.post("/mcp/weaviate_direct/get_schema")
async def get_schema(request: GetSchemaRequest, client: weaviate.WeaviateClient = Depends(get_client)):
    try:
        if request.class_names:
            schema_details = {}
            for class_name in request.class_names:
                try:
                    schema_details[class_name] = client.collections.get(class_name).config.get().to_dict()
                except Exception as e:
                    logger.warning(f"Could not get schema for class {class_name}: {e}")
                    schema_details[class_name] = {"error": str(e)}
            return schema_details
        else:
            return client.collections.list_all(simple=False)  # simple=False gives full config
    except Exception as e:
        logger.error(f"Error getting schema: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting schema: {str(e)}")


@app.post("/mcp/weaviate_direct/add_object", response_model=AddObjectResponse)
async def add_object(request: AddObjectRequest, client: weaviate.WeaviateClient = Depends(get_client)):
    try:
        collection = client.collections.get(request.collection_name)
        uuid_returned = collection.data.insert(
            properties=request.properties, vector=request.vector, uuid=request.uuid  # Let Weaviate generate if None
        )
        return AddObjectResponse(status="success", uuid=str(uuid_returned))
    except Exception as e:
        logger.error(f"Error adding object to {request.collection_name}: {e}", exc_info=True)
        return AddObjectResponse(status="failed", error=str(e))


@app.post("/mcp/weaviate_direct/get_object", response_model=GetObjectResponse)
async def get_object(request: GetObjectRequest, client: weaviate.WeaviateClient = Depends(get_client)):
    try:
        collection = client.collections.get(request.collection_name)
        obj = collection.query.fetch_object_by_id(uuid=request.uuid, include_vector=request.include_vector)
        if obj:
            return GetObjectResponse(
                properties=obj.properties,
                uuid=str(obj.uuid),
                vector=obj.vector.get("default") if obj.vector and request.include_vector else None,
            )
        return GetObjectResponse(
            properties=None, error=f"Object with UUID {request.uuid} not found in {request.collection_name}."
        )
    except Exception as e:
        logger.error(f"Error getting object {request.uuid} from {request.collection_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/weaviate_direct/delete_object", response_model=DeleteObjectResponse)
async def delete_object(request: DeleteObjectRequest, client: weaviate.WeaviateClient = Depends(get_client)):
    try:
        collection = client.collections.get(request.collection_name)
        collection.data.delete_by_id(uuid=request.uuid)
        # Delete by ID in v4 does not return a specific success/fail count, raises on error
        return DeleteObjectResponse(status="success")
    except weaviate.exceptions.UnexpectedStatusCodeError as e:
        if e.status_code == 404:  # Not found
            logger.warning(f"Object {request.uuid} not found for deletion in {request.collection_name}.")
            return DeleteObjectResponse(status="failed", error="Object not found.")
        logger.error(f"Error deleting object {request.uuid} from {request.collection_name}: {e}", exc_info=True)
        return DeleteObjectResponse(status="failed", error=str(e))
    except Exception as e:
        logger.error(f"Error deleting object {request.uuid} from {request.collection_name}: {e}", exc_info=True)
        return DeleteObjectResponse(status="failed", error=str(e))


def _translate_simple_filters(filters_dict: Optional[Dict[str, Any]]) -> Optional[wvc.query.Filter]:
    if not filters_dict:
        return None

    filter_conditions = []
    for key, value in filters_dict.items():
        # This is a very basic translation, assuming direct equality.
        # Real-world scenarios might need more complex logic for operators (>, <, CONTAINS_ANY, etc.)
        # and nested structures.
        if isinstance(value, dict) and "operator" in value and "value" in value:
            op = value["operator"].lower()
            val = value["value"]
            prop = wvc.query.Filter.by_property(key)
            if op == "equal":
                filter_conditions.append(prop.equal(val))
            elif op == "not_equal":
                filter_conditions.append(prop.not_equal(val))
            elif op == "greater_than":
                filter_conditions.append(prop.greater_than(val))
            # ... add more operators as needed
            else:
                logger.warning(f"Unsupported filter operator '{op}' for key '{key}'. Skipping.")
        else:  # Default to equality
            filter_conditions.append(wvc.query.Filter.by_property(key).equal(value))

    if not filter_conditions:
        return None
    if len(filter_conditions) == 1:
        return filter_conditions[0]
    return wvc.query.Filter.all_of(filter_conditions)


@app.post("/mcp/weaviate_direct/hybrid_search", response_model=HybridSearchResponse)
async def hybrid_search(request: HybridSearchRequest, client: weaviate.WeaviateClient = Depends(get_client)):
    try:
        collection = client.collections.get(request.collection_name)

        weaviate_filters = _translate_simple_filters(request.filters)

        response = collection.query.hybrid(
            query=request.query_text,
            alpha=request.alpha,
            vector=request.vector,
            query_properties=request.query_properties,
            limit=request.limit,
            filters=weaviate_filters,
            return_properties=request.properties_to_return,
            return_metadata=wvc.query.MetadataQuery(score=True, explain_score=True, uuid=True),  # Always get UUID
            include_vector=request.include_vector,
        )

        results = []
        for obj in response.objects:
            results.append(
                SearchResultItem(
                    uuid=str(obj.uuid),
                    properties=obj.properties,
                    score=obj.metadata.score if obj.metadata else None,
                    explain_score=obj.metadata.explain_score if obj.metadata else None,
                    vector=obj.vector.get("default") if obj.vector and request.include_vector else None,
                )
            )
        return HybridSearchResponse(results=results, count=len(results))
    except Exception as e:
        logger.error(f"Error performing hybrid search on {request.collection_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/weaviate_direct/raw_graphql_query", response_model=RawGraphQLResponse)
async def raw_graphql_query(request: RawGraphQLRequest, client: weaviate.WeaviateClient = Depends(get_client)):
    try:
        result = client.query.raw(request.graphql_query)
        # The result from client.query.raw() is already a dict matching GraphQL response structure
        return RawGraphQLResponse(data=result.get("data"), errors=result.get("errors"))
    except Exception as e:
        logger.error(f"Error executing raw GraphQL query: {e}", exc_info=True)
        # Try to parse a more specific error if possible from Weaviate exceptions
        error_detail = str(e)
        if hasattr(e, "messages"):  # For WeaviateQueryError
            error_detail = e.messages
        raise HTTPException(status_code=500, detail=error_detail)


# --- Health Endpoint ---
@app.get("/mcp/weaviate_direct/health")
async def health_check_endpoint(client: weaviate.WeaviateClient = Depends(get_client)):
    if client and client.is_ready():  # is_ready() checks connection and server status
        return {"status": "healthy", "service": "weaviate-direct-mcp"}
    else:
        logger.error("Health check failed: Weaviate client not ready or not connected.")
        raise HTTPException(status_code=503, detail="Weaviate service unavailable or not ready")


if __name__ == "__main__":
    port = int(os.getenv("MCP_WEAVIATE_DIRECT_PORT", "8001"))
    host = os.getenv("MCP_WEAVIATE_DIRECT_HOST", "0.0.0.0")

    logger.info(f"Starting Weaviate Direct MCP Server on {host}:{port}")
    # Validate config before starting server
    if not validate_weaviate_config():
        logger.critical("Invalid Weaviate configuration. Server will not start correctly.")
        # Depending on severity, you might want to sys.exit(1) here

    uvicorn.run(app, host=host, port=port)
