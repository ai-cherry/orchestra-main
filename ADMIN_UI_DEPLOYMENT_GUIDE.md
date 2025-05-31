# Admin UI Deployment Guide

This guide explains how to build and deploy the React Admin UI on the unified Vultr server.

## Prerequisites
- Node.js 20+ installed on the server
- Direct SSH access to the Vultr server

## 1. Local Build and Deploy
```bash
# SSH to server
ssh root@45.32.69.157

# Navigate to project
cd /root/orchestra-main

# Build Admin UI
cd admin-ui
npm install
npm run build

# Files are automatically served by Nginx
```

## 2. Automatic Sync via GitHub
Any push to the main branch automatically:
1. Syncs code to the server
2. Optionally rebuilds if package.json changed
3. No manual intervention needed

## 3. Access
The Admin UI is served by Nginx and available at:
- `http://45.32.69.157` - Direct IP access
- Port 80 - Default HTTP

## 4. Troubleshooting
```bash
# Check Nginx status
systemctl status nginx

# View Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Rebuild Admin UI
cd /root/orchestra-main/admin-ui
npm run build
```

## 5. Development Mode
For local development on the server:
```bash
cd /root/orchestra-main/admin-ui
npm run dev
# Access at http://45.32.69.157:3000
```
