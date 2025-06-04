# Pay Ready (Sophia) Domain - ETL & AI coordination Design

## Overview
This document outlines the architecture for integrating Airbyte Cloud, Weaviate Cloud, Prefect, and GitHub Actions into the Cherry AI system, specifically for the Pay Ready (Sophia) domain while maintaining modularity with Personal and Paragon domains.

## Domain Separation Strategy

### 1. Namespace Isolation
```yaml
domains:
  pay_ready:
    namespace: "pay_ready"
    persona: "sophia"
    database_schema: "pay_ready"
    weaviate_collections:
      - PayReadySlackMessage
      - PayReadyGongCallSegment
      - PayReadyHubSpotNote
      - PayReadySalesforceNote
    cache_prefix: "pr:"
    
  personal:
    namespace: "personal"
    database_schema: "personal"
    cache_prefix: "ps:"
    
  paragon:
    namespace: "paragon"
    database_schema: "paragon"
    cache_prefix: "pg:"
```

### 2. Database Architecture

#### PostgreSQL Schema Design
```sql
-- Pay Ready specific schema
CREATE SCHEMA IF NOT EXISTS pay_ready;

-- Domain-specific tables
CREATE TABLE pay_ready.data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(50) NOT NULL, -- 'gong', 'slack', 'hubspot', 'salesforce'
    connection_id VARCHAR(255) UNIQUE,
    config JSONB NOT NULL,
    last_sync_at TIMESTAMP,
    sync_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pay_ready.entity_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL, -- 'person', 'company'
    unified_id UUID NOT NULL,
    source_system VARCHAR(50) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    confidence_score FLOAT DEFAULT 1.0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_system, source_id)
);

CREATE TABLE pay_ready.sync_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(50) NOT NULL,
    stream_name VARCHAR(100) NOT NULL,
    last_processed_timestamp TIMESTAMP,
    last_processed_id VARCHAR(255),
    checkpoint_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_type, stream_name)
);

-- Indexes for performance
CREATE INDEX idx_entity_mappings_unified ON pay_ready.entity_mappings(unified_id);
CREATE INDEX idx_entity_mappings_source ON pay_ready.entity_mappings(source_system, source_id);
CREATE INDEX idx_sync_state_source ON pay_ready.sync_state(source_type, stream_name);
```

### 3. Weaviate Schema Design

```python
# Weaviate collections for Pay Ready domain
PAY_READY_SCHEMA = {
    "classes": [
        {
            "class": "PayReadySlackMessage",
            "description": "Slack messages for Pay Ready domain",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                    "model": "text-embedding-ada-002",
                    "type": "text"
                }
            },
            "properties": [
                {"name": "text", "dataType": ["text"]},
                {"name": "channel", "dataType": ["text"]},
                {"name": "user", "dataType": ["text"]},
                {"name": "timestamp", "dataType": ["number"]},
                {"name": "thread_id", "dataType": ["text"]},
                {"name": "unified_person_id", "dataType": ["text"]},
                {"name": "unified_company_id", "dataType": ["text"]},
                {"name": "domain", "dataType": ["text"], "defaultValue": "pay_ready"}
            ]
        },
        {
            "class": "PayReadyGongCallSegment",
            "description": "Gong call transcript segments for Pay Ready domain",
            "vectorizer": "text2vec-openai",
            "properties": [
                {"name": "text", "dataType": ["text"]},
                {"name": "call_id", "dataType": ["text"]},
                {"name": "speaker", "dataType": ["text"]},
                {"name": "start_time", "dataType": ["number"]},
                {"name": "call_date", "dataType": ["date"]},
                {"name": "unified_person_id", "dataType": ["text"]},
                {"name": "unified_company_id", "dataType": ["text"]},
                {"name": "sentiment", "dataType": ["text"]},
                {"name": "topics", "dataType": ["text[]"]},
                {"name": "domain", "dataType": ["text"], "defaultValue": "pay_ready"}
            ]
        }
    ]
}
```

## Component Architecture

### 1. ETL Pipeline Components

```python
# services/pay_ready/etl_conductor.py
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from prefect import flow, task
from shared.database.unified_postgresql_enhanced import get_unified_postgresql_enhanced
from services.weaviate_service import WeaviateService

class PayReadyETLconductor:
    """cherry_aites ETL operations for Pay Ready domain"""
    
    def __init__(self):
        self.domain = "pay_ready"
        self.postgres = None
        self.weaviate = None
        self.airbyte_client = None
        
    async def initialize(self):
        """Initialize connections and services"""
        self.postgres = await get_unified_postgresql_enhanced()
        self.weaviate = WeaviateService(config=self._get_weaviate_config())
        self.airbyte_client = await self._init_airbyte_client()
        
    @task(retries=3, retry_delay_seconds=60)
    async def trigger_airbyte_sync(self, source_type: str) -> str:
        """Trigger Airbyte sync for a specific source"""
        connection_id = await self._get_connection_id(source_type)
        job_id = await self.airbyte_client.trigger_sync(connection_id)
        
        # Store sync state
        await self.postgres.execute_raw("""
            INSERT INTO pay_ready.sync_state (source_type, stream_name, checkpoint_data)
            VALUES ($1, $2, $3)
            ON CONFLICT (source_type, stream_name) 
            DO UPDATE SET 
                checkpoint_data = $3,
                updated_at = CURRENT_TIMESTAMP
        """, source_type, f"{source_type}_sync", {"job_id": job_id, "status": "running"})
        
        return job_id
        
    @task
    async def process_new_data(self, source_type: str, batch_size: int = 100):
        """Process new data from a source"""
        last_processed = await self._get_last_processed(source_type)
        
        # Fetch new records
        new_records = await self._fetch_new_records(source_type, last_processed, batch_size)
        
        if not new_records:
            return 0
            
        # Process based on source type
        if source_type == "slack":
            await self._process_slack_messages(new_records)
        elif source_type == "gong":
            await self._process_gong_calls(new_records)
        elif source_type == "hubspot":
            await self._process_hubspot_notes(new_records)
        elif source_type == "salesforce":
            await self._process_salesforce_records(new_records)
            
        # Update checkpoint
        await self._update_checkpoint(source_type, new_records[-1])
        
        return len(new_records)
```

### 2. Entity Resolution Service

```python
# services/pay_ready/entity_resolver.py
from typing import Dict, List, Tuple, Optional
from rapidfuzz import fuzz, process
import asyncio

class PayReadyEntityResolver:
    """Handles entity resolution for Pay Ready domain"""
    
    def __init__(self, postgres_client):
        self.postgres = postgres_client
        self.cache = {}
        
    async def resolve_person(
        self, 
        name: Optional[str] = None, 
        email: Optional[str] = None,
        source_system: str = None,
        source_id: str = None
    ) -> Optional[str]:
        """Resolve a person to a unified ID"""
        
        # Try exact email match first
        if email:
            result = await self.postgres.fetchrow("""
                SELECT unified_id FROM pay_ready.entity_mappings
                WHERE entity_type = 'person' 
                AND metadata->>'email' = $1
                LIMIT 1
            """, email)
            if result:
                return str(result['unified_id'])
                
        # Try source system ID
        if source_system and source_id:
            result = await self.postgres.fetchrow("""
                SELECT unified_id FROM pay_ready.entity_mappings
                WHERE entity_type = 'person'
                AND source_system = $1
                AND source_id = $2
            """, source_system, source_id)
            if result:
                return str(result['unified_id'])
                
        # Fuzzy name matching
        if name:
            candidates = await self._get_name_candidates()
            match, score, _ = process.extractOne(
                name, 
                [c['name'] for c in candidates],
                scorer=fuzz.token_sort_ratio
            )
            if score > 85:  # Confidence threshold
                for candidate in candidates:
                    if candidate['name'] == match:
                        return str(candidate['unified_id'])
                        
        # Create new unified ID if no match
        return await self._create_new_person(name, email, source_system, source_id)
```

### 3. Workflow coordination with Prefect

```python
# workflows/pay_ready_etl_flow.py
from prefect import flow, task
from prefect.task_runners import ConcurrentTaskRunner
from datetime import datetime, timedelta
import asyncio

@flow(
    name="pay-ready-etl-pipeline",
    task_runner=ConcurrentTaskRunner(max_workers=4),
    persist_result=True,
    result_storage_key_fn=lambda context: f"pay-ready-etl-{context.flow_run.name}"
)
async def pay_ready_etl_pipeline(
    sources: List[str] = ["gong", "slack", "hubspot", "salesforce"],
    full_sync: bool = False
):
    """Main ETL pipeline for Pay Ready domain"""
    
    conductor = PayReadyETLconductor()
    await conductor.initialize()
    
    # Phase 1: Trigger Airbyte syncs in parallel
    sync_jobs = await asyncio.gather(*[
        conductor.trigger_airbyte_sync(source)
        for source in sources
    ])
    
    # Phase 2: Wait for syncs to complete
    await asyncio.gather(*[
        conductor.wait_for_sync(job_id)
        for job_id in sync_jobs
    ])
    
    # Phase 3: Process new data in parallel
    processing_results = await asyncio.gather(*[
        conductor.process_new_data(source)
        for source in sources
    ])
    
    # Phase 4: Entity resolution
    entity_resolver = PayReadyEntityResolver(conductor.postgres)
    await entity_resolver.run_resolution_batch()
    
    # Phase 5: Vector enrichment with Weaviate Transformation Agent
    await conductor.run_vector_enrichment()
    
    # Phase 6: Update analytics and cache
    await conductor.update_analytics_cache()
    
    return {
        "sources_synced": sources,
        "records_processed": sum(processing_results),
        "timestamp": datetime.utcnow().isoformat()
    }

@task(retries=2)
async def process_gong_calls(conductor, batch_size: int = 50):
    """Process Gong call transcripts"""
    new_calls = await conductor.fetch_new_gong_calls(batch_size)
    
    for call in new_calls:
        # Chunk transcript
        segments = conductor.chunk_transcript(call['transcript'])
        
        # Vectorize and store
        for segment in segments:
            await conductor.store_vector(
                collection="PayReadyGongCallSegment",
                data={
                    "text": segment['text'],
                    "call_id": call['id'],
                    "speaker": segment['speaker'],
                    "start_time": segment['start_time'],
                    "call_date": call['date'],
                    "unified_person_id": await conductor.resolve_person(segment['speaker']),
                    "unified_company_id": await conductor.resolve_company(call['account'])
                }
            )
```

### 4. GitHub Actions Integration

```yaml
# .github/workflows/pay_ready_etl.yml
name: Pay Ready ETL Pipeline

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:
    inputs:
      sources:
        description: 'Sources to sync (comma-separated)'
        required: false
        default: 'gong,slack,hubspot,salesforce'
      full_sync:
        description: 'Run full sync'
        required: false
        type: boolean
        default: false

jobs:
  etl-pipeline:
    runs-on: ubuntu-latest
    environment: production
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          pip install -r requirements/pay_ready.txt
          
      - name: Run ETL Pipeline
        env:
          AIRBYTE_CLIENT_ID: ${{ secrets.AIRBYTE_CLIENT_ID }}
          AIRBYTE_CLIENT_SECRET: ${{ secrets.AIRBYTE_CLIENT_SECRET }}
          WEAVIATE_API_KEY: ${{ secrets.WEAVIATE_API_KEY }}
          WEAVIATE_URL: ${{ secrets.WEAVIATE_URL }}
          POSTGRES_DSN: ${{ secrets.POSTGRES_DSN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          PREFECT_API_KEY: ${{ secrets.PREFECT_API_KEY }}
        run: |
          python -m workflows.pay_ready_etl_flow \
            --sources "${{ github.event.inputs.sources || 'gong,slack,hubspot,salesforce' }}" \
            --full-sync "${{ github.event.inputs.full_sync || 'false' }}"
          
      - name: Notify on Success
        if: success()
        uses: 8398a7/action-slack@v3
        with:
          status: success
          text: 'Pay Ready ETL Pipeline completed successfully'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
          
      - name: Notify on Failure
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: failure
          text: 'Pay Ready ETL Pipeline failed'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## Memory Optimization Strategy

### 1. Hierarchical Memory Structure
```python
class PayReadyMemoryManager:
    """Optimized memory management for Pay Ready domain"""
    
    def __init__(self):
        self.hot_cache = {}  # In-memory for frequent access
        self.warm_cache = None  # Redis/Dragonfly
        self.cold_storage = None  # PostgreSQL
        self.vector_store = None  # Weaviate
        
    async def store_interaction(self, interaction: Dict):
        """Store interaction with intelligent tiering"""
        
        # Hot cache for recent interactions (last 24h)
        if self._is_recent(interaction['timestamp']):
            self.hot_cache[interaction['id']] = interaction
            
        # Warm cache for medium-term (last 7 days)
        await self.warm_cache.set(
            f"pr:interaction:{interaction['id']}", 
            interaction,
            ttl=7*24*3600
        )
        
        # Cold storage for everything
        await self.cold_storage.store_interaction(interaction)
        
        # Vector store for semantic search
        if interaction.get('text'):
            await self.vector_store.index(interaction)
```

### 2. Context Pruning Strategy
```python
async def prune_context(self, context_id: str, max_size: int = 4000):
    """Intelligent context pruning for efficiency"""
    
    context = await self.get_context(context_id)
    
    # Prioritize recent and relevant information
    pruned = {
        'essential': context['essential'],  # Always keep
        'recent': self._get_recent_items(context['items'], days=7),
        'high_relevance': self._get_high_relevance_items(context['items'], threshold=0.8)
    }
    
    # Compress older items
    if len(pruned) > max_size:
        pruned['compressed'] = await self._compress_items(
            context['items'], 
            exclude=pruned['recent'] + pruned['high_relevance']
        )
    
    return pruned
```

## Integration Points

### 1. MCP Server Extensions
```python
# mcp_server/adapters/pay_ready_adapter.py
class PayReadyMCPAdapter(EnhancedMCPServerBase):
    """MCP adapter for Pay Ready domain operations"""
    
    async def handle_tool(self, tool_name: str, arguments: Dict) -> Dict:
        if tool_name == "search_customer_interactions":
            return await self.search_interactions(
                customer=arguments.get("customer"),
                date_range=arguments.get("date_range"),
                sources=arguments.get("sources", ["all"])
            )
        elif tool_name == "generate_coaching_report":
            return await self.generate_report(
                rep_name=arguments.get("rep_name"),
                period=arguments.get("period")
            )
```

### 2. API Endpoints
```python
# agent/app/routers/pay_ready.py
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/pay-ready", tags=["pay-ready"])

@router.get("/interactions/timeline")
async def get_interaction_timeline(
    customer_id: Optional[str] = Query(None),
    company_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    sources: List[str] = Query(["all"])
):
    """Get unified timeline of customer interactions"""
    conductor = PayReadyconductor()
    return await conductor.get_timeline(
        customer_id=customer_id,
        company_id=company_id,
        date_range=(start_date, end_date),
        sources=sources
    )

@router.post("/query")
async def natural_language_query(
    query: str,
    context: Optional[Dict] = None
):
    """Natural language query using Weaviate Query Agent"""
    agent = PayReadyQueryAgent()
    return await agent.query(query, context)
```

## Performance Optimizations

### 1. Parallel Processing
- Use asyncio.gather() for concurrent API calls
- Implement connection pooling for all services
- Batch operations where possible

### 2. Caching Strategy
- Hot cache: Last 24 hours of interactions
- Warm cache: Last 7 days with TTL
- Cold storage: Everything in PostgreSQL
- Vector cache: Frequently searched embeddings

### 3. Resource Management
- Circuit breakers for external APIs
- Rate limiting for Gong (3 req/sec) and Slack
- Automatic retry with exponential backoff
- Connection pool sizing based on load

## Monitoring and Observability

### 1. Metrics Collection
```python
# monitoring/pay_ready_metrics.py
class PayReadyMetrics:
    def __init__(self):
        self.prometheus_client = PrometheusClient()
        
    async def record_sync_duration(self, source: str, duration: float):
        self.prometheus_client.histogram(
            'pay_ready_sync_duration_seconds',
            duration,
            labels={'source': source}
        )
        
    async def record_processing_rate(self, source: str, records_per_second: float):
        self.prometheus_client.gauge(
            'pay_ready_processing_rate',
            records_per_second,
            labels={'source': source}
        )
```

### 2. Health Checks
```python
@router.get("/health")
async def health_check():
    """Comprehensive health check for Pay Ready services"""
    return {
        "status": "healthy",
        "services": {
            "postgres": await check_postgres_health(),
            "weaviate": await check_weaviate_health(),
            "airbyte": await check_airbyte_connections(),
            "cache": await check_cache_health()
        },
        "last_sync": await get_last_sync_times(),
        "queue_depth": await get_processing_queue_depth()
    }
```

## Security Considerations

1. **API Key Management**: All keys stored in GitHub Secrets or environment variables
2. **Data Encryption**: TLS for all external connections, encryption at rest
3. **Access Control**: Domain-specific permissions and row-level security
4. **Audit Logging**: All data access and modifications logged
5. **PII Handling**: Automatic detection and masking of sensitive data

## Next Steps

1. Implement core ETL conductor service
2. Set up Airbyte Cloud connections
3. Configure Weaviate schema and agents
4. Deploy Prefect flows
5. Set up GitHub Actions workflows
6. Implement monitoring dashboards
7. Create API documentation
8. Performance testing and optimization