#!/bin/bash

# Pay Ready CEO Business Intelligence Setup
# Quick setup for CEO dashboard with Zapier + Direct API integration

set -e

echo "🚀 Setting up Pay Ready CEO Business Intelligence..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check environment variable
check_env_var() {
    local var_name=$1
    local friendly_name=$2
    
    if [ -z "${!var_name}" ]; then
        echo -e "${RED}❌ Missing: $friendly_name ($var_name)${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Found: $friendly_name${NC}"
        return 0
    fi
}

echo -e "${BLUE}📋 Checking Prerequisites...${NC}"
echo ""

# Check required tools
TOOLS_OK=true

if ! command_exists "node"; then
    echo -e "${RED}❌ Node.js not found${NC}"
    TOOLS_OK=false
else
    echo -e "${GREEN}✅ Node.js found${NC}"
fi

if ! command_exists "python3"; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    TOOLS_OK=false
else
    echo -e "${GREEN}✅ Python 3 found${NC}"
fi

if [ "$TOOLS_OK" = false ]; then
    echo -e "${RED}Please install missing tools before continuing.${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}🔑 Checking API Keys...${NC}"
echo ""

# Load environment if .env exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check required API keys
ENV_OK=true

check_env_var "GONG_API_KEY" "Gong.io API Key" || ENV_OK=false
check_env_var "SALESFORCE_CLIENT_ID" "Salesforce Client ID" || ENV_OK=false
check_env_var "HUBSPOT_API_KEY" "HubSpot API Key" || ENV_OK=false
check_env_var "SLACK_BOT_TOKEN" "Slack Bot Token" || ENV_OK=false
check_env_var "LINEAR_API_KEY" "Linear API Key" || ENV_OK=false
check_env_var "OPENAI_API_KEY" "OpenAI API Key" || ENV_OK=false

if [ "$ENV_OK" = false ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Some API keys are missing. You can:${NC}"
    echo "   1. Add them to your .env file"
    echo "   2. Set them as environment variables"
    echo "   3. Continue setup and add them later"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}🔧 Setting up Zapier MCP Server...${NC}"
echo ""

# Navigate to zapier-mcp directory
cd zapier-mcp

# Install dependencies if not already installed
if [ ! -d "node_modules" ]; then
    echo "Installing Zapier MCP dependencies..."
    npm install
fi

# Copy environment config if not exists
if [ ! -f ".env" ]; then
    echo "Creating Zapier MCP environment config..."
    cp environment.config .env
    echo -e "${YELLOW}📝 Please update zapier-mcp/.env with your API keys${NC}"
fi

# Start Zapier MCP server in background
echo "Starting Zapier MCP server..."
if ! pgrep -f "zapier-mcp" > /dev/null; then
    npm run start &
    ZAPIER_PID=$!
    echo -e "${GREEN}✅ Zapier MCP server started (PID: $ZAPIER_PID)${NC}"
    sleep 3
    
    # Test the server
    if curl -s http://localhost:80/health > /dev/null; then
        echo -e "${GREEN}✅ Zapier MCP server is responding${NC}"
    else
        echo -e "${RED}❌ Zapier MCP server not responding${NC}"
    fi
else
    echo -e "${GREEN}✅ Zapier MCP server already running${NC}"
fi

cd ..

echo ""
echo -e "${BLUE}🧠 Setting up Sophia AI for CEO Analysis...${NC}"
echo ""

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Create CEO analysis test script
cat > test_ceo_analysis.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for CEO business intelligence analysis
"""
import asyncio
import json
from services.pay_ready.gong_ceo_analyzer import analyze_for_ceo_dashboard

async def test_ceo_analysis():
    """Test the CEO analysis functionality"""
    print("🧪 Testing CEO analysis with Gong data...")
    
    try:
        # Analyze last 7 days
        results = await analyze_for_ceo_dashboard(days_back=7)
        
        print(f"📊 Analysis Results:")
        print(f"   • Calls analyzed: {results['total_calls_analyzed']}")
        print(f"   • Coaching insights: {len(results['sales_coaching_insights'])}")
        print(f"   • Competitive mentions: {len(results['competitive_intelligence'])}")
        print(f"   • Client health signals: {len(results['client_health_signals'])}")
        
        # Save results to file
        with open('ceo_analysis_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"✅ Results saved to ceo_analysis_results.json")
        
        # Print executive summary
        if results.get('executive_summary'):
            print(f"\n📋 Executive Summary:")
            print(f"{results['executive_summary']}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_ceo_analysis())
EOF

chmod +x test_ceo_analysis.py

echo ""
echo -e "${BLUE}📊 Creating CEO Dashboard Configuration...${NC}"
echo ""

# Create CEO dashboard config
mkdir -p config/ceo_dashboard

cat > config/ceo_dashboard/dashboard_config.json << EOF
{
  "ceo_dashboard": {
    "refresh_interval_hours": 6,
    "email_reports": {
      "enabled": true,
      "recipient": "ceo@payready.com",
      "schedule": "daily_8am"
    },
    "slack_alerts": {
      "enabled": true,
      "channel": "#ceo-alerts",
      "thresholds": {
        "low_client_health": 60,
        "poor_sales_performance": 70,
        "competitive_threat": "any_mention"
      }
    },
    "metrics_tracked": [
      "sales_performance",
      "client_health",
      "competitive_intelligence",
      "pipeline_health",
      "development_velocity"
    ],
    "data_sources": {
      "gong": {
        "enabled": true,
        "analysis_depth": "detailed"
      },
      "salesforce": {
        "enabled": true,
        "objects": ["Opportunity", "Account", "Case"]
      },
      "hubspot": {
        "enabled": true,
        "focus": "engagement_tracking"
      },
      "linear": {
        "enabled": true,
        "team": "PayReady Development"
      }
    }
  }
}
EOF

echo ""
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo ""
echo "1. 🔑 Configure missing API keys in .env file"
echo "2. 🧪 Test CEO analysis:"
echo "   ${YELLOW}python3 test_ceo_analysis.py${NC}"
echo ""
echo "3. 🔗 Set up Zapier workflows:"
echo "   • Go to zapier.com and create new Zaps"
echo "   • Use webhook trigger: http://192.9.142.8/api/v1/zapier/trigger"
echo "   • Connect your Salesforce, HubSpot, Linear accounts"
echo ""
echo "4. 📊 Access your services:"
echo "   • Zapier MCP: ${GREEN}http://localhost:80${NC}"
echo "   • Sophia AI: ${GREEN}http://localhost:8014${NC}"
echo "   • CEO Dashboard: ${GREEN}http://localhost:8010/ceo-dashboard${NC}"
echo ""
echo "5. 📈 Monitor your setup:"
echo "   ${YELLOW}tail -f logs/ceo_bi.log${NC}"
echo ""
echo -e "${BLUE}🚀 Your CEO Business Intelligence platform is ready!${NC}"
echo ""

# Create simple monitoring script
cat > monitor_ceo_bi.sh << 'EOF'
#!/bin/bash
echo "🔍 CEO BI Status Check"
echo "====================="

# Check Zapier MCP
if curl -s http://localhost:80/health > /dev/null; then
    echo "✅ Zapier MCP: Running"
else
    echo "❌ Zapier MCP: Down"
fi

# Check Sophia AI
if curl -s http://localhost:8014/health > /dev/null; then
    echo "✅ Sophia AI: Running"
else
    echo "❌ Sophia AI: Down"
fi

# Check recent CEO analysis
if [ -f "ceo_analysis_results.json" ]; then
    ANALYSIS_AGE=$(find ceo_analysis_results.json -mtime +1 2>/dev/null)
    if [ -z "$ANALYSIS_AGE" ]; then
        echo "✅ CEO Analysis: Recent (< 24h)"
    else
        echo "⚠️  CEO Analysis: Stale (> 24h)"
    fi
else
    echo "❌ CEO Analysis: No results found"
fi

echo ""
echo "📊 Quick Stats:"
if [ -f "ceo_analysis_results.json" ]; then
    python3 -c "
import json
with open('ceo_analysis_results.json') as f:
    data = json.load(f)
    print(f'   • Total calls: {data.get(\"total_calls_analyzed\", 0)}')
    print(f'   • Coaching insights: {len(data.get(\"sales_coaching_insights\", []))}')
    print(f'   • At-risk clients: {data.get(\"key_metrics\", {}).get(\"at_risk_clients\", 0)}')
"
fi
EOF

chmod +x monitor_ceo_bi.sh

echo -e "${GREEN}💡 Pro tip: Run './monitor_ceo_bi.sh' anytime to check your BI platform status${NC}" 