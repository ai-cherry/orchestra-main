#!/bin/bash
# Orchestra AI Frontend Deployment Script

set -e

echo "🚀 Deploying Orchestra AI Frontend to Vercel..."

# Check if we're in the right directory
if [ ! -f "vercel.json" ] || [ ! -d "modern-admin" ]; then
    echo "❌ Error: Must run from Orchestra AI root directory"
    exit 1
fi

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Error: Vercel CLI not installed"
    echo "Install with: npm i -g vercel"
    exit 1
fi

# Check if we have required environment variables
if [ -z "$LAMBDA_BACKEND_URL" ]; then
    echo "⚠️  Warning: LAMBDA_BACKEND_URL not set"
    echo "Using default: http://150.136.94.139:8000"
    export LAMBDA_BACKEND_URL="http://150.136.94.139:8000"
fi

echo "📦 Installing dependencies..."
cd modern-admin
pnpm install

echo "🔨 Building React app..."
pnpm run build

echo "📤 Deploying to Vercel..."
cd ..

# Deploy with environment variable
vercel --prod \
    --yes \
    --no-clipboard \
    --env LAMBDA_BACKEND_URL="$LAMBDA_BACKEND_URL"

echo "✅ Deployment complete!"
echo ""
echo "🌐 Your app should be available at:"
echo "   https://orchestra-ai.vercel.app"
echo ""
echo "📊 Check deployment status:"
echo "   vercel ls"
echo ""
echo "📝 View logs:"
echo "   vercel logs" 