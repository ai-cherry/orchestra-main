# Cherry AI Infrastructure Status

The platform now runs entirely on a single Vultr bare-metal server managed via Pulumi.

## Services
- **Weaviate** 1.30 with Agents and ACORN enabled
- **PostgreSQL** 16 with pgvector
- **conductor & MCP servers** using Uvicorn/Gunicorn workers
- **Langfuse** observability
- **Optional Redis/Dragonfly** cache

All services run under Docker Compose and are restarted automatically.

## Snapshots
A cron job on the server executes `scripts/snapshot.sh` each night at 03:00 UTC to create a Vultr volume snapshot of `/data`.

## Secrets
Secrets such as `VULTR_API_KEY`, `POSTGRES_DSN`, and `WEAVIATE_URL` are stored in GitHub Secrets and pulled into Pulumi during CI/CD.

## Deployment
- GitHub Actions builds and tests the code.
- `pulumi up` is run automatically on the `main` branch to apply changes.

The legacy DigitalOcean and Paperspace resources have been removed.
