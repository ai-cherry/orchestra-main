#!/bin/bash
# setup_locked_env.sh - One-time setup for locked development environment
# This script ensures EXACT versions of all tools

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load version requirements
source .versions.lock

echo -e "${GREEN}🔒 cherry_ai Locked Environment Setup${NC}"
echo "======================================"

# Check Python version
echo -e "\n${YELLOW}Checking Python version...${NC}"
CURRENT_PYTHON=$(python3 --version 2>&1 | cut -d' ' -f2)
if [[ "$CURRENT_PYTHON" != "$PYTHON_VERSION" ]]; then
    echo -e "${RED}ERROR: Python $PYTHON_VERSION required, found $CURRENT_PYTHON${NC}"
    echo "Please install Python $PYTHON_VERSION using:"
    echo "  - pyenv: pyenv install $PYTHON_VERSION && pyenv local $PYTHON_VERSION"
    echo "  - apt: sudo apt install python3.10=3.10.12-1~20.04"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Create virtual environment
echo -e "\n${YELLOW}Creating virtual environment...${NC}"
if [ -d "venv" ]; then
    echo "Removing existing venv..."
    rm -rf venv
fi
python3.10 -m venv venv --prompt cherry_ai
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment created${NC}"

# Upgrade pip to specific version
echo -e "\n${YELLOW}Installing pip tools...${NC}"
pip install --no-cache-dir pip==24.0 setuptools==69.0.3 wheel==0.42.0
echo -e "${GREEN}✓ Pip tools installed${NC}"

# Install Python dependencies
echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
if [ -f "requirements/base.txt" ]; then
    pip install --no-cache-dir -r requirements/base.txt
else
    # Create base requirements if missing
    cat > requirements/base.txt << EOF
# Auto-generated base requirements - $(date)
fastapi==$FASTAPI_VERSION
pydantic==$PYDANTIC_VERSION
sqlalchemy==$SQLALCHEMY_VERSION
google-cloud-aiplatform==1.93.1
google-cloud-firestore==2.20.2
google-cloud-storage==2.19.0
litellm==$LITELLM_VERSION
redis==5.0.1
httpx==0.28.1
uvicorn==0.29.0
phidata==2.7.10
python-dotenv==1.1.0
EOF
    pip install --no-cache-dir -r requirements/base.txt
fi

if [ -f "requirements/dev.txt" ]; then
    pip install --no-cache-dir -r requirements/dev.txt
else
    # Create dev requirements if missing
    cat > requirements/dev.txt << EOF
# Auto-generated dev requirements - $(date)
pytest==$PYTEST_VERSION
black==$BLACK_VERSION
mypy==$MYPY_VERSION
flake8==$FLAKE8_VERSION
pre-commit==$PRECOMMIT_VERSION
types-PyYAML==6.0.12.20250516
EOF
    pip install --no-cache-dir -r requirements/dev.txt
fi
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Install Pulumi (if not exists or wrong version)
echo -e "\n${YELLOW}Checking Pulumi...${NC}"
if command -v pulumi &> /dev/null; then
    CURRENT_PULUMI=$(pulumi version 2>/dev/null | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' | sed 's/v//')
    if [[ "$CURRENT_PULUMI" != "$PULUMI_VERSION" ]]; then
        echo "Wrong Pulumi version ($CURRENT_PULUMI), installing $PULUMI_VERSION..."
        curl -fsSL https://get.pulumi.com | sh -s -- --version $PULUMI_VERSION
    else
        echo -e "${GREEN}✓ Pulumi $PULUMI_VERSION already installed${NC}"
    fi
else
    echo "Installing Pulumi $PULUMI_VERSION..."
    curl -fsSL https://get.pulumi.com | sh -s -- --version $PULUMI_VERSION
fi

# Install gcloud (if not exists or wrong version)
echo -e "\n${YELLOW}Checking gcloud...${NC}"
if command -v gcloud &> /dev/null; then
    CURRENT_GCLOUD=$(gcloud version 2>/dev/null | grep 'Vultr SDK' | awk '{print $4}')
    if [[ "$CURRENT_GCLOUD" != "$GCLOUD_VERSION" ]]; then
        echo "Wrong gcloud version ($CURRENT_GCLOUD), please install $GCLOUD_VERSION manually"
    else
        echo -e "${GREEN}✓ gcloud $GCLOUD_VERSION already installed${NC}"
    fi
else
    echo "gcloud not found. Install with:"
    echo "  curl https://sdk.cloud.google.com | bash -s -- --version=$GCLOUD_VERSION"
fi

# Create version check script
echo -e "\n${YELLOW}Creating version check script...${NC}"
cat > check_versions.sh << 'EOF'
#!/bin/bash
# check_versions.sh - Verify all tool versions

source .versions.lock

echo "🔍 Version Check Report"
echo "======================"

# Check Python
CURRENT_PYTHON=$(python --version 2>&1 | cut -d' ' -f2)
if [[ "$CURRENT_PYTHON" == "$PYTHON_VERSION" ]]; then
    echo "✅ Python: $CURRENT_PYTHON"
else
    echo "❌ Python: $CURRENT_PYTHON (expected $PYTHON_VERSION)"
fi

# Check key packages
for pkg in fastapi pydantic sqlalchemy litellm; do
    version=$(pip show $pkg 2>/dev/null | grep Version | cut -d' ' -f2)
    echo "📦 $pkg: $version"
done

# Check tools
if command -v pulumi &> /dev/null; then
    echo "🔧 Pulumi: $(pulumi version 2>/dev/null | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' || echo 'unknown')"
fi

if command -v docker &> /dev/null; then
    echo "🐳 Docker: $(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
fi

if command -v gcloud &> /dev/null; then
    echo "☁️  gcloud: $(gcloud version 2>/dev/null | grep 'Vultr SDK' | awk '{print $4}')"
fi
EOF
chmod +x check_versions.sh

# Create daily startup script
echo -e "\n${YELLOW}Creating startup script...${NC}"
cat > start_dev.sh << 'EOF'
#!/bin/bash
# start_dev.sh - Daily development startup

source .versions.lock

# Activate venv
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ No venv found! Run ./setup_locked_env.sh first"
    exit 1
fi

# Verify Python version
CURRENT_PYTHON=$(python --version 2>&1 | cut -d' ' -f2)
if [[ "$CURRENT_PYTHON" != "$PYTHON_VERSION" ]]; then
    echo "⚠️  Wrong Python version! Expected $PYTHON_VERSION, got $CURRENT_PYTHON"
fi

# Set environment variables
export PYTHONDONTWRITEBYTECODE=1
export PULUMI_SKIP_UPDATE_CHECK=1
export CLOUDSDK_CORE_DISABLE_PROMPTS=1
export DOCKER_BUILDKIT=1

# Disable all auto-updates
export HOMEBREW_NO_AUTO_UPDATE=1
export COMPOSE_DOCKER_CLI_BUILD=1

echo "✅ Development environment ready"
echo "📌 Python: $CURRENT_PYTHON"
echo "📌 Venv: $VIRTUAL_ENV"
echo ""
echo "Run ./check_versions.sh to verify all tools"
EOF
chmod +x start_dev.sh

# Final summary
echo -e "\n${GREEN}✅ Setup Complete!${NC}"
echo "=================="
echo "Next steps:"
echo "1. Run: source venv/bin/activate"
echo "2. Run: ./check_versions.sh"
echo "3. For daily work: ./start_dev.sh"
echo ""
echo "Version lock file: .versions.lock"
echo "DO NOT update any versions without team approval!"
