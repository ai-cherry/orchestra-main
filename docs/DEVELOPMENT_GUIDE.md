# AI Orchestra Development Guide

## Overview

This guide covers local development setup, testing procedures, debugging techniques, and best practices for contributing to the AI Orchestra project.

## Development Environment Setup

### Prerequisites

- Python 3.10 (exactly - not 3.11+)
- Docker Desktop
- Google Cloud SDK (`gcloud`)
- Pulumi CLI
- kubectl
- Git

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd orchestra-main
   ```

2. **Create Python virtual environment**
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r infra/requirements.txt
   pip install -r requirements/dev.txt  # Development tools
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your values:
   # GCP_PROJECT_ID=your-project-id
   # OPENROUTER_API_KEY=your-api-key
   # Add other required variables
   ```

5. **Configure GCP authentication**
   ```bash
   gcloud auth login
   gcloud config set project $GCP_PROJECT_ID
   gcloud auth application-default login
   ```

## Local Development

### Running Services Locally

#### Option 1: Port Forwarding (Recommended)

If infrastructure is already deployed:

```bash
# Forward services to local ports
kubectl port-forward svc/superagi 8080:8080 -n superagi &
kubectl port-forward svc/mcp-mongodb 8081:8080 -n superagi &
kubectl port-forward svc/mcp-weaviate 8082:8080 -n superagi &
kubectl port-forward svc/dragonfly 6379:6379 -n superagi &
kubectl port-forward svc/mongodb 27017:27017 -n superagi &
```

#### Option 2: Local Docker Compose (For isolated development)

```bash
# Create local docker-compose.yml
cat > docker-compose.local.yml << 'EOF'
version: '3.8'
services:
  dragonfly:
    image: docker.dragonflydb.io/dragonflydb/dragonfly:latest
    ports:
      - "6379:6379"
    environment:
      - DRAGONFLY_max_memory=1gb

  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=localdev
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
EOF

# Start local services
docker-compose -f docker-compose.local.yml up -d
```

### Code Structure

```
orchestra-main/
├── infra/                    # Infrastructure as Code (Pulumi)
│   ├── components/          # Reusable Pulumi components
│   └── main.py             # Main infrastructure definition
├── scripts/                 # Automation and utility scripts
│   ├── mcp_integration.py  # MCP client implementation
│   └── deploy_*.sh         # Deployment scripts
├── tests/                   # Test suites
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── docs/                    # Documentation
└── requirements/            # Python dependencies
```

### Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and test locally**
   ```bash
   # Run unit tests
   pytest tests/unit/

   # Run specific test
   pytest tests/unit/test_mcp_integration.py::test_mongodb_query

   # Run with coverage
   pytest --cov=scripts --cov-report=html
   ```

3. **Format and lint code**
   ```bash
   # Format with Black
   black scripts/ tests/

   # Lint with pylint
   pylint scripts/

   # Type check with mypy
   mypy scripts/
   ```

4. **Test infrastructure changes**
   ```bash
   cd infra
   pulumi preview --stack dev
   ```

5. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: add natural language query support"
   git push origin feature/your-feature-name
   ```

## Testing

### Unit Tests

Located in `tests/unit/`:

```python
# Example unit test
import pytest
from scripts.mcp_integration import MCPIntegration

def test_mcp_config():
    config = MCPConfig(timeout=30)
    assert config.timeout == 30
    assert config.mongodb_endpoint == "http://mcp-mongodb:8080"
```

Run unit tests:
```bash
pytest tests/unit/ -v
```

### Integration Tests

Located in `tests/integration/`:

```bash
# Run integration tests (requires deployed infrastructure)
pytest tests/integration/ -v

# Run specific integration test
pytest tests/integration/test_mcp_servers.py -v
```

### Infrastructure Tests

Test infrastructure deployment:
```bash
python scripts/test_infrastructure.py
```

### Manual Testing

1. **Test MCP queries**
   ```python
   # Start Python REPL
   python

   >>> import asyncio
   >>> from scripts.mcp_integration import MCPIntegration
   >>>
   >>> async def test():
   ...     mcp = MCPIntegration()
   ...     result = await mcp.query_mongodb("Show all agents")
   ...     print(result)
   >>>
   >>> asyncio.run(test())
   ```

2. **Test API endpoints**
   ```bash
   # Health check
   curl http://localhost:8080/health

   # Test agent execution
   curl -X POST http://localhost:8080/execute \
     -H "Content-Type: application/json" \
     -d '{"agent_type": "researcher", "task": "Find information about AI"}'
   ```

## Debugging

### Common Issues and Solutions

#### 1. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'mcp'`

**Solution**:
```bash
# Ensure you're in virtual environment
which python  # Should show venv path

# Install missing dependencies
pip install mcp
```

#### 2. Connection Errors

**Problem**: Cannot connect to services

**Solution**:
```bash
# Check if services are running
kubectl get pods -n superagi

# Check service endpoints
kubectl get svc -n superagi

# Verify port forwarding
ps aux | grep "port-forward"
```

#### 3. Authentication Errors

**Problem**: GCP authentication failures

**Solution**:
```bash
# Re-authenticate
gcloud auth application-default login

# Check current project
gcloud config get-value project

# Set correct project
gcloud config set project $GCP_PROJECT_ID
```

### Debugging Tools

1. **Kubernetes debugging**
   ```bash
   # Get pod logs
   kubectl logs -f deployment/superagi -n superagi

   # Describe pod for events
   kubectl describe pod <pod-name> -n superagi

   # Execute commands in pod
   kubectl exec -it <pod-name> -n superagi -- /bin/bash
   ```

2. **Pulumi debugging**
   ```bash
   # Export stack state
   pulumi stack export > stack-state.json

   # View detailed logs
   pulumi up --logtostderr -v=9 2> pulumi-debug.log
   ```

3. **Python debugging**
   ```python
   # Add breakpoints
   import pdb; pdb.set_trace()

   # Or use VS Code debugger with launch.json
   ```

## Best Practices

### Code Style

1. **Follow PEP 8**
   - Use Black for automatic formatting
   - Maximum line length: 88 characters

2. **Type Hints**
   ```python
   from typing import Dict, List, Optional

   def process_query(query: str, limit: Optional[int] = 10) -> Dict[str, Any]:
       """Process a natural language query."""
       pass
   ```

3. **Docstrings**
   ```python
   def complex_function(param1: str, param2: int) -> bool:
       """
       Brief description of function.

       Args:
           param1: Description of param1
           param2: Description of param2

       Returns:
           Description of return value

       Raises:
           ValueError: When param2 is negative
       """
       pass
   ```

### Git Workflow

1. **Commit Messages**
   - Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
   - Keep first line under 50 characters
   - Add detailed description if needed

2. **Pull Requests**
   - Create from feature branch to main
   - Include description of changes
   - Reference any related issues
   - Ensure all tests pass

### Security

1. **Never commit secrets**
   - Use `.env` files (gitignored)
   - Use GCP Secret Manager
   - Use Pulumi secrets

2. **Dependency management**
   - Regularly update dependencies
   - Use `pip-audit` for vulnerability scanning
   - Pin versions in requirements files

## IDE Setup

### VS Code (Recommended)

1. **Install extensions**
   - Python
   - Pylance
   - Black Formatter
   - GitLens
   - Kubernetes
   - YAML

2. **Settings** (`.vscode/settings.json`)
   ```json
   {
     "python.defaultInterpreterPath": "./venv/bin/python",
     "python.formatting.provider": "black",
     "python.linting.enabled": true,
     "python.linting.pylintEnabled": true,
     "editor.formatOnSave": true,
     "files.trimTrailingWhitespace": true
   }
   ```

3. **Launch configuration** (`.vscode/launch.json`)
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Python: Current File",
         "type": "python",
         "request": "launch",
         "program": "${file}",
         "console": "integratedTerminal",
         "env": {
           "PYTHONPATH": "${workspaceFolder}"
         }
       }
     ]
   }
   ```

### Cursor AI

See [Cursor AI Optimization Guide](CURSOR_AI_OPTIMIZATION_GUIDE.md) for AI-assisted development.

## Contributing

1. **Before starting**
   - Check existing issues and PRs
   - Discuss major changes in an issue first
   - Follow the code style guide

2. **Testing requirements**
   - All new features must have tests
   - Maintain or improve code coverage
   - Integration tests for infrastructure changes

3. **Documentation**
   - Update relevant documentation
   - Add docstrings to new functions
   - Update README if needed

## Resources

- [Python Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [Pulumi Best Practices](https://www.pulumi.com/docs/guides/self-hosted/components/)
- [Kubernetes Debugging](https://kubernetes.io/docs/tasks/debug/)
- [GCP Documentation](https://cloud.google.com/docs)
