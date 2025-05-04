# Memory Architecture Optimization

This document outlines the implementation of the memory architecture optimization, which includes real-time caching with Redis, persistent storage with AlloyDB, CI/CD pipeline enhancements, and monitoring capabilities.

## Architecture Overview

The memory system now follows a tiered architecture:

```
┌─────────────────────────────────────────┐
│             Client Applications          │
└───────────────────┬─────────────────────┘
                    │
┌───────────────────▼─────────────────────┐
│           Orchestra API Layer            │
└───────────────────┬─────────────────────┘
                    │
┌───────────────────▼─────────────────────┐
│         Tiered Memory Manager           │
└──┬──────────────────────┬───────────────┘
   │                      │
┌──▼──────────┐    ┌──────▼───────┐
│ Real-Time   │    │ Persistent   │
│ Layer       │    │ Layer        │
│ (Redis)     │    │ (AlloyDB)    │
└─────────────┘    └──────────────┘
```

## Components

### 1. Real-Time Layer (Redis)

The Redis SemanticCacher provides fast vector-based semantic search with configurable threshold and TTL settings.

**Key Features:**
- Semantic similarity threshold of 0.85
- Time-to-live of 3600 seconds (1 hour)
- Vector indexing for hybrid search
- YAML schema configuration

**Implementation:**
- `RedisSemanticCacheProvider` class in `packages/shared/src/memory/redis_semantic_cacher.py`
- Vector indexing for fast similarity search
- JSON serialization of metadata
- Async interface for non-blocking operations

### 2. Persistent Layer (AlloyDB)

AlloyDB provides persistent storage with vector indexing capabilities for efficient semantic search across large datasets.

**Key Features:**
- IVFFlat index for efficient vector search
- 1000 lists for balanced search speed/accuracy
- High availability with 3 replicas
- Comprehensive indexing for fast querying

**Implementation:**
- `AlloyDBMemoryProvider` class in `packages/shared/src/memory/alloydb_provider.py`
- Vector extension for PostgreSQL
- Configurable vector dimensions (default: 1536)
- Connection pooling for efficient resource utilization

### 3. CI/CD Pipeline Enhancement

The CI/CD pipeline has been enhanced with Workload Identity Federation for secure authentication with Google Cloud Platform.

**Key Features:**
- Eliminates the need for long-lived service account keys
- Secure authentication for GitHub Actions
- Fine-grained access control
- Automated Terraform deployments

**Implementation:**
- Terraform module in `terraform/modules/iam/workload_identity.tf`
- GitHub Actions workflow in `.github/workflows/terraform-deploy.yml`
- Secret Manager integration for sensitive data

### 4. Monitoring & Optimization

A comprehensive monitoring and cost tracking system has been implemented to provide visibility into resource usage and costs.

**Key Features:**
- BigQuery dataset for cost metrics
- Budget alerts at 80% of projected costs
- Custom views for memory system costs
- Visualization dashboard

**Implementation:**
- Terraform module in `terraform/modules/monitoring/cost_tracking.tf`
- Billing export to BigQuery
- Pub/Sub topic for budget alerts
- Time-partitioned tables for efficient querying

## Migration Strategy

A blue/green deployment strategy has been implemented to safely migrate from the current memory architecture to the new architecture.

**Key Phases:**
1. Preparation - Set up the new environment without affecting production
2. Testing - Validate functionality, performance, and security
3. Cutover - Switch traffic to the new environment during a maintenance window
4. Validation - Monitor for issues and verify successful migration
5. Finalization - Clean up temporary resources

**Implementation:**
- Migration script in `scripts/migration/blue_green_deployment.py`
- Automated validation with test suite
- Rollback procedure for emergency recovery
- Phased deployment with verification at each step

## Usage Guidelines

### Configuration

#### Redis SemanticCacher

```python
# Configure Redis SemanticCacher
redis_config = {
    "threshold": 0.85,  # Similarity threshold
    "ttl": 3600,        # TTL in seconds
    "index_schema": "agent_memory.yaml"
}

# Initialize provider
from packages.shared.src.memory.redis_semantic_cacher import RedisSemanticCacheProvider
redis_provider = RedisSemanticCacheProvider(config=redis_config)
await redis_provider.initialize()
```

#### AlloyDB Provider

```python
# Configure AlloyDB Provider
alloydb_config = {
    "host": "your-alloydb-host",
    "port": 5432,
    "user": "postgres",
    "password": "your-password",
    "database": "orchestra",
    "vector_dim": 1536,
    "high_availability": True
}

# Initialize provider
from packages.shared.src.memory.alloydb_provider import AlloyDBMemoryProvider
alloydb_provider = AlloyDBMemoryProvider(config=alloydb_config)
await alloydb_provider.initialize()
```

### Integration with TieredMemoryManager

To integrate these providers with the existing `TieredMemoryManager`:

```python
from packages.shared.src.memory.tiered_memory_manager import TieredMemoryManager

# Initialize TieredMemoryManager with the new providers
manager = TieredMemoryManager(config={
    "short_term_provider": redis_provider,
    "medium_term_provider": alloydb_provider,
    "long_term_enabled": True
})

# Initialize manager
await manager.initialize()
```

## Deployment Instructions

### 1. Deploy Redis with SemanticCacher

```bash
# Deploy Redis instance
./scripts/deploy_redis_with_semantic_cacher.sh

# Verify deployment
./scripts/verify_redis_deployment.sh
```

### 2. Deploy AlloyDB with Vector Indexing

```bash
# Deploy AlloyDB instance
./scripts/deploy_alloydb_with_vector.sh

# Setup vector extension and indexing
./scripts/setup_alloydb_vector_indexing.sh

# Configure high availability
./scripts/configure_alloydb_ha.sh
```

### 3. Configure CI/CD with Workload Identity

```bash
# Apply Terraform configuration
cd terraform
terraform init
terraform apply -target=module.iam_workload_identity
```

### 4. Set Up Monitoring Dashboard

```bash
# Apply monitoring configuration
terraform apply -target=module.monitoring

# Create dashboard
gcloud monitoring dashboards create --config-from-file=monitoring/dashboards/cost_dashboard.json
```

### 5. Execute Migration

```bash
# Run migration script
python scripts/migration/blue_green_deployment.py

# For scheduled maintenance window
python scripts/migration/blue_green_deployment.py --maintenance-window "2025-06-01 01:00"

# To run GPU stress tests during validation
python scripts/migration/blue_green_deployment.py --stress-test
```

## Verification and Testing

After deployment, verify the system by running the following tests:

```bash
# Basic functionality tests
./scripts/test_memory_functionality.sh

# Performance tests
./scripts/test_memory_performance.sh

# Security tests
./scripts/test_memory_security.sh
```

Expected results:
- Redis semantic cache hit rate > 85%
- Vector search p99 latency < 100ms
- AlloyDB query performance improved by 40%
- All security validations pass

## Rollback Procedure

In case of issues, use the blue/green deployment script with the rollback flag:

```bash
python scripts/migration/blue_green_deployment.py --rollback
```

This will revert to the previous architecture with minimal disruption.
