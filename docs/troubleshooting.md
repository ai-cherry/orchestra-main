# AI-Cherry Troubleshooting Guide

This guide provides solutions for common issues you might encounter when using AI-Cherry. It's organized by system component and includes diagnostic steps and solutions.

## Table of Contents

- [Diagnostic Tool](#diagnostic-tool)
- [LLM Integration Issues](#llm-integration-issues)
- [Memory System Issues](#memory-system-issues)
- [Agent and Orchestration Issues](#agent-and-orchestration-issues)
- [API and Server Issues](#api-and-server-issues)
- [Deployment Issues](#deployment-issues)
- [Common Error Messages](#common-error-messages)

## Diagnostic Tool

The system comes with a built-in diagnostic tool that can help identify and fix issues automatically:

```bash
python scripts/diagnose_system.py
```

Command line options:

- `--focus COMPONENT`: Run diagnostics only for a specific component (memory, llm, agents, api)
- `--verbose`: Show detailed diagnostic information
- `--fix`: Attempt to automatically fix detected issues
- `--output FILE`: Save diagnostic results to a JSON file

Example for checking only memory systems:

```bash
python scripts/diagnose_system.py --focus memory --verbose
```

## LLM Integration Issues

### LLM Timeouts

**Symptoms**:

- Long response times
- Responses cut off mid-generation
- "Request timed out" errors

**Solutions**:

1. Check your internet connection
2. Verify your API key has sufficient quota
3. Try a different LLM model (smaller models usually have better availability)
4. Increase the timeout setting in `config/settings.yaml`:
   ```yaml
   llm:
     timeout_seconds: 60 # Increase from default 30
   ```

### Authentication Errors

**Symptoms**:

- "API key not valid" error messages
- "Authentication failed" in logs

**Solutions**:

1. Verify your API key in `.env` file
2. Check if the API key has expired or been revoked
3. Ensure the API key has the correct permissions
4. If using multiple providers, verify each key:
   ```bash
   python scripts/verify_api_keys.py
   ```

### Rate Limiting

**Symptoms**:

- "Rate limit exceeded" errors
- Increasing frequency of 429 HTTP status codes

**Solutions**:

1. Implement request throttling in your configuration:
   ```yaml
   llm:
     max_requests_per_minute: 60
     rate_limit_strategy: "queue" # Options: queue, fail, fallback_model
   ```
2. Use a token bucket implementation to manage request rates
3. Consider upgrading your API tier for higher rate limits
4. Enable the multi-provider fallback feature:
   ```yaml
   llm:
     providers:
       - name: "openai"
         priority: 1
       - name: "anthropic"
         priority: 2
   ```

## Memory System Issues

### Vector Database Connection Failures

**Symptoms**:

- "Failed to connect to vector database" errors
- Empty semantic search results despite content existing
- Slow query performance

**Solutions**:

1. Check network connectivity to the vector database
2. Verify database credentials in `.env`
3. Ensure the vector database service is running:
   ```bash
   docker ps | grep pinecone  # or weaviate
   ```
4. Restart the vector database service:
   ```bash
   cd memory-api && docker compose restart pinecone
   ```
5. Check for database resource constraints:
   ```bash
   python scripts/diagnose_system.py --focus memory --check resource_usage
   ```

### Missing or Incomplete Memory Records

**Symptoms**:

- Expected memories not appearing in search results
- Incorrect or partial recall of stored information
- "Embedding generation failed" errors

**Solutions**:

1. Verify the memory was properly stored:
   ```bash
   curl -X GET "http://localhost:8000/memory/status?user_id=YOUR_USER_ID"
   ```
2. Check embedding service logs for errors:
   ```bash
   python scripts/diagnose_system.py --focus memory --check embeddings --verbose
   ```
3. Manually reindex problematic memories:
   ```bash
   python scripts/reindex_memories.py --user_id YOUR_USER_ID
   ```
4. Ensure text chunking is configured properly:
   ```yaml
   memory:
     chunking:
       chunk_size: 1000
       chunk_overlap: 200
   ```

### Redis Cache Issues

**Symptoms**:

- Slow memory retrieval
- "Redis connection error" in logs
- System working but with degraded performance

**Solutions**:

1. Verify Redis is running:
   ```bash
   redis-cli ping
   ```
2. Check Redis memory usage:
   ```bash
   redis-cli info memory
   ```
3. Flush Redis cache if corrupted:
   ```bash
   redis-cli flushdb
   ```
4. Adjust Redis connection settings:
   ```yaml
   cache:
     redis:
       connection_pool_size: 10
       socket_timeout: 5
   ```

## Agent and Orchestration Issues

### Persona Switching Failures

**Symptoms**:

- Agent using wrong persona
- "Persona not found" errors
- Unexpected fallback to default persona

**Solutions**:

1. Verify persona configurations:
   ```bash
   python scripts/diagnose_system.py --focus agents --check personas
   ```
2. Reload personas without restarting:
   ```bash
   curl -X POST "http://localhost:8000/api/personas/reload"
   ```
3. Check for syntax errors in persona config files
4. Verify the persona name matches exactly in API requests

### Graph Execution Failures

**Symptoms**:

- "Graph execution failed" errors
- Workflows getting stuck at specific nodes
- Unexpected agent behavior

**Solutions**:

1. Review LangGraph execution logs:
   ```bash
   python scripts/diagnose_system.py --focus agents --check workflows
   ```
2. Check for circular dependencies in the graph
3. Verify tool configurations:
   ```bash
   python scripts/verify_tool_configs.py
   ```
4. Increase logging detail for the problematic workflow:
   ```bash
   python -m orchestrator_core.runner --workflow WORKFLOW_NAME --debug
   ```

## API and Server Issues

### API Server Won't Start

**Symptoms**:

- "Address already in use" errors
- Server crashes immediately after starting
- Permission errors

**Solutions**:

1. Check if another process is using the port:
   ```bash
   lsof -i :8000
   ```
2. Kill the process if necessary:
   ```bash
   kill -9 PID
   ```
3. Verify environment setup:
   ```bash
   python scripts/verify_env.py
   ```
4. Check for recent breaking changes in the API:
   ```bash
   git log -p api/
   ```

### Slow API Response

**Symptoms**:

- API requests taking >1 second to respond
- Timeouts from client applications
- High server CPU or memory usage

**Solutions**:

1. Check server resource usage:
   ```bash
   python scripts/diagnose_system.py --focus api --check performance
   ```
2. Optimize database queries:
   ```bash
   python scripts/analyze_query_performance.py
   ```
3. Enable response caching:
   ```yaml
   api:
     response_cache:
       enabled: true
       ttl_seconds: 300
   ```
4. Scale up the service if on cloud:
   ```bash
   terraform apply -var="memory_api_instance_count=3"
   ```

## Deployment Issues

### Terraform Deployment Failures

**Symptoms**:

- "Error applying Terraform plan"
- Resource creation failures
- Permission issues

**Solutions**:

1. Verify cloud credentials:
   ```bash
   gcloud auth list
   ```
2. Check for resource quota limits in your cloud account
3. Run with detailed logging:
   ```bash
   terraform apply -var-file=prod.tfvars -input=false -auto-approve -detailed-exitcode
   ```
4. Check for conflicting resources:
   ```bash
   terraform import RESOURCE_ADDRESS ID
   ```

### Docker Image Build Failures

**Symptoms**:

- "Failed to build Docker image"
- Dependency installation errors
- Resource limitations during build

**Solutions**:

1. Update Docker and dependencies:
   ```bash
   docker --version
   sudo apt update && sudo apt upgrade docker-ce
   ```
2. Clean Docker system:
   ```bash
   docker system prune -af
   ```
3. Check disk space:
   ```bash
   df -h
   ```
4. Build with verbose output:
   ```bash
   docker build -t ai-cherry/memory-api:latest -f memory-api/Dockerfile . --progress=plain
   ```

## Common Error Messages

Here are solutions for specific error messages you might encounter:

### "Failed to connect to LLM provider"

This usually indicates network or authentication issues with the LLM API.

**Solutions**:

1. Check your internet connection
2. Verify API key in `.env`
3. Test direct API connectivity:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```
4. If using a proxy, check proxy settings

### "Vector search returned no results"

This can happen when the vector database doesn't contain relevant information or when there are embedding issues.

**Solutions**:

1. Verify content exists in the vector store:
   ```bash
   python scripts/list_vector_entries.py --user_id YOUR_USER_ID
   ```
2. Check embedding quality:
   ```bash
   python scripts/analyze_embeddings.py --text "your test query"
   ```
3. Adjust search parameters:
   ```yaml
   vector_search:
     similarity_threshold: 0.7 # Lower for more results
     top_k: 10 # Increase for more results
   ```

### "Memory component in degraded state"

This indicates the memory system is operating with reduced functionality.

**Solutions**:

1. Identify which components are degraded:
   ```bash
   python scripts/diagnose_system.py --focus memory --verbose
   ```
2. Check component connections:
   ```bash
   python scripts/check_component_connectivity.py
   ```
3. Restart memory services:
   ```bash
   cd memory-api && docker compose restart
   ```
4. Check for resource constraints on memory components

### "Error loading agent definition"

This indicates problems with agent configuration files.

**Solutions**:

1. Validate agent configuration formats:
   ```bash
   python scripts/validate_agent_configs.py
   ```
2. Check for missing dependencies in agent tools
3. Verify agent YAML syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('path/to/agent_config.yaml'))"
   ```
4. Update agent dependencies:
   ```bash
   pip install -r agents-core/requirements.txt
   ```

## Still Need Help?

If you're still experiencing issues:

1. Generate a detailed diagnostic report:

   ```bash
   python scripts/diagnose_system.py --verbose --output diagnostic_report.json
   ```

2. Check the AI-Cherry GitHub repository for recent issues and solutions

3. Join our Discord community for real-time support

4. Review CloudWatch logs (if deployed to AWS) or StackDriver logs (if on GCP) for deeper investigation
