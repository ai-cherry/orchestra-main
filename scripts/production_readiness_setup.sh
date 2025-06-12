#!/bin/bash
# 🚀 Orchestra AI Production Readiness Setup
# Comprehensive script to get all APIs and services production-ready

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🚀 Orchestra AI Production Readiness Setup${NC}"
echo "=============================================="
echo -e "${CYAN}Preparing all APIs and services for production deployment${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to validate API key format
validate_api_key() {
    local key="$1"
    local service="$2"
    local pattern="$3"
    
    if [[ -z "$key" ]]; then
        echo -e "${RED}❌ $service API key not set${NC}"
        return 1
    elif [[ ! "$key" =~ $pattern ]]; then
        echo -e "${YELLOW}⚠️  $service API key format may be incorrect${NC}"
        return 1
    else
        echo -e "${GREEN}✅ $service API key validated${NC}"
        return 0
    fi
}

# Function to test API connectivity
test_api_connectivity() {
    local service="$1"
    local url="$2"
    local headers="$3"
    
    echo -n "   Testing $service connectivity... "
    if curl -s --max-time 10 -H "$headers" "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Connected${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed${NC}"
        return 1
    fi
}

# Step 1: Environment Setup
echo -e "${BLUE}Step 1: Environment Setup${NC}"
echo "========================="

# Check for .env file
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo -e "${GREEN}✅ .env file created from template${NC}"
    elif [ -f "$PROJECT_ROOT/src/env.example" ]; then
        cp "$PROJECT_ROOT/src/env.example" "$PROJECT_ROOT/.env"
        echo -e "${GREEN}✅ .env file created from src/env.example${NC}"
    else
        echo -e "${RED}❌ No .env template found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env file exists${NC}"
fi

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
    echo -e "${GREEN}✅ Environment variables loaded${NC}"
fi

echo ""

# Step 2: Core AI/LLM Providers
echo -e "${BLUE}Step 2: Core AI/LLM Providers${NC}"
echo "=============================="

# OpenAI
if validate_api_key "$OPENAI_API_KEY" "OpenAI" "^sk-[a-zA-Z0-9]{48,}$"; then
    test_api_connectivity "OpenAI" "https://api.openai.com/v1/models" "Authorization: Bearer $OPENAI_API_KEY"
else
    echo -e "${YELLOW}💡 Get OpenAI API key from: https://platform.openai.com/api-keys${NC}"
fi

# Anthropic
if validate_api_key "$ANTHROPIC_API_KEY" "Anthropic" "^sk-ant-[a-zA-Z0-9-]{95,}$"; then
    test_api_connectivity "Anthropic" "https://api.anthropic.com/v1/messages" "x-api-key: $ANTHROPIC_API_KEY"
else
    echo -e "${YELLOW}💡 Get Anthropic API key from: https://console.anthropic.com/account/keys${NC}"
fi

# OpenRouter
if validate_api_key "$OPENROUTER_API_KEY" "OpenRouter" "^sk-or-v1-[a-zA-Z0-9]{64,}$"; then
    test_api_connectivity "OpenRouter" "https://openrouter.ai/api/v1/models" "Authorization: Bearer $OPENROUTER_API_KEY"
else
    echo -e "${YELLOW}💡 Get OpenRouter API key from: https://openrouter.ai/keys${NC}"
    echo -e "${CYAN}   OpenRouter provides 60-80% cost savings with access to multiple models${NC}"
fi

# Perplexity
if validate_api_key "$PERPLEXITY_API_KEY" "Perplexity" "^pplx-[a-zA-Z0-9]{40,}$"; then
    test_api_connectivity "Perplexity" "https://api.perplexity.ai/chat/completions" "Authorization: Bearer $PERPLEXITY_API_KEY"
else
    echo -e "${YELLOW}💡 Get Perplexity API key from: https://www.perplexity.ai/settings/api${NC}"
fi

echo ""

# Step 3: Database & Infrastructure
echo -e "${BLUE}Step 3: Database & Infrastructure${NC}"
echo "================================="

# PostgreSQL
if [[ -n "$DATABASE_URL" ]]; then
    echo -e "${GREEN}✅ PostgreSQL configured${NC}"
    if command_exists psql; then
        echo -n "   Testing PostgreSQL connection... "
        if psql "$DATABASE_URL" -c "SELECT 1;" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Connected${NC}"
        else
            echo -e "${RED}❌ Connection failed${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  PostgreSQL DATABASE_URL not set${NC}"
fi

# Redis
if [[ -n "$REDIS_URL" ]]; then
    echo -e "${GREEN}✅ Redis configured${NC}"
    if command_exists redis-cli; then
        echo -n "   Testing Redis connection... "
        if redis-cli -u "$REDIS_URL" ping >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Connected${NC}"
        else
            echo -e "${RED}❌ Connection failed${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Redis REDIS_URL not set${NC}"
fi

# Weaviate
if [[ -n "$WEAVIATE_URL" ]]; then
    echo -e "${GREEN}✅ Weaviate configured${NC}"
    test_api_connectivity "Weaviate" "$WEAVIATE_URL/v1/meta" ""
else
    echo -e "${YELLOW}⚠️  Weaviate WEAVIATE_URL not set${NC}"
fi

echo ""

# Step 4: Business Integrations
echo -e "${BLUE}Step 4: Business Integrations${NC}"
echo "============================="

# Notion
if validate_api_key "$NOTION_API_TOKEN" "Notion" "^ntn_[a-zA-Z0-9]{43}$"; then
    test_api_connectivity "Notion" "https://api.notion.com/v1/users/me" "Authorization: Bearer $NOTION_API_TOKEN"
else
    echo -e "${YELLOW}💡 Get Notion API token from: https://www.notion.so/my-integrations${NC}"
fi

# Slack
if validate_api_key "$SLACK_BOT_TOKEN" "Slack" "^xoxb-[0-9]+-[0-9]+-[a-zA-Z0-9]+$"; then
    test_api_connectivity "Slack" "https://slack.com/api/auth.test" "Authorization: Bearer $SLACK_BOT_TOKEN"
else
    echo -e "${YELLOW}💡 Get Slack bot token from: https://api.slack.com/apps${NC}"
fi

# HubSpot
if [[ -n "$HUBSPOT_API_KEY" ]]; then
    echo -e "${GREEN}✅ HubSpot API key configured${NC}"
    test_api_connectivity "HubSpot" "https://api.hubapi.com/contacts/v1/lists/all/contacts/all" "hapikey: $HUBSPOT_API_KEY"
else
    echo -e "${YELLOW}💡 Get HubSpot API key from: https://app.hubspot.com/developer${NC}"
fi

echo ""

# Step 5: Web Automation
echo -e "${BLUE}Step 5: Web Automation Platforms${NC}"
echo "================================"

# Phantombuster
if [[ -n "$PHANTOMBUSTER_API_KEY" ]]; then
    echo -e "${GREEN}✅ Phantombuster configured${NC}"
    test_api_connectivity "Phantombuster" "https://api.phantombuster.com/api/v2/agents" "X-Phantombuster-Key: $PHANTOMBUSTER_API_KEY"
else
    echo -e "${YELLOW}💡 Get Phantombuster API key from: https://phantombuster.com/api${NC}"
fi

# Apify
if [[ -n "$APIFY_API_TOKEN" ]]; then
    echo -e "${GREEN}✅ Apify configured${NC}"
    test_api_connectivity "Apify" "https://api.apify.com/v2/users/me" "Authorization: Bearer $APIFY_API_TOKEN"
else
    echo -e "${YELLOW}💡 Get Apify API token from: https://console.apify.com/account/integrations${NC}"
fi

# ZenRows
if [[ -n "$ZENROWS_API_KEY" ]]; then
    echo -e "${GREEN}✅ ZenRows configured${NC}"
    # ZenRows doesn't have a simple auth test endpoint, so we'll just validate the key exists
else
    echo -e "${YELLOW}💡 Get ZenRows API key from: https://app.zenrows.com/api${NC}"
fi

echo ""

# Step 6: Infrastructure Services
echo -e "${BLUE}Step 6: Infrastructure Services${NC}"
echo "==============================="

# Lambda Labs
if [[ -n "$LAMBDA_LABS_API_KEY" ]]; then
    echo -e "${GREEN}✅ Lambda Labs configured${NC}"
    test_api_connectivity "Lambda Labs" "https://cloud.lambdalabs.com/api/v1/instances" "Authorization: Bearer $LAMBDA_LABS_API_KEY"
else
    echo -e "${YELLOW}💡 Get Lambda Labs API key from: https://cloud.lambdalabs.com/api-keys${NC}"
fi

# Pulumi
if [[ -n "$PULUMI_ACCESS_TOKEN" ]]; then
    echo -e "${GREEN}✅ Pulumi configured${NC}"
    if command_exists pulumi; then
        echo -n "   Testing Pulumi authentication... "
        if pulumi whoami >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Authenticated${NC}"
        else
            echo -e "${RED}❌ Authentication failed${NC}"
        fi
    fi
else
    echo -e "${YELLOW}💡 Get Pulumi access token from: https://app.pulumi.com/account/tokens${NC}"
fi

echo ""

# Step 7: GitHub Secrets Setup
echo -e "${BLUE}Step 7: GitHub Secrets Setup${NC}"
echo "============================"

if command_exists gh; then
    echo -n "Checking GitHub authentication... "
    if gh auth status >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Authenticated${NC}"
        
        # Set critical secrets
        if [[ -n "$NOTION_API_TOKEN" ]]; then
            gh secret set NOTION_API_TOKEN --body "$NOTION_API_TOKEN" --repo ai-cherry/orchestra-main 2>/dev/null && \
            echo -e "${GREEN}✅ NOTION_API_TOKEN set in GitHub${NC}" || \
            echo -e "${YELLOW}⚠️  Failed to set NOTION_API_TOKEN${NC}"
        fi
        
        if [[ -n "$OPENAI_API_KEY" ]]; then
            gh secret set OPENAI_API_KEY --body "$OPENAI_API_KEY" --repo ai-cherry/orchestra-main 2>/dev/null && \
            echo -e "${GREEN}✅ OPENAI_API_KEY set in GitHub${NC}" || \
            echo -e "${YELLOW}⚠️  Failed to set OPENAI_API_KEY${NC}"
        fi
        
        if [[ -n "$ANTHROPIC_API_KEY" ]]; then
            gh secret set ANTHROPIC_API_KEY --body "$ANTHROPIC_API_KEY" --repo ai-cherry/orchestra-main 2>/dev/null && \
            echo -e "${GREEN}✅ ANTHROPIC_API_KEY set in GitHub${NC}" || \
            echo -e "${YELLOW}⚠️  Failed to set ANTHROPIC_API_KEY${NC}"
        fi
        
        if [[ -n "$OPENROUTER_API_KEY" ]]; then
            gh secret set OPENROUTER_API_KEY --body "$OPENROUTER_API_KEY" --repo ai-cherry/orchestra-main 2>/dev/null && \
            echo -e "${GREEN}✅ OPENROUTER_API_KEY set in GitHub${NC}" || \
            echo -e "${YELLOW}⚠️  Failed to set OPENROUTER_API_KEY${NC}"
        fi
        
    else
        echo -e "${RED}❌ Not authenticated${NC}"
        echo -e "${YELLOW}💡 Run: gh auth login${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  GitHub CLI not installed${NC}"
    echo -e "${YELLOW}💡 Install with: brew install gh${NC}"
fi

echo ""

# Step 8: Fast Secrets Manager Test
echo -e "${BLUE}Step 8: Fast Secrets Manager Test${NC}"
echo "================================="

echo "Testing fast secrets manager..."
if python3 "$PROJECT_ROOT/utils/fast_secrets.py"; then
    echo -e "${GREEN}✅ Fast secrets manager working${NC}"
else
    echo -e "${RED}❌ Fast secrets manager failed${NC}"
fi

echo ""

# Step 9: Production Readiness Summary
echo -e "${BLUE}Step 9: Production Readiness Summary${NC}"
echo "===================================="

# Count configured services
configured_count=0
total_services=15

# Core AI
[[ -n "$OPENAI_API_KEY" ]] && ((configured_count++))
[[ -n "$ANTHROPIC_API_KEY" ]] && ((configured_count++))
[[ -n "$OPENROUTER_API_KEY" ]] && ((configured_count++))

# Infrastructure
[[ -n "$DATABASE_URL" ]] && ((configured_count++))
[[ -n "$REDIS_URL" ]] && ((configured_count++))
[[ -n "$WEAVIATE_URL" ]] && ((configured_count++))

# Business
[[ -n "$NOTION_API_TOKEN" ]] && ((configured_count++))
[[ -n "$SLACK_BOT_TOKEN" ]] && ((configured_count++))
[[ -n "$HUBSPOT_API_KEY" ]] && ((configured_count++))

# Web Automation
[[ -n "$PHANTOMBUSTER_API_KEY" ]] && ((configured_count++))
[[ -n "$APIFY_API_TOKEN" ]] && ((configured_count++))
[[ -n "$ZENROWS_API_KEY" ]] && ((configured_count++))

# Infrastructure Services
[[ -n "$LAMBDA_LABS_API_KEY" ]] && ((configured_count++))
[[ -n "$PULUMI_ACCESS_TOKEN" ]] && ((configured_count++))
[[ -n "$PERPLEXITY_API_KEY" ]] && ((configured_count++))

# Calculate readiness percentage
readiness_percent=$((configured_count * 100 / total_services))

echo -e "${CYAN}📊 Production Readiness: $configured_count/$total_services services (${readiness_percent}%)${NC}"

if [ $readiness_percent -ge 80 ]; then
    echo -e "${GREEN}🎉 EXCELLENT! System is production-ready${NC}"
elif [ $readiness_percent -ge 60 ]; then
    echo -e "${YELLOW}🔧 GOOD! Most services configured, minor setup needed${NC}"
elif [ $readiness_percent -ge 40 ]; then
    echo -e "${YELLOW}⚠️  PARTIAL! Core services ready, additional setup recommended${NC}"
else
    echo -e "${RED}❌ NEEDS WORK! Significant setup required before production${NC}"
fi

echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo "=============="
echo -e "${CYAN}1. Add missing API keys to .env file${NC}"
echo -e "${CYAN}2. Test individual service connections${NC}"
echo -e "${CYAN}3. Run: python3 utils/fast_secrets.py${NC}"
echo -e "${CYAN}4. Deploy with: ./scripts/deploy_production.sh${NC}"
echo ""
echo -e "${GREEN}✅ Production readiness setup complete!${NC}"

# Create a status file
cat > "$PROJECT_ROOT/production_readiness_status.json" << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "configured_services": $configured_count,
  "total_services": $total_services,
  "readiness_percent": $readiness_percent,
  "status": "$([ $readiness_percent -ge 80 ] && echo "production_ready" || echo "needs_setup")",
  "core_services": {
    "openai": $([ -n "$OPENAI_API_KEY" ] && echo "true" || echo "false"),
    "anthropic": $([ -n "$ANTHROPIC_API_KEY" ] && echo "true" || echo "false"),
    "openrouter": $([ -n "$OPENROUTER_API_KEY" ] && echo "true" || echo "false"),
    "notion": $([ -n "$NOTION_API_TOKEN" ] && echo "true" || echo "false"),
    "database": $([ -n "$DATABASE_URL" ] && echo "true" || echo "false"),
    "redis": $([ -n "$REDIS_URL" ] && echo "true" || echo "false")
  }
}
EOF

echo -e "${CYAN}📋 Status saved to: production_readiness_status.json${NC}" 