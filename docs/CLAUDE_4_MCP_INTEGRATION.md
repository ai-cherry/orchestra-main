# Claude MCP Integration Guide

## Overview

This guide explains how to use the Model Context Protocol (MCP) servers with Claude to enable powerful AI-assisted development capabilities for the AI cherry_ai project.

## Architecture

```
┌─────────────────┐
│   Claude        │
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
    │ •     │ • Secrets MCP      :8002      │
    │ • Memory MCP       :8003      │
    │ • conductor MCP :8004      │
    └───────────────────────────────┘
```

## Quick Start

### 1. Start All MCP Servers

```bash
# Make scripts executable
chmod +x start_mcp_system.sh stop_mcp_system.sh

# Start all MCP servers
./start_mcp_system.sh

# Check health status
curl http://localhost:8000/health
```

### 2. Configure Claude

Add the MCP configuration to your Claude settings:

```json
{
  "mcp": {
    "servers": {
      "ai-cherry_ai": {
        "endpoint": "http://localhost:8000",
        "description": "AI cherry_ai MCP Gateway"
      }
    }
  }
}
```

### 3. Available Tools

Claude can now use these tools:

####
- `deploy_service` - Deploy or update - `get_service_status` - Check service status
- `list_services` - List all deployed services

#### Secret Management

- `get_secret` - Retrieve secret values
- `create_secret` - Create new secrets
- `update_secret` - Update existing secrets
- `list_secrets` - List all secrets

#### Memory Management

- `store_memory` - Store information in layered memory
- `query_memory` - Search across memory layers
- `consolidate_memories` - Move memories between layers
- `get_agent_memories` - Get all memories for an agent

#### coordination

- `switch_mode` - Change agent operational mode
 - `execute` - Execute predefined workflows
- `execute_task` - Run specific tasks
- `get_status` - Get conductor status

## Usage Examples

### Deploy a Service

```
Claude, deploy the admin API to ```

Claude will use:

```python
deploy_service(
    service_name="admin-api",
    image="gcr.io/cherry-ai-project/admin-api:latest",
    memory="1Gi",
    cpu="2"
)
```

### Store Important Information

```
Claude, remember that the production database connection string is stored in the secret "prod-db-connection"
```

Claude will use:

```python
store_memory(
    content="Production database connection string is in secret: prod-db-connection",
    importance=0.9,
    metadata={"type": "configuration", "environment": "production"}
)
```

### Run a Workflow

```
Claude, run the code review workflow on the current changes
```

Claude will use:

```python
execute(
    name="code_review",
    params={"branch": "main", "files": ["*.py"]}
)
```

### Switch Mode

```
Claude, switch to performance mode and optimize the API endpoints
```

Claude will use:

```python
switch_mode(
    mode="performance",
    context={"focus": "api_optimization"}
)
```

## Memory Architecture

The MCP memory system uses a three-layer architecture:

### 1. Short-term Memory (Redis)

- **Purpose**: Recent interactions and temporary state
- **TTL**: 1 hour
- **Use cases**: Current conversation context, temporary flags

### 2. Mid-term Memory (MongoDB

- **Purpose**: Episodic memory and task history
- **Retention**: 30 days
- **Use cases**: Recent project changes, completed tasks

### 3. Long-term Memory (Weaviate)

- **Purpose**: Semantic memory and knowledge base
- **Retention**: Permanent
- **Use cases**: Important configurations, learned patterns

## Monitoring

### Health Dashboard

Monitor all MCP servers in real-time:

```bash
python mcp_server/monitoring/health_dashboard.py
```

### Check Individual Server Health

```bash
# Gateway health
curl http://localhost:8000/health

# Detailed status
curl http://localhost:8000/status

# Prometheus metrics
curl http://localhost:8000/metrics
```

### View Logs

```bash
# All logs
tail -f /var/log/mcp/*.log

# Specific server
tail -f /var/log/mcp/Cloud_Run_MCP.log
```

## Workflows

### Available Workflows

1. **Code Review**

   - Analyze code quality
   - Check style compliance
   - Generate review report

2. **Test Automation**

   - Analyze code structure
   - Generate test cases
   - Run tests
   - Generate coverage report

3. **Performance Optimization**

   - Profile code
   - Identify bottlenecks
   - Apply optimizations
   - Benchmark results

4. **Deployment**
   - Run tests
   - Build container image
   - Deploy to staging
   - Run smoke tests
   - Deploy to production

### Custom Workflows

Create custom workflows by adding them to the conductor configuration.

## Best Practices

### 1. Memory Management

- Use appropriate importance scores (0-1)
- Add meaningful metadata
- Consolidate memories regularly

### 2. Error Handling

- Always check service health before operations
- Use the gateway for unified error handling
- Monitor logs for issues

### 3. Security

- Store sensitive data in - Use service accounts for authentication
- Rotate secrets regularly

### 4. Performance

- Use batch operations when possible
- Monitor latency through metrics
- Cache frequently accessed data

## Troubleshooting

### Server Won't Start

```bash
# Check if ports are in use
lsof -i :8000-8004

# Stop all servers
./stop_mcp_system.sh

# Restart
./start_mcp_system.sh
```

### Authentication Issues

```bash
# Check gcloud auth application-default print-access-token

# Set project
export ```

### Memory Backend Issues

```bash
# Check Redis
redis-cli ping

# Check MongoDB
gcloud MongoDB

# Check Weaviate
curl http://localhost:8082/v1/.well-known/ready
```

## Advanced Usage

### Direct Server Access

While the gateway provides a unified interface, you can also access servers directly:

```python
# Direct curl -X POST http://localhost:8001/mcp/deploy \
  -H "Content-Type: application/json" \
  -d '{"service_name": "test", "image": "gcr.io/test/image"}'
```

### Custom Tools

Add custom tools by extending the MCP servers:

1. Add tool definition in `get_tools()`
2. Implement endpoint
3. Update gateway routing

### Integration with IDEs

The MCP servers can be integrated with:

- VS Code extensions
- JetBrains plugins
- Command-line tools

## Performance Optimizations

### 1. Connection Pooling

All servers use connection pooling for better performance.

### 2. Caching

- Redis caches frequent queries
- Gateway caches health status
- Memory queries are indexed

### 3. Async Operations

All operations are async for better concurrency.

## Security Considerations

### 1. Authentication

- Service account authentication for - API key authentication for external services
- Role-based access control

### 2. Encryption

- TLS for all communications
- Encrypted storage for secrets
- Secure memory storage

### 3. Auditing

- All operations are logged
- Metrics track usage patterns
- Alerts for anomalies

## Next Steps

1. **Extend functionality**: Add more tools and workflows
2. **Improve monitoring**: Add Grafana dashboards
3. **Scale horizontally**: Deploy to 4. **Add webhooks**: Real-time notifications
5. **Create plugins**: IDE integrations

## Support

For issues or questions:

1. Check server logs in `/var/log/mcp/`
2. Run health dashboard for diagnostics
3. Review this documentation
4. Check server-specific READMEs
