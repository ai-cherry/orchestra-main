# Orchestra AI Infrastructure Status

The migration to a Vultr-based stack is complete. All previous DigitalOcean and Paperspace resources have been shut down.

## Current Server
- **Specs:** 16 vCPU / 64 GB RAM / 320 GB NVMe
- **OS:** Ubuntu 24.04 LTS
- **Services:** Docker Compose stack running Weaviate 1.30 (Agents & ACORN), PostgreSQL 16 + pgvector, Orchestrator & MCP, Langfuse, optional Redis.

## Automation
- Nightly snapshots of the `/data` volume are created via `scripts/snapshot.sh` at 03:00 UTC using the Vultr CLI.

## Cleanup Summary
- DragonflyDB Cloud, MongoDB Atlas, and Weaviate Cloud have been replaced with local services.
- All DigitalOcean droplets and Paperspace VMs are terminated.

## Cost Overview
- Single Vultr server: **≈ $160/month**.

The infrastructure is now simplified and easier to manage with Pulumi and GitHub Actions.
