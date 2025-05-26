# SuperAGI Migration Guide for Orchestra AI

## Overview

This guide provides step-by-step instructions for migrating the Orchestra AI system to use SuperAGI as the autonomous agent platform. SuperAGI provides enhanced capabilities for building, deploying, and managing AI agents with features like concurrent execution, tool integration, and advanced memory management.

## Why SuperAGI?

### Key Benefits

1. **AI Agent Focus**: Purpose-built for autonomous AI agents
2. **Concurrent Execution**: Run multiple agents simultaneously
3. **Tool Integration**: Connect to external systems (Slack, GitHub, etc.)
4. **Memory Management**: Built-in support for agent memory storage
5. **Open Source**: Full customization without vendor lock-in
6. **Production Ready**: GUI and CLI for easy management

### Architecture Comparison

| Component | Current (Orchestra) | With SuperAGI |
|-----------|-------------------|---------------|
| Agent Runtime | Custom Python | SuperAGI Engine |
| Memory | Firestore + Custom | DragonflyDB + Firestore |
| Deployment | Cloud Run | GKE + SuperAGI |
| Scaling | Manual | Auto-scaling |
| Tools | Limited | Extensible Plugin System |

## Prerequisites

Before starting the migration:

1. **GCP Project Setup**
   ```bash
   export GCP_PROJECT_ID="your-project-id"
   export GCP_REGION="us-central1"
   ```

2. **Required Tools**
   - gcloud CLI
   - kubectl
   - Pulumi
   - Docker
   - Python 3.10+

3. **API Keys**
   ```bash
   export OPENROUTER_API_KEY="your-api-key"
   ```

## Migration Steps

### Phase 1: Infrastructure Setup

1. **Enable Required APIs**
   ```bash
   ./scripts/deploy_superagi.sh enable_apis
   ```

2. **Deploy GKE Cluster**
   ```bash
   cd infra
   pulumi up -s superagi -f superagi_deployment.py
   ```

3. **Build and Push Docker Image**
   ```bash
   docker build -f Dockerfile.superagi -t gcr.io/${GCP_PROJECT_ID}/superagi:latest .
   docker push gcr.io/${GCP_PROJECT_ID}/superagi:latest
   ```

### Phase 2: Agent Migration

1. **Update Agent Definitions**

   Current Orchestra agent:
   ```python
   class SimpleTextAgent(Agent):
       async def process(self, context: AgentContext) -> AgentResponse:
           # Processing logic
           return AgentResponse(content=result)
   ```

   SuperAGI agent:
   ```python
   class SuperAGIAgent(Agent):
       def __init__(self, agent_id: str, config: Dict[str, Any]):
           self.tools = []
           self.memory_enabled = True
           self.max_iterations = 5

       async def process(self, context: AgentContext) -> AgentResponse:
           result = await self._execute_autonomous_task(
               task=context.user_input,
               tools=self.tools,
               max_iterations=self.max_iterations
           )
           return AgentResponse(content=result["output"])
   ```

2. **Register Agents with SuperAGI**
   ```python
   # In orchestra_adapter.py
   default_agents = [
       {
           "id": "researcher",
           "name": "Research Agent",
           "config": {
               "memory_enabled": True,
               "max_iterations": 5,
               "capabilities": ["web_search", "summarization"]
           }
       }
   ]
   ```

### Phase 3: Memory System Integration

1. **Configure DragonflyDB for Short-term Memory**
   ```yaml
   # In superagi ConfigMap
   redis:
     host: dragonfly
     port: 6379
   memory:
     short_term:
       provider: redis
       ttl: 3600
     long_term:
       provider: firestore
   ```

2. **Update Memory Access Patterns**
   ```python
   # Old pattern
   memory_item = await memory_manager.get_memory(user_id)

   # New pattern with SuperAGI
   memory_key = f"agent:{agent_id}:memory"
   memory_data = await redis_client.get(memory_key)
   ```

### Phase 4: API Migration

1. **Update API Endpoints**

   Old endpoint:
   ```python
   @app.post("/api/interact")
   async def interact(request: InteractionRequest):
       result = await orchestrator.process_interaction(
           user_input=request.message,
           persona_id=request.persona_id
       )
   ```

   New endpoint:
   ```python
   @app.post("/agents/execute")
   async def execute_agent(request: AgentRequest):
       result = await orchestra_adapter.execute_agent(
           agent_id=request.agent_id,
           context={
               "task": request.task,
               "persona_id": request.persona_id
           }
       )
   ```

2. **Update Client Code**
   ```javascript
   // Old client
   const response = await fetch('/api/interact', {
       method: 'POST',
       body: JSON.stringify({
           message: 'Hello',
           persona_id: 'cherry'
       })
   });

   // New client
   const response = await fetch('/agents/execute', {
       method: 'POST',
       body: JSON.stringify({
           agent_id: 'researcher',
           task: 'Research AI trends',
           persona_id: 'cherry'
       })
   });
   ```

### Phase 5: Tool Integration

1. **Add Tools to Agents**
   ```bash
   curl -X POST "http://${SERVICE_IP}:8080/agents/researcher/tools" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "web_search",
       "description": "Search the web",
       "parameters": {
         "query": "string",
         "max_results": "integer"
       }
     }'
   ```

2. **Implement Tool Handlers**
   ```python
   class WebSearchTool:
       async def execute(self, query: str, max_results: int = 5):
           # Tool implementation
           return results
   ```

## Testing and Validation

### 1. Health Checks
```bash
# Check SuperAGI health
curl http://${SERVICE_IP}:8080/health

# Check agent availability
curl http://${SERVICE_IP}:8080/agents
```

### 2. Integration Tests
```python
# Test agent execution
async def test_agent_execution():
    response = await client.post("/agents/execute", json={
        "agent_id": "researcher",
        "task": "Test research task"
    })
    assert response.status_code == 200
    assert "output" in response.json()["result"]
```

### 3. Performance Testing
```bash
# Load test with concurrent agents
ab -n 1000 -c 10 -p request.json -T application/json \
   http://${SERVICE_IP}:8080/agents/execute
```

## Rollback Plan

If issues arise during migration:

1. **Keep Original Services Running**
   - Don't delete Cloud Run services immediately
   - Run SuperAGI in parallel initially

2. **Feature Flags**
   ```python
   USE_SUPERAGI = os.getenv("USE_SUPERAGI", "false") == "true"

   if USE_SUPERAGI:
       result = await superagi_adapter.execute()
   else:
       result = await orchestrator.process()
   ```

3. **Data Backup**
   ```bash
   # Backup Firestore
   gcloud firestore export gs://${BUCKET}/backups/$(date +%Y%m%d)
   ```

## Monitoring and Observability

### 1. Prometheus Metrics
```yaml
# SuperAGI exposes metrics at /metrics
scrape_configs:
  - job_name: 'superagi'
    static_configs:
      - targets: ['superagi:8080']
```

### 2. Logging
```bash
# View logs
kubectl logs -f deployment/superagi -n superagi

# Stream to Cloud Logging
kubectl logs deployment/superagi -n superagi | \
  gcloud logging write superagi-logs --severity=INFO
```

### 3. Dashboards
- Use Grafana for metrics visualization
- Set up alerts for agent failures
- Monitor memory usage and response times

## Best Practices

1. **Agent Design**
   - Keep agents focused on specific tasks
   - Use tools for external integrations
   - Enable memory for stateful conversations

2. **Resource Management**
   - Set appropriate CPU/memory limits
   - Use horizontal pod autoscaling
   - Monitor DragonflyDB memory usage

3. **Security**
   - Use Workload Identity for GCP access
   - Store secrets in Secret Manager
   - Enable network policies in GKE

## Troubleshooting

### Common Issues

1. **Agent Not Found**
   ```bash
   # Check agent registration
   kubectl exec -it deployment/superagi -n superagi -- \
     python -c "from orchestra_adapter import *; print(list_agents())"
   ```

2. **Memory Connection Failed**
   ```bash
   # Test Redis connection
   kubectl exec -it deployment/dragonfly -n superagi -- \
     redis-cli ping
   ```

3. **Slow Response Times**
   ```bash
   # Check resource usage
   kubectl top pods -n superagi

   # Scale if needed
   kubectl scale deployment/superagi --replicas=5 -n superagi
   ```

## Support and Resources

- SuperAGI Documentation: https://docs.superagi.com
- Orchestra AI Issues: https://github.com/your-org/orchestra/issues
- Community Discord: https://discord.gg/superagi

## Next Steps

After successful migration:

1. **Optimize Agent Performance**
   - Fine-tune max_iterations
   - Add specialized tools
   - Implement caching strategies

2. **Expand Capabilities**
   - Integrate more external services
   - Build custom tools
   - Create agent teams

3. **Production Hardening**
   - Set up multi-region deployment
   - Implement disaster recovery
   - Add comprehensive monitoring
