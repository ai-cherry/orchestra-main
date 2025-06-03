#!/usr/bin/env python3
"""Creative search implementation with lateral thinking and concept expansion"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_search import BaseSearcher
from ..utils.circuit_breaker import circuit_breaker
from ..llm import LLMClient
from ..vector_db import WeaviateAdapter
from ..database import UnifiedDatabase

logger = logging.getLogger(__name__)


class CreativeSearcher(BaseSearcher):
    """
    Creative search that expands queries, finds lateral connections,
    and discovers non-obvious relationships
    """
    
    def __init__(self):
        super().__init__()
        self.max_expansions = 5
        self.max_hops = 3
    
    @circuit_breaker
    async def run(self, query: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute creative search with query expansion and lateral thinking
        """
        options = options or {}
        limit = min(options.get("limit", 30), 100)
        creativity_level = options.get("creativity_level", 0.7)
        
        try:
            # Step 1: Expand query with related concepts
            expanded_queries = await self._expand_query(query, creativity_level)
            logger.info(f"Expanded query to: {expanded_queries}")
            
            # Step 2: Search for each expanded query in parallel
            search_tasks = []
            for expanded_query in expanded_queries[:self.max_expansions]:
                task = asyncio.create_task(
                    self._search_expanded(expanded_query, limit // len(expanded_queries))
                )
                search_tasks.append(task)
            
            # Collect all results
            all_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Step 3: Find lateral connections
            merged_results = []
            for results in all_results:
                if not isinstance(results, Exception):
                    merged_results.extend(results)
            
            # Step 4: Discover hidden connections
            connections = await self._find_connections(query, merged_results)
            
            # Step 5: Generate creative insights
            insights = await self._generate_insights(query, merged_results, connections)
            
            # Step 6: Rank by creativity and relevance
            ranked_results = self._rank_by_creativity(merged_results, connections)
            
            return {
                "results": ranked_results[:limit],
                "expanded_queries": expanded_queries,
                "connections": connections,
                "insights": insights,
                "search_type": "creative",
                "creativity_score": creativity_level
            }
            
        except Exception as e:
            logger.error(f"Creative search error: {str(e)}")
            # Fallback to basic search
            return {
                "results": [],
                "error": str(e),
                "search_type": "creative_fallback"
            }
    
    async def _expand_query(self, query: str, creativity_level: float) -> List[str]:
        """Use LLM to generate creative query expansions"""
        try:
            prompt = f"""
Original query: "{query}"
Creativity level: {creativity_level} (0=conservative, 1=very creative)

Generate query expansions that:
1. Use metaphors and analogies
2. Explore adjacent concepts
3. Consider different perspectives
4. Make non-obvious connections
5. Think laterally about the topic

Return as JSON array of strings."""
            
            # TODO: Implement LLM call
            # For now, return basic expansions
            return [
                query,
                f"{query} innovative approaches",
                f"{query} alternative perspectives",
                f"{query} creative solutions"
            ]
            
        except Exception as e:
            logger.error(f"Query expansion error: {str(e)}")
            return [query]  # Fallback to original
    
    async def _search_expanded(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search for an expanded query"""
        try:
            # TODO: Implement actual search
            # For now, return mock results
            results = []
            for i in range(min(limit, 5)):
                results.append({
                    "id": f"creative_{query}_{i}",
                    "title": f"Creative result for {query}",
                    "content": f"This is a creative search result for the expanded query: {query}",
                    "score": 0.8 - (i * 0.1),
                    "expanded_from": query,
                    "search_method": "creative_expansion"
                })
            return results
            
        except Exception as e:
            logger.error(f"Expanded search error for '{query}': {str(e)}")
            return []
    
    async def _find_connections(self, original_query: str, results: List[Dict]) -> List[Dict[str, Any]]:
        """Discover hidden connections between results"""
        try:
            if not results:
                return []
            
            # Extract concepts from results
            concepts = set()
            for result in results[:20]:
                content = result.get("content", "")
                title = result.get("title", "")
                # Simple concept extraction (could be enhanced with NLP)
                words = (title + " " + content).lower().split()
                concepts.update(word for word in words if len(word) > 4)
            
            # TODO: Use LLM to find connections
            # For now, return mock connections
            connections = [
                {
                    "connection": "Pattern recognition",
                    "concepts": [original_query, "creative", "innovation"],
                    "insight": "Creative approaches often involve recognizing patterns others miss"
                },
                {
                    "connection": "Cross-domain thinking",
                    "concepts": [original_query, "alternative", "perspectives"],
                    "insight": "Solutions often come from applying concepts from unrelated fields"
                }
            ]
            
            return connections
            
        except Exception as e:
            logger.error(f"Connection finding error: {str(e)}")
            return []
    
    async def _generate_insights(self, query: str, results: List[Dict], connections: List[Dict]) -> str:
        """Generate creative insights from search results"""
        try:
            if not results:
                return "No results found to generate insights."
            
            # TODO: Use LLM to generate insights
            # For now, return a basic insight
            insight = f"""
Creative insights for "{query}":

1. **Lateral Connections**: The search revealed unexpected connections between {query} and related concepts, 
   suggesting new approaches to understanding the topic.

2. **Pattern Recognition**: Multiple results show a pattern of innovation through combining seemingly unrelated ideas.

3. **Alternative Perspectives**: Viewing {query} through different lenses opens up new possibilities for exploration.
"""
            
            return insight.strip()
            
        except Exception as e:
            logger.error(f"Insight generation error: {str(e)}")
            return "Unable to generate creative insights."
    
    def _rank_by_creativity(self, results: List[Dict], connections: List[Dict]) -> List[Dict]:
        """Rank results by creativity and connection strength"""
        try:
            # Extract concepts from connections
            connection_concepts = set()
            for conn in connections:
                connection_concepts.update(conn.get("concepts", []))
            
            # Score each result
            for result in results:
                creativity_score = 0.0
                
                # Base score from search
                creativity_score += result.get("score", 0.5)
                
                # Boost for expanded queries
                if result.get("expanded_from"):
                    creativity_score += 0.2
                
                # Boost for connection relevance
                content = (result.get("title", "") + " " + result.get("content", "")).lower()
                matching_concepts = sum(1 for concept in connection_concepts if concept in content)
                creativity_score += min(matching_concepts * 0.1, 0.5)
                
                result["creativity_score"] = creativity_score
            
            # Sort by creativity score
            results.sort(key=lambda x: x.get("creativity_score", 0), reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Ranking error: {str(e)}")
            return results