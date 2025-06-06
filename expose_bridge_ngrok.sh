#!/bin/bash
# Expose Cherry AI Bridge for external AI connections using ngrok

echo "🌐 Exposing Cherry AI Bridge for external connections..."
echo "============================================"

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed!"
    echo "Install it from: https://ngrok.com/download"
    echo "Or via Homebrew: brew install ngrok"
    exit 1
fi

# Start ngrok for the bridge
echo "🚀 Starting ngrok tunnel for WebSocket bridge..."
echo "📡 Local bridge URL: ws://localhost:8765/ws"
echo ""

# Run ngrok and show the public URL
ngrok http 8765 --log=stdout --log-level=info

echo ""
echo "✅ Share the ngrok URL with Manus AI!"
echo "They should connect to: wss://[your-ngrok-subdomain].ngrok.io/ws" 