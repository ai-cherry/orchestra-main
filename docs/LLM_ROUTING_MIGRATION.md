# LLM Routing System Migration Guide

This guide helps you migrate from the old LLM routing implementation to the new enhanced system.

## Overview of Changes

### Old System
- Hardcoded model mappings in `core/llm_router.py`
- Simple dictionary caching
- Basic HTTP clients without pooling
- No health monitoring
- Manual async initialization

### New System
- Dynamic database-driven configuration
- Memory-bounded LRU cache with TTL
- Connection pooling with circuit breakers
- Comprehensive health monitoring
- Factory-based initialization

## Migration Steps

### 1. Update Imports

**Old:**
```python
from core.llm_router import UnifiedLLMRouter, get_llm_router
```

**New:**
```python
from core.llm_factory import get_llm_router
from core.llm_types import UseCase, ModelTier, RouterConfig
```

### 2. Router Initialization

**Old:**
```python
# Synchronous initialization
router = get_llm_router()

# Or direct instantiation
router = UnifiedLLMRouter(config)
```

**New:**
```python
# Async initialization via factory
router = await get_llm_router(dynamic=True)

# Or with custom config
config = RouterConfig(
    portkey_api_key="your-key",
    cache_ttl=7200
)
router = await get_llm_router(dynamic=True, config=config)
```

### 3. Update API Endpoints

**Old:**
```python
@router.post("/complete")
def complete(request):
    router = get_llm_router()
    response = await router.complete(request.messages)
    return response
```

**New:**
```python
from core.llm_factory import get_llm_router
from core.llm_router_base import BaseLLMRouter

async def get_router() -> BaseLLMRouter:
    return await get_llm_router(dynamic=True)

@router.post("/complete")
async def complete(
    request: CompletionRequest,
    llm_router: BaseLLMRouter = Depends(get_router)
):
    response = await llm_router.complete(
        messages=request.messages,
        use_case=request.use_case,
        tier=request.tier
    )
    return response.dict()
```

### 4. Update Configuration

**Old `.env`:**
```bash
PORTKEY_API_KEY=xxx
OPENROUTER_API_KEY=xxx
```

**New `.env`:**
```bash
# API Keys
PORTKEY_API_KEY=xxx
OPENROUTER_API_KEY=xxx

# Database (required for dynamic router)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/cherry_ai

# Performance tuning (optional)
CONNECTION_POOL_SIZE=2
CACHE_TTL=3600
CACHE_MAX_SIZE=1000
CACHE_MEMORY_LIMIT_MB=100

# Health monitoring (optional)
HEALTH_CHECK_INTERVAL=60
ENABLE_MONITORING=true
```

### 5. Database Setup

Run the setup script to create tables:

```bash
python scripts/setup_llm_configuration.py
```

### 6. Update Docker Compose

**Add to `docker-compose.yml`:**
```yaml
services:
  app:
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db/cherry_ai
      - PORTKEY_API_KEY=${PORTKEY_API_KEY}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - CONNECTION_POOL_SIZE=2
      - CACHE_TTL=3600
```

### 7. Update Application Startup

**Old `main.py`:**
```python
from fastapi import FastAPI
