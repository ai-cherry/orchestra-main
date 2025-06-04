# Data Ingestion System Implementation Plan

## Integration with Existing cherry_ai System

### 1. System Integration Points

#### Existing Components to Leverage
- **LLM Intelligent Router** (`core/llm_intelligent_router.py`) - For query processing
- **Specialized Agents** (`agent/app/services/specialized_agents.py`) - For data parsing
- **Memory Manager** (`core/memory/implementations/manager.py`) - For context storage
- **Agent conductor** (`agent/app/services/agent_conductor.py`) - For workflow coordination

### 2. New Components Architecture

```python
# Core data ingestion structure
cherry_ai-main/
├── core/
│   └── data_ingestion/
│       ├── __init__.py
│       ├── interfaces/
│       │   ├── __init__.py
│       │   ├── parser.py          # ParserInterface
│       │   ├── storage.py         # StorageInterface
│       │   └── processor.py       # ProcessorInterface
│       ├── parsers/
│       │   ├── __init__.py
│       │   ├── slack_parser.py    # SlackParser
│       │   ├── gong_parser.py     # GongParser
│       │   ├── salesforce_parser.py # SalesforceParser
│       │   ├── looker_parser.py   # LookerParser
│       │   ├── hubspot_parser.py  # HubSpotParser
│       │   └── zip_handler.py     # ZipFileHandler
│       ├── processors/
│       │   ├── __init__.py
│       │   ├── file_processor.py  # Main processing conductor
│       │   ├── vector_embedder.py # Vector generation
│       │   └── metadata_extractor.py # Metadata extraction
│       └── storage/
│           ├── __init__.py
│           ├── postgres_adapter.py # PostgreSQL operations
│           ├── weaviate_adapter.py # Weaviate operations
│           └── s3_adapter.py      # File storage operations
```

### 3. Database Schema Implementation

```sql
-- Add to existing PostgreSQL schema
-- Create schema for data ingestion
CREATE SCHEMA IF NOT EXISTS data_ingestion;

-- Main tables
CREATE TABLE data_ingestion.file_imports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('slack', 'gong', 'salesforce', 'looker', 'hubspot')),
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    upload_timestamp TIMESTAMPTZ DEFAULT NOW(),
    processing_status VARCHAR(50) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    error_message TEXT,
    s3_key VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE data_ingestion.parsed_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_import_id UUID REFERENCES data_ingestion.file_imports(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL,
    source_id VARCHAR(255),
    content TEXT NOT NULL,
    content_hash VARCHAR(64) GENERATED ALWAYS AS (encode(sha256(content::bytea), 'hex')) STORED,
    metadata JSONB DEFAULT '{}',
    vector_id VARCHAR(255),
    tokens_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(file_import_id, content_hash)
);

CREATE TABLE data_ingestion.query_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash VARCHAR(64) NOT NULL,
    query_text TEXT NOT NULL,
    sources_searched TEXT[] NOT NULL,
    result_data JSONB NOT NULL,
    result_count INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(query_hash)
);

-- Performance indexes
CREATE INDEX idx_file_imports_status_created ON data_ingestion.file_imports(processing_status, created_at DESC);
CREATE INDEX idx_parsed_content_vector ON data_ingestion.parsed_content(vector_id) WHERE vector_id IS NOT NULL;
CREATE INDEX idx_parsed_content_search ON data_ingestion.parsed_content USING gin(to_tsvector('english', content));
CREATE INDEX idx_query_cache_expires ON data_ingestion.query_cache(expires_at) WHERE expires_at > NOW();

-- Partitioning for scale
CREATE TABLE data_ingestion.parsed_content_2025_01 PARTITION OF data_ingestion.parsed_content
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

### 4. API Endpoints Design

```python
# Add to agent/app/routers/data_ingestion.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Optional
import asyncio

router = APIRouter(prefix="/api/v1/data-ingestion", tags=["data-ingestion"])

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    source_type: str,
    process_immediately: bool = True
):
    """Upload files for ingestion"""
    # Implementation details below

@router.post("/upload-zip")
async def upload_zip(
    file: UploadFile = File(...),
    auto_detect_sources: bool = True
):
    """Upload ZIP file containing multiple data sources"""
    # Implementation details below

@router.get("/status/{file_id}")
async def get_processing_status(file_id: str):
    """Get processing status for uploaded file"""
    # Implementation details below

@router.post("/query")
async def query_data(
    query: str,
    sources: Optional[List[str]] = None,
    limit: int = 100
):
    """Query across all ingested data"""
    # Implementation details below
```

### 5. Parser Implementations

```python
# core/data_ingestion/parsers/slack_parser.py
from typing import Dict, List, Any
import json
from ..interfaces.parser import ParserInterface

class SlackParser(ParserInterface):
    """Parser for Slack export files"""
    
    async def parse(self, file_content: bytes, metadata: dict) -> List[Dict[str, Any]]:
        """Parse Slack JSON export"""
        data = json.loads(file_content)
        parsed_items = []
        
        # Handle different Slack export formats
        if isinstance(data, list):
            # Direct message export
            for message in data:
                parsed_items.append({
                    'content_type': 'message',
                    'source_id': message.get('ts'),
                    'content': message.get('text', ''),
                    'metadata': {
                        'user': message.get('user'),
                        'channel': metadata.get('channel'),
                        'timestamp': message.get('ts'),
                        'thread_ts': message.get('thread_ts')
                    }
                })
        
        return parsed_items
    
    async def validate(self, file_content: bytes) -> bool:
        """Validate Slack export format"""
        try:
            data = json.loads(file_content)
            return isinstance(data, (list, dict))
        except:
            return False
```

### 6. Vector Embedding Pipeline

```python
# core/data_ingestion/processors/vector_embedder.py
from typing import List, Dict
import asyncio
from weaviate import Client
import openai

class VectorEmbedder:
    def __init__(self, weaviate_client: Client, batch_size: int = 100):
        self.weaviate = weaviate_client
        self.batch_size = batch_size
    
    async def embed_content(self, content_items: List[Dict]) -> List[str]:
        """Generate and store vector embeddings"""
        vector_ids = []
        
        # Process in batches
        for i in range(0, len(content_items), self.batch_size):
            batch = content_items[i:i + self.batch_size]
            
            # Generate embeddings
            texts = [item['content'] for item in batch]
            embeddings = await self._generate_embeddings(texts)
            
            # Store in Weaviate
            with self.weaviate.batch as batch_writer:
                for item, embedding in zip(batch, embeddings):
                    vector_id = batch_writer.add_data_object(
                        data_object={
                            'content': item['content'],
                            'sourceType': item['source_type'],
                            'contentType': item['content_type'],
                            'metadata': item['metadata'],
                            'fileImportId': str(item['file_import_id'])
                        },
                        class_name='DataContent',
                        vector=embedding
                    )
                    vector_ids.append(vector_id)
        
        return vector_ids
```

### 7. Query Engine Implementation

```python
# core/data_ingestion/query_engine.py
from typing import List, Dict, Optional
import asyncio
from datetime import datetime, timedelta

class QueryEngine:
    def __init__(self, postgres_adapter, weaviate_adapter, cache_ttl_hours=1):
        self.postgres = postgres_adapter
        self.weaviate = weaviate_adapter
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
    
    async def query(
        self, 
        query_text: str, 
        sources: Optional[List[str]] = None,
        limit: int = 100
    ) -> Dict:
        """Execute cross-source query with caching"""
        
        # Check cache first
        cached_result = await self._check_cache(query_text, sources)
        if cached_result:
            return cached_result
        
        # Perform vector search
        start_time = datetime.now()
        
        # Build Weaviate query
        where_filter = None
        if sources:
            where_filter = {
                "path": ["sourceType"],
                "operator": "ContainsAny",
                "valueStringArray": sources
            }
        
        results = await self.weaviate.query.get(
            "DataContent",
            ["content", "sourceType", "contentType", "metadata", "fileImportId"]
        ).with_near_text({
            "concepts": [query_text]
        }).with_where(where_filter).with_limit(limit).do()
        
        # Blend and rank results
        blended_results = await self._blend_results(results)
        
        # Cache results
        response_time = int((datetime.now() - start_time).total_seconds() * 1000)
        await self._cache_results(query_text, sources, blended_results, response_time)
        
        return {
            "query": query_text,
            "sources": sources or "all",
            "results": blended_results,
            "response_time_ms": response_time
        }
```

### 8. Frontend Integration

```typescript
// admin-ui/src/components/data-ingestion/DataIngestionDashboard.tsx
import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Search } from 'lucide-react';

export const DataIngestionDashboard: React.FC = () => {
    const [uploadProgress, setUploadProgress] = useState<number>(0);
    const [processingStatus, setProcessingStatus] = useState<string>('idle');
    
    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        const formData = new FormData();
        acceptedFiles.forEach(file => {
            formData.append('files', file);
        });
        
        // Auto-detect source type from filename
        const sourceType = detectSourceType(acceptedFiles[0].name);
        formData.append('source_type', sourceType);
        
        try {
            const response = await fetch('/api/v1/data-ingestion/upload', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                setProcessingStatus('processing');
                // Start polling for status
                pollProcessingStatus(result.file_ids);
            }
        } catch (error) {
            console.error('Upload failed:', error);
        }
    }, []);
    
    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/json': ['.json'],
            'text/csv': ['.csv'],
            'application/zip': ['.zip'],
            'application/pdf': ['.pdf']
        }
    });
    
    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-6">Data Ingestion</h1>
            
            {/* Upload Area */}
            <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
                    ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}`}
            >
                <input {...getInputProps()} />
                <Upload className="mx-auto h-12 w-12 text-gray-400" />
                <p className="mt-2 text-sm text-gray-600">
                    {isDragActive
                        ? 'Drop files here...'
                        : 'Drag & drop files here, or click to select'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                    Supports: Slack, Gong.io, Salesforce, Looker, HubSpot exports
                </p>
            </div>
            
            {/* Processing Status */}
            {processingStatus !== 'idle' && (
                <ProcessingStatus status={processingStatus} progress={uploadProgress} />
            )}
            
            {/* Query Interface */}
            <QueryInterface />
        </div>
    );
};
```

### 9. Deployment Configuration

```yaml
# deploy/data-ingestion-stack.yaml
version: '3.8'

services:
  data-ingestion-worker:
    build:
      context: .
      dockerfile: Dockerfile.data-ingestion
    environment:
      - POSTGRES_URL=${POSTGRES_URL}
      - WEAVIATE_URL=${WEAVIATE_URL}
      - S3_BUCKET=${S3_BUCKET}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
    volumes:
      - ./data/uploads:/app/uploads
    networks:
      - cherry_ai-network

  redis-cache:
    image: redis:7-alpine
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    networks:
      - cherry_ai-network
```

### 10. Implementation Timeline

#### Week 1-2: Core Infrastructure
- [ ] PostgreSQL schema deployment
- [ ] Weaviate collection setup
- [ ] S3/MinIO configuration
- [ ] Basic API endpoints

#### Week 3-4: Parser Development
- [ ] Slack parser
- [ ] Salesforce parser
- [ ] Gong.io parser
- [ ] Looker parser
- [ ] HubSpot parser
- [ ] ZIP file handler

#### Week 5-6: Processing Pipeline
- [ ] File processor coordination
- [ ] Vector embedding pipeline
- [ ] Metadata extraction
- [ ] Error handling & retry logic

#### Week 7-8: Query System
- [ ] Query engine implementation
- [ ] Result blending algorithm
- [ ] Caching layer
- [ ] Performance optimization

#### Week 9-10: Frontend & Integration
- [ ] Upload interface
- [ ] Query interface
- [ ] Status monitoring
- [ ] API integration setup

### 11. Testing Strategy

```python
# tests/test_data_ingestion.py
import pytest
from core.data_ingestion.parsers import SlackParser, SalesforceParser

@pytest.mark.asyncio
async def test_slack_parser():
    """Test Slack export parsing"""
    parser = SlackParser()
    
    sample_data = b'[{"text": "Hello", "user": "U123", "ts": "1234567890.123"}]'
    result = await parser.parse(sample_data, {"channel": "general"})
    
    assert len(result) == 1
    assert result[0]['content'] == "Hello"
    assert result[0]['metadata']['user'] == "U123"

@pytest.mark.asyncio
async def test_query_performance():
    """Test query response time < 100ms"""
    engine = QueryEngine(postgres, weaviate)
    
    start = time.time()
    result = await engine.query("customer feedback", sources=["slack", "gong"])
    duration = (time.time() - start) * 1000
    
    assert duration < 100  # Sub-100ms requirement
    assert len(result['results']) > 0
```

## Next Steps

1. **Immediate Actions**:
   - Create database schema
   - Set up Weaviate collection
   - Implement first parser (Slack)

2. **Integration Points**:
   - Connect to existing LLM router for query processing
   - Use specialized agents for complex parsing tasks
   - Leverage memory manager for context storage

3. **Monitoring Setup**:
   - Processing queue metrics
   - Query performance tracking
   - Storage utilization alerts

This implementation plan provides a complete roadmap for building your data ingestion system with full integration into the existing cherry_ai platform.