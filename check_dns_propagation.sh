#!/bin/bash
# DNS Propagation Checker for cherry-ai.me

echo "🔍 DNS Propagation Checker"
echo "========================="
echo "Target IP: 45.32.69.157"
echo ""

while true; do
    echo "Checking DNS at $(date '+%Y-%m-%d %H:%M:%S')..."
    
    # Check main domain
    CURRENT_IP=$(dig cherry-ai.me +short)
    if [ "$CURRENT_IP" = "45.32.69.157" ]; then
        echo "✅ cherry-ai.me → $CURRENT_IP (UPDATED!)"
    else
        echo "❌ cherry-ai.me → $CURRENT_IP (old IP)"
    fi
    
    # Check www
    WWW_IP=$(dig www.cherry-ai.me +short)
    if [ "$WWW_IP" = "45.32.69.157" ]; then
        echo "✅ www.cherry-ai.me → $WWW_IP (UPDATED!)"
    else
        echo "❌ www.cherry-ai.me → $WWW_IP (not set)"
    fi
    
    # Check if all updated
    if [ "$CURRENT_IP" = "45.32.69.157" ] && [ "$WWW_IP" = "45.32.69.157" ]; then
        echo ""
        echo "🎉 DNS FULLY PROPAGATED!"
        echo "Your website is now accessible at:"
        echo "   https://cherry-ai.me"
        echo "   https://www.cherry-ai.me"
        break
    else
        echo ""
        echo "⏳ Waiting 30 seconds before next check..."
        echo "   (Press Ctrl+C to stop)"
        sleep 30
    fi
    echo "---"
done 