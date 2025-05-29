#!/usr/bin/env python3
"""
MemoryMCPServer: Neo4j-backed, LLM-augmented, production-grade memory server for MCP.

- Stores "episodes" as nodes in Neo4j, with embeddings, timestamps, metadata, and group_id namespacing.
- Extracts entities using LLM (OpenAI/Gemini) and links them in the graph.
- Supports hybrid semantic+graph search, robust health checks, and optional Redis/Dragonfly caching.
- All configuration/secrets via environment variables or config files.
- Exposes a clean, tool-based API for agent integration.
"""

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException
from neo4j import Driver, GraphDatabase
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

from mcp_server.config.loader import load_config
from mcp_server.config.models import MCPConfig

# --- Configuration & Logging ---
memory_config: MCPConfig = load_config()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Environment Variables & Defaults ---
NEO4J_URL = os.getenv("NEO4J_URL", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo-0125")
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "false").lower() == "true"
CACHE_URL = os.getenv("CACHE_URL", "redis://localhost:6379/0")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))
VECTOR_INDEX_NAME = os.getenv("NEO4J_VECTOR_INDEX_NAME", "memory_embeddings")

# --- Initialize Clients ---
try:
    neo4j_driver: Optional[Driver] = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    asyncio.get_event_loop().run_until_complete(asyncio.to_thread(neo4j_driver.verify_connectivity))
    logger.info(f"Connected to Neo4j at {NEO4J_URL}")

    embedder = SentenceTransformer(EMBEDDING_MODEL)
    logger.info(f"Loaded embedding model: {EMBEDDING_MODEL}")

    llm_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
    if llm_client:
        logger.info("LLM client initialized for entity extraction.")

    cache_client = aioredis.from_url(CACHE_URL, encoding="utf-8", decode_responses=True) if CACHE_ENABLED else None
    if cache_client:
        logger.info(f"Cache enabled at {CACHE_URL}")

except Exception as e:
    logger.error(f"Failed to initialize clients: {e}")
    neo4j_driver = None
    embedder = None
    llm_client = None
    cache_client = None

# --- FastAPI App ---
app = FastAPI(
    title="Memory MCP Server (Graphiti-Style)",
    description="Neo4j-backed, LLM-augmented memory server for MCP agents.",
    version="2.0.0",
)


# --- Models ---
class MemoryItem(BaseModel):
    id: Optional[str] = None
    group_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    agent_id: Optional[str] = None
    conversation_id: Optional[str] = None
    memory_type: str = Field(default="episode")
    embedding: Optional[List[float]] = None


class EntityItem(BaseModel):
    id: str
    group_id: str
    name: str
    type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MemoryQuery(BaseModel):
    group_id: str
    query: str
    agent_id: Optional[str] = None
    conversation_id: Optional[str] = None
    max_results: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class DeleteMemoryArgs(BaseModel):
    memory_id: str
    group_id: str


class ClearGraphArgs(BaseModel):
    group_id: str


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]


# --- Utility Functions ---
def generate_id(content: str, group_id: str, prefix: str = "mem") -> str:
    return f"{prefix}_{group_id[:8]}_{hashlib.sha256(f'{content}{group_id}{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:12]}"


def get_neo4j_session():
    if not neo4j_driver:
        raise ConnectionError("Neo4j driver not initialized.")
    return neo4j_driver.session()


async def run_sync_neo4j_op(fn):
    return await asyncio.to_thread(fn)


# --- Core Logic ---
async def store_memory_logic(memory: MemoryItem) -> Dict[str, Any]:
    if not neo4j_driver or not embedder:
        raise ConnectionError("Neo4j/Embedder not ready.")
    if not memory.id:
        memory.id = generate_id(memory.content, memory.group_id, memory.memory_type)
    if memory.embedding is None:
        memory.embedding = (await asyncio.to_thread(embedder.encode, memory.content)).tolist()

    node_label = memory.memory_type.capitalize()

    def _create_node_tx(tx):
        query = (
            f"MERGE (m:{node_label} {{id: $id, group_id: $group_id}}) "
            "SET m.content = $content, m.timestamp = datetime($timestamp), m.importance = $importance, "
            "m.metadata = $metadata, m.embedding = $embedding, m.memory_type = $memory_type, "
            "m.agent_id = $agent_id, m.conversation_id = $conversation_id "
            "WITH m WHERE $agent_id IS NOT NULL "
            "MERGE (a:Agent {id: $agent_id, group_id: $group_id}) SET a.last_updated = datetime() MERGE (m)-[:ASSOCIATED_WITH_AGENT]->(a) "
            "WITH m WHERE $conversation_id IS NOT NULL "
            "MERGE (c:Conversation {id: $conversation_id, group_id: $group_id}) SET c.last_updated = datetime() MERGE (m)-[:PART_OF_CONVERSATION]->(c) "
            "RETURN m.id as node_id"
        )
        tx.run(
            query,
            id=memory.id,
            group_id=memory.group_id,
            content=memory.content,
            timestamp=memory.timestamp.isoformat(),
            importance=memory.importance,
            metadata=json.dumps(memory.metadata),
            embedding=memory.embedding,
            agent_id=memory.agent_id,
            conversation_id=memory.conversation_id,
            memory_type=memory.memory_type,
        )

    await run_sync_neo4j_op(lambda: get_neo4j_session().execute_write(_create_node_tx))
    logger.info(f"Stored memory '{memory.id}' (type: {node_label}, group: {memory.group_id}).")

    # Entity extraction (episodes only)
    if memory.memory_type == "episode" and llm_client:
        try:
            entities = await extract_entities_with_llm(memory.content, memory.group_id)
            if entities:
                await store_extracted_entities(memory.id, entities, memory.group_id)
        except Exception as e:
            logger.error(f"Entity extraction failed for memory {memory.id}: {e}")
    return {"status": "success", "memory_id": memory.id, "group_id": memory.group_id}


async def extract_entities_with_llm(text_content: str, group_id: str) -> List[Dict[str, Any]]:
    if not llm_client:
        logger.info("LLM client not available. Skipping entity extraction.")
        return []
    try:
        response = await llm_client.chat.completions.create(
            model=OPENAI_API_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an advanced entity extraction service. Extract all named entities (people, organizations, concepts, locations, etc.) from the following text. Return a JSON array of objects with 'name' and 'type' fields.",
                },
                {"role": "user", "content": text_content},
            ],
            temperature=0.2,
            max_tokens=500,
        )
        extracted_data_str = response.choices[0].message.content
        if not extracted_data_str:
            return []
        if extracted_data_str.strip().startswith("```json"):
            extracted_data_str = extracted_data_str.split("```json")[1].split("```")[0].strip()
        extracted_entities_raw = json.loads(extracted_data_str)
        if isinstance(extracted_entities_raw, dict) and "entities" in extracted_entities_raw:
            extracted_entities = extracted_entities_raw["entities"]
        elif isinstance(extracted_entities_raw, list):
            extracted_entities = extracted_entities_raw
        else:
            return []
        valid_entities = [
            {"name": str(e["name"]), "type": str(e["type"]).upper()}
            for e in extracted_entities
            if isinstance(e, dict) and "name" in e and "type" in e
        ]
        return valid_entities
    except Exception as e:
        logger.error(f"LLM entity extraction error: {e}")
        return []


async def store_extracted_entities(episode_id: str, entities: List[Dict[str, Any]], group_id: str):
    if not neo4j_driver:
        return

    def _tx_logic(tx):
        for entity_data in entities:
            entity_name = entity_data.get("name")
            entity_type = entity_data.get("type", "CONCEPT").upper()
            if not entity_name:
                continue
            entity_id = generate_id(f"{entity_name}_{entity_type}", group_id, "ent")
            tx.run(
                "MERGE (e:Entity {id: $id, group_id: $group_id}) "
                "ON CREATE SET e.name = $name, e.type = $type, e.timestamp = datetime(), e.metadata = {source: 'llm_extraction'} "
                "ON MATCH SET e.last_seen = datetime(), e.type = CASE WHEN e.type <> $type THEN $type ELSE e.type END",
                id=entity_id,
                group_id=group_id,
                name=entity_name,
                type=entity_type,
            )
            tx.run(
                "MATCH (ep:Episode {id: $episode_id, group_id: $group_id}), (en:Entity {id: $entity_id, group_id: $group_id}) "
                "MERGE (ep)-[r:CONTAINS_ENTITY]->(en) ON CREATE SET r.timestamp = datetime()",
                episode_id=episode_id,
                entity_id=entity_id,
                group_id=group_id,
            )

    await run_sync_neo4j_op(lambda: get_neo4j_session().execute_write(_tx_logic))


async def query_memory_logic(query: MemoryQuery) -> List[Dict[str, Any]]:
    if not neo4j_driver or not embedder:
        raise ConnectionError("Neo4j/Embedder not ready.")
    cache_key = None
    if cache_client and CACHE_ENABLED:
        key_parts = [
            query.group_id,
            query.query,
            query.agent_id or "none",
            query.conversation_id or "none",
            str(query.max_results),
            str(query.similarity_threshold),
        ]
        cache_key = f"query_memory:{hashlib.md5(':'.join(key_parts).encode()).hexdigest()}"
        cached = await cache_client.get(cache_key)
        if cached:
            logger.info(f"Cache hit for query (group: {query.group_id})")
            return json.loads(cached)
    query_embedding = (await asyncio.to_thread(embedder.encode, query.query)).tolist()

    def _tx(tx):
        index_name = f"{VECTOR_INDEX_NAME}_episode"
        cypher = (
            "CALL db.index.vector.queryNodes($index_name, $top_k, $embedding) YIELD node AS m, score "
            "WHERE score >= $similarity_threshold AND m.group_id = $group_id AND m:Episode "
            "WITH m, score WHERE (m.content CONTAINS $query_text_regex OR score > ($similarity_threshold - 0.05)) "
        )
        if query.agent_id:
            cypher += "AND EXISTS {MATCH (m)-[:ASSOCIATED_WITH_AGENT]->(a:Agent {id: $agent_id, group_id: $group_id})} "
        if query.conversation_id:
            cypher += "AND EXISTS {MATCH (m)-[:PART_OF_CONVERSATION]->(c:Conversation {id: $conversation_id, group_id: $group_id})} "
        cypher += "RETURN m, score ORDER BY score DESC, m.timestamp DESC LIMIT $final_limit"
        params = {
            "index_name": index_name,
            "embedding": query_embedding,
            "top_k": query.max_results * 5,
            "similarity_threshold": query.similarity_threshold,
            "group_id": query.group_id,
            "query_text_regex": f"(?i).*{query.query}.*",
            "agent_id": query.agent_id,
            "conversation_id": query.conversation_id,
            "final_limit": query.max_results,
        }
        result = tx.run(cypher, params)
        return [{"m": record["m"], "score": record["score"]} for record in result]

    records = await run_sync_neo4j_op(lambda: get_neo4j_session().execute_read(_tx))
    results = []
    for record in records:
        node_data = dict(record["m"])
        score = record["score"]
        if "timestamp" in node_data and hasattr(node_data["timestamp"], "isoformat"):
            node_data["timestamp"] = node_data["timestamp"].isoformat()
        if "metadata" in node_data and isinstance(node_data["metadata"], str):
            try:
                node_data["metadata"] = json.loads(node_data["metadata"])
            except Exception:
                pass
        results.append({**node_data, "score": score if score is not None else 0.0})
    results.sort(key=lambda x: (x.get("score", 0.0), x.get("timestamp", "")), reverse=True)
    final_results = results[: query.max_results]
    if cache_client and CACHE_ENABLED and cache_key:
        await cache_client.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(final_results))
    return final_results


async def get_agent_memories_logic(agent_id: str, group_id: str) -> List[Dict[str, Any]]:
    if not neo4j_driver:
        raise ConnectionError("Neo4j driver not initialized.")

    def _tx(tx):
        query = (
            "MATCH (ag:Agent {id: $agent_id, group_id: $group_id})<-[:ASSOCIATED_WITH_AGENT]-(m) "
            "WHERE m.group_id = $group_id RETURN m ORDER BY m.timestamp DESC"
        )
        result = tx.run(query, agent_id=agent_id, group_id=group_id)
        return [{"m": record["m"]} for record in result]

    records = await run_sync_neo4j_op(lambda: get_neo4j_session().execute_read(_tx))
    results = []
    for record in records:
        node_data = dict(record["m"])
        if "timestamp" in node_data and hasattr(node_data["timestamp"], "isoformat"):
            node_data["timestamp"] = node_data["timestamp"].isoformat()
        if "metadata" in node_data and isinstance(node_data["metadata"], str):
            try:
                node_data["metadata"] = json.loads(node_data["metadata"])
            except Exception:
                pass
        results.append(node_data)
    return results


async def delete_memory_logic(memory_id: str, group_id: str) -> Dict[str, Any]:
    if not neo4j_driver:
        raise ConnectionError("Neo4j driver not initialized.")

    def _tx(tx):
        result = tx.run(
            "MATCH (m {id: $id, group_id: $group_id}) DETACH DELETE m RETURN count(m) as deleted_count",
            id=memory_id,
            group_id=group_id,
        )
        return result.single()["deleted_count"]

    deleted_count = await run_sync_neo4j_op(lambda: get_neo4j_session().execute_write(_tx))
    if deleted_count > 0:
        return {"status": "success", "deleted_count": deleted_count}
    raise ValueError(f"Memory {memory_id} not found in group {group_id} or already deleted.")


async def clear_graph_logic(group_id: str) -> Dict[str, Any]:
    if not neo4j_driver:
        raise ConnectionError("Neo4j driver not initialized.")

    def _tx(tx):
        result = tx.run(
            "MATCH (n {group_id: $group_id}) DETACH DELETE n RETURN count(n) as deleted_count",
            group_id=group_id,
        )
        return result.single()["deleted_count"]

    deleted_count = await run_sync_neo4j_op(lambda: get_neo4j_session().execute_write(_tx))
    return {"status": "success", "nodes_deleted": deleted_count}


# --- API Endpoints ---
@app.get("/mcp/tools")
async def get_tools() -> List[MCPToolDefinition]:
    """Return available memory management tools."""
    return [
        MCPToolDefinition(
            name="store_memory",
            description="Store a memory item. Extracts entities from episodes.",
            parameters=MemoryItem.schema(),
        ),
        MCPToolDefinition(
            name="query_memory",
            description="Query memories using text/vector search and graph context.",
            parameters=MemoryQuery.schema(),
        ),
        MCPToolDefinition(
            name="get_agent_memories",
            description="Get memories for an agent (scoped by group_id).",
            parameters={
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string"},
                    "group_id": {"type": "string"},
                },
                "required": ["agent_id", "group_id"],
            },
        ),
        MCPToolDefinition(
            name="delete_memory",
            description="Delete a memory item by ID and group_id.",
            parameters=DeleteMemoryArgs.schema(),
        ),
        MCPToolDefinition(
            name="clear_graph",
            description="Clear all data for a group_id.",
            parameters=ClearGraphArgs.schema(),
        ),
    ]


@app.post("/mcp/store_memory")
async def store_memory(memory: MemoryItem) -> Dict[str, Any]:
    """Store a memory item in Neo4j and extract entities if applicable."""
    try:
        return await store_memory_logic(memory)
    except Exception as e:
        logger.error(f"Error storing memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/query_memory")
async def query_memory(query: MemoryQuery) -> List[Dict[str, Any]]:
    """Query memories using hybrid semantic+graph search."""
    try:
        return await query_memory_logic(query)
    except Exception as e:
        logger.error(f"Error querying memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/agent_memories/{agent_id}/{group_id}")
async def get_agent_memories(agent_id: str, group_id: str) -> List[Dict[str, Any]]:
    """Get all memories for a specific agent and group."""
    try:
        return await get_agent_memories_logic(agent_id, group_id)
    except Exception as e:
        logger.error(f"Error getting agent memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/delete_memory")
async def delete_memory(args: DeleteMemoryArgs) -> Dict[str, Any]:
    """Delete a memory item by ID and group_id."""
    try:
        return await delete_memory_logic(args.memory_id, args.group_id)
    except Exception as e:
        logger.error(f"Error deleting memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/clear_graph")
async def clear_graph(args: ClearGraphArgs) -> Dict[str, Any]:
    """Clear all data for a group_id."""
    try:
        return await clear_graph_logic(args.group_id)
    except Exception as e:
        logger.error(f"Error clearing graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    status = {
        "status": "healthy",
        "service": "memory-mcp",
        "backends": {
            "neo4j": neo4j_driver is not None,
            "embedder": embedder is not None,
            "llm": llm_client is not None,
            "cache": cache_client is not None if CACHE_ENABLED else True,
        },
    }
    all_healthy = all(status["backends"].values())
    status["status"] = "healthy" if all_healthy else "degraded"
    return status


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
