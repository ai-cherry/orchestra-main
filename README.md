# Orchestra AI

A single-node platform for running multi-agent workflows, retrieval-augmented generation, and tool-based orchestration. Infrastructure is provisioned via Pulumi on Vultr, and services are managed with Docker Compose.

## Project Layout
- **core/** – FastAPI orchestrator and supporting modules
- **mcp_server/** – MCP services for memory and direct Weaviate access
- **admin-ui/** – Vite/React Admin interface
- **infra/** – Pulumi code for the Vultr server and nightly snapshot automation
- **scripts/** – Utility scripts including `snapshot.sh` and benchmarking tools

## Getting Started
1. Install Python 3.10 and Node.js 20
2. Clone the repo and run:
   ```bash
   pip install -r requirements/dev.txt
   cd admin-ui && pnpm install
   ```
3. Use `./run_docker_environment.sh` to start the local stack.
4. See `docs/AGENTIC_RETRIEVAL.md` and `docs/RECOVERY.md` for advanced features and recovery instructions.

## Development Notes
CI and deployment run on GitHub Actions. Nightly snapshots of the `/data` volume are created on the Vultr server via `snapshot.sh`. All secrets are stored in GitHub Secrets and Pulumi config.

