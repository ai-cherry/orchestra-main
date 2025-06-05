#!/bin/bash

# Cherry AI Server Fix Script
# This script fixes SSH access, restarts nginx, and deploys the collaboration bridge

echo "🔧 FIXING CHERRY AI SERVERS..."

# Add SSH key for user access
echo "📝 Adding SSH key..."
mkdir -p ~/.ssh
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDAvamdxYaJv2aUTmv0pj44dIjrMCn31iNPbeqq5lgIfX8gllGiHl0OR9R5Mu9IZaJGGz9lr5pU969CODGtEtCsYJRWnl/UheM487F3thZVP4R0oy+EllZcSlFZ5DdP2+kBaLe+hbws6mkFTRpL5G52fvMak6m1pVp9Z0r/lNMHeoT1c7DKsXCwpCmUxJnNYAjsZjbHRPhlObpag3Fmrujp17l/Hf/FH3pa19wZca8IAq0ZnxgP20lK9SX/jj8wogPkE+ZetRlJ1oX5dupaKSC6TaLGPm33kgP9XPg+Peb+GrpWeXqFgXWgwnB4+xfl/CO2hUsEZGEDBVRDqVH23BLTogJdfAzk3KH8oc88s3i8//+g+XTFIXg4QSfzDYU6zjUAZQgxyC1g0RSC9jrTI/IcmpG90wGfEBN3tFB1t2qKZ7wgWCU20hz99+cMhVMcxaK6+3DqOnjAJPfXqGfx57Tt6YtgFrH849DBS7MIp1bMwbrSix0uE9SUKoXKvBDuM8A39Bxx7r/zaZigFVrRlQHXa+YO0/qmptAFpXUuRkn/VqSLwyhoMSuDpi5tTlQ6XOejJHxmzCNiAraNEe7IDp/ZZPRptcqBPrB5p+qCpXDQhZMR7ANQpLhe2KBhc4DKAZpcWgfZhhwqLHowXsS8fnbBj0V9ExfYF34LPNyHh+wjXw== cherry-ai-collaboration-20250604" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh

# Update system packages
echo "📦 Updating system packages..."
apt update -y
apt upgrade -y

# Install required packages
echo "🔧 Installing required packages..."
apt install -y nginx python3 python3-pip python3-venv git curl wget ufw

# Install Python packages for collaboration bridge
echo "🐍 Installing Python packages..."
pip3 install websockets asyncio flask requests

# Configure firewall
echo "🔥 Configuring firewall..."
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8765/tcp  # Collaboration bridge
ufw --force enable

# Restart services
echo "🔄 Restarting services..."
systemctl restart ssh
systemctl enable ssh
systemctl restart nginx
systemctl enable nginx

# Check service status
echo "📊 Checking service status..."
systemctl status ssh --no-pager
systemctl status nginx --no-pager

# Create web directory if it doesn't exist
mkdir -p /var/www/html
mkdir -p /var/www/cherry-ai

# Set proper permissions
chown -R www-data:www-data /var/www/
chmod -R 755 /var/www/

echo "✅ Server fix completed!"
echo "🌐 Testing nginx: curl -I http://localhost"
curl -I http://localhost

echo "🔑 SSH should now work with the provided key"
echo "🚀 Ready for collaboration bridge deployment"

