#!/bin/bash

# Deploy Orchestra AI Platform to Vercel
# This script handles the deployment of both admin interface and frontend

set -e

echo "🚀 Starting Orchestra AI Platform Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    print_error "Not in orchestra-main directory. Please run from project root."
    exit 1
fi

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    print_error "Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Build both applications
print_status "Building applications..."

print_status "Building admin interface..."
if npm run build:admin; then
    print_status "Admin interface build successful ✅"
else
    print_error "Admin interface build failed ❌"
    exit 1
fi

print_status "Building React frontend..."
if npm run build:frontend; then
    print_status "React frontend build successful ✅"
else
    print_error "React frontend build failed ❌"
    exit 1
fi

# Check deployment status
print_status "Checking current deployment status..."

# Deploy admin interface
print_status "Deploying admin interface..."
echo "Run: vercel --prod --yes"
print_warning "Manual step required: Run 'vercel --prod --yes' to deploy"

# Deploy React app
print_status "Deploying React frontend from src/ui/web/react_app..."
echo "Run: cd src/ui/web/react_app && vercel --prod --yes"
print_warning "Manual step required: Run 'cd src/ui/web/react_app && vercel --prod --yes' to deploy React app"

print_status "Deployment preparation complete! 🎉"
print_status "Both applications are built and ready for deployment."

echo ""
echo "Next steps:"
echo "1. Run 'vercel --prod --yes' from project root for admin interface"
echo "2. Run 'cd src/ui/web/react_app && vercel --prod --yes' for React frontend"
echo "3. Configure domain aliases in Vercel dashboard"
echo "" 