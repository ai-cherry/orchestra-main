#!/bin/bash
# Script to add SSH key to DigitalOcean droplets using password

echo "🔑 Adding SSH key to DigitalOcean droplets..."

# Your SSH public key
SSH_PUBLIC_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICq38OXXQVPAqVHzP99JvpDJBw+Myl8kItDGXOrurNYB paperspace@ai-cherry-orchestra"

# Droplet IPs
VECTOR_IP="68.183.170.81"
APP_IP="159.65.79.26"

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "📦 Installing sshpass..."
    sudo apt-get update && sudo apt-get install -y sshpass
fi

# Function to add SSH key to a droplet
add_key_to_droplet() {
    local ip=$1
    local name=$2

    echo "📌 Adding SSH key to $name droplet ($ip)..."

    # Add the SSH key using sshpass
    sshpass -p 'xTD.8HBd?-+Bib' ssh -o StrictHostKeyChecking=no root@$ip "mkdir -p ~/.ssh && echo '$SSH_PUBLIC_KEY' >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys && echo 'SSH key added successfully'"

    if [ $? -eq 0 ]; then
        echo "✅ SSH key added to $name droplet"
    else
        echo "❌ Failed to add SSH key to $name droplet"
        return 1
    fi
}

# Add key to both droplets
add_key_to_droplet $VECTOR_IP "Vector"
add_key_to_droplet $APP_IP "App"

echo ""
echo "🎯 Testing SSH key authentication..."

# Test connections
echo -n "Testing Vector droplet... "
if ssh -o PasswordAuthentication=no -o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519 root@$VECTOR_IP "echo 'OK'" 2>/dev/null | grep -q "OK"; then
    echo "✅ Success"
else
    echo "❌ Failed"
fi

echo -n "Testing App droplet... "
if ssh -o PasswordAuthentication=no -o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519 root@$APP_IP "echo 'OK'" 2>/dev/null | grep -q "OK"; then
    echo "✅ Success"
else
    echo "❌ Failed"
fi

echo ""
echo "🚀 SSH key setup complete! You can now run ./setup_do_dev_environment.sh"
