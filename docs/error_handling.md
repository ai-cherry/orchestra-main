# Error Handling Strategy

This document outlines the comprehensive error handling strategy implemented in AI-Cherry, building on the resilience improvements from the Orchestra system.

## Design Philosophy

Our error handling is built on five core principles:

1. **Fail Gracefully**: When errors occur, systems should degrade in functionality rather than fail completely
2. **Be Transparent**: Users should understand what's happening when things go wrong
3. **Recover Automatically**: Systems should attempt to self-heal when possible
4. **Preserve Context**: Even during failures, maintain as much context and state as possible
5. **Learn From Failures**: Aggregate error data to improve system resilience over time

## Implementation Layers

Error handling is implemented at multiple layers of the system:

### 1. LLM Client Layer

The LLM client handles API calls to language model providers:

```python
async def generate_with_retry(messages, model="gpt-4", max_retries=3):
    for attempt in range(max_retries):
        try:
            return await llm_client.generate(messages, model=model)
        except TransientError as e:
            # Exponential backoff with jitter
            delay = (2 ** attempt * 0.5) + (random.random() * 0.5)
            logger.warning(f"Transient error: {e}. Retrying in {delay:.2f}s...")
            await asyncio.sleep(delay)
            continue
        except RateLimitError:
            # Switch to a different provider or fallback model
            logger.warning(f"Rate limit hit for {model}, falling back...")
            return await llm_client.generate(messages, model="gpt-3.5-turbo")
        except AuthenticationError:
            # Critical error, cannot recover
            logger.error("Authentication failed for LLM provider")
            return user_friendly_error_response(
                "I'm having trouble connecting to my knowledge service. " 
                "Please check your API key configuration."
            )
    
    # If we get here, all retries failed
    logger.error(f"All {max_retries} attempts failed")
    return user_friendly_error_response(
        "I'm currently experiencing technical difficulties. " 
        "Please try again in a few moments."
    )
```

### 2. Memory System Layer

The memory system implements graceful degradation when components fail:

```python
async def retrieve_memories(query, user_id):
    # Check component health
    health_status = await memory_system.health_check()
    
    results = []
    error_context = {}
    
    # Try vector search first (most relevant)
    if health_status.vector_db_healthy:
        try:
            vector_results = await memory_system.vector_search(query, user_id)
            results.extend(vector_results)
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            error_context["vector_search_error"] = str(e)
    else:
        logger.warning("Vector DB unavailable, skipping semantic search")
        error_context["vector_db_unavailable"] = True
    
    # Always try to get recent memories from SQL (fallback)
    try:
        recent_memories = await memory_system.get_recent_memories(user_id, limit=5)
        results.extend(recent_memories)
    except Exception as e:
        logger.error(f"Recent memory retrieval failed: {e}")
        error_context["recent_memory_error"] = str(e)
    
    # If we have enough results, return them
    if len(results) >= 3:
        return results, error_context
        
    # Last resort: try graph database for related memories
    if health_status.graph_db_healthy and not results:
        try:
            graph_results = await memory_system.graph_related_memories(query, user_id)
            results.extend(graph_results)
        except Exception as e:
            logger.error(f"Graph search failed: {e}")
            error_context["graph_search_error"] = str(e)
    
    return results, error_context
```

### 3. API Response Layer

The API endpoints include health information and contextual errors:

```python
@router.post("/search")
async def search_memories(request: SearchRequest):
    try:
        # Perform the memory search
        results, error_context = await retrieve_memories(
            request.query, request.user_id
        )
        
        # Determine response status
        if len(results) == 0 and error_context:
            status = "degraded"
        elif error_context:
            status = "partial"
        else:
            status = "success"
        
        # Include system health for client awareness
        system_health = {
            "status": status,
            "degraded_components": [k for k, v in error_context.items() if v],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return {
            "results": results,
            "system_health": system_health,
            "result_count": len(results)
        }
        
    except Exception as e:
        logger.exception(f"Search endpoint error: {e}")
        
        # Return a structured error with remediation steps
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "system_health": {"status": "error"},
                "remediation": "Please try again or check system logs."
            }
        )
```

## Error Categorization

We categorize errors to apply appropriate handling strategies:

### 1. Transient Errors

Temporary issues that might resolve on retry:
- Network timeouts
- Temporary service unavailability
- Rate limiting

**Strategy**: Automatic retries with exponential backoff and jitter

### 2. Configuration Errors

Issues with system configuration:
- Missing API keys
- Invalid database credentials
- Incorrect permissions

**Strategy**: Clear error messages with actionable remediation steps

### 3. Data Errors

Issues with data processing:
- Invalid input format
- Embedding generation failures
- Schema validation errors

**Strategy**: Detailed validation errors and fallback to simpler processing

### 4. System Errors

Fundamental issues with system components:
- Database connection failures
- Out of memory errors
- Service crashes

**Strategy**: Graceful degradation, component isolation, and automatic healing

## Monitoring and Recovery

### Health Monitoring

A background health monitoring task runs periodically:

```python
async def health_monitor():
    while True:
        try:
            # Check all system components
            status = await perform_health_checks()
            
            # Log current health
            logger.info(f"System health status: {status['overall']}")
            for component, health in status['components'].items():
                if health['status'] != 'healthy':
                    logger.warning(f"Component {component} health: {health['status']}")
            
            # Attempt recovery for unhealthy components
            for component, health in status['components'].items():
                if health['status'] == 'unhealthy' and health.get('recoverable', False):
                    logger.info(f"Attempting recovery for {component}")
                    await recovery_strategies[component]()
                    
        except Exception as e:
            logger.error(f"Health monitor error: {e}")
            
        # Check every 5 minutes
        await asyncio.sleep(300)
```

### Recovery Strategies

Component-specific recovery strategies:

```python
recovery_strategies = {
    "vector_db": async_reconnect_vector_db,
    "postgres": async_reconnect_postgres,
    "redis_cache": async_reset_redis_connection,
    "llm_client": async_reset_llm_client,
}

async def async_reconnect_vector_db():
    # Close existing connections
    await vector_db_client.close()
    # Initialize with fresh connection
    await vector_db_client.initialize()
    # Verify connection
    return await vector_db_client.ping()
```

## User-Friendly Error Messages

We transform technical errors into actionable, user-friendly messages:

```python
def user_friendly_error_response(technical_error):
    error_mapping = {
        "AuthenticationError": {
            "message": "I'm having trouble accessing my knowledge. This is likely due to an authentication issue.",
            "action": "Please check your API keys in the configuration."
        },
        "ConnectionError": {
            "message": "I'm unable to connect to my memory systems at the moment.",
            "action": "Please check your internet connection and try again."
        },
        "RateLimitError": {
            "message": "I've reached my current capacity for knowledge processing.",
            "action": "Please try again in a few minutes when capacity frees up."
        },
        # Default fallback for unrecognized errors
        "default": {
            "message": "I'm experiencing a technical issue.",
            "action": "Please try again or contact support if the problem persists."
        }
    }
    
    # Find the appropriate error category
    for error_type, response in error_mapping.items():
        if error_type in str(technical_error):
            return f"{response['message']} {response['action']}"
    
    # If no specific match, use default
    return f"{error_mapping['default']['message']} {error_mapping['default']['action']}"
```

## Diagnostic and Debug Support

For developers and operators, detailed diagnostic information is available:

### Diagnostic Endpoint

```python
@router.get("/system/diagnostics")
async def run_diagnostics(component: Optional[str] = None):
    """Run system diagnostics and return detailed results."""
    results = await system_diagnostics.run_checks(component=component)
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "results": results,
        "summary": system_diagnostics.summarize_results(results)
    }
```

### Logging Strategy

Logging is structured for easy analysis:

```json
{
  "timestamp": "2025-04-22T09:15:23.423Z",
  "level": "ERROR",
  "service": "memory-api",
  "component": "vector_db",
  "operation": "search",
  "error_type": "ConnectionError",
  "message": "Failed to connect to vector DB",
  "trace_id": "abc123xyz789",
  "retry_count": 2,
  "recovery_attempted": true,
  "recovery_success": false
}
```

## Integration with Monitoring

Error metrics are exposed for monitoring systems:

- Error rate by component
- Recovery success rate
- Degraded operation duration
- Failure impact score (affected users × severity)

These metrics can trigger alerts and feed into SLO dashboards.

## Conclusion

This comprehensive error handling strategy ensures AI-Cherry remains resilient even when individual components fail. By implementing proper error classification, recovery mechanisms, graceful degradation, and user-friendly messaging, we create a system that maintains usefulness even in degraded states.
