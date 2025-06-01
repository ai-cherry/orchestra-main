# Orchestra AI Quick Reference

## 🚀 Quick Start
```bash
# SSH to server
ssh -i ~/.ssh/vultr_orchestra root@45.32.69.157

# Start development
cd /root/orchestra-main
source venv/bin/activate
./scripts/start_mcp_for_coding.sh
```

## 📁 Key Directories
- **App**: `/root/orchestra-main/agent/`
- **MCP**: `/root/orchestra-main/mcp_server/`
- **Database**: `/root/orchestra-main/shared/database/`
- **Scripts**: `/root/orchestra-main/scripts/`

## 🔧 Common Commands
```bash
# Development
make dev-start              # Start development server
make validate              # Run validation
make ai-review-changes     # AI code review

# Services
make start-services        # Start all services
make stop-services         # Stop all services
make service-status        # Check status
make health-check          # Health check

# MCP Servers
./scripts/start_mcp_for_coding.sh    # Start MCP
./scripts/stop_mcp_servers.sh        # Stop MCP

# Database
python scripts/setup_postgres_schema.py     # Setup DB
python scripts/test_database_consolidation.py  # Test DB
```

## 🌐 Service Ports
- **Production API**: 8000
- **Dev API**: 8001
- **MCP Orchestrator**: 8002
- **MCP Memory**: 8003
- **MCP Tools**: 8006
- **PostgreSQL**: 5432
- **Weaviate**: 8080

## 🔄 Git Workflow
```bash
# Before coding
make before-ai-coding

# Commit changes
git add -A
git commit -m "feat: description"
git push origin main

# After coding
make after-ai-coding
```

## 📊 Database Architecture
- **PostgreSQL**: Agents, workflows, sessions, audit logs
- **Weaviate**: Memories, conversations, knowledge, documents

## 🆘 Troubleshooting
```bash
# Check logs
tail -f /tmp/mcp_*.log
journalctl -u orchestra-api -f

# Restart everything
make restart-services

# Check ports
lsof -i :8000

# Rebuild venv
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/base.txt
```

## 📝 Environment Variables
```bash
# Copy template
cp env.example .env

# Key vars:
POSTGRES_HOST=localhost
POSTGRES_DB=orchestra
WEAVIATE_HOST=localhost
API_KEY=4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd
```

## 🔗 Important URLs
- **GitHub**: https://github.com/ai-cherry/orchestra-main
- **Production**: http://45.32.69.157:8000
- **Dev**: http://45.32.69.157:8001
- **Health**: http://45.32.69.157:8000/health

---
*Python 3.10 | PostgreSQL + Weaviate | Single Vultr Server* 