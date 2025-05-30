# AI Orchestrator

This repository hosts a single-node deployment of the AI Orchestrator platform. Core services run under Docker Compose on a Vultr bare-metal server provisioned with Pulumi.

## Key Components

- **core/** – FastAPI orchestrator services and agent registry
- **mcp_server/** – Model Context Protocol (MCP) endpoints
- **admin-ui/** – Vite/React admin interface
- **infra/** – Pulumi stacks and components for Vultr
- **scripts/** – Utility scripts including `snapshot.sh` for nightly backups

## Development

1. Create a Python 3.10 virtualenv and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements/dev.txt
   ```
2. Spin up local services with Docker Compose:
   ```bash
   ./run_docker_environment.sh
   ```
3. Access the Admin UI at <http://localhost:3001>.

More details on agent registration and recovery procedures can be found in
[docs/AGENTIC_RETRIEVAL.md](docs/AGENTIC_RETRIEVAL.md) and
[docs/RECOVERY.md](docs/RECOVERY.md).
