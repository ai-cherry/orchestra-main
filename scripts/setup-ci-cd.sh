#!/bin/bash

# Orchestra AI CI/CD Setup Script
# Sets up pre-commit hooks and CI/CD dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

log "🚀 Setting up Orchestra AI CI/CD environment..."

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

if [[ "$PYTHON_VERSION" != "$REQUIRED_VERSION" ]]; then
    error "Python $REQUIRED_VERSION is required. Found: Python $PYTHON_VERSION"
    exit 1
fi

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    log "Installing pre-commit..."
    pip install pre-commit
else
    success "pre-commit is already installed"
fi

# Install pre-commit hooks
log "Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type commit-msg

# Install additional linting tools
log "Installing linting and formatting tools..."
pip install -q \
    black==24.2.0 \
    isort==5.13.2 \
    flake8==7.0.0 \
    mypy==1.8.0 \
    bandit==1.7.7 \
    pylint \
    yamllint

# Install Node.js dependencies for frontend linting
if command -v npm &> /dev/null; then
    log "Installing Node.js linting tools..."
    npm install -g \
        eslint@8.56.0 \
        prettier@3.1.0 \
        markdownlint-cli@0.39.0
else
    warning "npm not found. Skipping Node.js linting tools."
fi

# Create necessary configuration files
log "Creating configuration files..."

# Create .yamllint.yml if it doesn't exist
if [[ ! -f .yamllint.yml ]]; then
    cat > .yamllint.yml << 'EOF'
extends: default
rules:
  line-length:
    max: 120
    level: warning
  comments:
    min-spaces-from-content: 1
  truthy:
    allowed-values: ['true', 'false', 'on', 'off']
EOF
    success "Created .yamllint.yml"
fi

# Create .markdownlint.json if it doesn't exist
if [[ ! -f .markdownlint.json ]]; then
    cat > .markdownlint.json << 'EOF'
{
  "default": true,
  "MD013": {
    "line_length": 120,
    "heading_line_length": 120,
    "code_block_line_length": 120
  },
  "MD033": false,
  "MD041": false
}
EOF
    success "Created .markdownlint.json"
fi

# Create .license-header.txt if it doesn't exist
if [[ ! -f .license-header.txt ]]; then
    cat > .license-header.txt << 'EOF'
Orchestra AI - AI-Powered Development Platform
Copyright (c) 2025 Orchestra AI. All rights reserved.
Licensed under the MIT License.
EOF
    success "Created .license-header.txt"
fi

# Create helper scripts directory
mkdir -p scripts

# Create check-todos.sh
cat > scripts/check-todos.sh << 'EOF'
#!/bin/bash
# Check for TODO comments in code
TODO_COUNT=$(grep -r "TODO\|FIXME\|HACK\|XXX" --include="*.py" --include="*.ts" --include="*.tsx" --exclude-dir=node_modules --exclude-dir=venv . | wc -l)
if [[ $TODO_COUNT -gt 0 ]]; then
    echo "Found $TODO_COUNT TODO/FIXME/HACK comments. Please review:"
    grep -r "TODO\|FIXME\|HACK\|XXX" --include="*.py" --include="*.ts" --include="*.tsx" --exclude-dir=node_modules --exclude-dir=venv . | head -10
    exit 0  # Warning only, don't block commit
fi
EOF
chmod +x scripts/check-todos.sh

# Create validate-openapi.sh
cat > scripts/validate-openapi.sh << 'EOF'
#!/bin/bash
# Validate OpenAPI specifications
for file in "$@"; do
    python -c "import yaml, sys; yaml.safe_load(open('$file'))" || exit 1
    echo "✓ $file is valid YAML"
done
EOF
chmod +x scripts/validate-openapi.sh

# Create check-migrations.sh
cat > scripts/check-migrations.sh << 'EOF'
#!/bin/bash
# Check for database migration conflicts
if [[ -d "migrations" ]]; then
    # Check for duplicate migration numbers
    DUPLICATES=$(ls migrations/versions/*.py 2>/dev/null | sed 's/.*\///' | cut -d'_' -f1 | sort | uniq -d)
    if [[ -n "$DUPLICATES" ]]; then
        echo "Error: Duplicate migration numbers found: $DUPLICATES"
        exit 1
    fi
fi
EOF
chmod +x scripts/check-migrations.sh

# Create validate-env.sh
cat > scripts/validate-env.sh << 'EOF'
#!/bin/bash
# Validate environment files
for file in "$@"; do
    # Check for exposed secrets
    if grep -E "(password|secret|key|token).*=.*[A-Za-z0-9]" "$file"; then
        echo "Warning: Possible secret found in $file"
    fi
    
    # Check syntax
    while IFS= read -r line; do
        if [[ -n "$line" && "$line" != \#* ]]; then
            if ! [[ "$line" =~ ^[A-Z_][A-Z0-9_]*=.*$ ]]; then
                echo "Error: Invalid line in $file: $line"
                exit 1
            fi
        fi
    done < "$file"
done
EOF
chmod +x scripts/validate-env.sh

success "Created helper scripts"

# Create GitHub Actions directory structure
mkdir -p .github/workflows

# Run pre-commit on all files (initial run)
log "Running pre-commit checks on all files..."
pre-commit run --all-files || true

# Create secrets baseline for detect-secrets
if command -v detect-secrets &> /dev/null; then
    log "Creating secrets baseline..."
    detect-secrets scan > .secrets.baseline
    success "Created .secrets.baseline"
else
    warning "detect-secrets not installed. Run: pip install detect-secrets"
fi

# Summary
echo
success "🎉 CI/CD setup complete!"
echo
log "Next steps:"
echo "  1. Review and commit the configuration files"
echo "  2. Run 'pre-commit run --all-files' to check all existing files"
echo "  3. Configure GitHub secrets for the workflows:"
echo "     - PULUMI_ACCESS_TOKEN"
echo "     - LAMBDA_LABS_API_KEY"
echo "     - DOCKER_USERNAME / DOCKER_PASSWORD"
echo "     - SLACK_WEBHOOK (optional)"
echo "  4. Push to trigger the CI/CD pipeline"
echo
log "Pre-commit will now run automatically on every commit!" 