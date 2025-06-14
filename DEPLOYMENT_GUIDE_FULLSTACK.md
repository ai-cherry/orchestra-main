# 🚀 Orchestra AI - Full-Stack Deployment Guide

## Overview
This guide explains how to properly deploy Orchestra AI as a full-stack application with:
- **Frontend**: React app (modern-admin) on Vercel
- **Backend**: FastAPI on Lambda Labs GPU instances
- **Databases**: PostgreSQL, Redis, Pinecone, Weaviate

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────┐
│   Vercel CDN    │         │  Lambda Labs     │
│                 │         │  GPU Instance    │
│  React Frontend │ ──API──>│                  │
│  (modern-admin) │  Proxy  │  FastAPI Backend │
│                 │         │  MCP Servers     │
└─────────────────┘         └──────────────────┘
         │                           │
         │                           │
         ▼                           ▼
   [Static Assets]            [Databases]
                              - PostgreSQL
                              - Redis
                              - Pinecone
                              - Weaviate
```

## 📋 Pre-Deployment Checklist

### 1. Environment Variables
Create `.env.production` in project root:
```bash
# Lambda Labs
LAMBDA_API_KEY=your_lambda_api_key
LAMBDA_BACKEND_URL=http://your.lambda.ip:8000

# Database URLs
DATABASE_URL=postgresql://user:pass@host:5432/orchestra_ai
REDIS_URL=redis://host:6379

# API Keys
OPENAI_API_KEY=your_openai_key
PORTKEY_API_KEY=your_portkey_key
PINECONE_API_KEY=your_pinecone_key
WEAVIATE_API_KEY=your_weaviate_key

# Vercel
VERCEL_TOKEN=your_vercel_token
VERCEL_ORG_ID=your_org_id
VERCEL_PROJECT_ID=your_project_id
```

### 2. Frontend Configuration
Create `modern-admin/.env.production`:
```bash
# For production, leave empty to use proxy
VITE_API_URL=
```

## 🚀 Deployment Steps

### Step 1: Deploy Backend to Lambda Labs

1. **SSH into your Lambda Labs instance:**
```bash
ssh ubuntu@YOUR_LAMBDA_IP
```

2. **Clone and setup the repository:**
```bash
git clone https://github.com/ai-cherry/orchestra-main.git
cd orchestra-main
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env.production
# Edit .env.production with your actual values
nano .env.production
```

4. **Start backend services:**
```bash
# Using the service manager
./orchestra_service_manager.sh start

# Or manually with systemd
sudo systemctl start orchestra-api
sudo systemctl start orchestra-mcp-memory
sudo systemctl enable orchestra-api
sudo systemctl enable orchestra-mcp-memory
```

5. **Verify backend is running:**
```bash
curl http://localhost:8000/api/health/
```

### Step 2: Deploy Frontend to Vercel

1. **Install Vercel CLI:**
```bash
npm i -g vercel
```

2. **Login to Vercel:**
```bash
vercel login
```

3. **Configure Vercel environment:**
```bash
# Set the Lambda backend URL
vercel env add LAMBDA_BACKEND_URL production
# Enter: http://YOUR_LAMBDA_IP:8000
```

4. **Deploy to production:**
```bash
# From project root
vercel --prod

# Or with specific configuration
vercel --prod --yes --no-clipboard
```

### Step 3: Configure DNS & SSL

1. **For custom domain:**
```bash
vercel domains add yourdomain.com
```

2. **SSL for backend (optional but recommended):**
- Use Cloudflare Tunnel or nginx proxy
- Configure SSL certificates

## 🔧 Post-Deployment Configuration

### 1. Test the deployment:
```bash
# Test frontend
curl https://your-app.vercel.app

# Test API proxy
curl https://your-app.vercel.app/api/health/
```

### 2. Monitor services:
```bash
# On Lambda Labs instance
./orchestra_service_manager.sh status
```

### 3. View logs:
```bash
# Backend logs
./orchestra_service_manager.sh logs api

# Vercel logs
vercel logs
```

## 🚨 Troubleshooting

### Frontend shows "API Error"
1. Check LAMBDA_BACKEND_URL in Vercel env
2. Verify backend is accessible from internet
3. Check CORS configuration

### API calls timeout
1. Increase timeout in api/proxy.js
2. Check Lambda Labs firewall rules
3. Verify backend performance

### Build fails on Vercel
1. Check pnpm version compatibility
2. Verify all dependencies are installed
3. Check build logs: `vercel logs --scope=build`

## 🔐 Security Considerations

1. **Use environment variables** - Never commit secrets
2. **Configure firewall** - Only allow necessary ports
3. **Enable HTTPS** - Use SSL for production
4. **API authentication** - Implement proper auth tokens
5. **Rate limiting** - Protect against abuse

## 🎯 Success Criteria

Your deployment is successful when:
- ✅ Frontend loads at https://your-app.vercel.app
- ✅ Health dashboard shows all services "healthy"
- ✅ API calls work without CORS errors
- ✅ MCP servers are accessible
- ✅ Database connections are stable

## 📊 Performance Optimization

1. **Enable Vercel Edge caching:**
```javascript
// In api/proxy.js
res.setHeader('Cache-Control', 's-maxage=10, stale-while-revalidate');
```

2. **Use CDN for static assets**
3. **Enable gzip compression**
4. **Optimize database queries**

## 🔄 Continuous Deployment

Set up GitHub Actions for automatic deployment:
```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-args: '--prod'
```

## 📞 Support

If deployment fails:
1. Check this guide's troubleshooting section
2. Review logs on both Vercel and Lambda Labs
3. Ensure all environment variables are set correctly
4. Verify network connectivity between services

Remember: The key to successful deployment is proper configuration of the API proxy and environment variables! 