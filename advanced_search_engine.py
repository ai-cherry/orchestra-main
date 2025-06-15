# Orchestra AI Advanced Search Engine Implementation
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import asyncio
import aiohttp
import requests
import json
import time
from datetime import datetime
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Request/Response Models
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    persona: str = Field(default="sophia", description="Active persona for search context")
    search_mode: str = Field(default="normal", description="Search intensity mode")
    include_database: bool = Field(default=True, description="Include internal database search")
    include_internet: bool = Field(default=True, description="Include internet search")
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum results to return")

class SearchResult(BaseModel):
    title: str
    content: str
    url: Optional[str] = None
    source: str
    relevance_score: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BlendedSearchResponse(BaseModel):
    query: str
    persona: str
    search_mode: str
    total_results: int
    database_results: List[SearchResult]
    internet_results: List[SearchResult]
    blended_results: List[SearchResult]
    processing_time_ms: int
    sources_used: List[str]
    cost_estimate: float = 0.0

# Search Engine Configuration
class SearchConfig:
    def __init__(self):
        # API Keys (these should be loaded from environment variables)
        self.browser_use_api_key = os.getenv('BROWSER_USE_API_KEY', '')
        self.exa_ai_api_key = os.getenv('EXA_AI_API_KEY', '')
        self.serp_api_key = os.getenv('SERP_API_KEY', '')
        self.apify_api_key = os.getenv('APIFY_API_KEY', '')
        self.phantombuster_api_key = os.getenv('PHANTOMBUSTER_API_KEY', '')
        self.zenrows_api_key = os.getenv('ZENROWS_API_KEY', '')
        self.venice_ai_api_key = os.getenv('VENICE_AI_API_KEY', '')
        
        # Search mode configurations
        self.search_modes = {
            'normal': {
                'max_sources': 3,
                'timeout': 10,
                'apis': ['duckduckgo', 'database'],
                'scraping': False
            },
            'deep': {
                'max_sources': 5,
                'timeout': 20,
                'apis': ['duckduckgo', 'exa_ai', 'serp', 'database'],
                'scraping': True,
                'scraping_depth': 'light'
            },
            'super_deep': {
                'max_sources': 8,
                'timeout': 30,
                'apis': ['duckduckgo', 'exa_ai', 'serp', 'apify', 'phantombuster', 'database'],
                'scraping': True,
                'scraping_depth': 'aggressive'
            },
            'uncensored': {
                'max_sources': 6,
                'timeout': 25,
                'apis': ['venice_ai', 'zenrows', 'exa_ai', 'database'],
                'scraping': True,
                'scraping_depth': 'aggressive',
                'content_filtering': False
            }
        }

# Database Search Functions
async def search_database(query: str, persona: str, max_results: int = 10) -> List[SearchResult]:
    """Search internal PostgreSQL database for relevant information"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            database="orchestra_prod",
            user="orchestra",
            password="Orchestra_Prod_2025_Secure"
        )
        
        cursor = conn.cursor()
        results = []
        
        # Get persona context for search weighting
        cursor.execute("SELECT domain_leanings FROM orchestra.personas WHERE name = %s", (persona.title(),))
        persona_data = cursor.fetchone()
        domain_keywords = []
        if persona_data and persona_data[0]:
            domain_keywords = persona_data[0].get('keywords', [])
        
        # Search personas with domain weighting
        search_query = f"%{query}%"
        cursor.execute("""
            SELECT name, description, persona_type, domain_leanings 
            FROM orchestra.personas 
            WHERE description ILIKE %s OR name ILIKE %s
            ORDER BY 
                CASE WHEN name ILIKE %s THEN 1 ELSE 2 END,
                LENGTH(description) DESC
            LIMIT %s
        """, (search_query, search_query, search_query, max_results))
        
        for row in cursor.fetchall():
            results.append(SearchResult(
                title=f"Persona: {row[0]}",
                content=f"{row[1]} (Type: {row[2]})",
                source="Database - Personas",
                relevance_score=0.9,
                metadata={"persona_type": row[2], "domain_leanings": row[3]}
            ))
        
        # Search conversations and messages
        cursor.execute("""
            SELECT c.title, m.content, m.created_at
            FROM orchestra.conversations c
            JOIN orchestra.messages m ON c.id = m.conversation_id
            WHERE m.content ILIKE %s
            ORDER BY m.created_at DESC
            LIMIT %s
        """, (search_query, max_results))
        
        for row in cursor.fetchall():
            results.append(SearchResult(
                title=f"Conversation: {row[0] or 'Untitled'}",
                content=row[1][:500] + "..." if len(row[1]) > 500 else row[1],
                source="Database - Conversations",
                relevance_score=0.8,
                timestamp=row[2],
                metadata={"type": "conversation"}
            ))
        
        cursor.close()
        conn.close()
        
        return results[:max_results]
        
    except Exception as e:
        logger.error(f"Database search failed: {e}")
        return []

# Internet Search Functions
async def search_duckduckgo(query: str, max_results: int = 10) -> List[SearchResult]:
    """Search using DuckDuckGo Instant Answer API"""
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                data = await response.json()
        
        results = []
        
        # Add abstract if available
        if data.get('AbstractText'):
            results.append(SearchResult(
                title=data.get('Heading', 'DuckDuckGo Result'),
                content=data.get('AbstractText'),
                url=data.get('AbstractURL', ''),
                source="DuckDuckGo",
                relevance_score=0.8
            ))
        
        # Add related topics
        for topic in data.get('RelatedTopics', [])[:max_results-1]:
            if isinstance(topic, dict) and topic.get('Text'):
                results.append(SearchResult(
                    title=topic.get('Text', '')[:100] + '...',
                    content=topic.get('Text', ''),
                    url=topic.get('FirstURL', ''),
                    source="DuckDuckGo Related",
                    relevance_score=0.6
                ))
        
        return results[:max_results]
        
    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {e}")
        return []

async def search_exa_ai(query: str, api_key: str, max_results: int = 10) -> List[SearchResult]:
    """Search using Exa AI semantic search"""
    if not api_key:
        logger.warning("Exa AI API key not provided")
        return []
    
    try:
        url = "https://api.exa.ai/search"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "query": query,
            "num_results": max_results,
            "include_domains": [],
            "exclude_domains": [],
            "use_autoprompt": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=15) as response:
                if response.status == 200:
                    result_data = await response.json()
                    results = []
                    
                    for item in result_data.get('results', []):
                        results.append(SearchResult(
                            title=item.get('title', 'Exa AI Result'),
                            content=item.get('text', '')[:1000],
                            url=item.get('url', ''),
                            source="Exa AI",
                            relevance_score=item.get('score', 0.7),
                            metadata={"published_date": item.get('published_date')}
                        ))
                    
                    return results
                else:
                    logger.error(f"Exa AI search failed with status: {response.status}")
                    return []
                    
    except Exception as e:
        logger.error(f"Exa AI search failed: {e}")
        return []

async def search_serp_api(query: str, api_key: str, max_results: int = 10) -> List[SearchResult]:
    """Search using SERP API for Google results"""
    if not api_key:
        logger.warning("SERP API key not provided")
        return []
    
    try:
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": api_key,
            "engine": "google",
            "num": max_results
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for item in data.get('organic_results', []):
                        results.append(SearchResult(
                            title=item.get('title', 'SERP Result'),
                            content=item.get('snippet', ''),
                            url=item.get('link', ''),
                            source="Google (SERP)",
                            relevance_score=0.8,
                            metadata={"position": item.get('position')}
                        ))
                    
                    return results
                else:
                    logger.error(f"SERP API search failed with status: {response.status}")
                    return []
                    
    except Exception as e:
        logger.error(f"SERP API search failed: {e}")
        return []

async def search_with_scraping(query: str, mode: str, config: SearchConfig) -> List[SearchResult]:
    """Perform advanced search with web scraping capabilities"""
    results = []
    
    if mode in ['deep', 'super_deep', 'uncensored']:
        # For now, implement basic scraping simulation
        # In production, this would integrate with Apify, PhantomBuster, ZenRows
        
        try:
            # Simulate Apify actor run
            if 'apify' in config.search_modes[mode]['apis']:
                logger.info(f"Simulating Apify search for: {query}")
                results.append(SearchResult(
                    title=f"Apify Data Extraction: {query}",
                    content=f"Extracted structured data related to {query} using Apify actors.",
                    source="Apify (Simulated)",
                    relevance_score=0.7,
                    metadata={"extraction_type": "structured_data"}
                ))
            
            # Simulate PhantomBuster automation
            if 'phantombuster' in config.search_modes[mode]['apis']:
                logger.info(f"Simulating PhantomBuster search for: {query}")
                results.append(SearchResult(
                    title=f"PhantomBuster Social Data: {query}",
                    content=f"Social media and platform data related to {query} extracted via PhantomBuster.",
                    source="PhantomBuster (Simulated)",
                    relevance_score=0.6,
                    metadata={"extraction_type": "social_data"}
                ))
            
            # Simulate ZenRows proxy scraping
            if 'zenrows' in config.search_modes[mode]['apis']:
                logger.info(f"Simulating ZenRows scraping for: {query}")
                results.append(SearchResult(
                    title=f"ZenRows Scraped Content: {query}",
                    content=f"Web content related to {query} scraped using ZenRows proxy service.",
                    source="ZenRows (Simulated)",
                    relevance_score=0.8,
                    metadata={"extraction_type": "web_scraping"}
                ))
                
        except Exception as e:
            logger.error(f"Scraping simulation failed: {e}")
    
    return results

# Search Orchestration Engine
class SearchOrchestrator:
    def __init__(self):
        self.config = SearchConfig()
    
    async def execute_search(self, request: SearchRequest) -> BlendedSearchResponse:
        """Execute a comprehensive search across multiple sources"""
        start_time = time.time()
        
        database_results = []
        internet_results = []
        sources_used = []
        
        # Get search mode configuration
        mode_config = self.config.search_modes.get(request.search_mode, self.config.search_modes['normal'])
        
        # Execute database search if requested
        if request.include_database:
            try:
                database_results = await search_database(
                    request.query, 
                    request.persona, 
                    max_results=request.max_results // 2
                )
                if database_results:
                    sources_used.append("Database")
            except Exception as e:
                logger.error(f"Database search failed: {e}")
        
        # Execute internet searches if requested
        if request.include_internet:
            search_tasks = []
            
            # DuckDuckGo (always available)
            if 'duckduckgo' in mode_config['apis']:
                search_tasks.append(search_duckduckgo(request.query, max_results=5))
                sources_used.append("DuckDuckGo")
            
            # Exa AI
            if 'exa_ai' in mode_config['apis']:
                search_tasks.append(search_exa_ai(
                    request.query, 
                    self.config.exa_ai_api_key, 
                    max_results=5
                ))
                sources_used.append("Exa AI")
            
            # SERP API
            if 'serp' in mode_config['apis']:
                search_tasks.append(search_serp_api(
                    request.query, 
                    self.config.serp_api_key, 
                    max_results=5
                ))
                sources_used.append("SERP API")
            
            # Advanced scraping for deep modes
            if mode_config.get('scraping', False):
                search_tasks.append(search_with_scraping(
                    request.query, 
                    request.search_mode, 
                    self.config
                ))
                sources_used.extend(["Apify", "PhantomBuster", "ZenRows"])
            
            # Execute all internet searches concurrently
            try:
                search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
                
                for result in search_results:
                    if isinstance(result, list):
                        internet_results.extend(result)
                    elif isinstance(result, Exception):
                        logger.error(f"Search task failed: {result}")
                        
            except Exception as e:
                logger.error(f"Internet search orchestration failed: {e}")
        
        # Blend and rank results
        blended_results = self._blend_results(
            database_results, 
            internet_results, 
            request.persona, 
            request.query
        )
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)
        
        return BlendedSearchResponse(
            query=request.query,
            persona=request.persona,
            search_mode=request.search_mode,
            total_results=len(blended_results),
            database_results=database_results,
            internet_results=internet_results,
            blended_results=blended_results[:request.max_results],
            processing_time_ms=processing_time,
            sources_used=sources_used,
            cost_estimate=self._estimate_cost(sources_used, len(blended_results))
        )
    
    def _blend_results(self, db_results: List[SearchResult], web_results: List[SearchResult], 
                      persona: str, query: str) -> List[SearchResult]:
        """Intelligently blend database and web results based on persona and query"""
        
        # Combine all results
        all_results = db_results + web_results
        
        # Apply persona-specific weighting
        persona_weights = {
            'cherry': {'database': 0.3, 'creative': 1.2, 'entertainment': 1.1},
            'sophia': {'database': 0.8, 'business': 1.3, 'analytical': 1.2},
            'karen': {'database': 0.7, 'clinical': 1.4, 'regulatory': 1.3}
        }
        
        weights = persona_weights.get(persona.lower(), {'database': 0.5})
        
        # Adjust relevance scores based on persona
        for result in all_results:
            if 'Database' in result.source:
                result.relevance_score *= weights.get('database', 0.5)
            
            # Boost scores based on content relevance to persona domain
            content_lower = result.content.lower()
            for domain, weight in weights.items():
                if domain in content_lower:
                    result.relevance_score *= weight
        
        # Sort by relevance score and recency
        all_results.sort(key=lambda x: (x.relevance_score, x.timestamp), reverse=True)
        
        # Remove duplicates based on content similarity
        unique_results = []
        seen_content = set()
        
        for result in all_results:
            content_hash = hash(result.content[:100])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)
        
        return unique_results
    
    def _estimate_cost(self, sources: List[str], result_count: int) -> float:
        """Estimate the cost of the search operation"""
        cost_per_source = {
            'Database': 0.0,
            'DuckDuckGo': 0.0,
            'Exa AI': 0.01,
            'SERP API': 0.005,
            'Apify': 0.02,
            'PhantomBuster': 0.015,
            'ZenRows': 0.01
        }
        
        total_cost = 0.0
        for source in sources:
            total_cost += cost_per_source.get(source, 0.005)
        
        # Add result processing cost
        total_cost += result_count * 0.001
        
        return round(total_cost, 4)

# Initialize search orchestrator
search_orchestrator = SearchOrchestrator()

# Add these endpoints to your main FastAPI app
def add_advanced_search_endpoints(app: FastAPI):
    
    @app.post("/api/search/advanced", response_model=BlendedSearchResponse)
    async def advanced_search(request: SearchRequest):
        """Execute advanced search with blending across multiple sources"""
        try:
            return await search_orchestrator.execute_search(request)
        except Exception as e:
            logger.error(f"Advanced search failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/search/modes")
    async def get_search_modes():
        """Get available search modes and their configurations"""
        return {
            "modes": list(search_orchestrator.config.search_modes.keys()),
            "configurations": search_orchestrator.config.search_modes
        }
    
    @app.get("/api/search/sources")
    async def get_search_sources():
        """Get available search sources and their status"""
        config = search_orchestrator.config
        return {
            "sources": {
                "database": {"available": True, "cost": "Free"},
                "duckduckgo": {"available": True, "cost": "Free"},
                "exa_ai": {"available": bool(config.exa_ai_api_key), "cost": "$0.01/search"},
                "serp_api": {"available": bool(config.serp_api_key), "cost": "$0.005/search"},
                "apify": {"available": bool(config.apify_api_key), "cost": "$0.02/search"},
                "phantombuster": {"available": bool(config.phantombuster_api_key), "cost": "$0.015/search"},
                "zenrows": {"available": bool(config.zenrows_api_key), "cost": "$0.01/search"}
            }
        }

# Usage: Import and call add_advanced_search_endpoints(app) in your main API file

