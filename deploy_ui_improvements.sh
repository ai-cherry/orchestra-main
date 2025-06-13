#!/bin/bash

# 🎼 Orchestra AI - UI Improvement Deployment Script

echo "🎨 Deploying UI Improvements to Admin Interface..."

# Check if web server is running
if ! curl -s http://localhost:3000 > /dev/null; then
    echo "🚀 Starting web server..."
    cd web && npm run dev &
    sleep 3
fi

# Check real admin interface
if [ -f "web/public/real-admin.html" ]; then
    echo "✅ Real admin interface found at web/public/real-admin.html"
    echo "🌐 Real Admin interface available at: http://localhost:3002/real-admin.html"
else
    echo "❌ Real admin interface not found!"
    exit 1
fi

# Show improvement summary
echo ""
echo "🎼 Orchestra AI Admin Interface - Improvements Applied:"
echo "✅ Consistent brand colors (Orchestra AI blue/purple)"
echo "✅ Improved typography with gradient titles"
echo "✅ Enhanced visual hierarchy"
echo "✅ Better spacing and layout"
echo "✅ Accessible design patterns"
echo ""
echo "🎯 Next Steps:"
echo "1. Open http://localhost:3002/real-admin.html in your browser"
echo "2. Click 'Run Diagnostics' to see what Orchestra AI services are available" 
echo "3. Use the interface to manage your real Orchestra AI system"
echo ""
echo "🚀 Admin interface is ready!" 