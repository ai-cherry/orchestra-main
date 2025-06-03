#!/usr/bin/env python3
"""Base search class for all search implementations"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class BaseSearcher(ABC):
    """Abstract base class for all search implementations"""
    
    def __init__(self):
        self.logger = logger
    
    @abstractmethod
    async def run(self, query: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the search"""
        pass
    
    def validate_query(self, query: str) -> bool:
        """Validate the search query"""
        if not query or not query.strip():
            return False
        if len(query) > 1000:
            return False
        return True
