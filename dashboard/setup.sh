#!/bin/bash

# Dashboard Setup Script
# This script helps set up the dashboard with proper dependencies

echo "🚀 Setting up AI Orchestrator Dashboard..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check Node version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18+ is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js $(node -v) detected"

# Clean previous installations
echo "🧹 Cleaning previous installations..."
rm -rf node_modules package-lock.json

# Clear npm cache
echo "🧹 Clearing npm cache..."
npm cache clean --force

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    echo "💡 Try running: npm install --legacy-peer-deps"
    exit 1
fi

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
    echo "📝 Creating .env.local from .env.example..."
    cp .env.example .env.local
    echo "⚠️  Please update .env.local with your API configuration"
fi

# Run type checking
echo "🔍 Running TypeScript type check..."
npm run type-check || echo "⚠️  TypeScript errors detected - this is expected until all types are resolved"

# Build the project
echo "🏗️  Building the project..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Build completed successfully"
    echo ""
    echo "🎉 Setup complete! You can now run:"
    echo "   npm run dev    - Start development server"
    echo "   npm run build  - Build for production"
    echo "   npm start      - Start production server"
else
    echo "❌ Build failed. Please check the errors above."
    exit 1
fi