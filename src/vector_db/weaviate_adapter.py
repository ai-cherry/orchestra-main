"""Weaviate adapter for vector database operations"""

import os
import logging
from typing import Dict, Any, List, Optional
import weaviate

logger = logging.getLogger(__name__)


class WeaviateAdapter:
    """Adapter for Weaviate vector database"""
    
    def __init__(self, domain: str = "default"):
        self.domain = domain
        self.client = None
        self._connect()
    
    def _connect(self):
        """Connect to Weaviate instance"""
        try:
            weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
            self.client = weaviate.Client(url=weaviate_url)
            logger.info(f"Connected to Weaviate at {weaviate_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            # Create a mock client for development
            self.client = None
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        if not self.client:
            # Return mock results if not connected
            return [
                {
                    "id": f"mock_{i}",
                    "content": f"Mock result {i} for query: {query}",
                    "score": 0.9 - (i * 0.1)
                }
                for i in range(min(limit, 5))
            ]
        
        try:
            # TODO: Implement actual Weaviate search
            result = self.client.query.get(
                self.domain,
                ["content", "title", "metadata"]
            ).with_near_text({
                "concepts": [query]
            }).with_limit(limit).do()
            
            return self._format_results(result)
        except Exception as e:
            logger.error(f"Weaviate search error: {e}")
            return []
    
    async def insert(self, data: Dict[str, Any]) -> str:
        """Insert data into Weaviate"""
        if not self.client:
            return "mock_id"
        
        try:
            result = self.client.data_object.create(
                data_object=data,
                class_name=self.domain
            )
            return result
        except Exception as e:
            logger.error(f"Weaviate insert error: {e}")
            return ""
    
    def _format_results(self, weaviate_result: Dict) -> List[Dict[str, Any]]:
        """Format Weaviate results"""
        formatted = []
        
        if "data" in weaviate_result and "Get" in weaviate_result["data"]:
            items = weaviate_result["data"]["Get"].get(self.domain, [])
            for item in items:
                formatted.append({
                    "id": item.get("_additional", {}).get("id", ""),
                    "content": item.get("content", ""),
                    "title": item.get("title", ""),
                    "metadata": item.get("metadata", {}),
                    "score": item.get("_additional", {}).get("certainty", 0.0)
                })
        
        return formatted