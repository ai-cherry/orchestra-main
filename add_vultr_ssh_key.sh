#!/bin/bash
# Add SSH key to Vultr server

VULTR_IP="45.32.69.157"
SSH_PUBLIC_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICPAgt2FYOQOaBtA0BdytVd4Ig+FhI9R7lM0SWUIUE0g orchestra@vultr"

echo "🔑 Adding SSH key to Vultr server..."
echo "You'll be prompted for the root password from Vultr dashboard"
echo ""

# Install sshpass if needed
if ! command -v sshpass &> /dev/null; then
    echo "Installing sshpass..."
    sudo apt-get update && sudo apt-get install -y sshpass
fi

# Add the SSH key
ssh-copy-id -i ~/.ssh/vultr_orchestra.pub root@$VULTR_IP

echo ""
echo "✅ Testing connection with new key..."
ssh -i ~/.ssh/vultr_orchestra root@$VULTR_IP "echo 'Success! Connected to Vultr server' && uname -a"
