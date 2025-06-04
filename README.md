# AI cherry_ai

## Quick Start

### Option 1: Local Development with Docker Compose (Recommended)

1. **Clone and run locally**:
   ```bash
   git clone <repository>
   cd cherry_ai-main
   docker-compose up --build
   ```

2. **Access services**:
   - API: http://localhost:8000
   - Admin UI: http://localhost:3000
   - Weaviate: http://localhost:8080

### Option 2: Development on Vultr Server

1. **SSH to Vultr server**:
   ```bash
   ssh root@45.32.69.157
   cd /root/cherry_ai-main
   ```

2. **Code directly on Vultr**:
   - Edit files on the server
   - Test changes locally on the server
   - Commit and push from the server

3. **Deploy changes**:
   ```bash
   ./deploy.sh
   ```
   Or push to GitHub for auto-deploy:
   ```bash
   git push origin main
   ```

## Architecture

- **API**: Python FastAPI backend
- **Admin UI**: React frontend
- **Database**: PostgreSQL
- **Cache**: Redis (required for caching and semantic caching)
- **Vector DB**: Weaviate
- **Deployment**: Docker Compose on Vultr
- **MCP Servers**: Provide AI coding context for Cursor AI and other agents
- **Domain**: cherry-ai.me

## Docker & Redis Integration

- **Docker Compose is the preferred way to run the full stack locally and for development.**
- **Redis is required for caching and semantic caching.** It's included in the Docker Compose setup.
- **All AI coding context for Cursor AI and other agents is provided via MCP servers** to ensure consistent, up-to-date project context.

## Essential Files

- `docker-compose.yml` - Service definitions (includes Redis, PostgreSQL, Weaviate)
- `nginx.conf` - Reverse proxy config
- `.mcp.json` - MCP server configuration for AI coding context
- `.github/workflows/deploy.yml` - Auto-deployment
- `deploy.sh` - Manual deployment script
- `.env` - Environment variables (add your API keys, Redis URL)

## Working on Vultr

**Connect to server:**
```bash
ssh root@45.32.69.157
cd /root/cherry_ai-main
```

**Edit files:**
```bash
nano file.py  # or vim, or install your preferred editor
```

**Deploy changes:**
```bash
./deploy.sh
```

**View logs:**
```bash
docker-compose logs -f
```

## Workflow

1. SSH to Vultr server
2. Edit code directly on server
3. Run `./deploy.sh` to deploy
4. Changes live at cherry-ai.me

No local development. No Paperspace. Just Vultr.
