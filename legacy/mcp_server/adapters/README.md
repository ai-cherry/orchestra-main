# MCP Server Adapters for Factory AI Integration

This package provides adapters that bridge Factory AI Droids with existing MCP servers, enabling seamless integration while maintaining backward compatibility.

## Overview

The adapter system implements the Bridge pattern to translate between MCP protocol and Factory AI format, with built-in resilience features:

- **Circuit Breaker Pattern**: Prevents cascading failures when Factory AI services are unavailable
- **Automatic Fallback**: Seamlessly falls back to direct MCP server calls on failure
- **Performance Metrics**: Tracks request latency, success rates, and resource utilization
- **Prometheus Integration**: Exports metrics for monitoring and alerting

## Architecture

```
MCP Client Request
        ↓
   MCP Adapter
        ↓
 [Circuit Breaker]
    ↓        ↓
Factory AI   MCP Server
  Droid     (fallback)
    ↓        ↓
   Response
```

## Adapters

### 1. ArchitectAdapter
- **MCP Server**: conductor_server.py
- **Factory Droid**: Architect
- **Capabilities**: System design, Pulumi IaC generation, architectural diagrams
- **Special Features**: Complex diagram handling, infrastructure-as-code generation

### 2. CodeAdapter
- **MCP Server**: tools_server.py
- **Factory Droid**: Code
- **Capabilities**: Fast code generation, optimization, refactoring
- **Special Features**: Streaming responses, incremental updates

### 3. DebugAdapter
- **MCP Server**: tools_server.py
- **Factory Droid**: Debug
- **Capabilities**: Error diagnosis, query optimization, performance profiling
- **Special Features**: Stack trace analysis, profiling integration

### 4. ReliabilityAdapter
- **MCP Server**: deployment_server.py
- **Factory Droid**: Reliability
- **Capabilities**: Incident management, monitoring, alert aggregation
- **Special Features**: Automated remediation triggers, alert correlation

### 5. KnowledgeAdapter
- **MCP Server**: memory_server.py
- **Factory Droid**: Knowledge
- **Capabilities**: Vector operations, documentation, semantic search
- **Special Features**: Weaviate integration, embedding cache

## Usage

### Basic Example

```python
from mcp_server.adapters import ArchitectAdapter

# Initialize adapter
mcp_server = MCPconductorServer()
droid_config = {
    "api_key": "your-factory-ai-key",
    "failure_threshold": 5,
    "recovery_timeout": 60
}
adapter = ArchitectAdapter(mcp_server, droid_config)

# Process request
request = {
    "method": "design_system",
    "params": {
        "project_type": "microservices",
        "requirements": ["scalable", "fault-tolerant"],
        "cloud_provider": "Lambda"
    }
}
response = await adapter.process_request(request)
```

### Streaming Example (Code Adapter)

```python
from mcp_server.adapters import CodeAdapter

adapter = CodeAdapter(mcp_server, {"streaming": True})

request = {
    "method": "generate_code",
    "params": {
        "language": "python",
        "requirements": ["async FastAPI endpoint"],
        "stream": True
    }
}
# Response will include stream_id for real-time updates
response = await adapter.process_request(request)
```

## Circuit Breaker Configuration

Each adapter includes a circuit breaker with configurable parameters:

```python
droid_config = {
    "failure_threshold": 5,      # Failures before opening circuit
    "recovery_timeout": 60,      # Seconds before attempting recovery
    "api_key": "your-key",
    "base_url": "https://api.factory.ai"
}
```

## Metrics and Monitoring

### Available Metrics

1. **Request Metrics**
   - `factory_mcp_requests_total`: Total requests by adapter and status
   - `factory_mcp_request_duration_seconds`: Request duration histogram

2. **Circuit Breaker Metrics**
   - `factory_mcp_circuit_breaker_state`: Current state (0=closed, 1=open, 2=half_open)

3. **Adapter-specific Metrics**
   - Success rate
   - Average latency
   - Fallback count

### Health Check

```python
health = await adapter.health_check()
# Returns:
# {
#     "healthy": true,
#     "metrics": {...},
#     "timestamp": "2024-01-15T10:30:00Z"
# }
```

## Error Handling

The adapters implement graceful error handling:

1. **Factory AI Errors**: Caught and translated to MCP error format
2. **Circuit Open**: Automatic fallback to MCP server
3. **Network Issues**: Retries with exponential backoff (in Factory AI client)
4. **Invalid Requests**: Validation errors returned immediately

## Testing

Run the comprehensive test suite:

```bash
pytest mcp_server/adapters/test_adapters.py -v
```

Test coverage includes:
- Circuit breaker functionality
- Request/response translation
- Fallback mechanisms
- Metrics collection
- Integration scenarios

## Performance Considerations

1. **Caching**: Knowledge adapter includes embedding cache
2. **Streaming**: Code adapter supports streaming for large responses
3. **Connection Pooling**: Reuses Factory AI client connections
4. **Async Operations**: All operations are async for better concurrency

## Configuration Best Practices

1. **Circuit Breaker**: Set thresholds based on your SLA requirements
2. **Timeouts**: Configure based on expected response times
3. **Caching**: Enable for frequently accessed embeddings
4. **Monitoring**: Set up alerts on circuit breaker state changes

## Troubleshooting

### Circuit Breaker Stays Open
- Check Factory AI service health
- Verify API credentials

### High Fallback Rate
- Monitor Factory AI latency
- Adjust circuit breaker thresholds
- Check network connectivity

### Memory Usage
- Clear embedding cache periodically
- Monitor cache size in Knowledge adapter
- Implement cache eviction policy

## Future Enhancements

1. **Retry Logic**: Add configurable retry with backoff
2. **Request Queuing**: Buffer requests during circuit open state
3. **Advanced Caching**: Implement LRU cache for all adapters
4. **Metrics Dashboard**: Grafana templates for monitoring