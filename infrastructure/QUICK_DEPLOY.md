# Quick Deployment Guide

## Option 1: Automated Vultr Deployment (Requires API Key)

1. **Set your Vultr API key:**
   ```bash
   export VULTR_API_KEY="your-vultr-api-key"
   ```

2. **Run the deployment:**
   ```bash
   ./infrastructure/deploy-to-vultr.sh
   ```

This will create a new Vultr instance and deploy everything automatically.

## Option 2: Manual Deployment (Existing Server)

If you already have a Vultr server or want to deploy manually:

1. **Create a Vultr instance:**
   - OS: Ubuntu 22.04 LTS
   - Plan: Regular Cloud Compute, 2 vCPU, 4GB RAM ($20/month)
   - Region: Choose closest to your users
   - Enable IPv6 (optional)

2. **Deploy to your server:**
   ```bash
   ./infrastructure/manual-deploy.sh YOUR_SERVER_IP
   ```

   Example:
   ```bash
   ./infrastructure/manual-deploy.sh 45.32.123.456
   ```

3. **Enter the root password when prompted**

## What Gets Deployed

- Docker with the Orchestra API
- Nginx reverse proxy
- 5 AI Personas (Cherry, AI Assistant, Technical Architect, Sophia, Gordon Gekko)
- Health monitoring endpoint
- JWT authentication

## Testing the Deployment

1. **Check health:**
   ```bash
   curl http://YOUR_SERVER_IP/api/health
   ```

2. **Test authentication:**
   ```bash
   curl -X POST http://YOUR_SERVER_IP/api/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"username": "scoobyjava", "password": "Huskers1983$"}'
   ```

## Files Created

- **Docker Image**: `orchestra-api-minimal.tar.gz` (64MB)
- **Pulumi IaC**: `infrastructure/pulumi/` (for automated deployment)
- **Deployment Scripts**: 
  - `infrastructure/deploy-to-vultr.sh` (automated)
  - `infrastructure/manual-deploy.sh` (manual)

## Next Steps

1. Configure your domain to point to the server IP
2. Set up SSL certificate (Let's Encrypt)
3. Configure frontend to use the API endpoint
4. Set up monitoring and backups

## Troubleshooting

If deployment fails:
- Check Docker logs: `ssh root@YOUR_IP "docker logs orchestra-api"`
- Verify personas loaded: Look for "Successfully loaded 5 persona configurations"
- Test locally first: `curl http://YOUR_IP:8000/api/health`