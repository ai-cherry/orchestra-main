#!/bin/bash

# Fix missing dependencies for Orchestra AI

echo "🔧 Fixing missing dependencies..."

# Activate virtual environment
source venv/bin/activate

# Install missing Python packages
echo "📦 Installing missing Python packages..."
pip install greenlet python-magic python-magic-bin

# Fix libmagic for macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Fixing libmagic for macOS..."
    brew install libmagic
fi

# Install missing npm packages if needed
if [ -d "web" ]; then
    echo "📦 Installing frontend dependencies..."
    cd web
    npm install
    cd ..
fi

echo "✅ Dependencies fixed!"
echo ""
echo "Note: If you're still having issues with PostgreSQL, make sure it's running:"
echo "  brew services start postgresql@16  # For macOS"
echo "  sudo systemctl start postgresql    # For Linux" 