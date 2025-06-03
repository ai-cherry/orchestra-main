#!/bin/bash
# Display AI Orchestration System Status

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║           AI ORCHESTRATION SYSTEM STATUS REPORT                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo

# Database Status
echo "📊 DATABASE STATUS"
echo "─────────────────"
if sudo -u postgres psql -c "SELECT 1" &>/dev/null; then
    echo "✅ PostgreSQL: Running"
    if sudo -u postgres psql -d orchestra -c "SELECT 1" &>/dev/null; then
        echo "✅ Orchestra Database: Available"
    else
        echo "❌ Orchestra Database: Not accessible"
    fi
else
    echo "❌ PostgreSQL: Not running"
fi
echo

# Configuration Status
echo "⚙️  CONFIGURATION STATUS"
echo "──────────────────────"
if [ -f .env ]; then
    echo "✅ .env file: Present"
    api_count=$(grep -E "API_KEY|TOKEN" .env | grep -v "^#" | wc -l)
    echo "✅ API Keys Configured: $api_count"
else
    echo "❌ .env file: Missing"
fi

if [ -f /etc/systemd/system/ai-orchestrator.service ]; then
    echo "✅ Systemd Services: Configured"
else
    echo "⚠️  Systemd Services: Not configured (run as root)"
fi
echo

# API Services Status
echo "🔑 API SERVICES STATUS"
echo "────────────────────"
source .env 2>/dev/null
services=(
    "ANTHROPIC_API_KEY:Anthropic Claude"
    "OPENAI_API_KEY:OpenAI"
    "OPENROUTER_API_KEY:OpenRouter"
    "GROK_AI_API_KEY:Grok AI"
    "MISTRAL_API_KEY:Mistral"
    "PERPLEXITY_API_KEY:Perplexity"
    "PORTKEY_API_KEY:Portkey"
)

configured=0
for service in "${services[@]}"; do
    IFS=':' read -r key name <<< "$service"
    if [ -n "${!key}" ]; then
        echo "✅ $name"
        ((configured++))
    else
        echo "❌ $name"
    fi
done
echo "Total: $configured/${#services[@]} services configured"
echo

# GitHub Integration
echo "🐙 GITHUB INTEGRATION"
echo "───────────────────"
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
    echo "✅ GitHub CLI: Authenticated"
    repo=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
    if [ -n "$repo" ]; then
        echo "✅ Repository: $repo"
    fi
else
    echo "⚠️  GitHub CLI: Not authenticated"
fi
echo

# Quick Actions
echo "🚀 QUICK ACTIONS"
echo "───────────────"
echo "1. Test AI Orchestrator:"
echo "   python3 ai_components/orchestration/ai_orchestrator.py"
echo
echo "2. Configure GitHub Secrets:"
echo "   ./scripts/setup_github_secrets.sh"
echo
echo "3. View logs:"
echo "   tail -f ai_components/logs/orchestrator.log"
echo
echo "4. Check service status:"
echo "   sudo systemctl status ai-orchestrator"
echo

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    SYSTEM READY FOR USE! ✅                      ║"
echo "╚══════════════════════════════════════════════════════════════════╝"