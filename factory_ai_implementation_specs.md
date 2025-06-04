# Factory AI Integration - Implementation Specifications

## 1. Factory Bridge Integration Details

### 1.1 Factory Bridge API Gateway Specification

```yaml
# factory_bridge/api_spec.yaml
openapi: 3.0.0
info:
  title: Factory Bridge API
  version: 1.0.0
  description: API Gateway for Factory AI integration with cherry_ai

servers:
  - url: https://api.factory.cherry_ai.ai/v1
    description: Production server
  - url: http://localhost:8090/v1
    description: Development server

paths:
  /droids/execute:
    post:
      summary: Execute task using Factory AI Droid
      operationId: executeDroidTask
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DroidTaskRequest'
      responses:
        '200':
          description: Task executed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DroidTaskResponse'
        '202':
          description: Task accepted for async execution
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AsyncTaskResponse'
        '429':
          description: Rate limit exceeded
          headers:
            X-RateLimit-Limit:
              schema:
                type: integer
            X-RateLimit-Remaining:
              schema:
                type: integer
            X-RateLimit-Reset:
              schema:
                type: integer

  /context/sync:
    post:
      summary: Synchronize context between systems
      operationId: syncContext
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ContextSyncRequest'
      responses:
        '200':
          description: Context synchronized successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ContextSyncResponse'

components:
  schemas:
    DroidTaskRequest:
      type: object
      required:
        - task_type
        - context
        - priority
      properties:
        task_type:
          type: string
          enum: [architect, code, debug, reliability, knowledge]
        context:
          $ref: '#/components/schemas/TaskContext'
        priority:
          type: string
          enum: [low, normal, high, critical]
        options:
          type: object
          properties:
            timeout_ms:
              type: integer
              default: 30000
            fallback_to_roo:
              type: boolean
              default: true
            cache_enabled:
              type: boolean
              default: true

    TaskContext:
      type: object
      properties:
        project_id:
          type: string
        file_paths:
          type: array
          items:
            type: string
        code_context:
          type: string
        metadata:
          type: object

    DroidTaskResponse:
      type: object
      properties:
        task_id:
          type: string
        status:
          type: string
          enum: [completed, failed, partial]
        result:
          type: object
        execution_time_ms:
          type: integer
        droid_used:
          type: string
        cache_hit:
          type: boolean
```

### 1.2 Factory Bridge Implementation

```python
# factory_bridge/bridge_server.py
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from typing import Dict, Any, Optional
import redis.asyncio as redis
from prometheus_client import Counter, Histogram, Gauge
import structlog

logger = structlog.get_logger()

# Metrics
request_counter = Counter('factory_bridge_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('factory_bridge_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
active_connections = Gauge('factory_bridge_active_connections', 'Active connections')

class FactoryBridgeServer:
    def __init__(self):
        self.app = FastAPI(title="Factory Bridge API", version="1.0.0")
        self.redis_client = None
        self.droid_manager = DroidManager()
        self.context_manager = ContextManager()
        self.rate_limiter = RateLimiter()
        self.circuit_breaker = CircuitBreaker()
        
        self._setup_middleware()
        self._setup_routes()
        
    def _setup_middleware(self):
        """Configure middleware for the API"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @self.app.middleware("http")
        async def add_metrics(request: Request, call_next):
            """Track request metrics"""
            active_connections.inc()
            start_time = asyncio.get_event_loop().time()
            
            try:
                response = await call_next(request)
                request_counter.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    status=response.status_code
                ).inc()
                return response
            finally:
                duration = asyncio.get_event_loop().time() - start_time
                request_duration.labels(
                    method=request.method,
                    endpoint=request.url.path
                ).observe(duration)
                active_connections.dec()
    
    def _setup_routes(self):
        """Configure API routes"""
        
        @self.app.post("/v1/droids/execute")
        async def execute_droid_task(
            request: DroidTaskRequest,
            auth: AuthContext = Depends(self.authenticate)
        ):
            """Execute a task using Factory AI Droid"""
            # Rate limiting
            if not await self.rate_limiter.check_limit(auth.user_id):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            # Circuit breaker check
            if not self.circuit_breaker.is_closed():
                logger.warning("Circuit breaker open, falling back to Roo")
                if request.options.fallback_to_roo:
                    return await self._fallback_to_roo(request)
                raise HTTPException(status_code=503, detail="Service temporarily unavailable")
            
            try:
                # Check cache
                if request.options.cache_enabled:
                    cache_key = self._generate_cache_key(request)
                    if cached_result := await self.redis_client.get(cache_key):
                        return DroidTaskResponse(
                            task_id=f"cached-{cache_key[:8]}",
                            status="completed",
                            result=json.loads(cached_result),
                            cache_hit=True
                        )
                
                # Execute task
                result = await self.circuit_breaker.call(
                    self.droid_manager.execute_task,
                    request
                )
                
                # Cache result
                if request.options.cache_enabled and result.status == "completed":
                    await self.redis_client.setex(
                        cache_key,
                        300,  # 5 minute TTL
                        json.dumps(result.result)
                    )
                
                return result
                
            except Exception as e:
                logger.error(f"Droid execution failed: {e}")
                if request.options.fallback_to_roo:
                    return await self._fallback_to_roo(request)
                raise HTTPException(status_code=500, detail=str(e))
```

## 2. Enhanced MCP Server Adapters

### 2.1 Factory-MCP Adapter Architecture

```python
# mcp_server/adapters/factory_adapter_base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import asyncio
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()

@dataclass
class AdapterConfig:
    """Configuration for Factory-MCP adapter"""
    mcp_server_name: str
    droid_type: str
    capabilities: List[str]
    performance_profile: Dict[str, Any]
    fallback_enabled: bool = True
    cache_ttl: int = 300

class FactoryMCPAdapter(ABC):
    """Base adapter for bridging Factory AI Droids with MCP servers"""
    
    def __init__(self, config: AdapterConfig):
        self.config = config
        self.mcp_client = self._create_mcp_client()
        self.factory_client = self._create_factory_client()
        self.translator = MessageTranslator()
        self.performance_monitor = PerformanceMonitor()
        
    @abstractmethod
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request through the adapter"""
        pass
        
    async def _execute_with_monitoring(self, func, *args, **kwargs):
        """Execute function with performance monitoring"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            result = await func(*args, **kwargs)
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.performance_monitor.record_execution(
                adapter=self.config.mcp_server_name,
                droid=self.config.droid_type,
                execution_time_ms=execution_time,
                success=True
            )
            
            return result
            
        except Exception as e:
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.performance_monitor.record_execution(
                adapter=self.config.mcp_server_name,
                droid=self.config.droid_type,
                execution_time_ms=execution_time,
                success=False,
                error=str(e)
            )
            
            raise

# Specific adapter implementations
class conductorAdapter(FactoryMCPAdapter):
    """Adapter for conductor MCP server with Architect Droid"""
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process coordination request"""
        # Translate MCP request to Factory format
        factory_request = self.translator.mcp_to_factory(
            request,
            target_droid='architect',
            context_requirements=['system_design', 'architecture']
        )
        
        # Add conductor-specific enhancements
        factory_request['optimization_hints'] = {
            'prefer_modular_design': True,
            'target_platform': 'vultr',
            'use_pulumi': True
        }
        
        # Execute through Factory AI
        factory_response = await self._execute_with_monitoring(
            self.factory_client.execute,
            factory_request
        )
        
        # Translate back to MCP format
        mcp_response = self.translator.factory_to_mcp(factory_response)
        
        # Enhance with MCP-specific data
        mcp_response['mcp_metadata'] = {
            'server': 'conductor',
            'droid_used': 'architect',
            'execution_time_ms': factory_response.get('execution_time_ms', 0)
        }
        
        return mcp_response

class ToolsAdapter(FactoryMCPAdapter):
    """Adapter for Tools MCP server with Code/Debug Droids"""
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process tools request"""
        # Determine which droid to use
        droid_type = self._select_droid(request)
        
        # Translate request
        factory_request = self.translator.mcp_to_factory(
            request,
            target_droid=droid_type,
            context_requirements=self._get_context_requirements(droid_type)
        )
        
        # Execute with appropriate droid
        if droid_type == 'code':
            response = await self._execute_code_droid(factory_request)
        else:  # debug
            response = await self._execute_debug_droid(factory_request)
            
        return self.translator.factory_to_mcp(response)
    
    def _select_droid(self, request: Dict[str, Any]) -> str:
        """Select appropriate droid based on request type"""
        if request.get('operation') in ['generate', 'refactor', 'optimize']:
            return 'code'
        elif request.get('operation') in ['diagnose', 'profile', 'analyze']:
            return 'debug'
        else:
            # Default to code droid for general operations
            return 'code'
```

### 2.2 Message Translation Layer

```python
# mcp_server/adapters/message_translator.py
class MessageTranslator:
    """Translates messages between MCP and Factory AI formats"""
    
    def __init__(self):
        self.schema_validator = SchemaValidator()
        self.context_enricher = ContextEnricher()
        
    def mcp_to_factory(
        self, 
        mcp_message: Dict[str, Any],
        target_droid: str,
        context_requirements: List[str]
    ) -> Dict[str, Any]:
        """Convert MCP message to Factory AI format"""
        # Validate MCP message
        self.schema_validator.validate_mcp(mcp_message)
        
        # Extract core data
        factory_message = {
            'droid_type': target_droid,
            'operation': self._map_operation(mcp_message.get('method')),
            'parameters': self._map_parameters(mcp_message.get('params', {})),
            'context': self._build_context(mcp_message, context_requirements),
            'metadata': {
                'source': 'mcp',
                'original_method': mcp_message.get('method'),
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        # Enrich with additional context
        factory_message = self.context_enricher.enrich(factory_message)
        
        return factory_message
    
    def factory_to_mcp(self, factory_response: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Factory AI response to MCP format"""
        # Validate Factory response
        self.schema_validator.validate_factory(factory_response)
        
        # Map to MCP format
        mcp_response = {
            'result': self._extract_result(factory_response),
            'metadata': {
                'droid_used': factory_response.get('droid_type'),
                'execution_time_ms': factory_response.get('execution_time_ms'),
                'cache_hit': factory_response.get('cache_hit', False)
            }
        }
        
        # Add any warnings or additional info
        if warnings := factory_response.get('warnings'):
            mcp_response['warnings'] = warnings
            
        return mcp_response
    
    def _map_operation(self, mcp_method: str) -> str:
        """Map MCP method to Factory operation"""
        mapping = {
            'cherry_aite': 'design_system',
            'generate_code': 'generate',
            'debug_issue': 'diagnose',
            'deploy': 'validate_deployment',
            'store_memory': 'index_knowledge'
        }
        return mapping.get(mcp_method, mcp_method)
```

## 3. Unified Context Management Implementation

### 3.1 Context Synchronization Engine

```python
# context_management/sync_engine.py
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import hashlib
import json
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger()

@dataclass
class ContextVersion:
    """Represents a version of context"""
    id: str
    version: int
    content: Dict[str, Any]
    source: str  # 'roo', 'factory', 'unified'
    timestamp: datetime
    checksum: str
    parent_id: Optional[str] = None
    
    def calculate_checksum(self) -> str:
        """Calculate checksum of content"""
        content_str = json.dumps(self.content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

class ContextSynchronizationEngine:
    """
    Manages context synchronization between Roo and Factory AI
    Implements CRDT-like conflict resolution
    """
    
    def __init__(self):
        self.roo_provider = RooContextProvider()
        self.factory_provider = FactoryContextProvider()
        self.version_store = ContextVersionStore()
        self.conflict_resolver = ConflictResolver()
        self.event_bus = EventBus()
        self.sync_lock = asyncio.Lock()
        
    async def start_sync_loop(self, interval_seconds: int = 30):
        """Start continuous synchronization loop"""
        while True:
            try:
                await self.sync_contexts()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
                await asyncio.sleep(interval_seconds * 2)  # Back off on error
    
    async def sync_contexts(self) -> ContextVersion:
        """
        Perform context synchronization with conflict resolution
        """
        async with self.sync_lock:
            logger.info("Starting context synchronization")
            
            # Get current contexts
            roo_context = await self.roo_provider.get_current_context()
            factory_context = await self.factory_provider.get_current_context()
            
            # Get last unified version
            last_unified = await self.version_store.get_latest_unified()
            
            # Detect changes
            roo_changes = self._detect_changes(last_unified, roo_context)
            factory_changes = self._detect_changes(last_unified, factory_context)
            
            # Resolve conflicts
            unified_context = await self.conflict_resolver.resolve(
                base=last_unified,
                roo_changes=roo_changes,
                factory_changes=factory_changes
            )
            
            # Create new version
            new_version = ContextVersion(
                id=self._generate_version_id(),
                version=last_unified.version + 1 if last_unified else 1,
                content=unified_context,
                source='unified',
                timestamp=datetime.utcnow(),
                checksum=self._calculate_checksum(unified_context),
                parent_id=last_unified.id if last_unified else None
            )
            
            # Store version
            await self.version_store.store(new_version)
            
            # Update both systems
            await self._propagate_changes(new_version)
            
            # Emit sync event
            await self.event_bus.emit(ContextSyncCompleteEvent(
                version_id=new_version.id,
                changes_count=len(roo_changes) + len(factory_changes)
            ))
            
            logger.info(f"Context sync completed: version {new_version.version}")
            return new_version
    
    def _detect_changes(
        self, 
        base: Optional[ContextVersion], 
        current: Dict[str, Any]
    ) -> List[ContextChange]:
        """Detect changes between base and current context"""
        if not base:
            # Everything is new
            return [
                ContextChange(
                    type='add',
                    path=key,
                    value=value
                )
                for key, value in current.items()
            ]
        
        changes = []
        base_content = base.content
        
        # Check for additions and modifications
        for key, value in current.items():
            if key not in base_content:
                changes.append(ContextChange(type='add', path=key, value=value))
            elif base_content[key] != value:
                changes.append(ContextChange(
                    type='modify', 
                    path=key, 
                    old_value=base_content[key],
                    value=value
                ))
        
        # Check for deletions
        for key in base_content:
            if key not in current:
                changes.append(ContextChange(
                    type='delete', 
                    path=key, 
                    old_value=base_content[key]
                ))
        
        return changes
    
    async def _propagate_changes(self, unified_version: ContextVersion):
        """Propagate unified context back to both systems"""
        # Update Roo
        await self.roo_provider.update_context(unified_version.content)
        
        # Update Factory
        await self.factory_provider.update_context(unified_version.content)
        
        # Update caches
        await self._update_caches(unified_version)

class ConflictResolver:
    """
    Resolves conflicts between Roo and Factory context changes
    Uses a deterministic algorithm to ensure consistency
    """
    
    def __init__(self):
        self.resolution_strategies = {
            'timestamp': self._resolve_by_timestamp,
            'source_priority': self._resolve_by_source_priority,
            'merge': self._resolve_by_merge
        }
        self.default_strategy = 'source_priority'
        
    async def resolve(
        self,
        base: Optional[ContextVersion],
        roo_changes: List[ContextChange],
        factory_changes: List[ContextChange]
    ) -> Dict[str, Any]:
        """Resolve conflicts and produce unified context"""
        # Start with base or empty context
        unified = base.content.copy() if base else {}
        
        # Group changes by path
        roo_by_path = {c.path: c for c in roo_changes}
        factory_by_path = {c.path: c for c in factory_changes}
        
        # Process all unique paths
        all_paths = set(roo_by_path.keys()) | set(factory_by_path.keys())
        
        for path in all_paths:
            roo_change = roo_by_path.get(path)
            factory_change = factory_by_path.get(path)
            
            if roo_change and factory_change:
                # Conflict - use resolution strategy
                strategy = self._determine_strategy(path)
                resolution = await self.resolution_strategies[strategy](
                    path, roo_change, factory_change
                )
                self._apply_resolution(unified, resolution)
            elif roo_change:
                # Only Roo changed
                self._apply_change(unified, roo_change)
            else:
                # Only Factory changed
                self._apply_change(unified, factory_change)
        
        return unified
    
    def _resolve_by_source_priority(
        self, 
        path: str, 
        roo_change: ContextChange, 
        factory_change: ContextChange
    ) -> ContextChange:
        """Roo takes priority for conflicts"""
        logger.info(f"Conflict at {path}: choosing Roo change")
        return roo_change
```

### 3.2 Vector Store Integration

```python
# context_management/vector_integration.py
import weaviate
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import asyncio
from concurrent.futures import ThreadPoolExecutor

class EnhancedVectorStore:
    """
    Enhanced Weaviate integration for Factory AI context
    """
    
    def __init__(self):
        self.client = weaviate.Client(
            url=os.getenv("WEAVIATE_URL"),
            auth_client_secret=weaviate.AuthApiKey(
                api_key=os.getenv("WEAVIATE_API_KEY")
            )
        )
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.batch_size = 100
        
    async def index_unified_context(self, context: Dict[str, Any], version_id: str):
        """Index unified context with optimized batching"""
        # Prepare documents
        documents = self._prepare_documents(context, version_id)
        
        # Batch process for efficiency
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i:i + self.batch_size]
            await self._index_batch(batch)
            
        # Update indices
        await self._update_indices(version_id)
        
    def _prepare_documents(self, context: Dict[str, Any], version_id: str) -> List[Dict]:
        """Prepare context for vector indexing"""
        documents = []
        
        def flatten_context(obj, prefix=''):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, (dict, list)):
                        flatten_context(value, new_prefix)
                    else:
                        documents.append({
                            'content': f"{new_prefix}: {value}",
                            'path': new_prefix,
                            'value': str(value),
                            'version_id': version_id,
                            'context_type': self._determine_type(new_prefix),
                            'source_system': 'unified'
                        })
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    flatten_context(item, f"{prefix}[{i}]")
        
        flatten_context(context)
        return documents
    
    async def _index_batch(self, documents: List[Dict]):
        """Index a batch of documents with embeddings"""
        # Generate embeddings in parallel
        contents = [doc['content'] for doc in documents]
        embeddings = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.encoder.encode,
            contents
        )
        
        # Prepare batch
        with self.client.batch as batch:
            for doc, embedding in zip(documents, embeddings):
                batch.add_data_object(
                    data_object=doc,
                    class_name="FactoryContext",
                    vector=embedding.tolist()
                )
        
    async def search_context(
        self, 
        query: str, 
        filters: Optional[Dict] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Search context with hybrid search (vector + keyword)"""
        # Generate query embedding
        query_vector = await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.encoder.encode,
            [query]
        )
        
        # Build where filter
        where_filter = self._build_where_filter(filters) if filters else None
        
        # Perform hybrid search
        results = (
            self.client.query
            .get("FactoryContext", ["content", "path", "value", "context_type", "version_id"])
            .with_hybrid(
                query=query,
                vector=query_vector[0].tolist(),
                alpha=0.75  # 75% vector, 25% keyword
            )
            .with_where(where_filter)
            .with_limit(limit)
            .with_additional(["score", "explainScore"])
            .do()
        )
        
        return self._process_search_results(results)
```

## 4. Performance Optimization Implementation

### 4.1 Advanced Caching System

```python
# performance/advanced_cache.py
from typing import Any, Optional, Dict, List
import asyncio
import redis.asyncio as redis
import pickle
import json
from datetime import datetime, timedelta
import hashlib

class HierarchicalCache:
    """
    Implements a hierarchical caching system with L1 (memory), 
    L2 (Redis), and L3 (PostgreSQL) layers
    """
    
    def __init__(self):
        # L1: In-memory LRU cache
        self.l1_cache = LRUCache(max_size=1000)
        self.l1_stats = CacheStats("l1")
        
        # L2: Redis cache
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=False  # For binary data
        )
        self.l2_stats = CacheStats("l2")
        
        # L3: PostgreSQL cache
        self.pg_cache = PostgreSQLCache()
        self.l3_stats = CacheStats("l3")
        
        # Cache warming
        self.warmer = CacheWarmer(self)
        
    async def get(self, key: str, context: Optional[Dict] = None) -> Optional[Any]:
        """
        Get value from cache with context-aware key generation
        """
        # Generate context-aware key
        full_key = self._generate_key(key, context)
        
        # L1 lookup
        if value := self.l1_cache.get(full_key):
            self.l1_stats.record_hit()
            return value
        
        # L2 lookup
        if value := await self._get_from_redis(full_key):
            self.l1_stats.record_miss()
            self.l2_stats.record_hit()
            # Promote to L1
            self.l1_cache.put(full_key, value)
            return value
        
        # L3 lookup
        if value := await self.pg_cache.get(full_key):
            self.l2_stats.record_miss()
            self.l3_stats.record_hit()
            # Promote to L2 and L1
            await self._set_in_redis(full_key, value, ttl=300)
            self.l1_cache.put(full_key, value)
            return value
        
        # Cache miss
        self.l3_stats.record_miss()
        return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        context: Optional[Dict] = None,
        ttl: Optional[int] = None
    ):
        """Set value in all cache layers"""
        full_key = self._generate_key(key, context)
        
        # Set in all layers
        self.l1_cache.put(full_key, value)
        await self._set_in_redis(full_key, value, ttl or 300)
        await self.pg_cache.set(full_key, value, ttl or 3600)
        
        # Trigger cache warming for related keys
        asyncio.create_task(self.warmer.warm_related_keys(full_key, value))
    
    def _generate_key(self, base_key: str, context: Optional[Dict]) -> str:
        """Generate cache key with context"""
        if not context:
            return base_key
            
        # Sort context for consistent keys
        context_str = json.dumps(context, sort_keys=True)
        context_hash = hashlib.md5(context_str.encode()).hexdigest()[:8]
        return f"{base_key}:{context_hash}"
    
    async def _get_from_redis(self, key: str) -> Optional[Any]:
        """Get value from Redis with deserialization"""
        try:
            if data := await self.redis_client.get(key):
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
        return None
    
    async def _set_in_redis(self, key: str, value: Any, ttl: int):
        """Set value in Redis with serialization"""
        try:
            data =