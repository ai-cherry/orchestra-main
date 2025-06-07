#!/bin/bash
# Secure Environment Setup Script
# Ensures API keys are protected and environment is properly configured

set -e

echo "🔐 SECURE ENVIRONMENT SETUP"
echo "=========================="

# 1. Ensure .env is in .gitignore
echo "📝 Checking .gitignore..."
if [ ! -f .gitignore ]; then
    echo "Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Environment files
.env
.env.*
!.env.example

# API Keys and Secrets
*.pem
*.key
*.cert
secrets/
credentials/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
*.log
logs/
remediation_log.txt

# Temporary files
*.tmp
*.temp
*.enc
config_export.enc

# Database
*.db
*.sqlite
*.sqlite3

# OS
.DS_Store
Thumbs.db

# Deployment
deployment_validation_report.json
remediation_report.json
EOF
else
    # Ensure .env is in gitignore
    if ! grep -q "^\.env$" .gitignore; then
        echo -e "\n# Environment files\n.env\n.env.*\n!.env.example" >> .gitignore
    fi
fi

echo "✅ .gitignore configured"

# 2. Set proper permissions on .env
if [ -f .env ]; then
    chmod 600 .env
    echo "✅ Set secure permissions on .env (600)"
else
    echo "❌ .env file not found!"
    exit 1
fi

# 3. Generate secure keys if needed
echo ""
echo "🔑 Generating secure keys..."

# Function to generate secure key
generate_key() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
}

# Update .env with generated keys
if grep -q "generate_a_secure_random_key_here" .env; then
    SECRET_KEY=$(generate_key)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/generate_a_secure_random_key_here/$SECRET_KEY/g" .env
    else
        sed -i "s/generate_a_secure_random_key_here/$SECRET_KEY/g" .env
    fi
    echo "✅ Generated SECRET_KEY"
fi

if grep -q "another_secure_random_key_here" .env; then
    JWT_KEY=$(generate_key)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/another_secure_random_key_here/$JWT_KEY/g" .env
    else
        sed -i "s/another_secure_random_key_here/$JWT_KEY/g" .env
    fi
    echo "✅ Generated JWT_SECRET_KEY"
fi

# 4. Validate environment
echo ""
echo "🔍 Validating environment..."

# Check for critical variables
CRITICAL_VARS=(
    "OPENAI_API_KEY"
    "GITHUB_TOKEN"
    "WEAVIATE_URL"
    "WEAVIATE_API_KEY"
)

missing_vars=()
for var in "${CRITICAL_VARS[@]}"; do
    if ! grep -q "^$var=" .env || grep -q "^$var=your_" .env; then
        missing_vars+=($var)
    fi
done

if [ ${#missing_vars[@]} -eq 0 ]; then
    echo "✅ All critical environment variables are set"
else
    echo "⚠️  Missing or placeholder values for:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
fi

# 5. Create backup
BACKUP_FILE=".env.backup.$(date +%Y%m%d_%H%M%S)"
cp .env "$BACKUP_FILE"
echo ""
echo "📋 Created backup: $BACKUP_FILE"

# 6. Security recommendations
echo ""
echo "🛡️  SECURITY RECOMMENDATIONS:"
echo "   1. Never commit .env to version control"
echo "   2. Rotate API keys regularly"
echo "   3. Use different keys for each environment"
echo "   4. Enable 2FA on all service accounts"
echo "   5. Monitor API key usage"

# 7. Next steps
echo ""
echo "📌 NEXT STEPS:"
echo "   1. Update placeholder values in .env"
echo "   2. Run: python3 deployment_ready_check.py"
echo "   3. Deploy: ./deploy_production.sh staging"

echo ""
echo "✅ Environment setup complete!"