# Development Transition Roadmap: Paperspace → DigitalOcean

## Executive Summary
This roadmap guides the transition from the current Paperspace development environment to the production-ready DigitalOcean two-node architecture. The transition is designed to be zero-downtime with parallel development capabilities.

## Current State vs Target State

### Current (Paperspace)
- **Environment**: Single VM with Python venv
- **Database**: DragonflyDB (cloud), MongoDB Atlas, Weaviate Cloud
- **Status**: Development only, no services running

### Target (DigitalOcean)
- **Vector Node**: 68.183.170.81 - Weaviate v1.30+ with Agents runtime
- **App Node**: 159.65.79.26 - PostgreSQL 16 + pgvector, conductor, MCP servers
- **Status**: Production-ready, fully deployed

## Phase 1: Parallel Setup (Days 1-3)

### Day 1: Infrastructure Bootstrap
```bash
# From Paperspace environment
chmod +x setup_do_dev_environment.sh
./setup_do_dev_environment.sh

# Verify connections
ssh do-vector "docker ps"
ssh do-app "psql -U conductor -c '\l'"
```

### Day 2: Code Sync & Dependencies
```bash
# Sync codebase to App node
rsync -avz --exclude venv --exclude .git \
  /home/paperspace/cherry_ai-main/ \
  root@159.65.79.26:/opt/cherry_ai/

# Install dependencies on App node
ssh do-app "cd /opt/cherry_ai && source venv/bin/activate && pip install -r requirements/base.txt"
```

### Day 3: Data Migration
```bash
# Run migration script from Paperspace
cd /home/paperspace/cherry_ai-main
source venv/bin/activate
export WEAVIATE_ENDPOINT=http://68.183.170.81:8080
python scripts/migrate_dragonfly_to_weaviate.py
```

## Phase 2: Service Deployment (Days 4-5)

### Deploy conductor Services
```bash
# SSH to App node
ssh do-app

# Setup environment
cat > /opt/cherry_ai/.env << EOF
WEAVIATE_ENDPOINT=http://10.120.0.3:8080
POSTGRES_DSN=postgresql://conductor:dev-password-123@localhost/conductor
PYTHONPATH=/opt/cherry_ai
EOF

# Create systemd service
cat > /etc/systemd/system/cherry_ai-api.service << 'EOF'
[Unit]
Description=Cherry AI API
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/cherry_ai
EnvironmentFile=/opt/cherry_ai/.env
ExecStart=/opt/cherry_ai/venv/bin/python -m uvicorn core.api.main:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cherry_ai-api
systemctl start cherry_ai-api
```

### Deploy MCP Servers
```bash
# On App node
cd /opt/cherry_ai
docker run -d --name mcp-server \
  --network host \
  -v /opt/cherry_ai/mcp_server:/app \
  -e KUBECONFIG=/root/.kube/config \
  ghcr.io/openai/mcp:latest
```

## Phase 3: Development Workflow Transition (Days 6-7)

### Setup Remote Development
```bash
# Install VS Code Remote SSH extension
# Add to VS Code SSH config:
Host do-app-dev
    HostName 159.65.79.26
    User root
    ForwardAgent yes
    RemoteCommand cd /opt/cherry_ai && source venv/bin/activate && exec bash
```

### Development Commands Cheatsheet
```bash
# Local (Paperspace) → Remote (DO)
alias do-sync='rsync -avz --exclude venv /home/paperspace/cherry_ai-main/ root@159.65.79.26:/opt/cherry_ai/'
alias do-logs='ssh do-app journalctl -u cherry_ai-api -f'
alias do-restart='ssh do-app systemctl restart cherry_ai-api'

# Add to ~/.bashrc
echo "alias do-sync='rsync -avz --exclude venv /home/paperspace/cherry_ai-main/ root@159.65.79.26:/opt/cherry_ai/'" >> ~/.bashrc
echo "alias do-logs='ssh do-app journalctl -u cherry_ai-api -f'" >> ~/.bashrc
echo "alias do-restart='ssh do-app systemctl restart cherry_ai-api'" >> ~/.bashrc
```

## Phase 4: Validation & Cutover (Day 8)

### Health Checks
```bash
# Run validation script
python quick_verify_admin_ui.py

# Check service endpoints
curl -I http://159.65.79.26:8080/health
curl -I http://68.183.170.81:8080/v1/.well-known/ready

# Check latency
python /opt/cherry_ai/monitor_latency.py
```

### Performance Benchmarks
- Session query latency: Target < 50ms
- Weaviate ACORN query: Target < 150ms
- PostgreSQL TPS: Target > 500/s

## Phase 5: Primary Environment Switch (Day 9-10)

### Make DigitalOcean Primary
1. **Update Git remote**:
   ```bash
   git remote add do-origin git@github.com:your-org/cherry_ai-main.git
   git config --global push.default current
   ```

2. **Update CI/CD**:
   ```yaml
   # .github/workflows/deploy.yml
   - name: Deploy to DigitalOcean
     run: |
       ssh do-app "cd /opt/cherry_ai && git pull && systemctl restart cherry_ai-api"
   ```

3. **Archive Paperspace snapshot**:
   ```bash
   # Create final backup
   tar -czf paperspace_final_backup_$(date +%Y%m%d).tar.gz \
     --exclude venv --exclude .git \
     /home/paperspace/cherry_ai-main/

   # Upload to DO Spaces or S3
   ```

## Rollback Plan

If issues arise:
1. Services remain running on Paperspace (not shut down until Day 14)
2. Restore from backup: `tar -xzf paperspace_final_backup_*.tar.gz`
3. Point development back to Paperspace
4. Investigate and fix issues before retry

## Decision Points

### When to Develop on DigitalOcean vs Paperspace

**Continue on Paperspace**:
- Heavy experimental work
- Testing new dependencies
- Bulk data processing
- Breaking changes

**Switch to DigitalOcean**:
- Production bug fixes
- API development
- Integration testing
- Performance optimization

### Hybrid Workflow (Recommended for 2 weeks)
```bash
# Morning sync
do-sync && do-restart

# Development on Paperspace
cd /home/paperspace/cherry_ai-main
# ... make changes ...

# Test on DigitalOcean
do-sync
do-logs  # Watch for errors

# Commit from either environment
git add . && git commit -m "feat: ..." && git push
```

## Monitoring & Alerts

### Setup Monitoring (Day 5)
```bash
# Install on App node
ssh do-app << 'EOF'
# Prometheus node exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xzf node_exporter-1.7.0.linux-amd64.tar.gz
cp node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
```

### Key Metrics to Watch
- CPU usage > 80%
- Memory usage > 85%
- Disk usage > 70%
- API response time > 500ms
- Weaviate query p95 > 150ms

## Success Criteria

✅ Phase 1 Complete when:
- Both droplets accessible via SSH
- Weaviate and PostgreSQL running
- Code synced to App node

✅ Phase 2 Complete when:
- cherry_ai API responding on port 8080
- MCP servers running
- Data migration successful

✅ Phase 3 Complete when:
- VS Code connected to DO
- Development workflow smooth
- Sync commands working

✅ Phase 4 Complete when:
- All health checks passing
- Performance targets met
- No errors in logs

✅ Phase 5 Complete when:
- CI/CD updated
- Team using DO primarily
- Paperspace archived

## Timeline Summary

- **Days 1-3**: Infrastructure setup and data migration
- **Days 4-5**: Service deployment
- **Days 6-7**: Developer workflow setup
- **Day 8**: Validation and testing
- **Days 9-10**: Primary environment switch
- **Days 11-14**: Monitoring and stabilization
- **Day 15**: Decommission Paperspace

## Emergency Contacts

- DigitalOcean Support: support.digitalocean.com
- Weaviate Cloud: cloud.weaviate.io/support
- Backup location: `/backups/` on both nodes

## Next Steps After Migration

1. **Enable automated backups**:
   ```bash
   # Add to crontab on App node
   0 2 * * * pg_dump conductor | gzip > /backups/postgres_$(date +\%Y\%m\%d).sql.gz
   0 3 * * * curl -X POST http://localhost:8080/api/backup/weaviate
   ```

2. **Setup SSL/TLS**:
   ```bash
   apt install certbot python3-certbot-nginx
   certbot --nginx -d api.yourdomain.com
   ```

3. **Configure monitoring dashboards**:
   - Grafana: Monitor system metrics
   - Langfuse: Track LLM usage
   - Custom dashboard for cherry_ai metrics
