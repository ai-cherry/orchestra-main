# AI conductor System Guide

## Overview

The AI conductor is a comprehensive workflow coordination system that coordinates between EigenCode (code analysis), Cursor AI (implementation), and Roo Code (refinement) to provide automated code analysis, optimization, and improvement capabilities.

## Architecture

### Core Components

1. **Workflow conductor** (`ai_components/coordination/ai_conductor.py`)
   - Manages workflow execution with dependency resolution
   - Implements parallel task execution
   - Provides checkpointing and failure recovery
   - Handles context management via MCP

2. **Agent Coordinator**
   - **EigenCode Agent**: Performs holistic code analysis
   - **Cursor AI Agent**: Implements performance-focused changes
   - **Roo Code Agent**: Refines technology stack for ease of use

3. **Context Management**
   - **PostgreSQL**: Stores coordination logs and audit trails
   - **Weaviate Cloud**: Vector storage for context and results
   - **MCP Server**: Real-time task management and coordination

4. **Integration Layer**
   - **Airbyte Cloud**: Syncs data between PostgreSQL and Weaviate
   - **GitHub Actions**: Automated deployment pipeline
   - **Pulumi**: Infrastructure as Code for Lambda deployment

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Access to Weaviate Cloud
- Airbyte Cloud account (optional)
- Lambda account (for deployment)
- GitHub repository with Secrets configured

### Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/cherry_ai-main.git
cd cherry_ai-main

# Run quick start script
chmod +x quick_start_conductor.sh
./quick_start_conductor.sh
```

### Manual Installation

1. **Set up environment variables**
   ```bash
   cp ai_components/configs/.env.template ai_components/configs/.env
   # Edit .env with your credentials
   ```

2. **Install dependencies**
   ```bash
   cd ai_components
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run installation script**
   ```bash
   sudo ./install_ai_tools.sh
   ```

4. **Initialize services**
   ```bash
   # Initialize Weaviate schema
   python scripts/initialize_weaviate.py
   
   # Configure Airbyte
   python scripts/configure_airbyte.py
   
   # Start MCP server
   sudo systemctl start conductor-mcp
   ```

## Configuration

### Environment Variables

Required environment variables (set in GitHub Secrets for deployment):

```bash
# PostgreSQL
POSTGRES_HOST=your_postgres_host
POSTGRES_PORT=5432
POSTGRES_DB=conductor_db
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password

# Weaviate Cloud
WEAVIATE_URL=https://your-instance.weaviate.network
WEAVIATE_API_KEY=your_weaviate_api_key

# Airbyte Cloud (optional)
AIRBYTE_API_URL=https://api.airbyte.com
AIRBYTE_API_KEY=your_airbyte_api_key
AIRBYTE_WORKSPACE_ID=your_workspace_id

# AI Tools (when available)
EIGENCODE_API_KEY=your_eigencode_api_key
CURSOR_AI_API_KEY=your_cursor_ai_api_key
ROO_CODE_API_KEY=your_roo_code_api_key

# Lambda (for deployment)
LAMBDA_API_KEY=your_LAMBDA_API_KEY
```

### conductor Configuration

Edit `ai_components/configs/conductor_config.yaml`:

```yaml
conductor:
  workflow_timeout: 3600  # 1 hour
  max_parallel_tasks: 5
  checkpoint_interval: 300  # 5 minutes

agents:
  eigencode:
    enabled: true
    timeout: 600
    retry_attempts: 3
```

## Usage

### CLI Commands

The conductor provides a comprehensive CLI interface:

```bash
# Show help
./ai_components/conductor_cli.py --help

# Analyze codebase
./ai_components/conductor_cli.py analyze \
  --codebase /path/to/code \
  --output analysis.json

# Implement changes based on analysis
./ai_components/conductor_cli.py implement \
  --analysis analysis.json \
  --focus performance

# Refine technology stack
./ai_components/conductor_cli.py refine \
  --stack python_postgres_weaviate

# Run full coordination workflow
./ai_components/conductor_cli.py cherry_aite \
  --config configs/example_workflow.json
```

### Python API

```python
import asyncio
from ai_components.coordination.ai_conductor import (
    Workflowconductor, TaskDefinition, AgentRole
)

async def run_analysis():
    # Create conductor
    conductor = Workflowconductor()
    
    # Create workflow
    workflow_id = "my_analysis_workflow"
    context = await conductor.create_workflow(workflow_id)
    
    # Define tasks
    tasks = [
        TaskDefinition(
            task_id="analyze",
            name="Analyze Codebase",
            agent_role=AgentRole.ANALYZER,
            inputs={"codebase_path": "/path/to/code"}
        ),
        TaskDefinition(
            task_id="optimize",
            name="Optimize Performance",
            agent_role=AgentRole.IMPLEMENTER,
            inputs={"focus": "performance"},
            dependencies=["analyze"]
        )
    ]
    
    # Execute workflow
    result = await conductor.execute_workflow(workflow_id, tasks)
    print(f"Results: {result.results}")

# Run the workflow
asyncio.run(run_analysis())
```

### Workflow Configuration

Create custom workflows in JSON format:

```json
{
  "workflow_id": "custom_optimization",
  "description": "Custom optimization workflow",
  "tasks": [
    {
      "id": "analyze_performance",
      "name": "Analyze Performance Bottlenecks",
      "agent": "analyzer",
      "inputs": {
        "codebase_path": ".",
        "focus_areas": ["database", "api", "algorithms"]
      }
    },
    {
      "id": "implement_optimizations",
      "name": "Implement Optimizations",
      "agent": "implementer",
      "inputs": {
        "optimization_level": "aggressive"
      },
      "dependencies": ["analyze_performance"]
    }
  ]
}
```

## Deployment

### GitHub Actions Workflow

The system includes a comprehensive GitHub Actions workflow for automated deployment:

1. **Push to main branch** triggers deployment
2. **Validates** configuration and secrets
3. **Runs tests** with coverage reporting
4. **Builds** deployment artifacts
5. **Deploys infrastructure** via Pulumi
6. **Deploys application** to Lambda
7. **Runs post-deployment** tasks (Weaviate init, Airbyte config)
8. **Executes smoke tests**
9. **Sends notifications** on completion

### Manual Deployment

```bash
# Deploy infrastructure
cd infrastructure
pulumi up

# Deploy application
ssh root@your-server-ip
cd /opt/ai-conductor
git pull
systemctl restart conductor-mcp
systemctl restart ai-conductor
```

## Monitoring

### Service Health

```bash
# Check MCP server status
systemctl status conductor-mcp

# Check conductor service
systemctl status ai-conductor

# View MCP server logs
sudo journalctl -u conductor-mcp -f

# View conductor logs
tail -f ai_components/logs/conductor.log
```

### Metrics

Access monitoring dashboards:
- Prometheus: `http://your-server-ip:9090`
- Grafana: `http://your-server-ip:3000`

### Database Queries

```sql
-- View recent coordination logs
SELECT * FROM coordination_logs 
ORDER BY created_at DESC 
LIMIT 100;

-- Check workflow status
SELECT workflow_id, status, COUNT(*) 
FROM coordination_logs 
GROUP BY workflow_id, status;

-- Find failed tasks
SELECT * FROM coordination_logs 
WHERE status = 'failed' 
ORDER BY created_at DESC;
```

## Testing

### Run Unit Tests

```bash
cd ai_components
pytest tests/ -v --cov=coordination --cov-report=html
```

### Run Integration Tests

```bash
python scripts/smoke_tests.py --server localhost --mcp-url http://localhost:8080
```

## Troubleshooting

### Common Issues

#### 1. EigenCode Installation Failed

**Problem**: EigenCode service returns 404 error during installation.

**Solutions**:
```bash
# Run the alternative installation script
python scripts/eigencode_installer.py

# Check installation logs
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT * FROM coordination_logs WHERE agent_role='installer' ORDER BY created_at DESC LIMIT 10;"

# Query Weaviate for installation attempts
python -c "
from ai_components.coordination.ai_conductor import WeaviateManager
wm = WeaviateManager()
results = wm.retrieve_context('eigencode_installation')
for r in results:
    print(r)
"
```

**Alternative Methods**:
- Check GitHub releases: `python scripts/eigencode_installer.py --method github`
- Try package managers: `snap search eigencode` or `npm search eigencode`
- Contact API directly with your API key in environment

**Workarounds**:
```python
# Use mock EigenCode agent for testing
class MockEigenCodeAgent:
    async def execute(self, task, context):
        return {
            "analysis": {
                "status": "mock_analysis",
                "message": "Using placeholder until EigenCode is available"
            }
        }
```

#### 2. Database Connection Failed

**Diagnostics**:
```bash
# Test connection
psql "postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB?sslmode=require"

# Check firewall rules
sudo iptables -L -n | grep 5432

# Verify SSL certificate
openssl s_client -connect $POSTGRES_HOST:5432 -starttls postgres
```

**Performance Tuning**:
```sql
-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Optimize connection pool
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
```

#### 3. Weaviate Connection Failed

**Debugging Steps**:
```python
# Test Weaviate connection with detailed logging
import weaviate
import logging

logging.basicConfig(level=logging.DEBUG)

client = weaviate.Client(
    url=os.environ.get('WEAVIATE_URL'),
    auth_client_secret=weaviate.AuthApiKey(api_key=os.environ.get('WEAVIATE_API_KEY')),
    additional_headers={'X-Debug': 'true'}
)

print(f"Client ready: {client.is_ready()}")
print(f"Schema: {client.schema.get()}")
```

#### 4. MCP Server Issues

**Advanced Diagnostics**:
```bash
# Check port binding
sudo netstat -tlnp | grep 8080

# Test MCP endpoints
curl -X GET http://localhost:8080/docs
curl -X GET http://localhost:8080/tasks
curl -X POST http://localhost:8080/tasks -H "Content-Type: application/json" \
  -d '{"task_id":"test","name":"Test","agent_role":"analyzer","inputs":{}}'

# Monitor resource usage
htop -p $(pgrep -f coordinator_server)
```

### Performance Issues

#### Slow Workflow Execution

**Diagnosis Script**:
```python
# scripts/diagnose_performance.py
import asyncio
import time
from ai_components.coordination.ai_conductor import Workflowconductor

async def measure_performance():
    conductor = Workflowconductor()
    
    # Measure task creation time
    start = time.time()
    context = await conductor.create_workflow("perf_test")
    creation_time = time.time() - start
    
    print(f"Workflow creation: {creation_time:.3f}s")
    
    # Check database query performance
    with conductor.db_logger._get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("EXPLAIN ANALYZE SELECT * FROM coordination_logs LIMIT 1000")
            print(cur.fetchall())
```

## Performance Optimization

### 1. Workflow Optimization Strategies

#### Task Parallelization
```python
# Optimize task dependencies for maximum parallelization
def optimize_task_graph(tasks: List[TaskDefinition]) -> List[TaskDefinition]:
    """Analyze and optimize task dependencies"""
    # Build dependency graph
    graph = defaultdict(list)
    for task in tasks:
        for dep in task.dependencies:
            graph[dep].append(task.task_id)
    
    # Find tasks that can run in parallel
    levels = []
    visited = set()
    
    # Topological sort with level tracking
    def get_level(task_id, memo={}):
        if task_id in memo:
            return memo[task_id]
        
        task = next(t for t in tasks if t.task_id == task_id)
        if not task.dependencies:
            memo[task_id] = 0
        else:
            memo[task_id] = max(get_level(dep) for dep in task.dependencies) + 1
        
        return memo[task_id]
    
    # Group by level for parallel execution
    for task in tasks:
        level = get_level(task.task_id)
        task.priority = -level  # Higher priority for earlier levels
    
    return sorted(tasks, key=lambda t: t.priority)
```

#### Connection Pooling
```python
# Enhanced database connection pooling
from psycopg2 import pool

class OptimizedDatabaseLogger(DatabaseLogger):
    def __init__(self):
        super().__init__()
        self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=20,
            **self.connection_params
        )
    
    def _get_connection(self):
        return self.connection_pool.getconn()
    
    def _put_connection(self, conn):
        self.connection_pool.putconn(conn)
```

#### Caching Strategy
```python
# Implement intelligent caching
class CachedWeaviateManager(WeaviateManager):
    def __init__(self):
        super().__init__()
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def retrieve_context(self, workflow_id: str, limit: int = 10) -> List[Dict]:
        cache_key = f"{workflow_id}:{limit}"
        
        # Check cache
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if time.time() - entry['timestamp'] < self.cache_ttl:
                return entry['data']
        
        # Fetch from Weaviate
        data = super().retrieve_context(workflow_id, limit)
        
        # Update cache
        self.cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
        
        return data
```

### 2. Database Performance Tuning

#### Index Optimization
```sql
-- Create optimized indexes
CREATE INDEX CONCURRENTLY idx_logs_workflow_task
ON coordination_logs(workflow_id, task_id);

CREATE INDEX CONCURRENTLY idx_logs_created_status
ON coordination_logs(created_at DESC, status);

-- Partial index for active workflows
CREATE INDEX CONCURRENTLY idx_active_workflows
ON coordination_logs(workflow_id)
WHERE status IN ('pending', 'running');

-- Analyze table statistics
ANALYZE coordination_logs;
```

#### Query Optimization
```python
# Batch insert operations
class BatchDatabaseLogger(DatabaseLogger):
    def __init__(self, batch_size=100):
        super().__init__()
        self.batch_size = batch_size
        self.batch_buffer = []
    
    def log_action(self, **kwargs):
        self.batch_buffer.append(kwargs)
        
        if len(self.batch_buffer) >= self.batch_size:
            self.flush()
    
    def flush(self):
        if not self.batch_buffer:
            return
        
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Use COPY for bulk insert
                cur.execute("""
                    COPY coordination_logs (
                        workflow_id, task_id, agent_role,
                        action, status, metadata, error_message
                    ) FROM STDIN WITH (FORMAT CSV)
                """)
                
                for log in self.batch_buffer:
                    cur.copy_write(','.join([
                        log['workflow_id'],
                        log['task_id'],
                        log['agent_role'],
                        log['action'],
                        log['status'],
                        json.dumps(log.get('metadata', {})),
                        log.get('error', '')
                    ]) + '\n')
                
                cur.copy_end()
                conn.commit()
        
        self.batch_buffer.clear()
```

### 3. Vector Storage Optimization

#### Batch Operations
```python
# Optimize Weaviate batch operations
class OptimizedWeaviateManager(WeaviateManager):
    def batch_store_context(self, contexts: List[Dict]):
        """Store multiple contexts in a single batch"""
        with self.client.batch as batch:
            batch.batch_size = 100
            
            for ctx in contexts:
                batch.add_data_object(
                    data_object={
                        "workflow_id": ctx['workflow_id'],
                        "task_id": ctx['task_id'],
                        "context_type": ctx['context_type'],
                        "content": ctx['content'],
                        "metadata": json.dumps(ctx.get('metadata', {})),
                        "timestamp": datetime.now().isoformat()
                    },
                    class_name="coordinationContext"
                )
```

### 4. API Call Optimization

#### Circuit Breaker Pattern
```python
# Implement circuit breaker for external APIs
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
    
    async def call(self, func, *args, **kwargs):
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'half-open'
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == 'half-open':
                self.state = 'closed'
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'open'
            
            raise e
```

## Security Best Practices

### 1. API Secret Management

#### Secure Secret Storage
```python
# Enhanced secret manager with encryption
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class SecureSecretManager:
    def __init__(self, master_key: str = None):
        if not master_key:
            master_key = os.environ.get('MASTER_ENCRYPTION_KEY')
        
        # Derive encryption key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'conductor_salt',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.cipher = Fernet(key)
    
    def encrypt_secret(self, secret: str) -> str:
        """Encrypt a secret value"""
        return self.cipher.encrypt(secret.encode()).decode()
    
    def decrypt_secret(self, encrypted: str) -> str:
        """Decrypt a secret value"""
        return self.cipher.decrypt(encrypted.encode()).decode()
    
    def get_secret(self, key: str) -> Optional[str]:
        """Get and decrypt a secret"""
        encrypted = os.environ.get(f"ENCRYPTED_{key}")
        if encrypted:
            return self.decrypt_secret(encrypted)
        return os.environ.get(key)
```

#### API Key Rotation
```python
# Automated API key rotation
class APIKeyRotator:
    def __init__(self, rotation_interval=86400):  # 24 hours
        self.rotation_interval = rotation_interval
        self.last_rotation = {}
    
    async def rotate_if_needed(self, service: str):
        """Check and rotate API key if needed"""
        if service not in self.last_rotation:
            self.last_rotation[service] = 0
        
        if time.time() - self.last_rotation[service] > self.rotation_interval:
            await self.rotate_key(service)
            self.last_rotation[service] = time.time()
    
    async def rotate_key(self, service: str):
        """Rotate API key for a service"""
        # Implementation depends on service API
        pass
```

### 2. Database Security

#### Connection Security
```python
# Secure database connection with SSL
def get_secure_connection():
    return psycopg2.connect(
        host=os.environ.get('POSTGRES_HOST'),
        port=os.environ.get('POSTGRES_PORT'),
        database=os.environ.get('POSTGRES_DB'),
        user=os.environ.get('POSTGRES_USER'),
        password=os.environ.get('POSTGRES_PASSWORD'),
        sslmode='require',
        sslcert='/path/to/client-cert.pem',
        sslkey='/path/to/client-key.pem',
        sslrootcert='/path/to/ca-cert.pem'
    )
```

#### Query Sanitization
```python
# Prevent SQL injection
def safe_query(conn, query: str, params: tuple):
    """Execute query with parameter sanitization"""
    with conn.cursor() as cur:
        # Use parameterized queries
        cur.execute(query, params)
        return cur.fetchall()

# Example usage
results = safe_query(
    conn,
    "SELECT * FROM coordination_logs WHERE workflow_id = %s AND status = %s",
    (workflow_id, status)
)
```

### 3. Network Security

#### Request Validation
```python
# Validate and sanitize API requests
from pydantic import BaseModel, validator

class SecureTaskRequest(BaseModel):
    task_id: str
    name: str
    agent_role: str
    inputs: Dict
    
    @validator('task_id')
    def validate_task_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid task_id format')
        return v
    
    @validator('agent_role')
    def validate_agent_role(cls, v):
        allowed_roles = ['analyzer', 'implementer', 'refiner']
        if v not in allowed_roles:
            raise ValueError(f'Invalid agent_role. Must be one of: {allowed_roles}')
        return v
```

## Scalability Considerations

### 1. Horizontal Scaling

#### Multi-Instance Deployment
```python
# Load balancer for multiple conductor instances
class LoadBalancedconductor:
    def __init__(self, instances: List[str]):
        self.instances = instances
        self.current_instance = 0
    
    def get_next_instance(self) -> str:
        """Round-robin load balancing"""
        instance = self.instances[self.current_instance]
        self.current_instance = (self.current_instance + 1) % len(self.instances)
        return instance
    
    async def execute_workflow(self, workflow_id: str, tasks: List[TaskDefinition]):
        """Execute workflow on next available instance"""
        instance = self.get_next_instance()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{instance}/workflows",
                json={
                    "workflow_id": workflow_id,
                    "tasks": [t.dict() for t in tasks]
                }
            ) as response:
                return await response.json()
```

#### Distributed Task Queue
```python
# Redis-based task queue for distributed processing
import redis
import pickle

class DistributedTaskQueue:
    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url)
        self.queue_name = "conductor_tasks"
    
    def enqueue_task(self, task: TaskDefinition):
        """Add task to distributed queue"""
        self.redis_client.lpush(
            self.queue_name,
            pickle.dumps(task)
        )
    
    def dequeue_task(self) -> Optional[TaskDefinition]:
        """Get next task from queue"""
        data = self.redis_client.rpop(self.queue_name)
        if data:
            return pickle.loads(data)
        return None
```

### 2. Resource Management

#### Dynamic Resource Allocation
```python
# Kubernetes-based auto-scaling
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: conductor-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-conductor
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 3. Performance Monitoring

#### Metrics Collection
```python
# Prometheus metrics for monitoring
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
workflow_counter = Counter('conductor_workflows_total', 'Total workflows executed')
task_duration = Histogram('conductor_task_duration_seconds', 'Task execution duration')
active_workflows = Gauge('conductor_active_workflows', 'Number of active workflows')

# Use in conductor
class Monitoredconductor(Workflowconductor):
    async def execute_workflow(self, workflow_id: str, tasks: List[TaskDefinition]):
        workflow_counter.inc()
        active_workflows.inc()
        
        try:
            with task_duration.time():
                result = await super().execute_workflow(workflow_id, tasks)
            return result
        finally:
            active_workflows.dec()
```

## Future Enhancements

1. **Web UI**: Dashboard for workflow management
2. **More Agents**: Integration with additional AI tools
3. **Advanced Scheduling**: Cron-based workflow execution
4. **Multi-Cloud**: Support for AWS, GCP, Azure
5. **Enhanced Monitoring**: APM integration

## Support

- **Documentation**: This guide and inline code documentation
- **Issues**: Create GitHub issues for bugs or features
- **Logs**: Check application and system logs
- **Community**: Join our Discord/Slack channel

## License

[Your License Here]

---

**Note**: This system is designed for production use but requires proper configuration of all services and credentials. Always test in a development environment first.