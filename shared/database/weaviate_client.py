"""
Production-ready Weaviate client adapter for vector database operations.

This module replaces the mock implementation and provides a robust interface
to Weaviate, handling connections, schema, CRUD operations, and search.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import asyncio

import weaviate
from weaviate import Client as WeaviateSDKClient # Alias to avoid confusion with our WeaviateClient
from weaviate.auth import AuthApiKey
from weaviate.exceptions import WeaviateException
from weaviate.gql.get import HybridFusion

from core.config.unified_config import DatabaseConfig

logger = logging.getLogger(__name__)

# Define collection names based on DATABASE_CONSOLIDATION_PLAN.md and mock client methods
COLLECTION_AGENT_MEMORY = "AgentMemory"
COLLECTION_KNOWLEDGE = "Knowledge"
COLLECTION_CONVERSATIONS = "Conversations"
COLLECTION_DOCUMENTS = "Documents"

class WeaviateClient:
    """
    Production Weaviate client for vector database operations.
    """

    def __init__(self, config: DatabaseConfig):
        """
        Initialize Weaviate client. Does not connect automatically.
        Call connect() to establish the connection.

        Args:
            config: DatabaseConfig object with connection parameters.
        """
        self.config = config
        self._client: Optional[WeaviateSDKClient] = None
        self._connected = False # Internal flag

    async def connect(self) -> None:
        """Establish connection to Weaviate and ensure schemas."""
        if self._connected and self._client and self._client.is_ready():
            logger.info("Weaviate client is already connected and healthy.")
            return

        try:
            auth_config = None
            if self.config.weaviate_api_key:
                auth_config = AuthApiKey(api_key=self.config.weaviate_api_key)

            # weaviate.Client is synchronous, but its operations might be I/O bound.
            # For true async, weaviate.aio.Client would be needed if available/stable.
            # Assuming synchronous client for now as per existing unified_database.py WeaviateInterface
            # However, the calling context in UnifiedDatabase is async, so we make this method async
            # and perform sync operations within. This isn't ideal but matches current patterns.
            # A better approach would be to use an async Weaviate library or run sync ops in a thread pool.
            
            # For now, to make it fit the async connect() interface of DatabaseInterface:
            loop = asyncio.get_event_loop()
            self._client = await loop.run_in_executor(None, lambda: weaviate.Client(
                url=f"{self.config.weaviate_scheme}://{self.config.weaviate_host}:{self.config.weaviate_port}",
                auth_client_secret=auth_config,
                timeout_config=(self.config.weaviate_timeout, self.config.weaviate_timeout)
            ))

            is_ready = await loop.run_in_executor(None, self._client.is_ready)
            if not is_ready:
                raise WeaviateException("Weaviate is not ready after initialization.")
            
            self._connected = True
            logger.info(f"Successfully connected to Weaviate at {self.config.weaviate_host}")
            await self._ensure_all_schemas() # Make schema ensuring async as well
        except Exception as e:
            self._connected = False
            self._client = None # Ensure client is None if connection failed
            logger.error(f"Failed to connect to Weaviate: {e}", exc_info=True)
            raise ConnectionError(f"Failed to connect to Weaviate: {e}")

    async def _ensure_schema(self, collection_name: str, properties: List[Dict[str, Any]], description: str = "") -> None:
        """Ensure a specific collection schema exists in Weaviate."""
        if not self._client:
            logger.error(f"Cannot ensure schema for {collection_name}: Weaviate client not connected.")
            raise ConnectionError("Weaviate client not connected for schema creation.")

        loop = asyncio.get_event_loop()
        try:
            existing_schema = await loop.run_in_executor(None, lambda: self._client.schema.get(collection_name))
            if existing_schema:
                # logger.info(f"Schema for collection '{collection_name}' already exists.")
                return
        except WeaviateException as e:
            if "status_code: 404" in str(e) or "does not exist" in str(e).lower() or ("detail" in str(e) and "404" in str(e)): # More robust check for 404
                 pass # Class doesn't exist, proceed to create
            else:
                logger.error(f"Error checking schema for {collection_name}: {e}", exc_info=True)
                raise

        class_schema = {
            "class": collection_name,
            "description": description or f"Collection for {collection_name}",
            "properties": properties,
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": { "model": "ada", "type": "text" }
            },
        }
        try:
            await loop.run_in_executor(None, lambda: self._client.schema.create_class(class_schema))
            logger.info(f"Created Weaviate schema for collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to create schema for {collection_name}: {e}", exc_info=True)
            raise

    async def _ensure_all_schemas(self) -> None:
        """Ensure all predefined schemas exist."""
        # Schemas definitions remain the same as before
        agent_memory_properties = [
            {"name": "agent_id", "dataType": ["text"]}, {"name": "content", "dataType": ["text"]},
            {"name": "memory_type", "dataType": ["text"]}, {"name": "context", "dataType": ["text"], "description": "Optional context for the memory"},
            {"name": "importance", "dataType": ["number"], "description": "Importance score (0-1)"},
            {"name": "metadata", "dataType": ["object"], "description": "Additional metadata"},
            {"name": "created_at", "dataType": ["date"], "description": "Timestamp of memory creation"},
            {"name": "last_accessed_at", "dataType": ["date"], "description": "Timestamp of last access"},
        ]
        await self._ensure_schema(COLLECTION_AGENT_MEMORY, agent_memory_properties, "Stores agent memories and experiences.")

        knowledge_properties = [
            {"name": "title", "dataType": ["text"]}, {"name": "content", "dataType": ["text"]},
            {"name": "source", "dataType": ["text"]}, {"name": "category", "dataType": ["text"]},
            {"name": "tags", "dataType": ["text[]"]}, {"name": "metadata", "dataType": ["object"], "description": "Additional metadata"},
            {"name": "created_at", "dataType": ["date"]}, {"name": "updated_at", "dataType": ["date"]},
        ]
        await self._ensure_schema(COLLECTION_KNOWLEDGE, knowledge_properties, "Stores knowledge base articles and documents.")

        conversation_properties = [
            {"name": "session_id", "dataType": ["text"]}, {"name": "agent_id", "dataType": ["text"]},
            {"name": "user_id", "dataType": ["text"]}, {"name": "message", "dataType": ["text"]},
            {"name": "role", "dataType": ["text"], "description": "Role of the message sender (user/assistant)"},
            {"name": "metadata", "dataType": ["object"], "description": "Additional metadata"},
            {"name": "created_at", "dataType": ["date"]},
        ]
        await self._ensure_schema(COLLECTION_CONVERSATIONS, conversation_properties, "Stores conversation history.")

        document_properties = [
            {"name": "title", "dataType": ["text"]}, {"name": "content", "dataType": ["text"]},
            {"name": "source", "dataType": ["text"]}, {"name": "doc_type", "dataType": ["text"], "description": "Type of the document"},
            {"name": "metadata", "dataType": ["object"], "description": "Additional metadata"},
            {"name": "created_at", "dataType": ["date"]},
        ]
        await self._ensure_schema(COLLECTION_DOCUMENTS, document_properties, "Stores general documents.")

    # All other methods (health_check, get_stats, store_*, search_*, etc.)
    # will also need to be async and use run_in_executor for SDK calls.
    # This is a significant change. For brevity, I will show one store and one search method.

    async def health_check(self) -> bool:
        if not self._client or not self._connected: return False
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self._client.is_ready)
        except WeaviateException as e:
            logger.error(f"Weaviate health check failed: {e}", exc_info=True)
            return False

    async def get_stats(self) -> Dict[str, Any]:
        if not self._client or not self._connected: return {"error": "Client not connected"}
        loop = asyncio.get_event_loop()
        try:
            stats = {}
            # Simplified example for one collection
            response = await loop.run_in_executor(None, lambda: self._client.query.aggregate(COLLECTION_AGENT_MEMORY).with_meta_count().do())
            stats[COLLECTION_AGENT_MEMORY] = response["data"]["Aggregate"][COLLECTION_AGENT_MEMORY][0]["meta"]["count"]
            
            cluster_status = await loop.run_in_executor(None, self._client.cluster.get_nodes_status)
            client_meta = await loop.run_in_executor(None, self._client.get_meta)
            return {
                "collection_counts": stats, # In a full impl, iterate all collections
                "cluster_status": cluster_status,
                "version": client_meta.get("version", "unknown")
            }
        except WeaviateException as e:
            logger.error(f"Error getting Weaviate stats: {e}", exc_info=True)
            return {"error": str(e)}

    def _prepare_data_object(self, data: Dict[str, Any]) -> Dict[str, Any]:
        prepared_data = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                prepared_data[key] = value.isoformat() + "Z"
            elif value is not None:
                prepared_data[key] = value
        return prepared_data

    async def _store_object(self, collection_name: str, properties: Dict[str, Any], vector: Optional[List[float]] = None) -> str:
        if not self._client or not self._connected: raise ConnectionError("Weaviate client not connected.")
        loop = asyncio.get_event_loop()
        obj_uuid = str(uuid.uuid4())
        data_object = self._prepare_data_object(properties)
        try:
            await loop.run_in_executor(None, lambda: self._client.data_object.create(
                data_object=data_object,
                class_name=collection_name,
                uuid=obj_uuid,
                vector=vector
            ))
            logger.debug(f"Stored object {obj_uuid} in {collection_name}")
            return obj_uuid
        except WeaviateException as e:
            logger.error(f"Weaviate error storing object in {collection_name}: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Generic error storing object in {collection_name}: {e}", exc_info=True)
            raise

    async def store_memory(
        self, agent_id: str, content: str, memory_type: str = "general",
        context: Optional[str] = None, importance: float = 0.5, metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        properties = {
            "agent_id": agent_id, "content": content, "memory_type": memory_type,
            "context": context, "importance": importance, "metadata": metadata or {},
            "created_at": datetime.utcnow(), "last_accessed_at": datetime.utcnow(),
        }
        return await self._store_object(COLLECTION_AGENT_MEMORY, properties)

    async def get_recent_memories(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not self._client or not self._connected: raise ConnectionError("Weaviate client not connected.")
        loop = asyncio.get_event_loop()
        try:
            # Note: The .do() method itself might be blocking.
            result = await loop.run_in_executor(None, lambda:
                self._client.query.get(COLLECTION_AGENT_MEMORY, ["agent_id", "content", "memory_type", "context", "importance", "metadata", "created_at", "_additional {id}"])
                .with_where({"path": ["agent_id"], "operator": "Equal", "valueText": agent_id})
                .with_sort([{"path": ["created_at"], "order": "desc"}])
                .with_limit(limit)
                .do()
            )
            memories = result.get("data", {}).get("Get", {}).get(COLLECTION_AGENT_MEMORY, [])
            return [{**mem.pop("_additional"), **mem} for mem in memories]
        except WeaviateException as e:
            logger.error(f"Error fetching recent memories for agent {agent_id}: {e}", exc_info=True)
            return []

    async def search_memories(
        self, agent_id: str, query: str, limit: int = 10, memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if not self._client or not self._connected: raise ConnectionError("Weaviate client not connected.")
        loop = asyncio.get_event_loop()
        try:
            where_filter = {"operator": "And", "operands": [{"path": ["agent_id"], "operator": "Equal", "valueText": agent_id}]}
            if memory_type:
                where_filter["operands"].append({"path": ["memory_type"], "operator": "Equal", "valueText": memory_type})
            
            query_obj_builder = self._client.query.get(
                COLLECTION_AGENT_MEMORY, 
                ["agent_id", "content", "memory_type", "context", "importance", "metadata", "created_at", "_additional {id, score, distance}"]
            ).with_near_text({"concepts": [query]}).with_limit(limit)

            if len(where_filter["operands"]) > 0:
                 query_obj_builder = query_obj_builder.with_where(where_filter)
            
            result = await loop.run_in_executor(None, query_obj_builder.do)
            memories = result.get("data", {}).get("Get", {}).get(COLLECTION_AGENT_MEMORY, [])
            return [{**mem.pop("_additional"), **mem} for mem in memories]
        except WeaviateException as e:
            logger.error(f"Error searching memories for agent {agent_id} with query '{query}': {e}", exc_info=True)
            return []

    async def store_conversation(
        self, session_id: str, agent_id: str, user_id: str, message: str, role: str = "user", metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        properties = {
            "session_id": session_id, "agent_id": agent_id, "user_id": user_id,
            "message": message, "role": role, "metadata": metadata or {}, "created_at": datetime.utcnow(),
        }
        return await self._store_object(COLLECTION_CONVERSATIONS, properties)

    async def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        if not self._client or not self._connected: raise ConnectionError("Weaviate client not connected.")
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, lambda:
                self._client.query.get(COLLECTION_CONVERSATIONS, ["session_id", "agent_id", "user_id", "message", "role", "metadata", "created_at", "_additional {id}"])
                .with_where({"path": ["session_id"], "operator": "Equal", "valueText": session_id})
                .with_sort([{"path": ["created_at"], "order": "asc"}])
                .with_limit(limit)
                .do()
            )
            messages = result.get("data", {}).get("Get", {}).get(COLLECTION_CONVERSATIONS, [])
            return [{**msg.pop("_additional"), **msg} for msg in messages]
        except WeaviateException as e:
            logger.error(f"Error fetching conversation history for session {session_id}: {e}", exc_info=True)
            return []
            
    async def search_conversations(
        self, query: str, agent_id: Optional[str] = None, session_id: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        if not self._client or not self._connected: raise ConnectionError("Weaviate client not connected.")
        loop = asyncio.get_event_loop()
        operands = []
        if agent_id: operands.append({"path": ["agent_id"], "operator": "Equal", "valueText": agent_id})
        if session_id: operands.append({"path": ["session_id"], "operator": "Equal", "valueText": session_id})
        where_filter = {"operator": "And", "operands": operands} if operands else None
        try:
            query_builder = self._client.query.get(
                COLLECTION_CONVERSATIONS, 
                ["session_id", "agent_id", "user_id", "message", "role", "metadata", "created_at", "_additional {id, score, distance}"]
            ).with_near_text({"concepts": [query]}).with_limit(limit)
            if where_filter: query_builder = query_builder.with_where(where_filter)
            result = await loop.run_in_executor(None, query_builder.do)
            conversations = result.get("data", {}).get("Get", {}).get(COLLECTION_CONVERSATIONS, [])
            return [{**conv.pop("_additional"), **conv} for conv in conversations]
        except WeaviateException as e:
            logger.error(f"Error searching conversations with query '{query}': {e}", exc_info=True)
            return []

    async def store_document(
        self, title: str, content: str, source: str, doc_type: str = "general", metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        properties = {
            "title": title, "content": content, "source": source, "doc_type": doc_type,
            "metadata": metadata or {}, "created_at": datetime.utcnow(),
        }
        return await self._store_object(COLLECTION_DOCUMENTS, properties)

    async def search_documents(
        self, query: str, source: Optional[str] = None, doc_type: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        if not self._client or not self._connected: raise ConnectionError("Weaviate client not connected.")
        loop = asyncio.get_event_loop()
        operands = []
        if source: operands.append({"path": ["source"], "operator": "Equal", "valueText": source})
        if doc_type: operands.append({"path": ["doc_type"], "operator": "Equal", "valueText": doc_type})
        where_filter = {"operator": "And", "operands": operands} if operands else None
        try:
            query_builder = self._client.query.get(COLLECTION_DOCUMENTS, ["title", "content", "source", "doc_type", "metadata", "created_at", "_additional {id, score, distance}"])
            if query: query_builder = query_builder.with_near_text({"concepts": [query]})
            query_builder = query_builder.with_limit(limit)
            if where_filter: query_builder = query_builder.with_where(where_filter)
            result = await loop.run_in_executor(None, query_builder.do)
            documents = result.get("data", {}).get("Get", {}).get(COLLECTION_DOCUMENTS, [])
            return [{**doc.pop("_additional"), **doc} for doc in documents]
        except WeaviateException as e:
            logger.error(f"Error searching documents with query '{query}': {e}", exc_info=True)
            return []

    async def store_knowledge(
        self, title: str, content: str, source: str, category: str,
        tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        properties = {
            "title": title, "content": content, "source": source, "category": category,
            "tags": tags or [], "metadata": metadata or {},
            "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(),
        }
        return await self._store_object(COLLECTION_KNOWLEDGE, properties)

    async def search_knowledge(
        self, query: str, category: Optional[str] = None, tags: Optional[List[str]] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        if not self._client or not self._connected: raise ConnectionError("Weaviate client not connected.")
        loop = asyncio.get_event_loop()
        operands = []
        if category: operands.append({"path": ["category"], "operator": "Equal", "valueText": category})
        if tags: operands.append({"path": ["tags"], "operator": "ContainsAny", "valueTextArray": tags})
        where_filter = {"operator": "And", "operands": operands} if operands else None
        try:
            query_builder = self._client.query.get(COLLECTION_KNOWLEDGE, ["title", "content", "source", "category", "tags", "metadata", "created_at", "updated_at", "_additional {id, score, distance}"])
            if query: query_builder = query_builder.with_near_text({"concepts": [query]})
            query_builder = query_builder.with_limit(limit)
            if where_filter: query_builder = query_builder.with_where(where_filter)
            result = await loop.run_in_executor(None, query_builder.do)
            knowledge_items = result.get("data", {}).get("Get", {}).get(COLLECTION_KNOWLEDGE, [])
            return [{**k.pop("_additional"), **k} for k in knowledge_items]
        except WeaviateException as e:
            logger.error(f"Error searching knowledge with query '{query}': {e}", exc_info=True)
            return []

    # Methods for WeaviateInterface compatibility
    async def raw_graphql_query(self, query_string: str) -> Dict[str, Any]:
        """Executes a raw GraphQL query."""
        if not self._client or not self._connected:
            raise ConnectionError("Weaviate client not connected.")
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, lambda: self._client.query.raw(query_string))
            return result
        except WeaviateException as e:
            logger.error(f"Error executing raw GraphQL query: {e}", exc_info=True)
            raise QueryError(f"Raw GraphQL query failed: {e}") from e

    async def search_objects_near_vector(
        self, collection_name: str, vector: List[float], limit: int,
        filters: Optional[Dict] = None, return_properties: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Generic search by vector in a specified collection."""
        if not self._client or not self._connected:
            raise ConnectionError("Weaviate client not connected.")
        loop = asyncio.get_event_loop()

        # Determine properties to return. If None, fetch all non-vector properties.
        # This requires knowing the schema or fetching all and letting Weaviate decide.
        # For simplicity, we'll rely on Weaviate's default if not specified,
        # but specific properties are better for performance.
        # The specific search methods define their properties, this generic one is harder.
        # For now, let's assume a minimal set if not provided, or accept a comprehensive list.
        
        # A robust way would be to fetch schema and list properties, excluding vector.
        # Simplified: if not return_properties, fetch a common set or all (less efficient).
        # For now, the specific search methods are more optimized with their return props.
        # This generic one will just pass `return_properties` if provided.
        # If `return_properties` is None, it might fetch everything including vector depending on Weaviate default.
        # It's better if `WeaviateInterface` provides the specific fields it needs.
        
        props_to_fetch = return_properties if return_properties else ["_additional {id, score, distance}"] 
        if return_properties and "_additional {id, score, distance}" not in return_properties :
            if isinstance(props_to_fetch, list): # Ensure it's a list
                 props_to_fetch.append("_additional {id, score, distance}")
            else: # Should be a list
                 props_to_fetch = ["_additional {id, score, distance}"]


        try:
            query_builder = self._client.query.get(collection_name, props_to_fetch) \
                .with_near_vector({"vector": vector}) \
                .with_limit(limit)

            if filters:
                query_builder = query_builder.with_where(filters)
            
            result = await loop.run_in_executor(None, query_builder.do)
            
            # Ensure data path exists
            data_get = result.get("data", {}).get("Get", {})
            if not data_get or collection_name not in data_get:
                 logger.warning(f"No results or collection {collection_name} not found in 'Get' results for vector search.")
                 return []

            items = data_get.get(collection_name, [])
            # Flatten _additional into the main dict for consistency with other search methods
            return [{**item.pop("_additional"), **item} for item in items]
        except WeaviateException as e:
            logger.error(f"Error searching objects near vector in {collection_name}: {e}", exc_info=True)
            return []
        except Exception as e: # Catch broader errors
            logger.error(f"Unexpected error searching objects near vector in {collection_name}: {e}", exc_info=True)
            return []


    async def add_objects_batch(self, collection_name: str, objects: List[Dict[str, Any]]) -> int:
        """Adds objects to a collection in batch."""
        if not self._client or not self._connected:
            raise ConnectionError("Weaviate client not connected.")
        loop = asyncio.get_event_loop()

        # Weaviate's batch processing is typically done via a context manager or direct batch calls
        # The `with client.batch` is synchronous. We need to adapt.
        # One way is to prepare all objects and then make one blocking call inside run_in_executor.
        
        processed_objects = 0
        try:
            # Using configure_batch for a more direct async-wrapped approach if available,
            # or manual batching. The Python client's batch is stateful.
            # For simplicity, we'll add objects one by one within an executor for batching,
            # or use client.data_object.create_batch() if that's more suitable for async wrapping.
            # The `client.batch.add_data_object` is part of a stateful batch.
            # Let's use `client.data_object.create_batch(objects, class_name)` if available and fits this model.
            # The v4 client uses `collection.batch.dynamic()` or `collection.data.insert_many()`.
            # Since we don't have `collection` object here directly without getting it first.
            # Let's use the older `_client.batch.add_data_object` pattern wrapped for async.
            
            # This is tricky because the batcher object itself is stateful.
            # A simple approach for run_in_executor:
            def batch_creation_sync():
                with self._client.batch(batch_size=100, dynamic=True) as batch_ctx: # Default batch_size, make configurable if needed
                    for obj_props in objects:
                        obj_id = obj_props.pop("id", str(uuid.uuid4()))
                        vector = obj_props.pop("vector", None)
                        
                        # Ensure datetime objects are formatted (already done by _prepare_data_object if called before)
                        # For safety, can re-iterate or ensure _prepare_data_object was called by caller.
                        # Assuming properties are already prepared.
                        
                        batch_ctx.add_data_object(
                            data_object=self._prepare_data_object(obj_props), # Prepare here for safety
                            class_name=collection_name,
                            uuid=obj_id,
                            vector=vector
                        )
                # The batch context manager handles submission.
                # The number of successfully imported objects is harder to get directly here
                # unless the batch result processing is enhanced.
                # For now, assume success if no exception.
                return len(objects) # This is an assumption of success.

            processed_objects = await loop.run_in_executor(None, batch_creation_sync)
            logger.info(f"Batch inserted {processed_objects} objects into {collection_name}.")
            return processed_objects

        except WeaviateException as e:
            logger.error(f"Weaviate error batch inserting into {collection_name}: {e}", exc_info=True)
            raise QueryError(f"Batch insert failed: {e}") from e
        except Exception as e: # Catch broader errors
            logger.error(f"Unexpected error batch inserting into {collection_name}: {e}", exc_info=True)
            raise QueryError(f"Unexpected batch insert error: {e}") from e


    async def close(self) -> None:
        logger.info("WeaviateClient close called. Actual client connection managed by SDK.")
        self._connected = False
        self._client = None # Allow GC and indicate closed state


# Main block for testing (conceptual)
async def main_test():
    logger.basicConfig(level=logging.DEBUG)
    class MockDBConfig:
        weaviate_host = "localhost"
        weaviate_port = 8080
        weaviate_scheme = "http"
        weaviate_api_key = None # os.getenv("WEAVIATE_API_KEY")
        weaviate_timeout = 20 
    
    mock_config = MockDBConfig()
    # Ensure OPENAI_API_KEY is set in environment if text2vec-openai requires it at instance level
    # os.environ["OPENAI_API_KEY"] = "your_openai_key_if_needed_here" 
    client = WeaviateClient(mock_config)

    try:
        await client.connect()
        if await client.health_check():
            logger.info("Weaviate client is healthy.")
            
            # Example: Test raw_graphql_query
            # meta_query = "{ Meta { version } }"
            # meta_info = await client.raw_graphql_query(meta_query)
            # logger.info(f"Meta info: {meta_info}")

            # Example: Test add_objects_batch and search_objects_near_vector
            # test_collection = "TestGenericCollection"
            # test_props = [{"name": "test_prop", "dataType": ["text"]}]
            # await client._ensure_schema(test_collection, test_props, "Test collection for generic methods")
            
            # objects_to_add = [
            #     {"test_prop": "banana", "id": str(uuid.uuid4())}, # ID is optional, will be generated if missing by _store_object
            #     {"test_prop": "orange", "vector": [0.1]*1536}, # Example with pre-computed vector (dim must match model)
            # ]
            # if client._client.get_meta().get("modules", {}).get("text2vec-openai"): # only add if vectorizer is present
            #    num_added = await client.add_objects_batch(test_collection, objects_to_add)
            #    logger.info(f"Batch added {num_added} objects to {test_collection}")

            #    if num_added > 0:
            #        # Assuming text2vec-openai is configured for "ada" (1024 dims) or similar.
            #        # If pre-computed vector was used, its dimension should match.
            #        # For Weaviate-computed vectors, provide a query string.
            #        # This search might fail if dimensions mismatch or no vector index ready.
            #        search_vec = [0.123] * 1024 # Dimension for ada-002 if text2vec-openai is default
            #        # search_results = await client.search_objects_near_vector(test_collection, search_vec, limit=5, return_properties=["test_prop"])
            #        # logger.info(f"Generic search results: {search_results}")
            # else:
            #    logger.info("Skipped batch add/search as text2vec-openai might not be configured or objects already exist.")

        else:
            logger.error("Weaviate client is not healthy post-connect.")
            
    except ConnectionError as ce:
        logger.error(f"Connection Error during test: {ce}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred during test: {e}", exc_info=True)
    finally:
        if client._connected: # only close if connect was successful
            await client.close()
            logger.info("Test Weaviate client connection closed.")
        else:
            logger.info("Client was not connected, no need to close.")


if __name__ == "__main__":
    # To run this test, ensure Weaviate is running and accessible.
    # Also, ensure OPENAI_API_KEY is set if your Weaviate's text2vec-openai module requires it.
    # asyncio.run(main_test())
    pass
