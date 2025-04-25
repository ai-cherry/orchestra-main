# Orchestra Vertex AI Agent Manager

A Python package for automating infrastructure and operational tasks using Vertex AI Agents.

## Overview

This package provides integration with Google Cloud Vertex AI Agents to automate various tasks in the Orchestra platform, including:

- Infrastructure provisioning and management with Terraform
- Automated agent team creation and deployment
- Vector embedding management for semantic search
- Game session management for interactive experiences
- Resource monitoring and cost tracking

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/ai-cherry/orchestra-main.git
cd orchestra-main

# Install the package
cd packages/vertex_client
pip install -e .
```

### Requirements

This package requires Python 3.8+ and the following dependencies:

- Google Cloud libraries (aiplatform, pubsub, run, secretmanager)
- FastAPI and Uvicorn for API endpoints
- Other utilities like python-dotenv and tenacity

See `requirements.txt` for the full list of dependencies.

## Usage

The package provides three main interfaces:

1. **Python API**: Direct integration in Python code
2. **Command-line Interface**: For use in scripts and terminals
3. **REST API**: For integration with web applications

### Python API

```python
# Example: Running the initialization script
from packages.vertex_client import trigger_vertex_task

result = trigger_vertex_task("run init script")
print(f"Status: {result['status']}")

# Example: Applying Terraform configuration
result = trigger_vertex_task("apply terraform dev")
print(f"Status: {result['status']}")

# Example: Creating an agent team
result = trigger_vertex_task(
    "create agent team clinical-trial-followup", 
    roles=["planner", "doer", "reviewer"]
)
print(f"Team created: {result['team']}")
```

### Command-line Interface

The package includes a CLI that can be used to trigger tasks:

```bash
# Run the initialization script
vertex-cli init

# Apply Terraform configuration
vertex-cli terraform dev

# Create an agent team
vertex-cli team clinical-trial-followup --roles planner doer reviewer

# Manage embeddings
vertex-cli embeddings psychology-profile --data "Example text for embedding"

# Manage a game session
vertex-cli game trivia session_123 answer_a

# Monitor resources
vertex-cli monitor

# For help
vertex-cli --help
```

### REST API

The package also provides a FastAPI-based REST API that can be used for web integration:

```bash
# Start the API server
cd packages/vertex_client
python -m api
```

Then, you can make HTTP requests to the API:

```bash
# Trigger a task
curl -X POST http://localhost:8000/vertex/trigger-task \
  -H "Content-Type: application/json" \
  -d '{"task": "run init script"}'

# Apply Terraform
curl -X POST http://localhost:8000/vertex/terraform/dev

# Create an agent team
curl -X POST http://localhost:8000/vertex/agent-teams/clinical-trial-followup \
  -H "Content-Type: application/json" \
  -d '{"roles": ["planner", "doer", "reviewer"]}'

# Manage embeddings
curl -X POST http://localhost:8000/vertex/embeddings/psychology-profile \
  -H "Content-Type: application/json" \
  -d '{"data": "Example text for embedding"}'

# Manage a game session
curl -X POST http://localhost:8000/vertex/games/trivia/session_123 \
  -H "Content-Type: application/json" \
  -d '{"player_action": "answer_a"}'

# Monitor resources
curl -X POST http://localhost:8000/vertex/monitor
```

## Task Types

The package supports the following task types:

### Infrastructure Management

- `run init script`: Run the infrastructure initialization script
- `apply terraform <workspace>`: Apply Terraform configuration for a workspace (dev, stage, prod)

### Agent Team Management

- `create agent team <team_name>`: Create and deploy an agent team

### Vector Embedding Management

- `manage embeddings <index_name>`: Manage embeddings in Vertex AI Vector Search

### Game Session Management

- `manage game session <game_type> <session_id> <player_action>`: Manage a live game session

### Resource Monitoring

- `monitor resources`: Monitor GCP resource usage and costs

## Development

To set up a development environment:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/
```

## License

MIT License

## Credits

Developed by the Orchestra Team.
