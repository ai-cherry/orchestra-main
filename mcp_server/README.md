# AI Orchestra MCP Server Implementation

## Overview

The Model Context Protocol (MCP) implementation for AI Orchestra provides a comprehensive set of servers that enable Claude 4 and other AI assistants to interact with the project's infrastructure through a standardized protocol.

## Architecture

```
┌─────────────────┐
│   Claude 4      │
│  (MCP Client)   │
└────────┬────────┘
         │
    ┌────▼────┐
    │   MCP   │
    │ Gateway │ :8000
    └────┬────┘
         │
    ┌────▼──────────────────────────┐
    │      MCP Servers              │
    ├───────────────────────────────┤
    │ • Cloud Run MCP    :8001      │
    │ • Secrets MCP      :8002      │
    │ • Memory MCP       :8003      │
    │ • Orchestrator MCP :8004      │
    └───────────────────────────────┘
```

## Quick Start

### 1. Prerequisites

```bash
# Install required packages
pip install -r requirements.txt

# Ensure GCP authentication is set up
gcloud auth application-default login

# Set environment variables
export GCP_PROJECT_ID=your-project-id
export GCP_REGION=us-central1
```

### 2. Start All MCP Servers

```bash
# Start the entire MCP system
./start_mcp_system.sh

# Check system health
curl http://localhost:8000/health
```

### 3. Monitor System Health

```bash
# Real-time health monitoring
python mcp_server/monitoring/health_dashboard.py

# Check metrics
curl http://localhost:8000/metrics
```

### 4. Run Integration Tests

```bash
python test_mcp_system.py
```

### 5. Stop All Servers

```bash
./stop_mcp_system.sh
```

## Server Components

### 1. MCP Gateway (Port 8000)

The gateway provides a unified interface to all MCP servers:

- **Health Monitoring**: Real-time health checks for all servers
- **Request Routing**: Intelligent routing to appropriate servers
- **Error Handling**: Centralized error handling and recovery
- **Metrics Collection**: Prometheus-compatible metrics
- **Rate Limiting**: Configurable rate limits per endpoint
- **Caching**: Response caching for better performance

### 2. Cloud Run MCP Server (Port 8001)

Manages Google Cloud Run deployments:

**Tools:**

- `deploy_service`: Deploy or update Cloud Run services
- `get_service_status`: Check service status
- `list_services`: List all deployed services

**Example:**

```json
{
  "server": "cloud-run",
  "action": "deploy_service",
  "params": {
    "service_name": "my-api",
    "image": "gcr.io/project/image:latest",
    "memory": "1Gi",
    "cpu": "2"
  }
}
```

### 3. Secrets MCP Server (Port 8002)

Manages Google Secret Manager:

**Tools:**

- `get_secret`: Retrieve secret values
- `create_secret`: Create new secrets
- `update_secret`: Update existing secrets
- `list_secrets`: List all secrets
- `list_versions`: List secret versions

**Example:**

```json
{
  "server": "secrets",
  "action": "create_secret",
  "params": {
    "secret_id": "api-key",
    "value": "secret-value",
    "labels": { "env": "prod" }
  }
}
```

### 4. Memory MCP Server (Port 8003)

Implements layered memory architecture:

**Memory Layers:**

- **Short-term (Redis)**: TTL 1 hour, for temporary data
- **Mid-term (Firestore)**: 30-day retention, for episodic memory
- **Long-term (Qdrant)**: Permanent, for semantic memory

**Tools:**

- `store_memory`: Store memory with importance scoring
- `query_memory`: Search across memory layers
- `consolidate_memories`: Move memories between layers
- `get_agent_memories`: Get all memories for an agent

**Example:**

```json
{
  "server": "memory",
  "action": "store_memory",
  "params": {
    "content": "Important configuration detail",
    "importance": 0.9,
    "metadata": { "type": "config" },
    "agent_id": "main-agent"
  }
}
```

### 5. Orchestrator MCP Server (Port 8004)

Manages agent modes and workflows:

**Available Modes:**

- `standard`: Default operational mode
- `code`: Code generation and analysis
- `debug`: Debugging and troubleshooting
- `architect`: System design and architecture
- `strategy`: Strategic planning
- `ask`: Interactive Q&A mode
- `creative`: Creative problem solving
- `performance`: Performance optimization

**Tools:**

- `switch_mode`: Change operational mode
- `run_workflow`: Execute predefined workflows
- `execute_task`: Run specific tasks
- `get_status`: Get orchestrator status

**Available Workflows:**

- `code_review`: Automated code review
- `test_automation`: Generate and run tests
- `performance_optimization`: Optimize performance
- `deployment`: Full deployment pipeline

## Configuration

### Main Configuration File

The `.mcp.json` file contains all server configurations:

```json
{
  "gateway": {
    "url": "http://localhost:8000",
    "features": ["Health monitoring", "Request routing", ...]
  },
  "servers": {
    "cloud-run": { ... },
    "secrets": { ... },
    "memory": { ... },
    "orchestrator": { ... }
  },
  "performance": {
    "caching": { ... },
    "rateLimiting": { ... },
    "connectionPooling": { ... }
  }
}
```

### Performance Configuration

Edit `mcp_server/config/performance.yaml` to tune performance:

```yaml
connection_pools:
  redis:
    max_connections: 100
    min_idle: 10

caching:
  health_check:
    ttl: 30

rate_limiting:
  requests_per_minute: 1000
```

## Monitoring and Debugging

### Health Dashboard

```bash
# Interactive health monitoring
python mcp_server/monitoring/health_dashboard.py

# One-time health check
python mcp_server/monitoring/health_dashboard.py --once
```

### Logs

```bash
# View all logs
tail -f /var/log/mcp/*.log

# View specific server logs
tail -f /var/log/mcp/Memory_MCP.log
```

### Metrics

Access Prometheus metrics at `http://localhost:8000/metrics`

Key metrics:

- `mcp_gateway_requests_total`: Total requests by endpoint
- `mcp_gateway_request_duration_seconds`: Request latency
- `mcp_gateway_active_servers`: Number of healthy servers
- `mcp_gateway_errors_total`: Error counts by type

## Performance Optimizations

### 1. Connection Pooling

- Redis: 100 max connections
- Firestore: 50 concurrent requests
- Qdrant: 20 connections with gRPC compression

### 2. Caching Strategy

- Health checks: 30-second TTL
- Memory queries: 5-minute TTL
- Secret values: 10-minute TTL (encrypted)

### 3. Batch Processing

- Memory consolidation runs in batches
- Workflow tasks are queued and processed asynchronously

### 4. Rate Limiting

- Global: 1000 requests/minute
- Per-endpoint limits for resource-intensive operations

## Troubleshooting

### Common Issues

1. **Server won't start**

   ```bash
   # Check if ports are in use
   lsof -i :8000-8004

   # Kill existing processes
   ./stop_mcp_system.sh
   ```

2. **Authentication errors**

   ```bash
   # Check GCP auth
   gcloud auth application-default print-access-token

   # Set project
   export GCP_PROJECT_ID=your-project-id
   ```

3. **Memory backend issues**

   ```bash
   # Test Redis
   redis-cli ping

   # Test Firestore
   gcloud firestore operations list

   # Test Qdrant
   curl http://localhost:6333/health
   ```

### Debug Mode

Enable debug logging:

```bash
export MCP_LOG_LEVEL=DEBUG
./start_mcp_system.sh
```

## Development

### Adding New Tools

1. Add tool definition in server's `get_tools()` method
2. Implement the endpoint handler
3. Update gateway routing if needed
4. Add tests

Example:

```python
@app.post("/mcp/my_new_tool")
async def my_new_tool(param1: str, param2: int):
    # Implementation
    return {"result": "success"}
```

### Testing

Run the test suite:

```bash
# All tests
python test_mcp_system.py

# Specific server tests
pytest mcp_server/tests/test_memory_server.py
```

## Security

### Authentication

- Service account authentication for GCP services
- API key validation for external services
- Role-based access control

### Best Practices

1. Store sensitive data in Secret Manager
2. Use service accounts with minimal permissions
3. Enable audit logging
4. Rotate credentials regularly
5. Monitor for anomalous usage patterns

## Deployment to Production

### Cloud Run Deployment

Deploy all MCP servers to Cloud Run:

```bash
# Build and deploy
gcloud run deploy mcp-gateway \
  --source . \
  --port 8000 \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10 \
  --allow-unauthenticated
```

### Using GitHub Actions

The project includes GitHub Actions workflows for automated deployment:

1. Push to main branch triggers deployment
2. Service account authentication via Workload Identity Federation
3. Automatic health checks after deployment

### Environment Variables for Production

```yaml
env:
  GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  GCP_REGION: ${{ secrets.GCP_REGION }}
  REDIS_URL: ${{ secrets.REDIS_URL }}
  FIRESTORE_PROJECT: ${{ secrets.GCP_PROJECT_ID }}
  QDRANT_URL: ${{ secrets.QDRANT_URL }}
```

## Next Steps

1. **Production Deployment**: Deploy servers to Cloud Run
2. **Enhanced Monitoring**: Add Grafana dashboards
3. **WebSocket Support**: Real-time updates
4. **IDE Plugins**: VS Code and JetBrains integration
5. **Additional Servers**: BigQuery, Pub/Sub, Vertex AI

## Support

For issues or questions:

1. Check the health dashboard
2. Review server logs
3. Run integration tests
4. Check this documentation
5. Review individual server code

## Legacy Deployment Guide

For information about the legacy deployment process, see the sections below:

### Prerequisites (Legacy)

Before deploying the MCP server using legacy scripts, ensure you have:

1. A GCP project with APIs enabled
2. GitHub organization secrets configured
3. Docker installed locally

### Legacy Deployment Options

#### Setting Up Powerful Service Accounts

```bash
./setup_badass_credentials.sh
```

#### Manual Deployment

```bash
./deploy_mcp_server.sh [environment]
```

### Troubleshooting Legacy Issues

For Poetry dependency issues:

1. Update Poetry: `pip install --upgrade poetry`
2. Clear cache: `poetry cache clear --all pypi`
3. Rebuild lock: `poetry lock --no-update`
4. Update deps: `poetry update`
