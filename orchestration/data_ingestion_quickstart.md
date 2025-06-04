# Data Ingestion System - Quick Start Guide

## Overview
This guide will help you quickly set up and start using the data ingestion system for importing files from Slack, Gong.io, Salesforce, Looker, and HubSpot.

## Prerequisites

1. **System Requirements**:
   - PostgreSQL 15+ with pgvector extension
   - Weaviate 1.23+
   - Redis 7+
   - Python 3.11+
   - Node.js 18+
   - Docker & Docker Compose

2. **API Keys Required**:
   - OpenAI API key (for embeddings)
   - S3/MinIO credentials
   - (Optional) API keys for each data source

## Quick Start Steps

### 1. Deploy Infrastructure with Pulumi

```bash
# Install Pulumi
curl -fsSL https://get.pulumi.com | sh

# Set up Vultr provider
export VULTR_API_KEY="your-vultr-api-key"

# Deploy infrastructure
cd infrastructure/data-ingestion
pulumi up
```

### 2. Initialize Database

```bash
# Run database migrations
python scripts/migrate_database.py

# Create initial indexes
python scripts/create_indexes.py
```

### 3. Start Services

```bash
# Using Docker Compose
docker-compose -f deploy/data-ingestion-stack.yaml up -d

# Or run locally for development
python -m uvicorn agent.app.main:app --reload --port 8000
```

### 4. Access the Web Interface

Open your browser to: `https://cherry-ai.me/data-ingestion`

## Usage Examples

### Manual File Upload

1. **Upload a Slack Export**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/data-ingestion/upload \
     -F "files=@slack-export-2025.zip" \
     -F "source_type=slack"
   ```

2. **Upload Multiple Files**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/data-ingestion/upload \
     -F "files=@salesforce-accounts.csv" \
     -F "files=@salesforce-contacts.csv" \
     -F "source_type=salesforce"
   ```

### Query Data

1. **Simple Query**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/data-ingestion/query \
     -H "Content-Type: application/json" \
     -d '{
       "query": "customer feedback about pricing",
       "sources": ["slack", "gong"],
       "limit": 50
     }'
   ```

2. **Cross-Source Query**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/data-ingestion/query \
     -H "Content-Type: application/json" \
     -d '{
       "query": "deals closed last quarter",
       "sources": ["salesforce", "hubspot", "slack"],
       "limit": 100
     }'
   ```

### Check Processing Status

```bash
curl http://localhost:8000/api/v1/data-ingestion/status/{file_id}
```

## File Format Examples

### Slack Export Structure
```
slack-export/
├── channels.json
├── users.json
├── general/
