# Cherry AI Deployment Fix Guide

## 🚨 Current Issues

1. **Old Frontend Version**: The website shows an outdated version of the admin UI
2. **Backend API Down**: FastAPI backend is not running (502 Bad Gateway errors)
3. **Missing Environment Config**: No proper environment variables for LLM APIs
4. **No Service Management**: Backend not set up to run 24/7 automatically

## 🛠️ Quick Fix Solutions

### Option 1: Quick Frontend Fix (2 minutes)
If you just need to update the frontend immediately:

```bash
bash quick_fix_frontend.sh
```

This will:
- Build the latest admin-ui
- Deploy it to nginx
- Clear nginx cache

### Option 2: Full System Fix (10 minutes)
For a complete fix including backend:

```bash
bash fix_cherry_deployment.sh
```

This will:
- Build and deploy latest frontend
- Set up backend environment
- Create systemd service for 24/7 operation
- Configure nginx properly
- Start all services

### Option 3: Diagnose First
To see what's wrong before fixing:

```bash
bash diagnose_cherry_deployment.sh
```

## 📋 Manual Fix Steps

### 1. Fix Frontend Version

```bash
# Build latest frontend
cd /root/cherry_ai-main/admin-ui
npm install
npm run build

# Deploy to nginx
sudo rm -rf /var/www/html/*
sudo cp -r dist/* /var/www/html/
sudo chown -R www-data:www-data /var/www/html
sudo nginx -s reload
```

### 2. Fix Backend API

Create environment file `/etc/cherry_ai.env`:

```bash
# Security
JWT_SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=720

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=OrchAI_Admin2024!
ADMIN_EMAIL=admin@cherry_ai.ai

# LLM APIs (add your keys)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
# Add other API keys as needed
```

Create systemd service `/etc/systemd/system/cherry_ai-backend.service`:

```ini
[Unit]
Description=Cherry AI Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/cherry_ai-main
EnvironmentFile=/etc/cherry_ai.env
ExecStart=/root/cherry_ai-main/venv/bin/python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cherry_ai-backend
sudo systemctl start cherry_ai-backend
```

### 3. Configure Nginx

Update `/etc/nginx/sites-available/default` or create `/etc/nginx/sites-available/cherry-ai`:

```nginx
server {
    listen 443 ssl http2;
    server_name cherry-ai.me;
    
    ssl_certificate /etc/letsencrypt/live/cherry-ai.me/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cherry-ai.me/privkey.pem;
    
    root /var/www/html;
    index index.html;
    
    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔍 Troubleshooting

### Still Seeing Old Version?

1. **Clear Browser Cache**: Use incognito mode or clear all site data
2. **Clear CDN Cache**: If using Cloudflare, purge cache from dashboard
3. **Check Nginx Root**: Verify nginx is serving from correct directory
   ```bash
   grep -r "root" /etc/nginx/sites-enabled/
   ```

### Backend Not Starting?

1. **Check Logs**:
   ```bash
   journalctl -u cherry_ai-backend -f
   ```

2. **Common Issues**:
   - Missing Python dependencies: `pip install -r requirements.txt`
   - Missing API keys: Add to `/etc/cherry_ai.env`
   - Port 8000 in use: `lsof -i :8000`

3. **Test Manually**:
   ```bash
   cd /root/cherry_ai-main
   source venv/bin/activate
   python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8000
   ```

### API Returns 502?

1. **Check Backend Status**:
   ```bash
   systemctl status cherry_ai-backend
   ```

2. **Check Nginx Proxy**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Check Nginx Logs**:
   ```bash
   tail -f /var/log/nginx/error.log
   ```

## 📊 Monitoring Commands

```bash
# Backend logs
journalctl -u cherry_ai-backend -f

# Backend status
systemctl status cherry_ai-backend

# Nginx access logs
tail -f /var/log/nginx/access.log

# Check if services are running
ps aux | grep uvicorn
netstat -tuln | grep 8000
```

## 🔐 Security Notes

1. **Change Default Passwords**: Update admin password in production
2. **Secure API Keys**: Keep `/etc/cherry_ai.env` with restricted permissions
3. **SSL Certificate**: Ensure Let's Encrypt auto-renewal is configured
4. **Firewall**: Only expose necessary ports (80, 443)

## 🚀 Next Steps

After fixing the deployment:

1. **Add LLM API Keys**: Edit `/etc/cherry_ai.env` with your actual API keys
2. **Set Up Monitoring**: Configure Prometheus/Grafana for metrics
3. **Enable Backups**: Set up automated backups for data persistence
4. **Configure Alerts**: Set up alerts for service failures

## 📞 Support

If issues persist after following this guide:

1. Run the diagnostic script and save output
2. Check all log files mentioned above
3. Verify DNS is pointing to correct server
4. Ensure SSL certificates are valid

Remember to always test in incognito/private browsing mode to avoid cache issues!