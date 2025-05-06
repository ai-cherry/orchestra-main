"""
Semantic Router for AI Orchestration System.

This module provides a semantic router that selects agents based on
semantic similarity between queries and agent capabilities.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

from core.orchestrator.src.services.memory_service import get_memory_service
from core.orchestrator.src.agents.unified_agent_registry import get_agent_registry, AgentCapability

# Configure logging
logger = logging.getLogger(__name__)


class SemanticRouter:
    """Routes requests to agents based on semantic similarity"""
    
    def __init__(self):
        """Initialize the semantic router."""
        self._memory_service = get_memory_service()
        self._agent_registry = get_agent_registry()
        self._agent_embeddings: Dict[str, List[float]] = {}
        logger.info("SemanticRouter initialized")
        
    async def initialize(self):
        """Initialize agent embeddings."""
        # This would use an embedding model to create vectors for each agent's capabilities
        # For now, we'll use a simple placeholder implementation
        await self._generate_agent_embeddings()
        
    async def _generate_agent_embeddings(self):
        """Generate embeddings for each agent's capabilities."""
        # In a real implementation, this would use an embedding model
        # For now, we'll use random vectors as placeholders
        agent_types = self._agent_registry.get_agent_types()
        
        for agent_type in agent_types:
            # Get agent info
            agent_info = self._agent_registry.get_agent_info(agent_type)
            
            # Generate a random embedding for demonstration
            # In a real implementation, this would be based on agent capabilities
            # and would use a proper embedding model
            embedding_dim = 768  # Common embedding dimension
            self._agent_embeddings[agent_type] = list(np.random.randn(embedding_dim))
            
        logger.info(f"Generated embeddings for {len(agent_types)} agents")
        
    async def route_request(
        self, 
        user_id: str, 
        query: str, 
        query_embedding: List[float],
        required_capabilities: Optional[List[AgentCapability]] = None
    ) -> Tuple[str, float]:
        """
        Route a request to the most appropriate agent.
        
        Args:
            user_id: The user ID
            query: The user's query text
            query_embedding: Vector embedding of the query
            required_capabilities: Optional list of required capabilities
            
        Returns:
            Tuple of (agent_type, confidence)
        """
        # First filter by required capabilities
        candidate_agents = []
        
        if required_capabilities:
            # Use the registry to find agents with all required capabilities
            agent_types = self._agent_registry.get_agent_types()
            for agent_type in agent_types:
                agent_info = self._agent_registry.get_agent_info(agent_type)
                if all(agent_info.supports_capability(cap) for cap in required_capabilities):
                    candidate_agents.append(agent_type)
        else:
            # All agents are candidates
            candidate_agents = self._agent_registry.get_agent_types()
            
        if not candidate_agents:
            # No agents match the required capabilities
            logger.warning(f"No agents found with required capabilities: {required_capabilities}")
            return None, 0.0
            
        # Calculate semantic similarity with each agent's embedding
        similarities = []
        for agent_type in candidate_agents:
            if agent_type in self._agent_embeddings:
                # Calculate cosine similarity
                agent_embedding = self._agent_embeddings[agent_type]
                similarity = self._cosine_similarity(query_embedding, agent_embedding)
                similarities.append((agent_type, similarity))
            else:
                # No embedding, use a default low similarity
                similarities.append((agent_type, 0.1))
                
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        if not similarities:
            logger.warning("No agent similarities calculated")
            return None, 0.0
            
        # Return the best match
        best_agent, confidence = similarities[0]
        logger.info(f"Routed request to {best_agent} with confidence {confidence:.2f}")
        return best_agent, confidence
        
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity (0-1)
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # Avoid division by zero
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return np.dot(vec1, vec2) / (norm1 * norm2)
        
    async def get_query_embedding(self, query: str) -> List[float]:
        """
        Get embedding for a query.
        
        Args:
            query: The query text
            
        Returns:
            Vector embedding of the query
        """
        # In a real implementation, this would use an embedding model
        # For now, we'll use a random vector as a placeholder
        embedding_dim = 768  # Common embedding dimension
        return list(np.random.randn(embedding_dim))


# Singleton instance
_semantic_router = None


async def get_semantic_router() -> SemanticRouter:
    """
    Get the global semantic router instance.
    
    Returns:
        The global SemanticRouter instance
    """
    global _semantic_router
    if _semantic_router is None:
        _semantic_router = SemanticRouter()
        await _semantic_router.initialize()
    return _semantic_router