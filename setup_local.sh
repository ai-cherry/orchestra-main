#!/bin/bash

echo "🏠 Setting up local development environment"
echo "=========================================="

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment template
cp .env.example .env 2>/dev/null || cp .env .env.local

echo ""
echo "✅ Local setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys"
echo "2. Run: source venv/bin/activate"
echo "3. Start coding!"
echo "4. Deploy: git push origin main"
echo ""
echo "Production URL: https://cherry-ai.me"
