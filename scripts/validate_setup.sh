#!/bin/bash
# Quick validation script for the Lambda-free setup

echo "🔍 Cherry AI - Setup Validation"
echo "=================================="

# Check for Lambda references
echo -e "\n📋 Checking for remaining Lambda references..."
Lambda_COUNT=$(grep -r "google-cloud\|Lambda\|firestore" --include="*.py" --include="*.txt" . 2>/dev/null | grep -v "venv/" | grep -v "__pycache__" | wc -l)

if [ "$Lambda_COUNT" -eq 0 ]; then
    echo "✅ No Lambda references found in code"
else
    echo "⚠️  Found $Lambda_COUNT Lambda references remaining"
fi

# Check requirements
echo -e "\n📋 Checking requirements..."
if grep -q "pymongo" requirements/base.txt; then
    echo "✅ MongoDB driver (pymongo) is in requirements"
else
    echo "❌ MongoDB driver (pymongo) missing from requirements"
fi

if grep -q "weaviate-client" requirements/base.txt; then
    echo "✅ Weaviate client is in requirements"
else
    echo "⚠️  Weaviate client not in requirements (optional)"
fi

# Check environment file
echo -e "\n📋 Checking environment configuration..."
if [ -f "env.example" ]; then
    echo "✅ env.example file exists"
else
    echo "❌ env.example file missing"
fi

if [ -f ".env" ]; then
    echo "✅ .env file exists"

    # Check for required variables
    for var in MONGODB_URI DRAGONFLY_URI WEAVIATE_URL OPENROUTER_API_KEY; do
        if grep -q "^$var=" .env; then
            echo "  ✓ $var is configured"
        else
            echo "  ✗ $var is NOT configured"
        fi
    done
else
    echo "⚠️  .env file not found - copy env.example to .env and configure"
fi

# Check Docker
echo -e "\n📋 Checking Docker setup..."
if command -v docker &> /dev/null; then
    echo "✅ Docker is installed"

    if docker ps &> /dev/null; then
        echo "✅ Docker daemon is running"
    else
        echo "❌ Docker daemon is not running"
    fi
else
    echo "❌ Docker is not installed"
fi

# Check Python dependencies
echo -e "\n📋 Checking Python environment..."
if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"

    if [[ "$VIRTUAL_ENV" != "" ]]; then
        echo "✅ Virtual environment is activated"
    else
        echo "⚠️  Virtual environment not activated (run: source venv/bin/activate)"
    fi
else
    echo "❌ Virtual environment not found"
fi

# Summary
echo -e "\n📊 SUMMARY"
echo "=========="
echo "1. Lambda cleanup: ${Lambda_COUNT} references remaining"
echo "2. Environment: Check .env configuration"
echo "3. Dependencies: Install with 'pip install -r requirements/base.txt'"
echo "4. Test setup: Run 'python scripts/test_new_setup.py'"
echo ""
echo "🚀 Next steps:"
echo "   1. Copy env.example to .env and configure"
echo "   2. Install dependencies: pip install -r requirements/base.txt"
echo "   3. Run tests: python scripts/test_new_setup.py"
echo "   4. Start locally: docker-compose up"
