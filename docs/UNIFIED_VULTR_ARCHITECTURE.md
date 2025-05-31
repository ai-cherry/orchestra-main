# Unified Vultr Server Architecture

## Overview
Orchestra AI runs on a single Vultr server that serves as development, deployment, and production environment.

## Server Details
- **IP**: 45.32.69.157
- **OS**: Ubuntu/Linux
- **Location**: /root/orchestra-main
- **Cost**: ~$160/month

## Architecture Benefits
1. **Instant Deployment**: No build/deploy cycle - changes are live immediately
2. **Real Environment Testing**: Development happens in production environment
3. **Simplified Operations**: No complex CI/CD pipelines needed
4. **Cost Effective**: Single server instead of multiple environments

## Development Workflow
1. **Direct SSH Access**: 
   ```bash
   ssh -i ~/.ssh/vultr_orchestra root@45.32.69.157
   ```

2. **VSCode/Cursor Remote Development**:
   - Open folder: `/root/orchestra-main`
   - Edit files directly on server
   - Changes are instant

3. **Service Management**:
   ```bash
   make start-services  # Start all services
   make stop-services   # Stop all services
   make health-check    # Check service health
   ```

## Port Allocation
- **8000**: Production API
- **8001**: Development/testing API (if needed)
- **80**: Admin UI (served by Nginx)
- **5432**: PostgreSQL
- **6333**: Qdrant vector DB

## Safety Measures
1. **Git Version Control**: All changes tracked
2. **Nightly Snapshots**: Automated at 03:00 UTC
3. **Service Isolation**: Docker containers for each service
4. **Quick Rollback**: `git reset` for code, snapshots for data

## Best Practices
1. Always pull latest changes before starting work
2. Test changes locally before restarting services
3. Use `make validate` before commits
4. Monitor logs during development: `tail -f /var/log/orchestra/*`

## Migration Complete
- ✅ All DigitalOcean resources shut down
- ✅ All Paperspace resources shut down
- ✅ Single Vultr server fully operational 