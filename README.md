# AI Orchestra

## Quick Start

1. **SSH to Vultr server**:
   ```bash
   ssh root@45.32.69.157
   cd /root/orchestra-main
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
- **Cache**: Redis
- **Vector DB**: Weaviate
- **Deployment**: Docker Compose on Vultr
- **Domain**: cherry-ai.me

## Essential Files

- `docker-compose.yml` - Service definitions
- `nginx.conf` - Reverse proxy config
- `.github/workflows/deploy.yml` - Auto-deployment
- `deploy.sh` - Manual deployment script
- `.env` - Environment variables (add your API keys)

## Working on Vultr

**Connect to server:**
```bash
ssh root@45.32.69.157
cd /root/orchestra-main
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
