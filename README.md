# AI Orchestra

## Quick Start

1. **Clone locally** (on YOUR computer, not Paperspace):
   ```bash
   git clone https://github.com/yourusername/orchestra-main.git
   cd orchestra-main
   ```

2. **Deploy to production** (cherry-ai.me):
   ```bash
   git push origin main
   ```
   GitHub Actions automatically deploys to Vultr in ~2 minutes.

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

## Commands

**SSH to production:**
```bash
ssh root@45.32.69.157
```

**View logs:**
```bash
ssh root@45.32.69.157 "docker-compose logs -f"
```

**Manual deploy:**
```bash
ssh root@45.32.69.157 "cd /root/orchestra-main && ./deploy.sh"
```

## Workflow

1. Code locally
2. Push to GitHub
3. Auto-deploys to cherry-ai.me
4. That's it

No Paperspace. No GCP. No complexity.
