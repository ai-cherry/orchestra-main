# VULTR WORKFLOW - THE ONLY WAY

## 1. CONNECT TO VULTR
```bash
ssh root@45.32.69.157
cd /root/orchestra-main
```

## 2. CODE ON VULTR
- Edit files directly on the server
- Use vim, nano, or install VSCode Server
- All development happens here

## 3. DEPLOY YOUR CHANGES
```bash
./deploy.sh
```

## THAT'S IT

- NO local development
- NO Paperspace
- NO GCP
- ONLY Vultr

## Quick Commands

```bash
# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Restart services
docker-compose restart

# Pull latest changes
git pull origin main

# Push changes
git push origin main
```

## Your site: https://cherry-ai.me

Everything happens on Vultr. Period.
