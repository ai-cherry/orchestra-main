# AI cherry_ai Deployment Guide

This guide covers all deployment options for the AI cherry_ai API to Vultr, using GitHub secrets and automated workflows.

## Prerequisites

- Docker image built: `cherry_ai-api-minimal.tar.gz` (64MB) ✅
- GitHub secrets configured (VULTR_API_KEY, VULTR_IP_ADDRESS, etc.) ✅
- Vultr server (Ubuntu 22.04, 2 vCPU, 4GB RAM)

## Deployment Options

### Option 1: GitHub Actions (Recommended)

Push to main branch to trigger automatic deployment:

```bash
git add .
git commit -m "Deploy to Vultr"
git push origin main
```

The GitHub Action will:
1. Build and push Docker image to Docker Hub
2. Deploy to Vultr server using SSH
3. Configure personas and environment variables
4. Run health checks

### Option 2: Local Deployment with Environment Variables

1. **Setup environment variables:**
   ```bash
   ./scripts/sync-github-secrets.sh
   # Edit .env file with your actual values
   source .env
   ```

2. **Deploy:**
   ```bash
   ./scripts/deploy-from-env.sh
   ```

### Option 3: Manual Deployment to Existing Server

If you already have a Vultr server:

```bash
./infrastructure/manual-deploy.sh YOUR_SERVER_IP
```

### Option 4: Pulumi Infrastructure as Code

For complete infrastructure automation:

```bash
export VULTR_API_KEY="your-api-key"
./infrastructure/deploy-to-vultr.sh
```

## What Gets Deployed

- **API Container**: cherry_ai API with 5 AI personas
- **Nginx**: Reverse proxy on port 80
- **Personas**: Cherry, AI Assistant, Technical Architect, Sophia, Gordon Gekko
- **Environment**: All API keys from GitHub secrets

## GitHub Secrets Configuration

The following secrets are used from GitHub:

### Required
- `VULTR_IP_ADDRESS` - Your Vultr server IP
- `SSH_PRIVATE_KEY` - SSH key for server access
- `DOCKERHUB_USERNAME` - Docker Hub username
- `DOCKER_PERSONAL_ACCESS_TOKEN` - Docker Hub access token

### API Keys (Optional but recommended)
- `ANTHROPIC_API_KEY` - For Claude models
- `OPENAI_API_KEY` - For GPT models
- `PORTKEY_API_KEY` - For observability
- `LANGCHAIN_API_KEY` - For LangChain features

## Testing the Deployment

1. **Health Check:**
   ```bash
   curl http://YOUR_SERVER_IP/api/health
   ```

2. **Authentication Test:**
   ```bash
   curl -X POST http://YOUR_SERVER_IP/api/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"username": "scoobyjava", "password": "Huskers1983$"}'
   ```

3. **Check Personas:**
   ```bash
   curl http://YOUR_SERVER_IP/api/personas
   ```

## File Structure

```
.
├── .github/workflows/deploy-to-vultr.yml    # GitHub Actions workflow
├── .env.example                             # Environment template
├── cherry_ai-api-minimal.tar.gz             # Docker image
├── infrastructure/
│   ├── pulumi/                              # Pulumi IaC
│   │   ├── Pulumi.yaml
│   │   └── __main__.py
│   ├── deploy-to-vultr.sh                   # Automated Pulumi deployment
│   ├── manual-deploy.sh                     # Manual deployment script
│   ├── VULTR_DEPLOYMENT.md                  # Detailed deployment docs
│   └── QUICK_DEPLOY.md                      # Quick start guide
└── scripts/
    ├── sync-github-secrets.sh               # Sync GitHub secrets locally
    └── deploy-from-env.sh                   # Deploy using env vars
```

## Monitoring

After deployment:

1. **Container Logs:**
   ```bash
   ssh root@YOUR_SERVER_IP "docker logs cherry_ai-api"
   ```

2. **Container Status:**
   ```bash
   ssh root@YOUR_SERVER_IP "docker ps"
   ```

3. **Nginx Status:**
   ```bash
   ssh root@YOUR_SERVER_IP "systemctl status nginx"
   ```

## Troubleshooting

### Container Won't Start
- Check logs: `docker logs cherry_ai-api`
- Verify personas loaded: Look for "Successfully loaded 5 persona configurations"
- Check environment variables are set

### API Not Accessible
- Verify nginx is running: `systemctl status nginx`
- Check firewall: `ufw status`
- Test locally first: `curl http://localhost:8000/api/health`

### Authentication Fails
- Verify credentials: username: `scoobyjava`, password: `Huskers1983$`
- Check JWT secret is consistent

## Updates and Rollbacks

### Update Application
1. Build new image locally
2. Push to main branch (triggers GitHub Action)
3. Or use manual deployment scripts

### Rollback
```bash
ssh root@YOUR_SERVER_IP
docker stop cherry_ai-api
docker rm cherry_ai-api
docker run -d --name cherry_ai-api [previous-image-tag]
```

## Security Notes

- All secrets are stored in GitHub Secrets
- SSH keys are used for server access
- API keys are passed as environment variables
- Consider adding SSL/TLS for production

## Next Steps

1. Configure domain name
2. Set up SSL certificate (Let's Encrypt)
3. Enable monitoring and alerts
4. Configure backups
5. Set up staging environment

## Support

For issues, check:
- GitHub Actions logs
- Container logs on server
- This guide and related documentation