#!/bin/bash
# Deploy Admin UI to Vultr nginx
set -e

echo "🚀 Deploying Admin UI..."

cd admin-ui

# Build
echo "📦 Building Admin UI..."
pnpm run build-no-ts || pnpm build

# Deploy
echo "🗑️  Clearing old files..."
sudo rm -rf /var/www/orchestra-admin/*

echo "📤 Deploying new build..."
sudo cp -r dist/* /var/www/orchestra-admin/

# Set permissions
sudo chown -R www-data:www-data /var/www/orchestra-admin
sudo chmod -R 755 /var/www/orchestra-admin

# Reload nginx
echo "🔄 Reloading nginx..."
sudo systemctl reload nginx

echo "✅ Admin UI deployed successfully!"
echo "🌐 Access at: https://cherry-ai.me/admin/"
echo ""
echo "📝 Login credentials:"
echo "   Username: scoobyjava"
echo "   Password: Huskers1983$"
