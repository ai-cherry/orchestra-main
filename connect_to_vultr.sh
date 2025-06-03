#!/bin/bash

echo "🚀 Connecting to Vultr server..."
echo ""
echo "Server IP: 45.32.69.157"
echo ""

# Check if SSH key exists
SSH_KEY="$HOME/.ssh/id_rsa"
if [ ! -f "$SSH_KEY" ]; then
    SSH_KEY="$HOME/.ssh/orchestra_do_key"
fi

if [ ! -f "$SSH_KEY" ]; then
    echo "❌ No SSH key found. Please ensure you have an SSH key at:"
    echo "   ~/.ssh/id_rsa or ~/.ssh/orchestra_do_key"
    exit 1
fi

echo "Using SSH key: $SSH_KEY"
echo ""
echo "Connecting to root@45.32.69.157..."
echo ""

# Connect to Vultr server
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no root@45.32.69.157
