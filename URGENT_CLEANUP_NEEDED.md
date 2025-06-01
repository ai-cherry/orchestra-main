# 🚨 URGENT: Legacy Service References Throughout Codebase

## The Problem

Despite the decision to use **ONLY PostgreSQL + Weaviate**, the codebase is contaminated with references to deprecated services:
- GCP (Google Cloud Platform)
- Redis
- Firestore
- MongoDB
- DragonflyDB
- Qdrant

## Current Contamination Scope

### 📁 Files with GCP/Redis/Firestore references: **30+ files**

Including:
- Core application code (`core/orchestrator/src/`)
- Configuration files (`config/agents_new.yaml`)
- Environment examples (`env.example`)
- Deployment scripts (`deploy_to_vultr.sh`)
- Documentation (`README.md`, various guides)
- MCP server code
- Example scripts
- Infrastructure code

## Why This Keeps Happening

1. **Incomplete Migration**: The migration to PostgreSQL + Weaviate was done at the database layer but not propagated throughout the codebase
2. **Copy-Paste Code**: Old code is being copied without updating database references
3. **Template Files**: Templates and examples still contain old references
4. **Documentation Lag**: Docs weren't updated when the architecture changed

## Immediate Actions Taken

✅ Fixed `start_mcp_system.sh` - Now uses ONLY PostgreSQL + Weaviate
✅ Fixed `stop_mcp_system.sh` - Matches the new start script
✅ Created clear documentation for AI agents
✅ Updated `.cursorrules` to enforce correct database usage

## What Still Needs to Be Done

### 1. Critical Files to Update
- [ ] `env.example` - Remove REDIS_URL, GCP_REGION, etc.
- [ ] `deploy_to_vultr.sh` - Remove Redis/GCP references
- [ ] `config/agents_new.yaml` - Remove GCP region reference
- [ ] Core application code in `core/orchestrator/src/`

### 2. GitHub Actions Fix
The sync-vultr.yml workflow is failing because:
- Missing `SSH_PRIVATE_KEY` secret in GitHub repository settings

**To Fix**:
1. Go to https://github.com/ai-cherry/orchestra-main/settings/secrets/actions
2. Add new secret: `SSH_PRIVATE_KEY`
3. Value: Your Vultr server's private SSH key

### 3. Comprehensive Cleanup Script Needed

```bash
#!/bin/bash
# cleanup_deprecated_references.sh

# Find and report all deprecated references
echo "Files with Redis references:"
grep -r "REDIS_URL\|redis://" --exclude-dir=venv --exclude-dir=.git --exclude="*.log"

echo "Files with GCP references:"
grep -r "GCP_REGION\|GCP_PROJECT\|FIRESTORE" --exclude-dir=venv --exclude-dir=.git --exclude="*.log"

echo "Files with Qdrant references:"
grep -r "QDRANT_URL\|qdrant" --exclude-dir=venv --exclude-dir=.git --exclude="*.log"
```

## Recommended Approach

### Option 1: Gradual Cleanup (Safer)
1. Update critical runtime files first
2. Update documentation
3. Update examples and templates
4. Archive old code rather than delete

### Option 2: Aggressive Cleanup (Faster but riskier)
1. Global search and replace
2. Remove all deprecated code
3. Risk breaking things that might still depend on old references

## For Now: Use These Environment Variables ONLY

```bash
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=orchestra
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Weaviate
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_API_KEY=your_key  # Optional

# API
API_URL=http://localhost:8080
API_KEY=4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd
```

## Bottom Line

The migration to PostgreSQL + Weaviate is **incomplete**. While the database layer uses the correct databases, the rest of the codebase is full of deprecated references that need systematic cleanup.

**This is why you keep seeing GCP/Redis/Firestore pop up everywhere!** 