# Unified Vultr Server Architecture

## Overview
Cherry AI runs on a single Vultr server that serves as development, deployment, and production environment.

## Server Details
- **IP**: 45.32.69.157
- **OS**: Ubuntu/Linux
- **Location**: /root/cherry_ai-main
- **Cost**: ~$160/month

## Architecture Benefits
1. **Instant Deployment**: No build/deploy cycle - changes are live immediately
2. **Real Environment Testing**: Development happens in production environment
3. **Simplified Operations**: No complex CI/CD pipelines needed
4. **Cost Effective**: Single server instead of multiple environments

## Development Workflow
1. **Direct SSH Access**: 
   ```bash
   ssh -i ~/.ssh/vultr_cherry_ai root@45.32.69.157
   ```

2. **VSCode/Cursor Remote Development**:
   - Open folder: `/root/cherry_ai-main`
   - Edit files directly on server
   - Changes are instant

3. **Service Management**:
   ```bash
   make start-services  # Start all services
   make stop-services   # Stop all services
   make health-check    # Check service health
   ```

## Port Allocation
| Port | Service |
|------|---------|
| **80**  | Nginx (Admin-UI static files + API proxy) |
| **8000** | FastAPI conductor (production + dev, reloader enabled) |
| **5432** | PostgreSQL 14 (structured data) |
| **6379** | Redis 5 (short-term cache / pub-sub) |
| **8080** | Weaviate (vector memory) |

## Safety Measures
1. **Git Version Control** – All changes tracked on GitHub `main`.
2. **Secrets via GitHub** – Deployment pulls `.env` from GitHub Actions secrets; no secrets live in code.
3. **Nightly Snapshots** – Vultr automatic block-storage snapshots at 03:00 UTC.
4. **Quick Rollback** – `git reset --hard` for code, snapshot restore for data.

## Best Practices
1. Always pull latest changes before starting work
2. Test changes locally before restarting services
3. Use `make validate` before commits
4. Monitor logs during development: `tail -f /var/log/cherry_ai/*`

## Migration Complete
- ✅ All DigitalOcean resources shut down
- ✅ All Paperspace resources shut down
- ✅ Single Vultr server fully operational 