#!/bin/bash
# Setup deployment environment variables for Orchestra AI

echo "🔧 Setting up deployment environment variables..."

# Check if variables are already set
if [ -z "$VULTR_API_KEY" ]; then
    echo "⚠️  VULTR_API_KEY not set. Using demo key for testing."
    export VULTR_API_KEY="DEMO-VULTR-API-KEY-REPLACE-WITH-REAL"
fi

if [ -z "$POSTGRES_PASSWORD" ]; then
    echo "🔐 Generating secure PostgreSQL password..."
    export POSTGRES_PASSWORD=$(openssl rand -base64 32)
    echo "PostgreSQL password generated."
fi

if [ -z "$GRAFANA_ADMIN_PASSWORD" ]; then
    echo "🔐 Generating secure Grafana admin password..."
    export GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 16)
    echo "Grafana admin password generated."
fi

# Save to .env file for persistence
cat > .env.deployment << EOF
# Orchestra AI Deployment Environment Variables
# Generated: $(date)
export VULTR_API_KEY="${VULTR_API_KEY}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
export GRAFANA_ADMIN_PASSWORD="${GRAFANA_ADMIN_PASSWORD}"
export PULUMI_ACCESS_TOKEN="${PULUMI_ACCESS_TOKEN}"
EOF

echo "✅ Environment variables configured and saved to .env.deployment"
echo ""
echo "To load these variables in future sessions, run:"
echo "  source .env.deployment"
echo ""
echo "⚠️  IMPORTANT: Replace VULTR_API_KEY with your actual Vultr API key before deployment!"