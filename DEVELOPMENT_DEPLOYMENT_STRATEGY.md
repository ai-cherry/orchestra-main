# Cherry AI Development & Deployment Strategy

## 🐍 Python Virtual Environment (venv) Strategy

### Version Lock
- **Python Version**: 3.10 (STRICTLY ENFORCED)
- **Lock File**: `.python-version-lock`
- **No Poetry/Pipenv**: Use pip + venv only

### Virtual Environment Setup
```bash
# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements/base.txt
```

### Makefile Integration
- Auto-detects venv: `VENV_PYTHON := $(wildcard venv/bin/python)`
- Falls back to system Python if venv not found
- All make commands use venv Python automatically

## 💻 Development Strategy

### Local Development (On Vultr)
```bash
# SSH to Vultr server
ssh -i ~/.ssh/vultr_cherry_ai root@45.32.69.157

# Use screen/tmux for persistent sessions
screen -S dev

# Development directory
cd /root/cherry_ai-main

# Activate venv
source venv/bin/activate

# Run development server
python -m uvicorn agent.app.main:app --reload --port 8001
```

### Development Tools
- **MCP Servers**: `./scripts/start_mcp_for_coding.sh`
- **Code Review**: `make ai-review-changes`
- **Validation**: `make validate`
- **Health Check**: `make health-check`

### Git Workflow
```bash
# Before coding session
make before-ai-coding  # Creates checkpoint commit

# After coding session
make after-ai-coding   # Reviews and validates changes

# Push changes
git push origin main   # Triggers GitHub Actions
```

## 🚀 Deployment Strategy

### GitHub Actions (CI/CD)
**File**: `.github/workflows/sync-vultr.yml`

**Triggers**:
- Push to main branch
- Manual workflow dispatch

**Process**:
1. SSH to Vultr (45.32.69.157)
2. Pull latest from GitHub
3. Activate venv
4. Run validation
5. Restart services if needed
6. Health check

### Manual Deployment
```bash
# Quick deploy script
./scripts/quick_deploy.sh

# Or manually
git pull origin main
make restart-services
```

## 🏭 Production Strategy

### Server Architecture
- **Single Vultr Server**: 45.32.69.157
- **Combined Dev/Prod**: Same server, different ports
- **User Separation**: 
  - `root` for production
  - Optional `dev` user for development

### Port Allocation
```
Production API:      8000
Development API:     8001 or 8080
MCP conductor:    8002
MCP Memory:          8003
MCP Tools:           8006
PostgreSQL:          5432
Weaviate:            8080
Admin UI:            80/443 (nginx)
```

### Service Management
```bash
# Using systemd
systemctl start cherry_ai-api
systemctl status cherry_ai-api
systemctl restart cherry_ai-api

# Using Make
make start-services
make stop-services
make service-status
```

### Database Architecture
- **PostgreSQL**: Structured data (agents, workflows, sessions)
- **Weaviate**: Vector/semantic data (memories, knowledge base)
- **No MongoDB/Redis**: Simplified to 2 databases only

## 🔄 GitHub Update Strategy

### Repository Structure
```
cherry_ai-main/
├── .github/workflows/    # CI/CD
├── agent/               # Main application
├── mcp_server/          # MCP servers
├── shared/database/     # DB clients
├── scripts/             # Automation
├── requirements/        # Dependencies
└── venv/               # Virtual environment
```

### Branch Strategy
- **main**: Production branch
- **Feature branches**: For major changes
- **Direct commits**: For hotfixes/small changes

### Update Flow
1. **Local Changes**:
   ```bash
   git add -A
   git commit -m "feat: description"
   git push origin main
   ```

2. **GitHub Actions**:
   - Automatically syncs to Vultr
   - Runs validation
   - Restarts services if needed

3. **Rollback**:
   ```bash
   ./scripts/rollback.sh
   # Or manually: git revert HEAD
   ```

## 📋 Environment Configuration

### Environment Files
- **Template**: `env.example`
- **Development**: `.env`
- **Production**: `.env` (same file, different values)

### Key Environment Variables
```bash
# Server
ENVIRONMENT=unified
SERVER_HOST=45.32.69.157
API_PORT=8000

# Databases
POSTGRES_HOST=localhost
POSTGRES_DB=cherry_ai
WEAVIATE_HOST=localhost

# AI Services
OPENAI_API_KEY=xxx
ANTHROPIC_API_KEY=xxx

# Security
JWT_SECRET=xxx
API_KEY=xxx
```

## 🛡️ Best Practices

### Development
1. Always use venv
2. Use screen/tmux for long sessions
3. Test on different port before deploying
4. Create checkpoint commits before major changes

### Deployment
1. Always run validation before deploying
2. Monitor health checks after deployment
3. Keep logs for troubleshooting
4. Use GitHub Actions for consistency

### Production
1. Regular backups of PostgreSQL
2. Monitor resource usage
3. Keep services isolated by port
4. Use systemd for service management

## 🔧 Maintenance Commands

### Daily Operations
```bash
# Check status
make service-status
make health-check

# View logs
tail -f /tmp/mcp_*.log
journalctl -u cherry_ai-api -f

# Database maintenance
python scripts/setup_postgres_schema.py --verify-only
python scripts/test_database_consolidation.py
```

### Troubleshooting
```bash
# Restart everything
make restart-services

# Clean and rebuild
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/base.txt

# Check ports
lsof -i :8000  # Check what's using ports
```

## 📊 Monitoring

### Health Endpoints
- API Health: `http://45.32.69.157:8000/health`
- MCP Status: `make wait-for-mcp`
- Database: `make health-check`

### Logs
- Application: `/var/log/cherry_ai/`
- MCP Servers: `/tmp/mcp_*.log`
- Nginx: `/var/log/nginx/`
- Systemd: `journalctl -u cherry_ai-api`

This strategy provides a unified, simple approach focusing on a single Vultr server with clear separation between development and production through ports and process management. 