# 🧹 Cleanup Complete - Your New Workflow

## What Was Fixed:

### 1. **Python Version Standardized to 3.11**
   - All files now use Python 3.11 (matches your system and CI)
   - No more version conflicts
   - Updated: pyproject.toml, Dockerfile.dev, AI context files

### 2. **Documentation Cleaned Up**
   - Archived 70+ conflicting documentation files to `docs/archive/old-guides/`
   - Kept only 3 essential files:
     - `README.md` - Points to the right places
     - `README_NO_BS.md` - Quick reference  
     - `UNFUCK_EVERYTHING.md` - Complete guide

### 3. **Docker-Based Development**
   - Everything runs in containers
   - No local dependency hell
   - Consistent across all environments

### 4. **Simplified CI/CD**
   - `.github/workflows/main.yml` - Uses Python 3.11 and Poetry 1.7.1
   - Push to main = Deploy
   - No complex auth flows

## Your Daily Workflow:

### First Time Setup (Once):
```bash
./SETUP_ONCE.sh
```

### Every Day:
```bash
# 1. Start your day
./start.sh shell

# 2. Inside container, run what you need:
run-api      # Start API
run-ui       # Start Admin UI
run-tests    # Run tests
fix-format   # Format code
```

### Deploy:
```bash
git push origin main
# CI/CD handles the rest
```

## Key Files:

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Service definitions (used by `docker compose`) |
| `Dockerfile.dev` | Dev environment |
| `pyproject.toml` | Python dependencies |
| `SETUP_ONCE.sh` | One-time setup |
| `start.sh` | Daily launcher |

## Services:

> **Note:** All services run inside Docker containers managed by `docker compose`. Use only the provided scripts for starting/stopping services.

- **API**: http://localhost:8000
- **Admin UI**: http://localhost:3001  
- **Redis**: localhost:6379
- **PostgreSQL**: localhost:5432

## Dependency & Version Management:

- **Python:** Use Python 3.11+ everywhere. Upgrade pip with `pip install --upgrade pip` after creating your venv.
- **Poetry:** Managed inside the container, version pinned in CI (`poetry==1.7.1`).
- **Node/NPM:** Use Node 18+ and run `npm ci` (not `npm install`) in `admin-interface` for reproducible installs. Node/npm version is managed in the Dockerfile.
- **Docker Compose:** All workflows use `docker compose` (not `docker-compose`).

## Authentication:

- **One service account key**: `service-account-key.json`
- **No more auth loops**
- **GCP works automatically inside container**

## If Problems:

```bash
# Nuclear reset
./start.sh clean
./SETUP_ONCE.sh
```

---

For GCP infrastructure-as-code, see [`infra/README.md`](infra/README.md) for Pulumi workflows and best practices.


**That's it. No more bullshit. Just code.** 