"""
MongoDB-based memory manager for AI agents.
Replaces Firestore with MongoDB Atlas.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

logger = logging.getLogger(__name__)


class MongoDBMemoryManager:
    """Memory manager using MongoDB Atlas instead of Firestore."""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        database_name: str = "orchestra_memory",
    ):
        """
        Initialize MongoDB memory manager.

        Args:
            connection_string: MongoDB connection string (defaults to env var MONGODB_URI)
            database_name: Name of the database to use
        """
        self.connection_string = connection_string or os.getenv("MONGODB_URI")
        if not self.connection_string:
            raise ValueError("MongoDB connection string not provided")

        self.database_name = database_name
        self._client = None
        self._db = None

    @property
    def client(self) -> MongoClient:
        """Get or create MongoDB client."""
        if self._client is None:
            try:
                self._client = MongoClient(self.connection_string)
                # Test connection
                self._client.admin.command("ping")
                logger.info("Connected to MongoDB Atlas")
            except ConnectionFailure as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise
        return self._client

    @property
    def db(self):
        """Get database instance."""
        if self._db is None:
            self._db = self.client[self.database_name]
        return self._db

    def store_memory(self, agent_id: str, memory_type: str, content: Dict[str, Any]) -> str:
        """
        Store a memory entry.

        Args:
            agent_id: ID of the agent
            memory_type: Type of memory (short_term, long_term, episodic, etc.)
            content: Memory content

        Returns:
            ID of the stored memory
        """
        collection = self.db[f"{agent_id}_{memory_type}"]

        # Add metadata
        memory_doc = {
            **content,
            "timestamp": datetime.now(timezone.utc),
            "agent_id": agent_id,
            "memory_type": memory_type,
        }

        result = collection.insert_one(memory_doc)
        return str(result.inserted_id)

    def retrieve_memories(
        self,
        agent_id: str,
        memory_type: str,
        query: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        sort_by: str = "timestamp",
        ascending: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories for an agent.

        Args:
            agent_id: ID of the agent
            memory_type: Type of memory
            query: MongoDB query filter
            limit: Maximum number of results
            sort_by: Field to sort by
            ascending: Sort order

        Returns:
            List of memory documents
        """
        collection = self.db[f"{agent_id}_{memory_type}"]

        # Build query
        filter_query = query or {}
        filter_query["agent_id"] = agent_id

        # Execute query
        sort_order = ASCENDING if ascending else DESCENDING
        cursor = collection.find(filter_query).sort(sort_by, sort_order).limit(limit)

        # Convert ObjectId to string for JSON serialization
        memories = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            memories.append(doc)

        return memories

    def update_memory(self, agent_id: str, memory_type: str, memory_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a memory entry.

        Args:
            agent_id: ID of the agent
            memory_type: Type of memory
            memory_id: ID of the memory to update
            updates: Fields to update

        Returns:
            True if successful
        """
        from bson import ObjectId

        collection = self.db[f"{agent_id}_{memory_type}"]

        # Add update timestamp
        updates["last_updated"] = datetime.now(timezone.utc)

        result = collection.update_one({"_id": ObjectId(memory_id), "agent_id": agent_id}, {"$set": updates})

        return result.modified_count > 0

    def delete_memory(self, agent_id: str, memory_type: str, memory_id: str) -> bool:
        """
        Delete a memory entry.

        Args:
            agent_id: ID of the agent
            memory_type: Type of memory
            memory_id: ID of the memory to delete

        Returns:
            True if successful
        """
        from bson import ObjectId

        collection = self.db[f"{agent_id}_{memory_type}"]

        result = collection.delete_one({"_id": ObjectId(memory_id), "agent_id": agent_id})

        return result.deleted_count > 0

    def search_memories(
        self, agent_id: str, memory_type: str, text_query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search memories using text search.

        Args:
            agent_id: ID of the agent
            memory_type: Type of memory
            text_query: Text to search for
            limit: Maximum number of results

        Returns:
            List of matching memories
        """
        collection = self.db[f"{agent_id}_{memory_type}"]

        # Create text index if it doesn't exist
        try:
            collection.create_index([("content", "text")])
        except OperationFailure:
            pass  # Index already exists

        # Perform text search
        cursor = collection.find({"$text": {"$search": text_query}, "agent_id": agent_id}).limit(limit)

        # Convert results
        memories = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            memories.append(doc)

        return memories

    def get_memory_stats(self, agent_id: str) -> Dict[str, Any]:
        """
        Get statistics about an agent's memories.

        Args:
            agent_id: ID of the agent

        Returns:
            Dictionary with memory statistics
        """
        stats = {}

        # Get all collections for this agent
        collection_names = [name for name in self.db.list_collection_names() if name.startswith(f"{agent_id}_")]

        for collection_name in collection_names:
            memory_type = collection_name.replace(f"{agent_id}_", "")
            collection = self.db[collection_name]

            stats[memory_type] = {
                "count": collection.count_documents({"agent_id": agent_id}),
                "oldest": None,
                "newest": None,
            }

            # Get oldest and newest
            oldest = collection.find_one({"agent_id": agent_id}, sort=[("timestamp", ASCENDING)])
            newest = collection.find_one({"agent_id": agent_id}, sort=[("timestamp", DESCENDING)])

            if oldest:
                stats[memory_type]["oldest"] = oldest.get("timestamp")
            if newest:
                stats[memory_type]["newest"] = newest.get("timestamp")

        return stats

    def clear_agent_memories(self, agent_id: str, memory_type: Optional[str] = None) -> int:
        """
        Clear all memories for an agent.

        Args:
            agent_id: ID of the agent
            memory_type: Optional specific memory type to clear

        Returns:
            Number of memories deleted
        """
        total_deleted = 0

        if memory_type:
            # Clear specific memory type
            collection = self.db[f"{agent_id}_{memory_type}"]
            result = collection.delete_many({"agent_id": agent_id})
            total_deleted = result.deleted_count
        else:
            # Clear all memory types
            collection_names = [name for name in self.db.list_collection_names() if name.startswith(f"{agent_id}_")]

            for collection_name in collection_names:
                collection = self.db[collection_name]
                result = collection.delete_many({"agent_id": agent_id})
                total_deleted += result.deleted_count

        return total_deleted

    def close(self):
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
