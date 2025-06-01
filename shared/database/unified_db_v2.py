#!/usr/bin/env python3
"""
Unified Database Interface v2 for Orchestra AI.

This module provides a single, optimized interface for both PostgreSQL (structured data)
and Weaviate (vector/semantic data) operations, using the unified PostgreSQL client
to eliminate all duplication and maximize performance.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from uuid import UUID
import asyncio

from .unified_postgresql import get_unified_postgresql, UnifiedPostgreSQL
from .weaviate_client import WeaviateClient

logger = logging.getLogger(__name__)


class UnifiedDatabaseV2:
    """
    Unified interface for all database operations with zero duplication.
    Combines PostgreSQL and Weaviate through optimized, shared components.
    """
    
    def __init__(self, weaviate_config: Optional[Dict[str, Any]] = None):
        """Initialize unified database with integrated components."""
        self._postgres: Optional[UnifiedPostgreSQL] = None
        self._weaviate: Optional[WeaviateClient] = None
        self._weaviate_config = weaviate_config or {}
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize both database connections."""
        if self._initialized:
            return
            
        # Initialize PostgreSQL (uses shared connection pool)
        self._postgres = await get_unified_postgresql()
        
        # Initialize Weaviate
        self._weaviate = WeaviateClient(**self._weaviate_config)
        
        self._initialized = True
        logger.info("Unified Database v2 initialized with optimized components")
        
    async def close(self) -> None:
        """Close database connections gracefully."""
        # PostgreSQL cleanup is handled by the global instance
        # Weaviate client doesn't need explicit closing
        self._initialized = False
        logger.info("Unified Database v2 closed")
        
    def _ensure_initialized(self) -> None:
        """Ensure the database is initialized."""
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")
    
    # ==================== Agent Operations ====================
    
    async def create_agent(
        self,
        name: str,
        description: str,
        capabilities: Dict[str, Any],
        autonomy_level: int = 1,
        model_config: Optional[Dict[str, Any]] = None,
        initial_memory: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create an agent with both structured data and initial memory."""
        self._ensure_initialized()
        
        # Create agent in PostgreSQL
        agent_data = {
            "name": name,
            "description": description,
            "capabilities": capabilities,
            "autonomy_level": autonomy_level,
            "model_config": model_config or {},
            "metadata": metadata or {}
        }
        agent = await self._postgres.agent_create(agent_data)
        
        # Store initial memory in Weaviate if provided
        if initial_memory and agent:
            self._weaviate.store_memory(
                agent_id=agent["id"],
                content=initial_memory,
                memory_type="initialization",
                context=f"Agent {name} created",
                importance=1.0
            )
        
        # Create audit log
        await self._postgres.audit_log(
            event_type="agent_created",
            actor="system",
            resource_type="agent",
            resource_id=agent["id"],
            details={"name": name}
        )
        
        return agent
    
    async def get_agent_with_context(
        self, 
        agent_id: Union[str, UUID],
        include_memories: bool = True,
        include_sessions: bool = True,
        memory_limit: int = 10
    ) -> Optional[Dict[str, Any]]:
        """Get agent with full context including memories and active sessions."""
        self._ensure_initialized()
        
        agent = await self._postgres.agent_get(agent_id)
        if not agent:
            return None
        
        # Add recent memories from Weaviate
        if include_memories:
            agent["recent_memories"] = self._weaviate.get_recent_memories(
                agent["id"], 
                limit=memory_limit
            )
        
        # Add active sessions
        if include_sessions:
            sessions = await self._postgres.fetch_raw("""
                SELECT id, user_id, created_at, updated_at, expires_at
                FROM sessions.sessions
                WHERE agent_id = $1 AND is_active = true AND expires_at > CURRENT_TIMESTAMP
                ORDER BY updated_at DESC
                LIMIT 5
            """, agent["id"])
            agent["active_sessions"] = sessions
        
        return agent
    
    async def update_agent(
        self,
        agent_id: Union[str, UUID],
        updates: Dict[str, Any],
        actor: str = "system"
    ) -> Optional[Dict[str, Any]]:
        """Update agent and create audit log."""
        self._ensure_initialized()
        
        agent = await self._postgres.agent_update(agent_id, updates)
        
        if agent:
            await self._postgres.audit_log(
                event_type="agent_updated",
                actor=actor,
                resource_type="agent",
                resource_id=str(agent_id),
                details={"updates": updates}
            )
        
        return agent
    
    async def delete_agent(
        self, 
        agent_id: Union[str, UUID], 
        actor: str = "system",
        cleanup_vectors: bool = True
    ) -> bool:
        """Delete agent and all associated data."""
        self._ensure_initialized()
        
        # Delete from PostgreSQL
        deleted = await self._postgres.agent_delete(agent_id)
        
        if deleted:
            # Create audit log
            await self._postgres.audit_log(
                event_type="agent_deleted",
                actor=actor,
                resource_type="agent",
                resource_id=str(agent_id),
                details={"cleanup_vectors": cleanup_vectors}
            )
            
            # TODO: Implement batch delete in Weaviate by agent_id
            if cleanup_vectors:
                logger.warning(f"Vector cleanup for agent {agent_id} pending implementation")
        
        return deleted
    
    # ==================== Memory & Interaction Operations ====================
    
    async def store_interaction(
        self,
        session_id: str,
        agent_id: str,
        user_input: str,
        agent_response: str,
        user_id: str = "anonymous",
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.8
    ) -> Dict[str, Any]:
        """Store a complete interaction with optimized performance."""
        self._ensure_initialized()
        
        # Batch store conversation messages in Weaviate
        timestamp = datetime.utcnow()
        
        # Store user message
        self._weaviate.store_conversation(
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            message=user_input,
            role="user",
            metadata=metadata
        )
        
        # Store agent response
        self._weaviate.store_conversation(
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            message=agent_response,
            role="assistant",
            metadata=metadata
        )
        
        # Store in agent's memory with higher importance for learning
        memory_id = self._weaviate.store_memory(
            agent_id=agent_id,
            content=f"User: {user_input}\nAssistant: {agent_response}",
            memory_type="interaction",
            context=f"Session: {session_id}",
            importance=importance,
            metadata={
                "session_id": session_id,
                "user_id": user_id,
                "timestamp": timestamp.isoformat(),
                **(metadata or {}
        workflow = await self._postgres.workflow_create(workflow_data)
            }
        )
        
        # Update session activity
        await self._postgres.session_update(session_id, {
            "last_interaction": timestamp.isoformat(),
            "interaction_count": await self._get_interaction_count(session_id) + 1
        }
        workflow = await self._postgres.workflow_create(workflow_data)
        
        # Cache the interaction for quick retrieval
        cache_key = f"interaction:{session_id}:latest"
        await self._postgres.cache_set(
            cache_key,
            {
                "user_input": user_input,
                "agent_response": agent_response,
                "timestamp": timestamp.isoformat(),
                "memory_id": memory_id
            },
            ttl=3600,  # 1 hour cache
            tags=["interactions", f"session:{session_id}", f"agent:{agent_id}"]
        )
        
        return {
            "session_id": session_id,
            "memory_id": memory_id,
            "timestamp": timestamp.isoformat(),
            "cached": True
        }
    
    async def search_context(
        self,
        query: str,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        search_memories: bool = True,
        search_conversations: bool = True,
        search_knowledge: bool = True,
        limit: int = 20
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Unified context search across all data types."""
        self._ensure_initialized()
        
        results = {}
        
        # Parallel search across different data types
        tasks = []
        
        if search_memories and agent_id:
            tasks.append(('memories', self._search_memories(agent_id, query, limit)))
        
        if search_conversations:
            tasks.append(('conversations', self._search_conversations(
                query, agent_id, session_id, limit
            )))
        
        if search_knowledge:
            tasks.append(('knowledge', self._search_knowledge(query, limit)))
        
        # Execute searches in parallel
        if tasks:
            search_results = await asyncio.gather(
                *[task[1] for task in tasks],
                return_exceptions=True
            )
            
            for i, (name, _) in enumerate(tasks):
                if not isinstance(search_results[i], Exception):
                    results[name] = search_results[i]
                else:
                    logger.error(f"Search failed for {name}: {search_results[i]}")
                    results[name] = []
        
        return results
    
    async def _search_memories(self, agent_id: str, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search agent memories."""
        return self._weaviate.search_memories(
            agent_id=agent_id,
            query=query,
            limit=limit
        )
    
    async def _search_conversations(
        self, 
        query: str, 
        agent_id: Optional[str], 
        session_id: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search conversations."""
        return self._weaviate.search_conversations(
            query=query,
            agent_id=agent_id,
            session_id=session_id,
            limit=limit
        )
    
    async def _search_knowledge(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search knowledge base."""
        return self._weaviate.search_knowledge(query=query, limit=limit)
    
    async def _get_interaction_count(self, session_id: str) -> int:
        """Get interaction count for a session from cache or compute."""
        cache_key = f"stats:session:{session_id}:interactions"
        cached = await self._postgres.cache_get(cache_key)
        
        if cached:
            return cached.get("count", 0)
        
        # Compute from Weaviate if not cached
        count = len(self._weaviate.get_conversation_history(session_id, limit=1000))
        await self._postgres.cache_set(cache_key, {"count": count}, ttl=300)
        
        return count
    
    # ==================== Session Management ====================
    
    async def create_session(
        self,
        user_id: str,
        agent_id: Optional[str] = None,
        ttl_hours: int = 24,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new session with enhanced context."""
        self._ensure_initialized()
        
        session_data = {
            "context": initial_context or {},
            "created_at": datetime.utcnow().isoformat(),
            "interaction_count": 0
        }
        
        session_id = await self._postgres.session_create(
            user_id=user_id,
            agent_id=agent_id,
            data=session_data,
            ttl=ttl_hours * 3600,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"source": "unified_db_v2"}
        )
        
        # Cache session for quick access
        await self._postgres.cache_set(
            f"session:{session_id}",
            {
                "user_id": user_id,
                "agent_id": agent_id,
                "created_at": session_data["created_at"]
            },
            ttl=ttl_hours * 3600,
            tags=["sessions", f"user:{user_id}"]
        )
        
        return session_id
    
    async def get_session_with_history(
        self, 
        session_id: str,
        history_limit: int = 50
    ) -> Optional[Dict[str, Any]]:
        """Get session with conversation history."""
        self._ensure_initialized()
        
        # Try cache first
        cached = await self._postgres.cache_get(f"session:{session_id}:full")
        if cached:
            return cached
        
        # Get session from PostgreSQL
        session = await self._postgres.session_get(session_id)
        if not session:
            return None
        
        # Get conversation history from Weaviate
        history = self._weaviate.get_conversation_history(session_id, limit=history_limit)
        session["conversation_history"] = history
        
        # Cache the full session
        await self._postgres.cache_set(
            f"session:{session_id}:full",
            session,
            ttl=300,  # 5 minute cache
            tags=["sessions", f"session:{session_id}"]
        )
        
        return session
    
    # ==================== Workflow Operations ====================
    
    async def create_workflow(
        self,
        name: str,
        definition: Dict[str, Any],
        related_documents: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create workflow with related documents."""
        self._ensure_initialized()
        
        # Create workflow in PostgreSQL
        workflow_data = {
            "name": name,
            "definition": definition,
            "status": "draft",
            "metadata": metadata or {}
        }
        workflow = await self._postgres.workflow_create(workflow_data)
        
        # Store related documents in Weaviate
        if related_documents and workflow:
            for doc in related_documents:
                self._weaviate.store_document(
                    title=doc.get("title", f"{name} - Document"),
                    content=doc.get("content", ""),
                    source=f"workflow:{workflow['id']}",
                    doc_type="workflow_doc",
                    metadata={
                        "workflow_id": workflow["id"],
                        "workflow_name": name,
                        **(doc.get("metadata", {}
        workflow = await self._postgres.workflow_create(workflow_data))
                    }
                )
        
        # Cache workflow for quick access
        await self._postgres.cache_set(
            f"workflow:{workflow['id']}",
            workflow,
            ttl=3600,
            tags=["workflows", f"status:{workflow['status']}"]
        )
        
        return workflow
    
    async def get_workflow_with_documents(
        self, 
        workflow_id: Union[str, UUID]
    ) -> Optional[Dict[str, Any]]:
        """Get workflow with all related documents."""
        self._ensure_initialized()
        
        # Check cache first
        cache_key = f"workflow:{workflow_id}:full"
        cached = await self._postgres.cache_get(cache_key)
        if cached:
            return cached
        
        workflow = await self._postgres.workflow_get(workflow_id)
        if not workflow:
            return None
        
        # Get related documents from Weaviate
        documents = self._weaviate.search_documents(
            query="",  # Empty query to get all
            source=f"workflow:{workflow_id}",
            limit=100
        )
        workflow["documents"] = documents
        
        # Cache the complete workflow
        await self._postgres.cache_set(
            cache_key,
            workflow,
            ttl=600,  # 10 minute cache
            tags=["workflows", f"workflow:{workflow_id}"]
        )
        
        return workflow
    
    # ==================== Knowledge Base Operations ====================
    
    async def add_knowledge(
        self,
        title: str,
        content: str,
        category: str,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add item to knowledge base with caching."""
        self._ensure_initialized()
        
        knowledge_id = self._weaviate.store_knowledge(
            title=title,
            content=content,
            source=source or "manual",
            category=category,
            tags=tags,
            metadata=metadata
        )
        
        # Log the addition
        await self._postgres.audit_log(
            event_type="knowledge_added",
            actor="system",
            resource_type="knowledge",
            resource_id=knowledge_id,
            details={
                "title": title,
                "category": category,
                "tags": tags
            }
        )
        
        # Invalidate knowledge search cache
        await self._postgres.cache_clear(tags=["knowledge_search"])
        
        return knowledge_id
    
    async def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search knowledge base with caching."""
        self._ensure_initialized()
        
        # Create cache key from search parameters
        cache_key = f"knowledge:search:{hash((query, category, tuple(tags or []), limit))}"
        
        # Check cache
        cached = await self._postgres.cache_get(cache_key)
        if cached:
            return cached
        
        # Search Weaviate
        results = self._weaviate.search_knowledge(
            query=query,
            category=category,
            tags=tags,
            limit=limit
        )
        
        # Cache results
        await self._postgres.cache_set(
            cache_key,
            results,
            ttl=600,  # 10 minute cache
            tags=["knowledge_search"]
        )
        
        return results
    
    # ==================== Analytics & Monitoring ====================
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics."""
        self._ensure_initialized()
        
        # Get PostgreSQL metrics
        pg_health = await self._postgres.health_check()
        
        # Get Weaviate metrics
        wv_stats = self._weaviate.get_stats()
        wv_health = self._weaviate.health_check()
        
        # Get cache statistics
        cache_stats = await self._postgres.cache_stats()
        
        # Get session statistics
        session_stats = await self._postgres.fetch_raw("""
            SELECT 
                COUNT(*) FILTER (WHERE is_active = true AND expires_at > CURRENT_TIMESTAMP) as active_sessions,
                COUNT(*) FILTER (WHERE is_active = false) as inactive_sessions,
                COUNT(DISTINCT user_id) FILTER (WHERE is_active = true) as unique_users,
                COUNT(DISTINCT agent_id) FILTER (WHERE is_active = true AND agent_id IS NOT NULL) as active_agents
            FROM sessions.sessions
        """)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "postgresql": pg_health,
            "weaviate": {
                "stats": wv_stats,
                "health": wv_health
            },
            "cache": cache_stats,
            "sessions": session_stats[0] if session_stats else {},
            "status": "healthy" if pg_health["status"] == "healthy" and wv_health else "degraded"
        }
    
    async def get_agent_analytics(
        self,
        agent_id: Union[str, UUID],
        days: int = 7
    ) -> Dict[str, Any]:
        """Get detailed agent analytics."""
        self._ensure_initialized()
        
        agent = await self._postgres.agent_get(agent_id)
        if not agent:
            return {"error": "Agent not found"}
        
        # Get interaction statistics
        interaction_stats = await self._postgres.fetch_raw("""
            SELECT 
                COUNT(DISTINCT s.id) as total_sessions,
                COUNT(DISTINCT s.user_id) as unique_users,
                AVG(CAST(s.data->>'interaction_count' AS INTEGER)) as avg_interactions_per_session
            FROM sessions.sessions s
            WHERE s.agent_id = $1 
              AND s.created_at > CURRENT_TIMESTAMP - INTERVAL '%s days'
        """, agent_id, days)
        
        # Get memory statistics
        memories = self._weaviate.get_recent_memories(str(agent_id), limit=1000)
        memory_stats = {
            "total_memories": len(memories),
            "memory_types": {},
            "avg_importance": 0
        }
        
        if memories:
            for memory in memories:
                mem_type = memory.get("memory_type", "unknown")
                memory_stats["memory_types"][mem_type] = memory_stats["memory_types"].get(mem_type, 0) + 1
            memory_stats["avg_importance"] = sum(m.get("importance", 0) for m in memories) / len(memories)
        
        # Get audit events
        audit_events = await self._postgres.audit_query(
            resource_type="agent",
            resource_id=str(agent_id),
            limit=100
        )
        
        return {
            "agent": agent,
            "period_days": days,
            "interactions": interaction_stats[0] if interaction_stats else {},
            "memories": memory_stats,
            "audit_events": {
                "total": len(audit_events),
                "recent": audit_events[:10]
            }
        }
    
    # ==================== Maintenance Operations ====================
    
    async def optimize_performance(self) -> Dict[str, Any]:
        """Run performance optimization tasks."""
        self._ensure_initialized()
        
        results = {}
        
        # Analyze and vacuum PostgreSQL tables
        for table in ['cache.entries', 'sessions.sessions', 'orchestra.agents', 
                     'orchestra.workflows', 'orchestra.audit_logs']:
            await self._postgres.execute_raw(f"ANALYZE {table}")
            results[f"analyzed_{table}"] = True
        
        # Clear expired cache entries
        expired_cache = await self._postgres.cache_clear(tags=["expired"])
        results["cache_cleared"] = expired_cache
        
        # Get cache hit ratio
        cache_stats = await self._postgres.cache_stats()
        results["cache_stats"] = cache_stats
        
        return results
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check."""
        self._ensure_initialized()
        
        checks = {}
        
        # PostgreSQL health
        try:
            pg_health = await self._postgres.health_check()
            checks["postgresql"] = {
                "status": pg_health["status"],
                "details": pg_health
            }
        except Exception as e:
            checks["postgresql"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Weaviate health
        try:
            wv_health = self._weaviate.health_check()
            checks["weaviate"] = {
                "status": "healthy" if wv_health else "unhealthy",
                "ready": wv_health
            }
        except Exception as e:
            checks["weaviate"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Overall status
        all_healthy = all(
            check.get("status") == "healthy" 
            for check in checks.values()
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks
        }


# Global instance management
_unified_db_v2: Optional[UnifiedDatabaseV2] = None


async def get_unified_database() -> UnifiedDatabaseV2:
    """Get or create the global unified database instance."""
    global _unified_db_v2
    if _unified_db_v2 is None:
        _unified_db_v2 = UnifiedDatabaseV2()
        await _unified_db_v2.initialize()
    return _unified_db_v2


async def close_unified_database() -> None:
    """Close the global unified database instance."""
    global _unified_db_v2
    if _unified_db_v2:
        await _unified_db_v2.close()
        _unified_db_v2 = None