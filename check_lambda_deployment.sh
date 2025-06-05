#!/bin/bash

echo "🔍 Checking Lambda Labs deployment status..."
echo "================================================"

SERVER_IP="150.136.94.139"
USERNAME="ubuntu"

echo "1. Testing SSH connection..."
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no $USERNAME@$SERVER_IP "echo '✅ SSH connection successful'" 2>/dev/null || echo "❌ SSH connection failed"

echo -e "\n2. Checking deployed files..."
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no $USERNAME@$SERVER_IP "ls -la /opt/orchestra/ 2>/dev/null | head -10" || echo "❌ Cannot access /opt/orchestra"

echo -e "\n3. Checking nginx configuration..."
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no $USERNAME@$SERVER_IP "sudo nginx -t 2>&1" || echo "❌ Nginx check failed"

echo -e "\n4. Checking service status..."
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no $USERNAME@$SERVER_IP "systemctl is-active nginx 2>/dev/null" || echo "❌ Nginx not active"

echo -e "\n5. Testing web access..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://$SERVER_IP/orchestrator/ || echo "❌ Web access failed"

echo -e "\n================================================"
echo "📋 Summary:"
echo "- Server IP: $SERVER_IP"
echo "- Access URL: http://$SERVER_IP/orchestrator/"
echo "- API Endpoint: http://$SERVER_IP:8000/api/"
echo "================================================"