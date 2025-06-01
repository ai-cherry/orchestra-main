# AI Orchestra MCP Server Implementation

**Note:** The MCP components described herein are now integrated as modules within the main application running on a single Vultr server. This documentation requires further updates to fully reflect the simplified single-server architecture.

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
    │ • Memory MCP       :8003      │
    │ • Orchestrator MCP :8004      │
    └───────────────────────────────┘
```

## Quick Start

### 1. Prerequisites

```bash
# Install required packages
pip install -r requirements.txt

# Ensure necessary environment variables for the Vultr deployment are set
# (e.g., POSTGRES_URL, WEAVIATE_ENDPOINT, REDIS_URL, OPENAI_API_KEY, etc.)
```

### 2. Start All MCP Servers

```bash
# Start the entire MCP system (integrated in the main app)
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

- **Health Monitoring** – Real-time health checks for all servers  
- **Request Routing** – Intelligent routing to appropriate servers  
- **Error Handling** – Centralized error handling and recovery  
- **Metrics Collection** – Prometheus-compatible metrics  
- **Rate Limiting** – Configurable rate limits per endpoint  
- **Caching** – Response caching for better performance  

### 2. Memory MCP Server (Port 8003)

Implements layered memory architecture:

**Memory Layers**

- **Short-term (Redis)** – TTL-based cache for immediate context  
- **Mid-term (PostgreSQL)** – For structured episodic and relational memory  
- **Long-term (Weaviate)** – Permanent vector store for semantic memory  

**Tools**

- `store_memory` – Store memory with importance scoring  
- `query_memory` – Search across memory layers  
- `consolidate_memories` – Move memories between layers  
- `get_agent_memories` – Get all memories for an agent  

**Example**

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

### 3. Orchestrator MCP Server (Port 8004)

Manages agent modes and workflows:

**Available Modes**

`standard`, `code`, `debug`, `architect`, `strategy`, `ask`, `creative`, `performance`

**Tools**

- `switch_mode` – Change operational mode  
- `execute` – Execute predefined workflows  
- `execute_task` – Run specific tasks  
- `get_status` – Get orchestrator status  

**Available Workflows**

`code_review`, `test_automation`, `performance_optimization`, `deployment`

## Configuration

### Main Configuration File

The `.mcp.json` file contains all server configurations:

```json
{
  "gateway": {
    "url": "http://localhost:8000",
    "features": ["Health monitoring", "Request routing", "..."]
  },
  "servers": {
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

- `mcp_gateway_requests_total` – Total requests by endpoint  
- `mcp_gateway_request_duration_seconds` – Request latency  
- `mcp_gateway_active_servers` – Number of healthy servers  
- `mcp_gateway_errors_total` – Error counts by type  

## Performance Optimizations

### 1. Connection Pooling

- Redis: 100 max connections  
- Weaviate: 20 connections with gRPC compression  

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

   - Check application logs for specific authentication errors.
   - Verify environment variables containing credentials are set correctly.

3. **Memory backend issues**

   ```bash
   # Test Redis
   redis-cli ping

   # Test PostgreSQL
   psql -h localhost -U postgres -d orchestra -c '\q'

   # Test Weaviate
   curl http://localhost:8080/v1/.well-known/ready
   ```

### Debug Mode

Enable debug logging:

```bash
export MCP_LOG_LEVEL=DEBUG
./start_mcp_system.sh
```

## Development

### Adding New Tools

1. Add tool definition in the server's `get_tools()` method  
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

- Environment-variable-driven credentials for PostgreSQL, Redis, Weaviate, and LLM providers  
- API key validation for external services  
- Role-based access control  

### Best Practices

1. Store sensitive data in environment variables populated from GitHub ORG secrets  
2. Use least-privilege credentials  
3. Enable audit logging  
4. Rotate credentials regularly  
5. Monitor for anomalous usage patterns  

## Deployment to Production

The MCP services run as integrated modules within the main application, deployed to the Vultr server via Pulumi and application deployment scripts.

## Environment Variables for Production

Environment variables are configured according to the Vultr deployment, including credentials for PostgreSQL, Weaviate, Redis, and LLM providers.

## Next Steps

1. **Enhanced Monitoring** – Add Grafana dashboards  
2. **WebSocket Support** – Real-time updates  
3. **IDE Plugins** – VS Code and JetBrains integration  
4. **Additional Internal Tools** – e.g., advanced analytics dashboards  

## Support

For issues or questions:

1. Check the health dashboard  
2. Review server logs  
3. Run integration tests  
4. Review this documentation  
5. Review individual server code  
