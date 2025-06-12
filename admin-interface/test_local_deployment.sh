#!/bin/bash

# Test Local Deployment Script for Admin Interface
echo "🧪 Testing Orchestra AI Admin Interface Locally"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Not in admin-interface directory"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm ci
fi

# Build the project
echo "🔨 Building production bundle..."
npm run build

# Check if build succeeded
if [ ! -d "dist" ]; then
    echo "❌ Build failed - no dist directory found"
    exit 1
fi

# Check for root div in built HTML
echo "🔍 Checking for root element in built HTML..."
if grep -q '<div id="root"></div>' dist/index.html; then
    echo "✅ Root element found in dist/index.html"
else
    echo "❌ Root element missing in dist/index.html!"
    exit 1
fi

# Preview the build locally
echo ""
echo "🌐 Starting local preview server..."
echo "📍 Open http://localhost:4173 in your browser"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

npm run preview 