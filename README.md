# Orchestra AI

This repository contains the "AI-Orchestrator" platform running on a single Vultr bare-metal server. Core services are packaged with Docker Compose and provisioned via Pulumi.

## Services
- **Weaviate 1.30** with Agents and ACORN
- **PostgreSQL 16** (+pgvector)
- **FastAPI Orchestrator & MCP servers** served by Gunicorn/Uvicorn
- **Langfuse** for tracing
- **Optional Redis/Dragonfly** cache
- **Admin UI** built with Vite/React

## Development
1. Create a Python 3.10 virtualenv and install `requirements/dev.txt`.
2. Run `./run_docker_environment.sh` to start the stack locally.
3. The Admin UI lives in `admin-ui/` and uses pnpm. Run `pnpm dev` to start.

## Infrastructure
Pulumi scripts in `infra/` provision the Vultr server and schedule nightly volume snapshots via `snapshot.sh`. See [docs/RECOVERY.md](docs/RECOVERY.md) for restore instructions.

---
This README provides only a high-level view. See the `docs/` folder for more details on agents, retrieval logic, and operations.
