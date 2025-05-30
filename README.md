# AI Orchestrator

This repository hosts a single-node deployment of the AI Orchestrator platform. Core services run via Docker Compose on a Vultr bare-metal instance provisioned with Pulumi.

## Services
- **Weaviate** with ACORN and Agents enabled
- **PostgreSQL 16** with `pgvector`
- **FastAPI Orchestrator** and **MCP servers**
- **Langfuse** for tracing
- Optional **Redis/Dragonfly** cache
- **Admin UI** built with Vite and React

## Development
1. Create a Python 3.10 virtualenv and install requirements:
   ```bash
   python3.10 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements/base.txt
   ```
2. Copy `env.example` to `.env` and update values or generate from Pulumi using `scripts/generate_env_from_pulumi.py`.
3. Start the full stack:
   ```bash
   ./run_docker_environment.sh
   ```

## Documentation
- [Agentic Retrieval](docs/AGENTIC_RETRIEVAL.md)
- [Recovery Guide](docs/RECOVERY.md)
- [Infrastructure Details](infra/README.md)

