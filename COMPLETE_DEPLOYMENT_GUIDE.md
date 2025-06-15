# 🎼 Orchestra AI Complete Deployment Guide

This guide covers the complete deployment of Orchestra AI with admin interface, all MCP servers, and persistent service management.

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Admin Frontend Deployment (Vercel)](#admin-frontend-deployment-vercel)
3. [Backend Services Deployment (Lambda Labs)](#backend-services-deployment-lambda-labs)
4. [MCP Servers Configuration](#mcp-servers-configuration)
5. [Persistent Service Management](#persistent-service-management)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)

## System Architecture

### Services Overview
```
┌─────────────────────────────────────────────────────────────┐
│                     Orchestra AI System                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Frontend Services (Vercel):                                │
│  ├── Modern Admin Interface → https://admin.orchestra.ai    │
│  └── Main Web Interface → https://orchestra.ai             │
│                                                             │
│  Backend Services (Lambda Labs - 150.136.94.139):          │
│  ├── API Server (Port 8000)                                │
│  ├── MCP Memory Server (Port 8003)                         │
│  ├── MCP Portkey Server (Port 8004)                        │
│  ├── AI Context Service (Port 8005)                        │
│  └── Admin Backend (Port 3003)                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Admin Frontend Deployment (Vercel)

### 1. Deploy Modern Admin to Vercel

```bash
# Navigate to modern-admin directory
cd modern-admin

# Install dependencies
npm install

# Build the project
npm run build

# Deploy to Vercel
vercel --prod

# Follow prompts to configure:
# - Project name: orchestra-admin
# - Framework: Vite
# - Build command: npm run build
# - Output directory: dist
```

### 2. Configure Environment Variables in Vercel

Go to your Vercel project settings and add:

```
VITE_API_URL=http://150.136.94.139:8000
VITE_MCP_MEMORY_URL=http://150.136.94.139:8003
VITE_MCP_PORTKEY_URL=http://150.136.94.139:8004
VITE_CONTEXT_SERVICE_URL=http://150.136.94.139:8005
```

## Backend Services Deployment (Lambda Labs)

### 1. SSH into Lambda Labs Instance

```bash
ssh -i ~/.ssh/orchestra_lambda ubuntu@150.136.94.139
```

### 2. Pull Latest Code

```bash
cd /home/ubuntu/orchestra-dev
git pull origin main
```

### 3. Install System Dependencies

```bash
# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    nginx \
    supervisor \
    postgresql \
    redis-server \
    build-essential
```

### 4. Setup Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt
```

## MCP Servers Configuration

### 1. Create Enhanced Supervisor Configuration

Create `/home/ubuntu/orchestra-dev/supervisor_config.conf`:

```ini
[unix_http_server]
file=/tmp/supervisor.sock

[supervisord]
logfile=/home/ubuntu/orchestra-dev/logs/supervisord.log
logfile_maxbytes=50MB
logfile_backups=10
loglevel=info
pidfile=/tmp/supervisord.pid
nodaemon=false
minfds=1024
minprocs=200

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///tmp/supervisor.sock

# MCP Memory Server
[program:mcp_memory]
command=/home/ubuntu/orchestra-dev/venv/bin/python -m uvicorn memory_management_server:app --host 0.0.0.0 --port 8003 --workers 2
directory=/home/ubuntu/orchestra-dev/mcp_servers
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=10
stdout_logfile=/home/ubuntu/orchestra-dev/logs/mcp_memory.log
stderr_logfile=/home/ubuntu/orchestra-dev/logs/mcp_memory_error.log
environment=PYTHONPATH="/home/ubuntu/orchestra-dev:/home/ubuntu/orchestra-dev/api"

# MCP Portkey Server
[program:mcp_portkey]
command=/home/ubuntu/orchestra-dev/venv/bin/python -m uvicorn portkey_mcp:app --host 0.0.0.0 --port 8004 --workers 2
directory=/home/ubuntu/orchestra-dev/packages/mcp-enhanced
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=10
stdout_logfile=/home/ubuntu/orchestra-dev/logs/mcp_portkey.log
stderr_logfile=/home/ubuntu/orchestra-dev/logs/mcp_portkey_error.log
environment=PYTHONPATH="/home/ubuntu/orchestra-dev:/home/ubuntu/orchestra-dev/api"

# API Server
[program:api_server]
command=/home/ubuntu/orchestra-dev/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
directory=/home/ubuntu/orchestra-dev/api
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=10
stdout_logfile=/home/ubuntu/orchestra-dev/logs/api.log
stderr_logfile=/home/ubuntu/orchestra-dev/logs/api_error.log
environment=PYTHONPATH="/home/ubuntu/orchestra-dev:/home/ubuntu/orchestra-dev/api"

# AI Context Service
[program:ai_context]
command=/home/ubuntu/orchestra-dev/venv/bin/python context_service.py
directory=/home/ubuntu/orchestra-dev/.ai-context
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=10
stdout_logfile=/home/ubuntu/orchestra-dev/logs/context_service.log
stderr_logfile=/home/ubuntu/orchestra-dev/logs/context_service_error.log
environment=PYTHONPATH="/home/ubuntu/orchestra-dev"

[group:orchestra]
programs=mcp_memory,mcp_portkey,api_server,ai_context
```

### 2. Configure Nginx Reverse Proxy

Create `/etc/nginx/sites-available/orchestra`:

```nginx
upstream api_backend {
    server localhost:8000;
}

upstream mcp_memory {
    server localhost:8003;
}

upstream mcp_portkey {
    server localhost:8004;
}

upstream context_service {
    server localhost:8005;
}

server {
    listen 80;
    server_name 150.136.94.139;
    
    # API Server
    location /api {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
    
    # MCP Memory Server
    location /mcp/memory {
        proxy_pass http://mcp_memory;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # MCP Portkey Server
    location /mcp/portkey {
        proxy_pass http://mcp_portkey;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # AI Context Service
    location /context {
        proxy_pass http://context_service;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "Orchestra AI System Healthy\n";
        add_header Content-Type text/plain;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/orchestra /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

## Persistent Service Management

### 1. Create Systemd Service

Create `/etc/systemd/system/orchestra-supervisor.service`:

```ini
[Unit]
Description=Orchestra AI Supervisor
After=network.target postgresql.service redis.service

[Service]
Type=forking
User=ubuntu
ExecStart=/usr/bin/supervisord -c /home/ubuntu/orchestra-dev/supervisor_config.conf
ExecStop=/usr/bin/supervisorctl shutdown
ExecReload=/usr/bin/supervisorctl reload
KillMode=process
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

### 2. Enable Services

```bash
# Enable and start supervisor
sudo systemctl daemon-reload
sudo systemctl enable orchestra-supervisor.service
sudo systemctl start orchestra-supervisor.service

# Check status
sudo systemctl status orchestra-supervisor.service
```

### 3. Service Management Commands

```bash
# View all services
supervisorctl status

# Start all services
supervisorctl start orchestra:*

# Stop all services
supervisorctl stop orchestra:*

# Restart a specific service
supervisorctl restart api_server

# View logs
supervisorctl tail -f api_server
```

## Monitoring and Maintenance

### 1. Setup Health Monitoring Script

Create `/home/ubuntu/orchestra-dev/monitor_health.sh`:

```bash
#!/bin/bash

# Health check endpoints
endpoints=(
    "http://localhost:8000/api/health:API Server"
    "http://localhost:8003/health:MCP Memory"
    "http://localhost:8004/health:MCP Portkey"
    "http://localhost:8005/health:AI Context"
)

# Check each endpoint
for endpoint in "${endpoints[@]}"; do
    IFS=':' read -r url service <<< "$endpoint"
    if curl -s "$url" > /dev/null 2>&1; then
        echo "✅ $service is healthy"
    else
        echo "❌ $service is down"
        # Restart the service
        supervisorctl restart $(echo $service | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
    fi
done
```

### 2. Setup Cron Job for Monitoring

```bash
# Add to crontab
crontab -e

# Add this line to check health every 5 minutes
*/5 * * * * /home/ubuntu/orchestra-dev/monitor_health.sh >> /home/ubuntu/orchestra-dev/logs/health_monitor.log 2>&1
```

### 3. Log Rotation

Create `/etc/logrotate.d/orchestra`:

```
/home/ubuntu/orchestra-dev/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
    sharedscripts
    postrotate
        supervisorctl restart all
    endscript
}
```

## Quick Deployment Script

For convenience, here's a complete deployment script:

```bash
#!/bin/bash
# save as deploy_orchestra.sh

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🎼 Deploying Orchestra AI Complete System"

# 1. Deploy Admin Frontend to Vercel
echo "Deploying Admin Frontend..."
cd modern-admin
npm install && npm run build
vercel --prod --yes

# 2. Deploy Backend to Lambda Labs
echo "Deploying Backend Services..."
ssh -i ~/.ssh/orchestra_lambda ubuntu@150.136.94.139 << 'ENDSSH'
cd /home/ubuntu/orchestra-dev
git pull origin main
source venv/bin/activate
pip install -r requirements.txt

# Restart all services
sudo supervisorctl restart orchestra:*

# Check status
sudo supervisorctl status
ENDSSH

echo -e "${GREEN}✅ Deployment Complete!${NC}"
```

## Verification

After deployment, verify all services:

```bash
# From your local machine
curl http://150.136.94.139/health
curl http://150.136.94.139/api/health
curl http://150.136.94.139/mcp/memory/health
curl http://150.136.94.139/mcp/portkey/health
curl http://150.136.94.139/context/health
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs
supervisorctl tail -f service_name
journalctl -u orchestra-supervisor -f

# Check port availability
sudo lsof -i :8000
```

### Nginx Issues
```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log
```

### Python Import Errors
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/home/ubuntu/orchestra-dev:/home/ubuntu/orchestra-dev/api
```

---

This deployment ensures all Orchestra AI services run persistently with automatic restart on failure, proper logging, and monitoring. 