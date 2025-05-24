#!/usr/bin/env python3
"""
MCP Server for Memory Management
Implements the layered memory architecture with short, mid, and long-term storage
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import qdrant_client
import redis
from fastapi import BackgroundTasks, FastAPI, HTTPException
from google.cloud import firestore
from pydantic import BaseModel, Field
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

# --- MCP CONFIG IMPORTS ---
from mcp_server.config.loader import load_config
from mcp_server.config.models import MCPConfig

# Load MCP config at startup
memory_config: MCPConfig = load_config()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Memory Management MCP Server", description="Layered memory system for AI agents", version="1.0.0")

# Configuration (now loaded from unified config)
REDIS_URL = memory_config.storage.connection_string or "redis://localhost:6379"
FIRESTORE_PROJECT = os.getenv("FIRESTORE_PROJECT") or os.getenv("GCP_PROJECT_ID") or "default-project"
QDRANT_URL = os.getenv("QDRANT_URL") or "http://localhost:6333"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL") or "sentence-transformers/all-MiniLM-L6-v2"

# Prefer config values if present
if hasattr(memory_config, "redis_url") and memory_config.redis_url:
    REDIS_URL = memory_config.redis_url
if hasattr(memory_config, "firestore_project") and memory_config.firestore_project:
    FIRESTORE_PROJECT = memory_config.firestore_project
if hasattr(memory_config, "qdrant_url") and memory_config.qdrant_url:
    QDRANT_URL = memory_config.qdrant_url
if hasattr(memory_config, "embedding_model") and memory_config.embedding_model:
    EMBEDDING_MODEL = memory_config.embedding_model

# Initialize clients
try:
    # Redis for short-term memory
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)

    # Firestore for mid-term memory
    firestore_client = firestore.Client(project=FIRESTORE_PROJECT)

    # Qdrant for long-term memory
    qdrant_client = qdrant_client.QdrantClient(url=QDRANT_URL)

    # Sentence transformer for embeddings
    embedder = SentenceTransformer(EMBEDDING_MODEL)

except Exception as e:
    logger.error(f"Failed to initialize memory clients: {e}")
    redis_client = None
    firestore_client = None
    qdrant_client = None
    embedder = None


class MemoryItem(BaseModel):
    """Memory item model"""

    id: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    agent_id: Optional[str] = None
    conversation_id: Optional[str] = None
    memory_type: str = Field(default="general", description="Type of memory")


class MemoryQuery(BaseModel):
    """Query model for memory search"""

    query: str
    agent_id: Optional[str] = None
    conversation_id: Optional[str] = None
    memory_layers: List[str] = Field(default=["short", "mid", "long"])
    max_results: int = Field(default=10, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class ConsolidationRequest(BaseModel):
    """Request for memory consolidation"""

    agent_id: Optional[str] = None
    max_age_hours: int = Field(default=24, description="Max age for short-term memories")
    importance_threshold: float = Field(default=0.7, description="Min importance for long-term")


class MCPToolDefinition(BaseModel):
    """MCP tool definition"""

    name: str
    description: str
    parameters: Dict[str, Any]


def generate_memory_id(content: str, agent_id: str = None) -> str:
    """Generate unique memory ID"""
    data = f"{content}{agent_id or ''}{datetime.utcnow().isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


async def store_short_term(memory: MemoryItem) -> bool:
    """Store in short-term memory (Redis)"""
    if not redis_client:
        return False

    try:
        key = f"memory:short:{memory.id}"
        data = memory.dict()
        data["timestamp"] = data["timestamp"].isoformat()

        # Store with 1 hour TTL by default
        ttl = 3600
        redis_client.setex(key, ttl, json.dumps(data))

        # Add to agent's memory index
        if memory.agent_id:
            redis_client.sadd(f"agent:memories:{memory.agent_id}", key)
            redis_client.expire(f"agent:memories:{memory.agent_id}", ttl)

        return True
    except Exception as e:
        logger.error(f"Failed to store short-term memory: {e}")
        return False


async def store_mid_term(memory: MemoryItem) -> bool:
    """Store in mid-term memory (Firestore)"""
    if not firestore_client:
        return False

    try:
        doc_ref = firestore_client.collection("memories").document(memory.id)
        data = memory.dict()
        data["timestamp"] = data["timestamp"]
        data["expiry"] = datetime.utcnow() + timedelta(days=30)

        doc_ref.set(data)

        # Update agent's memory collection
        if memory.agent_id:
            agent_ref = firestore_client.collection("agents").document(memory.agent_id)
            agent_ref.update({"memory_ids": firestore.ArrayUnion([memory.id]), "last_updated": datetime.utcnow()})

        return True
    except Exception as e:
        logger.error(f"Failed to store mid-term memory: {e}")
        return False


async def store_long_term(memory: MemoryItem, embedding: np.ndarray) -> bool:
    """Store in long-term memory (Qdrant)"""
    if not qdrant_client:
        return False

    try:
        # Ensure collection exists
        collections = qdrant_client.get_collections().collections
        if not any(c.name == "long_term_memory" for c in collections):
            qdrant_client.create_collection(
                collection_name="long_term_memory", vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )

        # Store the memory
        point = PointStruct(
            id=memory.id,
            vector=embedding.tolist(),
            payload={
                "content": memory.content,
                "metadata": memory.metadata,
                "timestamp": memory.timestamp.isoformat(),
                "importance": memory.importance,
                "agent_id": memory.agent_id,
                "conversation_id": memory.conversation_id,
                "memory_type": memory.memory_type,
            },
        )

        qdrant_client.upsert(collection_name="long_term_memory", points=[point])

        return True
    except Exception as e:
        logger.error(f"Failed to store long-term memory: {e}")
        return False


@app.get("/mcp/tools")
async def get_tools() -> List[MCPToolDefinition]:
    """Return available memory management tools"""
    return [
        MCPToolDefinition(
            name="store_memory",
            description="Store a memory in the appropriate layer based on importance",
            parameters={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Memory content"},
                    "importance": {"type": "number", "description": "Importance score (0-1)"},
                    "metadata": {"type": "object", "description": "Additional metadata"},
                    "agent_id": {"type": "string", "description": "Agent identifier"},
                    "memory_type": {"type": "string", "description": "Type of memory"},
                },
                "required": ["content"],
            },
        ),
        MCPToolDefinition(
            name="query_memory",
            description="Query memories across all layers",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "agent_id": {"type": "string", "description": "Filter by agent"},
                    "memory_layers": {"type": "array", "description": "Layers to search"},
                    "max_results": {"type": "integer", "description": "Maximum results"},
                },
                "required": ["query"],
            },
        ),
        MCPToolDefinition(
            name="consolidate_memories",
            description="Consolidate short-term memories to longer-term storage",
            parameters={
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "Agent to consolidate for"},
                    "importance_threshold": {"type": "number", "description": "Min importance"},
                },
            },
        ),
        MCPToolDefinition(
            name="get_agent_memories",
            description="Get all memories for a specific agent",
            parameters={
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "Agent identifier"},
                    "memory_layer": {"type": "string", "description": "Memory layer to query"},
                },
                "required": ["agent_id"],
            },
        ),
    ]


@app.post("/mcp/store_memory")
async def store_memory(memory: MemoryItem, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Store a memory in the appropriate layer"""
    # Generate ID if not provided
    if not memory.id:
        memory.id = generate_memory_id(memory.content, memory.agent_id)

    # Determine storage layer based on importance
    layers_stored = []

    # Always store in short-term
    if await store_short_term(memory):
        layers_stored.append("short-term")

    # Store in mid-term if importance > 0.5
    if memory.importance > 0.5:
        if await store_mid_term(memory):
            layers_stored.append("mid-term")

    # Store in long-term if importance > 0.8
    if memory.importance > 0.8 and embedder:
        embedding = embedder.encode(memory.content)
        if await store_long_term(memory, embedding):
            layers_stored.append("long-term")

    # Schedule background consolidation if needed
    if memory.agent_id:
        background_tasks.add_task(check_consolidation_needed, memory.agent_id)

    return {
        "status": "success",
        "memory_id": memory.id,
        "layers_stored": layers_stored,
        "message": f"Memory stored in {len(layers_stored)} layer(s)",
    }


@app.post("/mcp/query_memory")
async def query_memory(query: MemoryQuery) -> List[Dict[str, Any]]:
    """Query memories across layers"""
    results = []

    # Search short-term memory
    if "short" in query.memory_layers and redis_client:
        try:
            # Get all short-term memories
            keys = redis_client.keys("memory:short:*")
            for key in keys:
                data = redis_client.get(key)
                if data:
                    memory = json.loads(data)

                    # Filter by agent if specified
                    if query.agent_id and memory.get("agent_id") != query.agent_id:
                        continue

                    # Simple text matching for short-term
                    if query.query.lower() in memory["content"].lower():
                        results.append({**memory, "layer": "short-term", "score": 0.8})  # Fixed score for text match
        except Exception as e:
            logger.error(f"Error searching short-term memory: {e}")

    # Search mid-term memory
    if "mid" in query.memory_layers and firestore_client:
        try:
            # Query Firestore
            query_ref = firestore_client.collection("memories")

            if query.agent_id:
                query_ref = query_ref.where("agent_id", "==", query.agent_id)

            # Get all documents and filter
            docs = query_ref.stream()
            for doc in docs:
                memory = doc.to_dict()

                # Simple text matching
                if query.query.lower() in memory["content"].lower():
                    memory["timestamp"] = memory["timestamp"].isoformat()
                    results.append({**memory, "layer": "mid-term", "score": 0.85})
        except Exception as e:
            logger.error(f"Error searching mid-term memory: {e}")

    # Search long-term memory
    if "long" in query.memory_layers and qdrant_client and embedder:
        try:
            # Generate query embedding
            query_embedding = embedder.encode(query.query)

            # Search in Qdrant
            search_result = qdrant_client.search(
                collection_name="long_term_memory",
                query_vector=query_embedding.tolist(),
                limit=query.max_results,
                score_threshold=query.similarity_threshold,
            )

            for hit in search_result:
                memory = hit.payload

                # Filter by agent if specified
                if query.agent_id and memory.get("agent_id") != query.agent_id:
                    continue

                results.append({**memory, "layer": "long-term", "score": hit.score})
        except Exception as e:
            logger.error(f"Error searching long-term memory: {e}")

    # Sort by score and limit results
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[: query.max_results]


@app.post("/mcp/consolidate_memories")
async def consolidate_memories(request: ConsolidationRequest) -> Dict[str, Any]:
    """Consolidate memories from short-term to longer-term storage"""
    consolidated = 0

    if not redis_client:
        raise HTTPException(status_code=500, detail="Redis client not available")

    try:
        # Get all short-term memories
        keys = redis_client.keys("memory:short:*")

        for key in keys:
            data = redis_client.get(key)
            if not data:
                continue

            memory_data = json.loads(data)

            # Filter by agent if specified
            if request.agent_id and memory_data.get("agent_id") != request.agent_id:
                continue

            # Check age
            timestamp = datetime.fromisoformat(memory_data["timestamp"])
            age = datetime.utcnow() - timestamp

            if age.total_seconds() > request.max_age_hours * 3600:
                continue

            # Check importance
            if memory_data["importance"] >= request.importance_threshold:
                # Convert back to MemoryItem
                memory = MemoryItem(**memory_data)
                memory.timestamp = timestamp

                # Store in long-term
                if embedder:
                    embedding = embedder.encode(memory.content)
                    if await store_long_term(memory, embedding):
                        consolidated += 1
                        # Remove from short-term
                        redis_client.delete(key)
            elif memory_data["importance"] >= 0.5:
                # Store in mid-term
                memory = MemoryItem(**memory_data)
                memory.timestamp = timestamp

                if await store_mid_term(memory):
                    consolidated += 1
                    # Remove from short-term
                    redis_client.delete(key)

        return {
            "status": "success",
            "memories_consolidated": consolidated,
            "message": f"Consolidated {consolidated} memories",
        }

    except Exception as e:
        logger.error(f"Error during consolidation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def check_consolidation_needed(agent_id: str):
    """Background task to check if consolidation is needed"""
    try:
        if redis_client:
            # Count memories for agent
            keys = redis_client.keys("memory:short:*")
            agent_memories = 0

            for key in keys:
                data = redis_client.get(key)
                if data:
                    memory = json.loads(data)
                    if memory.get("agent_id") == agent_id:
                        agent_memories += 1

            # Trigger consolidation if too many memories
            if agent_memories > 100:
                logger.info(f"Auto-consolidating memories for agent {agent_id}")
                await consolidate_memories(ConsolidationRequest(agent_id=agent_id))
    except Exception as e:
        logger.error(f"Error in consolidation check: {e}")


@app.get("/mcp/agent_memories/{agent_id}")
async def get_agent_memories(agent_id: str, layer: str = "all") -> List[Dict[str, Any]]:
    """Get all memories for a specific agent"""
    query = MemoryQuery(
        query="",  # Empty query to get all
        agent_id=agent_id,
        memory_layers=["short", "mid", "long"] if layer == "all" else [layer],
        max_results=100,
    )

    # Use a broad search
    return await query_memory(query)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "service": "memory-mcp",
        "backends": {
            "redis": redis_client is not None,
            "firestore": firestore_client is not None,
            "qdrant": qdrant_client is not None,
            "embedder": embedder is not None,
        },
    }

    # Overall health
    all_healthy = all(status["backends"].values())
    status["status"] = "healthy" if all_healthy else "degraded"

    return status


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
