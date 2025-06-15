"""
Orchestra AI - Unified Search Manager
Handles parallel search execution across multiple providers
"""

import os
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import aiohttp
import json

from ..database.models import SearchResult
from ..utils.api_config import get_api_config

logger = logging.getLogger(__name__)

class UnifiedSearchManager:
    """Manages unified search across multiple providers with intelligent routing"""
    
    def __init__(self):
        self.search_modes = {
            "normal": {
                "providers": ["database", "duckduckgo"],
                "blend_ratio": {"database": 0.6, "web": 0.4},
                "max_time": 5,
                "parallel": True
            },
            "deep": {
                "providers": ["database", "duckduckgo", "exa_ai", "serp"],
                "blend_ratio": {"database": 0.4, "web": 0.6},
                "max_time": 15,
                "strategy": "parallel_comprehensive",
                "query_expansion": True
            },
            "deeper": {
                "providers": ["database", "exa_ai", "serp", "apify", "zenrows"],
                "blend_ratio": {"database": 0.3, "web": 0.7},
                "max_time": 30,
                "includes_scraping": True,
                "aggressive_expansion": True
            },
            "uncensored": {
                "providers": ["venice_ai", "database"],
                "blend_ratio": {"uncensored": 0.8, "database": 0.2},
                "max_time": 20,
                "filter_results": False
            }
        }
        
        # API configurations
        self.api_configs = {
            "exa_ai": {
                "endpoint": "https://api.exa.ai/search",
                "api_key": os.getenv("EXA_AI_API_KEY"),
                "enabled": bool(os.getenv("EXA_AI_API_KEY"))
            },
            "serp": {
                "endpoint": "https://serpapi.com/search",
                "api_key": os.getenv("SERP_API_KEY"),
                "enabled": bool(os.getenv("SERP_API_KEY"))
            },
            "venice_ai": {
                "endpoint": "https://api.venice.ai/v1/search",
                "api_key": os.getenv("VENICE_AI_API_KEY"),
                "enabled": bool(os.getenv("VENICE_AI_API_KEY"))
            },
            "apify": {
                "endpoint": "https://api.apify.com/v2",
                "api_key": os.getenv("APIFY_API_KEY"),
                "enabled": bool(os.getenv("APIFY_API_KEY"))
            },
            "zenrows": {
                "endpoint": "https://api.zenrows.com/v1",
                "api_key": os.getenv("ZENROWS_API_KEY"),
                "enabled": bool(os.getenv("ZENROWS_API_KEY"))
            }
        }
    
    async def execute_search(
        self,
        query: str,
        mode: str = "normal",
        persona: str = "cherry",
        blend_ratio: Optional[Dict[str, float]] = None,
        max_results: int = 20
    ) -> Dict[str, List[Dict]]:
        """Execute unified search across configured providers"""
        
        mode_config = self.search_modes.get(mode, self.search_modes["normal"])
        providers = mode_config["providers"]
        
        # Use custom blend ratio if provided
        if not blend_ratio:
            blend_ratio = mode_config["blend_ratio"]
        
        # Execute searches in parallel
        search_tasks = []
        
        for provider in providers:
            if provider == "database":
                task = self._search_database(query, persona, max_results)
            elif provider == "duckduckgo":
                task = self._search_duckduckgo(query, max_results)
            elif provider == "exa_ai" and self.api_configs["exa_ai"]["enabled"]:
                task = self._search_exa_ai(query, max_results)
            elif provider == "serp" and self.api_configs["serp"]["enabled"]:
                task = self._search_serp(query, max_results)
            elif provider == "venice_ai" and self.api_configs["venice_ai"]["enabled"]:
                task = self._search_venice_ai(query, max_results)
            elif provider == "apify" and self.api_configs["apify"]["enabled"]:
                task = self._search_apify(query, max_results)
            elif provider == "zenrows" and self.api_configs["zenrows"]["enabled"]:
                task = self._search_zenrows(query, max_results)
            else:
                continue
            
            search_tasks.append(task)
        
        # Wait for all searches with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*search_tasks, return_exceptions=True),
                timeout=mode_config["max_time"]
            )
        except asyncio.TimeoutError:
            logger.warning(f"Search timeout after {mode_config['max_time']}s")
            results = []
        
        # Aggregate results by provider
        results_by_provider = {}
        for i, provider in enumerate(providers):
            if i < len(results) and not isinstance(results[i], Exception):
                results_by_provider[provider] = results[i]
            else:
                results_by_provider[provider] = []
        
        return results_by_provider
    
    async def _search_database(self, query: str, persona: str, max_results: int) -> List[Dict]:
        """Search internal database"""
        from ..database.db_manager import get_db
        
        try:
            db = get_db()
            # Search with persona-specific filters
            results = await db.search_knowledge_base(
                query=query,
                filters={"persona": persona},
                limit=max_results
            )
            
            return [
                {
                    "title": r.title,
                    "content": r.content,
                    "url": r.url,
                    "source": "Database",
                    "relevance_score": r.relevance_score,
                    "metadata": r.metadata
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Database search error: {e}")
            return []
    
    async def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict]:
        """Search using DuckDuckGo"""
        try:
            from duckduckgo_search import AsyncDDGS
            
            async with AsyncDDGS() as ddgs:
                results = []
                async for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "content": r.get("body", ""),
                        "url": r.get("href", ""),
                        "source": "DuckDuckGo",
                        "relevance_score": 0.0,  # DDG doesn't provide scores
                        "metadata": {}
                    })
                
                return results
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    async def _search_exa_ai(self, query: str, max_results: int) -> List[Dict]:
        """Search using Exa AI semantic search"""
        config = self.api_configs["exa_ai"]
        if not config["enabled"]:
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "query": query,
                    "num_results": max_results,
                    "use_autoprompt": True,
                    "type": "neural"
                }
                
                async with session.post(
                    config["endpoint"],
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result_data = await response.json()
                        
                        return [
                            {
                                "title": r.get("title", ""),
                                "content": r.get("text", ""),
                                "url": r.get("url", ""),
                                "source": "Exa AI",
                                "relevance_score": r.get("score", 0.0),
                                "metadata": {
                                    "published_date": r.get("published_date"),
                                    "author": r.get("author")
                                }
                            }
                            for r in result_data.get("results", [])
                        ]
                    else:
                        logger.error(f"Exa AI error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Exa AI search error: {e}")
            return []
    
    async def _search_serp(self, query: str, max_results: int) -> List[Dict]:
        """Search using SERP API for Google results"""
        config = self.api_configs["serp"]
        if not config["enabled"]:
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "q": query,
                    "api_key": config["api_key"],
                    "engine": "google",
                    "num": max_results,
                    "output": "json"
                }
                
                async with session.get(
                    config["endpoint"],
                    params=params
                ) as response:
                    if response.status == 200:
                        result_data = await response.json()
                        
                        results = []
                        for r in result_data.get("organic_results", []):
                            results.append({
                                "title": r.get("title", ""),
                                "content": r.get("snippet", ""),
                                "url": r.get("link", ""),
                                "source": "Google (SERP)",
                                "relevance_score": r.get("position", 100) / 100,
                                "metadata": {
                                    "date": r.get("date"),
                                    "displayed_link": r.get("displayed_link")
                                }
                            })
                        
                        return results
                    else:
                        logger.error(f"SERP API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"SERP API search error: {e}")
            return []
    
    async def _search_venice_ai(self, query: str, max_results: int) -> List[Dict]:
        """Search using Venice AI for uncensored results"""
        config = self.api_configs["venice_ai"]
        if not config["enabled"]:
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "query": query,
                    "max_results": max_results,
                    "safe_mode": False,  # Uncensored mode
                    "include_adult": True
                }
                
                async with session.post(
                    config["endpoint"],
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result_data = await response.json()
                        
                        return [
                            {
                                "title": r.get("title", ""),
                                "content": r.get("description", ""),
                                "url": r.get("url", ""),
                                "source": "Venice AI (Uncensored)",
                                "relevance_score": r.get("relevance", 0.0),
                                "metadata": {
                                    "content_type": r.get("content_type"),
                                    "uncensored": True
                                }
                            }
                            for r in result_data.get("results", [])
                        ]
                    else:
                        logger.error(f"Venice AI error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Venice AI search error: {e}")
            return []
    
    async def _search_apify(self, query: str, max_results: int) -> List[Dict]:
        """Search using Apify for deep web scraping"""
        config = self.api_configs["apify"]
        if not config["enabled"]:
            return []
        
        # Apify would be used for specific scraping tasks
        # For now, return empty as it requires actor configuration
        logger.info(f"Apify search requested but not implemented for query: {query}")
        return []
    
    async def _search_zenrows(self, query: str, max_results: int) -> List[Dict]:
        """Search using ZenRows for proxy-based scraping"""
        config = self.api_configs["zenrows"]
        if not config["enabled"]:
            return []
        
        # ZenRows would be used for specific scraping with proxies
        # For now, return empty as it requires specific URL targets
        logger.info(f"ZenRows search requested but not implemented for query: {query}")
        return [] 