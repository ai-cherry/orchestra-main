#!/bin/bash
# Quick deploy script for Admin UI

echo "🚀 Deploying Admin UI..."

# Navigate to admin UI directory
cd /root/orchestra-main/admin-ui

# Build the project
echo "📦 Building Admin UI..."
npm run build

# Clear old files and deploy new ones
echo "🗑️  Clearing old files..."
rm -rf /var/www/orchestra-admin/*

echo "📤 Deploying new build..."
cp -r dist/* /var/www/orchestra-admin/

# Reload nginx to ensure no caching issues
echo "🔄 Reloading nginx..."
systemctl reload nginx

echo "✅ Admin UI deployed successfully!"
echo "🌐 Access at: https://cherry-ai.me"
echo ""
echo "📝 Login credentials:"
echo "   Username: scoobyjava"
echo "   Password: Huskers1983$" 