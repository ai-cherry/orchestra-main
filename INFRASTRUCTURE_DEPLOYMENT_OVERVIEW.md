# 🏗️ Orchestra AI Complete Infrastructure & Deployment Overview

## 📍 Development Environment

### Local Development
- **Root Directory:** `/Users/lynnmusil/orchestra-dev`
- **Branch:** `main` (single branch workflow)
- **Repository:** `https://github.com/ai-cherry/orchestra-main.git`
- **Last Commit:** `dca5b34c` - Deployment readiness report

### Development Machine
- **OS:** macOS Darwin 24.3.0
- **Shell:** `/bin/zsh`
- **Node.js:** Multiple versions available (system default causing issues)
- **Python:** 3.11 (system), 3.10 (required for project)

## 🚀 Current Deployment Architecture

### 1. **Backend Services (Docker Compose)**
All running locally via `docker-compose.production.yml`:

```yaml
Services:
├── PostgreSQL (Port 5432)
│   └── Primary database for all services
├── Redis (Port 6379)
│   └── Caching layer for 5-tier memory architecture
├── Weaviate (Port 8080)
│   └── Vector database for semantic search
├── API Server (Port 8000)
│   └── FastAPI main application server
├── Nginx (Port 80)
│   └── Reverse proxy and static file serving
├── Fluentd (Port 24224)
│   └── Log aggregation and forwarding
└── Monitor Service
    └── Health monitoring and metrics collection
```

### 2. **MCP (Model Context Protocol) Services**
5 specialized servers running as background processes:

1. **Unified MCP Server** (`mcp_unified_server.py`)
   - Persona routing (Cherry, Sophia, Karen)
   - Memory management
   - Cross-domain queries
   - Notion integration

2. **Memory MCP Server** 
   - 5-tier memory architecture management
   - Compression and retrieval

3. **Puppeteer MCP Server**
   - Web automation capabilities
   - Browser control

4. **Sequential Thinking MCP Server**
   - Chain of thought processing
   - Complex reasoning

5. **Pulumi MCP Server**
   - Infrastructure as Code operations
   - Cloud resource management

### 3. **Frontend Deployments (Vercel)**

#### Current State:
```
┌─────────────────────────┬────────────┬─────────────────────────────────┐
│ Project                 │ Status     │ Description                     │
├─────────────────────────┼────────────┼─────────────────────────────────┤
│ orchestra-ai-frontend   │ ✅ READY   │ Static redirect/landing page    │
│ admin-interface         │ ❌ ERROR   │ Main admin UI (Vite + React)    │
│ orchestra-dashboard     │ ❌ ERROR   │ AI Conductor Dashboard (Next.js)│
└─────────────────────────┴────────────┴─────────────────────────────────┘
```

## 🔧 Deployment Fix Attempts Summary

### Phase 1: Initial Discovery
1. **Problem:** White screen on https://orchestra-admin-interface.vercel.app
2. **Root Cause:** Missing `<div id="root"></div>` in index.html
3. **Fix Applied:** Updated `admin-interface/index.html`

### Phase 2: Vercel Queue Management
1. **Problem:** 100+ deployments stuck in queue
2. **Actions Taken:**
   - Created `vercel_iac_troubleshoot.py` - Direct API troubleshooting
   - Created `vercel_iac_fix_queue.py` - Successfully cleaned 41 stuck deployments
   - Created `vercel_check_ready_deployments.py` - Found deployments with fix

### Phase 3: Project Cleanup
1. **Problem:** 9 Vercel projects (many duplicates/outdated)
2. **Actions Taken:**
   - Deleted 6 projects: orchestra-dev, v0-image-analysis, react_app, orchestra-admin-interface, dist, cherrybaby-mdzw
   - Kept 3 projects matching codebase structure

### Phase 4: Rebuild Attempts
1. **Created Tools:**
   - `vercel_rebuild_strategy.py` - Analyzes codebase vs Vercel projects
   - `rebuild_vercel_deployments.sh` - Automated rebuild script
   - `dashboard/vercel.json` - Missing Next.js configuration

2. **Deployment Results:**
   - orchestra-ai-frontend: ✅ Successfully deployed
   - admin-interface: ❌ Build fails on Vercel (works locally)
   - orchestra-dashboard: ❌ Multiple build errors

## 🗂️ Codebase Structure

```
/Users/lynnmusil/orchestra-dev/
├── admin-interface/          # Vite + React admin UI
│   ├── src/                  # React components
│   ├── dist/                 # Build output (local)
│   └── vercel.json          # Vercel config
├── dashboard/               # Next.js AI Conductor
│   ├── components/          # React components
│   ├── app/                 # Next.js app directory
│   └── vercel.json         # Newly created config
├── src/ui/web/react_app/    # Static redirect page
│   ├── index.html          # Simple HTML
│   └── vercel.json         # Vercel config
├── infrastructure/          # IaC configurations
│   └── pulumi/             # Pulumi projects
├── legacy/                  # Old codebase (being migrated)
├── scripts/                 # Automation scripts
└── docs/                    # Documentation
```

## 🔑 Key Infrastructure Components

### 1. **Lambda Labs Cloud** (Production Infrastructure)
- **Status:** Configured in Pulumi but not deployed
- **Purpose:** GPU-accelerated compute for AI workloads

### 2. **Notion Integration**
- **Workspace ID:** `20bdba04940280ca9ba7f9bce721f547`
- **8 Active Databases:** Epic tracking, task management, development logs, etc.
- **Status:** ✅ Live and integrated

### 3. **5-Tier Memory Architecture**
```
L0: CPU Cache (~1ns)       - Hot data
L1: Process Memory (~10ns) - Session context
L2: Redis (~100ns)         - Cross-persona sharing
L3: PostgreSQL (~1ms)      - Structured history
L4: Weaviate (~10ms)       - Vector embeddings
```

### 4. **AI Personas**
- **Cherry:** Project overseer (4,000 tokens)
- **Sophia:** Financial expert (6,000 tokens)
- **Karen:** Medical specialist (8,000 tokens)

## 🚨 Current Deployment Issues

### admin-interface Build Failure
- **Local Build:** ✅ Success
- **Vercel Build:** ❌ "npm run build exited with 1"
- **Suspected Causes:**
  - Node.js version mismatch
  - Missing environment variables
  - Build memory limits

### orchestra-dashboard Build Errors
1. Missing dependencies: `@tanstack/react-query`
2. Missing components: `McpServerList`, `McpServerForm`
3. Server Component errors: Need "use client" directives

## 📊 Deployment Strategy

### Current Approach:
1. **Backend:** Docker Compose for all services (local deployment)
2. **Frontend:** Vercel for static hosting and serverless functions
3. **State Management:** Local file system + PostgreSQL
4. **Monitoring:** Built-in monitor service + health checks

### Intended Production Architecture:
1. **Backend:** Lambda Labs VPS with Docker
2. **Frontend:** Vercel with custom domains
3. **Database:** Managed PostgreSQL + Redis
4. **Vector Store:** Self-hosted Weaviate
5. **CDN:** Vercel Edge Network

## 🎯 Summary

We have a complex multi-service architecture with:
- **7 Docker services** running locally
- **5 MCP servers** for AI operations
- **3 Vercel projects** (1 working, 2 with build issues)
- **Comprehensive monitoring** and health checks

The main challenge is getting the Vercel deployments working, particularly the admin-interface which contains the critical white screen fix. The backend infrastructure is stable and operational. 