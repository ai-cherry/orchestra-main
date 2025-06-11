#!/bin/bash
# Verification script for testing setup
# Run this to verify that the GitHub Actions pytest fixes are working correctly

set -e

echo "🧪 Verifying Cherry AI Testing Setup..."
echo "============================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    exit 1
fi

echo -e "${YELLOW}📋 Checking required files...${NC}"

# Check required files exist
files_to_check=(
    "requirements.txt"
    "requirements-dev.txt"
    "pytest.ini"
    "tests/__init__.py"
    "tests/test_mvp_imports.py"
    ".github/workflows/main.yml"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file exists"
    else
        echo -e "${RED}❌${NC} $file missing"
        exit 1
    fi
done

echo ""
echo -e "${YELLOW}🐍 Checking Python environment...${NC}"

# Check if we're in a virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo -e "${GREEN}✓${NC} Virtual environment active: $VIRTUAL_ENV"
else
    echo -e "${YELLOW}⚠️${NC} No virtual environment detected (recommended but not required)"
fi

# Check Python version
python_version=$(python --version 2>&1)
echo -e "${GREEN}✓${NC} Python version: $python_version"

echo ""
echo -e "${YELLOW}📦 Installing development dependencies...${NC}"

# Install development dependencies
pip install -r requirements-dev.txt > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Development dependencies installed successfully"
else
    echo -e "${RED}❌${NC} Failed to install development dependencies"
    exit 1
fi

echo ""
echo -e "${YELLOW}🧪 Running pytest...${NC}"

# Run pytest with verbose output
if pytest -v; then
    echo -e "${GREEN}✓${NC} All tests passed!"
else
    echo -e "${RED}❌${NC} Some tests failed"
    exit 1
fi

echo ""
echo -e "${YELLOW}📊 Checking test coverage...${NC}"

# Check if pytest-cov is available and run coverage
if python -c "import pytest_cov" 2>/dev/null; then
    echo "Running test coverage analysis..."
    pytest --cov=. --cov-report=term-missing tests/test_mvp_imports.py
else
    echo -e "${YELLOW}⚠️${NC} pytest-cov not available, skipping coverage analysis"
fi

echo ""
echo -e "${YELLOW}🔍 Verifying GitHub Actions workflow syntax...${NC}"

# Basic YAML syntax check
if command -v yamllint &> /dev/null; then
    if yamllint .github/workflows/main.yml; then
        echo -e "${GREEN}✓${NC} GitHub Actions workflow YAML is valid"
    else
        echo -e "${RED}❌${NC} GitHub Actions workflow YAML has syntax errors"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️${NC} yamllint not available, skipping YAML validation"
fi

echo ""
echo -e "${GREEN}🎉 Testing setup verification completed successfully!${NC}"
echo ""
echo "Your testing infrastructure is ready for:"
echo "• Local development testing"
echo "• GitHub Actions CI/CD"
echo "• MVP component validation"
echo ""
echo "Next steps:"
echo "• Push changes to GitHub to test the CI/CD pipeline"
echo "• Add more comprehensive tests as you develop new features"
echo "• Run 'pytest' locally before committing changes"
