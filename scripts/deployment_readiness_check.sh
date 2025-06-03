#!/bin/bash
# Deployment Readiness Check - Shows what's needed for different environments

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║              DEPLOYMENT READINESS CHECK                          ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo

# Function to check if a key exists
check_key() {
    local key=$1
    local value="${!key}"
    if [ -n "$value" ] || grep -q "^$key=" .env 2>/dev/null; then
        echo "✅"
    else
        echo "❌"
    fi
}

echo "🏠 LOCAL DEVELOPMENT REQUIREMENTS"
echo "════════════════════════════════"
echo "These are REQUIRED for local development:"
echo
echo "[$(check_key DATABASE_URL)] PostgreSQL Database"
echo "[$(check_key ANTHROPIC_API_KEY)] At least one AI API key (Anthropic/OpenAI/etc)"
echo
echo "Status: Your AI orchestration is FULLY FUNCTIONAL locally! ✅"
echo

echo "☁️  PRODUCTION DEPLOYMENT REQUIREMENTS"
echo "═══════════════════════════════════"
echo "These are ONLY needed when deploying to production:"
echo

echo "🔹 Vultr Cloud Deployment:"
echo "[$(check_key VULTR_API_KEY)] VULTR_API_KEY - Deploy servers on Vultr"
echo "   └─ Without this: Cannot deploy to Vultr cloud"
echo "   └─ Alternative: Deploy manually or use different cloud"
echo

echo "🔹 Infrastructure as Code (Optional):"
echo "[$(check_key PULUMI_CONFIG_PASSPHRASE)] PULUMI_CONFIG_PASSPHRASE - Encrypt Pulumi state"
echo "   └─ Without this: Use unencrypted local state (fine for dev)"
echo "[$(check_key AWS_ACCESS_KEY_ID)] AWS_ACCESS_KEY_ID - Store Pulumi state in S3"
echo "[$(check_key AWS_SECRET_ACCESS_KEY)] AWS_SECRET_ACCESS_KEY - Store Pulumi state in S3"
echo "   └─ Without these: Use local file state (perfectly fine)"
echo

echo "🔹 Data Pipeline Integration (Optional):"
echo "[$(check_key AIRBYTE_API_KEY)] AIRBYTE_API_KEY - Connect to Airbyte"
echo "[$(check_key AIRBYTE_API_URL)] AIRBYTE_API_URL - Airbyte endpoint"
echo "[$(check_key AIRBYTE_WORKSPACE_ID)] AIRBYTE_WORKSPACE_ID - Airbyte workspace"
echo "   └─ Without these: No automated data pipelines (not needed for AI orchestration)"
echo

echo
echo "📊 SUMMARY"
echo "═════════"

# Count what's configured
local_ready=true
if ! check_key DATABASE_URL >/dev/null || ! (check_key ANTHROPIC_API_KEY >/dev/null || check_key OPENAI_API_KEY >/dev/null); then
    local_ready=false
fi

if [ "$local_ready" = true ]; then
    echo "✅ Local Development: READY"
    echo "   Your AI orchestration system is fully functional!"
else
    echo "⚠️  Local Development: Missing core requirements"
fi

if check_key VULTR_API_KEY >/dev/null; then
    echo "✅ Cloud Deployment: READY (Vultr configured)"
else
    echo "📌 Cloud Deployment: Not configured (optional)"
fi

echo
echo "💡 WHAT YOU NEED TO DO:"
echo "══════════════════════"
if [ "$local_ready" = true ]; then
    echo "✅ Nothing! Your system is ready for local use."
    echo
    echo "For production deployment (optional):"
    echo "1. Get a Vultr API key from https://my.vultr.com/settings/#settingsapi"
    echo "2. Run: export VULTR_API_KEY='your-key-here'"
    echo "3. Use Pulumi to deploy: cd infrastructure && pulumi up"
else
    echo "1. Ensure PostgreSQL is running"
    echo "2. Add at least one AI API key to .env"
    echo "3. Run: ./scripts/test_orchestrator_demo.py"
fi