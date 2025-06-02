"""
Unified database interface for Orchestra AI.

Provides a single interface for both PostgreSQL (structured data) and
Weaviate (vector/semantic data) operations.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from functools import lru_cache
import json
from uuid import UUID

from .postgresql_client import PostgreSQLClient
from .weaviate_client import WeaviateClient

logger = logging.getLogger(__name__)


class UnifiedDatabase:
    """Unified interface for all database operations."""

    def __init__(
        self, postgres_config: Optional[Dict[str, Any]] = None, weaviate_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize unified database with both clients."""
        # Initialize PostgreSQL
        pg_config = postgres_config or {}
        self.postgres = PostgreSQLClient(**pg_config)

        # Initialize Weaviate
        wv_config = weaviate_config or {}
        self.weaviate = WeaviateClient(**wv_config)

        # In-memory cache for frequently accessed data
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes default TTL

        logger.info("Unified database interface initialized")

    # ==================== Agent Operations ====================

    def create_agent(
        self,
        name: str,
        description: str,
        capabilities: Dict[str, Any],
        autonomy_level: int = 1,
        model_config: Optional[Dict[str, Any]] = None,
        initial_memory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an agent with both structured data and initial memory."""
        # Create agent in PostgreSQL
        agent_data = {
            "name": name,
            "description": description,
            "capabilities": capabilities,
            "autonomy_level": autonomy_level,
            "model_config": model_config or {},
        }
        agent = self.postgres.create_agent(agent_data)

        # Store initial memory in Weaviate if provided
        if initial_memory and agent:
            self.weaviate.store_memory(
                agent_id=str(agent["id"]),
                content=initial_memory,
                memory_type="initialization",
                context=f"Agent {name} created",
                importance=1.0,
            )

        # Create audit log
        self.postgres.create_audit_log(
            event_type="agent_created",
            actor="system",
            resource_type="agent",
            resource_id=str(agent["id"]),
            details={"name": name},
        )

        return agent

    def get_agent_with_memory(self, agent_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get agent with recent memories."""
        agent = self.postgres.get_agent(agent_id)
        if not agent:
            return None

        # Get recent memories from Weaviate
        memories = self.weaviate.get_recent_memories(str(agent_id), limit=10)
        agent["recent_memories"] = memories

        return agent

    def update_agent_and_log(
        self, agent_id: Union[str, UUID], updates: Dict[str, Any], actor: str = "system"
    ) -> Optional[Dict[str, Any]]:
        """Update agent and create audit log."""
        agent = self.postgres.update_agent(agent_id, updates)

        if agent:
            self.postgres.create_audit_log(
                event_type="agent_updated",
                actor=actor,
                resource_type="agent",
                resource_id=str(agent_id),
                details={"updates": updates},
            )

        return agent

    def delete_agent_complete(self, agent_id: Union[str, UUID], actor: str = "system") -> bool:
        """Delete agent and all associated data."""
        # Delete from PostgreSQL
        deleted = self.postgres.delete_agent(agent_id)

        if deleted:
            # Delete memories from Weaviate (would need to implement batch delete by agent_id)
            # For now, log the deletion
            self.postgres.create_audit_log(
                event_type="agent_deleted",
                actor=actor,
                resource_type="agent",
                resource_id=str(agent_id),
                details={"cleanup_required": "weaviate_memories"},
            )

        return deleted

    # ==================== Memory Operations ====================

    def store_agent_interaction(
        self,
        agent_id: str,
        user_input: str,
        agent_response: str,
        session_id: str,
        user_id: str = "anonymous",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Store a complete interaction including memory and conversation."""
        # Store user message in conversation
        self.weaviate.store_conversation(
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            message=user_input,
            role="user",
            metadata=metadata,
        )

        # Store agent response in conversation
        self.weaviate.store_conversation(
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            message=agent_response,
            role="assistant",
            metadata=metadata,
        )

        # Store in agent's memory
        memory_id = self.weaviate.store_memory(
            agent_id=agent_id,
            content=f"User: {user_input}\nAssistant: {agent_response}",
            memory_type="interaction",
            context=f"Session: {session_id}",
            importance=0.8,
            metadata={"session_id": session_id, "user_id": user_id},
        )

        # Create audit log
        self.postgres.create_audit_log(
            event_type="interaction_stored",
            actor=agent_id,
            resource_type="conversation",
            resource_id=session_id,
            details={"memory_id": memory_id},
        )

        return {"session_id": session_id, "memory_id": memory_id, "timestamp": datetime.utcnow().isoformat()}

    def search_agent_context(
        self,
        agent_id: str,
        query: str,
        include_conversations: bool = True,
        include_memories: bool = True,
        limit: int = 20,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Search all agent context including memories and conversations."""
        results = {}

        if include_memories:
            results["memories"] = self.weaviate.search_memories(
                agent_id=agent_id, query=query, limit=limit // 2 if include_conversations else limit
            )

        if include_conversations:
            results["conversations"] = self.weaviate.search_conversations(
                query=query, agent_id=agent_id, limit=limit // 2 if include_memories else limit
            )

        return results

    # ==================== Workflow Operations ====================

    def create_workflow_with_context(
        self, name: str, definition: Dict[str, Any], related_documents: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Create workflow and store related documents."""
        # Create workflow in PostgreSQL
        workflow = self.postgres.create_workflow({"name": name, "definition": definition, "status": "draft"})

        # Store related documents in Weaviate
        if related_documents and workflow:
            for doc in related_documents:
                self.weaviate.store_document(
                    title=doc.get("title", f"{name} - Document"),
                    content=doc.get("content", ""),
                    source=f"workflow:{workflow['id']}",
                    doc_type="workflow_doc",
                    metadata={"workflow_id": str(workflow["id"])},
                )

        return workflow

    def get_workflow_with_documents(self, workflow_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get workflow with related documents."""
        workflow = self.postgres.get_workflow(workflow_id)
        if not workflow:
            return None

        # Get related documents from Weaviate
        documents = self.weaviate.search_documents(
            query="", source=f"workflow:{workflow_id}", limit=50  # Empty query to get all
        )
        workflow["documents"] = documents

        return workflow

    # ==================== Knowledge Base Operations ====================

    def add_to_knowledge_base(
        self,
        title: str,
        content: str,
        category: str,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add item to knowledge base."""
        knowledge_id = self.weaviate.store_knowledge(
            title=title, content=content, source=source or "manual", category=category, tags=tags, metadata=metadata
        )

        # Log the addition
        self.postgres.create_audit_log(
            event_type="knowledge_added",
            actor="system",
            resource_type="knowledge",
            resource_id=knowledge_id,
            details={"title": title, "category": category},
        )

        return knowledge_id

    def search_knowledge(
        self, query: str, category: Optional[str] = None, tags: Optional[List[str]] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search knowledge base."""
        return self.weaviate.search_knowledge(query=query, category=category, tags=tags, limit=limit)

    # ==================== Session Management ====================

    def create_session(
        self, session_id: str, user_id: str, agent_id: Optional[str] = None, ttl_hours: int = 24
    ) -> Dict[str, Any]:
        """Create a new session."""
        session_data = {
            "user_id": user_id,
            "agent_id": agent_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
        }

        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

        return self.postgres.create_session(session_id, session_data, expires_at)

    def get_session_with_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session with conversation history."""
        session = self.postgres.get_session(session_id)
        if not session:
            return None

        # Get conversation history from Weaviate
        history = self.weaviate.get_conversation_history(session_id)
        session["conversation_history"] = history

        return session

    def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity timestamp."""
        session = self.postgres.get_session(session_id)
        if not session:
            return False

        session_data = json.loads(session["data"]) if isinstance(session["data"], str) else session["data"]
        session_data["last_activity"] = datetime.utcnow().isoformat()

        updated = self.postgres.create_session(session_id, session_data, session["expires_at"])

        return updated is not None

    # ==================== Analytics & Reporting ====================

    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "postgresql": {
                "agents": len(self.postgres.list_agents(limit=1000)),
                "workflows": len(self.postgres.list_workflows(limit=1000)),
                "active_sessions": len(
                    [
                        s
                        for s in self.postgres.execute_query(
                            "SELECT id FROM orchestra.sessions WHERE expires_at > CURRENT_TIMESTAMP"
                        )
                    ]
                ),
                "health": self.postgres.health_check(),
            },
            "weaviate": self.weaviate.get_stats(),
            "weaviate_health": self.weaviate.health_check(),
        }

        return stats

    def get_agent_activity_report(self, agent_id: str, days: int = 7) -> Dict[str, Any]:
        """Get agent activity report."""
        # Get agent info
        agent = self.postgres.get_agent(agent_id)
        if not agent:
            return {"error": "Agent not found"}

        # Get recent memories count
        memories = self.weaviate.get_recent_memories(agent_id, limit=100)

        # Get audit logs
        audit_logs = self.postgres.get_audit_logs(resource_type="agent", limit=100)
        agent_logs = [log for log in audit_logs if log.get("resource_id") == str(agent_id)]

        return {
            "agent": agent,
            "memory_count": len(memories),
            "recent_memories": memories[:10],
            "audit_events": len(agent_logs),
            "recent_events": agent_logs[:10],
        }

    # ==================== Utility Methods ====================

    @lru_cache(maxsize=128)
    def cached_get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Cached agent retrieval for performance."""
        return self.postgres.get_agent(agent_id)

    def clear_cache(self) -> None:
        """Clear all caches."""
        self.cached_get_agent.cache_clear()
        self._cache.clear()

    def health_check(self) -> Dict[str, bool]:
        """Check health of both databases."""
        return {
            "postgresql": self.postgres.health_check(),
            "weaviate": self.weaviate.health_check(),
            "overall": self.postgres.health_check() and self.weaviate.health_check(),
        }

    def close(self) -> None:
        """Close all database connections."""
        self.postgres.close()
        # Weaviate client doesn't need explicit closing
        logger.info("Database connections closed")
