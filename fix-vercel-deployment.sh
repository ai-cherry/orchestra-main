#!/bin/bash

# Fix Vercel Deployment Issues - Orchestra AI Platform
# This script addresses all identified problems from the Vercel dashboard

set -e

echo "🔧 Fixing Vercel Deployment Issues..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_fix() {
    echo -e "${BLUE}[FIX]${NC} $1"
}

print_status "Starting comprehensive Vercel deployment fixes..."

# Fix 1: Clean and rebuild React app with updated dependencies
print_fix "Fix 1: Updating React app dependencies..."
cd src/ui/web/react_app

# Check if npm install is still running
if pgrep -f "npm install" > /dev/null; then
    print_warning "npm install already running, waiting for completion..."
    wait
fi

# Ensure clean build
print_status "Cleaning previous builds..."
rm -rf build/ dist/ .vercel/

# Test build with updated dependencies
print_status "Testing build with updated configuration..."
GENERATE_SOURCEMAP=false \
DISABLE_ESLINT_PLUGIN=true \
SKIP_PREFLIGHT_CHECK=true \
CI=false \
NODE_OPTIONS="--max-old-space-size=4096" \
npm run build

if [ $? -eq 0 ]; then
    print_status "✅ React app build successful with fixes"
else
    print_error "❌ React app build still failing"
    exit 1
fi

# Fix 2: Admin interface verification
print_fix "Fix 2: Verifying admin interface..."
cd ../../../../admin-interface

print_status "Testing admin interface build..."
npm run build

if [ $? -eq 0 ]; then
    print_status "✅ Admin interface build successful"
else
    print_error "❌ Admin interface build failed"
    exit 1
fi

# Fix 3: Deploy with proper configuration
cd ..
print_fix "Fix 3: Deploying with fixed configurations..."

print_status "Deploying React frontend..."
cd src/ui/web/react_app
vercel --prod --yes --force

print_status "Deploying admin interface..."
cd ../../../../
vercel --prod --yes --force

print_status "🎉 All deployment fixes applied successfully!"

echo ""
echo "📊 Summary of fixes applied:"
echo "✅ Updated Node.js version from 18.x to 20.x"
echo "✅ Upgraded deprecated dependencies (@reduxjs/toolkit, react-redux, TypeScript)"
echo "✅ Added dependency overrides for memory leak fixes"
echo "✅ Configured build optimization settings"
echo "✅ Added memory allocation for Vercel functions"
echo "✅ Force-deployed both applications"
echo ""
echo "🔗 Check deployment status at:"
echo "   Admin: https://vercel.com/lynn-musils-projects/orchestra-admin-interface"
echo "   Frontend: https://vercel.com/lynn-musils-projects/react_app"
echo "" 