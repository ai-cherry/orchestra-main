# Cherry-AI.me Authentication Fix Deployment Guide

## Overview
This guide provides step-by-step instructions to deploy the authentication fix for Cherry-AI.me on Vultr infrastructure.

## What Was Fixed

### 1. Backend Authentication Endpoints
- Added `/api/auth/login` endpoint that accepts JSON credentials
- Added `/api/token` endpoint for OAuth2 compatibility
- Both endpoints return JWT tokens with proper structure

### 2. Frontend Login Integration
- Updated login page to make actual API calls instead of client-side auth
- Frontend now POSTs credentials to `/api/auth/login`
- Proper error handling added to prevent React crashes

### 3. Stub API Endpoints
- Added stub endpoints for missing APIs to prevent frontend crashes:
  - `/api/agents`, `/api/personas`, `/api/workflows`
  - `/api/integrations`, `/api/resources`, `/api/logs`
  - `/api/query`, `/api/upload`

## Deployment Steps

### 1. Build the Docker Image
```bash
# The minimal Docker image has been built with:
docker build -t orchestra-api-minimal:latest -f Dockerfile.minimal .
```

### 2. Save and Transfer the Image
```bash
# Save the Docker image
docker save orchestra-api-minimal:latest | gzip > orchestra-api-minimal.tar.gz

# Transfer to your Vultr server
scp orchestra-api-minimal.tar.gz root@YOUR_VULTR_IP:/tmp/
```

### 3. Deploy on Vultr Server
SSH into your Vultr server and run:

```bash
# Load the Docker image
cd /tmp
docker load < orchestra-api-minimal.tar.gz

# Stop existing backend (if any)
docker stop orchestra-api || true
docker rm orchestra-api || true

# Run the new backend
docker run -d \
  --name orchestra-api \
  -p 8000:8000 \
  --restart always \
  -e JWT_SECRET_KEY="your-secret-key-here" \
  -e ADMIN_USERNAME="scoobyjava" \
  -e ADMIN_PASSWORD="Huskers1983$" \
  orchestra-api-minimal:latest
```

### 4. Update Nginx Configuration
Ensure your nginx is configured to proxy API requests:

```nginx
server {
    listen 80;
    server_name cherry-ai.me www.cherry-ai.me;
    
    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
    }
}
```

### 5. Deploy Frontend Updates
The frontend has been updated to make actual API calls. Deploy the updated frontend:

```bash
cd admin-ui
npm install
npm run build

# Copy build to your web server directory
# Or use your existing frontend deployment process
```

## Verification Steps

1. **Test Health Endpoint**:
   ```bash
   curl https://cherry-ai.me/api/health
   ```

2. **Test Auth Endpoint**:
   ```bash
   curl -X POST https://cherry-ai.me/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"scoobyjava","password":"Huskers1983$"}'
   ```

3. **Test Login Flow**:
   - Visit https://cherry-ai.me
   - Login with credentials:
     - Username: `scoobyjava`
     - Password: `Huskers1983$`
   - Verify no React errors occur
   - Check that you're redirected to the dashboard

## Environment Variables

The backend supports these environment variables:

- `JWT_SECRET_KEY`: Secret key for JWT token signing (required for production)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 720)
- `ADMIN_USERNAME`: Admin username (default: "admin")
- `ADMIN_PASSWORD`: Admin password (default: "orchestra-admin-2024")
- `ADMIN_EMAIL`: Admin email (default: "admin@orchestra.ai")

## Troubleshooting

### Container Won't Start
Check logs:
```bash
docker logs orchestra-api
```

### Authentication Fails
- Verify environment variables are set correctly
- Check that the frontend is using the correct API URL
- Ensure nginx is properly proxying requests

### Frontend Still Crashes
- Clear browser cache and cookies
- Check browser console for specific errors
- Verify all API endpoints are accessible

## Security Considerations

1. **Change Default Credentials**: Update the admin username and password
2. **Set Strong JWT Secret**: Use a cryptographically secure secret key
3. **Enable HTTPS**: Use Let's Encrypt to secure your domain
4. **Restrict API Access**: Consider adding rate limiting and IP restrictions

## Next Steps

1. **Add Real User Management**: Implement database-backed user authentication
2. **Implement Missing APIs**: Replace stub endpoints with real implementations
3. **Add Monitoring**: Set up logging and monitoring for the API
4. **Enable Auto-scaling**: Use Pulumi to manage infrastructure scaling

## Infrastructure as Code

The Pulumi configuration for Vultr deployment is available in:
- `infra/vultr_deployment.py` - Complete Vultr infrastructure setup
- `infra/Pulumi.yaml` - Pulumi project configuration

To deploy infrastructure:
```bash
cd infra
pulumi up
```

This will create:
- VPC for network isolation
- Firewall rules
- Server instance with Docker pre-installed
- Reserved IP address
- Object storage for backups
- PostgreSQL database (for future use)