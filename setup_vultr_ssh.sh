#!/bin/bash
echo "🔑 Setting up SSH access to Vultr"
echo "================================"
echo ""
echo "Please enter your Vultr root password:"
read -s VULTR_PASSWORD
echo ""

echo "Adding SSH key..."
sshpass -p "$VULTR_PASSWORD" ssh-copy-id -o StrictHostKeyChecking=no -i ~/.ssh/vultr_cherry_ai.pub root@45.32.69.157

echo ""
echo "Testing connection..."
ssh -i ~/.ssh/vultr_cherry_ai root@45.32.69.157 "echo '✅ SSH Setup Complete!' && hostname"
