# Orchestra AI Deployment Fix Guide

## Issues Identified

### 1. Vercel Frontend Deployment Issues

#### Problem: Dependency Conflict
- **Error**: `date-fns@^4.1.0` conflicts with `react-day-picker@8.10.1` which requires `date-fns@^2.28.0 || ^3.0.0`
- **Fixed**: Updated `modern-admin/package.json` to use `date-fns@^3.6.0`

#### Problem: Wrong Package Manager
- **Error**: Vercel was using npm but the project uses pnpm (has pnpm-lock.yaml)
- **Fixed**: Updated `vercel.json` to use pnpm with proper install command

#### Problem: Python Dependencies Being Installed
- **Error**: Vercel was trying to install Python requirements.txt for a frontend deployment
- **Fixed**: Created `.vercelignore` to exclude Python files and added `ignoreCommand`

#### Problem: API Proxy Path
- **Error**: Rewrite was pointing to `/api/proxy` instead of `/api/proxy.js`
- **Fixed**: Updated rewrite rule in `vercel.json`

### 2. Port Configuration

The current port setup is:
- **Backend API (Lambda Labs)**: http://150.136.94.139:8000 ✅
- **MCP Memory Service (Local)**: http://localhost:8003 ✅
- **Admin Frontend (Local)**: http://localhost:5173 ✅
- **Redis (Local)**: redis://localhost:6379 ✅

### 3. Infrastructure as Code Status

All components are properly configured:
- Docker Compose for local development ✅
- Vercel for frontend deployment 🔧 (now fixed)
- Lambda Labs for backend ✅

## Quick Fix Commands

### 1. Deploy Frontend to Vercel
```bash
# Commit the fixes
git add -A
git commit -m "fix: Resolve Vercel deployment issues"
git push

# Deploy to Vercel
cd /Users/lynnmusil/orchestra-dev
vercel --prod
```

### 2. Test Local Development
```bash
# Start all services locally
./deploy.sh local

# Or manually:
docker-compose -f docker-compose.dev.yml up -d
```

### 3. Verify Backend Health
```bash
# Lambda Labs backend
curl http://150.136.94.139:8000/health

# Local services
curl http://localhost:8000/health
curl http://localhost:8003/health
```

## Environment Variables

### For Vercel (Production)
Already configured in `vercel.json`:
- `LAMBDA_BACKEND_URL`: Points to Lambda Labs backend
- `VITE_API_URL`: Empty (uses proxy)

### For Local Development
Create `modern-admin/.env.local`:
```env
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
VITE_ENABLE_WEBSOCKET=true
VITE_ENABLE_MONITORING=true
VITE_ENABLE_AI_CHAT=true
VITE_DEBUG=true
```

## Deployment Architecture

```
┌─────────────────────┐     ┌──────────────────────┐
│   Vercel Frontend   │────▶│   Lambda Labs API    │
│  (Admin Dashboard)  │     │ (150.136.94.139:8000)│
│    /api/proxy.js    │     └──────────────────────┘
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Local Development  │
│ ├─ API (8000)      │
│ ├─ MCP (8003)      │
│ ├─ Admin (5173)    │
│ └─ Redis (6379)    │
└─────────────────────┘
```

## Next Steps

1. **Deploy to Vercel**: Run `vercel --prod` to test the fixes
2. **Monitor Logs**: Use `vercel logs [deployment-url]` to check runtime logs
3. **Test API Proxy**: Verify `/api/health` works on the deployed frontend
4. **Setup Monitoring**: Consider adding error tracking (Sentry) and uptime monitoring

## Troubleshooting

### If Vercel deployment still fails:
1. Check build logs: `vercel inspect --logs [deployment-url]`
2. Verify pnpm version matches: `pnpm@10.4.1`
3. Clear Vercel cache: Add `?forceNew=1` to deployment command

### If API proxy doesn't work:
1. Check CORS headers in `api/proxy.js`
2. Verify `LAMBDA_BACKEND_URL` environment variable
3. Test backend directly: `curl http://150.136.94.139:8000/health`

### If local development fails:
1. Ensure Docker is running
2. Check port availability: `lsof -i :8000,8003,5173,6379`
3. Reset volumes: `docker-compose -f docker-compose.dev.yml down -v` 