# Infrastructure Overview

The Orchestra platform runs on a single bare-metal Vultr server managed with Pulumi. All secrets are stored in GitHub and Pulumi config. Core services run via Docker Compose: Weaviate, PostgreSQL, the orchestrator, MCP server, Langfuse, and optional Redis.

## Key Components
- **Pulumi with Vultr provider** provisions the server, block storage volume, firewall rules, and installs a nightly snapshot cron job using `/root/snapshot.sh`.
- **Docker Compose** (`deploy/docker-compose.vultr.yml`) defines the production stack with restart policies and resource limits.
- **Admin UI** builds with Vite and is served statically by the orchestrator container.

## Getting Started
1. Install Pulumi and Python 3.10.
2. Set `VULTR_API_KEY` and `PULUMI_ACCESS_TOKEN` as environment variables.
3. From the `infra/` directory run:
   ```bash
   pip install -r requirements.txt
   pulumi stack init dev  # first time only
   pulumi up
   ```
4. The stack outputs the public IP of the server. SSH and run `docker compose` to manage services.

## Snapshot Recovery
Snapshots of the `/data` volume are created nightly. Refer to [RECOVERY.md](RECOVERY.md) for instructions on restoring a snapshot or triggering a manual backup.
