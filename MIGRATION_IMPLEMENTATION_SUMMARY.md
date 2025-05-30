# Migration Implementation Summary

This document captures the final move away from DigitalOcean and Paperspace to a single Vultr server managed with Pulumi.

## Highlights
- **Infrastructure**: `vultr_server_component.py` provisions the bare-metal instance and block storage. Snapshots are automated with `scripts/snapshot.sh`.
- **Data**: Weaviate 1.30 with Agents is now the primary vector store. PostgreSQL 16 + pgvector provides ACID storage. DragonflyDB is optional.
- **Automation**: GitHub Actions builds images, runs tests, and performs `pulumi up` on merges to main.

## Migration Steps
1. Pulumi deployed the new Vultr stack.
2. Data from DragonflyDB and MongoDB Atlas was migrated into local services.
3. Legacy droplets and Paperspace VMs were terminated.
4. Admin UI and API endpoints were updated to target the new server.

## Current State
All services run via Docker Compose on the Vultr server. Pulumi and GitHub Actions manage deployments and nightly snapshots keep `/data` safe.
