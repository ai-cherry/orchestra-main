# Deploy to cherry-ai.me NOW

## Quick Deploy Command

Replace `YOUR_Lambda_IP` with your actual Lambda server IP from GitHub secrets:

```bash
./infrastructure/manual-deploy.sh YOUR_Lambda_IP
```

For example, if your IP is 45.32.123.456:
```bash
./infrastructure/manual-deploy.sh 45.32.123.456
```

## What This Will Do

1. **Copy Docker image** (cherry_ai-api-minimal.tar.gz) to your server
2. **Install Docker and nginx** if not already installed
3. **Load the Docker image** with:
   - Fixed authentication system
   - 5 working AI personas
   - All API endpoints
4. **Configure nginx** reverse proxy
5. **Start the API** on port 8000
6. **Make it accessible** at http://YOUR_IP and http://cherry-ai.me

## After Deployment

Test your deployment:

```bash
# Health check
curl http://cherry-ai.me/api/health

# Test authentication
curl -X POST http://cherry-ai.me/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username": "scoobyjava", "password": "Huskers1983$"}'
```

## Alternative: GitHub Actions

If you prefer automatic deployment:
1. Push this code to GitHub
2. The workflow will trigger automatically
3. It will use your GitHub secrets to deploy

## Need Your Lambda IP?

Check your GitHub secrets page for `LAMBDA_IP_ADDRESS` or your Lambda dashboard.