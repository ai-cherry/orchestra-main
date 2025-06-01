# Factory AI Integration

This directory contains the Factory AI Droid integration for the Orchestra project, providing seamless integration between Factory AI's specialized droids and the existing Roo/MCP infrastructure.

## Overview

The Factory AI integration implements a bridge pattern that allows Factory AI Droids to work alongside Roo's existing capabilities, with automatic fallback mechanisms and unified context management.

## Directory Structure

```
.factory/
├── config.yaml           # Main configuration file
├── droids/              # Droid-specific documentation
│   ├── architect.md     # Architect Droid specs
│   ├── code.md         # Code Droid specs
│   ├── debug.md        # Debug Droid specs
│   ├── reliability.md  # Reliability Droid specs
│   └── knowledge.md    # Knowledge Droid specs
├── context.py          # Context management module
├── bridge/             # Bridge implementation
│   ├── __init__.py
│   └── api_gateway.py  # Main API gateway
└── README.md          # This file
```

## Available Droids

1. **Architect Droid**: System design and architecture planning
2. **Code Droid**: Code generation, refactoring, and optimization
3. **Debug Droid**: Error analysis and performance profiling
4. **Reliability Droid**: Deployment and infrastructure management
5. **Knowledge Droid**: Documentation and knowledge management

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Weaviate vector store
- Redis cache
- Vultr API access (for infrastructure)
- Factory AI API key

### Environment Variables

Required environment variables:
```bash
FACTORY_AI_API_KEY=your-factory-ai-key
VULTR_API_KEY=your-vultr-api-key
POSTGRES_CONNECTION_STRING=postgresql://user:pass@host:port/db
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your-weaviate-key
REDIS_URL=redis://localhost:6379
PULUMI_CONFIG_PASSPHRASE=your-secure-passphrase
```

Optional environment variables:
```bash
FACTORY_AI_BASE_URL=https://api.factoryai.com/v1
JAEGER_ENDPOINT=http://localhost:14268/api/traces
PROMETHEUS_PORT=9090
```

### Installation

1. Run the setup script:
```bash
cd factory_integration
./setup_bridge.sh
```

2. The script will:
   - Validate environment variables
   - Test Vultr API access
   - Configure Pulumi for infrastructure
   - Create Python virtual environment
   - Install dependencies
   - Test database connections
   - Create systemd service files

### Running the Bridge

For development:
```bash
source venv/bin/activate
uvicorn factory_integration.api.gateway:app --reload
```

For production:
```bash
sudo systemctl start factory-bridge-api
sudo systemctl start factory-context-sync
```

## API Usage

### Execute a Factory AI Task

```bash
curl -X POST http://localhost:8080/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "droid": "architect",
    "task": "design_system",
    "context": {
      "project_type": "web_application",
      "requirements": ["scalability", "security"]
    },
    "options": {
      "detail_level": "high"
    }
  }'
```

### Get Metrics

```bash
curl http://localhost:8080/api/v1/metrics
```

### Get Request History

```bash
curl http://localhost:8080/api/v1/history?limit=10
```

## Context Management

The context management system provides:
- Hierarchical context chains
- Context merging across droids
- Persistent storage in PostgreSQL
- Vector embeddings in Weaviate
- Fast access via Redis cache

Example usage:
```python
from factory.context import FactoryContextManager

manager = FactoryContextManager()

# Create context for architect droid
ctx = manager.create_context(
    "architect",
    initial_data={"project_type": "api"}
)

# Update context
manager.update_context(
    ctx.task_id,
    data_updates={"framework": "fastapi"}
)

# Get context chain
chain = manager.get_context_chain(ctx.task_id)
```

## Performance Targets

- P95 latency: < 85ms
- Throughput: 3,600 req/s
- Cache hit rate: > 85%
- Memory overhead: < 10%

## Monitoring

The integration includes:
- Prometheus metrics at `/metrics`
- Jaeger distributed tracing
- Custom Factory AI metrics
- Circuit breaker status
- Request history tracking

## Security

- API key authentication
- Secure credential storage
- Audit logging
- Rate limiting per droid/user
- Encryption at rest and in transit

## Troubleshooting

### Common Issues

1. **Circuit breaker open**: Too many failures for a specific droid
   - Check Factory AI API status
   - Review error logs
   - Wait for recovery timeout

2. **Connection failures**: Database or cache unreachable
   - Verify connection strings
   - Check network connectivity
   - Ensure services are running

3. **Authentication errors**: Invalid API keys
   - Verify environment variables
   - Check key expiration
   - Ensure proper permissions

### Logs

View logs:
```bash
# Bridge API logs
journalctl -u factory-bridge-api -f

# Context sync logs
journalctl -u factory-context-sync -f
```

## Development

### Running Tests

```bash
pytest tests/factory_integration/ -v --cov=factory_integration
```

### Code Standards

- Python 3.10+ with type hints
- Black formatting
- Google-style docstrings
- Minimum 80% test coverage

## Next Steps

1. Complete MCP server adapters (Phase 3.2)
2. Implement unified context manager (Phase 3.3)
3. Build caching layer (Phase 3.3)
4. Create API gateway (Phase 3.4)
5. Add monitoring integration (Phase 3.4)
6. Implement hybrid orchestrator (Phase 3.5)
7. Comprehensive testing (Phase 3.5)

## Support

For issues or questions:
1. Check the troubleshooting guide
2. Review droid-specific documentation
3. Check Factory AI documentation
4. Contact the development team