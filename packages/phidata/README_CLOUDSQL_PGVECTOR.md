# Phidata with Cloud SQL PostgreSQL and PGVector

This documentation explains how to use Phidata with Cloud SQL PostgreSQL for agent storage and PGVector for vector embeddings in Orchestra.

## Overview

This implementation provides:

- Cloud SQL PostgreSQL integration for persistent agent storage
- PGVector integration for vector embeddings using VertexAI
- Support for both IAM authentication and password auth via Secret Manager
- Table partitioning by user_id or agent_id
- Optimized performance with recommended indexes

## Setup Instructions

### 1. Install Required Dependencies

```bash
pip install -r phidata_requirements.txt
pip install google-cloud-sql-connector google-cloud-secret-manager sqlalchemy pg8000
```

### 2. Configure Environment Variables

Create a `.env` file with the following variables (or set them in your environment):

```bash
# GCP Configuration
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1

# Cloud SQL Configuration
CLOUD_SQL_INSTANCE_CONNECTION_NAME=project:region:instance
CLOUD_SQL_DATABASE=phidata
CLOUD_SQL_USER=postgres

# Authentication Method
CLOUD_SQL_USE_IAM_AUTH=false  # Set to true to use IAM authentication
CLOUD_SQL_PASSWORD_SECRET_NAME=cloudsql-postgres-password  # Name of Secret Manager secret

# Vertex AI Configuration
VERTEX_EMBEDDING_MODEL=textembedding-gecko@003

# Application Environment
APP_ENV=development  # Options: development, staging, production
```

### 3. Set Up Cloud SQL Database

1. Create a Cloud SQL PostgreSQL instance in Google Cloud Console
2. Enable the pgvector extension (Cloud SQL for PostgreSQL version 15 or later required)
3. Run the setup script to create the schema and configure the database:

```bash
python scripts/setup_postgres_pgvector.py --apply
```

Use `--use-iam-auth` if using IAM authentication, or ensure your password is stored in Secret Manager.

## Usage Examples

### Basic Usage

```python
from packages.phidata.src.cloudsql_pgvector import get_pgvector_memory, get_pg_agent_storage

# Get vector memory with Vertex AI embeddings
memory = get_pgvector_memory(user_id="user-123")

# Get agent storage with partitioning
storage = get_pg_agent_storage(agent_id="agent-abc")

# Use in your agents
result = memory.search("How does Cloud SQL work?")
```

### Register a Phidata Agent with PostgreSQL Storage

```python
# See examples/register_phidata_postgres_agent.py for a complete example
from packages.agent_registry import register_agent
from packages.agent_types import AGENT_TYPE_PHIDATA

agent_config = {
    "id": "pg-agent",
    "name": "PostgreSQL Agent",
    "description": "Agent with PostgreSQL storage",
    "type": AGENT_TYPE_PHIDATA,
    "phidata_agent_class": "agno.agent.Agent",
    "llm_ref": "gpt-4-turbo",

    # CloudSQL configuration
    "cloudsql_config": {
        "project_id": "your-project-id",
        "instance_connection_name": "project:region:instance",
        # Additional config...
    },

    # Storage and memory configuration
    "storage": {"table_name": "agent_storage"},
    "memory": {"table_name": "agent_memory"}
}

register_agent(agent_config)
```

### Full Team Example

For a complete example of setting up a team of agents with PostgreSQL storage, see `examples/register_phidata_postgres_agent.py`.

## Architecture

### Component Overview

The implementation consists of:

1. **PostgreSQL Connection Handler**

   - Uses google-cloud-sql-connector for secure communication
   - Supports IAM authentication for enhanced security
   - Falls back to Secret Manager for password retrieval

2. **PgAgentStorage**

   - Handles conversation history and agent state
   - Uses table partitioning by agent_id for improved performance
   - Automatic table creation with optimized schema

3. **PgVector2**
   - Vector storage for embeddings with VertexAI integration
   - Uses textembedding-gecko@003 for high-quality embeddings
   - 768-dimensional vectors with IVFFlat indexes for fast similarity search

### Database Schema

```
db: <CLOUD_SQL_DATABASE>
  schema: llm
    table: <agent_id>_storage  # Agent conversation history
    table: <agent_id>_memory   # Agent vector memory
```

## Performance Tuning

For optimal performance with PostgreSQL:

1. **Indexes**: IVFFlat indexes are automatically created for vector columns
2. **Partitioning**: Tables are partitioned by agent_id or user_id when possible
3. **Connection Pooling**: The SQLAlchemy engine is configured with connection pooling
4. **Query Optimization**: Vector queries use approximate nearest neighbor for speed

## Monitoring and Maintenance

### Health Checks

The PhidataAgentWrapper includes a `health_check()` method that verifies:

- Connection to Cloud SQL is active
- PGVector configuration is valid
- Agent is correctly initialized

### Connection Management

Connection pooling parameters can be adjusted in the `get_cloud_sql_connection` function:

- `pool_size`: Maximum number of persistent connections (default: 5)
- `max_overflow`: Maximum number of connections above pool_size (default: 2)
- `pool_timeout`: Seconds to wait for a connection from pool (default: 30)
- `pool_recycle`: Seconds after which a connection is recycled (default: 1800)
