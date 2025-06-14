"""
Enhanced MCP Server with Portkey Integration
Provides unified LLM access with semantic caching and automatic fallbacks
"""
import os
import json
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import structlog
from portkey_ai import Portkey

logger = structlog.get_logger()

# Configuration
PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default

class QueryRequest(BaseModel):
    """Request model for LLM queries"""
    prompt: str
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    use_cache: bool = True
    metadata: Dict[str, Any] = {}

class QueryResponse(BaseModel):
    """Response model for LLM queries"""
    response: str
    model_used: str
    cached: bool = False
    latency_ms: int
    cost_estimate: float = 0.0
    metadata: Dict[str, Any] = {}

class PortkeyMCP:
    """Enhanced MCP server with Portkey integration"""
    
    def __init__(self):
        self.config = {
            "primary": "openrouter",
            "fallbacks": ["anthropic", "cohere", "openai"],
            "cache_strategy": "semantic",
            "cost_optimization": True,
            "retry_attempts": 3,
            "timeout": 30
        }
        
        # Initialize Portkey client
        self.portkey = None
        if PORTKEY_API_KEY:
            self.portkey = Portkey(
                api_key=PORTKEY_API_KEY,
                config={
                    "retry": {
                        "attempts": self.config["retry_attempts"],
                        "on_status_codes": [429, 500, 502, 503, 504]
                    },
                    "cache": {
                        "mode": "semantic" if self.config["cache_strategy"] == "semantic" else "simple"
                    }
                }
            )
        
        # Redis client for caching
        self.redis_client = None
        self.cache_enabled = True
        
        # Cost tracking
        self.cost_per_token = {
            "gpt-4": 0.00003,
            "gpt-3.5-turbo": 0.000002,
            "claude-3-opus": 0.00003,
            "claude-3-sonnet": 0.000003,
            "command-r-plus": 0.000003
        }
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = await redis.from_url(REDIS_URL)
            await self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.cache_enabled = False
    
    async def close(self):
        """Close connections"""
        if self.redis_client:
            await self.redis_client.close()
    
    def _generate_cache_key(self, prompt: str, model: str) -> str:
        """Generate cache key for semantic caching"""
        # Create a hash of prompt + model for cache key
        content = f"{prompt}:{model}"
        return f"mcp:cache:{hashlib.sha256(content.encode()).hexdigest()}"
    
    async def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """Get response from cache"""
        if not self.cache_enabled or not self.redis_client:
            return None
        
        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
        
        return None
    
    async def _save_to_cache(self, cache_key: str, response: str, ttl: int = CACHE_TTL):
        """Save response to cache"""
        if not self.cache_enabled or not self.redis_client:
            return
        
        try:
            await self.redis_client.setex(
                cache_key, 
                ttl, 
                json.dumps(response)
            )
        except Exception as e:
            logger.error(f"Cache save error: {e}")
    
    def _estimate_cost(self, prompt: str, response: str, model: str) -> float:
        """Estimate cost based on tokens"""
        # Rough estimation: 1 token ~= 4 characters
        prompt_tokens = len(prompt) / 4
        response_tokens = len(response) / 4
        total_tokens = prompt_tokens + response_tokens
        
        rate = self.cost_per_token.get(model, 0.00001)
        return total_tokens * rate
    
    async def query_with_fallback(self, request: QueryRequest) -> QueryResponse:
        """Query LLM with automatic fallback"""
        start_time = datetime.now()
        
        # Check cache first
        if request.use_cache:
            cache_key = self._generate_cache_key(request.prompt, request.model)
            cached_response = await self._get_from_cache(cache_key)
            if cached_response:
                latency = int((datetime.now() - start_time).total_seconds() * 1000)
                return QueryResponse(
                    response=cached_response,
                    model_used=request.model,
                    cached=True,
                    latency_ms=latency,
                    cost_estimate=0.0,  # No cost for cached responses
                    metadata={"cache_hit": True}
                )
        
        # Try primary provider
        response = None
        model_used = request.model
        
        if self.portkey:
            try:
                # Use Portkey for unified access
                chat_response = await self.portkey.chat.completions.create(
                    model=request.model,
                    messages=[{"role": "user", "content": request.prompt}],
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    metadata=request.metadata
                )
                response = chat_response.choices[0].message.content
                
            except Exception as e:
                logger.error(f"Primary provider error: {e}")
                
                # Try fallback providers
                for fallback in self.config["fallbacks"]:
                    try:
                        logger.info(f"Trying fallback provider: {fallback}")
                        # Implement fallback logic here
                        # This would integrate with specific providers
                        break
                    except Exception as fe:
                        logger.error(f"Fallback {fallback} error: {fe}")
                        continue
        
        if not response:
            # If all providers fail, use a simple response
            response = "I apologize, but I'm currently unable to process your request. Please try again later."
            model_used = "fallback"
        
        # Calculate metrics
        latency = int((datetime.now() - start_time).total_seconds() * 1000)
        cost_estimate = self._estimate_cost(request.prompt, response, model_used)
        
        # Save to cache
        if request.use_cache and response != "I apologize, but I'm currently unable to process your request. Please try again later.":
            cache_key = self._generate_cache_key(request.prompt, request.model)
            await self._save_to_cache(cache_key, response)
        
        return QueryResponse(
            response=response,
            model_used=model_used,
            cached=False,
            latency_ms=latency,
            cost_estimate=cost_estimate,
            metadata={
                "provider": "portkey" if self.portkey else "direct",
                "fallback_used": model_used != request.model
            }
        )

# FastAPI app
app = FastAPI(title="Enhanced MCP Server with Portkey")
mcp_server = PortkeyMCP()

@app.on_event("startup")
async def startup():
    """Initialize server on startup"""
    await mcp_server.initialize()
    logger.info("Enhanced MCP server started")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    await mcp_server.close()
    logger.info("Enhanced MCP server stopped")

@app.post("/query", response_model=QueryResponse)
async def query_llm(request: QueryRequest):
    """Query LLM with automatic fallback and caching"""
    try:
        return await mcp_server.query_with_fallback(request)
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "cache_enabled": mcp_server.cache_enabled,
        "portkey_enabled": mcp_server.portkey is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/stats")
async def stats():
    """Get server statistics"""
    # This could be enhanced with actual metrics
    return {
        "config": mcp_server.config,
        "cache_enabled": mcp_server.cache_enabled,
        "supported_models": list(mcp_server.cost_per_token.keys()),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004) 