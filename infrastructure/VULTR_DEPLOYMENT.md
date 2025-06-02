# Vultr Deployment Guide for AI Orchestra

This guide provides step-by-step instructions for deploying the AI Orchestra API to Vultr using Pulumi Infrastructure as Code.

## Prerequisites

1. **Vultr Account**: You need a Vultr account with API access
2. **Vultr API Key**: Get your API key from https://my.vultr.com/settings/#settingsapi
3. **Pulumi CLI**: Will be installed automatically by the deployment script
4. **Python 3.8+**: Required for Pulumi
5. **Docker image**: `orchestra-api-minimal.tar.gz` (already created)

## Infrastructure Overview

The deployment creates:
- **Vultr Instance**: Ubuntu 22.04 LTS, 2 vCPU, 4GB RAM
- **Firewall Rules**: SSH (22), HTTP (80), HTTPS (443), API (8000)
- **Docker**: Pre-installed and configured
- **Nginx**: Reverse proxy for the API
- **Persistent Storage**: `/opt/orchestra` for configs and data

## Deployment Steps

### 1. Set Environment Variables

```bash
export VULTR_API_KEY="your-vultr-api-key-here"
```

### 2. Run the Deployment Script

```bash
cd /root/orchestra-main
./infrastructure/deploy-to-vultr.sh
```

The script will:
1. Generate SSH keys if needed
2. Install Pulumi and dependencies
3. Create Vultr infrastructure
4. Copy Docker image to server
5. Deploy and start the API
6. Configure nginx reverse proxy

### 3. Verify Deployment

After deployment, you'll see:
- Instance IP address
- API URL (http://YOUR_IP)
- SSH command to access the server

Test the API:
```bash
curl http://YOUR_IP/api/health
```

## Manual Deployment Steps

If you prefer to deploy manually:

### 1. Create Vultr Instance

Using Pulumi:
```bash
cd infrastructure/pulumi
pulumi up
```

### 2. Copy Docker Image

```bash
scp orchestra-api-minimal.tar.gz root@YOUR_IP:/opt/orchestra/
```

### 3. SSH to Server

```bash
ssh root@YOUR_IP
```

### 4. Load and Run Docker Image

```bash
cd /opt/orchestra
docker load < orchestra-api-minimal.tar.gz
docker run -d \
  --name orchestra-api \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /opt/orchestra/config:/app/core/orchestrator/src/config \
  -e ENVIRONMENT=production \
  orchestra-api-minimal:latest
```

## Configuration

### Persona Configuration

Personas are stored in `/opt/orchestra/config/personas.yaml` and include:
- Cherry (Creative AI)
- AI Assistant (General helper)
- Technical Architect
- Sophia (Analytical)
- Gordon Gekko (Business focused)

### Environment Variables

- `ENVIRONMENT`: Set to "production"
- `CORS_ORIGINS`: Configure allowed origins
- `PORT`: API port (default: 8000)

## Monitoring and Maintenance

### Check Container Status
```bash
docker ps
docker logs orchestra-api
```

### Restart Container
```bash
docker restart orchestra-api
```

### Update Application
```bash
# Build new image locally
docker build -f Dockerfile.minimal -t orchestra-api-minimal:latest .
docker save orchestra-api-minimal:latest | gzip > orchestra-api-minimal.tar.gz

# Copy to server
scp orchestra-api-minimal.tar.gz root@YOUR_IP:/opt/orchestra/

# On server
docker load < orchestra-api-minimal.tar.gz
docker stop orchestra-api
docker rm orchestra-api
docker run -d --name orchestra-api ... # same run command as above
```

## Troubleshooting

### Container Won't Start
```bash
docker logs orchestra-api
# Check for persona validation errors or missing dependencies
```

### API Not Accessible
```bash
# Check nginx
systemctl status nginx
nginx -t

# Check firewall
ufw status
```

### Persona Loading Errors
- Ensure `/opt/orchestra/config/personas.yaml` exists
- Verify YAML syntax
- Check persona structure matches PersonaConfig model

## Security Considerations

1. **SSH Access**: Use SSH keys only, disable password auth
2. **Firewall**: Only open required ports
3. **HTTPS**: Configure SSL certificate for production
4. **API Keys**: Use environment variables for sensitive data
5. **Updates**: Keep system and Docker updated

## Cost Optimization

- **Instance Type**: vc2-2c-4gb ($20/month) is suitable for moderate load
- **Backups**: Enable if needed ($4/month)
- **DDoS Protection**: Enable for production ($10/month)
- **Monitoring**: Use Vultr's built-in monitoring

## Rollback Procedure

If deployment fails:
```bash
cd infrastructure/pulumi
pulumi destroy  # Remove infrastructure
```

Or restore previous Docker image:
```bash
docker stop orchestra-api
docker rm orchestra-api
docker run -d --name orchestra-api ... # with previous image
```

## Support

For issues:
1. Check container logs: `docker logs orchestra-api`
2. Verify persona configuration
3. Ensure all dependencies are installed
4. Check Vultr instance status