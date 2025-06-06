#!/bin/bash
echo "🔑 Setting up SSH access to Lambda"
echo "================================"
echo ""
echo "Please enter your Lambda root password:"
read -s Lambda_PASSWORD
echo ""

echo "Adding SSH key..."
sshpass -p "$Lambda_PASSWORD" ssh-copy-id -o StrictHostKeyChecking=no -i ~/.ssh/Lambda_cherry_ai.pub root@45.32.69.157

echo ""
echo "Testing connection..."
ssh -i ~/.ssh/Lambda_cherry_ai root@45.32.69.157 "echo '✅ SSH Setup Complete!' && hostname"
