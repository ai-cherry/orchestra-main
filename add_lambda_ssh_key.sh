#!/bin/bash
# Add SSH key to Lambda server

Lambda_IP="45.32.69.157"
SSH_PUBLIC_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICPAgt2FYOQOaBtA0BdytVd4Ig+FhI9R7lM0SWUIUE0g cherry_ai@Lambda"

echo "🔑 Adding SSH key to Lambda server..."
echo "You'll be prompted for the root password from Lambda dashboard"
echo ""

# Install sshpass if needed
if ! command -v sshpass &> /dev/null; then
    echo "Installing sshpass..."
    sudo apt-get update && sudo apt-get install -y sshpass
fi

# Add the SSH key
ssh-copy-id -i ~/.ssh/Lambda_cherry_ai.pub root@$Lambda_IP

echo ""
echo "✅ Testing connection with new key..."
ssh -i ~/.ssh/Lambda_cherry_ai root@$Lambda_IP "echo 'Success! Connected to Lambda server' && uname -a"
