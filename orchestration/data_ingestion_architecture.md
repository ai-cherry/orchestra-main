# Data Ingestion System Architecture

## System Overview
A high-performance, modular data ingestion system designed for processing large files from multiple enterprise sources with sub-100ms query response times.

## Architecture Design

### 1. Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Web UI     │  │  REST API    │  │  GraphQL API     │   │
│  │  (Upload)   │  │  (Query)     │  │  (Subscriptions) │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Upload     │  │  Processing  │  │  Query           │   │
│  │  Service    │  │  conductor│  │  Engine          │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  File       │  │  Parser      │  │  Search          │   │
│  │  Entities   │  │  Strategies  │  │  Aggregates      │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  PostgreSQL │  │  Weaviate    │  │  S3/MinIO       │   │
│  │  (Metadata) │  │  (Vectors)   │  │  (Files)        │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2. Hot-Swappable Modules

#### Parser Module Interface
```python
class ParserInterface:
    async def parse(self, file_content: bytes, metadata: dict) -> ParsedData
    async def validate(self, file_content: bytes) -> bool
    async def extract_metadata(self, file_content: bytes) -> dict
```

#### Storage Module Interface
```python
class StorageInterface:
    async def store(self, data: Any, key: str) -> str
    async def retrieve(self, key: str) -> Any
    async def delete(self, key: str) -> bool
    async def list(self, prefix: str) -> List[str]
```

### 3. Database Schema Design

#### PostgreSQL Schema
```sql
-- File metadata and processing status
CREATE TABLE file_imports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- 'slack', 'gong', 'salesforce', etc.
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    upload_timestamp TIMESTAMPTZ DEFAULT NOW(),
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    error_message TEXT,
    s3_key VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Parsed content records
CREATE TABLE parsed_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_import_id UUID REFERENCES file_imports(id) ON DELETE CASCADE,
    content_type VARCHAR(50), -- 'message', 'transcript', 'record', etc.
    source_id VARCHAR(255), -- Original ID from source system
    content TEXT,
    metadata JSONB DEFAULT '{}',
    vector_id VARCHAR(255), -- Weaviate reference
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Query history for caching and analytics
CREATE TABLE query_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text TEXT NOT NULL,
    query_vector VECTOR(1536), -- For similarity matching
    sources_searched TEXT[],
    result_count INTEGER,
    response_time_ms INTEGER,
    cached BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_file_imports_source_type ON file_imports(source_type);
CREATE INDEX idx_file_imports_status ON file_imports(processing_status);
CREATE INDEX idx_file_imports_upload_timestamp ON file_imports(upload_timestamp DESC);
CREATE INDEX idx_parsed_content_file_import ON parsed_content(file_import_id);
CREATE INDEX idx_parsed_content_source ON parsed_content(content_type, source_id);
CREATE INDEX idx_query_history_created ON query_history(created_at DESC);
```

### 4. Weaviate Schema Design

```json
{
  "classes": [
    {
      "class": "DataContent",
      "description": "Unified content from all data sources",
      "vectorizer": "text2vec-openai",
      "properties": [
        {
          "name": "content",
          "dataType": ["text"],
          "description": "The actual content text"
        },
        {
          "name": "sourceType",
          "dataType": ["string"],
          "description": "Source system (slack, gong, salesforce, etc.)"
        },
        {
          "name": "contentType",
          "dataType": ["string"],
          "description": "Type of content (message, transcript, record)"
        },
        {
          "name": "timestamp",
          "dataType": ["date"],
          "description": "Original timestamp from source"
        },
        {
          "name": "metadata",
          "dataType": ["object"],
          "description": "Additional metadata from source"
        },
        {
          "name": "fileImportId",
          "dataType": ["string"],
          "description": "Reference to PostgreSQL file_imports"
        }
      ]
    }
  ]
}
```

### 5. Performance Optimization Strategies

#### Caching Layer
- **Redis** for query result caching
- **TTL**: 1 hour for query results
- **Invalidation**: On new data import

#### Query Optimization
```sql
-- Example optimized query with EXPLAIN ANALYZE
EXPLAIN ANALYZE
SELECT pc.*, fi.source_type, fi.filename
FROM parsed_content pc
JOIN file_imports fi ON pc.file_import_id = fi.id
WHERE fi.source_type = ANY(ARRAY['slack', 'gong'])
  AND pc.created_at > NOW() - INTERVAL '7 days'
  AND to_tsvector('english', pc.content) @@ plainto_tsquery('english', 'customer feedback')
LIMIT 100;
```

#### Batch Processing
- Process files in 10MB chunks
- Parallel processing with 4 workers per CPU core
- Vector embedding batch size: 100 documents

### 6. Event-Driven Architecture

```yaml
events:
  file_uploaded:
    payload:
      - file_id
      - filename
      - source_type
    handlers:
      - validate_file
      - queue_for_processing
  
  file_processed:
    payload:
      - file_id
      - record_count
      - processing_time
    handlers:
      - update_metadata
      - trigger_indexing
  
  indexing_completed:
    payload:
      - file_id
      - vector_count
    handlers:
      - notify_completion
      - invalidate_cache
```

### 7. API Integration Architecture

#### Circuit Breaker Configuration
```python
circuit_breaker_config = {
    "failure_threshold": 5,
    "recovery_timeout": 60,  # seconds
    "expected_exception": RequestException
}
```

#### Retry Strategy
```python
retry_config = {
    "max_attempts": 3,
    "backoff_factor": 2,
    "max_delay": 30,  # seconds
    "retry_on": [429, 500, 502, 503, 504]
}
```

### 8. Pulumi Infrastructure as Code

```python
# Lambda deployment configuration
import pulumi
import pulumi_lambda as Lambda

# Database cluster
postgres_cluster = lambda.DatabaseCluster("data-ingestion-postgres",
    database_engine="pg",
    database_engine_version="15",
    region="ewr",
    plan="Lambda-dbaas-startup-cc-1-55-2",
    cluster_size=3,
    tags=["data-ingestion", "postgres"]
)

# Kubernetes cluster for services
k8s_cluster = lambda.Kubernetes("data-ingestion-k8s",
    region="ewr",
    version="v1.28.2",
    node_pools=[{
        "node_quantity": 3,
        "plan": "vc2-4c-8gb",
        "label": "data-ingestion-workers"
    }]
)

# Object storage for files
object_storage = lambda.ObjectStorage("data-ingestion-storage",
    cluster_id=1,  # New Jersey cluster
    label="data-ingestion-files"
)
```

### 9. Monitoring & Observability

#### Key Metrics
- File processing rate (files/minute)
- Query response time (p50, p95, p99)
- Vector search latency
- Storage utilization
- API endpoint availability

#### Alerts
- Processing queue depth > 1000
- Query response time p95 > 100ms
- Storage usage > 80%
- Failed file processing rate > 5%

### 10. Security Considerations

#### Data Encryption
- At rest: AES-256 for S3/MinIO
- In transit: TLS 1.3 for all connections
- Database: Transparent Data Encryption (TDE)

#### Access Control
- API Gateway with rate limiting
- JWT tokens with 1-hour expiry
- Role-based access control (RBAC)
- Audit logging for all operations

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
- PostgreSQL schema deployment
- Weaviate cluster setup
- S3/MinIO configuration
- Basic API endpoints

### Phase 2: Parser Implementation (Week 3-4)
- Slack parser module
- Salesforce parser module
- Generic CSV/JSON parser
- File upload interface

### Phase 3: Search & Query (Week 5-6)
- Vector embedding pipeline
- Query engine implementation
- Result blending algorithm
- Caching layer

### Phase 4: API Integrations (Week 7-8)
- Slack API connector
- Salesforce API connector
- Webhook receivers
- Automated sync jobs

### Phase 5: Optimization & Scaling (Week 9-10)
- Performance tuning
- Load testing
- Monitoring setup
- Documentation

## Success Metrics

1. **Performance**
   - Query response time < 100ms (p95)
   - File processing rate > 100 files/minute
   - System availability > 99.9%

2. **Scalability**
   - Support 10TB of data without degradation
   - Handle 1000 concurrent queries
   - Process 1M files per day

3. **Accuracy**
   - Search relevance score > 0.85
   - Cross-source correlation accuracy > 90%
   - Zero data loss during processing│  │  Web UI     │  │  REST API    │  │  GraphQL API     │   │
│  │  (Upload)   │  │  (Query)     │  │  (Subscriptions) │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Upload     │  │  Processing  │  │  Query           │   │
│  │  Service    │  │  conductor│  │  Engine          │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  File       │  │  Parser      │  │  Search          │   │
│  │  Entities   │  │  Strategies  │  │  Aggregates      │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  PostgreSQL │  │  Weaviate    │  │  S3/MinIO       │   │
│  │  (Metadata) │  │  (Vectors)   │  │  (Files)        │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2. Hot-Swappable Modules

#### Parser Module Interface
```python
class ParserInterface:
    async def parse(self, file_content: bytes, metadata: dict) -> ParsedData
    async def validate(self, file_content: bytes) -> bool
    async def extract_metadata(self, file_content: bytes) -> dict
```

#### Storage Module Interface
```python
class StorageInterface:
    async def store(self, data: Any, key: str) -> str
    async def retrieve(self, key: str) -> Any
    async def delete(self, key: str) -> bool
    async def list(self, prefix: str) -> List[str]
```

### 3. Database Schema Design

#### PostgreSQL Schema
```sql
-- File metadata and processing status
CREATE TABLE file_imports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- 'slack', 'gong', 'salesforce', etc.
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    upload_timestamp TIMESTAMPTZ DEFAULT NOW(),
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    error_message TEXT,
    s3_key VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Parsed content records
CREATE TABLE parsed_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_import_id UUID REFERENCES file_imports(id) ON DELETE CASCADE,
    content_type VARCHAR(50), -- 'message', 'transcript', 'record', etc.
    source_id VARCHAR(255), -- Original ID from source system
    content TEXT,
    metadata JSONB DEFAULT '{}',
    vector_id VARCHAR(255), -- Weaviate reference
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Query history for caching and analytics
CREATE TABLE query_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text TEXT NOT NULL,
    query_vector VECTOR(1536), -- For similarity matching
    sources_searched TEXT[],
    result_count INTEGER,
    response_time_ms INTEGER,
    cached BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_file_imports_source_type ON file_imports(source_type);
CREATE INDEX idx_file_imports_status ON file_imports(processing_status);
CREATE INDEX idx_file_imports_upload_timestamp ON file_imports(upload_timestamp DESC);
CREATE INDEX idx_parsed_content_file_import ON parsed_content(file_import_id);
CREATE INDEX idx_parsed_content_source ON parsed_content(content_type, source_id);
CREATE INDEX idx_query_history_created ON query_history(created_at DESC);
```

### 4. Weaviate Schema Design

```json
{
  "classes": [
    {
      "class": "DataContent",
      "description": "Unified content from all data sources",
      "vectorizer": "text2vec-openai",
      "properties": [
        {
          "name": "content",
          "dataType": ["text"],
          "description": "The actual content text"
        },
        {
          "name": "sourceType",
          "dataType": ["string"],
          "description": "Source system (slack, gong, salesforce, etc.)"
        },
        {
          "name": "contentType",
          "dataType": ["string"],
          "description": "Type of content (message, transcript, record)"
        },
        {
          "name": "timestamp",
          "dataType": ["date"],
          "description": "Original timestamp from source"
        },
        {
          "name": "metadata",
          "dataType": ["object"],
          "description": "Additional metadata from source"
        },
        {
          "name": "fileImportId",
          "dataType": ["string"],
          "description": "Reference to PostgreSQL file_imports"
        }
      ]
    }
  ]
}
```

### 5. Performance Optimization Strategies

#### Caching Layer
- **Redis** for query result caching
- **TTL**: 1 hour for query results
- **Invalidation**: On new data import

#### Query Optimization
```sql
-- Example optimized query with EXPLAIN ANALYZE
EXPLAIN ANALYZE
SELECT pc.*, fi.source_type, fi.filename
FROM parsed_content pc
JOIN file_imports fi ON pc.file_import_id = fi.id
WHERE fi.source_type = ANY(ARRAY['slack', 'gong'])
  AND pc.created_at > NOW() - INTERVAL '7 days'
  AND to_tsvector('english', pc.content) @@ plainto_tsquery('english', 'customer feedback')
LIMIT 100;
```

#### Batch Processing
- Process files in 10MB chunks
- Parallel processing with 4 workers per CPU core
- Vector embedding batch size: 100 documents

### 6. Event-Driven Architecture

```yaml
events:
  file_uploaded:
    payload:
      - file_id
      - filename
      - source_type
    handlers:
      - validate_file
      - queue_for_processing
  
  file_processed:
    payload:
      - file_id
      - record_count
      - processing_time
    handlers:
      - update_metadata
      - trigger_indexing
  
  indexing_completed:
    payload:
      - file_id
      - vector_count
    handlers:
      - notify_completion
      - invalidate_cache
```

### 7. API Integration Architecture

#### Circuit Breaker Configuration
```python
circuit_breaker_config = {
    "failure_threshold": 5,
    "recovery_timeout": 60,  # seconds
    "expected_exception": RequestException
}
```

#### Retry Strategy
```python
retry_config = {
    "max_attempts": 3,
    "backoff_factor": 2,
    "max_delay": 30,  # seconds
    "retry_on": [429, 500, 502, 503, 504]
}
```

### 8. Pulumi Infrastructure as Code

```python
# Lambda deployment configuration
import pulumi
import pulumi_lambda as Lambda

# Database cluster
postgres_cluster = lambda.DatabaseCluster("data-ingestion-postgres",
    database_engine="pg",
    database_engine_version="15",
    region="ewr",
    plan="Lambda-dbaas-startup-cc-1-55-2",
    cluster_size=3,
    tags=["data-ingestion", "postgres"]
)

# Kubernetes cluster for services
k8s_cluster = lambda.Kubernetes("data-ingestion-k8s",
    region="ewr",
    version="v1.28.2",
    node_pools=[{
        "node_quantity": 3,
        "plan": "vc2-4c-8gb",
        "label": "data-ingestion-workers"
    }]
)

# Object storage for files
object_storage = lambda.ObjectStorage("data-ingestion-storage",
    cluster_id=1,  # New Jersey cluster
    label="data-ingestion-files"
)
```

### 9. Monitoring & Observability

#### Key Metrics
- File processing rate (files/minute)
- Query response time (p50, p95, p99)
- Vector search latency
- Storage utilization
- API endpoint availability

#### Alerts
- Processing queue depth > 1000
- Query response time p95 > 100ms
- Storage usage > 80%
- Failed file processing rate > 5%

### 10. Security Considerations

#### Data Encryption
- At rest: AES-256 for S3/MinIO
- In transit: TLS 1.3 for all connections
- Database: Transparent Data Encryption (TDE)

#### Access Control
- API Gateway with rate limiting
- JWT tokens with 1-hour expiry
- Role-based access control (RBAC)
- Audit logging for all operations

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
- PostgreSQL schema deployment
- Weaviate cluster setup
- S3/MinIO configuration
- Basic API endpoints

### Phase 2: Parser Implementation (Week 3-4)
- Slack parser module
- Salesforce parser module
- Generic CSV/JSON parser
- File upload interface

### Phase 3: Search & Query (Week 5-6)
- Vector embedding pipeline
- Query engine implementation
- Result blending algorithm
- Caching layer

### Phase 4: API Integrations (Week 7-8)
- Slack API connector
- Salesforce API connector
- Webhook receivers
- Automated sync jobs

### Phase 5: Optimization & Scaling (Week 9-10)
- Performance tuning
- Load testing
- Monitoring setup
- Documentation

## Success Metrics

1. **Performance**
   - Query response time < 100ms (p95)
   - File processing rate > 100 files/minute
   - System availability > 99.9%

2. **Scalability**
   - Support 10TB of data without degradation
   - Handle 1000 concurrent queries
   - Process 1M files per day

3. **Accuracy**
   - Search relevance score > 0.85
   - Cross-source correlation accuracy > 90%
   - Zero data loss during processing
