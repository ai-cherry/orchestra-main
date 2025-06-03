#!/usr/bin/env python3
"""Search router for handling different search modes"""

from enum import Enum
from typing import Dict, Any
import logging
from ..utils.circuit_breaker import circuit_breaker

logger = logging.getLogger(__name__)


class SearchMode(Enum):
    """Available search modes"""
    NORMAL = "normal"
    CREATIVE = "creative"
    DEEP = "deep"
    SUPER_DEEP = "super_deep"
    UNCENSORED = "uncensored"


class SearchRouter:
    """Routes search requests to appropriate search strategies"""
    
    def __init__(self):
        self.strategies = {
            SearchMode.NORMAL: self._normal_search,
            SearchMode.CREATIVE: self._creative_search,
            SearchMode.DEEP: self._deep_search,
            SearchMode.SUPER_DEEP: self._super_deep_search,
            SearchMode.UNCENSORED: self._uncensored_search
        }
    
    @circuit_breaker(name="search_router", failure_threshold=5)
    async def route_search(self, query: str, mode: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Route search request to appropriate strategy"""
        try:
            search_mode = SearchMode(mode)
            strategy = self.strategies.get(search_mode, self._normal_search)
            return await strategy(query, options or {})
        except ValueError:
            logger.warning(f"Invalid search mode: {mode}, defaulting to normal")
            return await self._normal_search(query, options or {})
    
    async def _normal_search(self, query: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Standard search implementation"""
        return {"mode": "normal", "query": query, "results": []}
    
    async def _creative_search(self, query: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Creative search with lateral thinking"""
        return {"mode": "creative", "query": query, "results": []}
    
    async def _deep_search(self, query: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Deep search with multi-hop reasoning"""
        return {"mode": "deep", "query": query, "results": []}
    
    async def _super_deep_search(self, query: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Research-grade search with citations"""
        return {"mode": "super_deep", "query": query, "results": []}
    
    async def _uncensored_search(self, query: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Uncensored search with minimal filtering"""
        return {"mode": "uncensored", "query": query, "results": []}
