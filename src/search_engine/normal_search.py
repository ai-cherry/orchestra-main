#!/usr/bin/env python3
"""Normal search implementation for standard queries"""

import asyncio
import logging
from typing import Dict, Any, List
from .base_search import BaseSearcher
from ..llm.client import LLMClient
from ..vector_db.weaviate_adapter import WeaviateAdapter
from ..database import UnifiedDatabase

logger = logging.getLogger(__name__)


class NormalSearcher(BaseSearcher):
    """Standard search implementation with semantic and keyword search"""
    
    def __init__(self):
        """Initialize normal searcher with required components"""
        self.llm = LLMClient(model="gpt-4", temperature=0.3)
        self.vector_db = WeaviateAdapter(domain="search")
        self.db = UnifiedDatabase()
        self.max_results = 20
        self.timeout = 5  # seconds
    
    async def run(self, query: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute normal search combining semantic and keyword approaches"""
        options = options or {}
        limit = min(options.get("limit", self.max_results), 50)
        offset = options.get("offset", 0)
        
        try:
            # Execute searches in parallel
            semantic_task = asyncio.create_task(
                self._semantic_search(query, limit, offset)
            )
            keyword_task = asyncio.create_task(
                self._keyword_search(query, limit, offset)
            )
            
            # Wait for both with timeout
            semantic_results, keyword_results = await asyncio.gather(
                semantic_task, 
                keyword_task,
                return_exceptions=True
            )
            
            # Handle errors
            if isinstance(semantic_results, Exception):
                logger.error(f"Semantic search failed: {semantic_results}")
                semantic_results = []
            if isinstance(keyword_results, Exception):
                logger.error(f"Keyword search failed: {keyword_results}")
                keyword_results = []
            
            # Merge and deduplicate results
            merged_results = self._merge_results(semantic_results, keyword_results)
            
            # Generate summary if we have results
            summary = ""
            if merged_results:
                summary = await self._generate_summary(query, merged_results[:5])
            
            return {
                "results": merged_results[:limit],
                "summary": summary,
                "total_found": len(merged_results),
                "search_type": "normal",
                "sources": {
                    "semantic": len(semantic_results),
                    "keyword": len(keyword_results)
                }
            }
            
        except asyncio.TimeoutError:
            logger.error(f"Search timeout for query: {query}")
            return {
                "results": [],
                "summary": "Search timed out. Please try again.",
                "error": "timeout"
            }
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return {
                "results": [],
                "summary": f"An error occurred during search: {str(e)}",
                "error": str(e)
            }
    
    async def _semantic_search(self, query: str, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Perform semantic search using Weaviate"""
        try:
            # Get query embedding
            embedding = await self.llm.get_embedding(query)
            
            # Search in Weaviate
            results = await self.vector_db.search(
                embedding=embedding,
                limit=limit,
                offset=offset,
                collection="documents"
            )
            
            # Format results
            formatted_results = []
            for idx, result in enumerate(results):
                formatted_results.append({
                    "id": result.get("id", f"semantic_{idx}"),
                    "title": result.get("title", "Untitled"),
                    "content": result.get("content", ""),
                    "score": result.get("certainty", 0.0),
                    "source": "semantic",
                    "metadata": result.get("metadata", {})
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Semantic search error: {str(e)}")
            raise
    
    async def _keyword_search(self, query: str, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Perform keyword search using PostgreSQL full-text search"""
        try:
            # Build search query with EXPLAIN for optimization
            search_query = """
            EXPLAIN ANALYZE
            SELECT id, title, content, 
                   ts_rank(search_vector, plainto_tsquery('english', $1)) as rank
            FROM documents
            WHERE search_vector @@ plainto_tsquery('english', $2)
            ORDER BY rank DESC
            LIMIT $3 OFFSET $4
            """
            
            # Log query plan
            plan_results = await self.db.fetch_all(search_query, (query, query, limit, offset))
            logger.info(f"Keyword search query plan: {plan_results}")
            
            # Execute actual query
            actual_query = search_query.replace("EXPLAIN ANALYZE\n", "")
            results = await self.db.fetch_all(
                actual_query,
                (query, query, limit, offset)
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result["id"],
                    "title": result["title"],
                    "content": result["content"],
                    "score": float(result["rank"]),
                    "source": "keyword",
                    "metadata": {}
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Keyword search error: {str(e)}")
            raise
    
    def _merge_results(self, semantic_results: List[Dict], keyword_results: List[Dict]) -> List[Dict]:
        """Merge and deduplicate results from different sources"""
        # Combine all results
        all_results = semantic_results + keyword_results
        
        # Sort by score
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # Deduplicate
        seen_ids = set()
        merged = []
        for result in all_results:
            result_id = result.get("id")
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                merged.append(result)
        
        return merged
    
    async def _generate_summary(self, query: str, top_results: List[Dict]) -> str:
        """Generate a summary of top search results using LLM"""
        try:
            # Extract content from top results
            contents = []
            for result in top_results:
                title = result.get("title", "")
                content = result.get("content", "")[:500]  # Limit content length
                contents.append(f"Title: {title}\nContent: {content}\n")
            
            # Build prompt
            prompt = f"""
            Based on the following search results for the query "{query}", 
            provide a concise summary (2-3 sentences) of the most relevant information found:
            
            {chr(10).join(contents)}
            """
            
            # Generate summary
            summary = await self.llm.generate(prompt, max_tokens=150)
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Summary generation error: {str(e)}")
            return "Unable to generate summary."