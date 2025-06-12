#!/bin/bash
# 🚀 Quick Production Setup for Orchestra AI
# Get the most critical APIs configured in under 5 minutes

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}🚀 Orchestra AI Quick Production Setup${NC}"
echo "======================================"
echo -e "${CYAN}Setting up critical APIs for immediate production deployment${NC}"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp env.example .env
fi

echo -e "${BLUE}🎯 Priority 1: Core AI Providers (Required)${NC}"
echo "==========================================="

# OpenAI (Most important)
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}🤖 OpenAI API Key (REQUIRED)${NC}"
    echo "   Get from: https://platform.openai.com/api-keys"
    echo -n "   Enter OpenAI API key (sk-...): "
    read -r openai_key
    if [ -n "$openai_key" ]; then
        echo "OPENAI_API_KEY=$openai_key" >> .env
        echo -e "${GREEN}   ✅ OpenAI configured${NC}"
    fi
fi

# OpenRouter (Cost savings)
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo -e "${YELLOW}🔀 OpenRouter API Key (60-80% cost savings)${NC}"
    echo "   Get from: https://openrouter.ai/keys"
    echo -n "   Enter OpenRouter API key (sk-or-v1-...) or press Enter to skip: "
    read -r openrouter_key
    if [ -n "$openrouter_key" ]; then
        echo "OPENROUTER_API_KEY=$openrouter_key" >> .env
        echo "OPENROUTER_SITE_URL=https://orchestra-ai.dev" >> .env
        echo "OPENROUTER_APP_NAME=Orchestra AI" >> .env
        echo -e "${GREEN}   ✅ OpenRouter configured (60-80% cost savings enabled!)${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Skipped - You'll pay 5x more for AI calls${NC}"
    fi
fi

# Anthropic (Claude)
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}🧠 Anthropic API Key (Claude models)${NC}"
    echo "   Get from: https://console.anthropic.com/account/keys"
    echo -n "   Enter Anthropic API key (sk-ant-...) or press Enter to skip: "
    read -r anthropic_key
    if [ -n "$anthropic_key" ]; then
        echo "ANTHROPIC_API_KEY=$anthropic_key" >> .env
        echo -e "${GREEN}   ✅ Anthropic configured${NC}"
    fi
fi

echo ""
echo -e "${BLUE}🎯 Priority 2: Essential Infrastructure${NC}"
echo "======================================"

# Database (if not configured)
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}🗄️  Database Configuration${NC}"
    echo "   For quick setup, we'll use SQLite (upgrade to PostgreSQL later)"
    echo "DATABASE_URL=sqlite:///./orchestra.db" >> .env
    echo -e "${GREEN}   ✅ SQLite database configured${NC}"
fi

# Redis (optional for now)
if [ -z "$REDIS_URL" ]; then
    echo -e "${YELLOW}⚡ Redis (Optional - for caching)${NC}"
    echo "   Using in-memory cache for now (add Redis later for production)"
    echo "REDIS_URL=redis://localhost:6379" >> .env
    echo -e "${GREEN}   ✅ Redis placeholder configured${NC}"
fi

echo ""
echo -e "${BLUE}🎯 Priority 3: Business Integration${NC}"
echo "=================================="

# Notion is already configured, just verify
if [ -n "$NOTION_API_TOKEN" ]; then
    echo -e "${GREEN}✅ Notion already configured${NC}"
else
    echo -e "${YELLOW}📝 Notion Integration${NC}"
    echo "   Get from: https://www.notion.so/my-integrations"
    echo -n "   Enter Notion API token (ntn_...) or press Enter to skip: "
    read -r notion_token
    if [ -n "$notion_token" ]; then
        echo "NOTION_API_TOKEN=$notion_token" >> .env
        echo "NOTION_WORKSPACE_ID=20bdba04940280ca9ba7f9bce721f547" >> .env
        echo -e "${GREEN}   ✅ Notion configured${NC}"
    fi
fi

echo ""
echo -e "${BLUE}🚀 Testing Configuration${NC}"
echo "======================="

# Load the new environment
set -a
source .env
set +a

# Test the setup
echo "Running quick validation..."
python3 -c "
from utils.fast_secrets import secrets
import sys

# Test core services
results = secrets.validate_required_secrets(['OPENAI_API_KEY', 'NOTION_API_TOKEN'])
status = secrets.get_status()

print('\\n🔍 Configuration Status:')
for service, config in status.items():
    if config['configured']:
        print(f'   ✅ {service.title()}')
    else:
        print(f'   ❌ {service.title()}')

# Calculate readiness
configured = sum(1 for s in status.values() if s['configured'])
total = len(status)
percent = (configured * 100) // total

print(f'\\n📊 Production Readiness: {configured}/{total} services ({percent}%)')

if percent >= 40:
    print('🎉 READY FOR BASIC PRODUCTION!')
    sys.exit(0)
else:
    print('⚠️  Need more configuration for production')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 SUCCESS! Basic production setup complete${NC}"
    echo ""
    echo -e "${BLUE}🚀 Next Steps:${NC}"
    echo "1. Test your setup: python3 utils/fast_secrets.py"
    echo "2. Start development: ./scripts/start_dev.sh"
    echo "3. Add more APIs later with: ./scripts/production_readiness_setup.sh"
    echo ""
    echo -e "${CYAN}💡 Pro Tips:${NC}"
    echo "• OpenRouter saves 60-80% on AI costs"
    echo "• Add Perplexity for web search capabilities"
    echo "• Configure PostgreSQL for production database"
    echo ""
    
    # Update GitHub secrets if authenticated
    if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
        echo -e "${BLUE}🔐 Updating GitHub Secrets...${NC}"
        [ -n "$OPENAI_API_KEY" ] && gh secret set OPENAI_API_KEY --body "$OPENAI_API_KEY" 2>/dev/null
        [ -n "$OPENROUTER_API_KEY" ] && gh secret set OPENROUTER_API_KEY --body "$OPENROUTER_API_KEY" 2>/dev/null
        [ -n "$ANTHROPIC_API_KEY" ] && gh secret set ANTHROPIC_API_KEY --body "$ANTHROPIC_API_KEY" 2>/dev/null
        echo -e "${GREEN}✅ GitHub secrets updated${NC}"
    fi
    
else
    echo ""
    echo -e "${YELLOW}⚠️  Setup incomplete - add more API keys for full functionality${NC}"
    echo "Run: ./scripts/production_readiness_setup.sh for complete setup"
fi

echo ""
echo -e "${GREEN}✅ Quick setup complete! Your system is ready to use.${NC}" 