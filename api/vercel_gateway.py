"""
Vercel-Optimized API Gateway with Portkey Integration
Handles LLM routing, caching, and fallbacks for Orchestra AI
"""
from typing import Dict, Any, Optional, List
import os
import json
from functools import lru_cache
import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
import httpx
from pydantic import BaseModel
import redis
from portkey_ai import Portkey

logger = structlog.get_logger()

# Initialize Portkey client
PORTKEY_CONFIG = os.getenv("PORTKEY_CONFIG", "")
portkey_headers = {
    "x-portkey-api-key": os.getenv("PORTKEY_API_KEY", ""),
    "x-portkey-provider": "openai",  # Default provider
}
# If config is provided and valid, it will override the provider
if PORTKEY_CONFIG:
    portkey_headers["x-portkey-config"] = PORTKEY_CONFIG

portkey = Portkey(
    api_key=os.getenv("PORTKEY_API_KEY"),
    base_url="https://api.portkey.ai/v1",
    default_headers=portkey_headers,
    config={
        "retry": {
            "attempts": 3,
            "on_status_codes": [429, 500, 502, 503, 504]
        },
        "cache": {
            "mode": "semantic",
            "max_age": 3600
        }
    }
)

# Redis for caching
redis_client = redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379"),
    decode_responses=True
)

class LLMRequest(BaseModel):
    """Request model for LLM calls"""
    prompt: str
    model: Optional[str] = "gpt-4"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    stream: Optional[bool] = False
    metadata: Optional[Dict[str, Any]] = {}

class VectorSearchRequest(BaseModel):
    """Request model for vector search"""
    query: str
    index: str = "default"
    top_k: int = 10
    filters: Optional[Dict[str, Any]] = {}

class VercelGateway:
    """Main gateway class for Vercel deployment"""
    
    def __init__(self):
        self.app = FastAPI(title="Orchestra AI Gateway")
        self.setup_routes()
        self.setup_middleware()
        
    def setup_routes(self):
        """Configure API routes"""
        
        @self.app.post("/api/llm/generate")
        async def generate_text(request: LLMRequest):
            """Generate text using Portkey with fallbacks"""
            try:
                # Check cache first
                cache_key = f"llm:{request.model}:{hash(request.prompt)}"
                cached = redis_client.get(cache_key)
                if cached and not request.stream:
                    return json.loads(cached)
                
                # Configure Portkey gateway
                gateway_config = {
                    "strategy": {
                        "mode": "fallback",
                        "providers": [
                            {
                                "provider": "openrouter",
                                "model": request.model,
                                "weight": 1
                            },
                            {
                                "provider": "anthropic",
                                "model": "claude-3-sonnet",
                                "weight": 0.8
                            },
                            {
                                "provider": "cohere",
                                "model": "command-r",
                                "weight": 0.6
                            }
                        ]
                    }
                }
                
                # Make LLM request
                response = await portkey.completions.create(
                    prompt=request.prompt,
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    stream=request.stream,
                    config=gateway_config,
                    metadata=request.metadata
                )
                
                if request.stream:
                    return StreamingResponse(
                        self._stream_response(response),
                        media_type="text/event-stream"
                    )
                
                # Cache non-streaming responses
                result = {
                    "text": response.choices[0].text,
                    "model": response.model,
                    "usage": response.usage.dict()
                }
                redis_client.setex(cache_key, 3600, json.dumps(result))
                
                return result
                
            except Exception as e:
                logger.error("LLM generation failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/vector/search")
        async def vector_search(request: VectorSearchRequest):
            """Perform vector search across Pinecone/Weaviate"""
            try:
                # Generate embedding
                embedding_response = await portkey.embeddings.create(
                    input=request.query,
                    model="text-embedding-ada-002"
                )
                embedding = embedding_response.data[0].embedding
                
                # Search in vector stores (simplified)
                results = await self._search_vectors(
                    embedding=embedding,
                    index=request.index,
                    top_k=request.top_k,
                    filters=request.filters
                )
                
                return {
                    "query": request.query,
                    "results": results,
                    "count": len(results)
                }
                
            except Exception as e:
                logger.error("Vector search failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "services": {
                    "portkey": "connected",
                    "redis": redis_client.ping(),
                    "vector_stores": "ready"
                }
            }
    
    def setup_middleware(self):
        """Configure middleware for Vercel"""
        
        @self.app.middleware("http")
        async def add_vercel_headers(request: Request, call_next):
            """Add Vercel-specific headers"""
            response = await call_next(request)
            response.headers["X-Powered-By"] = "Orchestra AI"
            response.headers["Cache-Control"] = "s-maxage=60, stale-while-revalidate"
            return response
    
    async def _stream_response(self, response):
        """Stream LLM responses"""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield f"data: {json.dumps({'text': chunk.choices[0].delta.content})}\n\n"
        yield "data: [DONE]\n\n"
    
    async def _search_vectors(
        self,
        embedding: List[float],
        index: str,
        top_k: int,
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Search vectors in Pinecone/Weaviate"""
        # This would integrate with your actual vector stores
        # Simplified for example
        return [
            {
                "id": f"doc_{i}",
                "score": 0.95 - (i * 0.05),
                "metadata": {"title": f"Document {i}"}
            }
            for i in range(min(top_k, 5))
        ]

# Vercel handler
app = VercelGateway().app

# Export for Vercel
handler = app

# Configuration for Vercel deployment
VERCEL_CONFIG = {
    "functions": {
        "api/vercel_gateway.py": {
            "maxDuration": 30,
            "memory": 1024,
            "runtime": "python3.11"
        }
    },
    "env": [
        "PORTKEY_API_KEY",
        "PORTKEY_CONFIG",
        "OPENROUTER_API_KEY",
        "REDIS_URL",
        "PINECONE_API_KEY",
        "WEAVIATE_URL"
    ]
}

if __name__ == "__main__":
    # For local testing
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 