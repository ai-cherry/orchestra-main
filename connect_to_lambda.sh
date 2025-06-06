#!/bin/bash

echo "🚀 Connecting to Lambda server..."
echo ""
echo "Server IP: 45.32.69.157"
echo ""

# Check if SSH key exists
SSH_KEY="$HOME/.ssh/id_rsa"
if [ ! -f "$SSH_KEY" ]; then
    SSH_KEY="$HOME/.ssh/cherry_ai_do_key"
fi

if [ ! -f "$SSH_KEY" ]; then
    echo "❌ No SSH key found. Please ensure you have an SSH key at:"
    echo "   ~/.ssh/id_rsa or ~/.ssh/cherry_ai_do_key"
    exit 1
fi

echo "Using SSH key: $SSH_KEY"
echo ""
echo "Connecting to root@45.32.69.157..."
echo ""

# Connect to Lambda server
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no root@45.32.69.157
