#!/usr/bin/env python3
"""
MCP Server for Google Firestore Management

This server enables Claude 4 to manage Firestore documents and collections
through the Model Context Protocol (MCP).
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import google.auth
from fastapi import FastAPI, HTTPException
from google.cloud import firestore
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app for MCP server
app = FastAPI(
    title="GCP Firestore MCP Server",
    description="MCP server for managing Google Firestore documents and collections",
    version="1.0.0",
)

# Get configuration from environment
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATABASE_ID = os.getenv("FIRESTORE_DATABASE_ID", "(default)")

# Initialize Firestore client
try:
    credentials, project = google.auth.default()
    if not PROJECT_ID:
        PROJECT_ID = project
    firestore_client = firestore.Client(project=PROJECT_ID, database=DATABASE_ID)
    logger.info(f"Firestore client initialized for project: {PROJECT_ID}, database: {DATABASE_ID}")
except Exception as e:
    logger.error(f"Failed to initialize Firestore client: {e}")
    firestore_client = None


class DocumentRequest(BaseModel):
    """Request model for document operations"""

    collection: str = Field(..., description="Collection name")
    document_id: str = Field(..., description="Document ID")
    data: Dict[str, Any] = Field(..., description="Document data")
    merge: bool = Field(default=False, description="Whether to merge with existing document")


class UpdateRequest(BaseModel):
    """Request model for updating documents"""

    collection: str = Field(..., description="Collection name")
    document_id: str = Field(..., description="Document ID")
    updates: Dict[str, Any] = Field(..., description="Fields to update")


class QueryRequest(BaseModel):
    """Request model for querying documents"""

    collection: str = Field(..., description="Collection name")
    filters: List[Dict[str, Any]] = Field(default=[], description="Query filters")
    order_by: Optional[str] = Field(None, description="Field to order by")
    limit: int = Field(default=10, description="Maximum number of results")
    offset: int = Field(default=0, description="Number of results to skip")


class BatchWriteRequest(BaseModel):
    """Request model for batch write operations"""

    operations: List[Dict[str, Any]] = Field(..., description="List of write operations")


class CollectionRequest(BaseModel):
    """Request model for collection operations"""

    collection: str = Field(..., description="Collection name")
    parent_document: Optional[Dict[str, str]] = Field(None, description="Parent document path for subcollections")


class MCPToolDefinition(BaseModel):
    """MCP tool definition for Claude"""

    name: str
    description: str
    parameters: Dict[str, Any]


@app.get("/mcp/firestore/tools")
async def get_tools() -> List[MCPToolDefinition]:
    """Return available tools for Claude to use"""
    return [
        MCPToolDefinition(
            name="create_document",
            description="Create a new document in Firestore",
            parameters={
                "type": "object",
                "properties": {
                    "collection": {"type": "string", "description": "Collection name"},
                    "document_id": {
                        "type": "string",
                        "description": "Document ID (optional, auto-generated if not provided)",
                    },
                    "data": {"type": "object", "description": "Document data"},
                },
                "required": ["collection", "data"],
            },
        ),
        MCPToolDefinition(
            name="get_document",
            description="Get a document from Firestore by ID",
            parameters={
                "type": "object",
                "properties": {
                    "collection": {"type": "string", "description": "Collection name"},
                    "document_id": {"type": "string", "description": "Document ID"},
                },
                "required": ["collection", "document_id"],
            },
        ),
        MCPToolDefinition(
            name="update_document",
            description="Update an existing document in Firestore",
            parameters={
                "type": "object",
                "properties": {
                    "collection": {"type": "string", "description": "Collection name"},
                    "document_id": {"type": "string", "description": "Document ID"},
                    "updates": {"type": "object", "description": "Fields to update"},
                },
                "required": ["collection", "document_id", "updates"],
            },
        ),
        MCPToolDefinition(
            name="delete_document",
            description="Delete a document from Firestore",
            parameters={
                "type": "object",
                "properties": {
                    "collection": {"type": "string", "description": "Collection name"},
                    "document_id": {"type": "string", "description": "Document ID"},
                },
                "required": ["collection", "document_id"],
            },
        ),
        MCPToolDefinition(
            name="query_documents",
            description="Query documents in a collection with filters",
            parameters={
                "type": "object",
                "properties": {
                    "collection": {"type": "string", "description": "Collection name"},
                    "filters": {
                        "type": "array",
                        "description": "Query filters",
                        "items": {
                            "type": "object",
                            "properties": {
                                "field": {"type": "string"},
                                "operator": {
                                    "type": "string",
                                    "enum": [
                                        "==",
                                        "!=",
                                        "<",
                                        "<=",
                                        ">",
                                        ">=",
                                        "in",
                                        "not-in",
                                        "array-contains",
                                        "array-contains-any",
                                    ],
                                },
                                "value": {},
                            },
                        },
                    },
                    "order_by": {"type": "string", "description": "Field to order by"},
                    "limit": {"type": "integer", "description": "Maximum number of results"},
                },
                "required": ["collection"],
            },
        ),
        MCPToolDefinition(
            name="list_collections",
            description="List all collections in the database",
            parameters={"type": "object", "properties": {}},
        ),
        MCPToolDefinition(
            name="batch_write",
            description="Perform multiple write operations in a single batch",
            parameters={
                "type": "object",
                "properties": {
                    "operations": {
                        "type": "array",
                        "description": "List of write operations",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "enum": ["create", "update", "delete"]},
                                "collection": {"type": "string"},
                                "document_id": {"type": "string"},
                                "data": {"type": "object"},
                            },
                        },
                    }
                },
                "required": ["operations"],
            },
        ),
    ]


@app.post("/mcp/firestore/document/create")
async def create_document(request: DocumentRequest) -> Dict[str, Any]:
    """Create a new document in Firestore"""
    if not firestore_client:
        raise HTTPException(status_code=500, detail="Firestore client not initialized")

    try:
        collection_ref = firestore_client.collection(request.collection)

        # Add timestamp
        doc_data = request.data.copy()
        doc_data["_created_at"] = datetime.utcnow()
        doc_data["_updated_at"] = datetime.utcnow()

        if request.document_id:
            # Create with specific ID
            doc_ref = collection_ref.document(request.document_id)
            doc_ref.set(doc_data, merge=request.merge)
            document_id = request.document_id
        else:
            # Auto-generate ID
            doc_ref = collection_ref.add(doc_data)
            document_id = doc_ref[1].id

        logger.info(f"Created document {document_id} in collection {request.collection}")

        return {
            "status": "success",
            "collection": request.collection,
            "document_id": document_id,
            "message": "Document created successfully",
        }

    except Exception as e:
        logger.error(f"Failed to create document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/firestore/document/{collection}/{document_id}")
async def get_document(collection: str, document_id: str) -> Dict[str, Any]:
    """Get a document from Firestore"""
    if not firestore_client:
        raise HTTPException(status_code=500, detail="Firestore client not initialized")

    try:
        doc_ref = firestore_client.collection(collection).document(document_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Document not found")

        doc_data = doc.to_dict()

        # Convert timestamps to ISO format
        for field in ["_created_at", "_updated_at"]:
            if field in doc_data and hasattr(doc_data[field], "isoformat"):
                doc_data[field] = doc_data[field].isoformat()

        return {"status": "success", "collection": collection, "document_id": document_id, "data": doc_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/mcp/firestore/document/update")
async def update_document(request: UpdateRequest) -> Dict[str, Any]:
    """Update an existing document in Firestore"""
    if not firestore_client:
        raise HTTPException(status_code=500, detail="Firestore client not initialized")

    try:
        doc_ref = firestore_client.collection(request.collection).document(request.document_id)

        # Check if document exists
        if not doc_ref.get().exists:
            raise HTTPException(status_code=404, detail="Document not found")

        # Add update timestamp
        updates = request.updates.copy()
        updates["_updated_at"] = datetime.utcnow()

        doc_ref.update(updates)

        logger.info(f"Updated document {request.document_id} in collection {request.collection}")

        return {
            "status": "success",
            "collection": request.collection,
            "document_id": request.document_id,
            "message": "Document updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/mcp/firestore/document/{collection}/{document_id}")
async def delete_document(collection: str, document_id: str) -> Dict[str, Any]:
    """Delete a document from Firestore"""
    if not firestore_client:
        raise HTTPException(status_code=500, detail="Firestore client not initialized")

    try:
        doc_ref = firestore_client.collection(collection).document(document_id)

        # Check if document exists
        if not doc_ref.get().exists:
            raise HTTPException(status_code=404, detail="Document not found")

        doc_ref.delete()

        logger.info(f"Deleted document {document_id} from collection {collection}")

        return {
            "status": "success",
            "collection": collection,
            "document_id": document_id,
            "message": "Document deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/firestore/query")
async def query_documents(request: QueryRequest) -> Dict[str, Any]:
    """Query documents in a collection"""
    if not firestore_client:
        raise HTTPException(status_code=500, detail="Firestore client not initialized")

    try:
        query = firestore_client.collection(request.collection)

        # Apply filters
        for filter_spec in request.filters:
            field = filter_spec.get("field")
            operator = filter_spec.get("operator", "==")
            value = filter_spec.get("value")

            if field and value is not None:
                if operator == "==":
                    query = query.where(field, "==", value)
                elif operator == "!=":
                    query = query.where(field, "!=", value)
                elif operator == "<":
                    query = query.where(field, "<", value)
                elif operator == "<=":
                    query = query.where(field, "<=", value)
                elif operator == ">":
                    query = query.where(field, ">", value)
                elif operator == ">=":
                    query = query.where(field, ">=", value)
                elif operator == "in":
                    query = query.where(field, "in", value)
                elif operator == "not-in":
                    query = query.where(field, "not-in", value)
                elif operator == "array-contains":
                    query = query.where(field, "array-contains", value)
                elif operator == "array-contains-any":
                    query = query.where(field, "array-contains-any", value)

        # Apply ordering
        if request.order_by:
            query = query.order_by(request.order_by)

        # Apply limit and offset
        if request.offset > 0:
            query = query.offset(request.offset)
        query = query.limit(request.limit)

        # Execute query
        docs = query.stream()

        results = []
        for doc in docs:
            doc_data = doc.to_dict()

            # Convert timestamps to ISO format
            for field in ["_created_at", "_updated_at"]:
                if field in doc_data and hasattr(doc_data[field], "isoformat"):
                    doc_data[field] = doc_data[field].isoformat()

            results.append({"document_id": doc.id, "data": doc_data})

        logger.info(f"Query returned {len(results)} documents from collection {request.collection}")

        return {"status": "success", "collection": request.collection, "count": len(results), "documents": results}

    except Exception as e:
        logger.error(f"Failed to query documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/firestore/collections")
async def list_collections() -> Dict[str, Any]:
    """List all collections in the database"""
    if not firestore_client:
        raise HTTPException(status_code=500, detail="Firestore client not initialized")

    try:
        collections = firestore_client.collections()
        collection_names = [collection.id for collection in collections]

        logger.info(f"Found {len(collection_names)} collections")

        return {"status": "success", "count": len(collection_names), "collections": collection_names}

    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/firestore/batch")
async def batch_write(request: BatchWriteRequest) -> Dict[str, Any]:
    """Perform batch write operations"""
    if not firestore_client:
        raise HTTPException(status_code=500, detail="Firestore client not initialized")

    try:
        batch = firestore_client.batch()
        operation_count = 0

        for op in request.operations:
            op_type = op.get("type")
            collection = op.get("collection")
            document_id = op.get("document_id")
            data = op.get("data", {})

            if not collection or not document_id:
                continue

            doc_ref = firestore_client.collection(collection).document(document_id)

            if op_type == "create":
                doc_data = data.copy()
                doc_data["_created_at"] = datetime.utcnow()
                doc_data["_updated_at"] = datetime.utcnow()
                batch.set(doc_ref, doc_data)
                operation_count += 1
            elif op_type == "update":
                updates = data.copy()
                updates["_updated_at"] = datetime.utcnow()
                batch.update(doc_ref, updates)
                operation_count += 1
            elif op_type == "delete":
                batch.delete(doc_ref)
                operation_count += 1

        # Commit the batch
        batch.commit()

        logger.info(f"Batch write completed with {operation_count} operations")

        return {
            "status": "success",
            "operations_count": operation_count,
            "message": "Batch write completed successfully",
        }

    except Exception as e:
        logger.error(f"Failed to perform batch write: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/firestore/document/exists/{collection}/{document_id}")
async def check_document_exists(collection: str, document_id: str) -> Dict[str, Any]:
    """Check if a document exists"""
    if not firestore_client:
        raise HTTPException(status_code=500, detail="Firestore client not initialized")

    try:
        doc_ref = firestore_client.collection(collection).document(document_id)
        exists = doc_ref.get().exists

        return {"status": "success", "collection": collection, "document_id": document_id, "exists": exists}

    except Exception as e:
        logger.error(f"Failed to check document existence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "service": "gcp-firestore-mcp",
        "project_id": PROJECT_ID,
        "database_id": DATABASE_ID,
        "client_initialized": firestore_client is not None,
    }

    # Test Firestore connection
    if firestore_client:
        try:
            # Try to list collections as a connectivity test
            list(firestore_client.collections())
            health_status["firestore_connected"] = True
        except Exception as e:
            health_status["firestore_connected"] = False
            health_status["firestore_error"] = str(e)

    return health_status


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8002"))
    uvicorn.run(app, host="0.0.0.0", port=port)
